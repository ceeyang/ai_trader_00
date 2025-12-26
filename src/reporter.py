import csv
import os
import time

class Reporter:
    def __init__(self, log_file="data/trades.csv"):
        self.log_file = log_file
        # Ensure data dir exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV with headers if not exists"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'symbol', 'side', 'amount', 'price', 'value', 'pnl'])

    def log_trade(self, symbol, side, amount, price, value, pnl=0):
        """Log trade to CSV"""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                symbol,
                side,
                amount,
                price,
                value,
                pnl
            ])
            print(f"📝 Logged trade: {symbol} {side} {amount}")

    def send_notification(self, message):
        """
        Send notification (e.g. Telegram)
        TODO: Implement real Telegram Bot API call
        """
        print(f"📨 NOTIFICATION: {message}")
