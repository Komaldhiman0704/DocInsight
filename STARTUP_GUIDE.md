# 🚀 PDF Chatbot - Startup Scripts Summary

## ✅ What Was Created

I've created a complete **one-click startup system** for your PDF chatbot project!

---

### 📑 Files Created/Updated

| File | Purpose | Status |
|------|---------|--------|
| **start.bat** | Launch both backend & frontend servers | ✅ Ready |
| **stop.bat** | Stop all servers gracefully | ✅ Ready |
| **setup-init.bat** | First-time setup (Python venv, npm install) | ✅ Ready |
| **QUICK_START.md** | User guide with troubleshooting | ✅ Ready |

---

## 🎯 Quick Start (3 Simple Steps)

### Step 1: Get API Key
Go to: https://console.groq.com/keys
- Click "Create API Key"
- Copy your key (starts with `gsk_`)

### Step 2: Set API Key
1. Open folder `backend`
2. Find file `.env`
3. Paste your key:
   ```
   GROQ_API_KEY=gsk_your_actual_key
   ```
4. Save

### Step 3: Run start.bat
**Double-click:** `start.bat` in the main pdf-chatbot folder
✨ Everything starts automatically!

---

## 📜 What Each Script Does

### `start.bat` (Main Script)
```
✓ Checks that venv and node_modules exist
✓ Validates GROQ_API_KEY is set
✓ Starts Backend on port 8000
✓ Starts Frontend on port 5173  
✓ Opens app in browser automatically
✓ Shows helpful instructions
```

**Usage:** Double-click or run:
```bash
start.bat
```

### `stop.bat` (Cleanup Script)
```
✓ Gracefully stops both servers
✓ Or force-kills them if needed
✓ Clears port resources
```

**Usage:** Double-click when done:
```bash
stop.bat
```

### `setup-init.bat` (First-Time Setup)
```
✓ Checks Python & Node.js are installed
✓ Creates Python virtual environment
✓ Installs all Python packages
✓ Runs npm install for frontend
✓ Shows next steps
```

**Usage:** Run only once if getting errors:
```bash
setup-init.bat
```

---

## 🔥 Running the Project

### Normal Startup (Every Time)
```
1. Double-click: start.bat
2. Wait 5-10 seconds
3. Browser opens at http://localhost:5173
4. Upload a PDF and chat!
```

### Stopping
```
Close both terminal windows
OR double-click: stop.bat
```

### Restarting
```
Just run start.bat again
(Both servers will restart cleanly)
```

---

## 🎨 Project Structure After Setup

```
pdf-chatbot/
├── start.bat              ← Main startup script
├── stop.bat               ← Stop all servers
├── setup-init.bat         ← Initial setup
├── QUICK_START.md         ← User guide
├── README.md
│
├── backend/
│   ├── .env               ← YOUR API KEY GOES HERE!
│   ├── venv/              ← Python environment (auto-created)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   ├── services/
│   └── uploads/           ← Uploaded PDFs stored here
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── node_modules/      ← Dependencies (auto-created)
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   ├── utils/
    │   └── styles/
    └── ...
```

---

## 🌐 URLs After Starting

| Service | URL | What It Does |
|---------|-----|--------------|
| **App UI** | http://localhost:5173 | Upload PDFs, ask questions |
| **API Docs** | http://localhost:8000/docs | Interactive API explorer |
| **Health** | http://localhost:8000/health | Check system status |

---

## ⚙️ System Status (start.bat Shows This)

```
🌐 App URL:        http://localhost:5173
📚 API Docs:       http://localhost:8000/docs
💚 Health Check:   http://localhost:8000/health

⚙️  Settings:
   - Max file size: 100MB per PDF
   - LLM model:    llama-3.3-70b-versatile (latest)
   - Vector DB:    ChromaDB (local, no setup required)
```

---

## 🆘 Troubleshooting

### Issue: "Virtual environment not found"
**Solution:** Run `setup-init.bat` first

### Issue: "Node modules not found"  
**Solution:** Run `setup-init.bat` first

### Issue: "GROQ_API_KEY is empty"
**Solution:** 
1. Open `backend\.env`
2. Get key from https://console.groq.com/keys
3. Set: `GROQ_API_KEY=gsk_your_key`
4. Save and restart

### Issue: "Port 8000 already in use"
**Solution:** Kill the process:
```bash
netstat -ano | findstr :8000
taskkill /PID <pid_number> /F
```

### Issue: "Browser doesn't open"
**Solution:** Manually go to http://localhost:5173

---

## 📚 Features Summary

✅ **One-click startup** - Double-click start.bat  
✅ **Auto-detection** - Checks for dependencies  
✅ **Error handling** - Shows what's missing  
✅ **Auto browser** - Opens app in default browser  
✅ **Graceful shutdown** - stop.bat script  
✅ **Professional UI** - Green color scheme, clear messages  
✅ **Full documentation** - Inline help text  

---

## 💡 For Developers

### To customize ports:
Edit `backend/.env`:
```ini
# You can change these (but also update frontend config)
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

### To use different LLM model:
Edit `backend/.env`:
```ini
# Instead of llama-3.3-70b-versatile:
GROQ_MODEL=llama-3.1-8b-instant  # Faster
GROQ_MODEL=openai/gpt-oss-120b   # Different provider
```

### To increase file size limit:
Edit `backend/.env`:
```ini
MAX_FILE_SIZE_MB=150  # From default 100MB
```

---

## 🎓 Next Steps

1. **Get API Key** → https://console.groq.com/keys
2. **Set in .env** → `backend/.env`
3. **Run start.bat** → Double-click!
4. **Upload PDF** → Drag & drop any document
5. **Ask Questions** → Chat with your PDFs!

---

## 📞 Support

- **Groq API Issues:** https://console.groq.com/docs
- **FastAPI Help:** https://fastapi.tiangolo.com
- **React Questions:** https://react.dev
- **Node Issues:** https://stackoverflow.com/questions/tagged/node.js

---

**Your PDF Chatbot is ready! Just click start.bat and enjoy! 🚀**
