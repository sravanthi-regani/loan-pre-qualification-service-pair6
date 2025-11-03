from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from decimal import Decimal
import logging
import sys
import os

# Add parent directory to path to import database package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import get_db, init_db
from database.crud import ApplicationCRUD

from pydantic_schemas import LoanApplicationRequest, LoanApplicationResponse
from kafka_producer import kafka_producer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Prequal API Service...")
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")

        # Connect to Kafka
        kafka_producer.connect()
        logger.info("Kafka producer connected successfully")

        logger.info("Prequal API Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Prequal API Service: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Prequal API Service...")
    kafka_producer.close()
    logger.info("Prequal API Service shut down successfully")


app = FastAPI(
    title="Prequal API",
    description="Loan Pre-Qualification API - Main entry point for loan applications",
    version="1.0.0",
    lifespan=lifespan
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
        "service": "Prequal API",
        "status": "running",
        "version": "1.0.0",
        "description": "Loan Pre-Qualification Service"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "prequal-api"
    }


@app.post("/applications", response_model=LoanApplicationResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_application(
    application_request: LoanApplicationRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new loan application.

    This endpoint:
    1. Validates the application data
    2. Saves the application to the database with PENDING status
    3. Publishes the application details to Kafka topic 'loan_applications_submitted'
    4. Returns the application ID and status

    The application will be processed asynchronously by:
    - Credit Service (for credit checks)
    - Decision Service (for final pre-qualification decision)
    """
    try:
        logger.info(f"Received loan application from {application_request.applicant_name} "
                   f"for PAN: {application_request.pan_number}")

        # Create application in database
        application = ApplicationCRUD.create_application(
            db=db,
            pan_number=application_request.pan_number,
            applicant_name=application_request.applicant_name,
            monthly_income_inr=Decimal(str(application_request.monthly_income)),
            loan_amount_inr=Decimal(str(application_request.loan_amount)),
            loan_type=application_request.loan_type.value.upper(),
            status="PENDING"
        )

        logger.info(f"Application created in database with ID: {application.id}")

        # Prepare Kafka message
        kafka_message = {
            "application_id": str(application.id),
            "pan_number": application.pan_number,
            "applicant_name": application.applicant_name,
            "monthly_income": float(application.monthly_income_inr),
            "loan_amount": float(application.loan_amount_inr),
            "loan_type": application.loan_type,
            "status": application.status,
            "created_at": application.created_at.isoformat()
        }

        # Publish to Kafka
        try:
            kafka_producer.send_message(
                topic="loan_applications_submitted",
                key=str(application.id),
                message=kafka_message
            )
            logger.info(f"Application {application.id} published to Kafka successfully")
        except Exception as kafka_error:
            logger.error(f"Failed to publish to Kafka: {kafka_error}")
            # Continue even if Kafka publish fails - application is already in DB
            # In production, you might want to implement a retry mechanism

        return LoanApplicationResponse(
            application_id=str(application.id),
            status=application.status
        )

    except Exception as e:
        logger.error(f"Error creating loan application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing application: {str(e)}"
        )


@app.get("/applications/{application_id}/status", response_model=LoanApplicationResponse, status_code=status.HTTP_200_OK)
async def get_application_status(
    application_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current status of a loan application by ID.

    Args:
        application_id: UUID of the application

    Returns:
        Application ID and current status
    """
    try:
        # Fetch application from database
        from uuid import UUID
        application_uuid = UUID(application_id)

        application = ApplicationCRUD.get_application_by_id(db, application_uuid)

        if not application:
            logger.warning(f"Application not found: {application_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )

        logger.info(f"Retrieved status for application {application_id}: {application.status}")

        return LoanApplicationResponse(
            application_id=str(application.id),
            status=application.status
        )

    except ValueError:
        logger.error(f"Invalid UUID format: {application_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid application ID format: {application_id}"
        )
    except Exception as e:
        logger.error(f"Error fetching application status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching application status: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)