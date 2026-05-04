from confluent_kafka import Consumer, KafkaError

def check_kafka():
    conf = {
        'bootstrap.servers': '127.0.0.1:9092',
        'group.id': 'debug-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)
    consumer.subscribe(['market_ticks'])
    
    print("Checking for messages in 'market_ticks'...")
    msg = consumer.poll(timeout=5.0)
    
    if msg is None:
        print("No messages found.")
    elif msg.error():
        print(f"Error: {msg.error()}")
    else:
        print(f"Found message: {msg.value().decode('utf-8')}")
    
    consumer.close()

if __name__ == "__main__":
    check_kafka()
