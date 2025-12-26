# Index-style Leveraged Long Bot

A Python-based quantitative trading bot that maintains a portfolio of top altcoins with low leverage and dynamic rebalancing.

## Requirements
- Python 3.9+
- Binance Futures Account (API Key & Secret)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your funds-loaded API Keys.

3. **Run the Bot**
   ```bash
   python run.py
   ```

## Docker Deployment

1. **Build Image**
   ```bash
   docker build -t trader-bot .
   ```

2. **Run Container**
   ```bash
   docker run -d --env-file .env --name my-trader trader-bot
   ```

## Strategy
- **Scan**: Picks top coins by volume.
- **Rebalance**: Checks every 5 minutes.
- **Trade**: Buys low, sells high to maintain ~20 USDT value per coin.
