import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
from typing import List, Dict, Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DockerDocumentationScraper:
    """Scraper for Docker documentation"""
    
    def __init__(self, base_url: str = "https://docs.docker.com/"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_docker_docs(self, max_pages: int = 80) -> List[Dict]:
        """Scrape Docker documentation"""
        logger.info(f"🕷️ Starting Docker documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key Docker documentation sections
        start_urls = [
            "get-started/",
            "guides/",
            "reference/",
            "engine/",
            "compose/"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} Docker documentation pages")
        return self.documents
    
    async def _scrape_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of Docker docs"""
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
                            doc_data = self._parse_docker_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_docker_links(soup, url)
                                urls_to_process.extend(new_urls[:3])  # Limit new URLs
                                
                        await asyncio.sleep(0.2)  # Be respectful
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_docker_page(self, html: str, url: str) -> Dict:
        """Parse a Docker documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.sidebar', '.breadcrumb']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Docker Documentation"
            
            # Get main content
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('.content') or
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
            doc_type = self._classify_docker_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'docker',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_docker_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant Docker documentation links"""
        links = []
        base_domain = urlparse(self.base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only Docker docs, avoid external links and anchors
            if (parsed.netloc == base_domain and 
                not href.startswith('#') and 
                not href.startswith('mailto:') and
                '/docs/' in full_url):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _classify_docker_doc(self, title: str, content: str, url: str) -> str:
        """Classify Docker documentation type"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if any(keyword in url_lower for keyword in ['/reference/', 'cli', 'api']):
            return 'api_reference'
        elif any(keyword in url_lower for keyword in ['/get-started/', 'tutorial']):
            return 'tutorial'
        elif any(keyword in url_lower for keyword in ['/guides/', 'guide']):
            return 'guide'
        elif 'compose' in url_lower:
            return 'compose'
        elif 'engine' in url_lower:
            return 'engine'
        else:
            return 'general'

async def main():
    """Test the Docker scraper"""
    scraper = DockerDocumentationScraper()
    documents = await scraper.scrape_docker_docs(max_pages=60)
    
    logger.info(f"📊 Scraped {len(documents)} Docker documents")
    
    # Save to file for inspection
    output_file = Path("data/scraped/docker_docs.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())




