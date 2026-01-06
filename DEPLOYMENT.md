# Docker Deployment Guide for Math24 Game

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Gemini API key

### Local Deployment

1. **Set up environment variables:**
   ```bash
   # Create .env file in backend directory
   echo "GEMINI_API_KEY=your_api_key_here" > backend/.env
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Health: http://localhost:8000/health

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Individual Container Builds

#### Backend Only
```bash
cd backend
docker build -t math24-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key math24-backend
```

#### Frontend Only
```bash
cd math24-game
docker build -t math24-frontend .
docker run -p 80:80 math24-frontend
```

## Free Cloud Deployment Options

### 🥇 Recommended: Render.com (Best Free Option)

**Why Render:**
- ✅ Free tier includes web services + databases
- ✅ Automatic HTTPS
- ✅ Easy Docker deployment
- ✅ Environment variables support
- ✅ 750 hours/month free (enough for 24/7)

**Deployment Steps:**

1. **Backend (Web Service):**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - Name: `math24-backend`
     - Root Directory: `backend`
     - Environment: `Docker`
     - Instance Type: `Free`
     - Add Environment Variable: `GEMINI_API_KEY` = your_key
   - Deploy!

2. **Frontend (Static Site):**
   - Click "New +" → "Static Site"
   - Connect your GitHub repo
   - Settings:
     - Name: `math24-frontend`
     - Root Directory: `math24-game`
     - Build Command: `npm install && npm run build`
     - Publish Directory: `dist`
     - Add Environment Variable: `VITE_API_BASE` = `https://math24-backend.onrender.com`
   - Deploy!

**Cost:** FREE ($0/month)

---

### 🥈 Alternative: Fly.io

**Why Fly.io:**
- ✅ Great free tier (3 VMs)
- ✅ Global edge network
- ✅ Native Docker support
- ✅ Easy CLI deployment

**Deployment Steps:**

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Deploy Backend:**
   ```bash
   cd backend
   fly launch --name math24-backend
   fly secrets set GEMINI_API_KEY=your_key
   fly deploy
   ```

3. **Deploy Frontend:**
   ```bash
   cd math24-game
   fly launch --name math24-frontend
   fly deploy
   ```

**Cost:** FREE for 3 shared VMs ($0/month)

---

### 🥉 Alternative: Railway.app

**Why Railway:**
- ✅ $5 free credit/month
- ✅ Very simple deployment
- ✅ Automatic HTTPS
- ✅ GitHub integration

**Deployment Steps:**

1. Go to [Railway.app](https://railway.app)
2. Connect GitHub repo
3. Create two services:
   - Backend: Select `backend` directory
   - Frontend: Select `math24-game` directory
4. Add environment variables
5. Deploy!

**Cost:** $5 credit/month (FREE effectively)

---

### Other Options

#### Google Cloud Run
- FREE tier: 2 million requests/month
- Best for: Production apps
- Deployment: `gcloud run deploy`

#### Vercel (Frontend) + Render (Backend)
- Frontend on Vercel: Unlimited bandwidth
- Backend on Render: Free tier
- Best for: Static frontend with API backend

#### Netlify (Frontend) + Railway (Backend)
- Similar to Vercel option
- Good CI/CD

## Recommended Setup

**For This Project:**
```
Frontend: Render Static Site (FREE)
Backend: Render Web Service (FREE)
Total Cost: $0/month
```

**Deployment Commands:**

```bash
# 1. Push to GitHub
git add .
git commit -m "Add Docker support"
git push

# 2. Go to Render.com and connect repo
# 3. Deploy both services (follow steps above)
# 4. Update frontend env with backend URL
# 5. Access your live app!
```

## Environment Variables

### Backend (.env)
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Frontend (build-time)
```env
VITE_API_BASE=https://your-backend-url.onrender.com
```

## Health Checks

Both services include health check endpoints:
- Backend: `/health`
- Frontend: `/health`

## Monitoring

Free monitoring options:
- Render: Built-in logs and metrics
- Fly.io: Built-in dashboard
- Railway: Real-time logs

## Troubleshooting

**Backend not connecting:**
- Check GEMINI_API_KEY is set
- Verify CORS settings in main.py

**Frontend can't reach backend:**
- Update VITE_API_BASE environment variable
- Rebuild frontend after changing API URL

**Docker build fails:**
- Check .dockerignore files
- Ensure all dependencies in package.json/pyproject.toml
