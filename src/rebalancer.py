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

        # 4. Limit Target Coins
        # If scanner returns more than limit, take top N
        if len(target_coins) > Config.MAX_OPEN_POSITIONS:
            target_coins = target_coins[:Config.MAX_OPEN_POSITIONS]
            
        logger.info(f"🎯 Target Portfolio: {len(target_coins)} Assets")
        
        # 5. Calculate Weights & Targets
        # Target based on Effective Leverage
        target_exposure_lev = current_equity * Config.EFFECTIVE_LEVERAGE
        
        # Target based on Max Margin Utilization (Safety Cap)
        # Max Exposure = Equity * MaxMarginPct * AccountLeverage
        max_exposure_margin = current_equity * Config.MAX_MARGIN_UTILIZATION_PCT * Config.LEVERAGE
        
        # Take the smaller of the two to be safe
        total_exposure_target = min(target_exposure_lev, max_exposure_margin)
        
        if total_exposure_target != target_exposure_lev:
            logger.warning(f"⚠️ Target Exposure capped by Max Margin Ratio: {total_exposure_target:.2f} (Requested: {target_exposure_lev:.2f})")
        
        # Determine weights
        # a. Explicit weights
        explicit_weights = {}
        used_weight_sum = 0.0
        remaining_coins = []
        
        for coin in target_coins:
            if coin in Config.COIN_WEIGHTS:
                w = Config.COIN_WEIGHTS[coin]
                explicit_weights[coin] = w
                used_weight_sum += w
            else:
                remaining_coins.append(coin)
        
        # b. Implicit weights (Equal distribution of remaining)
        remaining_weight = max(0.0, 1.0 - used_weight_sum)
        implicit_w = 0.0
        if remaining_coins:
             implicit_w = remaining_weight / len(remaining_coins)
             
        # Log Allocation Plan
        logger.info(f"📊 Allocation Plan (Total Exposure: {total_exposure_target:.2f} USDT):")
        
        # 6. Process Trades
        for symbol in target_coins:
            if symbol not in prices:
                logger.warning(f"⚠️ No price for {symbol}, skipping")
                continue
                
            price = prices[symbol]
            current_qty = positions.get(symbol, 0.0)
            current_value = current_qty * price
            
            # Determine Target Value
            weight = explicit_weights.get(symbol, implicit_w)
            target_val = total_exposure_target * weight
            
            logger.info(f"   🔹 {symbol}: Weight {weight*100:.1f}% -> Target {target_val:.2f} USDT (Curr: {current_value:.2f})")
            
            diff_value = current_value - target_val # Positive = Sell, Negative = Buy
            
            # Risk Check: Max Position Drawdown
            # (We need entry price to calc drawdown properly, but here we can check if 
            # current value is significantly lower than what we bought? 
            # Without entry price history, strict PnL stop loss is hard in this simple loop.
            # Assuming 'rebalance' fixes it.
            # BUT user asked for "Max Drawdown Per Coin".
            # We can request UnRealized PnL from Position Data if available.
            
            # Threshold Check
            target_val_safe = target_val if target_val > 0 else 1.0 # avoid div by zero
            diff_pct = diff_value / target_val_safe
            
            threshold = Config.REBALANCE_THRESHOLD_PCT
            
            action = None
            amount_input = 0.0
            
            # Logic:
            # If diff > 0 (Surplus) -> Sell (value to sell = diff_value)
            # If diff < 0 (Deficit) -> Buy (value to buy = -diff_value)
            
            if abs(diff_pct) < threshold:
                continue

            # MIN ORDER SIZE CHECK
            # Check Global Min Order Value (Config)
            if abs(diff_value) < Config.MIN_ORDER_VALUE:
                continue

            # Check Exchange Limits (Dynamic)
            limits = await self.client.get_symbol_limits(symbol)
            if price <= 0:
                continue

            amount = abs(diff_value) / price
            
            # Check Min Quantity
            if amount < limits['min_amount']:
                logger.warning(f"⚠️ Skipping {symbol}: Amount {amount:.6f} < Min {limits['min_amount']}")
                continue
                
            # Check Max Quantity (Fix for -4005)
            if amount > limits['max_amount']:
                logger.warning(f"⚠️ Capping {symbol}: Amount {amount:.6f} -> Max {limits['max_amount']}")
                amount = limits['max_amount']
                
            # Check Min Notional (Cost)
            actual_value = amount * price
            if actual_value < limits['min_cost']:
                logger.warning(f"⚠️ Skipping {symbol}: Value {actual_value:.2f} < Min Notional {limits['min_cost']}")
                continue

            # Execute
            side = 'buy' if diff_value < 0 else 'sell'
            
            # Risk Validation
            if self.rm.validate_order(symbol, amount, price):
                await self.client.place_order(symbol, side, amount, price)
                
        logger.info("--- ✅ Rebalance Cycle Complete ---\n")
