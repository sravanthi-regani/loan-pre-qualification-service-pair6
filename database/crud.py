from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Application


class ApplicationCRUD:
    """
    CRUD operations for Application model.
    """

    @staticmethod
    def create_application(
        db: Session,
        pan_number: str,
        applicant_name: str,
        monthly_income_inr: Decimal,
        loan_amount_inr: Decimal,
        loan_type: str,
        status: str = "PENDING",
        cibil_score: Optional[int] = None,
    ) -> Application:
        """
        Create a new application record.

        Args:
            db: Database session
            pan_number: Applicant's PAN number
            applicant_name: Applicant's full name
            monthly_income_inr: Monthly income in INR
            loan_amount_inr: Requested loan amount in INR
            loan_type: Type of loan (PERSONAL, HOME, AUTO, BUSINESS)
            status: Application status (default: PENDING)
            cibil_score: CIBIL score (optional)

        Returns:
            Application: Created application instance

        Raises:
            IntegrityError: If duplicate entry or constraint violation
        """
        try:
            application = Application(
                pan_number=pan_number,
                applicant_name=applicant_name,
                monthly_income_inr=monthly_income_inr,
                loan_amount_inr=loan_amount_inr,
                loan_type=loan_type,
                status=status,
                cibil_score=cibil_score,
            )
            db.add(application)
            db.commit()
            db.refresh(application)
            return application
        except IntegrityError as e:
            db.rollback()
            raise e

    @staticmethod
    def get_application_by_id(db: Session, application_id: UUID) -> Optional[Application]:
        """
        Get application by ID.

        Args:
            db: Database session
            application_id: UUID of the application

        Returns:
            Application if found, None otherwise
        """
        return db.query(Application).filter(Application.id == application_id).first()

    @staticmethod
    def get_applications_by_status(db: Session, status: str, limit: int = 100, offset: int = 0) -> List[Application]:
        """
        Get applications by status with pagination.

        Args:
            db: Database session
            status: Application status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Application instances
        """
        return (
            db.query(Application)
            .filter(Application.status == status)
            .order_by(Application.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_all_applications(db: Session, limit: int = 100, offset: int = 0) -> List[Application]:
        """
        Get all applications with pagination.

        Args:
            db: Database session
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Application instances
        """
        return db.query(Application).order_by(Application.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def update_application_status(
        db: Session,
        application_id: UUID,
        status: str,
        cibil_score: Optional[int] = None,
    ) -> Optional[Application]:
        """
        Update application status and optionally CIBIL score.

        Args:
            db: Database session
            application_id: UUID of the application
            status: New status
            cibil_score: CIBIL score (optional)

        Returns:
            Updated Application if found, None otherwise
        """
        application = db.query(Application).filter(Application.id == application_id).first()
        if application:
            application.status = status
            if cibil_score is not None:
                application.cibil_score = cibil_score
            db.commit()
            db.refresh(application)
        return application

    @staticmethod
    def count_applications_by_status(db: Session, status: str) -> int:
        """
        Count applications by status.

        Args:
            db: Database session
            status: Application status

        Returns:
            Number of applications with the given status
        """
        return db.query(Application).filter(Application.status == status).count()

    @staticmethod
    def get_statistics(db: Session) -> dict:
        """
        Get statistics about applications.

        Args:
            db: Database session

        Returns:
            Dictionary with statistics
        """
        total = db.query(Application).count()
        pending = ApplicationCRUD.count_applications_by_status(db, "PENDING")
        pre_approved = ApplicationCRUD.count_applications_by_status(db, "PRE_APPROVED")
        rejected = ApplicationCRUD.count_applications_by_status(db, "REJECTED")
        manual_review = ApplicationCRUD.count_applications_by_status(db, "MANUAL_REVIEW")

        return {
            "total": total,
            "pending": pending,
            "pre_approved": pre_approved,
            "rejected": rejected,
            "manual_review": manual_review,
        }
