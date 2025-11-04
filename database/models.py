import uuid

from sqlalchemy import DECIMAL, TIMESTAMP, Column, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class Application(Base):
    """
    SQLAlchemy model for the applications table.

    Stores loan application data with credit check results and status.
    """

    __tablename__ = "applications"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="Unique identifier for the application",
        index=True,
    )

    # Applicant information
    pan_number = Column(String(10), nullable=False, comment="Applicant's PAN number")

    applicant_name = Column(String(255), nullable=True, comment="Applicant's full name")

    # Financial information
    monthly_income_inr = Column(
        DECIMAL(12, 2),
        nullable=False,
        comment="Applicant's gross monthly income in INR",
    )

    loan_amount_inr = Column(DECIMAL(12, 2), nullable=False, comment="Requested loan amount in INR")

    # Loan details
    loan_type = Column(
        String(20),
        nullable=False,
        comment="Type of loan: PERSONAL, HOME, AUTO, BUSINESS",
    )

    # Application status
    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        comment="Application status: PENDING, PRE_APPROVED, REJECTED, MANUAL_REVIEW",
    )

    # Credit information
    cibil_score = Column(Integer, nullable=True, comment="Simulated CIBIL score (300-900)")

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the application was created",
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when the application was last updated",
    )

    def __repr__(self):
        return (
            f"<Application(id={self.id}, pan_number={self.pan_number}, "
            f"applicant_name={self.applicant_name}, status={self.status})>"
        )

    def to_dict(self):
        """
        Convert the model instance to a dictionary.
        Useful for JSON serialization.
        """
        return {
            "id": str(self.id),
            "pan_number": self.pan_number,
            "applicant_name": self.applicant_name,
            "monthly_income_inr": (float(self.monthly_income_inr) if self.monthly_income_inr else None),
            "loan_amount_inr": (float(self.loan_amount_inr) if self.loan_amount_inr else None),
            "loan_type": self.loan_type,
            "status": self.status,
            "cibil_score": self.cibil_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
