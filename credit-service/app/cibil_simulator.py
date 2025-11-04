import logging
import random

logger = logging.getLogger(__name__)


class CIBILSimulator:
    """
    Simulates CIBIL score calculation based on PAN number and application details.

    Business Logic:
    - Test PANs have predefined scores
    - Other PANs follow a rule-based calculation
    """

    # Test PAN numbers with predefined scores
    TEST_PANS = {
        "ABCDE1234F": 790,  # Test PAN 1 - Good credit
        "FGHIJ5678K": 610,  # Test PAN 2 - Below average credit
    }

    # Score boundaries
    MIN_SCORE = 300
    MAX_SCORE = 900
    BASE_SCORE = 650

    @classmethod
    def calculate_cibil_score(cls, pan_number: str, monthly_income: float, loan_type: str) -> int:
        """
        Calculate CIBIL score based on PAN number and application details.

        Args:
            pan_number: Applicant's PAN number
            monthly_income: Monthly income in INR
            loan_type: Type of loan (PERSONAL, HOME, AUTO, BUSINESS)

        Returns:
            CIBIL score (300-900)
        """
        # Check if this is a test PAN
        if pan_number in cls.TEST_PANS:
            score = cls.TEST_PANS[pan_number]
            logger.info(f"Using predefined CIBIL score for test PAN {pan_number}: {score}")
            return score

        # Default logic for all other PANs
        score = cls.BASE_SCORE

        # Income-based adjustments
        if monthly_income > 75000:
            score += 40
            logger.debug(f"High income ({monthly_income}) bonus: +40 points")
        elif monthly_income < 30000:
            score -= 20
            logger.debug(f"Low income ({monthly_income}) penalty: -20 points")

        # Loan type adjustments
        loan_type_upper = loan_type.upper()

        if loan_type_upper == "PERSONAL":
            score -= 10  # Unsecured loan
            logger.debug("Personal loan (unsecured) penalty: -10 points")
        elif loan_type_upper == "HOME":
            score += 10  # Secured loan
            logger.debug("Home loan (secured) bonus: +10 points")

        # Add random variation to make it realistic (-5 to +5)
        random_adjustment = random.randint(-5, 5)
        score += random_adjustment
        logger.debug(f"Random adjustment: {random_adjustment:+d} points")

        # Ensure score is within valid range (300-900)
        score = max(cls.MIN_SCORE, min(cls.MAX_SCORE, score))

        logger.info(f"Calculated CIBIL score for PAN {pan_number}: {score} (income: {monthly_income}, loan_type: {loan_type})")

        return score
