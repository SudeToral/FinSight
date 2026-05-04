import json
import os
from confluent_kafka import Consumer, KafkaError
from agents.graph import app

KAFKA_BROKER = "127.0.0.1:9092"
TOPIC = "market_ticks"
GROUP_ID = "finsight-agent-group"

def start_consumer():
    conf = {
        'bootstrap.servers': '127.0.0.1:9092',
        'group.id': GROUP_ID,
        'auto.offset.reset': 'latest',
        'max.poll.interval.ms': 600000 # 10 minutes for human approval
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
            # Initialize Advanced Agentic AI Fields
            payload["news_headlines"] = []
            payload["reasoning"] = ""
            payload["next_step"] = ""
            payload["critic_feedback"] = ""
            payload["human_approval"] = True # Default to true unless changed
            payload["iterations"] = 0
            payload["market_analyzed"] = False
            payload["news_researched"] = False
            
            # Trigger LangGraph Agent with memory config
            try:
                # Use a specific thread_id (e.g. symbol) so the agent remembers per symbol
                config = {"configurable": {"thread_id": f"agent_thread_{payload['symbol']}"}}
                result = app.invoke(payload, config=config)
                print(f"--- Final Agent Decision ---")
                print(f"Action: {result.get('decision', 'HOLD')}")
                print(f"Reasoning: {result.get('reasoning', '')}")
                print(f"Execution Status: {'SUCCESS' if result.get('trade_executed') else 'NOT EXECUTED'}")
                print("-" * 30)
            except Exception as e:
                print(f"Error executing agent: {e}")
                
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    start_consumer()
