# Credit Service

Microservice for performing credit checks on loan applications.

## Features

- REST API endpoint to receive loan applications
- Simulates credit bureau checks (credit score, existing loans)
- Evaluates creditworthiness based on:
  - Credit score (300-850 range)
  - Debt-to-income ratio
  - Loan type specific thresholds
- Publishes credit check results to Kafka topic `credit-checks`

## API Endpoints

### POST /application

Perform a credit check for a loan application.

**Request Body:**
```json
{
  "pan_number": "ABCDE1234F",
  "applicant_name": "John Doe",
  "monthly_income": 50000,
  "loan_amount": 500000,
  "loan_type": "personal"
}
```

**Loan Types:** `personal`, `home`, `auto`, `business`

**Response:**
```json
{
  "application_id": "APP-A1B2C3D4E5F6",
  "pan_number": "ABCDE1234F",
  "applicant_name": "John Doe",
  "credit_score": 720,
  "existing_loans": 250000,
  "debt_to_income_ratio": 32.5,
  "status": "APPROVED",
  "message": "Good credit profile"
}
```

**Status Values:**
- `APPROVED` - Application meets credit criteria
- `REJECTED` - Application fails credit criteria
- `REVIEW_REQUIRED` - Manual review needed

### GET /health

Health check endpoint.

### GET /

Service information endpoint.

## Running the Service

### Prerequisites

- Python 3.8+
- Kafka running on localhost:9092

### Installation

```bash
cd credit-service
pip install -r requirements.txt
```

### Start the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

The service will be available at http://localhost:8002

API documentation available at http://localhost:8002/docs

## Configuration

The service connects to Kafka at `localhost:9092` by default. This can be modified in `app/kafka_producer.py`.

## Credit Check Logic

### Credit Score Ranges
- 300-599: Rejected
- 600-649: Review Required
- 650-699: Approved (Acceptable)
- 700-749: Approved (Good)
- 750-850: Approved (Excellent)

### Debt-to-Income Ratio Thresholds
- Personal Loan: 40%
- Home Loan: 45%
- Auto Loan: 40%
- Business Loan: 50%