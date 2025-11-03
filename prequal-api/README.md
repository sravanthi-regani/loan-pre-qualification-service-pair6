# Prequal API

Main entry point for loan pre-qualification applications. This service acts as a Kafka producer, publishing loan applications to be processed by downstream services.

## Features

- REST API to submit loan applications
- Validates application data
- Publishes applications to Kafka topic `loan_applications_submitted`
- Tracks application status
- Provides application lookup endpoints

## API Endpoints

### POST /applications

Submit a new loan application.

**Request Body:**
```json
{
  "applicant_name": "Rajesh Kumar",
  "applicant_email": "rajesh.kumar@example.com",
  "applicant_phone": "+919876543210",
  "pan_number": "ABCDE1234F",
  "loan_type": "personal",
  "loan_amount": 500000,
  "monthly_income": 75000,
  "employment_type": "salaried"
}
```

**Loan Types:** `personal`, `home`, `auto`, `business`

**PAN Number Format:** Must be in format ABCDE1234F (5 letters, 4 digits, 1 letter)

**Response:**
```json
{
  "application_id": "APP-A1B2C3D4E5F6",
  "applicant_name": "Rajesh Kumar",
  "status": "PENDING",
  "message": "Application submitted successfully and is being processed",
  "timestamp": "2025-11-03T10:30:00.000Z"
}
```

### GET /applications/{application_id}

Get the status of a specific application.

**Response:**
```json
{
  "application_id": "APP-A1B2C3D4E5F6",
  "status": "PENDING",
  "current_stage": "SUBMITTED",
  "details": null,
  "last_updated": "2025-11-03T10:30:00.000Z"
}
```

### GET /applications

List all applications (for admin/testing).

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
cd prequal-api
pip install -r requirements.txt
```

### Start the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at http://localhost:8000

API documentation available at http://localhost:8000/docs

## Workflow

1. Client submits loan application to POST /applications
2. Prequal API validates the data
3. Generates unique application ID
4. Publishes application to Kafka topic `loan_applications_submitted`
5. Returns application ID to client
6. Downstream services (Credit Service, Decision Service) process the application
7. Client can check status using GET /applications/{application_id}

## Configuration

The service connects to Kafka at `localhost:9092` by default. This can be modified in `app/kafka_producer.py`.

## Kafka Topics

- **Produces to:** `loan_applications_submitted` - New loan applications
