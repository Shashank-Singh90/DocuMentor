# Create updated settings.py
@"
# GOOD (replace with):
CHROMA_DB_PATH = "./data/chroma_db"
COLLECTION_NAME = "documents"
CHROMA_PERSIST_DIRECTORY = "./data/chroma_db"
#!/usr/bin/env python3
"""
Professional Settings Management for DocuMentor
Python 3.11 Compatible Version
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_title: str = Field(default="DocuMentor API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(default="AI-powered documentation assistant", description="API description")
    
    # Server Configuration
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Ollama Configuration
    ollama_host: str = Field(default="localhost:11434", description="Ollama server host")
    ollama_model: str = Field(default="gemma3:4b", description="Default Ollama model")
    ollama_timeout: int = Field(default=120, description="Ollama timeout in seconds")
    
    # Vector Database Configuration
    chroma_persist_directory: str = Field(default="./data/vectordb", description="ChromaDB persistence directory")
    collection_name: str = Field(default="documenter", description="ChromaDB collection name")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    embedding_dimension: int = Field(default=384, description="Embedding dimension")
    
    # Generation Settings
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    
    # File Upload Settings
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Maximum file size in bytes")
    allowed_extensions: List[str] = Field(default=[".pdf", ".txt", ".md", ".docx"], description="Allowed file extensions")
    upload_directory: str = Field(default="./data/uploads", description="Upload directory")
    
    # Security Settings
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Monitoring
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    log_file: str = Field(default="./logs/app.log", description="Log file path")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

def create_directories(settings_instance: Settings):
    """Create required directories if they don't exist"""
    directories = [
        Path(settings_instance.chroma_persist_directory),
        Path(settings_instance.upload_directory),
        Path(settings_instance.log_file).parent,
        Path("./data/scraped"),
        Path("./data/processed")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

if __name__ == "__main__":
    create_directories(settings)
    print("Settings loaded and directories created")
"@ | Out-File -FilePath "src/config/settings.py" -Encoding utf8
