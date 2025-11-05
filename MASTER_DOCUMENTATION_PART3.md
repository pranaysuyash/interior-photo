# Interior AI - Master Documentation Part 3
## Production Deployment & Advanced Topics

**Continuation of MASTER_DOCUMENTATION_PART2.md**

---

## 12. Production Deployment

### 12.1 Pre-Deployment Checklist

Before deploying to production, ensure:

**Security:**
- [ ] Change all default passwords
- [ ] Generate new SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS only
- [ ] Configure proper CORS origins
- [ ] Review and restrict API rate limits
- [ ] Enable SQL injection protection (SQLAlchemy ORM)
- [ ] Set up API key authentication
- [ ] Configure firewall rules
- [ ] Enable DDoS protection

**Configuration:**
- [ ] Set `DEBUG=False` in backend
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure production database
- [ ] Set up Redis cluster (optional)
- [ ] Configure S3 bucket lifecycle policies
- [ ] Set up CloudFront CDN
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure domain names

**Infrastructure:**
- [ ] Set up database backups
- [ ] Configure auto-scaling
- [ ] Set up load balancer
- [ ] Configure health checks
- [ ] Set up monitoring (Sentry, Datadog)
- [ ] Configure logging
- [ ] Set up alerting
- [ ] Plan disaster recovery

### 12.2 Environment Variables for Production

**Backend (.env.production):**

```bash
# Application
APP_NAME=Interior AI
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000

# Database - Use RDS or managed PostgreSQL
DATABASE_URL=postgresql://user:pass@prod-db.amazonaws.com:5432/interiorai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis - Use ElastiCache or managed Redis
REDIS_URL=redis://prod-redis.amazonaws.com:6379/0

# Security - GENERATE NEW SECRET KEY!
SECRET_KEY=<new-production-secret-key-64-characters>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3 Production
AWS_ACCESS_KEY_ID=<prod-access-key>
AWS_SECRET_ACCESS_KEY=<prod-secret-key>
AWS_REGION=us-east-1
S3_BUCKET_NAME=interior-ai-production
S3_BUCKET_URL=https://interior-ai-production.s3.amazonaws.com
CLOUDFRONT_URL=https://dxxxxxxxxxxxxx.cloudfront.net

# Replicate
REPLICATE_API_TOKEN=<your-replicate-token>
REPLICATE_MODEL=adirik/interior-design:76604baddc85a8fdb0b3cad03c9fd9634ff8c64c0e15f74e9f2be61dc63e5c7f

# Celery
CELERY_BROKER_URL=redis://prod-redis.amazonaws.com:6379/1
CELERY_RESULT_BACKEND=redis://prod-redis.amazonaws.com:6379/2

# Rate Limiting (stricter in production)
RATE_LIMIT_FREE_DAILY=5
RATE_LIMIT_PRO_DAILY=100
RATE_LIMIT_ENTERPRISE_DAILY=1000

# File Upload (stricter in production)
MAX_IMAGE_SIZE_MB=10
ALLOWED_IMAGE_TYPES=jpg,jpeg,png,webp

# CORS (production domains only)
CORS_ORIGINS=https://interiorai.com,https://www.interiorai.com

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx

# Email (if implementing notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@interiorai.com
SMTP_PASSWORD=<app-specific-password>
```

**Frontend (.env.production):**

```bash
VITE_API_URL=https://api.interiorai.com
VITE_APP_NAME=Interior AI
VITE_SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### 12.3 AWS Deployment (Recommended)

#### Architecture Overview

```
┌─────────────┐
│  Route 53   │ (DNS)
└──────┬──────┘
       │
┌──────▼──────┐
│ CloudFront  │ (CDN for frontend)
└──────┬──────┘
       │
┌──────▼───────────────────────────┐
│  S3 Static Website              │ (Frontend)
│  interiorai.com                  │
└──────────────────────────────────┘

       │ API Calls
       │
┌──────▼──────┐
│     ALB     │ (Application Load Balancer)
│ api.interior│
└──────┬──────┘
       │
┌──────▼──────┐
│     ECS     │ (Container Service)
│  Fargate    │
│             │
│  ┌────────┐ │
│  │FastAPI │ │
│  │  API   │ │
│  └────────┘ │
│             │
│  ┌────────┐ │
│  │ Celery │ │
│  │ Worker │ │
│  └────────┘ │
└──────┬──────┘
       │
       ├──────────────────┐
       │                  │
┌──────▼──────┐   ┌───────▼────────┐
│     RDS     │   │  ElastiCache   │
│ PostgreSQL  │   │     Redis      │
└─────────────┘   └────────────────┘
       │
       │
