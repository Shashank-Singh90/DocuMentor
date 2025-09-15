import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
from typing import List, Dict, Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PostgreSQLDocumentationScraper:
    """Scraper for PostgreSQL documentation"""
    
    def __init__(self, base_url: str = "https://www.postgresql.org/docs/current/"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_postgresql_docs(self, max_pages: int = 80) -> List[Dict]:
        """Scrape PostgreSQL documentation"""
        logger.info(f"🕷️ Starting PostgreSQL documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key PostgreSQL documentation sections
        start_urls = [
            "tutorial.html",
            "sql.html",
            "admin.html",
            "client-interfaces.html",
            "reference.html"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} PostgreSQL documentation pages")
        return self.documents
    
    async def _scrape_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of PostgreSQL docs"""
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
                            doc_data = self._parse_postgresql_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_postgresql_links(soup, url)
                                urls_to_process.extend(new_urls[:3])
                                
                        await asyncio.sleep(0.2)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_postgresql_page(self, html: str, url: str) -> Dict:
        """Parse a PostgreSQL documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.navheader', '.navfooter']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "PostgreSQL Documentation"
            
            # Get main content
            main_content = soup.find('body')
            
            if not main_content:
                return None
            
            # Extract text content
            content = main_content.get_text(separator='\n', strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
            if len(content) < 300:
                return None
            
            # Determine document type
            doc_type = self._classify_postgresql_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'postgresql',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_postgresql_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant PostgreSQL documentation links"""
        links = []
        base_domain = urlparse(self.base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            if (parsed.netloc == base_domain and 
                href.endswith('.html') and
                not href.startswith('#')):
                links.append(full_url)
        
        return list(set(links))
    
    def _classify_postgresql_doc(self, title: str, content: str, url: str) -> str:
        """Classify PostgreSQL documentation type"""
        url_lower = url.lower()
        
        if 'tutorial' in url_lower:
            return 'tutorial'
        elif 'reference' in url_lower:
            return 'reference'
        elif 'admin' in url_lower:
            return 'administration'
        elif 'sql' in url_lower:
            return 'sql_reference'
        else:
            return 'general'

class MongoDBDocumentationScraper:
    """Scraper for MongoDB documentation"""
    
    def __init__(self, base_url: str = "https://www.mongodb.com/docs/"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_mongodb_docs(self, max_pages: int = 60) -> List[Dict]:
        """Scrape MongoDB documentation"""
        logger.info(f"🕷️ Starting MongoDB documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key MongoDB documentation sections
        start_urls = [
            "manual/",
            "drivers/python/",
            "atlas/",
            "compass/"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_mongodb_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} MongoDB documentation pages")
        return self.documents
    
    async def _scrape_mongodb_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of MongoDB docs"""
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
                            doc_data = self._parse_mongodb_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_mongodb_links(soup, url)
                                urls_to_process.extend(new_urls[:3])
                                
                        await asyncio.sleep(0.2)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_mongodb_page(self, html: str, url: str) -> Dict:
        """Parse a MongoDB documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.sidebar']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "MongoDB Documentation"
            
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
            
            if len(content) < 300:
                return None
            
            # Determine document type
            doc_type = self._classify_mongodb_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'mongodb',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_mongodb_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant MongoDB documentation links"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            
            if ('mongodb.com/docs' in full_url and 
                not href.startswith('#') and 
                not href.startswith('mailto:')):
                links.append(full_url)
        
        return list(set(links))
    
    def _classify_mongodb_doc(self, title: str, content: str, url: str) -> str:
        """Classify MongoDB documentation type"""
        url_lower = url.lower()
        
        if 'manual' in url_lower:
            return 'manual'
        elif 'drivers' in url_lower:
            return 'driver'
        elif 'atlas' in url_lower:
            return 'atlas'
        elif 'compass' in url_lower:
            return 'compass'
        else:
            return 'general'

async def main():
    """Test both database scrapers"""
    # Test PostgreSQL scraper
    postgresql_scraper = PostgreSQLDocumentationScraper()
    postgresql_docs = await postgresql_scraper.scrape_postgresql_docs(max_pages=40)
    
    # Test MongoDB scraper
    mongodb_scraper = MongoDBDocumentationScraper()
    mongodb_docs = await mongodb_scraper.scrape_mongodb_docs(max_pages=40)
    
    # Combine documents
    all_docs = postgresql_docs + mongodb_docs
    
    logger.info(f"📊 Total database documents: {len(all_docs)}")
    logger.info(f"📊 PostgreSQL docs: {len(postgresql_docs)}")
    logger.info(f"📊 MongoDB docs: {len(mongodb_docs)}")
    
    # Save to file for inspection
    output_file = Path("data/scraped/database_docs.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())




