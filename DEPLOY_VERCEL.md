# Vercel Deployment Guide for Finance RAG Bot Frontend

## Quick Deploy

### 1. Deploy from GitHub

1. Go to https://vercel.com/new
2. Select "Import Git Repository"
3. Choose `maggie288/finance_rag_bot`
4. Configure project:
   - Framework Preset: `Next.js`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

### 2. Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy (first time)
cd frontend
vercel

# Link to existing project
vercel --prod
```

## Environment Variables

Configure in Vercel Dashboard → Your Project → Settings → Environment Variables:

```env
# Required
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Optional (for development)
NEXT_PUBLIC_DEBUG=false
```

## Custom Domain

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed

## Configuration

`vercel.json` is already configured with:

```json
{
  "framework": "nextjs",
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next"
}
```

## Troubleshooting

### 404 on API Routes
- Ensure `NEXT_PUBLIC_API_URL` points to your backend
- Backend must be deployed and accessible

### CORS Errors
- Add your Vercel URL to backend's `CORS_ORIGINS` environment variable
- Format: `https://your-app.vercel.app`

### Build Fails
```bash
# Test build locally
cd frontend
npm run build

# Check Node version
node -v  # Should be 18.x or 20.x
```

## Production Settings

### Security Headers
Already configured in `vercel.json`:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin

### Performance
- Next.js automatically optimizes images and fonts
- Consider enabling Edge caching in Vercel Dashboard

## Deploy with Custom Domain

```bash
# Add custom domain
vercel domains add your-domain.com

# Deploy to production
vercel --prod --domains your-domain.com
```

## Git Integration

Vercel automatically deploys on every push to main branch. Configure in:
Vercel Dashboard → Your Project → Settings → Git
