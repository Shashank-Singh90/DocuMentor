import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json
from typing import List, Dict, Set
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ReactDocumentationScraper:
    """Scraper for React documentation"""
    
    def __init__(self, base_url: str = "https://react.dev/"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_react_docs(self, max_pages: int = 80) -> List[Dict]:
        """Scrape React documentation"""
        logger.info(f"🕷️ Starting React documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key React documentation sections
        start_urls = [
            "learn",
            "reference/react",
            "reference/react-dom",
            "blog"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} React documentation pages")
        return self.documents
    
    async def _scrape_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of React docs"""
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
                            doc_data = self._parse_react_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_react_links(soup, url)
                                urls_to_process.extend(new_urls[:3])  # Limit new URLs
                                
                        await asyncio.sleep(0.2)  # Be respectful
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_react_page(self, html: str, url: str) -> Dict:
        """Parse a React documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.sidebar', '.breadcrumb']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "React Documentation"
            
            # Get main content
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('[role="main"]') or 
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
            doc_type = self._classify_react_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'react',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_react_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant React documentation links"""
        links = []
        base_domain = urlparse(self.base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only React docs, avoid external links and anchors
            if (parsed.netloc == base_domain and 
                not href.startswith('#') and 
                not href.startswith('mailto:') and
                not 'github.com' in full_url):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _classify_react_doc(self, title: str, content: str, url: str) -> str:
        """Classify React documentation type"""
        title_lower = title.lower()
        url_lower = url.lower()
        content_lower = content.lower()
        
        if any(keyword in url_lower for keyword in ['/reference/', 'api']):
            return 'api_reference'
        elif any(keyword in url_lower for keyword in ['/learn/', 'tutorial', 'guide']):
            return 'tutorial'
        elif any(keyword in title_lower for keyword in ['hook', 'component']):
            return 'api_reference'
        elif any(keyword in content_lower for keyword in ['example', 'demo']):
            return 'example'
        elif any(keyword in url_lower for keyword in ['/blog/']):
            return 'blog'
        else:
            return 'conceptual'

class NextJSDocumentationScraper:
    """Scraper for Next.js documentation"""
    
    def __init__(self, base_url: str = "https://nextjs.org/docs"):
        self.base_url = base_url
        self.scraped_urls: Set[str] = set()
        self.documents: List[Dict] = []
        
    async def scrape_nextjs_docs(self, max_pages: int = 60) -> List[Dict]:
        """Scrape Next.js documentation"""
        logger.info(f"🕷️ Starting Next.js documentation scraping...")
        logger.info(f"📍 Base URL: {self.base_url}")
        
        # Key Next.js documentation sections
        start_urls = [
            "",  # Main docs
            "/app",
            "/pages",
            "/api-reference"
        ]
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for section in start_urls:
                url = urljoin(self.base_url, section)
                tasks.append(self._scrape_nextjs_section(session, url, max_pages//len(start_urls)))
            
            await asyncio.gather(*tasks)
        
        logger.info(f"✅ Scraped {len(self.documents)} Next.js documentation pages")
        return self.documents
    
    async def _scrape_nextjs_section(self, session: aiohttp.ClientSession, section_url: str, max_pages: int):
        """Scrape a specific section of Next.js docs"""
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
                            doc_data = self._parse_nextjs_page(html, url)
                            
                            if doc_data:
                                self.documents.append(doc_data)
                                processed += 1
                                
                                # Find more URLs in this page
                                soup = BeautifulSoup(html, 'html.parser')
                                new_urls = self._extract_nextjs_links(soup, url)
                                urls_to_process.extend(new_urls[:3])  # Limit new URLs
                                
                        await asyncio.sleep(0.2)  # Be respectful
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error scraping {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in section scraping: {e}")
    
    def _parse_nextjs_page(self, html: str, url: str) -> Dict:
        """Parse a Next.js documentation page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove navigation and footer
            for element in soup.find_all(['nav', 'footer', 'header', '.sidebar']):
                element.decompose()
            
            # Get title
            title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Next.js Documentation"
            
            # Get main content
            main_content = (soup.find('main') or 
                          soup.find('article') or 
                          soup.find('.prose') or
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
            doc_type = self._classify_nextjs_doc(title, content, url)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'source': 'nextjs',
                'doc_type': doc_type,
                'scraped_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing page {url}: {e}")
            return None
    
    def _extract_nextjs_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant Next.js documentation links"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only Next.js docs
            if ('nextjs.org' in parsed.netloc and 
                '/docs' in full_url and
                not href.startswith('#') and 
                not href.startswith('mailto:')):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def _classify_nextjs_doc(self, title: str, content: str, url: str) -> str:
        """Classify Next.js documentation type"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if 'api-reference' in url_lower:
            return 'api_reference'
        elif any(keyword in url_lower for keyword in ['/app/', '/pages/']):
            return 'tutorial'
        elif 'getting-started' in url_lower:
            return 'tutorial'
        else:
            return 'conceptual'

async def main():
    """Test both React and Next.js scrapers"""
    # Test React scraper
    react_scraper = ReactDocumentationScraper()
    react_docs = await react_scraper.scrape_react_docs(max_pages=40)
    
    # Test Next.js scraper
    nextjs_scraper = NextJSDocumentationScraper()
    nextjs_docs = await nextjs_scraper.scrape_nextjs_docs(max_pages=30)
    
    # Combine documents
    all_docs = react_docs + nextjs_docs
    
    logger.info(f"📊 Total scraped documents: {len(all_docs)}")
    logger.info(f"📊 React docs: {len(react_docs)}")
    logger.info(f"📊 Next.js docs: {len(nextjs_docs)}")
    
    # Save to file for inspection
    output_file = Path("data/scraped/react_nextjs_docs.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())