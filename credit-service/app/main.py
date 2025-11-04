import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from cibil_simulator import CIBILSimulator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka_handler import CreditKafkaHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global Kafka handler
kafka_handler = None


def process_loan_application(message: dict) -> dict:
    """
    Process loan application message and calculate CIBIL score.

    Args:
        message: Loan application data from Kafka

    Returns:
        Credit report with CIBIL score to be published to credit_reports_generated topic
    """
    try:
        application_id = message.get("application_id")
        pan_number = message.get("pan_number")
        monthly_income = message.get("monthly_income")
        loan_type = message.get("loan_type")

        logger.info(f"Processing CIBIL calculation for application {application_id}, PAN: {pan_number}")

        # Calculate CIBIL score
        cibil_score = CIBILSimulator.calculate_cibil_score(
            pan_number=pan_number, monthly_income=monthly_income, loan_type=loan_type
        )

        logger.info(f"Calculated CIBIL score {cibil_score} for application {application_id}")

        # Create credit report with CIBIL score and forward all application data
        credit_report = {
            **message,  # Forward all original application data
            "cibil_score": cibil_score,
            "credit_check_completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"CIBIL score {cibil_score} calculated for application {application_id}, publishing to credit_reports_generated"
        )

        return credit_report

    except Exception as e:
        logger.error(f"Error calculating CIBIL score: {e}", exc_info=True)

        # Return error with original message data
        return {
            **message,
            "cibil_score": None,
            "error": str(e),
            "credit_check_completed_at": datetime.now(timezone.utc).isoformat(),
        }


def start_kafka_consumer():
    """
    Start Kafka consumer in background thread.
    """
    global kafka_handler

    logger.info("Starting Credit Service Kafka Consumer...")

    try:
        kafka_handler = CreditKafkaHandler(
            bootstrap_servers="localhost:9092",
            consumer_group="credit-service-group",
            consume_topic="loan_applications_submitted",
            produce_topic="credit_reports_generated",
        )

        kafka_handler.connect()
        logger.info("Kafka consumer connected successfully")

        # Start consuming messages
        kafka_handler.consume_and_process(process_loan_application)

    except KeyboardInterrupt:
        logger.info("Shutting down Kafka consumer...")
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}", exc_info=True)
    finally:
        if kafka_handler:
            kafka_handler.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Credit Service API...")

    # Start Kafka consumer in a separate daemon thread
    consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    consumer_thread.start()

    logger.info("Credit Service API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Credit Service...")
    global kafka_handler
    if kafka_handler:
        kafka_handler.close()


app = FastAPI(
    title="Credit Service",
    description="Microservice for performing credit checks and CIBIL score simulation",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "Credit Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Credit Check and CIBIL Score Simulation Service",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "credit-service",
        "kafka_connected": kafka_handler is not None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
