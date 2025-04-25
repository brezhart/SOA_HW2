import json
import os
from datetime import datetime
from kafka import KafkaProducer

# Kafka topics
USER_REGISTRATION_TOPIC = "user-registration-events"

class KafkaClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KafkaClient, cls).__new__(cls)
            bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
            cls._instance.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k is not None else None
            )
            print(f"Kafka producer initialized with bootstrap servers: {bootstrap_servers}")
        return cls._instance
    
    def send_user_registration_event(self, user_id: int, registration_date: datetime):
        """Send a user registration event to Kafka"""
        # Convert datetime to string for JSON serialization
        event_dict = {
            "user_id": user_id,
            "registration_date": registration_date.isoformat()
        }
        
        try:
            future = self.producer.send(
                USER_REGISTRATION_TOPIC,
                key=user_id,
                value=event_dict
            )
            # Wait for the message to be delivered
            record_metadata = future.get(timeout=10)
            print(f"User registration event sent to Kafka: {event_dict}")
            print(f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
        except Exception as e:
            print(f"Error sending user registration event to Kafka: {e}")
            return False

# Create a singleton instance
kafka_client = KafkaClient()
