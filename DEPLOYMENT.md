# Interior AI - Production Deployment Guide

Complete guide for deploying Interior AI to production.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: Minimum 4GB (8GB+ recommended)
- **CPU**: 2+ cores (4+ recommended)
- **Storage**: 50GB+ available space
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Required Services & Accounts
1. **Replicate.com** account with API token
2. **AWS Account** with:
   - S3 bucket created
   - CloudFront distribution (optional but recommended)
   - IAM user with S3 access
3. **Domain name** (for production)
4. **SSL Certificate** (Let's Encrypt or purchased)

## 🚀 Quick Start (5 Minutes)

### 1. Clone Repository
```bash
git clone <repository-url>
cd interior-photo
```

### 2. Configure Environment
```bash
# Backend configuration
cd backend
cp .env.example .env
nano .env  # Edit with your credentials
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@postgres:5432/interior_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD
POSTGRES_DB=interior_ai

# Redis
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=YOUR_SECURE_REDIS_PASSWORD

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Service
REPLICATE_API_TOKEN=r8_your_token_here

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
CLOUDFRONT_DOMAIN=your-cdn-domain.cloudfront.net

# Application
ENVIRONMENT=production
APP_NAME="Interior AI"
APP_VERSION=1.0.0
DEBUG=false

# Admin (change after first login!)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=ChangeMe123!
```

### 3. Generate Secrets
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate passwords
openssl rand -base64 32
```

### 4. Start Production Services
```bash
cd backend
chmod +x scripts/*.sh
./scripts/start_prod.sh
```

This script will:
- ✅ Validate environment
- ✅ Start all Docker services
- ✅ Run database migrations
- ✅ Seed initial data
- ✅ Perform health checks

### 5. Verify Deployment
```bash
# Check services
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Run health check
./scripts/health_check.sh
```

Access points:
- Frontend: http://your-domain.com
- API Docs: http://your-domain.com/docs
- Grafana: http://your-domain.com:3000

## 🔧 Manual Setup (Advanced)

### Frontend Build
```bash
# Install dependencies
npm install

# Build for production
npm run build

# Files will be in ./dist/
# Nginx serves these automatically from docker-compose.prod.yml
```

### Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn -c gunicorn.conf.py app.main:app
```

## 🗄️ Database Management

### Run Migrations
```bash
./scripts/db_manage.sh migrate
```

### Create New Migration
```bash
./scripts/db_manage.sh create-migration "add new field"
```

### Backup Database
```bash
./scripts/backup.sh
```

Backups are stored in `backend/backups/` and optionally uploaded to S3.

### Restore from Backup
```bash
# List backups
ls -lh backend/backups/

# Restore (replace with your backup file)
docker-compose -f docker-compose.prod.yml exec -T postgres psql \
  -U postgres -d interior_ai < backend/backups/backup_20240101_120000.sql.gz
```

### Database Console
```bash
./scripts/db_manage.sh console
```

## 📊 Monitoring

### Prometheus Metrics
Access: http://localhost:9090

Metrics collected:
- API response times
- Request rates
- Error rates
- Database performance
- Celery task metrics
- System resources

### Grafana Dashboards
Access: http://localhost:3000
Default credentials: admin / admin (change immediately!)

Pre-configured dashboards:
- Application Overview
- API Performance
- Database Metrics
- Celery Workers
- System Resources

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api

# Tail last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 api
```

### Health Checks
```bash
# Run comprehensive health check
./scripts/health_check.sh

# Check API only
curl http://localhost/api/v1/health

# Check specific service
docker-compose -f docker-compose.prod.yml exec api curl localhost:8000/api/v1/health
```

## 🔒 Security Hardening

### 1. SSL/TLS Setup

#### Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem backend/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem backend/nginx/ssl/key.pem

# Set permissions
sudo chmod 600 backend/nginx/ssl/*.pem
```

#### Auto-renewal
```bash
# Add to crontab
0 0 * * * certbot renew --quiet && docker-compose -f /path/to/docker-compose.prod.yml restart nginx
```

### 2. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 3. Change Default Passwords
```bash
# Admin user
# Login and change via API or database

# Grafana
# Access http://localhost:3000 and change password

# Database passwords
# Update .env and restart services
```

### 4. Enable Rate Limiting
Already configured in nginx.conf:
- API: 10 requests/second
- Uploads: 2 requests/second

Adjust in `backend/nginx/nginx.conf` if needed.

## 📈 Scaling

### Horizontal Scaling (Multiple Servers)

1. **Use External Database & Redis**
   - Set up managed PostgreSQL (AWS RDS, DigitalOcean, etc.)
   - Set up managed Redis
   - Update DATABASE_URL and REDIS_URL in .env

2. **Use Load Balancer**
   - AWS ALB, DigitalOcean Load Balancer, or Nginx
   - Distribute traffic across multiple API instances

3. **Update docker-compose.prod.yml**
   ```yaml
   api:
     deploy:
       replicas: 4  # Increase replicas

   celery_worker:
     deploy:
       replicas: 4  # More workers
   ```

### Vertical Scaling (Resource Limits)

Edit resource limits in docker-compose.prod.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

## 🔄 Updates & Deployments

### Zero-Downtime Deployment
```bash
./scripts/deploy.sh
```

This script:
1. Creates database backup
2. Builds new images
3. Runs migrations
4. Performs rolling update
5. Validates deployment
6. Rolls back on failure

### Manual Update
```bash
cd backend

# Pull latest code
git pull

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

## 🐛 Troubleshooting

### API Not Responding
```bash
# Check API logs
docker-compose -f docker-compose.prod.yml logs api

# Restart API
docker-compose -f docker-compose.prod.yml restart api

# Check health
curl http://localhost:8000/api/v1/health
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
```

### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Prune unused resources
docker system prune -af
```

### Celery Workers Not Processing
```bash
# Check worker status
docker-compose -f docker-compose.prod.yml logs celery_worker

# Inspect active tasks
docker-compose -f docker-compose.prod.yml exec celery_worker \
  celery -A app.tasks.celery_app inspect active

# Restart workers
docker-compose -f docker-compose.prod.yml restart celery_worker
```

## 🌐 Cloud Deployment

### AWS EC2

1. **Launch Instance**
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t3.large or larger
   - Security Group: Allow 80, 443, 22

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   ```

3. **Deploy Application**
   ```bash
   git clone <repo>
   cd interior-photo/backend
   cp .env.example .env
   # Edit .env with production values
   ./scripts/start_prod.sh
   ```

### DigitalOcean Droplet

Similar to AWS EC2. Use Droplet marketplace Docker image for faster setup.

### Docker Swarm / Kubernetes

For orchestration at scale, see MASTER_DOCUMENTATION_PART3.md section on container orchestration.

## 📞 Support

For issues or questions:
1. Check documentation: /docs
2. Review logs: `docker-compose logs`
3. Run health check: `./scripts/health_check.sh`
4. Check GitHub issues

## 📊 Performance Optimization

### Database Optimization
```bash
# Run VACUUM
./scripts/db_manage.sh vacuum

# Check query performance
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d interior_ai
# Then: EXPLAIN ANALYZE <your-query>;
```

### Redis Optimization
Configured in docker-compose.prod.yml:
- Max memory: 512MB
- Eviction policy: allkeys-lru

### Image Optimization
Already implemented in image_processor.py:
- EXIF stripping
- Format optimization
- Compression

## 🎯 Cost Optimization

### Estimated Monthly Costs

**AWS (Moderate Traffic)**
- EC2 t3.large: $60/month
- RDS PostgreSQL: $30/month
- S3 + CloudFront: $20/month
- **Total**: ~$110/month

**DigitalOcean (Moderate Traffic)**
- 4GB Droplet: $24/month
- Managed PostgreSQL: $15/month
- Spaces (S3 alternative): $5/month
- **Total**: ~$44/month

**Replicate API (Variable)**
- $0.01-0.015 per transformation
- 1000 transformations: $10-15/month

### Reduce Costs
1. Use DigitalOcean instead of AWS
2. Implement aggressive caching
3. Use smaller instance during low traffic
4. Enable auto-scaling
5. Use spot instances for workers

---

## ✅ Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] SSL certificates installed
- [ ] Database backed up
- [ ] Admin password changed
- [ ] Grafana password changed
- [ ] Firewall configured
- [ ] Monitoring working
- [ ] Alerts configured
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Backup script scheduled
- [ ] Domain configured
- [ ] DNS records set
- [ ] Email notifications set up

---

**Interior AI** - Transform Your Space with AI-Powered Design
