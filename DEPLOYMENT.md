# Crypto Trading AI - Cloud Deployment Guide

## Free/Cheap Cloud Hosting Options

### Option 1: Railway.app (Recommended)
**Free Tier**: $5 credit/month, ~500 hours of compute
**Pros**: Easy deployment, supports Docker, free PostgreSQL
**Cons**: Limited free tier

#### Deployment Steps:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

#### railway.toml Configuration:
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Option 2: Render.com
**Free Tier**: 750 hours/month for web services
**Pros**: Free PostgreSQL & Redis, auto-deploy from GitHub
**Cons**: Spins down after 15 min inactivity

#### render.yaml:
```yaml
services:
  - type: web
    name: crypto-api
    env: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: crypto-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: crypto-redis
          type: redis
          property: connectionString
    
  - type: web
    name: crypto-frontend
    env: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: ./frontend/build
    headers:
      - path: /*
        name: X-Frame-Options
        value: DENY

databases:
  - name: crypto-db
    plan: free

services:
  - type: redis
    name: crypto-redis
    plan: free
```

### Option 3: Fly.io
**Free Tier**: 3 shared VMs, 3GB storage
**Pros**: Global deployment, WebSocket support
**Cons**: Credit card required

#### fly.toml:
```toml
app = "crypto-trading-ai"

[env]
  PORT = "8080"

[experimental]
  auto_rollback = true

[[services]]
  http_checks = []
  internal_port = 8080
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

### Option 4: Vercel (Frontend Only)
**Free Tier**: Unlimited for personal use
**Pros**: Excellent for React apps, auto-SSL
**Cons**: Frontend only, need separate backend

#### vercel.json:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.railway.app/api/:path*"
    }
  ]
}
```

## Hybrid Deployment Strategy (Recommended)

### 1. Frontend: Vercel (Free)
- Deploy React app to Vercel
- Automatic HTTPS, global CDN
- GitHub integration

### 2. Backend API: Railway (Free tier)
- Deploy FastAPI server
- WebSocket support
- Includes PostgreSQL

### 3. ML Training: Local Desktop
- Use your RTX 4080 for training
- Upload models to cloud storage
- API fetches latest models

### 4. Data Storage: Supabase (Free tier)
- PostgreSQL with 500MB storage
- Real-time subscriptions
- Built-in auth

## Deployment Commands

### Quick Deploy to Railway:
```bash
# Frontend
cd frontend
railway init
railway add
railway up

# Backend
cd ..
railway init
railway add
railway up
```

### Environment Variables:
```env
# Railway automatically provides:
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
PORT=...

# You need to add:
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
# etc.
```

## Free Database Options

### 1. Supabase
- 500MB PostgreSQL
- Real-time subscriptions
- 2GB file storage

### 2. PlanetScale
- 10GB MySQL
- Serverless scaling
- Branch databases

### 3. Neon
- 3GB PostgreSQL
- Serverless
- Branching

### 4. MongoDB Atlas
- 512MB free cluster
- Good for logs/history

## Monitoring (Free Tier)

### 1. Sentry
- Error tracking
- Performance monitoring
- 5k events/month free

### 2. LogDNA
- Log aggregation
- 2GB/month free
- Real-time tail

### 3. UptimeRobot
- Uptime monitoring
- 50 monitors free
- 5-minute checks

## SSL/Domain

### 1. Cloudflare (Recommended)
- Free SSL
- DDoS protection
- Analytics

### 2. Let's Encrypt
- Free SSL certificates
- Auto-renewal
- Wide support

## Deployment Script

Create `deploy.sh`:
```bash
#!/bin/bash

# Build frontend
cd frontend
npm run build
cd ..

# Deploy to Railway
railway up

# Or deploy to Render
# render deploy

# Or deploy to Fly.io
# flyctl deploy

echo "Deployment complete!"
```

## Cost Optimization Tips

1. **Use Serverless Functions**: For pump detection alerts
2. **Cache Aggressively**: Redis for market data
3. **Compress Data**: Use gzip for API responses
4. **Schedule Heavy Tasks**: Run ML training during off-peak
5. **Use CDN**: CloudFlare for static assets

## Production Checklist

- [ ] Environment variables set
- [ ] SSL configured
- [ ] Error logging enabled
- [ ] Rate limiting configured
- [ ] Database backups scheduled
- [ ] Monitoring alerts set
- [ ] API keys secured
- [ ] CORS configured
- [ ] WebSocket scaling tested
- [ ] Graceful shutdown handling
