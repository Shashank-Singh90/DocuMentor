import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    MODELS_DIR = DATA_DIR / "models"
    VECTORDB_DIR = DATA_DIR / "vectordb"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # LLM Configuration
    LLAMA_MODEL_PATH: str = os.getenv(
        "LLAMA_MODEL_PATH", 
        str(MODELS_DIR / "llama-2-7b-chat.Q4_K_M.gguf")
    )
    MODEL_N_CTX: int = int(os.getenv("MODEL_N_CTX", "4096"))
    MODEL_N_GPU_LAYERS: int = int(os.getenv("MODEL_N_GPU_LAYERS", "0"))
    
    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY", 
        str(VECTORDB_DIR)
    )
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "documenter")
    
    # Embedding Model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # Document Sources
    LANGCHAIN_DOCS_URL: str = os.getenv(
        "LANGCHAIN_DOCS_URL", 
        "https://python.langchain.com/docs/"
    )
    FASTAPI_DOCS_URL: str = os.getenv(
        "FASTAPI_DOCS_URL", 
        "https://fastapi.tiangolo.com/"
    )
    
    # API Keys (Optional)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Monitoring
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_MONITORING: bool = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    
    # Chunking settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Search settings
    DEFAULT_SEARCH_K: int = 5
    VECTOR_SEARCH_WEIGHT: float = 0.5
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_DIR,
            cls.MODELS_DIR,
            cls.VECTORDB_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.LOGS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Created project directories in {cls.PROJECT_ROOT}")

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.create_directories()