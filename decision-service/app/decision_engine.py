import logging

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Decision engine for loan pre-qualification.

    Rules:
    - If cibil_score < 650: REJECTED (High Risk)
    - If cibil_score >= 650 AND monthly_income > (loan_amount / 48): PRE_APPROVED
    - If cibil_score >= 650 AND monthly_income <= (loan_amount / 48): MANUAL_REVIEW
    """

    MIN_CIBIL_SCORE = 650
    LOAN_TERM_MONTHS = 48  # 4-year loan term

    @classmethod
    def make_decision(
        cls,
        cibil_score: int,
        monthly_income: float,
        loan_amount: float
    ) -> str:
        """
        Make pre-qualification decision based on CIBIL score and income ratio.

        Args:
            cibil_score: CIBIL score (300-900)
            monthly_income: Monthly income in INR
            loan_amount: Requested loan amount in INR

        Returns:
            Decision status: REJECTED, PRE_APPROVED, or MANUAL_REVIEW
        """
        logger.info(f"Evaluating decision: CIBIL={cibil_score}, "
                   f"Income={monthly_income}, Loan={loan_amount}")

        # Rule 1: CIBIL score below minimum threshold
        if cibil_score < cls.MIN_CIBIL_SCORE:
            logger.info(f"REJECTED: CIBIL score {cibil_score} < {cls.MIN_CIBIL_SCORE} (High Risk)")
            return "REJECTED"

        # Calculate minimum required monthly income
        # For a 4-year (48 months) loan, monthly EMI ≈ loan_amount / 48
        minimum_monthly_income = loan_amount / cls.LOAN_TERM_MONTHS

        logger.debug(f"Minimum required monthly income: {minimum_monthly_income:.2f}")
        logger.debug(f"Actual monthly income: {monthly_income:.2f}")
        logger.debug(f"Income ratio: {monthly_income / minimum_monthly_income:.2f}x")

        # Rule 2: Good CIBIL with sufficient income
        if monthly_income > minimum_monthly_income:
            logger.info(f"PRE_APPROVED: CIBIL score {cibil_score} >= {cls.MIN_CIBIL_SCORE} "
                       f"and income {monthly_income:.2f} > required {minimum_monthly_income:.2f}")
            return "PRE_APPROVED"

        # Rule 3: Good CIBIL but tight income ratio
        logger.info(f"MANUAL_REVIEW: CIBIL score {cibil_score} >= {cls.MIN_CIBIL_SCORE} "
                   f"but income {monthly_income:.2f} <= required {minimum_monthly_income:.2f} "
                   f"(Tight income ratio)")
        return "MANUAL_REVIEW"