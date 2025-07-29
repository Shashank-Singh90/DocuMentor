#!/usr/bin/env python3
"""Test both LangChain and FastAPI scrapers"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.ingestion.langchain_scraper import LangChainScraper
from src.ingestion.fastapi_scraper import FastAPIScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_both_scrapers():
    """Test both scrapers"""
    logger.info("🚀 Testing both documentation scrapers...")
    
    try:
        # Test LangChain scraper (async)
        logger.info("📚 Testing LangChain scraper...")
        langchain_scraper = LangChainScraper()
        await langchain_scraper.scrape(max_pages=3)
        
        # Test FastAPI scraper (sync)
        logger.info("🚀 Testing FastAPI scraper...")
        fastapi_scraper = FastAPIScraper()
        fastapi_scraper.scrape(max_pages=3)
        
        logger.info("✅ Both scrapers completed successfully!")
        
        # Check what we got
        from pathlib import Path
        langchain_files = list(Path("data/raw/langchain").glob("*.json"))
        fastapi_files = list(Path("data/raw/fastapi").glob("*.json"))
        
        logger.info(f"📊 Results:")
        logger.info(f"   LangChain files: {len(langchain_files)}")
        logger.info(f"   FastAPI files: {len(fastapi_files)}")
        
        for file in langchain_files:
            logger.info(f"   📄 {file}")
        for file in fastapi_files:
            logger.info(f"   📄 {file}")
        
    except Exception as e:
        logger.error(f"❌ Scraper test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_both_scrapers())