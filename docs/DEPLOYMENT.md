# ROADGUARD AI — Enterprise Deployment Guide

This guide covers production deployment of ROADGUARD AI on persistent cloud infrastructure.

## Local Development (Windows)

### Prerequisites
- Python 3.10+ (Tested on Python 3.12.10)
- Node.js 18+ (Tested on Node.js v22.23.1)

### 1. Backend Setup
```powershell
cd roadguard-ai\backend
python -m pip install -r requirements.txt
python seed_data.py   # Seeds sample road inspections
python run_backend.py # Starts FastAPI on http://127.0.0.1:8000
```

### 2. Frontend Setup
```powershell
cd roadguard-ai\frontend
npm install
npm run dev           # Starts Vite on http://127.0.0.1:5173
```

---

## Production Cloud Deployment

### Architecture Requirements
1. **Frontend**: Static Web Hosting (Vercel, Netlify, Cloudflare Pages, AWS S3 + CloudFront).
2. **Backend**: Container or Python hosting (Render, Railway, Fly.io, AWS ECS, Google Cloud Run).
3. **Database**: Managed PostgreSQL (Supabase, Neon, AWS RDS, Render Postgres).
4. **Persistent Image Storage**: AWS S3, Cloudflare R2, Google Cloud Storage, or persistent Docker volume.

### Connecting PostgreSQL
1. Set the environment variable in your backend container/service:
   ```env
   DATABASE_URL=postgresql+psycopg2://<user>:<password>@<db-host>:5432/<dbname>
   ```
2. Install psycopg2 in your production environment:
   ```bash
   pip install psycopg2-binary
   ```
3. SQLAlchemy automatically provisions tables upon startup.

### Persistent Storage for Uploads and Annotations
In containerized environments (e.g. Render / Docker / Kubernetes), local disk storage is ephemeral.
- Mount a persistent volume at `/app/storage` or:
- Configure an S3 adapter in `app/services/image_service.py` to stream uploaded and annotated buffers directly to AWS S3 / Cloudflare R2 buckets.

### Frontend Production Build
```bash
cd frontend
npm run build
```
Upload the generated `frontend/dist/` directory to Vercel, Netlify, or your CDN.
Set `VITE_API_URL` to your production backend domain.
