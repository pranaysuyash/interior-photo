# Interior AI - Master Documentation Part 2
## Running, Testing, and Deployment

**Continuation of MASTER_DOCUMENTATION.md**

---

## 8. Running the Application

### 8.1 Complete Startup Sequence

Here's the complete process to get everything running from scratch:

#### Terminal 1: Backend (Docker)

```bash
# Navigate to backend
cd /path/to/interior-photo/backend

# Start all backend services
docker-compose up -d

# Wait 10 seconds for services to start
sleep 10

# Run migrations (first time only)
docker-compose exec api alembic upgrade head

# View logs (optional)
docker-compose logs -f api
```

#### Terminal 2: Frontend

```bash
# Navigate to frontend (adjust path as needed)
cd /path/to/interior-photo

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Should show:
# ➜  Local:   http://localhost:5173/
```

#### Terminal 3: Monitor (Optional)

```bash
# Watch Celery worker logs
cd /path/to/interior-photo/backend
docker-compose logs -f celery_worker
```

### 8.2 Verification Checklist

Before using the app, verify all services are running:

```bash
# Backend API
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy",...}

# Frontend
curl http://localhost:5173
# Expected: HTML content

# PostgreSQL
docker-compose exec postgres pg_isready
# Expected: /var/run/postgresql:5432 - accepting connections

# Redis
docker-compose exec redis redis-cli ping
# Expected: PONG

# Celery Worker
docker-compose logs celery_worker | grep "ready"
# Expected: celery@hostname ready.
```

### 8.3 First-Time User Flow

#### Step 1: Open Application

```bash
open http://localhost:5173
# Or manually navigate in browser
```

#### Step 2: Register Account

1. Look for "Register" or "Sign Up" button
2. Enter email, password, name
3. Click "Register"
4. Should automatically log in

**Or test via API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demo123456",
    "name": "Demo User"
  }'
```

#### Step 3: Login (if needed)

1. Enter email and password
2. Click "Login"
3. Tokens stored in localStorage

**Or test via API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demo123456"
  }'
```

#### Step 4: Upload Image

1. Click upload area or drag & drop image
2. Select a photo of a room (JPG, PNG, WEBP)
3. Image should preview

#### Step 5: Choose Style

1. Select **Vibe**: Modern, Minimalist, Cozy, etc.
2. Select **Colors**: Neutral, Warm, Cool, etc.
3. Optionally add description: "Add more plants"
4. Optionally upload reference images

#### Step 6: Transform

1. Click "Transform Space" button
2. Wait for processing (5-15 seconds)
3. View result with before/after slider

### 8.4 End-to-End Test

**Complete test scenario:**

```bash
# 1. Start backend
cd backend
docker-compose up -d
docker-compose exec api alembic upgrade head

# 2. Start frontend (new terminal)
cd ..
npm run dev

# 3. Test API (new terminal)
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234","name":"Test"}' \
  | jq

# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}' \
  | jq -r '.access_token')

# Check user info
curl http://localhost:8000/api/v1/user/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# Check credits
curl http://localhost:8000/api/v1/user/credits \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# 4. Test in browser
# Open http://localhost:5173
# Login with test@test.com / test1234
# Upload image and transform
```

### 8.5 Development Workflow

#### Making Changes

**Backend Changes:**
```bash
# Edit Python files in backend/app/
# Changes auto-reload with uvicorn --reload

# If you change models, create migration:
docker-compose exec api alembic revision --autogenerate -m "Add new field"
docker-compose exec api alembic upgrade head

# If you change dependencies, rebuild:
docker-compose up -d --build
```

**Frontend Changes:**
```bash
# Edit files in src/
# Vite hot-reloads automatically
# Just save and browser updates

# If you add dependencies:
npm install new-package
# Restart dev server (Ctrl+C, npm run dev)
```

#### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Make changes
# ...

# Commit
git add .
git commit -m "Add amazing feature"

# Push
git push origin feature/my-new-feature

# Create pull request on GitHub
```

### 8.6 Stopping the Application

**Stop Frontend:**
```bash
# In terminal running npm run dev
# Press Ctrl+C
```

**Stop Backend:**
```bash
# In backend directory
docker-compose down

