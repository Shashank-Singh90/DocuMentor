import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import time
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class FastAPIScraper:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.FASTAPI_DOCS_URL
        self.output_dir = settings.RAW_DATA_DIR / "fastapi"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        
        # Set headers to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def scrape(self, max_pages: int = 20):
        """Scrape FastAPI documentation"""
        logger.info(f"🚀 Starting FastAPI documentation scrape from {self.base_url}")
        
        documents = []
        
        # FastAPI has well-structured documentation sections
        doc_sections = [
            "",  # Main page
            "tutorial/",
            "advanced/",
            "deployment/",
            "reference/",
            "tutorial/first-steps/",
            "tutorial/path-params/",
            "tutorial/query-params/",
            "tutorial/request-body/",
            "tutorial/response-model/",
            "advanced/security/",
            "advanced/dependencies/",
            "advanced/middleware/",
            "advanced/background-tasks/",
        ]
        
        scraped_count = 0
        for section in doc_sections:
            if scraped_count >= max_pages:
                break
                
            section_url = urljoin(self.base_url, section)
            docs = self._scrape_section(section_url, section)
            documents.extend(docs)
            scraped_count += len(docs)
            
            # Rate limiting - be respectful
            time.sleep(1)
            
        # Save documents
        self._save_documents(documents)
        
    def _scrape_section(self, section_url: str, section_type: str) -> List[Dict]:
        """Scrape a documentation section"""
        documents = []
        
        try:
            logger.info(f"📄 Scraping FastAPI section: {section_url}")
            
            response = self.session.get(section_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main content
            doc_data = self._scrape_page(section_url, section_type, soup)
            if doc_data:
                documents.append(doc_data)
                logger.info(f"✅ Extracted content from {section_url}")
            
            # Look for links to other docs in this section
            nav_links = self._find_navigation_links(soup, section_url)
            
            for link_url in nav_links[:5]:  # Limit to avoid too many requests
                if self._is_valid_doc_url(link_url):
                    try:
                        response = self.session.get(link_url, timeout=30)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            doc_data = self._scrape_page(link_url, section_type, soup)
                            if doc_data:
                                documents.append(doc_data)
                                logger.info(f"✅ Extracted content from {link_url}")
                        time.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to scrape {link_url}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error scraping section {section_url}: {e}")
            
        return documents
        
    def _scrape_page(self, url: str, section_type: str, soup: BeautifulSoup) -> Dict:
        """Scrape individual documentation page"""
        # Find main content area
        content = (soup.find('main') or 
                  soup.find('article') or 
                  soup.find('[role="main"]') or
                  soup.find('.content') or
                  soup.find('.md-content'))
        
        if not content:
            logger.warning(f"⚠️ No main content found for {url}")
            return None
            
        # Remove navigation and unwanted elements
        for unwanted in content.find_all(['nav', 'aside', '.md-nav', '.md-sidebar']):
            unwanted.decompose()
            
        title = self._extract_title(content, url)
        sections = self._extract_sections(content)
        
        if not sections:
            return None
            
        # Create full content string
        full_content = self._sections_to_content(title, sections)
        
        return {
            "url": url,
            "title": title,
            "sections": sections,
            "content": full_content,
            "doc_type": self._classify_doc_type(section_type, title),
            "source": "fastapi"
        }
    
    def _extract_title(self, content, url: str) -> str:
        """Extract page title"""
        # Try different title selectors
        title_selectors = ['h1', '.md-content__title', 'title']
        
        for selector in title_selectors:
            title_elem = content.find(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 0:
                    return title
                    
        # Fallback to URL-based title
        path = urlparse(url).path
        parts = [p for p in path.split('/') if p]
        if parts:
            return parts[-1].replace('-', ' ').replace('_', ' ').title()
        return "FastAPI Documentation"
    
    def _extract_sections(self, content) -> List[Dict]:
        """Extract structured sections from content"""
        sections = []
        current_section = {"title": "", "content": [], "code_blocks": []}
        
        # Process all elements
        for element in content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'pre', 'div', 'li']):
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
                if code_text and len(code_text) > 5:
                    language = self._detect_language(element, code_elem)
                    current_section["code_blocks"].append({
                        "code": code_text,
                        "language": language
                    })
            elif element.name in ['div'] and 'highlight' in element.get('class', []):
                # Highlighted code blocks
                code_elem = element.find('code')
                if code_elem:
                    code_text = code_elem.get_text().strip()
                    if code_text:
                        current_section["code_blocks"].append({
                            "code": code_text,
                            "language": "python"
                        })
            elif element.name in ['p', 'li', 'div']:
                # Text content
                text = element.get_text().strip()
                if text and len(text) > 15:  # Filter very short texts
                    # Skip if it's mostly code
                    if not (element.find('code') and len(text) < 50):
                        current_section["content"].append(text)
                        
        # Add the last section
        if current_section["content"] or current_section["code_blocks"]:
            sections.append(current_section)
            
        return sections
    
    def _sections_to_content(self, title: str, sections: List[Dict]) -> str:
        """Convert sections to full content string"""
        content_parts = [f"# {title}\n"]
        
        for section in sections:
            section_title = section.get("title", "").strip()
            if section_title and section_title != title:
                content_parts.append(f"\n## {section_title}\n")
            
            # Add text content
            for paragraph in section.get("content", []):
                content_parts.append(f"{paragraph}\n")
            
            # Add code blocks
            for code_block in section.get("code_blocks", []):
                language = code_block.get("language", "python")
                content_parts.append(f"\n```{language}\n{code_block['code']}\n```\n")
        
        return "\n".join(content_parts)
    
    def _detect_language(self, parent_element, code_element) -> str:
        """Detect programming language from code element"""
        # Check classes
        for element in [code_element, parent_element]:
            classes = element.get('class', [])
            for cls in classes:
                if 'language-' in str(cls):
                    return str(cls).replace('language-', '')
                if cls in ['python', 'javascript', 'bash', 'json', 'yaml', 'html', 'css']:
                    return cls
        
        # Check if it looks like Python (FastAPI is Python-focused)
        code_text = code_element.get_text().strip()
        if any(keyword in code_text for keyword in ['from fastapi', 'import fastapi', 'FastAPI()', 'def ', 'async def']):
            return 'python'
        elif any(keyword in code_text for keyword in ['curl', 'http', 'GET', 'POST']):
            return 'bash'
        elif code_text.startswith('{') and code_text.endswith('}'):
            return 'json'
        
        return 'python'  # Default for FastAPI docs
    
    def _find_navigation_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find navigation links on the page"""
        links = []
        
        # Look for navigation elements
        nav_selectors = [
            '.md-nav__link',
            '.toctree a',
            'nav a',
            '.navigation a'
        ]
        
        for selector in nav_selectors:
            nav_links = soup.select(selector)
            for link in nav_links[:10]:  # Limit links
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_doc_url(full_url):
                        links.append(full_url)
                        
        return list(set(links))  # Remove duplicates
    
    def _classify_doc_type(self, section_type: str, title: str) -> str:
        """Classify the type of documentation"""
        title_lower = title.lower()
        section_lower = section_type.lower()
        
        if 'reference' in section_lower or 'api' in title_lower:
            return 'api_reference'
        elif 'tutorial' in section_lower or 'first' in title_lower or 'getting started' in title_lower:
            return 'tutorial'
        elif 'advanced' in section_lower or 'advanced' in title_lower:
            return 'advanced'
        else:
            return 'conceptual'
    
    def _is_valid_doc_url(self, url: str) -> bool:
        """Check if URL is a valid documentation page"""
        parsed = urlparse(url)
        
        # Must be from FastAPI docs
        if 'fastapi.tiangolo.com' not in parsed.netloc:
            return False
            
        # Skip certain file types and fragments
        if (parsed.path.endswith(('.png', '.jpg', '.gif', '.svg', '.pdf', '.zip')) or
            parsed.fragment or
            '#' in parsed.path):
            return False
            
        return True
        
    def _save_documents(self, documents: List[Dict]):
        """Save scraped documents to JSON"""
        if not documents:
            logger.warning("⚠️ No FastAPI documents scraped!")
            return
            
        output_file = self.output_dir / "fastapi_docs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
            
        logger.info(f"💾 Saved {len(documents)} FastAPI documents to {output_file}")
        
        # Save summary
        summary = {
            "total_documents": len(documents),
            "documents_with_content": len([d for d in documents if d.get('content')]),
            "total_sections": sum(len(d.get('sections', [])) for d in documents),
            "doc_types": {}
        }
        
        # Count doc types
        for doc in documents:
            doc_type = doc.get('doc_type', 'unknown')
            summary["doc_types"][doc_type] = summary["doc_types"].get(doc_type, 0) + 1
        
        summary_file = self.output_dir / "scraping_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"📊 FastAPI scraping summary: {summary}")

# Test function
def test_scraper():
    """Test the FastAPI scraper"""
    scraper = FastAPIScraper()
    scraper.scrape(max_pages=5)  # Test with just 5 pages

if __name__ == "__main__":
    test_scraper()