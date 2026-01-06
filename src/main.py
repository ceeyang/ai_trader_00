import asyncio
import signal
from config import Config
from exchange import BinanceClient
from market_scanner import MarketScanner
from risk_manager import RiskManager
from rebalancer import Rebalancer
from logger import logger

# Graceful shutdown handler
class GracefulExit:
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True

async def main_loop():
    logger.info("=== 🚀 Starting Quantitative Trading Bot (AsyncIO) ===")
    
    client = None
    try:
        # 1. Initialize Components
        client = BinanceClient()
        if not await client.validate_connectivity():
            return
            
        scanner = MarketScanner(client)
        risk_manager = RiskManager()
        rebalancer = Rebalancer(client, risk_manager)
        
        killer = GracefulExit()
        
        logger.info(f"✅ Bot initialized. Schedule: Every {Config.SCAN_INTERVAL_MINUTES} minutes.")

        # 2. Main Loop
        while not killer.kill_now:
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Step A: Scan
                # In production, we might want to cache this list or update it less frequently than rebalancing
                coins = await scanner.get_top_coins()
                if not coins:
                    logger.warning("⚠️ No coins to trade. Waiting for next cycle.")
                else:
                    # Step B: Rebalance
                    await rebalancer.rebalance(coins)
                
                # Check for exit before sleeping
                if killer.kill_now:
                    break

                # Sleep until next interval
                # Calculate elapsed time to maintain precise schedule
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_sec = (Config.SCAN_INTERVAL_MINUTES * 60) - elapsed
                
                if sleep_sec > 0:
                    logger.info(f"💤 Sleeping for {sleep_sec:.1f}s...")
                    # We sleep in chunks to check for exit signals (or use asyncio.wait)
                    # Simple chunk sleep:
                    while sleep_sec > 0 and not killer.kill_now:
                        step = min(1, sleep_sec)
                        await asyncio.sleep(step)
                        sleep_sec -= step
                        
            except Exception as e:
                logger.error(f"❌ Cycle Failed: {e}", exc_info=True)
                await asyncio.sleep(60) # Retry after 1 min on error

        logger.info("🛑 Bot stopping gracefully...")

    except Exception as e:
        logger.critical(f"❌ Fatal Error: {e}", exc_info=True)
    finally:
        if client:
            await client.close()
            logger.info("🔌 Connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        # Should be caught by signal handler, but just in case
        pass
    except Exception as e:
        print(f"Global Error: {e}")
