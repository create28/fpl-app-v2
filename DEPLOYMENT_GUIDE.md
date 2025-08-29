# 🚀 FPL App Deployment Guide

## Overview

This guide explains how to deploy your FPL application to Render while maintaining a local development version.

## 🏠 **Local Development (Port 8000)**

### Quick Start
```bash
# Run locally for development
python3 run_local.py

# Or run directly
python3 main.py
```

**Local URL**: http://localhost:8000

### Local Features
- ✅ Full Python backend with HTTP server
- ✅ SQLite database
- ✅ All API endpoints working
- ✅ Real-time data processing
- ✅ Award calculations

---

## ☁️ **Production Deployment (Render)**

### Step 1: Connect to Render
1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository: `create28/fpl-app-v2`

### Step 2: Configure Service
- **Name**: `fpl-app-v2`
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Plan**: Free (or paid if you need more resources)

### Step 3: Environment Variables
Add these in Render dashboard:
```
ENVIRONMENT=production
PORT=8000
API_BASE_URL=https://your-app-name.onrender.com
```

### Step 4: Deploy
- Click "Create Web Service"
- Render will automatically build and deploy
- Your app will be available at: `https://your-app-name.onrender.com`

---

## 🔄 **How It Works**

### Environment Detection
The app automatically detects where it's running:

```javascript
// Frontend automatically detects environment
const isProduction = window.location.hostname !== 'localhost';
const API_BASE_URL = isProduction 
    ? 'https://fpl-app-v2.onrender.com'  // Production
    : 'http://localhost:8000';            // Local
```

### Configuration Management
```python
# config.py handles different environments
class Config:
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    if IS_PRODUCTION:
        API_BASE_URL = os.getenv('API_BASE_URL', 'https://fpl-app-v2.onrender.com')
    else:
        API_BASE_URL = f'http://{HOST}:{PORT}'
```

---

## 🎯 **Running Both Versions**

### Option 1: Two Terminal Windows
```bash
# Terminal 1: Local Development
cd "14 FPL Updated"
python3 run_local.py

# Terminal 2: Production (Render)
# Deploy to Render and access via browser
```

### Option 2: Different Ports
```bash
# Local on port 8000
python3 run_local.py

# Production on Render (different port automatically assigned)
```

---

## 📱 **Testing Both Versions**

### Local Testing
1. Open http://localhost:8000
2. Check browser console: "Environment: Local Development"
3. All API calls go to localhost:8000

### Production Testing
1. Open your Render URL (e.g., https://fpl-app-v2.onrender.com)
2. Check browser console: "Environment: Production"
3. All API calls go to Render

---

## 🔧 **Troubleshooting**

### Local Issues
```bash
# Check if port 8000 is free
lsof -ti:8000

# Kill any existing processes
lsof -ti:8000 | xargs kill -9

# Restart local server
python3 run_local.py
```

### Render Issues
1. Check Render logs in dashboard
2. Verify environment variables
3. Ensure `requirements.txt` is correct
4. Check if Python version is supported

### API Endpoint Issues
- Local: http://localhost:8000/api/current-gameweek
- Production: https://your-app.onrender.com/api/current-gameweek

---

## 📊 **Monitoring**

### Local Monitoring
- Server logs in terminal
- Database: `fpl_history.db`
- Port: 8000

### Production Monitoring
- Render dashboard logs
- Health check: `/api/current-gameweek`
- Automatic restarts on failure

---

## 🚀 **Deployment Commands**

### Update and Deploy
```bash
# 1. Make changes locally
# 2. Test locally
python3 run_local.py

# 3. Commit changes
git add .
git commit -m "Your changes"
git push origin main

# 4. Render automatically redeploys
# 5. Test production
# 6. Both versions are now updated
```

---

## ✅ **Success Checklist**

- [ ] Local version runs on http://localhost:8000
- [ ] Production version deployed to Render
- [ ] Both versions accessible simultaneously
- [ ] API endpoints working on both
- [ ] Environment detection working
- [ ] Database working locally
- [ ] Production logs accessible

---

## 🆘 **Need Help?**

### Common Issues
1. **Port 8000 in use**: Kill existing processes
2. **Import errors**: Check you're in the right directory
3. **Render deployment fails**: Check logs and requirements.txt
4. **API 404 errors**: Verify environment detection

### Support
- Check Render logs first
- Verify environment variables
- Test locally before deploying
- Check browser console for environment detection

---

**Happy Deploying! 🎉**
