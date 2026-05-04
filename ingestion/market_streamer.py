import json
import time
import datetime
import random
import sys
import os
from confluent_kafka import Producer
import yfinance as yf

# Add project root to sys.path for infrastructure imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infrastructure.database import get_db_connection

KAFKA_BROKER = "127.0.0.1:9092"
TOPIC = "market_ticks"

def delivery_report(err, msg):
    if err is not None:
        print(f"[Kafka] Delivery failed: {err}")

def get_watchlist():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM watchlist")
        symbols = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return symbols
    except Exception as e:
        print(f"[DB Error] Could not fetch watchlist: {e}")
        return ["AAPL"] # Fallback

def stream_market_data():
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    print(f"🚀 Starting Dynamic Market Streamer (Broker: {KAFKA_BROKER})...")

    while True:
        symbols = get_watchlist()
        print(f"\n--- Cycle Start: Streaming {len(symbols)} symbols ---")
        
        for symbol in symbols:
            try:
                # Fetch only the last 2 minutes to get the "latest" tick
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m").tail(1)
                
                if hist.empty:
                    continue
                
                price = hist['Close'].iloc[0] + random.uniform(-0.02, 0.02)
                prev_close = ticker.info.get('previousClose', price)
                daily_return = (price - prev_close) / prev_close if prev_close else 0
                
                payload = {
                    "symbol": symbol,
                    "current_price": round(price, 2),
                    "daily_return": round(daily_return, 4),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "news_headlines": [],
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
                print(f"[Produced] {symbol} @ ${payload['current_price']}")
                
            except Exception as e:
                print(f"[Error] {symbol}: {e}")
            
            producer.poll(0)
        
        producer.flush()
        print(f"--- Cycle End. Sleeping for 10 seconds ---")
        time.sleep(10)

if __name__ == "__main__":
    try:
        stream_market_data()
    except KeyboardInterrupt:
        print("\nStopping streamer...")
