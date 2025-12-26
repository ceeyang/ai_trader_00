import ccxt
import time
from typing import Dict, List, Optional
from config import Config

class BinanceClient:
    def __init__(self):
        """
        初始化 Binance 交易所客户端 (Initialize Binance Exchange Client)
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
            # Update specific keys instead of replacing entire dict to avoid missing 'sapi' errors
            self.exchange.urls['api']['fapiPublic'] = 'https://testnet.binancefuture.com/fapi/v1'
            self.exchange.urls['api']['fapiPrivate'] = 'https://testnet.binancefuture.com/fapi/v1'
            self.exchange.urls['api']['public'] = 'https://testnet.binancefuture.com/fapi/v1'
            self.exchange.urls['api']['private'] = 'https://testnet.binancefuture.com/fapi/v1'
            
            # Map sapi (Spot API) to allow CCXT internals to pass checks, even if we don't use it
            # We point it to the spot testnet just in case
            self.exchange.urls['api']['sapi'] = 'https://testnet.binance.vision/sapi/v1'
            
            print("⚠️ Running in TESTNET mode (Manual URL Config)")
            
        # Optimization: Disable fetchCurrencies to prevent CCXT from hitting SAPI endpoints on load_markets()
        self.exchange.has['fetchCurrencies'] = False


    def validate_connectivity(self):
        """
        验证 API 连接 (Validate API Connectivity)
        """
        try:
            self.exchange.fetch_time()
            print("✅ Binance API Connected Successfully")
            return True
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            raise e

    def get_market_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取最新价格 (Batch Fetch Latest Prices)
        Optimize: 使用 fetch_tickers 一次性获取所有价格，减少 API 调用
        """
        try:
            tickers = self.exchange.fetch_tickers(symbols)
            prices = {symbol: float(data['last']) for symbol, data in tickers.items()}
            return prices
        except Exception as e:
            print(f"❌ Error fetching prices: {e}")
            return {}

    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额信息 (Get Account Balance)
        """
        try:
            # Bypass CCXT fetch_balance() which may try to hit SAPI (Spot) endpoints
            # Use direct Futures API call: GET /fapi/v2/account
            account_info = self.exchange.fapiPrivateV2GetAccount()
            
            # Extract Equity and Margin
            total_equity = float(account_info['totalMarginBalance'])
            free_margin = float(account_info['availableBalance'])
            
            return {
                'total_equity': total_equity,
                'free_margin': free_margin
            }
        except Exception as e:
            print(f"❌ Error fetching balance: {e}")
            return {'total_equity': 0.0, 'free_margin': 0.0}

    def get_cw_positions(self) -> Dict[str, float]:
        """
        获取当前持仓大小 (Get Current Positions)
        Return: {symbol: amount} (amount 可以是负数，但本策略只做多)
        """
        try:
            # fetch_positions normally returns list
            positions = self.exchange.fetch_positions()
            # Filter non-zero positions and map to dict
            active_positions = {}
            for pos in positions:
                amt = float(pos['contracts'])
                if amt != 0:
                    active_positions[pos['symbol']] = amt
            return active_positions
        except Exception as e:
            print(f"❌ Error fetching positions: {e}")
            return {}

    def set_leverage(self, symbol: str, leverage: int):
        """
        设置杠杆倍数 (Set Leverage)
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            print(f"⚠️ Failed to set leverage for {symbol}: {e}")

    def place_order(self, symbol: str, side: str, amount: float, price: float = None):
        """
        下单 (Place Order)
        side: 'buy' or 'sell'
        """
        try:
            # 必须检查最小下单价值 (MIN_ORDER_VALUE check is vital)
            # 我们在 Rebalancer 层做计算，这里做最后一道防线或直接执行
            # 本策略主要是 Market Order 做再平衡 (Rebalancing uses Market Orders usually for speed)
            
            type = 'market'
            params = {}
            
            # log
            print(f"🚀 Executing {side.upper()} {symbol}: {amount} units")
            
            order = self.exchange.create_order(symbol, type, side, amount, price, params)
            return order
        except Exception as e:
            print(f"❌ Order Failed ({symbol} {side}): {e}")
            return None

    def get_funding_rates(self) -> Dict[str, float]:
        """
        批量获取资金费率 (Batch Fetch Funding Rates)
        """
        try:
            # Endpoint: fapiPublicGetPremiumIndex
            response = self.exchange.fapiPublicGetPremiumIndex()
            
            # Debugging type check
            if not isinstance(response, list):
                print(f"⚠️ get_funding_rates: info response is not a list, got {type(response)}")
                return {}

            funding_map = {}
            for item in response:
                # item should be a dict
                if not isinstance(item, dict):
                    continue
                    
                raw_symbol = item.get('symbol')
                rate = item.get('lastFundingRate')
                
                if raw_symbol and rate is not None:
                    # Resolve to CCXT symbol if possible
                    market = self.exchange.markets_by_id.get(raw_symbol)
                    
                    # Handle case where market might be a list (collision or ccxt structure)
                    if isinstance(market, list):
                        market = market[0]
                        
                    if market and isinstance(market, dict):
                        funding_map[market['symbol']] = float(rate)
                    else:
                        # Map raw symbol directly as fallback or try simple parsing
                         funding_map[raw_symbol] = float(rate)
                    
            return funding_map
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error fetching funding rates: {e}")
            return {}
