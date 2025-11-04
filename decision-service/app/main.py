import logging
import os
import sys
import threading
import time
from contextlib import asynccontextmanager

from decision_engine import DecisionEngine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka_handler import DecisionKafkaHandler
from sqlalchemy.orm import Session

from database import init_db
from database.crud import ApplicationCRUD

# Add parent directory to path to import database package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global Kafka handler
kafka_handler = None


def process_credit_report(message: dict, db_session: Session) -> None:
    """
    Process credit report message and make decision.

    Args:
        message: Credit report data from Kafka
        db_session: Database session
    """
    try:
        application_id = message.get("application_id")
        cibil_score = message.get("cibil_score")
        monthly_income = message.get("monthly_income")
        loan_amount = message.get("loan_amount")

        logger.info(
            f"Processing decision for application {application_id}, "
            f"CIBIL: {cibil_score}, Income: {monthly_income}, Loan: {loan_amount}"
        )

        # Check if CIBIL score is available
        if cibil_score is None:
            logger.error(f"CIBIL score not available for application {application_id}")
            # Update status to indicate failure
            from uuid import UUID

            ApplicationCRUD.update_application_status(db_session, UUID(application_id), status="MANUAL_REVIEW")
            return

        # sleep for 1 min before updating the application status
        time.sleep(60)

        # Apply decision engine rules
        decision_status = DecisionEngine.make_decision(
            cibil_score=cibil_score,
            monthly_income=monthly_income,
            loan_amount=loan_amount,
        )

        logger.info(f"Decision for application {application_id}: {decision_status}")

        # Update database with decision and CIBIL score
        from uuid import UUID

        updated_application = ApplicationCRUD.update_application_status(
            db_session,
            UUID(application_id),
            status=decision_status,
            cibil_score=cibil_score,
        )

        if updated_application:
            logger.info(f"Database updated for application {application_id}: status={decision_status}, cibil_score={cibil_score}")
        else:
            logger.warning(f"Application {application_id} not found in database")

    except Exception as e:
        logger.error(f"Error processing credit report: {e}", exc_info=True)


def start_kafka_consumer():
    """
    Start Kafka consumer in background thread.
    """
    global kafka_handler

    logger.info("Starting Decision Service Kafka Consumer...")

    try:
        kafka_handler = DecisionKafkaHandler(
            bootstrap_servers=None,  # Will use KAFKA_BOOTSTRAP_SERVERS env var
            consumer_group="decision-service-group",
            consume_topic="credit_reports_generated",
        )

        kafka_handler.connect()
        logger.info("Kafka consumer connected successfully")

        # Start consuming messages with database session injection
        kafka_handler.consume_and_process(process_credit_report)

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
    logger.info("Starting Decision Service API...")

    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Start Kafka consumer in a separate daemon thread
    consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    consumer_thread.start()

    logger.info("Decision Service API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Decision Service...")
    global kafka_handler
    if kafka_handler:
        kafka_handler.close()


app = FastAPI(
    title="Decision Service",
    description="Microservice for making loan pre-qualification decisions",
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
        "service": "Decision Service",
        "status": "running",
        "version": "1.0.0",
        "description": "Loan Pre-Qualification Decision Service",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "decision-service",
        "kafka_connected": kafka_handler is not None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