# To also remove volumes (⚠️ deletes database)
docker-compose down -v
```

**Stop All and Clean Up:**
```bash
# Stop frontend (Ctrl+C in terminal)

# Stop backend
cd backend
docker-compose down

# Remove all unused Docker resources
docker system prune -a
```

---

## 9. Testing

### 9.1 Manual Testing

#### Frontend Testing

**UI Components:**
- [ ] App loads without errors
- [ ] Upload area works (drag & drop, click)
- [ ] Image preview shows after upload
- [ ] All vibe buttons are clickable
- [ ] All color buttons are clickable
- [ ] Description textarea works
- [ ] Reference images can be added/removed
- [ ] Transform button is clickable
- [ ] Loading state shows during processing
- [ ] Result displays in before/after slider
- [ ] Slider moves smoothly
- [ ] Download button works

**Authentication:**
- [ ] Can register new user
- [ ] Can login with credentials
- [ ] Can logout
- [ ] Protected routes require login
- [ ] Credits display correctly
- [ ] Invalid credentials show error

#### Backend Testing

**Using API Documentation:**

1. Open http://localhost:8000/docs
2. Test each endpoint:

**Auth Endpoints:**
```
POST /api/v1/auth/register
- Try with valid data → Should return user
- Try with duplicate email → Should return error

POST /api/v1/auth/login
- Try with valid credentials → Should return tokens
- Try with invalid credentials → Should return 401

POST /api/v1/auth/refresh
- Try with valid refresh token → Should return new tokens
```

**User Endpoints:**
```
GET /api/v1/user/me
- With valid token → Should return user data
- Without token → Should return 401

GET /api/v1/user/credits
- With valid token → Should return credits
```

**Transform Endpoints:**
```
POST /api/v1/transform/transform
- With image + preferences → Should return job_id
- Without image → Should return 400
- Large image → Should return 400
- Invalid format → Should return 400

GET /api/v1/transform/{job_id}
- Valid job_id → Should return status
- Invalid job_id → Should return 404

GET /api/v1/transform/history
- With auth → Should return user's history
- Without auth → Should return 401
```

### 9.2 Automated Testing

#### Backend Unit Tests

```bash
cd backend

# Activate virtual environment (if not using Docker)
source venv/bin/activate

# Install test dependencies (if not already)
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_auth.py

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

**Create test file example:**

```python
# backend/tests/test_api/test_transform.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_transform_without_auth():
    """Test transformation requires authentication"""
    response = client.post("/api/v1/transform/transform")
    assert response.status_code == 401

def test_transform_without_image():
    """Test transformation requires image"""
    # Get auth token first
    # ... (implement)

    response = client.post(
        "/api/v1/transform/transform",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "vibe": "modern",
            "colors": "neutral"
        }
    )
    assert response.status_code == 422  # Validation error
```

#### Frontend Unit Tests

```bash
# Install testing libraries
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom

# Run tests
npm run test

# Run with coverage
npm run test:coverage
```

**Create test file example:**

```typescript
// src/components/__tests__/ImageUpload.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ImageUpload from '../ImageUpload';

describe('ImageUpload', () => {
  it('renders upload area', () => {
    render(<ImageUpload onImageSelect={() => {}} label="Test" description="Test" />);
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    const mockOnSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnSelect} label="Test" description="Test" />);

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const input = screen.getByRole('button').querySelector('input');

    fireEvent.change(input!, { target: { files: [file] } });

    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockOnSelect).toHaveBeenCalled();
  });
});
```

### 9.3 Integration Testing

**End-to-End Flow Test:**

