import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Add root directory to path to import database module
# Path structure: loan-pre-qualification-service-pair6/prequal-api/app/conftest.py
# Database is at: loan-pre-qualification-service-pair6/database
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
def mock_kafka_producer():
    """Mock Kafka producer for testing."""
    with patch('main.kafka_producer') as mock_producer:
        mock_producer.connect = MagicMock()
        mock_producer.send_message = MagicMock()
        mock_producer.close = MagicMock()
        yield mock_producer


@pytest.fixture(scope="function")
def client(db_session, mock_kafka_producer):
    """Create a test client with mocked dependencies."""
    import main

    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    main.app.dependency_overrides[get_db] = override_get_db

    # Create test client
    test_client = TestClient(main.app)

    yield test_client

    # Clean up
    main.app.dependency_overrides.clear()


@pytest.fixture
def sample_application_data():
    """Sample loan application data for testing."""
    return {
        "applicant_name": "John Doe",
        "pan_number": "ABCDE1234F",
        "loan_type": "personal",
        "loan_amount": 500000.0,
        "monthly_income": 50000.0
    }


@pytest.fixture
def sample_application_data_list():
    """Multiple sample loan applications for testing."""
    return [
        {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": 500000.0,
            "monthly_income": 50000.0
        },
        {
            "applicant_name": "Jane Smith",
            "pan_number": "XYZAB5678C",
            "loan_type": "home",
            "loan_amount": 5000000.0,
            "monthly_income": 150000.0
        },
        {
            "applicant_name": "Bob Johnson",
            "pan_number": "PQRST9012D",
            "loan_type": "auto",
            "loan_amount": 800000.0,
            "monthly_income": 75000.0
        }
    ]