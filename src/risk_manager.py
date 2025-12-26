from config import Config

class RiskManager:
    def __init__(self):
        self.initial_equity = Config.INITIAL_EQUITY
        self.stop_loss_equity = self.initial_equity * (1 - Config.MAX_DRAWDOWN_PCT) # e.g. 200 * 0.7 = 140

    def check_hard_stop(self, current_equity: float) -> bool:
        """
        检查是否触发硬止损 (Check Hard Stop Loss)
        Returns: True if STOP triggered (Equity too low)
        """
        if current_equity < self.stop_loss_equity:
            print(f"🚨 ALERT: Hard Stop Triggered! Equity {current_equity:.2f} < Limit {self.stop_loss_equity:.2f}")
            return True
        return False
    
    def validate_order(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Safety check before order
        """
        if quantity <= 0:
            return False
        
        # Min Value Check (Double check here just in case)
        notional = quantity * price
        if notional < Config.MIN_ORDER_VALUE:
            # print(f"⚠️ Risk Manager: Order value {notional:.2f} too small for {symbol}")
            return False
            
        return True
