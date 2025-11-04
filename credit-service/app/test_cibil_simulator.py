from unittest.mock import patch

from cibil_simulator import CIBILSimulator


class TestCIBILSimulator:
    """Test cases for CIBIL score calculation."""

    def test_predefined_test_pan_1(self):
        """Test that predefined test PAN ABCDE1234F returns score 790."""
        score = CIBILSimulator.calculate_cibil_score(pan_number="ABCDE1234F", monthly_income=50000, loan_type="PERSONAL")
        assert score == 790

    def test_predefined_test_pan_2(self):
        """Test that predefined test PAN FGHIJ5678K returns score 610."""
        score = CIBILSimulator.calculate_cibil_score(pan_number="FGHIJ5678K", monthly_income=50000, loan_type="PERSONAL")
        assert score == 610

    def test_predefined_pans_ignore_other_parameters(self):
        """Test that predefined PANs return fixed scores regardless of other parameters."""
        # Test PAN 1 with various parameters
        score1 = CIBILSimulator.calculate_cibil_score(pan_number="ABCDE1234F", monthly_income=100000, loan_type="HOME")
        assert score1 == 790

        score2 = CIBILSimulator.calculate_cibil_score(pan_number="ABCDE1234F", monthly_income=20000, loan_type="AUTO")
        assert score2 == 790

        # Test PAN 2 with various parameters
        score3 = CIBILSimulator.calculate_cibil_score(pan_number="FGHIJ5678K", monthly_income=100000, loan_type="HOME")
        assert score3 == 610

    @patch("cibil_simulator.random.randint")
    def test_base_score_calculation(self, mock_random):
        """Test base score calculation for non-test PAN."""
        mock_random.return_value = 0  # No random adjustment

        score = CIBILSimulator.calculate_cibil_score(
            pan_number="XYZAB9012C",
            monthly_income=50000,  # Normal income, no adjustment
            loan_type="AUTO",  # No specific adjustment
        )
        # Base score is 650, no adjustments
        assert score == 650

    @patch("cibil_simulator.random.randint")
    def test_high_income_bonus(self, mock_random):
        """Test that high income (>75000) adds 40 points."""
        mock_random.return_value = 0  # No random adjustment

        score = CIBILSimulator.calculate_cibil_score(
            pan_number="XYZAB9012C",
            monthly_income=80000,  # High income
            loan_type="AUTO",
        )
        # Base 650 + 40 (high income) = 690
        assert score == 690

    @patch("cibil_simulator.random.randint")
    def test_low_income_penalty(self, mock_random):
        """Test that low income (<30000) subtracts 20 points."""
        mock_random.return_value = 0  # No random adjustment

        score = CIBILSimulator.calculate_cibil_score(
            pan_number="XYZAB9012C",
            monthly_income=25000,  # Low income
            loan_type="AUTO",
        )
        # Base 650 - 20 (low income) = 630
        assert score == 630

    @patch("cibil_simulator.random.randint")
    def test_personal_loan_penalty(self, mock_random):
        """Test that personal loan (unsecured) subtracts 10 points."""
        mock_random.return_value = 0  # No random adjustment

        score = CIBILSimulator.calculate_cibil_score(pan_number="XYZAB9012C", monthly_income=50000, loan_type="PERSONAL")
        # Base 650 - 10 (personal loan) = 640
        assert score == 640

    @patch("cibil_simulator.random.randint")
    def test_home_loan_bonus(self, mock_random):
        """Test that home loan (secured) adds 10 points."""
        mock_random.return_value = 0  # No random adjustment

        score = CIBILSimulator.calculate_cibil_score(pan_number="XYZAB9012C", monthly_income=50000, loan_type="HOME")
        # Base 650 + 10 (home loan) = 660
        assert score == 660

    @patch("cibil_simulator.random.randint")
    def test_combined_high_income_and_home_loan(self, mock_random):
        """Test combined effect of high income and home loan."""
        mock_random.return_value = 0

        score = CIBILSimulator.calculate_cibil_score(
            pan_number="XYZAB9012C",
            monthly_income=80000,  # +40
            loan_type="HOME",  # +10
        )
        # Base 650 + 40 (income) + 10 (home) = 700
        assert score == 700

    @patch("cibil_simulator.random.randint")
    def test_score_within_valid_range(self, mock_random):
        """Test that calculated score is always within 300-900 range."""
        mock_random.return_value = 0

        # Test various scenarios
        test_cases = [
            (25000, "PERSONAL"),  # Low income + personal
            (80000, "HOME"),  # High income + home
            (50000, "AUTO"),  # Normal income + auto
            (100000, "BUSINESS"),  # Very high income
            (20000, "PERSONAL"),  # Very low income
        ]

        for income, loan_type in test_cases:
            score = CIBILSimulator.calculate_cibil_score(pan_number="XYZAB9012C", monthly_income=income, loan_type=loan_type)
            assert CIBILSimulator.MIN_SCORE <= score <= CIBILSimulator.MAX_SCORE
