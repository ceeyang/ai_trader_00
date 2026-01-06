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
        # Select Keys based on environment
        if Config.IS_TESTNET and Config.TESTNET_API_KEY:
            api_key = Config.TESTNET_API_KEY
            secret = Config.TESTNET_SECRET_KEY
        else:
            api_key = Config.API_KEY
            secret = Config.SECRET_KEY
            
        self.config = {
            'apiKey': api_key,
            'secret': secret,
            # 'verbose': True, # DEBUG: Enable verbose output to see raw requests
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # 默认使用合约 (Futures)
                'fetchMarkets': ['linear'], # Only fetch USDT Futures to avoid SAPI/Margin calls
            }
        }
        
        self.exchange = ccxt.binance(self.config)
        
        if Config.IS_TESTNET:
            # Manual Override for Futures Testnet
            # According to official docs: https://demo-fapi.binance.com
            testnet_base = 'https://demo-fapi.binance.com/fapi/v1'
            testnet_base_v2 = 'https://demo-fapi.binance.com/fapi/v2'
            testnet_base_v3 = 'https://demo-fapi.binance.com/fapi/v3'
            
            self.exchange.urls['api']['fapiPublic'] = testnet_base
            self.exchange.urls['api']['fapiPrivate'] = testnet_base
            self.exchange.urls['api']['fapiPublicV2'] = testnet_base_v2
            self.exchange.urls['api']['fapiPrivateV2'] = testnet_base_v2
            self.exchange.urls['api']['fapiPublicV3'] = testnet_base_v3
            self.exchange.urls['api']['fapiPrivateV3'] = testnet_base_v3
            
            # General public/private overrides just in case
            self.exchange.urls['api']['public'] = testnet_base
            self.exchange.urls['api']['private'] = testnet_base
            
            # Map sapi (Spot API) to allow CCXT internals to pass checks
            self.exchange.urls['api']['sapi'] = 'https://testnet.binance.vision/sapi/v1'
            
            logger.warning("⚠️ Running in TESTNET mode (URL: demo-fapi.binance.com)")
            
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
            # Use standard CCXT fetch_balance which handles Testnet URLs better if config is right
            # We filter for 'future' type implicitly by connection options, but specifying type is safer
            balance = await self.exchange.fetch_balance({'type': 'future'})
            
            # CCXT normalizes this into 'total' and 'free'
            # For Futures, we typically care about:
            # - total_equity (Total Margin Balance) matches 'total'['USDT'] typically?
            # Actually CCXT structures futures balance differently sometimes.
            # Let's inspect the 'info' if needed, or use the common structure.
            
            # Common CCXT futures structure:
            # balance['USDT']['total'] = wallet balance ? or margin balance?
            # It's safer to read from specific fields if we want "Total Equity" (Margin Balance).
            
            # However, for robustness, let's look at the raw info if available, or trust CCXT.
            # The previous code used 'totalMarginBalance' from raw API.
            # CCXT maps 'total' to wallet balance usually.
            
            # Let's try to find 'totalMarginBalance' in info
            info = balance.get('info', {})
            
            if 'totalMarginBalance' in info:
                total_equity = float(info['totalMarginBalance'])
                free_margin = float(info['availableBalance'])
            else:
                # Fallback to standard CCXT structure (might be slightly different meaning)
                total_equity = float(balance.get('USDT', {}).get('total', 0.0))
                free_margin = float(balance.get('USDT', {}).get('free', 0.0))
            
            return {
                'total_equity': total_equity,
                'free_margin': free_margin
            }

        except Exception as e:
            msg = str(e)
            if "-2015" in msg:
                 logger.error(f"❌ AUTH ERROR: Invalid API Key or Permissions. \n"
                              f"   >> Ensure you are using BINANCE FUTURES TESTNET keys (https://testnet.binancefuture.com/)\n"
                              f"   >> NOT Spot Testnet keys.")
            else:
                logger.error(f"❌ Error fetching balance: {e}")
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

    async def get_symbol_limits(self, symbol: str) -> Dict[str, float]:
        """
        获取交易对的限制信息 (Get Symbol Limits)
        """
        try:
            if not self.exchange.markets:
                await self.exchange.load_markets()
            
            market = self.exchange.market(symbol)
            return {
                'min_amount': market['limits']['amount']['min'],
                'max_amount': market['limits']['amount']['max'], # Added Max Amount
                'min_cost': market['limits']['cost']['min'], # Min Notional
                'amount_precision': market['precision']['amount'],
            }
        except Exception as e:
            logger.warning(f"⚠️ Could not get limits for {symbol}: {e}")
            # Return safe defaults (conservative)
            return {'min_amount': 0.001, 'max_amount': 1000000.0, 'min_cost': 5.0, 'amount_precision': 0.001}
