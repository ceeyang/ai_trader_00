from typing import List
from exchange import BinanceClient
from config import Config

class MarketScanner:
    def __init__(self, client: BinanceClient):
        self.client = client
        self.blacklist = ["USDC/USDT", "TUSD/USDT", "FDUSD/USDT", "USDP/USDT"] # Stablecoins

    def get_top_coins(self, limit: int = 50) -> List[str]:
        """
        获取筛选后的 Top Coin List (Get Filtered Top Coin List)
        """
        try:
            print("🔍 Scanning Market for Top Assets...")
            
            # 1. Fetch Tickers (Vol based)
            # fetch_tickers returns all, we sort by 'quoteVolume'
            tickers = self.client.exchange.fetch_tickers()
            
            # Convert to list and filter for USDT futures (PERPETUAL only)
            valid_tickers = []
            for symbol, data in tickers.items():
                # Check 1: Symbol string
                if '/USDT' in symbol and 'BUSD' not in symbol:
                     # Check 2: Contract Type (strictly swap/perpetual)
                     # CCXT usually puts 'swap' in type, or check if info has contractType
                     is_perp = False
                     if data.get('swap'): # CCXT 'swap' boolean
                         is_perp = True
                     elif data.get('info') and data['info'].get('contractType') == 'PERPETUAL':
                         is_perp = True
                     elif ':' in symbol:
                         # Heuristic: linear perps usually "BTC/USDT:USDT"
                         # Delivery usually has dates e.g. "BTC/USDT:USDT-250328"
                         # Check if suffix contains digits
                         suffix = symbol.split(':')[-1]
                         has_digits = any(char.isdigit() for char in suffix)
                         if not has_digits:
                              is_perp = True
                     
                     if is_perp and data.get('quoteVolume') is not None:
                         valid_tickers.append(data)
            
            # Sort by 24h Volume (descending)
            sorted_tickers = sorted(valid_tickers, key=lambda x: x['quoteVolume'], reverse=True)
            
            # Take top N candidates (e.g., top 100 to filter down to 20)
            candidates = sorted_tickers[:100]
            
            # 2. Filter Logic
            final_list = []
            
            # Get Funding Rates for check
            funding_rates = self.client.get_funding_rates()
            
            for ticker in candidates:
                symbol = ticker['symbol']
                
                # Filter 1: Blacklist (Stables)
                is_stable = any(stable in symbol for stable in self.blacklist)
                if is_stable:
                    continue
                
                # Filter 2: Funding Rate < 100% APR (approx 0.009% per 8h * 3 * 365 ? No, 100% APR is High)
                # 100% / 365 / 3 = 0.09% per 8h interval
                # Realistically, let's skip if rate > 0.001 (0.1% per 8h) just to be safe, or user config
                fr = funding_rates.get(symbol, 0.0)
                # APR = fr * 3 * 365
                apr = fr * 3 * 365
                if apr > Config.MAX_FUNDING_RATE_APR:
                    # print(f"⚠️ Skipping {symbol} due to High Funding Rate: {apr:.2%}")
                    continue
                
                final_list.append(symbol)
                
                if len(final_list) >= Config.TARGET_COIN_COUNT:
                    break
            
            print(f"✅ Scanner Selected {len(final_list)} coins: {final_list}")
            return final_list

        except Exception as e:
            print(f"❌ Market Scan Failed: {e}")
            return Config.DEFAULT_COINS  # Fallback
