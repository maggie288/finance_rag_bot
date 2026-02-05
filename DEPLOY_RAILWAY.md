# Railway Deployment Guide for Finance RAG Bot

## Quick Deploy

### 1. Create New Project on Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project (if already connected to GitHub)
railway link
```

### 2. Deploy from GitHub

1. Go to https://railway.app/new
2. Select "Deploy from GitHub repo"
3. Choose `maggie288/finance_rag_bot`
4. Select the `backend` directory
5. Add environment variables (see below)
6. Deploy!

### 3. Add Services

#### PostgreSQL
```bash
railway add postgresql
```

#### Redis
```bash
railway add redis
```

## Environment Variables

Configure these in Railway Dashboard or `.env`:

```env
# Database (auto-filled when you add PostgreSQL service)
DATABASE_URL=postgresql://user:pass@hostname:5432/dbname

# Redis (auto-filled when you add Redis service)
REDIS_URL=redis://:password@hostname:6379/0

# JWT (IMPORTANT: Generate a secure random string)
JWT_SECRET=your-super-secret-jwt-key-at-least-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# TwelveData API (https://twelvedata.com/)
TWELVEDATA_API_KEY=your-twelvedata-api-key

# Pinecone Vector DB (https://app.pinecone.io/)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=finance-rag-bot

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-api03-...
DEEPSEEK_API_KEY=sk-...
MINIMAX_API_KEY=...

# Embedding (free local model)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# CORS (your Vercel frontend URL)
CORS_ORIGINS=https://your-app.vercel.app

# Default Credits
DEFAULT_CREDITS=100.0
```

## Health Check

Railway uses `/health` endpoint for health checks. This is already configured in `railway.toml`:

```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
```

## Scaling

### Vertical Scaling (Resource Tier)
- Go to Railway Dashboard → Your Service → Settings
- Increase "Railway Machine" (recommend: 2GB RAM minimum)

### Horizontal Scaling
- Railway supports multiple replicas
- Go to Service → Networking → Add domain
- Configure load balancer if needed

## Troubleshooting

### Build Fails
```bash
# Check build logs in Railway Dashboard
# Common issues:
# 1. Missing environment variables
# 2. Python version mismatch (use Python 3.11)
# 3. Dependency conflicts
```

### Database Connection Failed
```bash
# Check DATABASE_URL format
postgresql://username:password@hostname:5432/database_name

# Verify database is running
railway status
```

### Out of Memory
```bash
# Increase memory in Railway settings
# Recommended: 2GB minimum for ML models
```

## Deploy Backend Only (without services)

```bash
cd backend
railway deploy
```

## Useful Commands

```bash
# View logs
railway logs

# Open shell
railway run bash

# Check status
railway status

# Restart service
railway up
```

## CI/CD with GitHub

Railway automatically deploys when you push to GitHub. Configure in:
Railway Dashboard → Your Project → Settings → Git Sync
