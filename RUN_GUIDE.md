# Loan Pre-Qualification Service - Complete Run Guide

This guide provides step-by-step instructions to run the entire loan pre-qualification system end-to-end.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Running with Docker Compose](#running-with-docker-compose)
4. [Running Locally (Development)](#running-locally-development)
5. [Testing the Application](#testing-the-application)
6. [Monitoring and Debugging](#monitoring-and-debugging)
7. [Stopping Services](#stopping-services)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Python** (v3.9+) - for local development
- **Git** - for version control
- **curl** or **Postman** - for API testing

### Verify Installation

```bash
docker --version
docker-compose --version
python --version
```

---

## Quick Start

The fastest way to run the entire application:

```bash
# 1. Clone the repository (if not already)
cd /Users/jatin.gupta/Desktop/loan-pre-qualification-service-pair6

# 2. Start all services with Docker Compose
make run-local

# Or manually:
docker-compose up --build
```

This will start:
- PostgreSQL database (port 5432)
- Kafka + Zookeeper (ports 9092, 9093)
- Kafka UI (port 8080)
- pgAdmin (port 5050)
- PreQual API Service (port 8000)
- Credit Service (Kafka consumer)
- Decision Service (Kafka consumer)

---

## Running with Docker Compose

### Step 1: Start Infrastructure Services

Start only the infrastructure (database, Kafka) first:

```bash
docker-compose up -d postgres kafka zookeeper
```

Wait for services to be healthy (about 30-60 seconds):

```bash
docker-compose ps
```

### Step 2: Initialize Database

Create the database tables:

```bash
# Option 1: Run from host (requires local Python environment)
python init_db.py

# Option 2: Run inside container
docker-compose exec prequal-api python /app/init_db.py
```

### Step 3: Start Application Services

```bash
# Start all application services
docker-compose up -d prequal-api credit-service decision-service

# View logs to ensure services started correctly
docker-compose logs -f prequal-api credit-service decision-service
```

### Step 4: Verify Services Are Running

```bash
# Check all services status
docker-compose ps

# All services should show "Up" status
# Check specific service health
curl http://localhost:8000/docs  # API documentation
```

---

## Running Locally (Development)

For local development without Docker:

### Step 1: Setup Python Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install
# Or: pip install -r requirements.txt

# Setup pre-commit hooks
make setup-hooks
```

### Step 2: Start Infrastructure with Docker

```bash
# Start only infrastructure services
docker-compose up -d postgres kafka zookeeper kafka-ui pgadmin
```

### Step 3: Set Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/loan_prequal_db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

Or export them:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/loan_prequal_db
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### Step 4: Initialize Database

```bash
python init_db.py
```

### Step 5: Start Services in Separate Terminals

**Terminal 1 - PreQual API:**
```bash
cd prequal-api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Credit Service:**
```bash
cd credit-service
python app/main.py
```

**Terminal 3 - Decision Service:**
```bash
cd decision-service
python app/main.py
```

---

## Testing the Application

### Option 1: Using curl

#### 1. Create a Loan Application

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "pan_number": "ABCDE1234F",
    "applicant_name": "John Doe",
    "monthly_income_inr": 75000,
    "loan_amount_inr": 500000,
    "loan_type": "PERSONAL"
  }'
```

**Expected Response:**
```json
{
  "application_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Application submitted successfully",
  "status": "PENDING"
}
```

#### 2. Check Application Status

Copy the `application_id` from the response above:

```bash
curl http://localhost:8000/applications/{application_id}
```

**Expected Response (after processing):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "pan_number": "ABCDE1234F",
  "applicant_name": "John Doe",
  "monthly_income_inr": 75000.0,
  "loan_amount_inr": 500000.0,
  "loan_type": "PERSONAL",
  "status": "PRE_APPROVED",
  "cibil_score": 790,
  "created_at": "2025-11-04T10:30:00",
  "updated_at": "2025-11-04T10:30:02"
}
```

### Option 2: Using Interactive API Documentation

Open your browser and navigate to:
```
http://localhost:8000/docs
```

This opens the FastAPI Swagger UI where you can:
1. See all available endpoints
2. Test endpoints interactively
3. View request/response schemas

### Option 3: Using Postman

Import this collection or create requests manually:

**1. POST Create Application**
- URL: `http://localhost:8000/applications`
- Method: POST
- Headers: `Content-Type: application/json`
- Body (JSON):
  ```json
  {
    "pan_number": "FGHIJ5678K",
    "applicant_name": "Jane Smith",
    "monthly_income_inr": 45000,
    "loan_amount_inr": 300000,
    "loan_type": "AUTO"
  }
  ```

**2. GET Application Status**
- URL: `http://localhost:8000/applications/{application_id}`
- Method: GET

### Test Scenarios

#### Scenario 1: PRE_APPROVED Application
- High CIBIL score + sufficient income

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "pan_number": "ABCDE1234F",
    "applicant_name": "High Score User",
    "monthly_income_inr": 100000,
    "loan_amount_inr": 1000000,
    "loan_type": "HOME"
  }'
```

#### Scenario 2: REJECTED Application
- Low CIBIL score

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "pan_number": "FGHIJ5678K",
    "applicant_name": "Low Score User",
    "monthly_income_inr": 80000,
    "loan_amount_inr": 500000,
    "loan_type": "PERSONAL"
  }'
```

#### Scenario 3: MANUAL_REVIEW Application
- Good CIBIL but insufficient income

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "pan_number": "XYZAB9012C",
    "applicant_name": "Review Needed User",
    "monthly_income_inr": 30000,
    "loan_amount_inr": 2000000,
    "loan_type": "HOME"
  }'
```

### Running Automated Tests

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage
make test-coverage
```

---

## Monitoring and Debugging

### View Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f prequal-api
docker-compose logs -f credit-service
docker-compose logs -f decision-service

# View last 100 lines
docker-compose logs --tail=100 prequal-api
```

### Access Kafka UI

Monitor Kafka topics and messages:
```
http://localhost:8080
```

Features:
- View all topics
- Browse messages
- Monitor consumer groups
- Check topic configurations

### Access pgAdmin

Manage PostgreSQL database:
```
http://localhost:5050
```

**Login Credentials:**
- Email: `admin@admin.com`
- Password: `admin`

**Add Server:**
1. Right-click "Servers" → Create → Server
2. General tab: Name: `loan-prequal-db`
3. Connection tab:
   - Host: `postgres`
   - Port: `5432`
   - Database: `loan_prequal_db`
   - Username: `postgres`
   - Password: `postgres`

### Check Database Directly

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d loan_prequal_db

# Useful SQL queries:
# View all applications
SELECT * FROM applications;

# View recent applications
SELECT id, applicant_name, status, cibil_score
FROM applications
ORDER BY created_at DESC
LIMIT 10;

# Count by status
SELECT status, COUNT(*)
FROM applications
GROUP BY status;
```

### Service Health Checks

```bash
# Check container health
docker-compose ps

# Check API health
curl http://localhost:8000/docs

# Check Kafka connectivity
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check PostgreSQL connectivity
docker-compose exec postgres pg_isready -U postgres
```

---

## Stopping Services

### Stop All Services

```bash
# Stop all services (keep containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers, volumes, and networks
docker-compose down -v

# Or use Makefile
make docker-down
```

### Stop Specific Services

```bash
docker-compose stop prequal-api
docker-compose stop credit-service decision-service
```

---

## Troubleshooting

### Issue: Containers fail to start

**Solution:**
```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose up --build
```

### Issue: Database connection errors

**Solution:**
```bash
# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U postgres

# Reinitialize database
python init_db.py
```

### Issue: Kafka connection errors

**Solution:**
```bash
# Check Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Restart Kafka
docker-compose restart kafka
```

### Issue: Services can't connect to each other

**Solution:**
```bash
# Check network
docker network ls
docker network inspect loan-pre-qualification-service-pair6_loan-prequal-network

# Ensure all services use the same network
docker-compose down
docker-compose up
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port
lsof -i :8000  # Or any other port

# Kill the process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Issue: Application not processing requests

**Check:**
1. Are all three services running?
   ```bash
   docker-compose ps
   ```

2. Check Kafka topics exist:
   ```bash
   docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

3. View service logs for errors:
   ```bash
   docker-compose logs -f credit-service decision-service
   ```

### Issue: Tests fail

**Solution:**
```bash
# Ensure dependencies installed
make install

# Ensure PYTHONPATH is set
export PYTHONPATH=.

# Run tests
make test
```

---

## Application Architecture Flow

```
1. User submits application → PreQual API (POST /applications)
2. PreQual API saves to PostgreSQL with status=PENDING
3. PreQual API publishes to Kafka topic: loan-applications
4. Credit Service consumes from loan-applications
5. Credit Service calculates CIBIL score
6. Credit Service publishes to Kafka topic: credit-reports
7. Decision Service consumes from credit-reports
8. Decision Service evaluates loan decision
9. Decision Service updates PostgreSQL with CIBIL score and status
10. User checks status → PreQual API (GET /applications/{id})
```

---

## Service Ports Reference

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| PreQual API | 8000 | http://localhost:8000 | Main REST API |
| API Docs | 8000 | http://localhost:8000/docs | Swagger UI |
| Credit Service | 8001 | N/A | Kafka consumer |
| Decision Service | 8002 | N/A | Kafka consumer |
| Kafka | 9092 | localhost:9092 | Kafka broker (external) |
| Kafka UI | 8080 | http://localhost:8080 | Kafka monitoring |
| PostgreSQL | 5432 | localhost:5432 | Database |
| pgAdmin | 5050 | http://localhost:5050 | DB management |
| Zookeeper | 2181 | localhost:2181 | Kafka coordination |

---

## Environment Variables Reference

### PreQual API & Decision Service
- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address

### Credit Service
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address

### Default Values
```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/loan_prequal_db
KAFKA_BOOTSTRAP_SERVERS=kafka:9093  # Internal Docker network
# or
KAFKA_BOOTSTRAP_SERVERS=localhost:9092  # Local development
```

---

## Next Steps

1. **Development**: Make code changes and use `make format` and `make lint`
2. **Testing**: Run `make test` before committing
3. **Committing**: Use git normally - pre-commit hooks will run automatically
4. **Production**: Create separate docker-compose.prod.yml with production configs

---

## Summary of Commands

```bash
# Quick start
make run-local          # Start all services
make test               # Run all tests
make lint               # Lint code
make format             # Format code

# Docker Compose
docker-compose up --build              # Build and start all
docker-compose up -d                   # Start in detached mode
docker-compose down                    # Stop and remove
docker-compose logs -f prequal-api     # View logs
docker-compose ps                      # Check status

# Database
python init_db.py                      # Initialize database
python init_db.py --drop               # Drop all tables

# Testing
curl -X POST http://localhost:8000/applications -H "Content-Type: application/json" -d '{"pan_number":"ABCDE1234F","applicant_name":"Test User","monthly_income_inr":75000,"loan_amount_inr":500000,"loan_type":"PERSONAL"}'

curl http://localhost:8000/applications/{id}
```

---

**Need Help?** Check the logs first: `docker-compose logs -f`
