# Interior AI - Complete Setup & Development Guide
## From Zero to Production-Ready AI Interior Design Application

**Version:** 1.0.0
**Last Updated:** January 2025
**Estimated Setup Time:** 30-60 minutes

---

## 📋 Table of Contents

1. [Introduction](#1-introduction)
2. [Prerequisites & Requirements](#2-prerequisites--requirements)
3. [Project Overview](#3-project-overview)
4. [Initial Setup](#4-initial-setup)
5. [Backend Setup - Detailed](#5-backend-setup---detailed)
6. [Frontend Setup - Detailed](#6-frontend-setup---detailed)
7. [API Integration](#7-api-integration)
8. [Running the Application](#8-running-the-application)
9. [Testing](#9-testing)
10. [API Documentation](#10-api-documentation)
11. [Troubleshooting](#11-troubleshooting)
12. [Production Deployment](#12-production-deployment)
13. [Development Workflow](#13-development-workflow)
14. [Advanced Configuration](#14-advanced-configuration)

---

## 1. Introduction

### What is Interior AI?

Interior AI is a full-stack web application that uses artificial intelligence to transform interior spaces. Users can upload photos of their rooms and receive AI-generated redesigns based on their style preferences (modern, minimalist, cozy, etc.) and color palettes.

### Key Features

- 🎨 **AI-Powered Transformations** - Using Replicate's adirik/interior-design model
- 🖼️ **Before/After Slider** - Interactive comparison of original and transformed images
- 👤 **User Authentication** - JWT-based secure authentication
- 💳 **Credits System** - Free and paid tiers with usage limits
- 📊 **Transformation History** - Track all your past designs
- 🎭 **Multiple Styles** - 8 design vibes and 6 color palettes
- 📷 **Reference Images** - Upload inspiration photos
- ⚡ **Real-time Updates** - Watch transformations process live

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- Framer Motion (animations)
- Lucide React (icons)

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL (database)
- Redis (caching & queue)
- Celery (background jobs)
- SQLAlchemy (ORM)
- Replicate AI (image transformation)
- AWS S3 + CloudFront (image storage)

---

## 2. Prerequisites & Requirements

### 2.1 System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB free space
- OS: macOS, Linux, or Windows 10+

**Recommended:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB free space
- OS: macOS or Linux (for best Docker performance)

### 2.2 Required Software

#### Essential (Must Have):

1. **Docker & Docker Compose** (Recommended)
   - Docker Desktop 4.0+ (includes Docker Compose)
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)

   **Verify installation:**
   ```bash
   docker --version
   # Should show: Docker version 24.0.0 or higher

   docker-compose --version
   # Should show: Docker Compose version 2.0.0 or higher
   ```

2. **Node.js & npm**
   - Node.js 18+ (LTS recommended)
   - npm 9+
   - [Download Node.js](https://nodejs.org/)

   **Verify installation:**
   ```bash
   node --version
   # Should show: v18.0.0 or higher

   npm --version
   # Should show: 9.0.0 or higher
   ```

3. **Git**
   - Git 2.30+
   - [Download Git](https://git-scm.com/)

   **Verify installation:**
   ```bash
   git --version
   # Should show: git version 2.30.0 or higher
   ```

#### Optional (For Manual Backend Setup):

4. **Python** (if not using Docker for backend)
   - Python 3.11+
   - pip 23+

   **Verify installation:**
   ```bash
   python3 --version
   # Should show: Python 3.11.0 or higher

   pip3 --version
   # Should show: pip 23.0 or higher
   ```

5. **PostgreSQL** (if not using Docker)
   - PostgreSQL 15+
   - [Download PostgreSQL](https://www.postgresql.org/download/)

6. **Redis** (if not using Docker)
   - Redis 7+
   - [Download Redis](https://redis.io/download)

### 2.3 Required API Keys & Services

You'll need accounts and API keys for:

#### 1. **Replicate** (Required - AI Model)

   **Sign up:** [https://replicate.com](https://replicate.com)

   **Get API Key:**
   1. Create account at replicate.com
   2. Go to Account Settings
   3. Navigate to API Tokens
   4. Copy your API token (starts with `r8_`)

   **Cost:** ~$0.01-0.015 per transformation (pay-as-you-go)

#### 2. **AWS Account** (Required - Image Storage)

   **Sign up:** [https://aws.amazon.com](https://aws.amazon.com)

   **Setup S3 Bucket:**
   ```bash
   # Login to AWS Console
   # Go to S3 service
   # Click "Create bucket"
   # Name: interior-ai-images (or your choice)
   # Region: us-east-1 (or nearest to you)
   # Uncheck "Block all public access"
   # Create bucket
   ```

   **Get AWS Credentials:**
   1. Go to IAM Console
   2. Create new user: `interior-ai-app`
   3. Attach policy: `AmazonS3FullAccess`
   4. Create access key
   5. Save Access Key ID and Secret Access Key

   **Cost:** ~$5-10/month for 10k images (with lifecycle policies)

#### 3. **CloudFront** (Optional - CDN)

   **Setup:**
   1. Go to CloudFront in AWS Console
   2. Create distribution
   3. Origin: Your S3 bucket
   4. Copy CloudFront domain name

   **Cost:** ~$40/month for 500GB transfer (optional but recommended)

### 2.4 Code Editor

**Recommended:**
- VS Code with extensions:
  - Python
  - Pylance
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
  - Docker

**Alternatives:**
- PyCharm (for backend)
- WebStorm (for frontend)
- Any modern code editor

### 2.5 Pre-Setup Checklist

Before proceeding, ensure you have:

- [ ] Docker installed and running
- [ ] Node.js and npm installed
- [ ] Git installed
- [ ] Replicate account created and API token obtained
- [ ] AWS account created
- [ ] S3 bucket created
- [ ] AWS access key and secret key obtained
- [ ] Code editor installed
- [ ] Terminal/command line access
- [ ] Internet connection (for downloading dependencies)

---

## 3. Project Overview

### 3.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│                     (Web Browser)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    FRONTEND                                 │
│   React + TypeScript + Vite + TailwindCSS                  │
│   Port: 3000 (dev) / 5173 (vite)                          │
│                                                             │
│   Components:                                               │
│   ├── App.tsx (main)                                       │
│   ├── ImageUpload (drag & drop)                           │
│   ├── StylePreferences (vibe & colors)                    │
│   ├── BeforeAfterSlider (comparison)                      │
│   └── ReferenceImages (inspiration)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ REST API (JSON)
                     │ /api/v1/*
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    BACKEND                                  │
│            FastAPI + Python 3.11                            │
│            Port: 8000                                       │
│                                                             │
│   Endpoints:                                                │
│   ├── /auth/register, /auth/login                         │
│   ├── /transform/transform (upload)                       │
│   ├── /transform/{job_id} (status)                        │
│   ├── /user/me, /user/credits                            │
│   └── /health (monitoring)                                │
│                                                             │
│   Services:                                                 │
│   ├── AuthService (JWT)                                   │
│   ├── TransformationService                               │
│   ├── S3Service (image storage)                          │
│   └── ReplicateService (AI)                              │
└─────┬──────────┬──────────┬──────────┬────────────────────┘
      │          │          │          │
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│PostgreSQL│ │  Redis   │ │  Celery  │ │  Replicate   │
│  Port:   │ │  Port:   │ │  Worker  │ │     API      │
│  5432    │ │  6379    │ │          │ │              │
│          │ │          │ │          │ │              │
│ - Users  │ │ - Cache  │ │ - Jobs   │ │ - AI Model   │
│ - Trans  │ │ - Queue  │ │ - Tasks  │ │ - Transform  │
│ - Refs   │ │ - Limit  │ │          │ │              │
└──────────┘ └──────────┘ └──────────┘ └──────┬───────┘
                                              │
                                              │
                                              ▼
                                        ┌──────────────┐
                                        │   AWS S3     │
                                        │ + CloudFront │
                                        │              │
                                        │ - Original   │
                                        │ - Transform  │
                                        │ - Reference  │
                                        └──────────────┘
```

### 3.2 Data Flow

**User Registration/Login:**
```
User → Frontend → POST /api/v1/auth/register
                → Backend validates
                → Creates user in PostgreSQL
                → Returns JWT tokens
Frontend stores tokens → Used for authenticated requests
```

**Image Transformation:**
```
1. User uploads image + preferences
   → Frontend: POST /api/v1/transform/transform

2. Backend receives request
   → Validates image (size, format)
   → Uploads to S3 (originals/)
   → Creates transformation record in PostgreSQL
   → Queues Celery job
   → Returns job_id immediately

3. Frontend polls for status
   → GET /api/v1/transform/{job_id}
   → Shows loading state

4. Celery worker (background)
   → Picks up job from Redis queue
   → Builds AI prompt from preferences
   → Calls Replicate API
   → Waits for AI transformation (~5-10 seconds)
   → Downloads result from Replicate
   → Uploads to S3 (transformed/)
   → Updates PostgreSQL with result URL
   → Marks job as completed

5. Frontend receives completed status
   → Displays transformed image
   → Shows before/after slider
```

### 3.3 Directory Structure

```
interior-photo/
│
├── frontend/                          # React frontend (if separate)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── services/                 # API integration
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app
│   │   ├── core/                     # Config, security
│   │   ├── db/                       # Database
│   │   ├── models/                   # SQLAlchemy models
│   │   ├── api/v1/endpoints/         # API routes
│   │   ├── services/                 # Business logic
│   │   ├── tasks/                    # Celery tasks
│   │   └── utils/                    # Utilities
│   ├── alembic/                      # Migrations
│   ├── tests/                        # Tests
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env
│
├── docs/                              # Documentation
│   ├── MASTER_DOCUMENTATION.md       # This file
│   ├── API.md                        # API reference
│   └── DEPLOYMENT.md                 # Deploy guide
│
├── .gitignore
└── README.md
```

### 3.4 Key Concepts

#### JWT Authentication
- Access token (15 min expiry) for API requests
- Refresh token (7 days) for getting new access tokens
- Stored in frontend (memory + httpOnly cookie)

#### Credits System
- Each transformation costs 1 credit
- Free tier: 5 transformations/day
- Pro tier: 100 transformations/day
- Enterprise: 1000 transformations/day

#### Background Jobs
- Transformations run in background (Celery)
- Frontend doesn't wait for completion
- Polls for status updates every 1-2 seconds
- Supports long-running AI operations

#### Image Storage
- Original images: S3 bucket (originals/)
- Transformed images: S3 bucket (transformed/)
- Reference images: S3 bucket (references/)
- CDN (CloudFront) for fast delivery worldwide

---

## 4. Initial Setup

### 4.1 Clone or Navigate to Repository

```bash
# If you have the code
cd interior-photo

# If cloning from repository
git clone <your-repo-url>
cd interior-photo

# Check current structure
ls -la
# Should see: backend/, src/ (or frontend/), package.json, README.md, etc.
```

### 4.2 Project Structure Verification

```bash
# Verify backend exists
ls -la backend/
# Should see: app/, requirements.txt, Dockerfile, docker-compose.yml

# Verify frontend exists
ls -la src/        # If frontend in root
# OR
ls -la frontend/   # If frontend in separate folder
# Should see: App.tsx, main.tsx, components/

# Check documentation
ls -la *.md
# Should see: README.md, BACKEND_PLAN.md, AI_MODELS_COMPARISON.md, etc.
```

### 4.3 Environment Setup Decision

You have two options:

**Option A: Docker (Recommended)** ✅
- Pros: Easier setup, consistent environment, includes all services
- Cons: Requires Docker Desktop, uses more resources
- Best for: Most developers, production-like environment

**Option B: Manual Setup**
- Pros: More control, lighter weight, easier debugging
- Cons: More setup steps, need to manage services manually
- Best for: Experienced developers, custom configurations

**We'll cover both options in the following sections.**

---

## 5. Backend Setup - Detailed

### 5.1 Backend Setup with Docker (Recommended)

#### Step 1: Navigate to Backend Directory

```bash
cd backend
pwd
# Should show: /path/to/interior-photo/backend
```

#### Step 2: Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Verify it was created
ls -la .env
# Should show: .env file
```

#### Step 3: Configure Environment Variables

Open `.env` in your code editor:

```bash
# Using VS Code
code .env

# Or using nano
nano .env

# Or using vim
vim .env
```

**Update the following values:**

```bash
# Application
APP_NAME=Interior AI
APP_VERSION=1.0.0
DEBUG=True                              # Set to False in production
ENVIRONMENT=development                 # Change to 'production' later

# Server
HOST=0.0.0.0
PORT=8000

# Database (Docker will use these)
DATABASE_URL=postgresql://interiorai:changeme123@postgres:5432/interiorai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0

# Redis (Docker will use these)
REDIS_URL=redis://redis:6379/0

# Security - CHANGE THIS!
SECRET_KEY=your-super-secret-key-here-use-python-secrets-token-urlsafe-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3 - UPDATE WITH YOUR VALUES!
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE        # Your AWS access key
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG  # Your AWS secret key
AWS_REGION=us-east-1                          # Your bucket region
S3_BUCKET_NAME=interior-ai-images             # Your bucket name
S3_BUCKET_URL=https://interior-ai-images.s3.amazonaws.com
CLOUDFRONT_URL=https://d1234567890.cloudfront.net  # Optional

# Replicate - UPDATE WITH YOUR TOKEN!
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxx  # Your Replicate token
REPLICATE_MODEL=adirik/interior-design:76604baddc85a8fdb0b3cad03c9fd9634ff8c64c0e15f74e9f2be61dc63e5c7f

# Celery (Docker will use these)
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Rate Limiting
RATE_LIMIT_FREE_DAILY=5
RATE_LIMIT_PRO_DAILY=100
RATE_LIMIT_ENTERPRISE_DAILY=1000

# File Upload
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_TYPES=jpg,jpeg,png,webp

# CORS - Update if frontend runs on different port
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Monitoring (Optional)
SENTRY_DSN=
```

**Generate a secure SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and paste it as SECRET_KEY in .env
```

#### Step 4: Start Docker Services

```bash
# Make sure Docker Desktop is running first!

# Start all services (PostgreSQL, Redis, API, Celery Worker)
docker-compose up -d

# This will:
# - Download required Docker images (first time only)
# - Create containers for postgres, redis, api, celery_worker
# - Start all services in background (detached mode)
```

**Expected output:**
```
Creating network "backend_default" with the default driver
Creating volume "backend_postgres_data" with default driver
Creating backend_postgres_1 ... done
Creating backend_redis_1    ... done
Creating backend_api_1      ... done
Creating backend_celery_worker_1 ... done
```

#### Step 5: Verify Services Are Running

```bash
# Check status of all services
docker-compose ps

# Should show something like:
# NAME                    STATUS          PORTS
# backend_api_1           Up 10 seconds   0.0.0.0:8000->8000/tcp
# backend_celery_worker_1 Up 10 seconds
# backend_postgres_1      Up 15 seconds   0.0.0.0:5432->5432/tcp
# backend_redis_1         Up 15 seconds   0.0.0.0:6379->6379/tcp
```

#### Step 6: Run Database Migrations

```bash
# Run Alembic migrations to create database tables
docker-compose exec api alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, Initial schema
```

#### Step 7: Test Backend

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Should return:
# {"status":"healthy","version":"1.0.0","environment":"development","checks":{"database":"healthy","redis":"healthy"}}

# Or open in browser:
open http://localhost:8000/api/v1/health
```

#### Step 8: Access API Documentation

```bash
# Open Swagger UI in browser
open http://localhost:8000/docs

# Or visit:
# http://localhost:8000/docs        (Swagger UI)
# http://localhost:8000/redoc       (ReDoc)
```

#### Step 9: View Logs (Optional)

```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View Celery worker logs
docker-compose logs -f celery_worker

# View last 100 lines
docker-compose logs --tail=100 api

# Press Ctrl+C to stop viewing logs
```

#### Step 10: Common Docker Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database data)
docker-compose down -v

# Restart specific service
docker-compose restart api

# Rebuild containers after code changes
docker-compose up -d --build

# Execute command in container
docker-compose exec api python -c "print('Hello')"

# Access container shell
docker-compose exec api bash

# View resource usage
docker stats
```

### 5.2 Backend Setup - Manual (Without Docker)

#### Step 1: Install System Dependencies

**On macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Install Redis
brew install redis
brew services start redis

# Install Python
brew install python@3.11
```

**On Ubuntu/Debian:**
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql-15 postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Redis
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip
```

**On Windows:**
- Download and install PostgreSQL from postgresql.org
- Download and install Redis from redis.io/download
- Download and install Python 3.11 from python.org

#### Step 2: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql postgres

# In psql prompt, run:
CREATE DATABASE interiorai;
CREATE USER interiorai WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE interiorai TO interiorai;

# Exit psql
\q
```

#### Step 3: Verify Redis is Running

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

#### Step 4: Setup Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Your prompt should now show (venv)
```

#### Step 5: Install Python Dependencies

```bash
# Make sure virtual environment is activated

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will take a few minutes...
```

#### Step 6: Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env file
code .env  # or nano .env, vim .env, etc.
```

**Update these values for manual setup:**

```bash
# Database (update with your local PostgreSQL)
DATABASE_URL=postgresql://interiorai:your_password@localhost:5432/interiorai

# Redis (local)
REDIS_URL=redis://localhost:6379/0

# Celery (local Redis)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Rest of the configuration same as Docker setup
# (AWS, Replicate, etc.)
```

#### Step 7: Run Database Migrations

```bash
# Make sure virtual environment is activated
# Make sure PostgreSQL is running

# Run migrations
alembic upgrade head

# Should see:
# INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, Initial schema
```

#### Step 8: Start Backend Server

```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

#### Step 9: Start Celery Worker (New Terminal)

```bash
# Open a new terminal window
cd backend

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate    # On Windows

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Should see:
# [tasks]
#   . app.tasks.transformation_tasks.process_transformation
# celery@hostname ready.
```

#### Step 10: Test Backend

```bash
# In another terminal, test the API
curl http://localhost:8000/api/v1/health

# Open API docs
open http://localhost:8000/docs
```

### 5.3 Backend Verification Checklist

Once backend is running, verify:

- [ ] API server responds at http://localhost:8000
- [ ] Health check returns "healthy" status
- [ ] API documentation loads at http://localhost:8000/docs
- [ ] PostgreSQL is accessible
- [ ] Redis is accessible
- [ ] Celery worker is running (check logs)
- [ ] Can register a new user via API
- [ ] Can login and receive JWT tokens

**Test user registration:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "name": "Test User"
  }'

# Should return user data with ID
```

---

## 6. Frontend Setup - Detailed

### 6.1 Locate Frontend Files

The frontend can be in two places:

**Option A: Frontend in root directory**
```bash
# Check if these exist:
ls -la src/
ls -la package.json
ls -la index.html
# If yes, frontend is in root
```

**Option B: Frontend in separate directory**
```bash
# Check if these exist:
ls -la frontend/src/
ls -la frontend/package.json
# If yes, frontend is in frontend/ folder
cd frontend
```

For this guide, we'll assume **frontend is in the root directory**. If yours is in `frontend/`, just `cd frontend` first.

### 6.2 Install Frontend Dependencies

```bash
# Make sure you're in the directory with package.json
pwd
# Should show the frontend directory

# Install dependencies
npm install

# This will:
# - Read package.json
# - Download all dependencies to node_modules/
# - Create package-lock.json
# - May take 2-5 minutes depending on internet speed
```

**Expected output:**
```
added 280 packages, and audited 281 packages in 45s

67 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
```

### 6.3 Configure Frontend Environment (if needed)

Some projects need environment variables for the frontend. Check if there's a `.env` file needed:

```bash
# Check if .env.example exists
ls -la .env.example

# If it exists, copy it
cp .env.example .env

# Edit if needed
code .env
```

**Common frontend environment variables:**
```bash
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Interior AI
```

### 6.4 Update API Base URL

The frontend needs to know where the backend API is running.

**Find API configuration:**
```bash
# Search for API URL configuration
grep -r "localhost:8000" src/
# or
grep -r "API_URL" src/
# or
grep -r "baseURL" src/
```

**Common locations for API config:**
- `src/config.ts`
- `src/services/api.ts`
- `src/utils/api.ts`
- `src/constants.ts`

**If you need to create an API service, create:**

```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  auth: {
    register: `${API_BASE_URL}/api/v1/auth/register`,
    login: `${API_BASE_URL}/api/v1/auth/login`,
    refresh: `${API_BASE_URL}/api/v1/auth/refresh`,
  },
  user: {
    me: `${API_BASE_URL}/api/v1/user/me`,
    credits: `${API_BASE_URL}/api/v1/user/credits`,
  },
  transform: {
    create: `${API_BASE_URL}/api/v1/transform/transform`,
    status: (jobId: string) => `${API_BASE_URL}/api/v1/transform/${jobId}`,
    history: `${API_BASE_URL}/api/v1/transform/history`,
  },
};

// Helper function to get auth headers
export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};
```

### 6.5 Start Frontend Development Server

```bash
# Start Vite development server
npm run dev

# Should see:
#   VITE v5.0.8  ready in 500 ms
#
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose
#   ➜  press h to show help
```

**Note:** Vite uses port 5173 by default. If you need port 3000, update `vite.config.ts`:

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
})
```

Then restart:
```bash
# Stop server (Ctrl+C)
# Start again
npm run dev
```

### 6.6 Open Application in Browser

```bash
# Automatically open browser
open http://localhost:5173

# Or manually navigate to:
# http://localhost:5173
# or
# http://localhost:3000
```

### 6.7 Frontend Verification

You should see:
- [ ] Application loads without errors
- [ ] Beautiful gradient background (purple theme)
- [ ] "Interior AI" title
- [ ] Upload area for images
- [ ] Style preference selectors (vibe & colors)
- [ ] No console errors (open browser DevTools)

**Check browser console (F12):**
- Look for any errors (red text)
- Check Network tab for failed requests
- Verify no CORS errors

### 6.8 Common Frontend Issues

**Issue: Port already in use**
```
Error: Port 5173 is already in use
```
**Solution:**
```bash
# Kill process using port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port in vite.config.ts
```

**Issue: Module not found**
```
Error: Cannot find module 'framer-motion'
```
**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Issue: TypeScript errors**
```
Error: Property 'xyz' does not exist on type...
```
**Solution:**
```bash
# Check tsconfig.json is present
# Restart TypeScript server in VS Code
# Cmd/Ctrl + Shift + P → "TypeScript: Restart TS Server"
```

---

## 7. API Integration

### 7.1 Understanding the API Flow

The frontend and backend communicate via REST API:

```
Frontend (React)  ←→  Backend (FastAPI)
http://localhost:5173    http://localhost:8000

Request Flow:
1. User action (e.g., click "Transform")
2. Frontend makes HTTP request
3. Backend processes request
4. Backend returns response
5. Frontend updates UI
```

### 7.2 API Service Implementation

Create a comprehensive API service for the frontend:

```typescript
// src/services/api.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiError {
  detail: string;
}

interface User {
  id: string;
  email: string;
  name?: string;
  credits: number;
  subscription_tier: string;
}

interface TransformationResponse {
  job_id: string;
  status: string;
  original_url: string;
  transformed_url?: string;
  processing_time?: number;
  created_at: string;
  completed_at?: string;
  metadata: Record<string, any>;
}

class ApiService {
  private baseURL = API_BASE_URL;

  // Helper to get auth token
  private getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // Helper to build headers
  private getHeaders(includeAuth = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = this.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  // Helper to handle response
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An error occurred'
      }));
      throw new Error(error.detail);
    }
    return response.json();
  }

  // ========== AUTH ENDPOINTS ==========

  async register(email: string, password: string, name?: string): Promise<User> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(false),
      body: JSON.stringify({ email, password, name }),
    });
    return this.handleResponse<User>(response);
  }

  async login(email: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(false),
      body: JSON.stringify({ email, password }),
    });
    const data = await this.handleResponse<{ access_token: string; refresh_token: string }>(response);

    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // ========== USER ENDPOINTS ==========

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${this.baseURL}/api/v1/user/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<User>(response);
  }

  async getUserCredits(): Promise<{ credits: number; subscription_tier: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/user/credits`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse(response);
  }

  // ========== TRANSFORMATION ENDPOINTS ==========

  async createTransformation(
    image: File,
    vibe: string,
    colors: string,
    description?: string,
    referenceImages?: File[]
  ): Promise<TransformationResponse> {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('vibe', vibe);
    formData.append('colors', colors);
    if (description) {
      formData.append('description', description);
    }
    if (referenceImages) {
      referenceImages.forEach((ref) => {
        formData.append('reference_images', ref);
      });
    }

    const token = this.getAuthToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}/api/v1/transform/transform`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return this.handleResponse<TransformationResponse>(response);
  }

  async getTransformationStatus(jobId: string): Promise<TransformationResponse> {
    const token = this.getAuthToken();
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}/api/v1/transform/${jobId}`, {
      headers,
    });
    return this.handleResponse<TransformationResponse>(response);
  }

  async getTransformationHistory(limit = 10, offset = 0): Promise<{
    transformations: TransformationResponse[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await fetch(
      `${this.baseURL}/api/v1/transform/history?limit=${limit}&offset=${offset}`,
      {
        headers: this.getHeaders(),
      }
    );
    return this.handleResponse(response);
  }

  // ========== HEALTH CHECK ==========

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/health`);
    return this.handleResponse(response);
  }
}

export const apiService = new ApiService();
export default apiService;
```

### 7.3 Integrating API with Frontend Components

**Update App.tsx to use the API:**

```typescript
// src/App.tsx (partial - add to your existing App.tsx)

import { useState } from 'react';
import apiService from './services/api';

function App() {
  const [originalImage, setOriginalImage] = useState<string>('');
  const [transformedImage, setTransformedImage] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleTransform = async () => {
    if (!originalImage) {
      setError('Please upload an image first');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      // Convert base64 to File (if needed)
      // Assuming you have a file object from ImageUpload component
      const file = imageFile; // Your file from upload

      // Create transformation
      const response = await apiService.createTransformation(
        file,
        vibe,
        colors,
        description,
        referenceImages
      );

      setJobId(response.job_id);

      // Poll for status
      pollTransformationStatus(response.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create transformation');
      setIsProcessing(false);
    }
  };

  const pollTransformationStatus = async (jobId: string) => {
    const maxAttempts = 120; // 2 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await apiService.getTransformationStatus(jobId);

        if (status.status === 'completed') {
          setTransformedImage(status.transformed_url!);
          setIsProcessing(false);
        } else if (status.status === 'failed') {
          setError('Transformation failed');
          setIsProcessing(false);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000); // Poll every second
        } else {
          setError('Transformation timeout');
          setIsProcessing(false);
        }
      } catch (err) {
        setError('Failed to get transformation status');
        setIsProcessing(false);
      }
    };

    poll();
  };

  // Rest of your component...
}
```

### 7.4 Authentication Integration

**Create Auth Context:**

```typescript
// src/contexts/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import apiService from '../services/api';

interface AuthContextType {
  user: any | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on mount
    const loadUser = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await apiService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token might be expired
          apiService.logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    await apiService.login(email, password);
    const userData = await apiService.getCurrentUser();
    setUser(userData);
  };

  const register = async (email: string, password: string, name?: string) => {
    await apiService.register(email, password, name);
    // Auto-login after registration
    await login(email, password);
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

**Wrap App with AuthProvider:**

```typescript
// src/main.tsx

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { AuthProvider } from './contexts/AuthContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
)
```

### 7.5 CORS Configuration

If you get CORS errors, ensure backend CORS is configured correctly:

**Backend: app/main.py**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # ["http://localhost:3000", "http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Backend: .env**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 7.6 Testing API Integration

**Test in browser console:**
```javascript
// Open browser console (F12)

// Test health check
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)

// Test registration
fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'testpass123',
    name: 'Test User'
  })
})
  .then(r => r.json())
  .then(console.log)
```

---

**This is Part 1 of the Master Documentation. Continue to MASTER_DOCUMENTATION_PART2.md for:**
- Running the Application (Full workflow)
- Testing (Frontend, Backend, Integration)
- API Documentation
- Troubleshooting Guide
- Production Deployment
- Development Workflow
- Advanced Configuration

Shall I continue with Part 2?
