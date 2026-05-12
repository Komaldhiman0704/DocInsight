# Deployment Guide

Complete guide for deploying DocInsight to production environments.

---

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Azure Container Apps](#azure-container-apps)
3. [AWS ECS/Fargate](#aws-ecstargate)
4. [Railway](#railway)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Logging](#monitoring--logging)
7. [Scaling](#scaling)

---

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed
- Groq API key
- Basic familiarity with Docker

### Build & Run

**1. Create `.env` file:**

```env
# backend/.env
GROQ_API_KEY=your_api_key_here
LLM_MODEL=mixtral-8x7b-32768
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=4
```

**2. Build images:**

```bash
# Build backend
docker build -f backend/Dockerfile -t docinsight-backend:latest .

# Build frontend
docker build -f frontend/Dockerfile -t docinsight-frontend:latest .
```

**3. Run with Docker Compose:**

```bash
docker-compose up -d
```

### Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - LLM_MODEL=${LLM_MODEL}
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_db:/app/chroma_db
      - ./backend/chat_sessions:/app/chat_sessions
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://backend:8000/api
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: always
```

### Dockerfiles

**backend/Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY backend/ .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**frontend/Dockerfile:**

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY frontend/package*.json .
RUN npm ci

COPY frontend/ .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

---

## Azure Container Apps

### Prerequisites

- Azure CLI installed
- Azure subscription
- Resource group created

### Deployment Steps

**1. Create container registry:**

```bash
az acr create \
  --resource-group my-rg \
  --name docinsightacr \
  --sku Basic
```

**2. Build and push images:**

```bash
# Login to registry
az acr login --name docinsightacr

# Build backend
az acr build \
  --registry docinsightacr \
  --image docinsight-backend:latest \
  --file backend/Dockerfile .

# Build frontend
az acr build \
  --registry docinsightacr \
  --image docinsight-frontend:latest \
  --file frontend/Dockerfile .
```

**3. Create Container Apps environment:**

```bash
az containerapp env create \
  --name docinsight-env \
  --resource-group my-rg \
  --location eastus
```

**4. Deploy backend:**

```bash
az containerapp create \
  --name docinsight-backend \
  --resource-group my-rg \
  --environment docinsight-env \
  --image docinsightacr.azurecr.io/docinsight-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server docinsightacr.azurecr.io \
  --env-vars \
    GROQ_API_KEY="${GROQ_API_KEY}" \
    LLM_MODEL=mixtral-8x7b-32768
```

**5. Deploy frontend:**

```bash
az containerapp create \
  --name docinsight-frontend \
  --resource-group my-rg \
  --environment docinsight-env \
  --image docinsightacr.azurecr.io/docinsight-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server docinsightacr.azurecr.io \
  --env-vars VITE_API_URL="https://docinsight-backend.xxx.azurecontainerapps.io/api"
```

---

## AWS ECS/Fargate

### Prerequisites

- AWS CLI configured
- ECR repository created
- ECS cluster and task definition ready

### Deployment Steps

**1. Push images to ECR:**

```bash
# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -f backend/Dockerfile -t docinsight-backend:latest .
docker tag docinsight-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/docinsight-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/docinsight-backend:latest

# Build and push frontend
docker build -f frontend/Dockerfile -t docinsight-frontend:latest .
docker tag docinsight-frontend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/docinsight-frontend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/docinsight-frontend:latest
```

**2. Create task definition (task-definition.json):**

```json
{
  "family": "docinsight",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/docinsight-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LLM_MODEL",
          "value": "mixtral-8x7b-32768"
        }
      ],
      "secrets": [
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:groq-api-key"
        }
      ]
    }
  ]
}
```

**3. Register task definition:**

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

**4. Create service:**

```bash
aws ecs create-service \
  --cluster my-cluster \
  --service-name docinsight-service \
  --task-definition docinsight \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## Railway

### Prerequisites

