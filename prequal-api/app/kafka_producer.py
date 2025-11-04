import json
import logging

from kafka import KafkaProducer

logger = logging.getLogger(__name__)


class PrequalKafkaProducer:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    def connect(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def send_message(self, topic: str, key: str, message: dict):
        if not self.producer:
            self.connect()
        try:
            future = self.producer.send(topic, key=key, value=message)
            result = future.get(timeout=10)
            logger.info(f"Message sent to topic {topic} with key {key}: partition={result.partition}, offset={result.offset}")
            return result
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            raise

    def close(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")


# Global producer instance
kafka_producer = PrequalKafkaProducer()
