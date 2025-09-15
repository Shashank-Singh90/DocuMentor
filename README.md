# 🧠 DocuMentor - AI-Powered Documentation Assistant

An intelligent documentation assistant that uses Gemma 3 (or llama3.2 if you can't get Gemma working) to help developers find answers from documentation. Still a work in progress but mostly functional.

## ✨ Features

- 🤖 **Gemma 3/Llama Integration** - Uses 4B parameter model (warning: needs tons of RAM)
- 📚 **9+ Documentation Sources** - LangChain, FastAPI, React, Django, Node.js, etc (some might be outdated)
- 🚀 **Vector Search** - ChromaDB for documentation retrieval (sometimes slow on first query)
- 💬 **Streaming Responses** - Real-time AI responses (when it works - see troubleshooting)
- 📤 **Document Upload** - Add your own docs (PDF support is flaky, stick to MD/TXT)
- 🎨 **Modern UI** - React interface (TODO - using API directly for now)

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **AI Model**: Gemma 3 (via Ollama)
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers
- **Frontend**: React (in development)

## 🚀 Quick Start

**Note**: Tested on Windows 11 and Ubuntu 22.04. Mac users see issue #23 (M1 chips have memory issues).

### Prerequisites
- Python 3.9+ (3.12 has issues with ChromaDB, stick to 3.11)
- Ollama installed and running (check with `ollama list`)
- ~70GB free space (yeah, it's huge with all the models and embeddings)
- 16GB RAM minimum (32GB recommended - trust me, it'll swap like crazy otherwise)

### Installation

```bash
git clone https://github.com/Shashank-Singh90/DocuMentor.git
cd DocuMentor

# Windows users: Use venv, conda has weird issues with sentence-transformers
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install deps (this takes forever first time, go grab coffee)
pip install -r requirements.txt

# IMPORTANT: Pull model BEFORE running (gemma3 might fail, use llama as backup)
ollama pull gemma3:4b
# If above fails, try: ollama pull llama3.2:3b
# or even: ollama pull mistral:7b (needs more RAM though)
```

### Configuration

Create `.env` file (copy from .env.example if it exists, otherwise create manually):

```bash
# .env
MODEL_NAME=gemma3:4b  # or llama3.2:3b if gemma doesn't work
CHROMA_PATH=./chroma_db  # don't change unless you know what you're doing
EMBEDDING_MODEL=all-MiniLM-L6-v2  # this one actually works well
PORT=8000
HOST=0.0.0.0  # change to 127.0.0.1 if you don't want network access
```

### Running the Server

```bash
# Make sure Ollama is running first!
ollama serve  # in another terminal

# Then start the API
python api_server.py

# If you get "model not found", double-check:
# 1. Ollama is running (check http://localhost:11434)
# 2. Model is pulled (ollama list)
# 3. Model name in .env matches exactly
```

API should be available at: http://localhost:8000/docs

**Common Issues**:
- Port 8000 already in use? Change it in .env
- Getting timeout errors? Increase `TIMEOUT=120` in .env
- ChromaDB sqlite errors? Delete `chroma_db` folder and restart

## 📖 API Endpoints

### Working Endpoints:
- `POST /ask` - Ask a question and get AI response (might timeout on first request)
- `POST /search` - Search documentation (fast once warmed up)
- `GET /sources` - List available sources

### Partially Working:
- `POST /upload` - Upload custom docs (PDFs are broken, use MD/TXT for now)
- `GET /stats` - System stats (sometimes returns null for memory)

## 🎯 Roadmap / TODO

- [x] ~~Gemma 3 integration~~ (works but llama3.2 is more stable)
- [x] FastAPI backend (mostly done)
- [x] Vector search (works but needs optimization)
- [x] Document upload (text files only really work well)
- [ ] Fix PDF upload parsing
- [ ] Modern React UI (started but not committed yet)
- [ ] Authentication (do we really need this?)
- [ ] Chat history (sqlite integration started)
- [ ] Export functionality
- [ ] Cloud deployment (too expensive for hobby project)
- [ ] Better error handling (currently just crashes)
- [ ] Proper logging instead of print statements

## 🔧 Troubleshooting

### Model keeps failing/crashing?
```bash
# Try smaller model
ollama pull llama3.2:3b
# Update .env to use it
```

### ChromaDB errors?
```bash
# Nuclear option - delete and rebuild
rm -rf chroma_db/  # or delete folder manually on Windows
python build_vectordb.py  # if this script exists
```

### Windows specific issues:
- If you get DLL errors, install Visual C++ Redistributable
- Defender might flag Ollama, add exception
- Use PowerShell as Admin if permission errors

### Linux issues:
- May need to install `libgomp1` for sentence-transformers
- Ubuntu 20.04 users: upgrade Python, default 3.8 won't work

## 🤝 Contributing

Feel free to submit PRs! The code is a bit messy in places (especially the vector search logic). Main branch might be broken sometimes - check the `stable` branch if you need something that definitely works.

### Known Issues / Help Wanted:
- PDF parsing is completely broken (pypdf issues)
- Memory leak somewhere in the streaming response handler
- Need better error messages (currently just 500 errors)
- Tests? What tests? (PRs welcome for adding tests)

## 📄 License

MIT License (see LICENSE file)

## 🙏 Credits

- Google for Gemma (when it works)
- Ollama team for making local LLMs actually usable
- LangChain/FastAPI/React communities for docs
- StackOverflow for fixing all my bugs
- Coffee for keeping me awake

---

**Last Updated**: Working as of Dec 2024 (mostly)

**PS**: If you get it working on Mac M1/M2, please let me know how! The memory management is weird on Apple Silicon.

**PPS**: Star the repo if it helped you! Need those GitHub stats for my resume 😅





