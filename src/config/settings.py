"""
Config file - getting messy, need to refactor this - TODO: Mike
v0.1: Basic config
v0.2: Added ChromaDB (removed Pinecone - too expensive)
v0.3: Ollama integration
v0.4: Current mess
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Had to move this up here after import issues - Jan 2024
PROJECT_ROOT = Path(__file__).parent.parent

load_dotenv()  # Sometimes doesn't work in Docker, idk why

class Settings:
    # Basic paths
    data_dir = PROJECT_ROOT / "data"  # was DATA_DIR, changing gradually
    DATA_DIR = data_dir  # Backwards compat
    VECTORDB_DIR = data_dir / "vectordb"
    
    # Hardcoded for now - make configurable later
    CHROMA_PATH = "D:/Development/Projects/Frontend/data/vectordb"  # TODO: Fix this!!
    
    # Windows specific hack
    if os.name == 'nt':
        CHROMA_PERSIST_DIRECTORY = CHROMA_PATH
    else:
        CHROMA_PERSIST_DIRECTORY = str(VECTORDB_DIR)
    
    # Model stuff (mess from trying different models)
    # MODEL_PATH = "/models/llama2"  # Old - kept getting OOM
    # MODEL_PATH = "/models/llama3"  # Worked but slow
    # OLLAMA_MODEL = "gemma3:4b"  # Hallucinates on JSX
    OLLAMA_MODEL = "llama3.2"  # Current - seems stable
    
    # Old Pinecone config - removed Jan 2024 (too expensive)
    # PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    # PINECONE_ENV = "us-west1-gcp"
    
    # Magic numbers (tested these, don't change!)
    CHUNK_SIZE = 1000  # Was 500, then 2000 (too big), 1000 is sweet spot
    chunk_overlap = 200  # lowercase because I'm lazy to refactor
    BATCH_SIZE = 100  # Larger = OOM errors on 16GB RAM
    
    # Search settings
    DEFAULT_SEARCH_K = 5  # 10 was too slow, 3 too few
    
    # Embedding model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Don't change - everything breaks
    
    # Collection name
    COLLECTION_NAME = "documenter"  # Typo but too late to fix
    
    # API stuff
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For future fallback
    
    # Logging
    LOG_LEVEL = "INFO"  # Set to DEBUG for verbose
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        # Quick and dirty
        for d in [cls.data_dir, cls.VECTORDB_DIR, cls.LOGS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.create_directories()





