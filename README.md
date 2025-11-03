# Loan Pre-Qualification Microservices

In the fast-growing Indian credit market, lenders (Banks and NBFCs) need to provide instant, high-level decisions on loan eligibility to capture new customers. This "prequalification" step is not a final approval but a quick check to see if an applicant meets the basic criteria.

## Architecture

This project implements a microservices architecture with Kafka-based event-driven communication:

```
┌─────────────────┐      Kafka         ┌──────────────────┐
│                 │   loan_applications_submitted│                  │
│  Prequal API    ├───────────────────►│ Credit Service   │
│  (Producer)     │                    │  (Consumer)      │
│  Port: 8000     │                    │  Port: 8002      │
└─────────────────┘                    └────────┬─────────┘
                                               │
                                               │ Kafka
                                               │ credit-checks
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │                      │
                                    │  Decision Service    │
                                    │  (Consumer)          │
                                    │  Port: 8001          │
                                    │                      │
                                    └──────────┬───────────┘
                                               │
                                               │ Kafka
                                               │ decisions
                                               ▼
```

## Services

### 1. Prequal API (Port 8000)
**Role:** Kafka Producer - Main entry point

**Responsibilities:**
- Receives loan applications via REST API
- Validates application data
- Publishes applications to Kafka topic `loan_applications_submitted`
- Provides application status endpoints

**Key Endpoints:**
- `POST /applications` - Submit loan application
- `GET /applications/{id}` - Get application status
- `GET /applications` - List all applications

### 2. Credit Service (Port 8002)
**Role:** Kafka Producer - Credit check processor

**Responsibilities:**
- Receives application details via REST API
- Simulates credit bureau checks (credit score, existing loans)
- Calculates debt-to-income ratio
- Evaluates creditworthiness
- Publishes results to Kafka topic `credit-checks`

**Key Endpoints:**
- `POST /application` - Perform credit check
- `GET /health` - Health check

### 3. Decision Service (Port 8001)
**Role:** Kafka Consumer - Final decision maker

**Responsibilities:**
- Consumes credit check results from Kafka topic `credit-checks`
- Applies business rules for loan pre-qualification
- Makes final APPROVED/REJECTED/REVIEW_REQUIRED decisions
- Publishes decisions to Kafka topic `decisions`
- Provides decision query endpoints

**Key Endpoints:**
- `GET /decisions/{id}` - Get decision for application
- `GET /decisions` - List all decisions
- `GET /stats` - Get decision statistics

## Kafka Topics

1. **loan_applications_submitted** - New loan applications from Prequal API
2. **credit-checks** - Credit check results from Credit Service
3. **decisions** - Final pre-qualification decisions from Decision Service

## Technology Stack

- **Framework:** FastAPI
- **Message Broker:** Apache Kafka
- **Data Validation:** Pydantic
- **ASGI Server:** Uvicorn
- **Container Orchestration:** Docker Compose

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- pip (Python package manager)

## Quick Start

### 1. Start Kafka and Zookeeper

```bash
docker-compose up -d
```

This will start:
- Zookeeper (Port 2181)
- Kafka (Port 9092)
- Kafka UI (Port 8080) - Web interface at http://localhost:8080

### 2. Install Dependencies

```bash
# Install for all services (from project root)
pip install -r requirements.txt

# Or install per service
cd prequal-api && pip install -r requirements.txt
cd ../credit-service && pip install -r requirements.txt
cd ../decision-service && pip install -r requirements.txt
```

### 3. Start the Services

Open 3 separate terminals:

**Terminal 1 - Prequal API:**
```bash
cd prequal-api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Credit Service:**
```bash
cd credit-service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

**Terminal 3 - Decision Service:**
```bash
cd decision-service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Test the System

The services will be available at:
- Prequal API: http://localhost:8000/docs
- Decision Service: http://localhost:8001/docs
- Credit Service: http://localhost:8002/docs
- Kafka UI: http://localhost:8080

## Complete Workflow Example

### Step 1: Submit a loan application to Credit Service

```bash
curl -X POST "http://localhost:8002/application" \
  -H "Content-Type: application/json" \
  -d '{
    "pan_number": "ABCDE1234F",
    "applicant_name": "Rajesh Kumar",
    "monthly_income": 75000,
    "loan_amount": 500000,
    "loan_type": "personal"
  }'
