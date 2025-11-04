from decision_engine import DecisionEngine


class TestDecisionEngine:
    """Test cases for loan pre-qualification decision logic."""

    def test_rejected_low_cibil_score(self):
        """Test that CIBIL score < 650 results in REJECTED."""
        decision = DecisionEngine.make_decision(cibil_score=600, monthly_income=50000, loan_amount=500000)
        assert decision == "REJECTED"

    def test_rejected_very_low_cibil_score(self):
        """Test that very low CIBIL score results in REJECTED."""
        decision = DecisionEngine.make_decision(cibil_score=300, monthly_income=100000, loan_amount=500000)
        assert decision == "REJECTED"

    def test_rejected_cibil_just_below_threshold(self):
        """Test CIBIL score just below 650 threshold."""
        decision = DecisionEngine.make_decision(cibil_score=649, monthly_income=50000, loan_amount=500000)
        assert decision == "REJECTED"

    def test_rejected_regardless_of_income(self):
        """Test that low CIBIL results in REJECTED even with high income."""
        # Very high income but low CIBIL
        decision = DecisionEngine.make_decision(cibil_score=600, monthly_income=1000000, loan_amount=500000)
        assert decision == "REJECTED"

    def test_pre_approved_good_cibil_sufficient_income(self):
        """Test PRE_APPROVED with CIBIL >= 650 and sufficient income."""
        # Income 50000, required = 500000/48 = 10416.67
        # 50000 > 10416.67, so PRE_APPROVED
        decision = DecisionEngine.make_decision(cibil_score=750, monthly_income=50000, loan_amount=500000)
        assert decision == "PRE_APPROVED"

    def test_pre_approved_excellent_cibil_high_income(self):
        """Test PRE_APPROVED with excellent CIBIL and high income."""
        decision = DecisionEngine.make_decision(cibil_score=850, monthly_income=150000, loan_amount=3000000)
        assert decision == "PRE_APPROVED"

    def test_pre_approved_cibil_at_threshold(self):
        """Test PRE_APPROVED with CIBIL exactly at 650 threshold."""
        # Income 30000, required = 500000/48 = 10416.67
        # 30000 > 10416.67, so PRE_APPROVED
        decision = DecisionEngine.make_decision(cibil_score=650, monthly_income=30000, loan_amount=500000)
        assert decision == "PRE_APPROVED"

    def test_manual_review_good_cibil_insufficient_income(self):
        """Test MANUAL_REVIEW with good CIBIL but insufficient income."""
        # Income 10000, required = 500000/48 = 10416.67
        # 10000 < 10416.67, so MANUAL_REVIEW
        decision = DecisionEngine.make_decision(cibil_score=750, monthly_income=10000, loan_amount=500000)
        assert decision == "MANUAL_REVIEW"

    def test_manual_review_income_exactly_at_threshold(self):
        """Test MANUAL_REVIEW when income equals required amount."""
        loan_amount = 500000
        required_income = loan_amount / 48  # 10416.67

        # Income exactly equal to required (should be MANUAL_REVIEW, not >)
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=required_income, loan_amount=loan_amount)
        assert decision == "MANUAL_REVIEW"

    def test_manual_review_income_just_below_threshold(self):
        """Test MANUAL_REVIEW when income is just below required amount."""
        loan_amount = 500000
        required_income = loan_amount / 48  # 10416.67

        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=required_income - 1, loan_amount=loan_amount)
        assert decision == "MANUAL_REVIEW"

    def test_pre_approved_income_just_above_threshold(self):
        """Test PRE_APPROVED when income is just above required amount."""
        loan_amount = 500000
        required_income = loan_amount / 48  # 10416.67

        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=required_income + 1, loan_amount=loan_amount)
        assert decision == "PRE_APPROVED"

    def test_small_loan_amount_low_income(self):
        """Test decision with small loan amount and low income."""
        # Loan 100000, required income = 100000/48 = 2083.33
        # Income 5000 > 2083.33, so PRE_APPROVED
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=5000, loan_amount=100000)
        assert decision == "PRE_APPROVED"

    def test_large_loan_amount_high_income(self):
        """Test decision with large loan amount and high income."""
        # Loan 10000000, required income = 10000000/48 = 208333.33
        # Income 250000 > 208333.33, so PRE_APPROVED
        decision = DecisionEngine.make_decision(cibil_score=750, monthly_income=250000, loan_amount=10000000)
        assert decision == "PRE_APPROVED"

    def test_large_loan_amount_insufficient_income(self):
        """Test MANUAL_REVIEW with large loan and insufficient income."""
        # Loan 10000000, required income = 10000000/48 = 208333.33
        # Income 150000 < 208333.33, so MANUAL_REVIEW
        decision = DecisionEngine.make_decision(cibil_score=750, monthly_income=150000, loan_amount=10000000)
        assert decision == "MANUAL_REVIEW"

    def test_income_ratio_calculations(self):
        """Test various income to loan ratios."""
        test_cases = [
            # (cibil, income, loan, expected)
            (700, 20000, 500000, "PRE_APPROVED"),  # 20000 > 10416.67
            (700, 10000, 500000, "MANUAL_REVIEW"),  # 10000 < 10416.67
            (700, 50000, 1000000, "PRE_APPROVED"),  # 50000 > 20833.33
            (700, 15000, 1000000, "MANUAL_REVIEW"),  # 15000 < 20833.33
            (700, 100000, 2000000, "PRE_APPROVED"),  # 100000 > 41666.67
            (700, 30000, 2000000, "MANUAL_REVIEW"),  # 30000 < 41666.67
        ]

        for cibil, income, loan, expected in test_cases:
            decision = DecisionEngine.make_decision(cibil_score=cibil, monthly_income=income, loan_amount=loan)
            assert (
                decision == expected
            ), f"Failed for CIBIL={cibil}, Income={income}, Loan={loan}. Expected {expected}, got {decision}"

    def test_edge_case_minimum_loan_amount(self):
        """Test with minimum realistic loan amount."""
        # Very small loan
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=1000, loan_amount=10000)
        # Required income = 10000/48 = 208.33
        # 1000 > 208.33, so PRE_APPROVED
        assert decision == "PRE_APPROVED"

    def test_edge_case_maximum_loan_amount(self):
        """Test with very large loan amount."""
        # Very large loan
        decision = DecisionEngine.make_decision(cibil_score=850, monthly_income=500000, loan_amount=20000000)
        # Required income = 20000000/48 = 416666.67
        # 500000 > 416666.67, so PRE_APPROVED
        assert decision == "PRE_APPROVED"

    def test_various_cibil_scores_above_threshold(self):
        """Test that all CIBIL scores >= 650 follow income rules."""
        cibil_scores = [650, 700, 750, 800, 850, 900]

        for cibil in cibil_scores:
            # With sufficient income
            decision = DecisionEngine.make_decision(cibil_score=cibil, monthly_income=50000, loan_amount=500000)
            assert decision == "PRE_APPROVED"

            # With insufficient income
            decision = DecisionEngine.make_decision(cibil_score=cibil, monthly_income=5000, loan_amount=500000)
            assert decision == "MANUAL_REVIEW"

    def test_various_cibil_scores_below_threshold(self):
        """Test that all CIBIL scores < 650 are REJECTED."""
        cibil_scores = [300, 400, 500, 600, 649]

        for cibil in cibil_scores:
            decision = DecisionEngine.make_decision(
                cibil_score=cibil,
                monthly_income=100000,  # Very high income
                loan_amount=500000,
            )
            assert decision == "REJECTED"

    def test_loan_term_calculation(self):
        """Test that loan term is correctly set to 48 months."""
        # Verify the constant
        assert DecisionEngine.LOAN_TERM_MONTHS == 48

        # Verify calculation uses 48 months
        loan_amount = 480000  # Divisible by 48
        monthly_income = 10001  # Just above 480000/48 = 10000

        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=monthly_income, loan_amount=loan_amount)
        assert decision == "PRE_APPROVED"

    def test_zero_loan_amount(self):
        """Test behavior with zero loan amount (edge case)."""
        # Required income = 0/48 = 0
        # Any positive income > 0, so PRE_APPROVED
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=1, loan_amount=0)
        assert decision == "PRE_APPROVED"

    def test_very_small_loan_very_low_income(self):
        """Test with minimal loan and minimal income."""
        # Loan 1000, required income = 1000/48 = 20.83
        # Income 100 > 20.83, so PRE_APPROVED
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=100, loan_amount=1000)
        assert decision == "PRE_APPROVED"

    def test_personal_loan_scenario(self):
        """Test typical personal loan scenario."""
        # Personal loan: 500K, income: 50K
        decision = DecisionEngine.make_decision(cibil_score=750, monthly_income=50000, loan_amount=500000)
        assert decision == "PRE_APPROVED"

    def test_home_loan_scenario(self):
        """Test typical home loan scenario."""
        # Home loan: 5M, income: 150K
        decision = DecisionEngine.make_decision(cibil_score=750, monthly_income=150000, loan_amount=5000000)
        # Required = 5000000/48 = 104166.67
        # 150000 > 104166.67, so PRE_APPROVED
        assert decision == "PRE_APPROVED"

    def test_auto_loan_scenario(self):
        """Test typical auto loan scenario."""
        # Auto loan: 800K, income: 40K
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=40000, loan_amount=800000)
        # Required = 800000/48 = 16666.67
        # 40000 > 16666.67, so PRE_APPROVED
        assert decision == "PRE_APPROVED"

    def test_business_loan_scenario(self):
        """Test typical business loan scenario."""
        # Business loan: 2M, income: 80K
        decision = DecisionEngine.make_decision(cibil_score=720, monthly_income=80000, loan_amount=2000000)
        # Required = 2000000/48 = 41666.67
        # 80000 > 41666.67, so PRE_APPROVED
        assert decision == "PRE_APPROVED"


