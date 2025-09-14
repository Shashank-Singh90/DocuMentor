# Config file - getting messy, need to refactor this - TODO: Mike
import os
from pathlib import Path

# Had to move this up here after import issues - Jan 2024
PROJECT_ROOT = Path(__file__).parent.parent

class Settings:
    # Basic paths
    data_dir = PROJECT_ROOT / "data"  # was DATA_DIR, changing gradually
    VECTORDB_DIR = data_dir / "vectordb"
    
    # Hardcoded for now - make configurable later
    CHROMA_PATH = "D:/Development/Projects/Frontend/data/vectordb"  # TODO: Fix this!!
    
    # Model stuff (mess from trying different models)
    # MODEL_PATH = "/models/llama2"  # Old - kept getting OOM
    # MODEL_PATH = "/models/llama3"  # Worked but slow
    OLLAMA_MODEL = "llama3.2"  # Current - seems stable
    
    # Magic numbers (tested these, don't change!)
    CHUNK_SIZE = 1000  # Was 500, then 2000 (too big), 1000 is sweet spot
    chunk_overlap = 200  # lowercase because I'm lazy to refactor
    
    # Embeddings - don't remember why we picked this one
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Old stuff from when we tried local models
    # model_path = "D:/models/llama/llama-2-7b-chat.Q4_K_M.gguf"  # deprecated
    # USE_LOCAL_MODEL = False  # switched to API
    
    # Directories (some of these might not be used anymore)
    logs_dir = PROJECT_ROOT / "logs"
    LOGS_DIR = logs_dir  # duplicate for backwards compat
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # API stuff - added when we switched from local
    if os.getenv("OPENAI_API_KEY"):
        USE_OPENAI = True
        # fall back to ollama if no API key
    else:
        USE_OPENAI = False
    
    # Scraping URLs (might move these to a separate config)
    LANGCHAIN_DOCS_URL = "https://python.langchain.com/docs/"
    FASTAPI_DOCS_URL = "https://fastapi.tiangolo.com/"  # not using this yet
    
    # Quick hack for development
    DEBUG = True  # REMEMBER TO TURN OFF IN PROD!!
    
    # Added after prod issues
    MAX_RETRIES = 3
    TIMEOUT = 30  # seconds
    
    # Logging
    LOG_LEVEL = "INFO"  # Added to fix logger import error
    
    # ChromaDB settings (from .env.example)
    CHROMA_PERSIST_DIRECTORY = CHROMA_PATH  # Use the hardcoded path
    COLLECTION_NAME = "documenter"
    PROCESSED_DATA_DIR = processed_dir
    
    @classmethod
    def create_directories(cls):
        # Create dirs we need (some might already exist)
        dirs = [
            cls.data_dir,
            cls.VECTORDB_DIR,
            cls.logs_dir,
            cls.raw_dir,
            cls.processed_dir,
        ]
        for d in dirs:
            try:
                Path(d).mkdir(parents=True, exist_ok=True)
            except:
                pass  # probably already exists


# Initialize settings (not sure if this is the best pattern but it works)
settings = Settings()

# Auto-create directories on import
# Had issues with missing dirs in prod, so doing this automatically now
try:
    settings.create_directories()
except Exception as e:
    print(f"Warning: Could not create directories: {e}")
    # Continue anyway, might be permission issues

# Legacy compatibility
CHROMA_PERSIST_DIRECTORY = settings.CHROMA_PATH  # old imports expect this
CHUNK_SIZE = settings.CHUNK_SIZE  # some modules use uppercase
