# 🌐 Deployment Guide — Free Cloud Hosting

Deploy your PDF Chatbot online for free using **Render** (backend) + **Vercel** (frontend).

---

## Backend → Render (Free)

Render gives you a free Python web service. The free tier sleeps after 15 minutes of inactivity — wake it by hitting the URL.

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/pdf-chatbot.git
git push -u origin main
```

### Step 2 — Create Render Service

1. Go to https://render.com → Sign up (free)
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3 — Add Environment Variables

In Render dashboard → Environment:
```
GROQ_API_KEY       = gsk_xxxx...
LLM_PROVIDER       = groq
GROQ_MODEL         = llama3-8b-8192
EMBEDDING_MODEL    = sentence-transformers/all-MiniLM-L6-v2
CHROMA_PERSIST_DIR = ./chroma_db
UPLOAD_DIR         = ./uploads
```

> ⚠️ Note: Render free tier has ephemeral storage — uploaded files reset on restart.
> For persistent storage, add a Render Disk ($7/month) or use Cloudflare R2 (free 10GB).

---

## Frontend → Vercel (Free)

### Step 1 — Update API URL

Edit `frontend/src/utils/api.js` — change the BASE URL to point to your Render backend:

```js
// Change this line:
const BASE = '/api'

// To your Render URL:
const BASE = 'https://your-app-name.onrender.com/api'
```

Also update `vite.config.js` — the proxy is only for local dev, Vercel doesn't need it.

### Step 2 — Deploy to Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Follow prompts:
# - Framework: Vite
# - Root: frontend/
# - Build: npm run build
# - Output: dist
```

Or connect via vercel.com → Import Git Repository → select your repo → set **Root Directory** to `frontend`.

### Step 3 — Add Environment Variable

In Vercel dashboard → Settings → Environment Variables:
```
VITE_API_URL = https://your-app-name.onrender.com
```

Then update `api.js` to use:
```js
const BASE = (import.meta.env.VITE_API_URL || '') + '/api'
```

---

## Alternative: Run Locally with Public URL (Ngrok)

For demo day without deploying:

```bash
# Install ngrok from https://ngrok.com (free)
ngrok http 8000

# Copy the https URL e.g. https://abc123.ngrok.io
# Update frontend/src/utils/api.js:
const BASE = 'https://abc123.ngrok.io/api'
```

This gives you a public URL for your locally running backend — great for demos.

---

## Docker (Optional — for consistent deployment)

A `Dockerfile` for the backend:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads chroma_db
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t pdf-chatbot-backend ./backend
docker run -p 8000:8000 --env-file backend/.env pdf-chatbot-backend
```
