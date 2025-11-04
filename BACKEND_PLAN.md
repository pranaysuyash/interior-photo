# Backend Architecture & AI Model Plan

## 🎯 Executive Summary

This document outlines the backend architecture and AI model selection for the Interior AI application. After researching multiple platforms (FAL.ai, Replicate, HuggingFace, Higgsfield, Segmind, ModelsLab), we have identified the most suitable AI models and designed a scalable backend system.

---

## 🤖 AI Models Research Summary

### **Option 1: Replicate (RECOMMENDED)**

#### **Model: adirik/interior-design**
- **Platform**: Replicate
- **Base Model**: Realistic Vision V3.0 with ControlNet
- **Type**: Custom pipeline combining inpainting + segmentation + MLSD ControlNet
- **Processing Time**: ~3-5 seconds
- **Hardware**: Nvidia L40S GPU

**Pros:**
- ✅ Purpose-built for interior design
- ✅ Preserves room layout while transforming style
- ✅ Simple API integration (one line of code)
- ✅ Production-ready with proven scale
- ✅ Cost-effective pay-per-use pricing
- ✅ Handles both text prompts and reference images

**Cons:**
- ❌ Less customization than self-hosted solutions
- ❌ Dependent on third-party service

**API Example:**
```python
import replicate

output = replicate.run(
  "adirik/interior-design:76604baddc85a8fdb0b3cad03c9fd9634ff8c64c0e15f74e9f2be61dc63e5c7f",
  input={
    "image": "https://...",
    "prompt": "A modern living room with neutral tones and minimalist furniture",
    "negative_prompt": "ugly, distorted, low quality",
    "num_inference_steps": 50,
    "guidance_scale": 7.5
  }
)
```

**Pricing**: ~$0.0023 per second (~$0.01-0.015 per image)

---

### **Option 2: HuggingFace ControlNet Models**

#### **Model: BertChristiaens/controlnet-seg-room**
- **Platform**: HuggingFace
- **Training Data**: 130k images, 15 room types, 30 design styles
- **Type**: ControlNet with segmentation conditioning
- **Hosting**: Self-hosted or HuggingFace Inference API

**Pros:**
- ✅ Fine-grained control over object placement
- ✅ Trained specifically on interior design dataset
- ✅ Can self-host for full control
- ✅ Open source and customizable
- ✅ Works well with segmentation masks

**Cons:**
- ❌ Requires more technical setup
- ❌ Need to manage GPU infrastructure
- ❌ Higher initial development cost

**Use Cases:**
- Precise room layout preservation
- Multiple object placement control
- Style transfer with layout constraints

---

### **Option 3: Stable Diffusion XL Inpainting**

#### **Models Available:**
1. **diffusers/stable-diffusion-xl-1.0-inpainting-0.1** (Official)
2. **lucataco/sdxl-inpainting** (Replicate)
3. **ModelsLab SDXL V5 VAE Inpainting**

**Pros:**
- ✅ High-quality photorealistic outputs
- ✅ Multiple API providers (Replicate, ModelsLab, Segmind)
- ✅ Well-documented and widely supported
- ✅ Flexible for various use cases

**Cons:**
- ❌ Not specifically trained for interior design
- ❌ May require fine-tuning for best results
- ❌ Slower than specialized models

**Best For:**
- Targeted modifications (change wall color, add furniture)
- High-resolution outputs
- Custom inpainting tasks

---

### **Option 4: ControlNet Depth Models**

#### **Use Case**: Layout-preserving transformations

**Platforms:**
- Segmind API
- Laozhang.ai (1.2s average processing)
- Self-hosted via Hugging Face

**Pros:**
- ✅ 91.8% accuracy for spatial relationship preservation
- ✅ Perfect for maintaining room structure
- ✅ Fast processing (1.2s with optimized APIs)
- ✅ Works great with depth maps

**Cons:**
- ❌ Requires depth map generation
- ❌ Additional preprocessing step

---

### **Platform Comparison Matrix**

