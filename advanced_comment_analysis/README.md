# ACAS: Advanced Comment Analysis System (MVP)

A production-ready MVP for AI-powered comment analysis, ticket routing, and sentiment analysis. Built with **FastAPI** (backend), **SQLite** (local dev), and **React** (frontend).

## Quick Start (60 seconds)

### One-Command Startup

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\START_HERE.ps1
```

This will:
- ✓ Create Python virtualenv (if needed)
- ✓ Install Python dependencies  
- ✓ Create SQLite database
- ✓ Start FastAPI backend on **http://127.0.0.1:8000**

### Open the Dashboard

Open `frontend/static_index.html` directly in your browser (no build needed!).

### Test a Comment

```powershell
# Test the AI analysis endpoint
$body = @{ comment_text = "This API keeps crashing!" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8000/ai/analyze" `
  -Method Post -Body $body -ContentType "application/json" | ForEach-Object Content | ConvertFrom-Json
```

Expected response:
```json
{
  "emotion": "frustration",
  "intent": "support", 
  "priority": "High",
  "needs_ticket": true,
  "confidence": 0.94,
  "suggested_response": "We sincerely apologize..."
}
```

---

## Features

- ✅ AI comment analysis (local fallback + OpenAI integration)
- ✅ Automatic ticket routing (Support / Tech / Product)
- ✅ Real-time dashboard with KPIs
- ✅ JWT authentication
- ✅ CSV batch import
- ✅ SQLite local database (+ Postgres support)
- ✅ RBAC (role-based access control)
- ✅ 100% offline mode (no Docker required)

---

## API Endpoints

### Health Check
```
GET /health
→ { "status": "ok" }
```

### Auth
```
POST /auth/register
{ "email": "admin@local", "password": "pass" }

POST /auth/token
username=admin@local&password=pass
→ { "access_token": "eyJ0...", "token_type": "bearer" }
```

### AI Analysis
```
POST /ai/analyze
Authorization: Bearer <token>
{ "comment_text": "Your API is slow" }
→ { "emotion": "...", "priority": "...", "confidence": 0.94, ...}
```

### Comments & Tickets
```
POST /comments          # Add comment
GET /comments           # List comments
POST /comments/upload   # CSV batch import
GET /tickets            # List tickets
POST /tickets/{id}/close
```

### Dashboard
```
GET /dashboard/metrics  # Returns KPIs for frontend
```

---

## Configuration

Check `.env`:
```
FORCE_LOCAL=true           # Use simulated AI (offline mode)
USE_SQLITE_DEV=true        # Use local SQLite
DATABASE_URL=sqlite:///data/dev.db
JWT_SECRET_KEY=local-secret-change-in-prod
AI_CONFIDENCE_THRESHOLD=0.85
```

---

## Development

### Run Tests
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

### Add an Endpoint
1. Create schema in `app/schemas/feature.py`
2. Create service in `app/services/feature_service.py`
3. Create router in `app/api/feature.py`
4. Include router in `app/main.py`

### Production Deployment

Use Docker Compose (includes Postgres + Streamlit):
```powershell
docker-compose up --build
```

Or manually with your own Postgres:
1. Set `USE_SQLITE_DEV=false` in `.env`
2. Set `DATABASE_URL=postgresql://...`
3. Install deps and run: `python -m uvicorn app.main:app`

---

## Troubleshooting

**Port 8000 in use?**
```powershell
$pid = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
Stop-Process -Id $pid -Force
```

**Module import errors?**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Database locked?**
Kill all Python processes and restart.

---

**Built with ❤️ for faster comment analysis**
