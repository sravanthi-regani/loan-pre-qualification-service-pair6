from uuid import uuid4

from fastapi import status

from database.crud import ApplicationCRUD


class TestCreateApplication:
    """Test cases for creating loan applications."""

    def test_create_application_success(self, client, sample_application_data, mock_kafka_producer):
        """Test successful creation of a loan application."""
        response = client.post("/applications", json=sample_application_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "application_id" in data
        assert data["status"] == "PENDING"

        # Verify Kafka producer was called
        mock_kafka_producer.send_message.assert_called_once()
        call_args = mock_kafka_producer.send_message.call_args
        assert call_args.kwargs["topic"] == "loan_applications_submitted"

    def test_create_application_with_all_loan_types(self, client, mock_kafka_producer):
        """Test creating applications with all supported loan types."""
        loan_types = ["personal", "home", "auto", "business"]

        for loan_type in loan_types:
            application_data = {
                "applicant_name": f"Test User {loan_type}",
                "pan_number": "ABCDE1234F",
                "loan_type": loan_type,
                "loan_amount": 500000.0,
                "monthly_income": 50000.0,
            }
            response = client.post("/applications", json=application_data)
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert data["status"] == "PENDING"

    def test_create_application_invalid_pan_format(self, client):
        """Test application creation with invalid PAN number format."""
        invalid_pan_data = {
            "applicant_name": "John Doe",
            "pan_number": "INVALID123",  # Invalid format
            "loan_type": "personal",
            "loan_amount": 500000.0,
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=invalid_pan_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_invalid_loan_type(self, client):
        """Test application creation with invalid loan type."""
        invalid_loan_type_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "invalid_type",
            "loan_amount": 500000.0,
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=invalid_loan_type_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_zero_loan_amount(self, client):
        """Test application creation with zero loan amount."""
        zero_amount_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": 0.0,
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=zero_amount_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_negative_loan_amount(self, client):
        """Test application creation with negative loan amount."""
        negative_amount_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": -100000.0,
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=negative_amount_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_excessive_loan_amount(self, client):
        """Test application creation with loan amount exceeding maximum."""
        excessive_amount_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": 200000000.0,  # Exceeds 100000000 limit
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=excessive_amount_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_zero_monthly_income(self, client):
        """Test application creation with zero monthly income."""
        zero_income_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": 500000.0,
            "monthly_income": 0.0,
        }
        response = client.post("/applications", json=zero_income_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_negative_monthly_income(self, client):
        """Test application creation with negative monthly income."""
        negative_income_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": 500000.0,
            "monthly_income": -50000.0,
        }
        response = client.post("/applications", json=negative_income_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_short_name(self, client):
        """Test application creation with name too short."""
        short_name_data = {
            "applicant_name": "J",  # Less than 2 characters
            "pan_number": "ABCDE1234F",
            "loan_type": "personal",
            "loan_amount": 500000.0,
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=short_name_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_missing_required_field(self, client):
        """Test application creation with missing required field."""
        incomplete_data = {
            "applicant_name": "John Doe",
            "pan_number": "ABCDE1234F",
            # Missing loan_type
            "loan_amount": 500000.0,
            "monthly_income": 50000.0,
        }
        response = client.post("/applications", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_kafka_failure_continues(self, client, sample_application_data, mock_kafka_producer):
        """Test that application creation continues even if Kafka publish fails."""
        # Mock Kafka producer to raise exception
        mock_kafka_producer.send_message.side_effect = Exception("Kafka connection error")

        response = client.post("/applications", json=sample_application_data)

        # Application should still be created successfully
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "application_id" in data
        assert data["status"] == "PENDING"


class TestGetApplicationStatus:
    """Test cases for retrieving application status."""

    def test_get_application_status_success(self, client, db_session, sample_application_data):
        """Test successful retrieval of application status."""
        # First create an application
        create_response = client.post("/applications", json=sample_application_data)
        assert create_response.status_code == status.HTTP_202_ACCEPTED
        application_id = create_response.json()["application_id"]

        # Now retrieve its status
        response = client.get(f"/applications/{application_id}/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["application_id"] == application_id
        assert data["status"] == "PENDING"

    def test_get_application_status_not_found(self, client):
        """Test retrieval of non-existent application."""
        non_existent_id = str(uuid4())
        response = client.get(f"/applications/{non_existent_id}/status")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_application_status_invalid_uuid(self, client):
        """Test retrieval with invalid UUID format."""
        invalid_id = "not-a-valid-uuid"
        response = client.get(f"/applications/{invalid_id}/status")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()

    def test_get_application_status_after_update(self, client, db_session, sample_application_data):
        """Test that status changes are reflected in the API."""
        # Create an application
        create_response = client.post("/applications", json=sample_application_data)
        application_id = create_response.json()["application_id"]

        # Update the application status in the database
        from uuid import UUID

        ApplicationCRUD.update_application_status(
            db=db_session,
            application_id=UUID(application_id),
            status="PRE_APPROVED",
            cibil_score=750,
        )

        # Retrieve and verify the updated status
        response = client.get(f"/applications/{application_id}/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "PRE_APPROVED"
