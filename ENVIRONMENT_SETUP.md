# Environment Variables & Secrets Management

## ⚠️ SECURITY NOTICE

**NEVER commit `.env` files or files containing API keys, passwords, or credentials to version control.**

This project uses `.gitignore` to prevent accidental commits. Always:
1. Copy `.env.example` → `.env`
2. Fill in your actual values in `.env` (which is ignored by git)
3. Never add `.env` to git

## Setup Instructions

### 1. Copy Example Files
```bash
# Root directory
cp .env.example .env

# Backend directory
cd backend
cp .env.example .env
cd ..
```

### 2. Configure Environment Variables

#### Root `.env`:
```env
YOUTUBE_API_KEY=your_actual_key_here
```

#### Backend `.env` (backend/.env):
```env
DATABASE_URL=sqlite:///./cycling_workouts.db  # or postgres://user:pass@host/db
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
API_V1_PREFIX=/api/v1
PROJECT_NAME=Cycling Workout API
```

### 3. Verify .env is Ignored
```bash
git status  # Should NOT show .env in changes
```

## Environment Variables by Purpose

| Variable | Purpose | Example |
|----------|---------|---------|
| `YOUTUBE_API_KEY` | YouTube Data API access | `AIzaSyD...` |
| `DATABASE_URL` | Database connection string | `sqlite:///./cycling_workouts.db` |
| `REDIS_URL` | Cache/session store | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:3000` |
| `API_V1_PREFIX` | API base path | `/api/v1` |
| `PROJECT_NAME` | Application name | `Cycling Workout API` |

## For CI/CD Deployment

Add these as GitHub Secrets (or equivalent in your CI platform):
- `YOUTUBE_API_KEY`
- `DATABASE_URL` (production)
- `REDIS_URL` (production)

Reference in workflows as: `${{ secrets.YOUTUBE_API_KEY }}`

## Database Connection Strings

### SQLite (Development)
```
sqlite:///./cycling_workouts.db
```

### PostgreSQL (Production)
```
postgresql://username:password@localhost:5432/cycling_workouts
```

## If You Accidentally Committed Secrets

**Immediately:**
1. Regenerate all API keys/credentials
2. Remove from git history:
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from tracking"
   git push
   ```
3. Run `git log` to verify it's gone
