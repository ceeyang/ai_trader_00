from typing import List
from exchange import BinanceClient
from config import Config
from logger import logger

class MarketScanner:
    def __init__(self, client: BinanceClient):
        self.client = client
        self.blacklist = ["USDC/USDT", "TUSD/USDT", "FDUSD/USDT", "USDP/USDT"] # Stablecoins

    async def get_top_coins(self, limit: int = 50) -> List[str]:
        """
        获取筛选后的 Top Coin List (Get Filtered Top Coin List) - Async
        """
        try:
            logger.info("🔍 Scanning Market for Top Assets...")
            
            # 1. Fetch Tickers (Vol based)
            # fetch_tickers returns all, we sort by 'quoteVolume'
            tickers = await self.client.exchange.fetch_tickers()
            
            # Ensure markets are loaded for metadata check
            if not self.client.exchange.markets:
                await self.client.exchange.load_markets()
            
            markets = self.client.exchange.markets

            # Convert to list and filter for USDT futures (PERPETUAL only)
            valid_tickers = []
            for symbol, data in tickers.items():
                market_info = markets.get(symbol)
                
                # Strict Filtering using CCXT Market Metadata
                # 1. Must exist in markets
                # 2. Must be linear (USDT-margined)
                # 3. Must be swap (Perpetual)
                # 4. Must be active
                # 5. Quote currency must be USDT
                
                if not market_info:
                    continue

                if (market_info.get('linear') is True and 
                    market_info.get('swap') is True and 
                    market_info.get('contract') is True and
                    market_info.get('quote') == 'USDT' and
                    market_info.get('active', True) is True):  # Default to True if active not set
                     
                     if data.get('quoteVolume') is not None:
                         valid_tickers.append(data)
            
            # Sort by 24h Volume (descending)
            sorted_tickers = sorted(valid_tickers, key=lambda x: x['quoteVolume'], reverse=True)
            
            # Take top N candidates (e.g., top 100 to filter down to 20)
            candidates = sorted_tickers[:100]
            
            # 2. Filter Logic
            final_list = []
            
            # Get Funding Rates for check
            funding_rates = await self.client.get_funding_rates()
            
            for ticker in candidates:
                symbol = ticker['symbol']
                
                # Filter 1: Blacklist (Stables)
                is_stable = any(stable in symbol for stable in self.blacklist)
                if is_stable:
                    continue
                
                # Filter 2: Funding Rate < 100% APR 
                fr = funding_rates.get(symbol, 0.0)
                # APR = fr * 3 * 365
                apr = fr * 3 * 365
                if apr > Config.MAX_FUNDING_RATE_APR:
                    # logger.debug(f"⚠️ Skipping {symbol} due to High Funding Rate: {apr:.2%}")
                    continue
                
                final_list.append(symbol)
                
                if len(final_list) >= Config.TARGET_COIN_COUNT:
                    break
            
            logger.info(f"✅ Scanner Selected {len(final_list)} coins: {final_list}")
            return final_list

        except Exception as e:
            logger.error(f"❌ Market Scan Failed: {e}")
            return Config.DEFAULT_COINS  # Fallback
