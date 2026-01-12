# Darner

Darner is a full-stack job scouting app that surfaces the freshest IT roles (last 20 minutes through 25 hours), highlights H1B sponsorship signals, and estimates fit based on user-provided skills. No user data is stored; skills are used only for real-time scoring in each request.

## Architecture
- **Backend**: FastAPI + JobSpy integration (`backend/app`).
- **Frontend**: React (Vite) app (`frontend/`).
- **Deploy**: GitHub Actions for GitHub Pages (frontend) + Fly.io (backend).

## Local development
### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
uvicorn app.main:app --reload --app-dir backend
```

### Frontend
```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

## API endpoints
- `GET /health` - health check
- `GET /roles` - available roles and search terms
- `POST /jobs/search` - fetch recent jobs for a role

Example payload:
```json
{
  "role": "new_grad_swe",
  "location": "United States",
  "include_remote": true,
  "skills": ["React", "Python", "AWS"]
}
```

## Deployment (GitHub Actions)
### Frontend (GitHub Pages)
1. Set the repository to use GitHub Pages with **GitHub Actions** as the source.
2. Add `VITE_API_URL` as a repository secret pointing to your backend URL.

### Backend (Fly.io)
1. Create a Fly.io app (`flyctl launch`) and note the app name.
2. Add these repository secrets:
   - `FLY_API_TOKEN` - Fly API token
   - `FLY_APP_NAME` - Fly app name
3. Set Fly app environment variables:
   - `ALLOWED_ORIGINS` - comma-separated list of allowed frontend URLs
   - `DEFAULT_LOCATION` - optional default search location

The workflows live in `.github/workflows/` and deploy on pushes to `main`.
