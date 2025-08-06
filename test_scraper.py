#!/usr/bin/env python3
"""Test script for the LangChain scraper"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.ingestion.langchain_scraper import LangChainScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_langchain_scraper():
    """Test the LangChain scraper with a few pages"""
    logger.info("🚀 Starting LangChain scraper test...")
    
    try:
        scraper = LangChainScraper()
        await scraper.scrape(max_pages=3)  # Start with just 3 pages for testing
        
        logger.info("✅ Scraper test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Scraper test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_langchain_scraper())