# Finance RAG Bot - Production Deployment Guide

## Overview

Finance RAG Bot is a comprehensive AI-powered investment assistant platform featuring:
- **Stock Market Data**: A-share, HK-share, US-stock, and cryptocurrency data aggregation
- **AI Trading Agent**: Intelligent trading signals and portfolio management
- **RAG-powered Chat**: Context-aware investment Q&A with knowledge base
- **ClawdBot Auto-Trading**: Automated trading through Polymarket prediction markets
- **Real-time Market Data**: Redis-cached quotes with automatic refresh
- **News Aggregation**: Automated news fetching and sentiment analysis

## Production Deployment

### Prerequisites

- Docker & Docker Compose v2
- PostgreSQL 16+ (or use provided Docker setup)
- Redis 7+ (or use provided Docker setup)
- 4GB+ RAM (8GB recommended for AI models)
- 10GB+ disk space

### Quick Start

#### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd finance_rag_bot

# Copy production environment template
cp backend/.env.production backend/.env

# Edit with your production values
nano backend/.env
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secure random string (32+ chars)
- `TWELVEDATA_API_KEY`: TwelveData API key for stock data
- `DEEPSEEK_API_KEY`: DeepSeek API key for LLM
- `PINECONE_API_KEY`: Pinecone API key for vector storage

#### 2. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

#### 3. Manual Deployment (without Docker)

```bash
# Backend
cd backend
python3 -m pip install -r requirements.txt
cp .env.production .env  # Edit with your values
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm install
npm run build
npm start
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | Main application API |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & Celery broker |

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response
{"status": "ok", "service": "Finance RAG Bot"}
```

## Scheduled Tasks

For production, run scheduled tasks separately:

```bash
# Start all scheduled tasks (Celery Worker + Beat)
./scheduler.sh start

# Or individually:
./scheduler.sh worker    # Celery Worker (news fetching, data processing)
./scheduler.sh beat      # Celery Beat (task scheduler)

# Check status
./scheduler.sh status

# Stop all
./scheduler.sh stop
```

### Task Details

| Task | Type | Frequency | Description |
|------|------|-----------|-------------|
| News Fetching | Celery Beat | Every 15 min | Fetches market news |
| Quote Refresh | APScheduler | Every 5 min | Updates cached stock quotes |
| Watchlist Sync | APScheduler | Hourly | Syncs user watchlist data |
| Data Cleanup | Manual | As needed | Cleans old K-line data |

## Environment Variables

### Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET` | Yes | Secret key for JWT tokens |
| `TWELVEDATA_API_KEY` | Yes | TwelveData API key |
| `DEEPSEEK_API_KEY` | No | DeepSeek LLM API key |
| `OPENAI_API_KEY` | No | OpenAI LLM API key |
| `ANTHROPIC_API_KEY` | No | Anthropic LLM API key |
| `PINECONE_API_KEY` | No | Pinecone vector DB API key |
| `EMBEDDING_MODEL` | No | Embedding model (default: sentence-transformers/all-MiniLM-L6-v2) |
| `CORS_ORIGINS` | Yes | Comma-separated CORS origins |
| `DEFAULT_CREDITS` | No | Default user credits (default: 100.0) |

### Frontend

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL (default: http://localhost:8000) |

## API Documentation

Once deployed, access Swagger documentation at:
```
http://your-domain:8000/docs
```

## Monitoring

### Logs

```bash
# Backend logs (Docker)
docker-compose -f docker-compose.prod.yml logs backend

# All logs
docker-compose -f docker-compose.prod.yml logs
```

### Health Endpoints

- `GET /health` - Overall health check
- `GET /health/db` - Database health
- `GET /health/redis` - Redis health

## Scaling

### Horizontal Scaling (Multiple Backend Instances)

```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      replicas: 3
```

### Production Nginx Setup (Recommended)

```nginx
upstream finance_rag_bot {
    server localhost:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://finance_rag_bot;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Database Migrations

```bash
# Run migrations (Docker)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Manual
cd backend
alembic upgrade head
```

### Reset Database

```bash
# Warning: This will delete all data
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Set strong `JWT_SECRET`
- [ ] Configure `CORS_ORIGINS` for production domain
- [ ] Enable SSL/TLS (Let's Encrypt recommended)
- [ ] Set up firewall rules
- [ ] Enable database encryption
- [ ] Rotate API keys regularly

## Backup & Recovery

### Database Backup

```bash
# Backup (Docker)
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U finance_bot finance_rag_bot > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U finance_bot -d finance_rag_bot < backup.sql
```

### Automated Backups (Cron)

```bash
# Add to crontab
0 3 * * * docker-compose -f /path/to/finance_rag_bot/docker-compose.prod.yml exec -T postgres pg_dump -U finance_bot finance_rag_bot | gzip > /backup/finance_rag_bot_$(date +\%Y\%m\%d).sql.gz
```

## License

MIT License
