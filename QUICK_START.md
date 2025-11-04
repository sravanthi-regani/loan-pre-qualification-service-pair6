# Quick Start Guide - Loan Pre-Qualification Service

## Run Application End-to-End in 2 Steps

### Step 1: Start All Services

```bash
docker-compose up --build
```

This automatically:
- ✅ Starts PostgreSQL database
- ✅ Starts Kafka + Zookeeper
- ✅ **Creates database tables automatically**
- ✅ Starts PreQual API (port 8000)
- ✅ Starts Credit Service
- ✅ Starts Decision Service

Wait about 60 seconds for all services to be ready. Watch the logs for:
```
✓ Database tables created successfully!
Created tables:
  - applications
```

### Step 2: Test the Application

#### Create an application:

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

**Response:**
```json
{
  "application_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Application submitted successfully",
  "status": "PENDING"
}
```

#### Check status (wait 2-3 seconds for processing):

```bash
curl http://localhost:8000/applications/{application_id}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PRE_APPROVED",
  "cibil_score": 790,
  ...
}
```

---

## Alternative: Use Swagger UI

Open browser: **http://localhost:8000/docs**

1. Click on **POST /applications**
2. Click **"Try it out"**
3. Enter request body
4. Click **"Execute"**
5. Copy the `application_id`
6. Use **GET /applications/{application_id}** to check status

---

## Stop Services

### Just Stop (Keep Data)
```bash
docker-compose down
# or
make docker-down
```

### Stop and Cleanup All Data
```bash
docker-compose down -v
# or
make docker-clean
```

**Note:** `-v` flag removes all volumes including database data. Use this for a fresh start.

---

## Test Scenarios

### ✅ PRE_APPROVED (High CIBIL + Good Income)
```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{"pan_number":"ABCDE1234F","applicant_name":"High Score","monthly_income_inr":100000,"loan_amount_inr":1000000,"loan_type":"HOME"}'
```

### ❌ REJECTED (Low CIBIL)
```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{"pan_number":"FGHIJ5678K","applicant_name":"Low Score","monthly_income_inr":80000,"loan_amount_inr":500000,"loan_type":"PERSONAL"}'
```

### ⚠️ MANUAL_REVIEW (Good CIBIL + Low Income)
```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{"pan_number":"XYZAB9012C","applicant_name":"Review Needed","monthly_income_inr":30000,"loan_amount_inr":2000000,"loan_type":"HOME"}'
```

---

## Monitoring Tools

| Tool | URL |
|------|-----|
| API Docs | http://localhost:8000/docs |

---

## Troubleshooting

### Services not starting?
```bash
docker-compose logs -f
```

### Database errors?
```bash
docker-compose restart postgres
python init_db.py
```

### Need to rebuild?
```bash
docker-compose down
docker-compose up --build
```

---

## Full Documentation

For detailed information, see:
- **[RUN_GUIDE.md](./RUN_GUIDE.md)** - Complete end-to-end guide
- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)** - Development and testing

---

## Architecture Flow

```
User → PreQual API → Kafka (loan-applications)
                        ↓
                   Credit Service (calculates CIBIL)
                        ↓
                   Kafka (credit-reports)
                        ↓
                   Decision Service (makes decision)
                        ↓
                   PostgreSQL (updates status)
                        ↓
User ← PreQual API (GET status)
```
