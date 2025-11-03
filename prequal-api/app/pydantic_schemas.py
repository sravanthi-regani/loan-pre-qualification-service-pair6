from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class LoanType(str, Enum):
    PERSONAL = "personal"
    HOME = "home"
    AUTO = "auto"
    BUSINESS = "business"


class LoanApplicationRequest(BaseModel):
    applicant_name: str = Field(..., min_length=2, max_length=100)
    pan_number: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    loan_type: LoanType
    loan_amount: float = Field(..., gt=0, le=100000000)
    monthly_income: float = Field(..., gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "applicant_name": "Sri",
                "pan_number": "UUVGH2323K",
                "loan_type": "personal",
                "loan_amount": "10202303",
                "monthly_income": "1341240",
            }
        }


class LoanApplicationResponse(BaseModel):
    application_id: str
    status: str = "PENDING"

