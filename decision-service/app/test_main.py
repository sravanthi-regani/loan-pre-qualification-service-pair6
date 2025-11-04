import os
import sys
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from main import process_credit_report

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestProcessCreditReport:
    """Test cases for the process_credit_report function."""

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_pre_approved(self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report):
        """Test processing credit report that results in PRE_APPROVED."""
        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        process_credit_report(sample_credit_report, db_session)

        # Verify decision engine was called
        mock_decision.assert_called_once_with(cibil_score=750, monthly_income=50000.0, loan_amount=500000.0)

        # Verify database update
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert isinstance(call_args[0][1], UUID)  # application_id is UUID
        assert call_args[1]["status"] == "PRE_APPROVED"
        assert call_args[1]["cibil_score"] == 750

        # Verify sleep was called (1 minute delay)
        mock_sleep.assert_called_once_with(60)

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_rejected(self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report):
        """Test processing credit report that results in REJECTED."""
        mock_decision.return_value = "REJECTED"
        mock_update.return_value = MagicMock()
        sample_credit_report["cibil_score"] = 600

        process_credit_report(sample_credit_report, db_session)

        mock_decision.assert_called_once_with(cibil_score=600, monthly_income=50000.0, loan_amount=500000.0)

        # Verify database update
        call_args = mock_update.call_args
        assert call_args[1]["status"] == "REJECTED"
        assert call_args[1]["cibil_score"] == 600

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_manual_review(self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report):
        """Test processing credit report that results in MANUAL_REVIEW."""
        mock_decision.return_value = "MANUAL_REVIEW"
        mock_update.return_value = MagicMock()
        sample_credit_report["cibil_score"] = 750
        sample_credit_report["monthly_income"] = 10000.0

        process_credit_report(sample_credit_report, db_session)

        mock_decision.assert_called_once_with(cibil_score=750, monthly_income=10000.0, loan_amount=500000.0)

        call_args = mock_update.call_args
        assert call_args[1]["status"] == "MANUAL_REVIEW"

    # @patch('main.time.sleep')
    # @patch('main.DecisionEngine.make_decision')
    # @patch('main.ApplicationCRUD.update_application_status')
    # def test_process_credit_report_application_not_found(
    #     self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report
    # ):
    #     """Test processing when application doesn't exist in database."""
    #     mock_decision.return_value = "PRE_APPROVED"
    #     mock_update.return_value = None  # Simulate not found
    #
    #     # Should not raise exception, just log warning
    #     process_credit_report(sample_credit_report, db_session)
    #
    #     # Verify decision was still made
    #     mock_decision.assert_called_once()
    #     mock_update.assert_called_once()

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_decision_engine_error(
        self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report
    ):
        """Test handling of decision engine errors."""
        mock_decision.side_effect = Exception("Decision engine error")

        # Should not raise exception, just log error
        process_credit_report(sample_credit_report, db_session)

        # Update should not be called due to error
        mock_update.assert_not_called()

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_database_error(self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report):
        """Test handling of database update errors."""
        mock_decision.return_value = "PRE_APPROVED"
        mock_update.side_effect = Exception("Database error")

        # Should not raise exception, just log error
        process_credit_report(sample_credit_report, db_session)

        # Decision should still have been called
        mock_decision.assert_called_once()

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_extracts_correct_fields(self, mock_update, mock_decision, mock_sleep, db_session):
        """Test that correct fields are extracted from message."""
        message = {
            "application_id": "123e4567-e89b-12d3-a456-426614174000",
            "cibil_score": 780,
            "monthly_income": 75000.0,
            "loan_amount": 1500000.0,
            "extra_field": "ignored",
        }

        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        process_credit_report(message, db_session)

        # Verify correct values were passed
        mock_decision.assert_called_once_with(cibil_score=780, monthly_income=75000.0, loan_amount=1500000.0)

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_various_decisions(
        self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_reports
    ):
        """Test processing multiple credit reports with different decisions."""
        decisions = ["PRE_APPROVED", "REJECTED", "MANUAL_REVIEW"]
        mock_update.return_value = MagicMock()

        for i, report in enumerate(sample_credit_reports):
            mock_decision.return_value = decisions[i]
            process_credit_report(report, db_session)

        # Verify all were processed
        assert mock_decision.call_count == 3
        assert mock_update.call_count == 3

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_high_cibil_high_income(self, mock_update, mock_decision, mock_sleep, db_session):
        """Test processing with high CIBIL and high income."""
        message = {
            "application_id": str(uuid4()),
            "cibil_score": 850,
            "monthly_income": 200000.0,
            "loan_amount": 5000000.0,
        }

        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        process_credit_report(message, db_session)

        mock_decision.assert_called_once_with(cibil_score=850, monthly_income=200000.0, loan_amount=5000000.0)

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_low_cibil(self, mock_update, mock_decision, mock_sleep, db_session):
        """Test processing with low CIBIL score."""
        message = {
            "application_id": str(uuid4()),
            "cibil_score": 500,
            "monthly_income": 50000.0,
            "loan_amount": 500000.0,
        }

        mock_decision.return_value = "REJECTED"
        mock_update.return_value = MagicMock()

        process_credit_report(message, db_session)

        call_args = mock_update.call_args
        assert call_args[1]["status"] == "REJECTED"
        assert call_args[1]["cibil_score"] == 500

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_both_cibil_and_status_updated(
        self, mock_update, mock_decision, mock_sleep, db_session, sample_credit_report
    ):
        """Test that both status and CIBIL score are updated in database."""
        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        process_credit_report(sample_credit_report, db_session)

        # Verify both parameters are passed to update
        call_args = mock_update.call_args
        assert "status" in call_args[1]
        assert "cibil_score" in call_args[1]
        assert call_args[1]["status"] == "PRE_APPROVED"
        assert call_args[1]["cibil_score"] == 750

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_edge_case_cibil_at_threshold(self, mock_update, mock_decision, mock_sleep, db_session):
        """Test processing with CIBIL score at decision threshold."""
        message = {
            "application_id": str(uuid4()),
            "cibil_score": 650,  # At threshold
            "monthly_income": 50000.0,
            "loan_amount": 500000.0,
        }

        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        process_credit_report(message, db_session)

        mock_decision.assert_called_once_with(cibil_score=650, monthly_income=50000.0, loan_amount=500000.0)

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_data_types(self, mock_update, mock_decision, mock_sleep, db_session):
        """Test that correct data types are used in processing."""
        message = {
            "application_id": "123e4567-e89b-12d3-a456-426614174000",
            "cibil_score": 750,  # int
            "monthly_income": 50000.0,  # float
            "loan_amount": 500000.0,  # float
        }

        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        process_credit_report(message, db_session)

        call_args = mock_decision.call_args
        assert isinstance(call_args[1]["cibil_score"], int)
        assert isinstance(call_args[1]["monthly_income"], float)
        assert isinstance(call_args[1]["loan_amount"], float)

    @patch("main.time.sleep")
    @patch("main.DecisionEngine.make_decision")
    @patch("main.ApplicationCRUD.update_application_status")
    def test_process_credit_report_missing_optional_fields(self, mock_update, mock_decision, mock_sleep, db_session):
        """Test processing with only required fields."""
        message = {
            "application_id": str(uuid4()),
            "cibil_score": 750,
            "monthly_income": 50000.0,
            "loan_amount": 500000.0,
        }

        mock_decision.return_value = "PRE_APPROVED"
        mock_update.return_value = MagicMock()

        # Should process successfully
        process_credit_report(message, db_session)

        mock_decision.assert_called_once()
        mock_update.assert_called_once()
