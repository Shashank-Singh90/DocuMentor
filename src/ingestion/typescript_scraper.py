import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
from typing import List, Dict, Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TypeScriptDocumentationScraper:
    """Scraper for TypeScript documentation"""
    
    def __init__(self, base_url: str = "https://www.typescriptlang.org/docs/"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_typescript_docs(self, max_pages: int = 100) -> List[Dict]:
        """Scrape TypeScript documentation"""
        logger.info(f"🕷️ Starting TypeScript documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key TypeScript documentation sections
        start_urls = [
            "",  # Main docs
            "handbook/",
            "reference/",
            "project-config/"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} TypeScript documentation pages")
        return self.documents
    
    async def _scrape_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of TypeScript docs"""
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
                            doc_data = self._parse_typescript_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_typescript_links(soup, url)
                                urls_to_process.extend(new_urls[:4])  # Get more TS docs
                                
                        await asyncio.sleep(0.2)  # Be respectful
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_typescript_page(self, html: str, url: str) -> Dict:
        """Parse a TypeScript documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.sidebar', '.breadcrumb']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "TypeScript Documentation"
            
            # Get main content
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('.markdown') or
                          soup.find('body'))
            
            if not main_content:
                return None
            
            # Extract text content
            content = main_content.get_text(separator='\n', strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
            if len(content) < 200:  # Skip very short pages
                return None
            
            # Determine document type
            doc_type = self._classify_typescript_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'typescript',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_typescript_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant TypeScript documentation links"""
        links = []
        base_domain = urlparse(self.base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only TypeScript docs, avoid external links and anchors
            if (parsed.netloc == base_domain and 
                '/docs/' in full_url and
                not href.startswith('#') and 
                not href.startswith('mailto:')):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _classify_typescript_doc(self, title: str, content: str, url: str) -> str:
        """Classify TypeScript documentation type"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if any(keyword in url_lower for keyword in ['/handbook/', 'basic']):
            return 'handbook'
        elif any(keyword in url_lower for keyword in ['/reference/', 'utility-types']):
            return 'reference'
        elif any(keyword in url_lower for keyword in ['/project-config/', 'tsconfig']):
            return 'configuration'
        elif any(keyword in title_lower for keyword in ['tutorial', 'getting started']):
            return 'tutorial'
        elif any(keyword in content.lower() for keyword in ['interface', 'type', 'generic']):
            return 'type_system'
        else:
            return 'general'

async def main():
    """Test the TypeScript scraper"""
    scraper = TypeScriptDocumentationScraper()
    documents = await scraper.scrape_typescript_docs(max_pages=80)
    
    logger.info(f"📊 Scraped {len(documents)} TypeScript documents")
    
    # Save to file for inspection
    output_file = Path("data/scraped/typescript_docs.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())