```bash
# Create integration test script
cat > test_e2e.sh << 'EOF'
#!/bin/bash

set -e

API_URL="http://localhost:8000"
EMAIL="test_$(date +%s)@example.com"
PASSWORD="testpass123"

echo "=== E2E Test ==="

# 1. Register
echo "1. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"name\":\"Test User\"}")

echo "   Response: $REGISTER_RESPONSE"
USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.id')
echo "   User ID: $USER_ID"

# 2. Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "   Token: ${TOKEN:0:20}..."

# 3. Get user info
echo "3. Getting user info..."
USER_INFO=$(curl -s $API_URL/api/v1/user/me \
  -H "Authorization: Bearer $TOKEN")
echo "   User: $(echo $USER_INFO | jq -r '.email')"

# 4. Check credits
echo "4. Checking credits..."
CREDITS=$(curl -s $API_URL/api/v1/user/credits \
  -H "Authorization: Bearer $TOKEN")
echo "   Credits: $(echo $CREDITS | jq -r '.credits')"

# 5. Test transformation (with dummy image)
echo "5. Testing transformation..."
# Create test image
convert -size 800x600 xc:white test_room.jpg 2>/dev/null || echo "   (Skipping - ImageMagick not installed)"

if [ -f test_room.jpg ]; then
  TRANSFORM_RESPONSE=$(curl -s -X POST $API_URL/api/v1/transform/transform \
    -H "Authorization: Bearer $TOKEN" \
    -F "image=@test_room.jpg" \
    -F "vibe=modern" \
    -F "colors=neutral")

  JOB_ID=$(echo $TRANSFORM_RESPONSE | jq -r '.job_id')
  echo "   Job ID: $JOB_ID"

  # Wait and check status
  sleep 3
  STATUS=$(curl -s $API_URL/api/v1/transform/$JOB_ID \
    -H "Authorization: Bearer $TOKEN")
  echo "   Status: $(echo $STATUS | jq -r '.status')"

  rm test_room.jpg
fi

echo ""
echo "=== E2E Test Complete ==="
EOF

chmod +x test_e2e.sh
./test_e2e.sh
```

### 9.4 Load Testing

**Using Apache Bench:**

```bash
# Install Apache Bench
# macOS: brew install apache2
# Ubuntu: sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# Results show:
# - Requests per second
# - Time per request
# - Transfer rate
# - Connection times
```

**Using Hey:**

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Test API
hey -n 1000 -c 50 http://localhost:8000/api/v1/health

# With authentication
hey -n 100 -c 10 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/user/me
```

### 9.5 Database Testing

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U interiorai -d interiorai

# Check tables
\dt

# Count users
SELECT COUNT(*) FROM users;

# Count transformations
SELECT COUNT(*) FROM transformations;

# Check recent transformations
SELECT job_id, status, created_at
FROM transformations
ORDER BY created_at DESC
LIMIT 10;

# Check user with most transformations
SELECT users.email, COUNT(transformations.id) as count
FROM users
LEFT JOIN transformations ON users.id = transformations.user_id
GROUP BY users.email
ORDER BY count DESC;

# Exit
\q
```

---

## 10. API Documentation

### 10.1 Interactive API Documentation

**Swagger UI:**
- URL: http://localhost:8000/docs
- Features:
  - Interactive endpoint testing
  - Request/response schemas
  - Try it out functionality
  - Example values

**ReDoc:**
- URL: http://localhost:8000/redoc
- Features:
  - Clean, readable documentation
  - Search functionality
  - Code samples
  - Download OpenAPI spec

### 10.2 Authentication

All authenticated endpoints require JWT token in header:

```
Authorization: Bearer <access_token>
```

**Getting tokens:**

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Using tokens:**

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:8000/api/v1/user/me \
  -H "Authorization: Bearer $TOKEN"
```

### 10.3 API Endpoints Reference

#### Authentication Endpoints

**POST /api/v1/auth/register**

Register a new user.

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

Response (201):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "credits": 10,
  "subscription_tier": "free"
}
```

---

**POST /api/v1/auth/login**

Login and receive JWT tokens.

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

**POST /api/v1/auth/refresh**

Refresh access token using refresh token.

Request:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### User Endpoints

**GET /api/v1/user/me**

Get current user information.

Requires: Authentication

