# Interior AI - Quick Start Guide

Get your AI-powered interior design app running in minutes!

## 🎯 What You'll Need

- **Replicate API Key**: Get from [replicate.com](https://replicate.com) (required for AI transformations)
- **AWS Account**: For S3 image storage (or use alternatives like Cloudflare R2)
- **Docker** (recommended) or Python 3.11+, PostgreSQL 15+, Redis 7+

## 🚀 Quick Start with Docker (Recommended)

### 1. Clone & Setup

```bash
cd interior-photo
```

### 2. Configure Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your credentials:
```bash
# Required
REPLICATE_API_TOKEN=r8_xxx...  # From replicate.com
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=your-bucket-name

# Generate a secure secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
```

### 3. Start Backend

```bash
# Start all services (PostgreSQL, Redis, API, Celery)
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api
```

✅ **Backend running at:** http://localhost:8000

✅ **API Documentation:** http://localhost:8000/docs

### 4. Configure & Start Frontend

```bash
cd ../  # Back to root
cd frontend  # If you have frontend in separate folder

# Or if frontend is in root:
npm install
npm run dev
```

✅ **Frontend running at:** http://localhost:3000 or http://localhost:5173

## 📱 Test the Application

1. **Open frontend** in your browser
2. **Register** a new account
3. **Upload** a room photo
4. **Choose** your style preferences (vibe & colors)
5. **Transform!** ✨

## 🔧 Troubleshooting

### Backend not starting?
```bash
# Check if all services are healthy
docker-compose ps

# View specific service logs
docker-compose logs api
docker-compose logs postgres
docker-compose logs redis
```

### Database migration issues?
```bash
# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Celery worker not processing?
```bash
# Check worker logs
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker
```

### S3 upload failing?
- Verify AWS credentials in `.env`
- Check S3 bucket exists and has correct permissions
- Ensure bucket is in the region specified in `.env`

## 📊 Monitor Your App

```bash
# View all logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api

# View Celery worker logs
docker-compose logs -f celery_worker

# Check service status
docker-compose ps
```

## 🛑 Stop Everything

```bash
cd backend
docker-compose down

# To also remove volumes (database data)
docker-compose down -v
```

## 📚 What's Next?

### For Development:
- See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed backend info
- See [backend/README.md](backend/README.md) for backend documentation
- See [BACKEND_PLAN.md](BACKEND_PLAN.md) for architecture details

### For Production:
- Set up proper domain & SSL certificate
- Configure CDN (CloudFront) for image delivery
- Set up monitoring (Sentry for errors, Datadog for metrics)
- Implement payment integration (Stripe)
- Set up automated backups for PostgreSQL
- Configure auto-scaling for API servers

### Recommended AWS S3 Setup:
```bash
# Create S3 bucket
aws s3 mb s3://your-bucket-name --region us-east-1

# Enable CORS
aws s3api put-bucket-cors --bucket your-bucket-name --cors-configuration file://cors.json

# Set lifecycle policy for old files
aws s3api put-bucket-lifecycle-configuration --bucket your-bucket-name --lifecycle-configuration file://lifecycle.json
```

## 💰 Cost Estimates

**For 1,000 transformations/month:**
- Replicate AI: ~$12-15
- AWS S3 + CloudFront: ~$5-10
- PostgreSQL (RDS t3.micro): ~$15
- Redis (ElastiCache t3.micro): ~$15
- API Hosting (EC2 t3.small): ~$15

**Total: ~$62-70/month**

**Revenue to break even:**
- ~7 Pro users ($9.99/mo)
- or ~2 Enterprise users ($49.99/mo)

## 🎨 Architecture Overview

```
┌─────────────┐
│   Frontend  │ (React + Vite)
│  Port 3000  │
└──────┬──────┘
       │
       ↓ HTTP/HTTPS
┌──────────────────┐
│   FastAPI        │
│   Port 8000      │ ← JWT Auth
└────┬────┬────────┘
     │    │
     │    └───→ ┌─────────────┐
     │          │  Replicate  │ (AI Model)
     │          │     API     │
     │          └─────────────┘
     │
     ↓
┌────────────────┐
│   PostgreSQL   │ (User data, transformations)
│   Port 5432    │
└────────────────┘
     │
     │   ┌─────────────┐
     └──→│   Redis     │ (Rate limiting, caching)
         │  Port 6379  │
         └─────────────┘
              │
              ↓
         ┌─────────────┐
         │   Celery    │ (Background jobs)
         │   Worker    │
         └─────────────┘
              │
              ↓
         ┌─────────────┐
         │   AWS S3    │ (Image storage)
         │  +CloudFront│ (CDN)
         └─────────────┘
```

## 🆘 Need Help?

1. **Documentation**: Check [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
2. **API Docs**: Visit http://localhost:8000/docs when running
3. **Issues**: Check troubleshooting section above
4. **Logs**: `docker-compose logs -f` shows everything

## 🎉 Success Checklist

- [ ] Backend running at http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Frontend running at http://localhost:3000
- [ ] Can register a new user
- [ ] Can login successfully
- [ ] Can upload an image
- [ ] Transformation processes successfully
- [ ] Can view results with before/after slider

---

**You're all set! Start transforming interiors with AI! 🏠✨**
