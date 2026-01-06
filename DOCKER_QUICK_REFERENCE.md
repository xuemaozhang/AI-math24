# Docker Quick Reference

## 🚀 Quick Start

```bash
# Run the automated test suite
./test-docker.sh

# Or manually start services
docker compose up -d

# View logs
docker compose logs -f
```

## 📋 Common Commands

### Starting/Stopping
```bash
# Start services (detached)
docker compose up -d

# Start with logs visible
docker compose up

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Building
```bash
# Build images
docker compose build

# Rebuild and start
docker compose up -d --build

# Build without cache
docker compose build --no-cache
```

### Monitoring
```bash
# Check status
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend
docker compose logs -f frontend

# Check last 50 lines
docker compose logs --tail 50
```

### Testing
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost/health

# Test API
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"numbers":[3,8,3,8],"expression":"8/(3-8/3)","target":24}'
```

### Debugging
```bash
# Enter backend container
docker compose exec backend bash

# Enter frontend container  
docker compose exec frontend sh

# View container stats
docker stats
```

## 🔧 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend

# Verify .env file
cat backend/.env

# Restart service
docker compose restart backend
```

### Frontend Won't Build
```bash
# Clean build
docker compose build --no-cache frontend

# Check nginx logs
docker compose logs frontend
```

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Or port 80
lsof -i :80

# Change ports in docker-compose.yml
ports:
  - "8080:8000"  # Map to 8080 instead
```

## 📦 Image Management

```bash
# List images
docker images | grep math24

# Remove unused images
docker image prune

# Remove all unused data
docker system prune -a
```

## 🌐 Access Points

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000  
- **API Documentation:** http://localhost:8000/docs
- **Backend Health:** http://localhost:8000/health
- **Frontend Health:** http://localhost/health

## 📁 File Structure

```
AI-math24/
├── backend/
│   ├── Dockerfile          # Backend container config
│   ├── .dockerignore       # Build exclusions
│   ├── .env                # Environment variables
│   └── main.py             # FastAPI application
├── math24-game/
│   ├── Dockerfile          # Frontend container config
│   ├── .dockerignore       # Build exclusions
│   ├── nginx.conf          # Nginx configuration
│   └── src/                # React application
├── docker-compose.yml      # Service orchestration
├── test-docker.sh          # Automated test suite
└── DEPLOYMENT.md           # Cloud deployment guide
```

## ⚙️ Configuration

### Backend Environment Variables
Edit `backend/.env`:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Frontend API Base URL
Set at build time in `docker-compose.yml`:
```yaml
build:
  args:
    - VITE_API_BASE=http://your-backend-url
```

## 🔄 Development Workflow

### Local Development
```bash
# 1. Make code changes
# 2. Rebuild specific service
docker compose up -d --build backend

# 3. Check logs
docker compose logs -f backend
```

### Full Rebuild
```bash
# Stop everything
docker compose down

# Rebuild all
docker compose up -d --build

# Verify
./test-docker.sh
```

## 📊 Resource Usage

- **Backend Image:** ~336 MB
- **Frontend Image:** ~54 MB
- **RAM Usage:** ~200 MB total
- **Startup Time:** ~5 seconds

## ✅ Health Checks

Both services include automatic health checks:
- **Interval:** 30 seconds
- **Timeout:** 3 seconds  
- **Retries:** 3
- **Start Period:** 5 seconds

View health status:
```bash
docker compose ps
```

## 🚨 Common Issues

1. **"GEMINI_API_KEY not set"**
   - Check `backend/.env` file exists
   - Verify API key is set

2. **Port conflicts**
   - Change ports in `docker-compose.yml`
   - Kill conflicting processes

3. **Build failures**
   - Try `--no-cache` flag
   - Check Docker disk space

4. **Network issues**
   - Restart Docker Desktop
   - Check firewall settings
