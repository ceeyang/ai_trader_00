import ccxt.pro as ccxt  # Use pro if available, otherwise standard ccxt async
# Fallback if pro not installed/licensed, but usually ccxt includes async in standard package as ccxt.async_support
# safely import async support
try:
    import ccxt.async_support as ccxt
except ImportError:
    import ccxt

import asyncio
from typing import Dict, List, Optional
from config import Config
from logger import logger

class BinanceClient:
    def __init__(self):
        """
        初始化 Binance 交易所客户端 (Initialize Binance Exchange Client) - Async
        """
        self.config = {
            'apiKey': Config.API_KEY,
            'secret': Config.SECRET_KEY,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # 默认使用合约 (Futures)
                'fetchMarkets': ['linear'], # Only fetch USDT Futures to avoid SAPI/Margin calls
            }
        }
        
        self.exchange = ccxt.binance(self.config)
        
        if Config.IS_TESTNET:
            # Manual Override for Futures Testnet
            self.exchange.urls['api']['fapiPublic'] = 'https://testnet.binancefuture.com/fapi/v1'
            self.exchange.urls['api']['fapiPrivate'] = 'https://testnet.binancefuture.com/fapi/v1'
            self.exchange.urls['api']['public'] = 'https://testnet.binancefuture.com/fapi/v1'
            self.exchange.urls['api']['private'] = 'https://testnet.binancefuture.com/fapi/v1'
            
            # Map sapi (Spot API) to allow CCXT internals to pass checks
            self.exchange.urls['api']['sapi'] = 'https://testnet.binance.vision/sapi/v1'
            
            logger.warning("⚠️ Running in TESTNET mode (Manual URL Config)")
            
        # Optimization: Disable fetchCurrencies
        self.exchange.has['fetchCurrencies'] = False

    async def close(self):
        """Cleanup connection"""
        if self.exchange:
            await self.exchange.close()

    async def validate_connectivity(self):
        """
        验证 API 连接 (Validate API Connectivity)
        """
        try:
            await self.exchange.fetch_time()
            logger.info("✅ Binance API Connected Successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Connection Failed: {e}")
            raise e

    async def get_market_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取最新价格 (Batch Fetch Latest Prices)
        """
        try:
            # fetch_tickers supports multiple symbols
            tickers = await self.exchange.fetch_tickers(symbols)
            prices = {symbol: float(data['last']) for symbol, data in tickers.items()}
            return prices
        except Exception as e:
            logger.error(f"❌ Error fetching prices: {e}")
            return {}

    async def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额信息 (Get Account Balance)
        """
        try:
            # Bypass CCXT fetch_balance() which may try to hit SAPI (Spot) endpoints
            # Use direct Futures API call: GET /fapi/v2/account
            account_info = await self.exchange.fapiPrivateV2GetAccount()
            
            # Extract Equity and Margin
            total_equity = float(account_info['totalMarginBalance'])
            free_margin = float(account_info['availableBalance'])
            
            return {
                'total_equity': total_equity,
                'free_margin': free_margin
            }
        except Exception as e:
            logger.error(f"❌ Error fetching balance: {e}")
            return {'total_equity': 0.0, 'free_margin': 0.0}

    async def get_cw_positions(self) -> Dict[str, float]:
        """
        获取当前持仓大小 (Get Current Positions)
        """
        try:
            positions = await self.exchange.fetch_positions()
            active_positions = {}
            for pos in positions:
                amt = float(pos['contracts'])
                if amt != 0:
                    active_positions[pos['symbol']] = amt
            return active_positions
        except Exception as e:
            logger.error(f"❌ Error fetching positions: {e}")
            return {}

    async def set_leverage(self, symbol: str, leverage: int):
        """
        设置杠杆倍数 (Set Leverage)
        """
        try:
            await self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            logger.warning(f"⚠️ Failed to set leverage for {symbol}: {e}")

    async def place_order(self, symbol: str, side: str, amount: float, price: float = None) -> Optional[Dict]:
        """
        下单 (Place Order)
        """
        try:
            type_ = 'market'
            params = {}
            
            logger.info(f"🚀 Executing {side.upper()} {symbol}: {amount} units")
            
            order = await self.exchange.create_order(symbol, type_, side, amount, price, params)
            return order
        except Exception as e:
            logger.error(f"❌ Order Failed ({symbol} {side}): {e}")
            return None

    async def get_funding_rates(self) -> Dict[str, float]:
        """
        批量获取资金费率 (Batch Fetch Funding Rates)
        """
        try:
            response = await self.exchange.fapiPublicGetPremiumIndex()
            
            if not isinstance(response, list):
                logger.warning(f"⚠️ get_funding_rates: info response is not a list, got {type(response)}")
                return {}

            funding_map = {}
            for item in response:
                if not isinstance(item, dict):
                    continue
                    
                raw_symbol = item.get('symbol')
                rate = item.get('lastFundingRate')
                
                if raw_symbol and rate is not None:
                    # Note: resolving to ccxt symbol async is tricky without loading all markets.
                    # We can use raw symbol if we are careful, or try to map if we loaded markets.
                    # For optimization, we use loose mapping or pre-loaded cache.
                    # Here we return raw symbols map, caller needs to handle matching or we map simply.
                    # NOTE: config.DEFAULT_COINS are usually in CCXT format (BTC/USDT).
                    # Binance raw is BTCUSDT.
                    
                    # Simple conversion attempt
                    ccxt_symbol = raw_symbol
                    if raw_symbol.endswith('USDT'):
                        base = raw_symbol[:-4]
                        ccxt_symbol = f"{base}/USDT"
                    
                    funding_map[ccxt_symbol] = float(rate)
                    
            return funding_map
        except Exception as e:
            logger.error(f"❌ Error fetching funding rates: {e}")
            return {}
