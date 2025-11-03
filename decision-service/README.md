# Decision Service

Microservice that consumes credit check results from Kafka and makes final loan pre-qualification decisions.

## Features

- Kafka consumer subscribed to `credit-checks` topic
- Decision engine with business rules for loan pre-qualification
- Evaluates applications based on:
  - Credit score thresholds by loan type
  - Debt-to-income ratios
  - Loan-to-income ratios
- Publishes decisions to Kafka topic `decisions`
- REST API to query decisions

## Decision Criteria

### Minimum Credit Scores by Loan Type
- Personal Loan: 650
- Home Loan: 700
- Auto Loan: 650
- Business Loan: 680

### Maximum Debt-to-Income Ratios
- Personal Loan: 40%
- Home Loan: 45%
- Auto Loan: 40%
- Business Loan: 50%

### Maximum Loan-to-Income Ratios (Annual)
- Personal Loan: 5x annual income
- Home Loan: 10x annual income
- Auto Loan: 3x annual income
- Business Loan: 8x annual income

## Decision Outcomes

- **APPROVED**: Application meets all criteria
- **REJECTED**: Application fails one or more critical criteria
- **REVIEW_REQUIRED**: Application requires manual review (borderline cases)

## API Endpoints

### GET /decisions/{application_id}

Get the decision for a specific application.

**Response:**
```json
{
  "application_id": "APP-A1B2C3D4E5F6",
  "decision": "APPROVED",
  "applicant_name": "John Doe",
  "reason": "Excellent credit profile. Pre-qualified for requested amount.",
  "timestamp": "2025-11-03T10:30:00.000Z"
}
```

### GET /decisions

List all decisions.

### GET /stats

Get decision statistics.

**Response:**
```json
{
  "total": 100,
  "approved": 65,
  "rejected": 20,
  "review_required": 15
}
```

### GET /health

Health check endpoint.

### GET /

Service information endpoint.

## Running the Service

### Prerequisites

- Python 3.8+
- Kafka running on localhost:9092
- Credit Service running and publishing to `credit-checks` topic

### Installation

```bash
cd decision-service
pip install -r requirements.txt
```

### Start the Service

The service runs both the Kafka consumer and REST API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The Kafka consumer starts automatically in a background thread when the API starts.

API available at http://localhost:8001

API documentation at http://localhost:8001/docs

### Run Consumer Only (without API)

```bash
python -m app.consumer
```

## Workflow

1. Credit Service publishes credit check results to `credit-checks` topic
2. Decision Service consumes messages from `credit-checks`
3. Decision Engine evaluates application using business rules
4. Decision is stored in memory
5. Decision is published to `decisions` topic
6. Decision can be queried via REST API

## Configuration

The service connects to Kafka at `localhost:9092` by default.

Consumer group ID: `decision-service-group`

## Kafka Topics

- **Consumes from:** `credit-checks` - Credit check results
- **Produces to:** `decisions` - Final pre-qualification decisions