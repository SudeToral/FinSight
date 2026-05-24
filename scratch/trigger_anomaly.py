import json
import datetime
from confluent_kafka import Producer

KAFKA_BROKER = "127.0.0.1:9092"
TOPIC = "market_ticks"

def delivery_report(err, msg):
    if err is not None:
        print(f"[Kafka] Delivery failed: {err}")
    else:
        print(f"[Kafka] Trigger tick successfully sent to {msg.topic()}!")

def trigger_fake_anomaly():
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    print(f"🚀 Injecting anomalous high-volatility trade trigger for TSLA...")

    # We inject a massive anomaly tick: a massive price jump with custom positive news
    payload = {
        "symbol": "TSLA",
        "current_price": 450.00,
        "daily_return": 0.15,  # 15% daily return (huge anomaly!)
        "timestamp": datetime.datetime.now().isoformat(),
        "news_headlines": [
            "Tesla Swarm AI trading agent achieves 99% accuracy in live market tests.",
            "TSLA stock price breaks all-time daily volume records after AI breakthrough."
        ],
        "anomaly_detected": True,
        "risk_score": 0.0,
        "decision": "HOLD"
    }

    producer.produce(
        TOPIC,
        key="TSLA".encode('utf-8'),
        value=json.dumps(payload).encode('utf-8'),
        callback=delivery_report
    )
    producer.flush()

if __name__ == "__main__":
    trigger_fake_anomaly()
