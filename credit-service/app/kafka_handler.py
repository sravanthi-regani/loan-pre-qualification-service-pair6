from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class CreditKafkaHandler:
    """
    Kafka handler for Credit Service.
    Consumes from loan_applications_submitted topic and produces to credit-checks topic.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        consumer_group: str = "credit-service-group",
        consume_topic: str = "loan_applications_submitted",
        produce_topic: str = "credit-checks"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.consume_topic = consume_topic
        self.produce_topic = produce_topic
        self.consumer: Optional[KafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None

    def connect(self):
        """
        Connect to Kafka broker and initialize consumer and producer.
        """
        try:
            # Initialize consumer
            self.consumer = KafkaConsumer(
                self.consume_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_interval_ms=300000
            )

            # Initialize producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )

            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            logger.info(f"Consuming from topic: {self.consume_topic}")
            logger.info(f"Producing to topic: {self.produce_topic}")
            logger.info(f"Consumer group: {self.consumer_group}")

        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def consume_and_process(self, message_handler: Callable[[dict], dict]):
        """
        Consume messages from Kafka and process them with the provided handler.

        Args:
            message_handler: Function to process each message and return result
        """
        if not self.consumer or not self.producer:
            raise RuntimeError("Kafka consumer/producer not connected. Call connect() first.")

        logger.info("Starting to consume messages from Kafka...")

        try:
            for message in self.consumer:
                try:
                    logger.info(
                        f"Received message from topic {message.topic}, "
                        f"partition {message.partition}, offset {message.offset}"
                    )
                    logger.debug(f"Message key: {message.key}, value: {message.value}")

                    # Process the message using the handler
                    result = message_handler(message.value)

                    # Publish result to output topic if handler returned something
                    if result:
                        self._publish_result(result)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing other messages

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}", exc_info=True)
            raise

    def _publish_result(self, result: dict):
        """
        Publish result to the output Kafka topic.

        Args:
            result: Dictionary to publish
        """
        try:
            application_id = result.get("application_id")

            future = self.producer.send(
                self.produce_topic,
                key=application_id,
                value=result
            )

            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)

            logger.info(
                f"Published credit report for application {application_id} "
                f"to topic {self.produce_topic}, "
                f"partition {record_metadata.partition}, "
                f"offset {record_metadata.offset}"
            )

        except Exception as e:
            logger.error(f"Failed to publish result to Kafka: {e}", exc_info=True)
            raise

    def close(self):
        """
        Close Kafka consumer and producer connections.
        """
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")

        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")