- Railway account (https://railway.app)
- GitHub repository

### Deployment Steps

**1. Connect repository:**

- Go to Railway dashboard
- New Project → GitHub Repo

**2. Add services:**

- **Backend service:**
  - Source: Dockerfile → `backend/Dockerfile`
  - Port: 8000
  - Environment: Add `GROQ_API_KEY`

- **Frontend service:**
  - Source: Dockerfile → `frontend/Dockerfile`
  - Port: 3000
  - Environment: Add `VITE_API_URL=https://backend-url/api`

**3. Deploy:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

---

## Production Checklist

### Security

- [ ] Enable HTTPS/SSL certificates (Let's Encrypt recommended)
- [ ] Configure API authentication (API keys or OAuth)
- [ ] Set up firewall rules
- [ ] Enable CORS properly (restrict origins)
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up DDoS protection
- [ ] Use reverse proxy (Nginx/HAProxy)
- [ ] Enable request logging
- [ ] Regular security audits

### Performance

- [ ] Enable caching (Redis for sessions)
- [ ] Use CDN for frontend assets
- [ ] Configure database connection pooling
- [ ] Set up load balancing
- [ ] Optimize Docker image sizes
- [ ] Use health checks
- [ ] Configure auto-scaling policies
- [ ] Monitor resource utilization

### Data Management

- [ ] Set up automated backups
- [ ] Define retention policies
- [ ] Enable encryption at rest
- [ ] Encrypt in-transit (HTTPS)
- [ ] Test disaster recovery procedures
- [ ] Set up audit logging

### Monitoring & Alerts

- [ ] Set up application monitoring (New Relic, DataDog)
- [ ] Configure error tracking (Sentry)
- [ ] Set up log aggregation (ELK, Splunk)
- [ ] Create alerts for critical errors
- [ ] Monitor uptime
- [ ] Track performance metrics

### Maintenance

- [ ] Document deployment process
- [ ] Set up CI/CD pipeline
- [ ] Plan maintenance windows
- [ ] Test rollback procedures
- [ ] Keep dependencies updated
- [ ] Regular security patching

---

## Monitoring & Logging

### Application Monitoring

**Setup with New Relic:**

```python
# backend/main.py
import newrelic.agent

newrelic.agent.initialize('newrelic.ini')

@app.middleware("http")
async def add_newrelic(request: Request, call_next):
    return await call_next(request)
```

### Log Aggregation

**Setup with ELK Stack:**

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.0.0
    volumes:
      - ./backend/logs:/var/log/backend:ro
      - ./frontend/logs:/var/log/frontend:ro
```

### Health Checks

```bash
# Monitor endpoint
curl http://localhost:8000/api/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

## Scaling

### Horizontal Scaling

**Kubernetes:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docinsight-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docinsight-backend
  template:
    metadata:
      labels:
        app: docinsight-backend
    spec:
      containers:
      - name: backend
        image: docinsight-backend:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### Vertical Scaling

Increase container resources:

```bash
# Azure Container Apps
az containerapp update \
  --name docinsight-backend \
  --resource-group my-rg \
  --cpu 2 \
  --memory 4Gi
```

### Database Scaling

For large-scale deployments, consider:

- **Vector Database**: Use managed services (Pinecone, Weaviate Cloud)
- **Session Storage**: Use Redis or managed databases
- **File Storage**: Use S3/Blob Storage instead of local filesystem

```python
# Use managed vector store
from langchain.vectorstores import Pinecone

vector_store = Pinecone.from_documents(
    documents=docs,
    embedding=embeddings,
    index_name="docinsight"
)
```

---

## Troubleshooting Deployment

### Container won't start

```bash
# Check logs
docker logs <container_id>

# Check image
docker images

# Rebuild
docker build --no-cache -f backend/Dockerfile -t docinsight-backend .
```

### Memory issues

```bash
# Check memory usage
docker stats

# Increase memory limit
docker run --memory=4g docinsight-backend
```

### Network connectivity

```bash
# Test backend from frontend container
docker exec frontend-container curl http://backend:8000/api/health

# Check DNS resolution
docker exec backend-container nslookup backend
```

---

## Rollback Strategy

### Version Control

```bash
# Tag releases
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0

# Docker image versioning
docker tag docinsight-backend:latest docinsight-backend:v1.0.0
docker push docinsight-backend:v1.0.0
```

### Blue-Green Deployment

```bash
# Deploy new version (green)
docker-compose up -d --scale backend-green=1

# Test green environment
curl http://localhost:8001/api/health

# Switch traffic to green
# Update reverse proxy configuration

# Keep blue for rollback
docker-compose up -d --scale backend-blue=1
```

---

## Cost Optimization

- Use spot instances/preemptible VMs
- Implement auto-scaling (scale down during off-hours)
- Optimize image sizes
- Use cost monitoring tools
- Consider reserved instances for stable workloads

---

## Support

For deployment issues:
- Check logs in your cloud platform
- Review Docker Compose setup
- Consult [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Open GitHub issue with deployment details
