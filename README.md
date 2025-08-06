# 🧠 DocuMentor - AI-Powered Documentation Assistant

An intelligent documentation assistant powered by Llama 4 (67GB) that helps developers instantly find answers from multiple documentation sources.

## ✨ Features

- 🤖 **Llama 4 Integration** - Latest 67GB multimodal model for superior responses
- 📚 **9+ Documentation Sources** - LangChain, FastAPI, React, Django, Node.js, and more
- 🚀 **Fast Vector Search** - ChromaDB for instant documentation retrieval
- 💬 **Streaming Responses** - Real-time AI responses with source citations
- 📤 **Document Upload** - Add your own documentation (PDF, MD, TXT)
- 🎨 **Modern UI** - Beautiful interface built with React (coming soon)

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **AI Model**: Llama 4 (via Ollama)
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers
- **Frontend**: React (in development)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Ollama installed
- 70GB+ free disk space
- 16GB+ RAM recommended

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DocuMentor.git
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

4. Pull Llama 4 model:
```bash
ollama pull llama4:16x17b
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

- [x] Llama 4 integration
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

- Meta for Llama 4
- Ollama team for local LLM support
- All documentation providers

---

**Note**: This project requires significant computational resources due to the 67GB Llama 4 model.