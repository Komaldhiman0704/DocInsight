# ⚡ Quick Start Guide - PDF Chatbot

## 🚀 Fastest Way to Start

**Double-click:** `start.bat`

That's it! This will:
- ✅ Start the backend server (Port 8000)
- ✅ Start the frontend server (Port 5173)  
- ✅ Open the app in your browser
- ✅ Show you all the URLs and settings

## 📋 What You Need BEFORE Starting

### 1️⃣ Groq API Key (Free)
Get a free key at: https://console.groq.com/keys
- Click "Create API Key"
- Copy the key (starts with `gsk_`)

### 2️⃣ Set Your API Key
1. Open the folder `backend`
2. Find the file `.env`
3. Paste your key here:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
4. Save the file

### 3️⃣ Run start.bat
Double-click `start.bat` in this folder

---

## 📂 File Structure

```
pdf-chatbot/
├── start.bat           ← CLICK THIS to start everything! 
├── stop.bat            ← Click to stop servers
├── backend/            
│   ├── .env            ← PUT YOUR API KEY HERE
│   ├── main.py
│   ├── venv/           ← Python virtual environment
│   └── requirements.txt
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
```

---

## 🎯 First Time Setup (If Needed)

If `start.bat` gives an error, you may need to initialize:

### Option A: Use setup.bat (if available)
```
Double-click setup.bat
```

### Option B: Manual Setup

**For Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**For Frontend:**
```bash
cd frontend
npm install
```

Then run `start.bat`

---

## 🌐 URLs After Starting

| Service | URL | Purpose |
|---------|-----|---------|
| **App** | http://localhost:5173 | Upload PDFs, ask questions |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | System status |

---

## 💡 How to Use the App

1. **Upload PDF**
   - Drag & drop a PDF file onto the upload zone
   - Or click "browse" to select a file
   - Max size: 100MB per file

2. **Wait for Processing**
   - First upload takes 30-60 seconds (downloads embedding model)
   - Future uploads are faster
   - Green "Ready!" notification when done

3. **Ask Questions**
   - Type any question in the chat box
   - Examples:
     - "What is this document about?"
     - "Summarize the key points"
     - "What does page 3 say about...?"

4. **See Sources**
   - Click "sources found" to see which pages answered your question
   - Great for verifying facts!

---

## 🛑 How to Stop

### Easy Way:
Close both terminal windows

### Or use stop.bat:
Double-click `stop.bat` in this folder

---

## ⚙️ Settings You Can Change

Edit `backend/.env` to customize:

```ini
# Change LLM Model (if you want faster responses)
GROQ_MODEL=llama-3.1-8b-instant  # Faster
GROQ_MODEL=llama-3.3-70b-versatile  # Better quality (default)

# Change max file size (in MB)
MAX_FILE_SIZE_MB=100

# Change chunk size for PDF processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# How many sources to return
TOP_K_RESULTS=4
```

Then restart `start.bat`

---

## 🆘 Troubleshooting

### "Backend failed to start"
→ Check that your `GROQ_API_KEY` is set in `backend/.env`

### "Frontend shows blank screen"
→ Refresh the page (Ctrl+R or Cmd+R)

### "Upload fails"
→ Make sure the PDF file is valid and not corrupted

### "Chat returns an error"
→ Get a Groq API key at https://console.groq.com/keys

### "Port 8000 or 5173 already in use"
→ Close other applications using those ports
→ Or edit .env to use different ports

---

## 📚 More Information

- **Groq API Docs:** https://console.groq.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **React Docs:** https://react.dev
- **LangChain Docs:** https://python.langchain.com

---

## 🎓 Learning the Project

To understand how it works:

1. **Backend Pipeline:**
   - `backend/main.py` - FastAPI server
   - `backend/services/rag_chain.py` - AI question answering
   - `backend/services/vector_store.py` - PDF storage
   - `backend/routers/upload.py` - File handling

2. **Frontend:**
   - `frontend/src/App.jsx` - Main React component
   - `frontend/src/components/UploadZone.jsx` - File upload UI
   - `frontend/src/utils/api.js` - API calls

---

**Happy PDF Chatting! 🚀**