| Platform | Best Model | Speed | Cost/Image | Ease of Integration | Production Ready |
|----------|------------|-------|------------|---------------------|------------------|
| **Replicate** | adirik/interior-design | ⚡⚡⚡ 3-5s | 💰 $0.01-0.015 | ✅ Excellent | ✅ Yes |
| **HuggingFace** | controlnet-seg-room | ⚡⚡ 5-10s | 💰💰 Self-hosted | ⚠️ Moderate | ⚠️ Requires setup |
| **Replicate** | sdxl-inpainting | ⚡⚡⚡ 3s | 💰 $0.01 | ✅ Excellent | ✅ Yes |
| **ModelsLab** | SDXL Inpainting | ⚡⚡ 4-6s | 💰 $0.008-0.012 | ✅ Good | ✅ Yes |
| **Segmind** | ControlNet Depth | ⚡⚡⚡ 1.2s | 💰 $0.005-0.010 | ✅ Good | ✅ Yes |

---

## 🏗️ Recommended Backend Architecture

### **Tech Stack**

```
Frontend (React) → API Gateway → Backend Services → AI Model APIs
                                      ↓
                                  Database
                                      ↓
                              Object Storage (S3)
```

### **Backend Components**

#### **1. API Server (Node.js/Express or Python/FastAPI)**

**Recommended**: **FastAPI (Python)**
- Native async support
- Excellent for ML integrations
- Fast performance
- Automatic API documentation
- Type safety with Pydantic

**Alternative**: **Node.js/Express**
- Better TypeScript integration with frontend
- Larger ecosystem
- Familiar for frontend developers

#### **2. Core Services**

```
/backend
  /services
    /ai
      - replicate_service.py        # Replicate API integration
      - image_processor.py          # Image preprocessing/postprocessing
      - prompt_builder.py           # Smart prompt generation
    /storage
      - s3_service.py               # Image storage (AWS S3/Cloudflare R2)
    /database
      - user_service.py             # User management
      - transformation_service.py   # Transformation history
    /queue
      - job_queue.py                # Background processing (Celery/Bull)
```

---

## 📋 API Endpoints Design

### **Base URL**: `https://api.interiorai.com/v1`

### **Endpoints**

#### **1. Transform Image**
```http
POST /transform
Content-Type: multipart/form-data

Request:
{
  "image": <file>,
  "vibe": "modern",
  "colors": "neutral",
  "description": "Add more plants",
  "reference_images": [<file1>, <file2>],
  "preserve_layout": true,
  "quality": "high" // "standard" or "high"
}

Response:
{
  "job_id": "uuid-xxx",
  "status": "processing",
  "estimated_time": 5,
  "original_url": "https://...",
  "message": "Your transformation is being processed"
}
```

#### **2. Get Transformation Status**
```http
GET /transform/{job_id}

Response:
{
  "job_id": "uuid-xxx",
  "status": "completed", // "processing", "completed", "failed"
  "original_url": "https://...",
  "transformed_url": "https://...",
  "processing_time": 4.2,
  "created_at": "2025-01-04T10:30:00Z",
  "metadata": {
    "vibe": "modern",
    "colors": "neutral",
    "model_used": "adirik/interior-design"
  }
}
```

#### **3. Get User History**
```http
GET /user/transformations?limit=10&offset=0

Response:
{
  "transformations": [
    {
      "id": "uuid-xxx",
      "original_url": "https://...",
      "transformed_url": "https://...",
      "created_at": "2025-01-04T10:30:00Z",
      "vibe": "modern",
      "colors": "neutral"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

#### **4. Download Image**
```http
GET /download/{transformation_id}

Response: Binary image data with appropriate headers
```

#### **5. Webhook for Processing Completion** (Optional)
```http
POST /webhooks/replicate

Receives callback from Replicate when processing completes
Updates job status and notifies user
```

---

## 🔄 Image Processing Pipeline

### **Step-by-Step Flow**

```
1. User uploads image + preferences
         ↓
2. Validate image (format, size, content)
         ↓
3. Generate unique job ID
         ↓
4. Upload original to S3 with signed URL
         ↓
5. Build AI prompt from user preferences
         ↓
6. Queue job for processing
         ↓
7. Return job_id to frontend (immediate response)
         ↓
8. Background worker picks up job
         ↓
