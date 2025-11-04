import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Add root directory to path to import database module
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from database import get_db, Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Replace UUID type with GUID for SQLite compatibility
    from database import models
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if hasattr(column.type, '__class__') and column.type.__class__.__name__ == 'UUID':
                column.type = GUID()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def mock_kafka_handler():
    """Mock Kafka handler for testing."""
    with patch('main.kafka_handler') as mock_handler:
        mock_handler.connect = MagicMock()
        mock_handler.consume_and_process = MagicMock()
        mock_handler.close = MagicMock()
        yield mock_handler


@pytest.fixture(scope="function")
def client():
    """Create a test client for the FastAPI app."""
    import main

    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def sample_credit_report():
    """Sample credit report message for testing."""
    return {
        "application_id": "123e4567-e89b-12d3-a456-426614174000",
        "pan_number": "ABCDE1234F",
        "applicant_name": "John Doe",
        "monthly_income": 50000.0,
        "loan_amount": 500000.0,
        "loan_type": "PERSONAL",
        "status": "PENDING",
        "cibil_score": 750,
        "credit_check_completed_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_credit_reports():
    """Multiple sample credit reports for testing."""
    return [
        {
            "application_id": "123e4567-e89b-12d3-a456-426614174001",
            "pan_number": "ABCDE1234F",
            "applicant_name": "John Doe",
            "monthly_income": 50000.0,
            "loan_amount": 500000.0,
            "loan_type": "PERSONAL",
            "cibil_score": 750,
        },
        {
            "application_id": "123e4567-e89b-12d3-a456-426614174002",
            "pan_number": "FGHIJ5678K",
            "applicant_name": "Jane Smith",
            "monthly_income": 80000.0,
            "loan_amount": 5000000.0,
            "loan_type": "HOME",
            "cibil_score": 600,
        },
        {
            "application_id": "123e4567-e89b-12d3-a456-426614174003",
            "pan_number": "XYZAB9012C",
            "applicant_name": "Bob Johnson",
            "monthly_income": 150000.0,
            "loan_amount": 3000000.0,
            "loan_type": "HOME",
            "cibil_score": 800,
        }
    ]
