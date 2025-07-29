import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
from pathlib import Path
import json
from typing import Set, List, Dict
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class LangChainScraper:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.LANGCHAIN_DOCS_URL
        self.visited_urls: Set[str] = set()
        self.documents: List[Dict] = []
        self.output_dir = settings.RAW_DATA_DIR / "langchain"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def scrape(self, max_pages: int = 50):
        """Main scraping function"""
        logger.info(f"🕷️ Starting LangChain documentation scrape from {self.base_url}")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent to avoid blocking
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            try:
                await self._crawl_docs(page, self.base_url, max_pages=max_pages)
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
            finally:
                await browser.close()
                
        # Save scraped data
        self._save_documents()
        
    async def _crawl_docs(self, page, url: str, depth: int = 0, max_depth: int = 3, max_pages: int = 50):
        """Recursively crawl documentation"""
        if (url in self.visited_urls or 
            depth > max_depth or 
            len(self.visited_urls) >= max_pages):
            return
            
        self.visited_urls.add(url)
        logger.info(f"📄 Scraping ({len(self.visited_urls)}/{max_pages}): {url}")
        
        try:
            # Navigate to page
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            
            if response.status != 200:
                logger.warning(f"⚠️ Failed to load {url}: {response.status}")
                return
                
            await page.wait_for_selector("main, article, .content", timeout=10000)
            
            # Extract content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find main content area
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('[role="main"]') or
                          soup.find('.content') or
                          soup.find('.markdown'))
            
            if not main_content:
                logger.warning(f"⚠️ No main content found for {url}")
                return
                
            # Extract structured content
            doc_data = self._extract_content(main_content, url)
            if doc_data and doc_data.get('content'):
                self.documents.append(doc_data)
                logger.info(f"✅ Extracted content from {url}")
            
            # Find links to other docs (if not at max depth)
            if depth < max_depth and len(self.visited_urls) < max_pages:
                links = main_content.find_all('a', href=True)
                for link in links[:10]:  # Limit links per page
                    next_url = urljoin(url, link['href'])
                    if self._is_valid_doc_url(next_url):
                        await self._crawl_docs(page, next_url, depth + 1, max_depth, max_pages)
                        
        except Exception as e:
            logger.error(f"❌ Error scraping {url}: {e}")
            
    def _extract_content(self, soup_element, url: str) -> Dict:
        """Extract structured content from page"""
        # Get title
        title_elem = soup_element.find('h1')
        title_text = title_elem.get_text().strip() if title_elem else self._extract_title_from_url(url)
        
        # Remove navigation and other unwanted elements
        for unwanted in soup_element.find_all(['nav', 'aside', '.nav', '.sidebar', '.toc']):
            unwanted.decompose()
        
        # Extract sections
        sections = []
        current_section = {"title": title_text, "content": [], "code_blocks": []}
        
        # Process all relevant elements
        for element in soup_element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'pre', 'code', 'li', 'div']):
            if element.name in ['h1', 'h2', 'h3', 'h4']:
                # Start new section
                if current_section["content"] or current_section["code_blocks"]:
                    sections.append(current_section)
                current_section = {
                    "title": element.get_text().strip(),
                    "content": [],
                    "code_blocks": []
                }
            elif element.name == 'pre':
                # Code block
                code_elem = element.find('code') or element
                code_text = code_elem.get_text().strip()
                if code_text and len(code_text) > 10:  # Filter very short code
                    # Try to detect language
                    language = self._detect_language(code_elem)
                    current_section["code_blocks"].append({
                        "code": code_text,
                        "language": language
                    })
            elif element.name in ['p', 'li', 'div']:
                # Text content
                text = element.get_text().strip()
                if text and len(text) > 20:  # Filter very short texts
                    # Skip if it's just a code snippet inline
                    if not (element.find('code') and len(text) < 100):
                        current_section["content"].append(text)
                        
        # Add the last section
        if current_section["content"] or current_section["code_blocks"]:
            sections.append(current_section)
            
        # Create full content string
        full_content = self._sections_to_content(title_text, sections)
            
        return {
            "url": url,
            "title": title_text,
            "sections": sections,
            "content": full_content,
            "doc_type": "conceptual",
            "source": "langchain"
        }
    
    def _sections_to_content(self, title: str, sections: List[Dict]) -> str:
        """Convert sections to full content string"""
        content_parts = [f"# {title}\n"]
        
        for section in sections:
            if section["title"] != title:  # Don't repeat main title
                content_parts.append(f"\n## {section['title']}\n")
            
            # Add text content
            for paragraph in section.get("content", []):
                content_parts.append(f"{paragraph}\n")
            
            # Add code blocks
            for code_block in section.get("code_blocks", []):
                language = code_block.get("language", "")
                content_parts.append(f"\n```{language}\n{code_block['code']}\n```\n")
        
        return "\n".join(content_parts)
    
    def _detect_language(self, code_elem) -> str:
        """Detect programming language from code element"""
        # Check class attributes
        classes = code_elem.get('class', [])
        for cls in classes:
            if 'language-' in cls:
                return cls.replace('language-', '')
            if cls in ['python', 'javascript', 'bash', 'json', 'yaml']:
                return cls
        
        # Check parent classes
        parent = code_elem.parent
        if parent and parent.get('class'):
            for cls in parent.get('class', []):
                if 'language-' in cls:
                    return cls.replace('language-', '')
        
        return 'python'  # Default for LangChain docs
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract title from URL if no h1 found"""
        path = urlparse(url).path
        parts = [p for p in path.split('/') if p]
        if parts:
            title = parts[-1].replace('-', ' ').replace('_', ' ').title()
            return title
        return "Untitled"
        
    def _is_valid_doc_url(self, url: str) -> bool:
        """Check if URL is a valid documentation page"""
        parsed = urlparse(url)
        
        # Must be from LangChain docs
        if 'langchain.com' not in parsed.netloc:
            return False
            
        # Must be a docs page
        if '/docs/' not in parsed.path:
            return False
            
        # Skip certain file types
        if parsed.path.endswith(('.png', '.jpg', '.gif', '.svg', '.pdf', '.zip')):
            return False
            
        # Skip external links and anchors
        if parsed.fragment or parsed.query:
            return False
            
        return True
        
    def _save_documents(self):
        """Save scraped documents to JSON"""
        if not self.documents:
            logger.warning("⚠️ No documents scraped!")
            return
            
        output_file = self.output_dir / "langchain_docs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
        logger.info(f"💾 Saved {len(self.documents)} LangChain documents to {output_file}")
        
        # Save summary
        summary = {
            "total_documents": len(self.documents),
            "total_urls_visited": len(self.visited_urls),
            "documents_with_content": len([d for d in self.documents if d.get('content')]),
            "total_sections": sum(len(d.get('sections', [])) for d in self.documents)
        }
        
        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"📊 Scraping summary: {summary}")

# Test function
async def test_scraper():
    """Test the scraper with a few pages"""
    scraper = LangChainScraper()
    await scraper.scrape(max_pages=5)  # Test with just 5 pages

if __name__ == "__main__":
    asyncio.run(test_scraper())