9. Call Replicate API with:
   - Original image URL
   - Generated prompt
   - Style parameters
         ↓
10. Poll Replicate for completion (or webhook)
         ↓
11. Download transformed image
         ↓
12. Upload to S3
         ↓
13. Update database with URLs and metadata
         ↓
14. Notify frontend via WebSocket/Server-Sent Events
         ↓
15. User sees result
```

### **Smart Prompt Building**

```python
def build_prompt(vibe, colors, description, reference_images):
    """
    Convert user preferences into optimized AI prompt
    """

    # Base style prompts
    vibe_prompts = {
        "modern": "contemporary, clean lines, sleek furniture, minimalist decor",
        "minimalist": "simple, uncluttered, neutral palette, essential furniture only",
        "cozy": "warm, comfortable, inviting, soft textures, ambient lighting",
        "industrial": "exposed brick, metal elements, concrete, Edison bulbs, loft style",
        "bohemian": "eclectic, colorful textiles, plants, vintage pieces, layered decor",
        "scandinavian": "light wood, white walls, natural materials, hygge, functional",
        "luxurious": "elegant, high-end materials, chandeliers, plush furniture, ornate",
        "rustic": "wood beams, natural stone, vintage furniture, farmhouse style"
    }

    # Color palette prompts
    color_prompts = {
        "neutral": "beige, white, gray, cream, taupe color scheme",
        "warm": "terracotta, amber, rust, golden tones",
        "cool": "blue, teal, mint, cool gray tones",
        "earthy": "brown, olive green, terracotta, natural wood tones",
        "pastel": "soft pink, lavender, mint, baby blue, muted colors",
        "bold": "vibrant colors, deep jewel tones, saturated hues"
    }

    # Construct final prompt
    prompt_parts = [
        f"A {vibe} interior design,",
        vibe_prompts[vibe],
        f"with {color_prompts[colors]},",
        "photorealistic, high quality, professional photography,",
        "8k resolution, detailed textures"
    ]

    if description:
        prompt_parts.append(description)

    positive_prompt = " ".join(prompt_parts)

    # Negative prompt for quality
    negative_prompt = (
        "ugly, distorted, low quality, blurry, pixelated, "
        "unrealistic, artificial, cartoonish, amateur"
    )

    return positive_prompt, negative_prompt
```

---

## 💾 Database Schema

### **PostgreSQL Tables**

#### **users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    credits INTEGER DEFAULT 10,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **transformations**
```sql
CREATE TABLE transformations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',
    original_image_url TEXT NOT NULL,
    transformed_image_url TEXT,
    vibe VARCHAR(50),
    colors VARCHAR(50),
    description TEXT,
    processing_time_seconds FLOAT,
    model_used VARCHAR(100),
    prompt_used TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_transformations_user_id ON transformations(user_id);
