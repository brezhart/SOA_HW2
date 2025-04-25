import json
import os
from datetime import datetime
from kafka import KafkaProducer
from app.schemas import UserRegistrationEvent, PostViewEvent, PostLikeEvent, PostCommentEvent

# Kafka topics
USER_REGISTRATION_TOPIC = "user-registration-events"
POST_VIEW_TOPIC = "post-view-events"
POST_LIKE_TOPIC = "post-like-events"
POST_COMMENT_TOPIC = "post-comment-events"

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
        event = UserRegistrationEvent(
            user_id=user_id,
            registration_date=registration_date
        )
        
        event_dict = {
            "user_id": event.user_id,
            "registration_date": event.registration_date.isoformat()
        }
        
        try:
            future = self.producer.send(
                USER_REGISTRATION_TOPIC,
                key=user_id,
                value=event_dict
            )
            record_metadata = future.get(timeout=10)
            print(f"User registration event sent to Kafka: {event_dict}")
            print(f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
        except Exception as e:
            print(f"Error sending user registration event to Kafka: {e}")
            return False
    
    def send_post_view_event(self, user_id: int, post_id: int, view_date: datetime):
        """Send a post view event to Kafka"""
        event = PostViewEvent(
            user_id=user_id,
            post_id=post_id,
            view_date=view_date
        )
        
        event_dict = {
            "user_id": event.user_id,
            "post_id": event.post_id,
            "view_date": event.view_date.isoformat()
        }
        
        try:
            future = self.producer.send(
                POST_VIEW_TOPIC,
                key=f"{post_id}-{user_id}",
                value=event_dict
            )
            record_metadata = future.get(timeout=10)
            print(f"Post view event sent to Kafka: {event_dict}")
            print(f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
        except Exception as e:
            print(f"Error sending post view event to Kafka: {e}")
            return False
    
    def send_post_like_event(self, user_id: int, post_id: int, like_date: datetime, is_like: bool):
        """Send a post like event to Kafka"""
        event = PostLikeEvent(
            user_id=user_id,
            post_id=post_id,
            like_date=like_date,
            is_like=is_like
        )
        
        event_dict = {
            "user_id": event.user_id,
            "post_id": event.post_id,
            "like_date": event.like_date.isoformat(),
            "is_like": event.is_like
        }
        
        try:
            future = self.producer.send(
                POST_LIKE_TOPIC,
                key=f"{post_id}-{user_id}",
                value=event_dict
            )
            record_metadata = future.get(timeout=10)
            print(f"Post like event sent to Kafka: {event_dict}")
            print(f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
        except Exception as e:
            print(f"Error sending post like event to Kafka: {e}")
            return False
    
    def send_post_comment_event(self, user_id: int, post_id: int, comment_id: int, comment_date: datetime):
        """Send a post comment event to Kafka"""
        event = PostCommentEvent(
            user_id=user_id,
            post_id=post_id,
            comment_id=comment_id,
            comment_date=comment_date
        )
        
        event_dict = {
            "user_id": event.user_id,
            "post_id": event.post_id,
            "comment_id": event.comment_id,
            "comment_date": event.comment_date.isoformat()
        }
        
        try:
            future = self.producer.send(
                POST_COMMENT_TOPIC,
                key=f"{post_id}-{user_id}-{comment_id}",
                value=event_dict
            )
            # Wait for the message to be delivered
            record_metadata = future.get(timeout=10)
            print(f"Post comment event sent to Kafka: {event_dict}")
            print(f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
        except Exception as e:
            print(f"Error sending post comment event to Kafka: {e}")
            return False

kafka_client = KafkaClient()
