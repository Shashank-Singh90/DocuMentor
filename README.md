# DocuMentor

DocuMentor is a RAG (Retrieval-Augmented Generation) system designed to help developers standardise and query their documentation. It indexes documentation files and provides an interface to ask questions, returning answers with context from the indexed documents.

## Features

- **RAG Architecture**: Uses vector search to find relevant documentation chunks.
- **Multiple LLM Support**: Works with Ollama, OpenAI, and Gemini.
- **Web Search**: Fallback to web search for up-to-date information.
- **API & UI**: Includes a FastAPI backend and a Streamlit frontend.

## Setup

1.  **Environment Variables**:
    Copy `.env.example` to `.env` and configure your keys.

    ```bash
    cp .env.example .env
    ```

2.  **Installation**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run API**:

    ```bash
    python -m rag_system.api.server
    ```

4.  **Run Web UI**:
    ```bash
    streamlit run rag_system/web/app.py
    ```

## Architecture

- **Core**: Contains the logic for chunking (`DocumentChunker`), retrieval (`VectorStore`), and generation (`LLMService`).
- **API**: FastAPI server handling requests.
- **Web**: Streamlit interface for easy interaction.

## Tech Stack

- Python 3.13+
- FastAPI
- Streamlit
- ChromaDB
- LangChain