CREATE INDEX idx_transformations_status ON transformations(status);
CREATE INDEX idx_transformations_created_at ON transformations(created_at DESC);
```

#### **reference_images**
```sql
CREATE TABLE reference_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_id UUID REFERENCES transformations(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    image_type VARCHAR(50), -- 'furniture', 'color', 'object'
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **api_keys** (for future API access)
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 Authentication & Authorization

### **Strategy: JWT + Refresh Tokens**

```python
# Auth Flow
1. User signs up/logs in → Get JWT access token (15min) + refresh token (7 days)
2. Store refresh token in httpOnly cookie
3. Access token in memory (frontend)
4. API calls include: Authorization: Bearer <access_token>
5. When access token expires → Use refresh token to get new access token
6. If refresh token expires → Re-authenticate
```

### **Rate Limiting**

```python
# Different tiers
FREE_TIER = {
    "transformations_per_day": 5,
    "max_image_size_mb": 5,
    "queue_priority": 1
}

PRO_TIER = {
    "transformations_per_day": 100,
    "max_image_size_mb": 10,
    "queue_priority": 2,
    "webhook_support": true
}

ENTERPRISE_TIER = {
    "transformations_per_day": "unlimited",
    "max_image_size_mb": 20,
    "queue_priority": 3,
    "webhook_support": true,
    "dedicated_support": true
}
```

### **Implementation**
- Use Redis for rate limiting counters
- Implement per-user and per-IP rate limits
- Return appropriate headers:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 73
  X-RateLimit-Reset: 1704369600
  ```

---

## 📦 Object Storage Strategy

### **AWS S3 / Cloudflare R2**

```
Bucket Structure:
/production
  /originals
    /2025
      /01
        /04
          /{user_id}
            /{uuid}.jpg
  /transformed
    /2025
      /01
        /04
          /{user_id}
            /{uuid}.jpg
  /references
    /2025
      /01
        /04
          /{user_id}
            /{uuid}.jpg
```

### **Lifecycle Policies**
```
- Original images: Keep for 30 days (free tier) / 365 days (paid tier)
- Transformed images: Keep for 90 days (free tier) / indefinite (paid tier)
- Reference images: Keep for 30 days
- After expiration: Archive to Glacier or delete
```

### **CDN Configuration**
- Use CloudFront/Cloudflare CDN for fast delivery
- Signed URLs for private content
- Cache-Control headers for optimization
- Automatic image optimization (WebP conversion, compression)

---

## 🚀 Background Job Queue

### **Technology: Celery (Python) or Bull (Node.js)**

**Recommended: Celery with Redis**

```python
# tasks.py
from celery import Celery
import replicate

app = Celery('tasks', broker='redis://localhost:6379')

@app.task(bind=True, max_retries=3)
def process_transformation(self, job_id, image_url, prompt, negative_prompt):
    try:
        # Call Replicate API
        output = replicate.run(
            "adirik/interior-design:76604baddc85a8fdb0b3cad03c9fd9634ff8c64c0e15f74e9f2be61dc63e5c7f",
            input={
                "image": image_url,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            }
        )

        # Update database with result
        update_transformation_status(job_id, 'completed', output)

        # Notify user via WebSocket
        notify_user(job_id, 'completed')

    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### **Queue Priorities**
```python
# High priority (paid users)
process_transformation.apply_async(
    args=[job_id, image_url, prompt, negative_prompt],
    priority=9
)

# Normal priority (free users)
process_transformation.apply_async(
    args=[job_id, image_url, prompt, negative_prompt],
    priority=5
)
```

---

## 🔔 Real-time Updates

### **Server-Sent Events (SSE) or WebSockets**

**Recommended: Server-Sent Events (simpler for one-way updates)**

```python
# FastAPI endpoint
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

@app.get("/stream/{job_id}")
async def stream_transformation_status(job_id: str):
    async def event_generator():
        while True:
            status = await get_transformation_status(job_id)

            yield f"data: {json.dumps(status)}\n\n"

            if status['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Frontend Integration:**
```typescript
const eventSource = new EventSource(`/api/stream/${jobId}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.status === 'completed') {
    setTransformedImage(data.transformed_url);
    eventSource.close();
  }
};
```

---

## 💰 Cost Estimation

### **Monthly Cost Breakdown (1000 users, avg 10 transformations/user)**

| Service | Usage | Cost |
|---------|-------|------|
| Replicate API | 10,000 transformations × $0.012 | ~$120 |
| AWS S3 Storage | 50GB storage + 100GB transfer | ~$15 |
| CloudFront CDN | 500GB data transfer | ~$40 |
| AWS RDS (PostgreSQL) | db.t3.medium | ~$60 |
| Redis (ElastiCache) | cache.t3.micro | ~$15 |
| EC2/App Hosting | 2× t3.medium instances | ~$70 |
| **Total** | | **~$320/month** |

### **Revenue Model**
```
Free Tier: 5 transformations/day (loss leader)
Pro Tier: $9.99/month → 100 transformations
Enterprise: $49.99/month → Unlimited transformations

Break-even: ~40 Pro users or ~7 Enterprise users
```

---

## 🛠️ Implementation Phases

### **Phase 1: MVP (2-3 weeks)**
- ✅ Basic FastAPI backend
- ✅ Replicate integration (adirik/interior-design)
- ✅ S3 image storage
- ✅ PostgreSQL database
- ✅ Simple authentication (JWT)
- ✅ Basic rate limiting
- ✅ Frontend integration

### **Phase 2: Enhanced Features (2-3 weeks)**
- ✅ Background job queue (Celery)
- ✅ Real-time updates (SSE)
- ✅ User dashboard
- ✅ Transformation history
- ✅ Download functionality
- ✅ Email notifications

### **Phase 3: Production Ready (2-3 weeks)**
- ✅ Payment integration (Stripe)
- ✅ Subscription management
- ✅ Advanced rate limiting
- ✅ Monitoring & logging
- ✅ Error tracking (Sentry)
- ✅ Performance optimization
- ✅ CDN setup

### **Phase 4: Advanced Features (Ongoing)**
- ✅ Multiple model options
- ✅ A/B testing different models
- ✅ Custom model fine-tuning
- ✅ Bulk processing
- ✅ API for third-party access
- ✅ Mobile apps

---

## 📊 Monitoring & Observability

### **Key Metrics to Track**

```python
# Application Metrics
- Transformation success rate
- Average processing time
- Queue length and wait time
- API response times
- Error rates by endpoint
- User engagement (transformations per user)

# Business Metrics
- Daily active users (DAU)
- Conversion rate (free → paid)
- Churn rate
- Average revenue per user (ARPU)
- Credits consumed
- Cost per transformation

# Infrastructure Metrics
- CPU/Memory usage
- Database connections
- S3 storage used
- API rate limit hits
- Replicate API costs
```

### **Tools**
- **Application Monitoring**: Datadog, New Relic, or Prometheus + Grafana
- **Error Tracking**: Sentry
- **Logging**: ELK Stack or CloudWatch
- **Uptime Monitoring**: UptimeRobot, Pingdom

---

## 🔒 Security Considerations

### **Image Upload Security**
```python
# Validate file types
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

# Check file size
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Scan for malicious content
# Use ClamAV or VirusTotal API

# Strip EXIF data
from PIL import Image

def sanitize_image(image_path):
    img = Image.open(image_path)
    data = list(img.getdata())
    image_without_exif = Image.new(img.mode, img.size)
    image_without_exif.putdata(data)
    return image_without_exif
```

### **API Security**
- HTTPS only
- CORS configuration
- SQL injection prevention (use ORMs)
- Input validation and sanitization
- Secrets management (AWS Secrets Manager)
- Regular security audits

---

## 🚀 Deployment Strategy

### **Infrastructure as Code (Terraform)**

```hcl
# Basic architecture
- Application Load Balancer
- Auto Scaling Group (2-10 instances)
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis
- S3 buckets with lifecycle policies
- CloudFront CDN
- Route53 DNS
- ACM SSL certificates
```

### **CI/CD Pipeline**
```yaml
# GitHub Actions
1. Run tests
2. Build Docker image
3. Push to ECR
4. Deploy to staging
5. Run integration tests
6. Deploy to production (manual approval)
7. Run smoke tests
```

### **Environment Variables**
```bash
# .env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=...
REPLICATE_API_KEY=...
JWT_SECRET=...
STRIPE_API_KEY=...
SENTRY_DSN=...
```

---

## 📝 Next Steps

1. **Choose Final Model**: Recommend starting with **Replicate's adirik/interior-design**
2. **Set up Development Environment**: FastAPI + PostgreSQL + Redis
3. **Implement Core API Endpoints**: /transform, /status, /history
4. **Integrate Replicate API**: Test with sample images
5. **Set up S3 Storage**: Configure buckets and CDN
6. **Build Job Queue**: Celery worker for background processing
7. **Add Authentication**: JWT-based auth system
8. **Connect Frontend**: Update React app to use new API
9. **Testing**: Unit tests, integration tests, load testing
10. **Deploy MVP**: Launch to staging environment

---

## 🎯 Recommended Starting Point

**Build MVP with:**
- FastAPI backend
- Replicate's adirik/interior-design model
- PostgreSQL database
- AWS S3 storage
- Simple JWT auth
- Docker containerization

**Estimated Timeline**: 2-3 weeks for MVP
**Estimated Initial Cost**: ~$100-200/month (low traffic)