class TestDecisionEngineConstants:
    """Test decision engine constants."""

    def test_min_cibil_score_constant(self):
        """Test that MIN_CIBIL_SCORE is 650."""
        assert DecisionEngine.MIN_CIBIL_SCORE == 650

    def test_loan_term_months_constant(self):
        """Test that LOAN_TERM_MONTHS is 48."""
        assert DecisionEngine.LOAN_TERM_MONTHS == 48


class TestDecisionEngineEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_cibil_boundary_649_vs_650(self):
        """Test decision at CIBIL score boundary."""
        # 649 should be REJECTED
        decision1 = DecisionEngine.make_decision(cibil_score=649, monthly_income=100000, loan_amount=500000)
        assert decision1 == "REJECTED"

        # 650 should follow income rules
        decision2 = DecisionEngine.make_decision(cibil_score=650, monthly_income=100000, loan_amount=500000)
        assert decision2 == "PRE_APPROVED"

    def test_income_boundary_conditions(self):
        """Test various boundary conditions for income."""
        loan_amount = 480000
        required_income = 10000  # 480000 / 48

        # Exactly at boundary
        decision = DecisionEngine.make_decision(cibil_score=700, monthly_income=required_income, loan_amount=loan_amount)
        assert decision == "MANUAL_REVIEW"

        # Just below boundary
        decision = DecisionEngine.make_decision(
            cibil_score=700,
            monthly_income=required_income - 0.01,
            loan_amount=loan_amount,
        )
        assert decision == "MANUAL_REVIEW"

        # Just above boundary
        decision = DecisionEngine.make_decision(
            cibil_score=700,
            monthly_income=required_income + 0.01,
            loan_amount=loan_amount,
        )
        assert decision == "PRE_APPROVED"

    def test_extreme_values(self):
        """Test with extreme but valid values."""
        # Maximum CIBIL, very high income
        decision = DecisionEngine.make_decision(cibil_score=900, monthly_income=10000000, loan_amount=100000000)
        assert decision == "PRE_APPROVED"

        # Minimum passing CIBIL, minimal income
        decision = DecisionEngine.make_decision(cibil_score=650, monthly_income=2, loan_amount=48)
        assert decision == "PRE_APPROVED"