┌──────▼──────┐
│     S3      │ (Image Storage)
│ + CloudFront│ (CDN for images)
└─────────────┘
```

#### Step-by-Step AWS Deployment

**1. Set Up RDS PostgreSQL:**

```bash
# Using AWS CLI
aws rds create-db-instance \
  --db-instance-identifier interiorai-prod \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username interiorai \
  --master-user-password <strong-password> \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default \
  --publicly-accessible \
  --backup-retention-period 7 \
  --multi-az

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier interiorai-prod \
  --query 'DBInstances[0].Endpoint.Address'
```

**2. Set Up ElastiCache Redis:**

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id interiorai-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name default \
  --security-group-ids sg-xxxxx

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id interiorai-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address'
```

**3. Build and Push Docker Image:**

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name interiorai-api

# Build image
cd backend
docker build -t interiorai-api:latest .

# Tag image
docker tag interiorai-api:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/interiorai-api:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/interiorai-api:latest
```

**4. Create ECS Cluster and Task Definition:**

```bash
# Create cluster
aws ecs create-cluster --cluster-name interiorai-prod

# Create task definition JSON
cat > task-definition.json << 'EOF'
{
  "family": "interiorai-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/interiorai-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "False"},
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxx:secret:prod/db-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxx:secret:prod/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/interiorai-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

**5. Create Application Load Balancer:**

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name interiorai-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing

# Create target group
aws elbv2 create-target-group \
  --name interiorai-api-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path /api/v1/health

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

**6. Create ECS Service:**

```bash
# Create service
aws ecs create-service \
  --cluster interiorai-prod \
  --service-name interiorai-api \
  --task-definition interiorai-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api,containerPort=8000"
```

**7. Deploy Frontend to S3 + CloudFront:**

```bash
# Build frontend
npm run build

# Create S3 bucket
aws s3 mb s3://interiorai-frontend

# Enable static website hosting
aws s3 website s3://interiorai-frontend \
  --index-document index.html \
  --error-document index.html

# Upload build
aws s3 sync dist/ s3://interiorai-frontend --delete

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name interiorai-frontend.s3.amazonaws.com \
  --default-root-object index.html
```

**8. Set Up Route 53:**

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone --name interiorai.com

# Create A record for frontend
aws route53 change-resource-record-sets \
  --hosted-zone-id Z... \
  --change-batch file://frontend-record.json

# frontend-record.json:
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "interiorai.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "Z2FDTNDATAQYW2",
        "DNSName": "dxxxxx.cloudfront.net",
        "EvaluateTargetHealth": false
      }
    }
  }]
}

# Create A record for API
# (Point to ALB)
```

### 12.4 Alternative: DigitalOcean Deployment

**Simpler and cheaper alternative to AWS:**

**1. Create Droplet:**

```bash
# Create Ubuntu 22.04 droplet (2GB RAM minimum)
# Enable Docker during creation
# Add SSH key for access
```

**2. SSH into Droplet:**

```bash
ssh root@<droplet-ip>

# Update system
apt update && apt upgrade -y

# Install Docker & Docker Compose (if not pre-installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

**3. Set Up Application:**

```bash
# Clone repository
git clone <your-repo-url>
cd interior-photo/backend

# Create production .env
cp .env.example .env
nano .env  # Edit with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

**4. Set Up Nginx Reverse Proxy:**

```bash
# Install Nginx
apt install nginx -y

