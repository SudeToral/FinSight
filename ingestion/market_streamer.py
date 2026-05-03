import json
import time
import datetime
import random
from confluent_kafka import Producer
import yfinance as yf

KAFKA_BROKER = "localhost:9092"
TOPIC = "market_ticks"

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        pass # To avoid too much spam, we don't print successful deliveries here

def fetch_and_produce(producer, symbol="AAPL"):
    try:
        # Fetch 1m data for today to simulate ticks
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        
        if hist.empty:
            print(f"No data available for {symbol}")
            return
            
        print(f"Fetched {len(hist)} data points for {symbol}. Starting stream...")
        
        for index, row in hist.iterrows():
            # Add a slight random noise to simulate tick-by-tick within the minute
            price = row['Close'] + random.uniform(-0.05, 0.05)
            
            payload = {
                "symbol": symbol,
                "current_price": round(price, 2),
                "timestamp": index.isoformat(),
                "news_headlines": [], # Will be populated by news agent later
                "anomaly_detected": False,
                "risk_score": 0.0,
                "decision": "HOLD"
            }
            
            producer.produce(
                TOPIC, 
                key=symbol.encode('utf-8'), 
                value=json.dumps(payload).encode('utf-8'), 
                callback=delivery_report
            )
            producer.poll(0) # trigger callbacks
            
            print(f"Produced: {payload['symbol']} @ ${payload['current_price']} at {payload['timestamp']}")
            time.sleep(1) # stream speed (1 tick per second)
            
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")

if __name__ == "__main__":
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    print(f"Starting Market Streamer (connecting to {KAFKA_BROKER})...")
    
    try:
        # Send a few ticks
        fetch_and_produce(producer, "AAPL")
    except KeyboardInterrupt:
        print("Stopping streamer...")
    finally:
        producer.flush()
