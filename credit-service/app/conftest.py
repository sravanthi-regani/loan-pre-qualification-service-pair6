from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def mock_kafka_handler():
    """Mock Kafka handler for testing."""
    with patch("main.kafka_handler") as mock_handler:
        mock_handler.connect = MagicMock()
        mock_handler.consume_and_process = MagicMock()
        mock_handler.close = MagicMock()
        yield mock_handler


@pytest.fixture(scope="function")
def client():
    """Create a test client for the FastAPI app."""
    import main

    # Use TestClient without triggering lifespan events
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def sample_loan_application():
    """Sample loan application message for testing."""
    return {
        "application_id": "123e4567-e89b-12d3-a456-426614174000",
        "pan_number": "ABCDE1234F",
        "applicant_name": "John Doe",
        "monthly_income": 50000.0,
        "loan_amount": 500000.0,
        "loan_type": "PERSONAL",
        "status": "PENDING",
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_loan_applications():
    """Multiple sample loan applications for testing."""
    return [
        {
            "application_id": "123e4567-e89b-12d3-a456-426614174001",
            "pan_number": "ABCDE1234F",
            "applicant_name": "John Doe",
            "monthly_income": 50000.0,
            "loan_amount": 500000.0,
            "loan_type": "PERSONAL",
            "status": "PENDING",
        },
        {
            "application_id": "123e4567-e89b-12d3-a456-426614174002",
            "pan_number": "FGHIJ5678K",
            "applicant_name": "Jane Smith",
            "monthly_income": 80000.0,
            "loan_amount": 5000000.0,
            "loan_type": "HOME",
            "status": "PENDING",
        },
        {
            "application_id": "123e4567-e89b-12d3-a456-426614174003",
            "pan_number": "XYZAB9012C",
            "applicant_name": "Bob Johnson",
            "monthly_income": 25000.0,
            "loan_amount": 800000.0,
            "loan_type": "AUTO",
            "status": "PENDING",
        },
    ]
