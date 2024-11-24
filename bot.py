
import ccxt
import pandas as pd
import time
from datetime import datetime
import numpy as np

class BitcoinTradingBot:
    def __init__(self, demo_api_key='', demo_secret=''):
        # Initialize exchange with demo/testnet account
        self.exchange = ccxt.binance({
            'apiKey': demo_api_key,
            'secret': demo_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures trading
                'testnet': True,  # Enable testnet/demo mode
            }
        })
        
        self.symbol = 'BTC/USDT'
        self.timeframe = '1h'
        self.position = None
        self.in_position = False

    def get_historical_data(self):
        """Fetch historical price data"""
        ohlcv = self.exchange.fetch_ohlcv(
            symbol=self.symbol,
            timeframe=self.timeframe,
            limit=100
        )
        
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def calculate_signals(self, df):
        """Calculate trading signals using Simple Moving Averages"""
        # Calculate moving averages
        df['SMA20'] = df['close'].rolling(window=20).mean()
        df['SMA50'] = df['close'].rolling(window=50).mean()
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['SMA20'] > df['SMA50'], 'signal'] = 1  # Buy signal
        df.loc[df['SMA20'] < df['SMA50'], 'signal'] = -1  # Sell signal
        
        return df

    def execute_trade(self, signal):
        """Execute trades based on signals"""
        try:
            balance = self.exchange.fetch_balance()
            usdt_balance = balance['USDT']['free']
            
            if signal == 1 and not self.in_position:  # Buy signal
                # Calculate position size (1% of balance)
                amount = (usdt_balance * 0.01) / self.exchange.fetch_ticker(self.symbol)['last']
                
                # Create market buy order
                order = self.exchange.create_market_buy_order(
                    symbol=self.symbol,
                    amount=amount
                )
                self.in_position = True
                self.position = amount
                print(f"Buy order executed: {order}")
                
            elif signal == -1 and self.in_position:  # Sell signal
                # Create market sell order
                order = self.exchange.create_market_sell_order(
                    symbol=self.symbol,
                    amount=self.position
                )
                self.in_position = False
                self.position = None
                print(f"Sell order executed: {order}")
                
        except Exception as e:
            print(f"Error executing trade: {e}")

    def run(self):
        """Main bot loop"""
        print("Starting Bitcoin trading bot...")
        while True:
            try:
                # Get historical data
                df = self.get_historical_data()
                
                # Calculate signals
                df = self.calculate_signals(df)
                
                # Get latest signal
                current_signal = df['signal'].iloc[-1]
                
                # Execute trade if there's a signal
                if current_signal != 0:
                    self.execute_trade(current_signal)
                
                # Print current status
                print(f"Current time: {datetime.now()}")
                print(f"Current BTC price: {df['close'].iloc[-1]}")
                print(f"Current signal: {current_signal}")
                print(f"In position: {self.in_position}")
                print("------------------------")
                
                # Wait for next interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying

# Usage example
if __name__ == "__main__":
    bot = BitcoinTradingBot()
    bot.run()
