import json
import os
from confluent_kafka import Consumer, KafkaError
from agents.graph import app

KAFKA_BROKER = "localhost:9092"
TOPIC = "market_ticks"
GROUP_ID = "finsight-agent-group"

def start_consumer():
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'latest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([TOPIC])
    
    print(f"Agent Consumer started. Listening to topic '{TOPIC}' on broker {KAFKA_BROKER}...")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            
            payload = json.loads(msg.value().decode('utf-8'))
            print(f"\n[Kafka] Received tick for {payload['symbol']} at {payload['current_price']}")
            
            # Here we might need to compute the features that the model expects 
            # like daily_return, volatility_5d, etc. For now, we mock them
            # so the market_analyzer doesn't fail.
            payload["daily_return"] = 0.0 # Placeholder
            payload["volatility_5d"] = 0.0 # Placeholder
            payload["volume_ratio"] = 1.0 # Placeholder
            payload["price_range_pct"] = 0.0 # Placeholder
            payload["reasoning"] = ""
            
            # Trigger LangGraph Agent with memory config
            try:
                # Use a specific thread_id (e.g. symbol) so the agent remembers per symbol
                config = {"configurable": {"thread_id": f"agent_thread_{payload['symbol']}"}}
                result = app.invoke(payload, config=config)
                print(f"--- Agent Decision ---")
                print(f"Action: {result.get('decision', 'HOLD')}")
                print(f"Reasoning: {result.get('reasoning', '')}")
                print("-" * 20)
            except Exception as e:
                print(f"Error executing agent: {e}")
                
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    start_consumer()
