"""
Professional Configuration Management for RAG System
"""

from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application Info
    app_name: str = Field(default="RAG System", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")

    # Server Configuration
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8501, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Ollama Configuration
    ollama_host: str = Field(default="localhost:11434", description="Ollama server host")
    ollama_model: str = Field(default="gemma2:2b", description="Default Ollama model")
    ollama_timeout: int = Field(default=120, description="Ollama timeout in seconds")

    # Vector Database Configuration
    vectordb_path: str = Field(default="./data/vectordb", description="Vector database path")
    chroma_persist_directory: str = Field(default="./data/chroma_db", description="ChromaDB persist directory")
    collection_name: str = Field(default="documents", description="Collection name")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model")
    embedding_dimension: int = Field(default=384, description="Embedding dimension")

    # Chunking Configuration
    chunk_size: int = Field(default=1000, description="Default chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap")
    max_chunks_per_doc: int = Field(default=1000, description="Maximum chunks per document")

    # Caching Configuration
    cache_dir: str = Field(default="./data/cache", description="Cache directory")
    embedding_cache_dir: str = Field(default="./data/cache/embeddings", description="Embedding cache directory")
    max_cache_size: int = Field(default=1000, description="Maximum cache entries")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # Performance Configuration
    max_workers: int = Field(default=4, description="Maximum worker threads")
    batch_size: int = Field(default=100, description="Default batch size")
    timeout: int = Field(default=30, description="Default timeout")

    # File Upload Configuration
    upload_dir: str = Field(default="./data/uploads", description="Upload directory")
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Max file size in bytes")
    allowed_extensions: List[str] = Field(
        default=[".txt", ".md", ".pdf", ".docx", ".csv", ".doc", ".rtf", ".odt", ".pptx", ".xlsx"],
        description="Allowed file extensions"
    )

    # External API Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    firecrawl_api_key: Optional[str] = Field(default=None, description="Firecrawl API key")

    # LLM Provider Settings
    default_llm_provider: str = Field(default="ollama", description="Default LLM provider (ollama, openai, gemini)")
    enable_web_search: bool = Field(default=True, description="Enable web search functionality")
    enable_code_generation: bool = Field(default=True, description="Enable code generation features")

    # Pre-embedded Documents
    preembedded_docs_dir: str = Field(default="./data/preembedded", description="Pre-embedded documents directory")
    enable_source_filtering: bool = Field(default=True, description="Enable filtering by document source")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/rag_system.log", description="Log file path")
    log_max_size: int = Field(default=10 * 1024 * 1024, description="Max log file size")
    log_backup_count: int = Field(default=5, description="Log backup count")

    # Security Configuration
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def create_directories(self):
        """Create required directories"""
        directories = [
            Path(self.vectordb_path),
            Path(self.cache_dir),
            Path(self.embedding_cache_dir),
            Path(self.upload_dir),
            Path(self.log_file).parent,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings