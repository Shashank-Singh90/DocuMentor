import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
from typing import List, Dict, Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PythonDocumentationScraper:
    """Scraper for Python Standard Library documentation"""
    
    def __init__(self, base_url: str = "https://docs.python.org/3/"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_python_docs(self, max_pages: int = 100) -> List[Dict]:
        """Scrape Python documentation"""
        logger.info(f"🕷️ Starting Python documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key Python documentation sections
        start_urls = [
            "library/index.html",
            "tutorial/index.html",
            "reference/index.html",
            "howto/index.html"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} Python documentation pages")
        return self.documents
    
    async def _scrape_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of Python docs"""
        try:
            urls_to_process = [section_url]
            processed = 0
            
            while urls_to_process and processed < max_pages:
                url = urls_to_process.pop(0)
                
                if url in self.scraped_urls:
                    continue
                    
                self.scraped_urls.add(url)
                
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            doc_data = self._parse_python_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_python_links(soup, url)
                                urls_to_process.extend(new_urls[:5])  # Limit new URLs
                                
                        await asyncio.sleep(0.1)  # Be respectful
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_python_page(self, html: str, url: str) -> Dict:
        """Parse a Python documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.sphinxsidebar', '.related']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Python Documentation"
            
            # Get main content
            content_elem = (soup.find('.body') or 
                          soup.find('.document') or 
                          soup.find('main') or 
                          soup.find('body'))
            
            if not content_elem:
                return None
            
            # Extract text content
            content = content_elem.get_text(separator='\n', strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
            if len(content) < 200:  # Skip very short pages
                return None
            
            # Determine document type
            doc_type = self._classify_python_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'python',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_python_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant Python documentation links"""
        links = []
        base_domain = urlparse(self.base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only Python docs, avoid external links and anchors
            if (parsed.netloc == base_domain and 
                not href.startswith('#') and 
                not href.startswith('mailto:') and
                href.endswith('.html')):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _classify_python_doc(self, title: str, content: str, url: str) -> str:
        """Classify Python documentation type"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if '/library/' in url_lower:
            return 'api_reference'
        elif '/tutorial/' in url_lower:
            return 'tutorial'
        elif '/reference/' in url_lower:
            return 'language_reference'
        elif '/howto/' in url_lower:
            return 'howto'
        elif any(keyword in title_lower for keyword in ['module', 'library', 'package']):
            return 'api_reference'
        else:
            return 'general'

async def main():
    """Test the Python scraper"""
    scraper = PythonDocumentationScraper()
    documents = await scraper.scrape_python_docs(max_pages=60)
    
    logger.info(f"📊 Scraped {len(documents)} Python documents")
    
    # Save to file for inspection
    output_file = Path("data/scraped/python_docs.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())




