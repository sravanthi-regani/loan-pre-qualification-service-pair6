from unittest.mock import patch

from main import process_loan_application


class TestProcessLoanApplication:
    """Test cases for the process_loan_application function."""

    @patch("main.CIBILSimulator.calculate_cibil_score")
    def test_process_loan_application_success(self, mock_calculate, sample_loan_application):
        """Test successful loan application processing."""
        mock_calculate.return_value = 750

        result = process_loan_application(sample_loan_application)

        # Verify CIBIL calculator was called with correct parameters
        mock_calculate.assert_called_once_with(
            pan_number=sample_loan_application["pan_number"],
            monthly_income=sample_loan_application["monthly_income"],
            loan_type=sample_loan_application["loan_type"],
        )

        # Verify result contains all original data plus CIBIL score
        assert result["application_id"] == sample_loan_application["application_id"]
        assert result["pan_number"] == sample_loan_application["pan_number"]
        assert result["applicant_name"] == sample_loan_application["applicant_name"]
        assert result["monthly_income"] == sample_loan_application["monthly_income"]
        assert result["loan_amount"] == sample_loan_application["loan_amount"]
        assert result["loan_type"] == sample_loan_application["loan_type"]
        assert result["cibil_score"] == 750
        assert "credit_check_completed_at" in result

    @patch("main.CIBILSimulator.calculate_cibil_score")
    def test_process_loan_application_with_test_pan(self, mock_calculate, sample_loan_application):
        """Test processing with predefined test PAN."""
        mock_calculate.return_value = 790
        sample_loan_application["pan_number"] = "ABCDE1234F"

        result = process_loan_application(sample_loan_application)

        assert result["cibil_score"] == 790
        assert result["pan_number"] == "ABCDE1234F"

    @patch("main.CIBILSimulator.calculate_cibil_score")
    def test_process_loan_application_forwards_all_fields(self, mock_calculate, sample_loan_application):
        """Test that all fields from original message are forwarded."""
        mock_calculate.return_value = 700

        # Add extra fields to test forwarding
        sample_loan_application["extra_field"] = "extra_value"
        sample_loan_application["another_field"] = 123

        result = process_loan_application(sample_loan_application)

        # All original fields should be present
        for key, value in sample_loan_application.items():
            assert key in result
            assert result[key] == value

        # Plus the new fields
        assert result["cibil_score"] == 700
        assert "credit_check_completed_at" in result

    @patch("main.CIBILSimulator.calculate_cibil_score")
    def test_process_loan_application_error_handling(self, mock_calculate, sample_loan_application):
        """Test error handling when CIBIL calculation fails."""
        mock_calculate.side_effect = Exception("CIBIL service unavailable")

        result = process_loan_application(sample_loan_application)

        # Result should contain error information
        assert result["cibil_score"] is None
        assert "error" in result
        assert "CIBIL service unavailable" in result["error"]
        assert "credit_check_completed_at" in result

        # Original data should still be present
        assert result["application_id"] == sample_loan_application["application_id"]
        assert result["pan_number"] == sample_loan_application["pan_number"]

    @patch("main.CIBILSimulator.calculate_cibil_score")
    def test_process_loan_application_various_loan_types(self, mock_calculate, sample_loan_application):
        """Test processing applications with different loan types."""
        loan_types_and_scores = [
            ("PERSONAL", 640),
            ("HOME", 660),
            ("AUTO", 650),
            ("BUSINESS", 650),
        ]

        for loan_type, expected_score in loan_types_and_scores:
            mock_calculate.return_value = expected_score
            sample_loan_application["loan_type"] = loan_type

            result = process_loan_application(sample_loan_application)

            assert result["loan_type"] == loan_type
            assert result["cibil_score"] == expected_score
