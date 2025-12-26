import time
from typing import List, Dict
from exchange import BinanceClient
from risk_manager import RiskManager
from config import Config

class Rebalancer:
    def __init__(self, client: BinanceClient, risk_manager: RiskManager):
        self.client = client
        self.rm = risk_manager

    def rebalance(self, target_coins: List[str]):
        """
        核心再平衡逻辑 (Core Rebalance Logic)
        """
        print(f"\n--- ⚖️ Starting Rebalance Cycle at {time.strftime('%H:%M:%S')} ---")
        
        # 1. Get Account Info
        balance = self.client.get_account_balance()
        current_equity = balance['total_equity']
        print(f"💰 Account Equity: {current_equity:.2f} USDT")

        # 2. Risk Check
        if self.rm.check_hard_stop(current_equity):
            print("🛑 STOPPING BOT DUE TO RISK LIMIT")
            return

        # 3. Get Data
        prices = self.client.get_market_prices(target_coins)
        positions = self.client.get_cw_positions() # {symbol: quantity}

        # 4. Process each coin
        for symbol in target_coins:
            if symbol not in prices:
                print(f"⚠️ No price for {symbol}, skipping")
                continue
                
            price = prices[symbol]
            current_qty = positions.get(symbol, 0.0)
            current_value = current_qty * price
            
            # Target Value (Static 20 USDT or Dynamic based on equity?)
            # PRD says "Target Value: 20 USDT" constant, but effective leverage 2x.
            # Ideally = (Equity * Effective_Lev) / N_Coins
            # For strict adherence to PRD "Target Value 20", we use config.
            target_val = Config.TARGET_VALUE_PER_COIN
            
            diff_value = current_value - target_val
            diff_pct = diff_value / target_val if target_val > 0 else 0
            
            # Threshold Check
            # Sell if Value > Target * (1+Threshold) -> diff_pct > 0.05
            # Buy if Value < Target * (1-Threshold) -> diff_pct < -0.05
            
            threshold = Config.REBALANCE_THRESHOLD_PCT
            
            action = None
            qty_to_trade = 0.0
            
            if diff_pct > threshold:
                # Surplus: Sell the difference
                action = 'sell'
                amount_value = diff_value # e.g. 21.5 - 20 = 1.5 excess
            elif diff_pct < -threshold:
                # Deficit: Buy the difference
                action = 'buy'
                amount_value = -diff_value # e.g. 18.5 - 20 = -1.5 -> need 1.5
            else:
                # Balanced
                continue

            # MIN ORDER SIZE CHECK
            # If we need to trade $1.5 but min is $5.1, we have two choices:
            # 1. Skip (wait for $5 deviation)
            # 2. Force (not possible on exchange)
            # We must Skip.
            
            if amount_value < Config.MIN_ORDER_VALUE:
                # print(f"⏳ {symbol}: Deviation {amount_value:.2f} < MinOrder {Config.MIN_ORDER_VALUE}, Waiting...")
                continue
                
            # Execute
            qty_to_trade = amount_value / price
            
            # Risk Validation
            if self.rm.validate_order(symbol, qty_to_trade, price):
                self.client.place_order(symbol, action, qty_to_trade)
                
        print("--- ✅ Rebalance Cycle Complete ---\n")