# Create Nginx config
cat > /etc/nginx/sites-available/interiorai << 'EOF'
server {
    listen 80;
    server_name api.interiorai.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/interiorai /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

**5. Set Up SSL with Let's Encrypt:**

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot --nginx -d api.interiorai.com

# Auto-renewal is set up automatically
```

**6. Deploy Frontend:**

```bash
# Build frontend locally
npm run build

# Upload to droplet
scp -r dist/* root@<droplet-ip>:/var/www/interiorai

# Configure Nginx for frontend
cat > /etc/nginx/sites-available/interiorai-frontend << 'EOF'
server {
    listen 80;
    server_name interiorai.com www.interiorai.com;
    root /var/www/interiorai;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

ln -s /etc/nginx/sites-available/interiorai-frontend /etc/nginx/sites-enabled/
certbot --nginx -d interiorai.com -d www.interiorai.com
systemctl restart nginx
```

### 12.5 Docker Compose Production Configuration

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - backend
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    networks:
      - backend
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

volumes:
  postgres_data:

networks:
  backend:
    driver: bridge
```

**Dockerfile.prod:**

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run with Gunicorn for production
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
```

### 12.6 CI/CD Pipeline

**GitHub Actions (.github/workflows/deploy.yml):**

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: interiorai-api
          IMAGE_TAG: ${{ github.sha }}
        run: |
          cd backend
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster interiorai-prod \
            --service interiorai-api \
            --force-new-deployment

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install

      - name: Build
        run: npm run build
        env:
          VITE_API_URL: https://api.interiorai.com

      - name: Deploy to S3
        run: |
          aws s3 sync dist/ s3://interiorai-frontend --delete
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

### 12.7 Monitoring and Logging

**Set Up Sentry for Error Tracking:**

```bash
# Install Sentry SDK
pip install sentry-sdk[fastapi]

# In app/main.py:
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,
)
```

**Set Up CloudWatch Logs (AWS):**

```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/interiorai-api

# Logs automatically stream from ECS tasks
# View logs:
aws logs tail /ecs/interiorai-api --follow
```

**Set Up Prometheus + Grafana:**

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
```

### 12.8 Backup Strategy

**Automated PostgreSQL Backups:**

```bash
# Create backup script
cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U interiorai interiorai | \
  gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz \
  s3://interiorai-backups/postgres/backup_$DATE.sql.gz
EOF

chmod +x /usr/local/bin/backup-db.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-db.sh" | crontab -
```

**S3 Lifecycle Policy:**

```json
{
  "Rules": [
    {
      "Id": "TransitionOldImages",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

---

## 13. Advanced Configuration

### 13.1 Custom Domain Setup

**1. Purchase Domain** (GoDaddy, Namecheap, Google Domains)

**2. Configure DNS** (using Cloudflare - recommended):

```
Type    Name    Content
A       @       <your-server-ip>
A       www     <your-server-ip>
CNAME   api     <alb-dns-name>.us-east-1.elb.amazonaws.com
```

**3. Get SSL Certificate:**

```bash
# Using Let's Encrypt (free)
certbot --nginx -d interiorai.com -d www.interiorai.com -d api.interiorai.com

# Using AWS ACM (for ALB)
aws acm request-certificate \
  --domain-name interiorai.com \
  --subject-alternative-names www.interiorai.com api.interiorai.com \
  --validation-method DNS
```

### 13.2 Email Configuration

**Using SendGrid:**

```bash
# Install SendGrid
pip install sendgrid

# Configure in .env
SENDGRID_API_KEY=SG.xxxxx
FROM_EMAIL=noreply@interiorai.com
```

**Email service:**

```python
# app/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_transformation_complete_email(user_email, job_id, result_url):
    message = Mail(
        from_email='noreply@interiorai.com',
        to_emails=user_email,
        subject='Your Interior Transformation is Ready!',
        html_content=f'''
            <h2>Your transformation is complete!</h2>
            <p>Job ID: {job_id}</p>
            <p><a href="{result_url}">View Result</a></p>
        '''
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
```

### 13.3 Payment Integration (Stripe)

```bash
# Install Stripe
pip install stripe

# Configure in .env
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

**Create subscription:**

```python
# app/api/v1/endpoints/subscription.py
import stripe
from fastapi import APIRouter

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-checkout-session")
async def create_checkout_session(
    plan: str,  # 'pro' or 'enterprise'
    user = Depends(get_current_user)
):
    prices = {
        'pro': 'price_xxxxx',  # $9.99/month
        'enterprise': 'price_yyyyy'  # $49.99/month
    }

    session = stripe.checkout.Session.create(
        customer_email=user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': prices[plan],
            'quantity': 1,
        }],
        mode='subscription',
        success_url='https://interiorai.com/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='https://interiorai.com/cancel',
    )

    return {'checkout_url': session.url}
```

### 13.4 Analytics Integration

**Google Analytics:**

```html
<!-- index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

**PostHog (Open Source):**

```typescript
// src/main.tsx
import posthog from 'posthog-js'

posthog.init('phc_xxxxx', {
  api_host: 'https://app.posthog.com'
})

// Track events
posthog.capture('transformation_created', {
  vibe: 'modern',
  colors: 'neutral'
})
```

### 13.5 Rate Limiting (Advanced)

**Redis-based rate limiter with multiple tiers:**

```python
# app/middleware/advanced_rate_limit.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import redis
from datetime import datetime, timedelta

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = redis.from_url(settings.REDIS_URL)

    async def dispatch(self, request: Request, call_next):
        # Get user or IP
        user = getattr(request.state, 'user', None)
        identifier = str(user.id) if user else request.client.host

        # Check rate limit
        key = f"rate_limit:{identifier}:{datetime.utcnow().date()}"
        current = self.redis.get(key)

        # Get limit based on tier
        limit = self.get_limit(user)

        if current and int(current) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)  # 24 hours
        pipe.execute()

        return await call_next(request)

    def get_limit(self, user):
        if not user:
            return 3
        return {
            'free': 5,
            'pro': 100,
            'enterprise': 1000
        }.get(user.subscription_tier, 5)
```

---

## 14. Security Best Practices

### 14.1 Security Checklist

**API Security:**
- [ ] Use HTTPS everywhere (enforce SSL)
- [ ] Implement rate limiting
- [ ] Validate all inputs
- [ ] Use parameterized queries (SQLAlchemy ORM)
- [ ] Hash passwords with bcrypt
- [ ] Use short-lived JWT tokens
- [ ] Implement CORS properly
- [ ] Set security headers
- [ ] Disable debug mode in production
- [ ] Hide error details in production
- [ ] Use environment variables for secrets
- [ ] Implement API key authentication
- [ ] Use secure session cookies

**Infrastructure Security:**
- [ ] Use firewalls
- [ ] Restrict database access
- [ ] Use VPCs/private networks
- [ ] Enable DDoS protection
- [ ] Regular security updates
- [ ] Use secrets management (AWS Secrets Manager)
- [ ] Enable CloudTrail/logging
- [ ] Implement WAF rules
- [ ] Use least privilege IAM policies
- [ ] Enable MFA for admin access

### 14.2 Security Headers

```python
# app/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

# Add to app
app.add_middleware(SecurityHeadersMiddleware)
```

### 14.3 Secrets Management

**Using AWS Secrets Manager:**

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None

# Usage
secrets = get_secret('prod/interiorai/database')
DATABASE_URL = secrets['url']
```

---

## 15. Performance Optimization

### 15.1 Database Optimization

**Add Indexes:**

```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_transformations_user_id ON transformations(user_id);
CREATE INDEX idx_transformations_status ON transformations(status);
CREATE INDEX idx_transformations_created_at ON transformations(created_at DESC);
CREATE INDEX idx_users_email ON users(email);

-- Composite index for common queries
CREATE INDEX idx_transformations_user_status ON transformations(user_id, status);
```

**Connection Pooling:**

```python
# app/db/session.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,              # Number of connections to keep
    max_overflow=10,           # Additional connections when pool full
    pool_pre_ping=True,        # Test connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False                 # Don't log all SQL (performance)
)
```

### 15.2 Caching Strategy

**Redis Caching:**

```python
# app/services/cache_service.py
import redis
import json
from functools import wraps

redis_client = redis.from_url(settings.REDIS_URL)

def cache(key_prefix: str, expiry: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{str(args)}:{str(kwargs)}"

            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            redis_client.setex(
                cache_key,
                expiry,
                json.dumps(result)
            )

            return result
        return wrapper
    return decorator

# Usage
@cache('user', expiry=600)
async def get_user(user_id):
    # ...
    return user
```

### 15.3 Image Optimization

**Resize images before upload:**

```python
from PIL import Image
from io import BytesIO

def optimize_image(image_bytes: bytes, max_size: tuple = (2048, 2048)) -> bytes:
    """Resize and optimize image"""
    img = Image.open(BytesIO(image_bytes))

    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')

    # Resize if larger than max_size
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Save optimized
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()
```

### 15.4 Auto-Scaling

**AWS ECS Auto-scaling:**

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/interiorai-prod/interiorai-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU based)
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/interiorai-prod/interiorai-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json

# scaling-policy.json:
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

---

## 16. Cost Optimization

### 16.1 AWS Cost Breakdown

**Monthly costs for different scales:**

**Small Scale (1,000 transformations/month):**
- ECS Fargate (2 tasks, 0.5 vCPU, 1GB): $30
- RDS t3.micro: $15
- ElastiCache t3.micro: $15
- S3 (50GB + requests): $5
- CloudFront (100GB): $10
- Replicate API: $12
- **Total: ~$87/month**

**Medium Scale (10,000 transformations/month):**
- ECS Fargate (4 tasks, 1 vCPU, 2GB): $120
- RDS t3.small: $30
- ElastiCache t3.small: $30
- S3 (500GB + requests): $15
- CloudFront (500GB): $40
- Replicate API: $120
- **Total: ~$355/month**

**Large Scale (100,000 transformations/month):**
- ECS Fargate (10 tasks, 2 vCPU, 4GB): $600
- RDS t3.large: $140
- ElastiCache t3.medium: $70
- S3 (5TB + requests): $120
- CloudFront (5TB): $425
- Replicate API: $1,200
- **Total: ~$2,555/month**

### 16.2 Cost Optimization Tips

1. **Use Reserved Instances** (save 30-50%)
2. **Enable S3 Lifecycle Policies** (move old images to Glacier)
3. **Use CloudFront caching** (reduce S3 requests)
4. **Optimize Replicate usage** (batch requests, cache results)
5. **Right-size instances** (monitor and adjust)
6. **Use Spot Instances** for Celery workers (save 70%)
7. **Enable compression** (reduce bandwidth costs)
8. **Delete unused resources** regularly

---

**This completes the comprehensive Master Documentation.**

**Summary:**
- Part 1: Introduction, Prerequisites, Setup (Backend & Frontend), API Integration
- Part 2: Running, Testing, API Reference, Troubleshooting
- Part 3: Production Deployment, Advanced Configuration, Security, Performance

You now have everything needed to build, deploy, and scale Interior AI! 🚀
