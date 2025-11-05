# Interior AI Backend

Complete FastAPI backend for AI-powered interior design transformations.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your credentials (Replicate API key, AWS keys, etc.)

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api

# Access API
open http://localhost:8000/docs
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL and Redis
# ... (see Implementation Guide)

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/      # API route handlers
│   ├── core/                  # Core config & security
│   ├── db/                    # Database setup
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── tasks/                 # Celery background tasks
│   ├── utils/                 # Utilities
│   ├── middleware/            # Custom middleware
│   └── main.py               # FastAPI app
├── alembic/                   # Database migrations
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
├── Dockerfile                # Docker configuration
└── docker-compose.yml        # Docker Compose setup
```

## 🔑 Environment Variables

See `.env.example` for all required environment variables.

**Critical settings:**
- `REPLICATE_API_TOKEN` - Get from [replicate.com](https://replicate.com)
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `SECRET_KEY` - Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

## 📚 API Documentation

Once running, access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Architecture

### Tech Stack
- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Queue**: Celery
- **AI Model**: Replicate (adirik/interior-design)
- **Storage**: AWS S3 + CloudFront

### Key Features
- ✅ JWT Authentication
- ✅ Rate Limiting (Redis-based)
- ✅ Background Job Processing (Celery)
- ✅ Real-time Updates (Server-Sent Events)
- ✅ Image Upload & Validation
- ✅ AI-powered Transformations
- ✅ User Credits System
- ✅ Comprehensive Error Handling

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_auth.py
```

## 📊 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 🔄 Background Jobs

The app uses Celery for async processing of AI transformations:

```bash
# Start worker
celery -A app.tasks.celery_app worker --loglevel=info

# Monitor tasks
celery -A app.tasks.celery_app flower
```

## 📝 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### Transformations
- `POST /api/v1/transform/transform` - Create transformation
- `GET /api/v1/transform/{job_id}` - Get status
- `GET /api/v1/transform/history` - User history
- `DELETE /api/v1/transform/{id}` - Delete transformation

### Real-time
- `GET /api/v1/stream/{job_id}` - SSE stream for updates

### User
- `GET /api/v1/user/me` - Current user info
- `GET /api/v1/user/credits` - User credits

### Health
- `GET /api/v1/health` - Health check

## 💰 Cost Optimization

- Image transformations: ~$0.01-0.015 per image (Replicate)
- S3 storage with lifecycle policies
- CloudFront CDN for fast delivery
- Redis caching for rate limiting
- Connection pooling for database

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting per user/IP
- Input validation & sanitization
- CORS configuration
- SQL injection protection (SQLAlchemy ORM)
- Image validation & EXIF stripping

## 📈 Monitoring

- Health check endpoint
- Structured logging
- Error tracking (ready for Sentry)
- Request/response logging
- Database query logging

## 🚀 Deployment

See `IMPLEMENTATION_GUIDE_PART3.md` for detailed deployment instructions.

Quick production deployment:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📖 Further Documentation

- [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) - Complete setup guide
- [IMPLEMENTATION_GUIDE_PART2.md](../IMPLEMENTATION_GUIDE_PART2.md) - API & Jobs
- [IMPLEMENTATION_GUIDE_PART3.md](../IMPLEMENTATION_GUIDE_PART3.md) - Testing & Deployment
- [BACKEND_PLAN.md](../BACKEND_PLAN.md) - Architecture design
- [AI_MODELS_COMPARISON.md](../AI_MODELS_COMPARISON.md) - Model research

## 🐛 Troubleshooting

See `IMPLEMENTATION_GUIDE_PART3.md` Section 20 for common issues and solutions.

## 🙏 Acknowledgments

- FastAPI framework
- Replicate AI platform
- RoomGPT open source project (inspiration)
