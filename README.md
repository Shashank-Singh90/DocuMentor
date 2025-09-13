# 🧠 DocuMentor - AI-Powered Documentation Assistant

An intelligent documentation assistant powered by Gemma 3 (4B) that helps developers instantly find answers from multiple documentation sources.

## ✨ Features

- 🤖 **Gemma 3 Integration** - Powerful 4B parameter model for intelligent responses
- 📚 **9+ Documentation Sources** - LangChain, FastAPI, React, Django, Node.js, and more
- 🚀 **Fast Vector Search** - ChromaDB for instant documentation retrieval
- 💬 **Streaming Responses** - Real-time AI responses with source citations
- 📤 **Document Upload** - Add your own documentation (PDF, MD, TXT)
- 🎨 **Modern UI** - Beautiful interface built with React (coming soon)

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **AI Model**: Gemma 3 (via Ollama)
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers
- **Frontend**: React (in development)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Ollama installed
- 8GB+ free disk space
- 8GB+ RAM recommended

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Shashank-Singh90/DocuMentor.git
cd DocuMentor
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Pull Gemma 3 model:
```bash
ollama pull gemma3:4b
```

5. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

6. Start the API server:
```bash
python api_server.py
```

7. Visit API docs: http://localhost:8000/docs

## 📖 API Endpoints

- `POST /ask` - Ask a question and get AI response
- `POST /search` - Search documentation
- `POST /upload` - Upload custom documentation
- `GET /sources` - List available sources
- `GET /stats` - Get system statistics

## 🎯 Roadmap

- [x] Gemma 3 integration
- [x] FastAPI backend
- [x] Vector search implementation
- [x] Document upload
- [ ] Modern React UI
- [ ] Authentication system
- [ ] Chat history
- [ ] Export functionality
- [ ] Cloud deployment

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google for Gemma 3
- Ollama team for local LLM support
- All documentation providers

---

**Note**: This project works best with at least 8GB RAM for optimal performance with the Gemma 3 4B model.
