import time
import asyncio
from typing import List, Dict
from exchange import BinanceClient
from risk_manager import RiskManager
from config import Config
from logger import logger

class Rebalancer:
    def __init__(self, client: BinanceClient, risk_manager: RiskManager):
        self.client = client
        self.rm = risk_manager

    async def rebalance(self, target_coins: List[str]):
        """
        核心再平衡逻辑 (Core Rebalance Logic) - Async
        """
        logger.info(f"--- ⚖️ Starting Rebalance Cycle ---")
        
        # 1. Get Account Info
        balance = await self.client.get_account_balance()
        current_equity = balance['total_equity']
        logger.info(f"💰 Account Equity: {current_equity:.2f} USDT")

        # 2. Risk Check
        if self.rm.check_hard_stop(current_equity):
            logger.critical("🛑 STOPPING BOT DUE TO RISK LIMIT")
            return

        # 3. Get Data
        prices = await self.client.get_market_prices(target_coins)
        positions = await self.client.get_cw_positions() # {symbol: quantity}

        # 4. Process each coin
        # Note: We process sequentially to avoid API rate limits on ordering, 
        # allowing for some delay between orders if needed in future.
        for symbol in target_coins:
            if symbol not in prices:
                logger.warning(f"⚠️ No price for {symbol}, skipping")
                continue
                
            price = prices[symbol]
            current_qty = positions.get(symbol, 0.0)
            current_value = current_qty * price
            
            # Target Value
            target_val = Config.TARGET_VALUE_PER_COIN
            
            diff_value = current_value - target_val
            diff_pct = diff_value / target_val if target_val > 0 else 0
            
            # Threshold Check
            threshold = Config.REBALANCE_THRESHOLD_PCT
            
            action = None
            qty_to_trade = 0.0
            amount_value = 0.0
            
            if diff_pct > threshold:
                # Surplus: Sell the difference
                action = 'sell'
                amount_value = diff_value 
            elif diff_pct < -threshold:
                # Deficit: Buy the difference
                action = 'buy'
                amount_value = -diff_value 
            else:
                # Balanced
                continue

            # MIN ORDER SIZE CHECK
            if amount_value < Config.MIN_ORDER_VALUE:
                # logger.debug(f"⏳ {symbol}: Deviation {amount_value:.2f} < MinOrder {Config.MIN_ORDER_VALUE}, Waiting...")
                continue
                
            # Execute
            qty_to_trade = amount_value / price
            
            # Risk Validation
            if self.rm.validate_order(symbol, qty_to_trade, price):
                await self.client.place_order(symbol, action, qty_to_trade)
                
        logger.info("--- ✅ Rebalance Cycle Complete ---\n")