Response (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "credits": 5,
  "subscription_tier": "free",
  "created_at": "2025-01-01T10:00:00Z"
}
```

---

**GET /api/v1/user/credits**

Get user's remaining credits.

Requires: Authentication

Response (200):
```json
{
  "credits": 5,
  "subscription_tier": "free"
}
```

#### Transformation Endpoints

**POST /api/v1/transform/transform**

Create a new interior transformation.

Requires: Authentication (optional for anonymous users)

Request (multipart/form-data):
```
image: <file>                 # Required, JPG/PNG/WEBP, max 10MB
vibe: "modern"               # Required, one of: modern, minimalist, cozy, industrial, bohemian, scandinavian, luxurious, rustic
colors: "neutral"            # Required, one of: neutral, warm, cool, earthy, pastel, bold
description: "Add plants"    # Optional
reference_images: [<file>]   # Optional, max 6 files
```

Response (202 Accepted):
```json
{
  "job_id": "abc123def456",
  "status": "pending",
  "original_url": "https://cdn.example.com/originals/2025/01/04/uuid.jpg",
  "transformed_url": null,
  "processing_time": null,
  "created_at": "2025-01-04T10:30:00Z",
  "completed_at": null,
  "metadata": {
    "vibe": "modern",
    "colors": "neutral"
  }
}
```

---

**GET /api/v1/transform/{job_id}**

Get transformation status and result.

Requires: Authentication (if transformation was created by authenticated user)

Response (200):
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "original_url": "https://cdn.example.com/originals/2025/01/04/uuid.jpg",
  "transformed_url": "https://cdn.example.com/transformed/2025/01/04/uuid.jpg",
  "processing_time": 8.5,
  "created_at": "2025-01-04T10:30:00Z",
  "completed_at": "2025-01-04T10:30:15Z",
  "metadata": {
    "vibe": "modern",
    "colors": "neutral",
    "description": "Add plants"
  }
}
```

Status values:
- `pending`: Queued, not yet processing
- `processing`: Currently being transformed
- `completed`: Successfully completed
- `failed`: Error occurred

---

**GET /api/v1/transform/history**

Get user's transformation history.

Requires: Authentication

Query Parameters:
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)

Response (200):
```json
{
  "transformations": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "job_id": "abc123def456",
      "status": "completed",
      "original_image_url": "https://...",
      "transformed_image_url": "https://...",
      "vibe": "modern",
      "colors": "neutral",
      "created_at": "2025-01-04T10:30:00Z"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

#### Health Check

**GET /api/v1/health**

Health check endpoint.

Response (200):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### 10.4 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400`: Bad Request - Invalid input
- `401`: Unauthorized - Authentication required or invalid token
- `402`: Payment Required - Insufficient credits
- `403`: Forbidden - Not enough permissions
- `404`: Not Found - Resource doesn't exist
- `422`: Unprocessable Entity - Validation error
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

### 10.5 Rate Limits

Rate limits by subscription tier (per day):

| Tier       | Transformations/Day | API Requests/Minute |
|------------|---------------------|---------------------|
| Anonymous  | 3                   | 30                  |
| Free       | 5                   | 60                  |
| Pro        | 100                 | 300                 |
| Enterprise | 1000                | Unlimited           |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 2025-01-05T00:00:00Z
```

---

## 11. Troubleshooting

### 11.1 Common Backend Issues

#### Issue: Port 8000 already in use

**Error:**
```
ERROR: for api  Cannot start service api: driver failed programming external connectivity on endpoint backend_api_1:
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or change port in docker-compose.yml:
ports:
  - "8001:8000"  # Use 8001 instead
```

#### Issue: Database connection failed

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check if PostgreSQL container is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready

# Verify connection string in .env
DATABASE_URL=postgresql://interiorai:password@postgres:5432/interiorai
```

#### Issue: Redis connection failed

**Error:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis
```

#### Issue: Celery worker not processing jobs

**Symptoms:**
- Transformations stuck in "pending" status
- No logs in celery_worker

**Solution:**
```bash
# Check Celery worker status
docker-compose logs celery_worker

# Look for errors like:
# - Connection to Redis failed
# - Import errors
# - Configuration errors

# Restart Celery worker
docker-compose restart celery_worker

# Check if tasks are queued in Redis
docker-compose exec redis redis-cli
> KEYS *
> LLEN celery

# Manually trigger a test task
docker-compose exec api python -c "
from app.tasks.transformation_tasks import process_transformation
result = process_transformation.delay('test-id', 'url', 'modern', 'neutral')
print(f'Task ID: {result.id}')
"
```

#### Issue: Replicate API error

**Error:**
```
replicate.exceptions.ReplicateError: Your API token is invalid
```

**Solution:**
```bash
# Verify Replicate API token in .env
cat .env | grep REPLICATE_API_TOKEN

