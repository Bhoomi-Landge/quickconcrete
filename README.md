# QuickConcrete

MVP for on-demand Ready-Mix Concrete (RMC) delivery — contractors browse supplier plants/rates and place orders; suppliers manage plants, grades, and order status.

## Live hosting (Render — free)

**Render free tier:** $0, public HTTPS URL. The service **sleeps after ~15 minutes idle**; the first open after sleep can take **30–60 seconds**.

1. Push this repo to GitHub.
2. Go to [https://dashboard.render.com/select-repo?type=blueprint](https://dashboard.render.com/select-repo?type=blueprint) (sign up with GitHub).
3. Select this repository — it reads `render.yaml` + `Dockerfile`.
4. Deploy. Your URL will look like: `https://quickconcrete.onrender.com`

**Railway:** also has a small free credit (~$1–5 trial). Same Docker image works (`railway.toml`). Prefer Render for a no-card free demo.

Default admin after deploy: `admin@quickconcrete.local` / `admin123` (change via env vars).

## Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-CORS, SQLite
- **Frontend:** React, Vite, React Router

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # optional
python app.py
```

API runs at `http://127.0.0.1:5000`.

On first start, tables are created and a demo admin user is seeded:

- Email: `admin@quickconcrete.local`
- Password: `admin123`

Override with `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `backend/.env`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`. Vite proxies `/api` to the Flask server.

## Phase 1 features

- Contractor and supplier registration
- Login / logout (Flask session cookies, hashed passwords)
- Admin login (seeded account only)
- Role-based routes: `/contractor`, `/supplier`, `/admin`

## Project layout

```
quickconcrete/
  backend/          Flask API
  frontend/         React UI
  README.md
```