```

Response:
```json
{
  "application_id": "APP-A1B2C3D4E5F6",
  "pan_number": "ABCDE1234F",
  "applicant_name": "Rajesh Kumar",
  "credit_score": 720,
  "existing_loans": 150000,
  "debt_to_income_ratio": 28.5,
  "status": "APPROVED",
  "message": "Good credit profile"
}
```

### Step 2: Check the decision (after a few seconds)

```bash
curl -X GET "http://localhost:8001/decisions/APP-A1B2C3D4E5F6"
```

Response:
```json
{
  "application_id": "APP-A1B2C3D4E5F6",
  "decision": "APPROVED",
  "applicant_name": "Rajesh Kumar",
  "reason": "Good credit profile. Pre-qualified for requested amount.",
  "timestamp": "2025-11-03T10:30:00.000Z"
}
```

### Step 3: View statistics

```bash
curl -X GET "http://localhost:8001/stats"
```

## Project Structure

```
loan-pre-qualification-service-pair6/
├── prequal-api/              # Main API service
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models.py         # Pydantic models
│   │   └── kafka_producer.py # Kafka producer
│   ├── requirements.txt
│   └── README.md
├── credit-service/           # Credit check service
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models.py         # Pydantic models
│   │   ├── kafka_producer.py # Kafka producer
│   │   └── credit_service.py # Credit check logic
│   ├── requirements.txt
│   └── README.md
├── decision-service/         # Decision making service
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── models.py         # Pydantic models
│   │   ├── kafka_consumer.py # Kafka consumer
│   │   ├── consumer.py       # Message processor
│   │   └── decision_engine.py # Decision logic
│   ├── requirements.txt
│   └── README.md
├── shared/                   # Shared models (optional)
│   ├── models.py
│   ├── config.py
│   └── __init__.py
├── docker-compose.yml        # Kafka & Zookeeper
├── requirements.txt          # Global dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Decision Logic

### Credit Score Requirements
- Personal Loan: 650+
- Home Loan: 700+
- Auto Loan: 650+
- Business Loan: 680+

### Debt-to-Income Ratio Limits
- Personal Loan: 40%
- Home Loan: 45%
- Auto Loan: 40%
- Business Loan: 50%

### Loan-to-Income Ratio (Annual)
- Personal Loan: 5x
- Home Loan: 10x
- Auto Loan: 3x
- Business Loan: 8x

## Monitoring

### Kafka UI
Access Kafka UI at http://localhost:8080 to:
- View topics and messages
- Monitor consumer groups
- Check partition details

### Service Health Checks
- Prequal API: http://localhost:8000/health
- Decision Service: http://localhost:8001/health
- Credit Service: http://localhost:8002/health

## Development

### Running Tests
```bash
pytest
```

### Stopping Services
```bash
# Stop Kafka and Zookeeper
docker-compose down

# Stop the microservices
# Press Ctrl+C in each terminal
```

### Cleaning Up
```bash
# Remove Kafka data
docker-compose down -v
```

## Environment Variables

Copy `.env.example` to `.env` and modify as needed:
```bash
cp .env.example .env
```

## Troubleshooting

### Kafka Connection Issues
- Ensure Kafka is running: `docker-compose ps`
- Check Kafka logs: `docker-compose logs kafka`

### Service Not Starting
- Check if ports 8000, 8001, 8002 are available
- Verify Python dependencies are installed
- Check service logs for errors

### Messages Not Being Consumed
- Verify Kafka topics exist in Kafka UI
- Check consumer group status
- Ensure all services are running

## Future Enhancements

- Add database persistence (PostgreSQL/MongoDB)
- Implement authentication and authorization
- Add distributed tracing (Jaeger/Zipkin)
- Implement retry mechanisms and dead letter queues
- Add comprehensive unit and integration tests
- Containerize microservices with Docker
- Add API rate limiting
- Implement caching (Redis)

## License

MIT

## Contributors

Pair 6