# Test token
curl https://api.replicate.com/v1/models/adirik/interior-design \
  -H "Authorization: Token $REPLICATE_API_TOKEN"

# Get new token from replicate.com if needed
# Update .env and restart:
docker-compose restart api celery_worker
```

#### Issue: S3 upload failed

**Error:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**
```bash
# Check AWS credentials in .env
cat .env | grep AWS_

# Verify credentials with AWS CLI
aws configure list

# Test S3 access
aws s3 ls s3://your-bucket-name

# Check bucket permissions
aws s3api get-bucket-policy --bucket your-bucket-name

# Update .env with correct credentials
# Restart services
docker-compose restart api
```

### 11.2 Common Frontend Issues

#### Issue: Cannot connect to backend

**Error in console:**
```
Failed to fetch
TypeError: Network request failed
```

**Solution:**
```bash
# 1. Verify backend is running
curl http://localhost:8000/api/v1/health

# 2. Check CORS configuration in backend
# backend/.env should have:
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 3. Check API URL in frontend
# Look for API_BASE_URL or similar
grep -r "localhost:8000" src/

# 4. Restart both frontend and backend
```

#### Issue: Module not found errors

**Error:**
```
Error: Cannot find module 'framer-motion'
```

**Solution:**
```bash
# Clear and reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# If specific package missing
npm install framer-motion

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

#### Issue: TypeScript errors

**Error:**
```
Property 'xyz' does not exist on type 'ABC'
```

**Solution:**
```bash
# Restart TypeScript server in VS Code
# Cmd+Shift+P → "TypeScript: Restart TS Server"

# Check tsconfig.json exists
cat tsconfig.json

# Regenerate types if using API codegen
npm run generate-types  # If script exists

# Install type definitions if missing
npm install --save-dev @types/node @types/react
```

#### Issue: Build fails

**Error:**
```
npm run build
> Build failed
```

**Solution:**
```bash
# Check for TypeScript errors
npm run type-check  # If script exists

# Check for linting errors
npm run lint

# Clear cache and rebuild
rm -rf dist
npm run build

# Check build output for specific errors
npm run build 2>&1 | tee build.log
```

### 11.3 Docker Issues

#### Issue: Out of disk space

**Error:**
```
no space left on device
```

**Solution:**
```bash
# Check Docker disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused containers
docker container prune

# Remove unused volumes
docker volume prune

# Complete cleanup (⚠️ removes everything not running)
docker system prune -a --volumes
```

#### Issue: Container won't start

**Solution:**
```bash
# Check container logs
docker-compose logs <service-name>

# Inspect container
docker inspect backend_api_1

# Remove and recreate container
docker-compose rm -f api
docker-compose up -d api

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 11.4 Performance Issues

#### Issue: Slow API response

**Solution:**
```bash
# Check database query performance
docker-compose exec postgres psql -U interiorai -d interiorai

# Enable query logging
ALTER DATABASE interiorai SET log_statement = 'all';

# Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Add database indexes if needed
CREATE INDEX idx_transformations_user_id ON transformations(user_id);
CREATE INDEX idx_transformations_status ON transformations(status);
```

#### Issue: High memory usage

**Solution:**
```bash
# Check Docker resource usage
docker stats

# Increase Docker resources in Docker Desktop
# Settings → Resources → Memory (8GB recommended)

# Limit container resources in docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

### 11.5 Getting Help

**Check logs first:**
```bash
# Backend API logs
docker-compose logs api

# Celery worker logs
docker-compose logs celery_worker

# All logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f
```

**Enable debug mode:**
```bash
# Backend .env
DEBUG=True
ENVIRONMENT=development

# Restart services
docker-compose restart
```

**Check service health:**
```bash
# Health endpoint
curl http://localhost:8000/api/v1/health | jq

# Database
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

---

**This is Part 2 of the Master Documentation.**

**Continue to MASTER_DOCUMENTATION_PART3.md for:**
- Production Deployment Guide
- Environment Variables Reference
- Security Best Practices
- Monitoring & Logging
- Scaling Strategies
- Backup & Recovery

Shall I create Part 3 with deployment and production details?
