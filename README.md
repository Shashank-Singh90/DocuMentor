# Docu - LangChain & Ollama Integration

A local document Q&A application powered by LangChain and Ollama, featuring a modern Streamlit web interface. This project demonstrates how to build a complete RAG (Retrieval Augmented Generation) system that runs entirely on your local machine for maximum privacy and control.

## Features

- **Local LLM Integration**: Uses Ollama with Gemma2:2b model for completely offline operation
- **Document Processing**: Support for PDF and text files with intelligent chunking
- **Vector Search**: ChromaDB integration with nomic-embed-text embeddings for semantic search
- **RAG Pipeline**: Complete retrieval-augmented generation for accurate document-based answers
- **Web Interface**: Professional Streamlit UI with both simple chat and document Q&A modes
- **Privacy First**: All processing happens locally - no data leaves your machine
- **Flexible Architecture**: Modular design for easy extension and customization

## Requirements

### System Requirements
- Python 3.11+
- 8GB+ RAM recommended
- NVIDIA GPU (optional, CPU-only mode available)
- Windows 10/11 (tested), Linux/macOS (should work)

### Software Dependencies
- [Ollama](https://ollama.com/) - Local LLM runtime
- Python packages (see requirements.txt)

## Installation

### 1. Install Ollama

Download and install Ollama from [https://ollama.com/](https://ollama.com/)

### 2. Download Required Models

```bash
# Download the language model
ollama pull gemma2:2b

# Download the embedding model
ollama pull nomic-embed-text
```

### 3. Clone and Setup Project

```bash
git clone <repository-url>
cd Docu

# Create virtual environment
python -m venv langchain_env

# Activate virtual environment (Windows)
.\langchain_env\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

Create a `.env` file in the project root:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:2b
CHROMA_DB_PATH=./data/chroma_db
```

## Usage

### Starting the Application

1. **Start Ollama Server** (in a separate terminal):
   ```bash
   ollama serve
   ```

2. **Launch Streamlit App**:
   ```bash
   # Activate virtual environment first
   .\langchain_env\Scripts\Activate.ps1
   
   # Start the web application
   streamlit run streamlit_app.py
   ```

3. **Access the Application**:
   Open your browser to `http://localhost:8501`

### Using the Interface

#### Initial Setup
1. Click **"Initialize System"** in the sidebar
2. Wait for successful initialization message
3. Optionally test connection with **"Test Connection"** button

#### Simple Chat Mode
- Direct conversation with your local Gemma2:2b model
- No document context, pure LLM responses
- Useful for general questions and testing

#### Document Q&A Mode
1. **Upload Documents**: Drag and drop PDF or text files
2. **Process Documents**: Click "Process Documents" to create embeddings
3. **Ask Questions**: Query your documents with natural language
4. **View Sources**: See which document chunks were used for answers

#### Using Test Documents
- Click **"Use Test Docs"** to load pre-created example documents
- Test with questions like:
  - "What is LangChain used for?"
  - "How do you combine LangChain with Ollama?"
  - "What are the features of the Docu project?"

## Project Structure

```
Docu/
├── src/
│   ├── llm_handler.py          # Ollama LLM integration
│   └── document_processor.py   # Document loading & vector processing
├── data/
│   ├── documents/             # Default document storage
│   └── chroma_db/            # Vector database storage
├── streamlit_app.py          # Main web application
├── main.py                   # Command-line version
├── requirements.txt          # Python dependencies
├── .env                     # Environment configuration
└── README.md               # This file
```

## Architecture

### Core Components

1. **LLM Handler** (`src/llm_handler.py`)
   - Manages Ollama connection and model interactions
   - Handles response generation and error management
   - Configurable model parameters

2. **Document Processor** (`src/document_processor.py`)
   - Loads PDF and text documents
   - Chunks documents for optimal processing
   - Creates and manages vector embeddings
   - Handles similarity search

3. **Streamlit Interface** (`streamlit_app.py`)
   - Professional web UI
   - Session state management
   - Real-time chat interface
   - Document upload and processing

### Data Flow

```
Documents → Text Extraction → Chunking → Embeddings → Vector Store
                                                          ↓
User Query → Embedding → Similarity Search → Context → LLM → Response
```

## Troubleshooting

### Common Issues

#### Connection Errors
- **Error**: `[WinError 10061] No connection could be made`
- **Solution**: Ensure Ollama is running with `ollama serve`
- **Check**: Verify correct port in `.env` file

#### CUDA Out of Memory
- **Error**: `CUDA error: out of memory`
- **Solution**: Force CPU-only mode:
  ```bash
  $env:CUDA_VISIBLE_DEVICES=""
  ollama serve
  ```

#### Environment Variables Not Loading
- **Error**: Configuration not recognized
- **Solution**: Ensure `python-dotenv` is installed:
  ```bash
  pip install python-dotenv
  ```

#### Port Conflicts
- **Error**: `bind: Only one usage of each socket address`
- **Solution**: Use different port:
  ```bash
  $env:OLLAMA_HOST="127.0.0.1:11435"
  ollama serve
  ```

### Performance Optimization

#### For Low-Memory Systems
- Use CPU-only mode
- Reduce context window: `$env:OLLAMA_CONTEXT_LENGTH="1024"`
- Process smaller document batches

#### For Better Performance
- Use GPU acceleration (if sufficient VRAM)
- Increase chunk overlap for better retrieval
- Use larger embedding models if available

## Technical Details

### Models Used
- **Language Model**: Gemma2:2b (Google's efficient 2B parameter model)
- **Embedding Model**: nomic-embed-text (Optimized for retrieval tasks)
- **Vector Database**: ChromaDB (Persistent local storage)

### Key Libraries
- **LangChain**: Framework for LLM applications
- **Streamlit**: Web interface framework
- **ChromaDB**: Vector database for embeddings
- **PyPDF**: PDF document processing
- **Ollama**: Local LLM runtime

## Development

### Adding New Document Types
1. Update `document_processor.py` with new loaders
2. Add file type to Streamlit upload filter
3. Test processing pipeline

### Customizing Models
1. Download new model: `ollama pull <model-name>`
2. Update `.env` file with new model name
3. Adjust parameters in `llm_handler.py` if needed

### Extending Functionality
- Add conversation memory
- Implement document summarization
- Add multi-language support
- Create custom prompt templates

## Future Enhancements

- [ ] Conversation memory and context persistence
- [ ] Support for more document formats (DOCX, HTML, etc.)
- [ ] Advanced retrieval strategies
- [ ] Document preview and management
- [ ] User authentication and multi-user support
- [ ] API endpoint for programmatic access
- [ ] Docker containerization
- [ ] Cloud deployment options

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.com/) for local LLM runtime
- [LangChain](https://python.langchain.com/) for LLM application framework
- [Streamlit](https://streamlit.io/) for the web interface framework
- [ChromaDB](https://www.trychroma.com/) for vector database capabilities

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Ollama documentation
3. Check LangChain community resources
4. Open an issue in this repository

---

**Built with privacy in mind - your documents never leave your machine.**






