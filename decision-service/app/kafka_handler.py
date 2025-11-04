import json
import logging
import os
import sys
from typing import Callable

from kafka import KafkaConsumer

from database import SessionLocal

# Add parent directory to path to import database package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)


class DecisionKafkaHandler:
    """
    Kafka handler for Decision Service.
    Consumes from credit_reports_generated topic.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        consumer_group: str = "decision-service-group",
        consume_topic: str = "credit_reports_generated",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.consume_topic = consume_topic
        self.consumer = None

    def connect(self):
        """
        Connect to Kafka broker and initialize consumer.
        """
        try:
            self.consumer = KafkaConsumer(
                self.consume_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                max_poll_interval_ms=300000,
            )

            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            logger.info(f"Consuming from topic: {self.consume_topic}")
            logger.info(f"Consumer group: {self.consumer_group}")

        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def consume_and_process(self, message_handler: Callable):
        """
        Consume messages from Kafka and process them with the provided handler.

        The handler receives both the message and a database session.

        Args:
            message_handler: Function to process each message with signature:
                            message_handler(message: dict, db_session: Session)
        """
        if not self.consumer:
            raise RuntimeError("Kafka consumer not connected. Call connect() first.")

        logger.info("Starting to consume messages from Kafka...")

        try:
            for message in self.consumer:
                db_session = SessionLocal()
                try:
                    logger.info(
                        f"Received message from topic {message.topic}, partition {message.partition}, offset {message.offset}"
                    )
                    logger.debug(f"Message key: {message.key}, value: {message.value}")

                    # Process the message using the handler with database session
                    message_handler(message.value, db_session)

                    # Commit the database transaction
                    db_session.commit()

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    db_session.rollback()
                    # Continue processing other messages
                finally:
                    db_session.close()

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}", exc_info=True)
            raise

    def close(self):
        """
        Close Kafka consumer connection.
        """
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
