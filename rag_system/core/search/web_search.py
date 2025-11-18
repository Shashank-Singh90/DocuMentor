"""
Web Search Integration with Local Firecrawl and fallback options
"""

import json
import sys
import os
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from pathlib import Path

# Add local Firecrawl to path
firecrawl_path = Path(__file__).parent.parent.parent.parent / "firecrowl" / "apps" / "python-sdk"
if firecrawl_path.exists():
    sys.path.insert(0, str(firecrawl_path))

try:
    from firecrawl import Firecrawl
    HAS_LOCAL_FIRECRAWL = True
except ImportError:
    HAS_LOCAL_FIRECRAWL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

from rag_system.core.utils.logger import get_logger
from rag_system.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

class WebSearchProvider:
    """Web search with multiple providers"""

    def __init__(self):
        # Initialize local Firecrawl client if available
        self.local_firecrawl = None
        if HAS_LOCAL_FIRECRAWL:
            try:
                # Try to initialize local Firecrawl
                # Get API key from settings or environment, no hardcoded fallback
                api_key = getattr(settings, 'firecrawl_api_key', None) or os.getenv("FIRECRAWL_API_KEY")
                api_url = os.getenv("FIRECRAWL_API_URL", "http://localhost:3002")

                if api_key:
                    self.local_firecrawl = Firecrawl(api_key=api_key, api_url=api_url)
                    logger.info("Local Firecrawl client initialized successfully")
                else:
                    logger.debug("Firecrawl API key not configured")
            except Exception as e:
                logger.warning(f"Failed to initialize local Firecrawl: {e}")
                self.local_firecrawl = None

        # Keep legacy settings for fallback
        self.firecrawl_api_key = getattr(settings, 'firecrawl_api_key', None)
        self.firecrawl_base_url = "https://api.firecrawl.dev/v0"

    def search_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the web for information

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with content
        """
        if not getattr(settings, 'enable_web_search', True):
            return []

        # Try local Firecrawl first
        if self.local_firecrawl:
            results = self._search_with_local_firecrawl(query, max_results)
            if results:
                return results
            # If local Firecrawl returns no results, continue to fallback

        # Fallback to real web search
        return self._search_web_scraping(query, max_results)

    def _search_with_local_firecrawl(self, query: str, max_results: int) -> List[Dict]:
        """Search using local Firecrawl repository"""
        try:
            # Use the search function from the local Firecrawl client
            search_response = self.local_firecrawl.search(query=query, limit=max_results)

            # Extract web results from the response
            web_results = getattr(search_response, "web", []) or []

            results = []
            for item in web_results[:max_results]:
                # Try to get markdown content or fallback to text content
                content = ""
                if hasattr(item, 'markdown') and item.markdown:
                    content = item.markdown[:2000]  # Limit content
                elif hasattr(item, 'content') and item.content:
                    content = item.content[:2000]
                elif hasattr(item, 'text') and item.text:
                    content = item.text[:2000]

                if content:  # Only add if we have content
                    result = {
                        'content': content,
                        'metadata': {
                            'title': getattr(item, 'title', 'Local Firecrawl Result'),
                            'url': getattr(item, 'url', ''),
                            'source': 'web_search',
                            'provider': 'local_firecrawl'
                        },
                        'score': 0.95  # High relevance for local Firecrawl results
                    }
                    results.append(result)

            logger.info(f"Local Firecrawl returned {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Local Firecrawl search error: {e}")
            return []

    def _search_with_firecrawl(self, query: str, max_results: int) -> List[Dict]:
        """Search using Firecrawl API"""
        if not HAS_REQUESTS:
            logger.error("requests library not available for web search")
            return []

        try:
            # First, search for URLs
            search_url = f"{self.firecrawl_base_url}/search"
            search_payload = {
                "query": query,
                "pageOptions": {
                    "fetchPageContent": True,
                    "includeMarkdown": True
                },
                "limit": max_results
            }

            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(search_url, json=search_payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get('data', [])[:max_results]:
                    result = {
                        'content': item.get('markdown', item.get('content', ''))[:2000],  # Limit content
                        'metadata': {
                            'title': item.get('title', 'Web Result'),
                            'url': item.get('url', ''),
                            'source': 'web_search',
                            'provider': 'firecrawl'
                        },
                        'score': 0.9  # High relevance for web results
                    }
                    results.append(result)

                logger.info(f"Firecrawl returned {len(results)} results for query: {query}")
                return results

            else:
                logger.error(f"Firecrawl search failed with status: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Firecrawl search error: {e}")
            return []

    def _search_web_scraping(self, query: str, max_results: int) -> List[Dict]:
        """Perform real web search using DuckDuckGo web scraping"""
        if not HAS_REQUESTS:
            return self._create_fallback_results(query, max_results)

        try:
            # Use DuckDuckGo web search (doesn't require API key)
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'b': '',  # Start from beginning
                'kl': 'us-en',  # Language
                'df': '',  # Date filter
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=10)

            if response.status_code == 200 and HAS_BEAUTIFULSOUP:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []

                # Find search result elements
                result_elements = soup.find_all('div', class_='result')

                for element in result_elements[:max_results]:
                    try:
                        # Extract title
                        title_elem = element.find('a', class_='result__a')
                        title = title_elem.get_text().strip() if title_elem else "Search Result"
                        url = title_elem.get('href', '') if title_elem else ''

                        # Extract snippet
                        snippet_elem = element.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                        if snippet and len(snippet) > 20:  # Only add if we have meaningful content
                            results.append({
                                'content': snippet,
                                'metadata': {
                                    'title': title,
                                    'url': url,
                                    'source': 'web_search',
                                    'provider': 'duckduckgo_web'
                                },
                                'score': 0.8
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing search result: {e}")
                        continue

                if results:
                    logger.info(f"DuckDuckGo web search returned {len(results)} results for query: {query}")
                    return results

            # If web scraping fails, try the API approach
            return self._search_with_duckduckgo_api(query, max_results)

        except Exception as e:
            logger.warning(f"Web scraping search error: {e}")
            return self._search_with_duckduckgo_api(query, max_results)

    def _search_with_duckduckgo_api(self, query: str, max_results: int) -> List[Dict]:
        """Fallback search using DuckDuckGo Instant Answer API with enhanced fallback"""
        if not HAS_REQUESTS:
            return self._create_fallback_results(query, max_results)

        try:
            # DuckDuckGo Instant Answer API (free, no key required)
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []

                # Get abstract if available
                if data.get('Abstract'):
                    results.append({
                        'content': data['Abstract'][:1000],
                        'metadata': {
                            'title': data.get('AbstractText', 'DuckDuckGo Result'),
                            'url': data.get('AbstractURL', ''),
                            'source': 'web_search',
                            'provider': 'duckduckgo'
                        },
                        'score': 0.8
                    })

                # Get related topics
                for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'content': topic['Text'][:800],
                            'metadata': {
                                'title': topic.get('Text', '').split('.')[0],
                                'url': topic.get('FirstURL', ''),
                                'source': 'web_search',
                                'provider': 'duckduckgo'
                            },
                            'score': 0.7
                        })

                logger.info(f"DuckDuckGo returned {len(results)} results for query: {query}")

                # If no results from DuckDuckGo, provide fallback
                if not results:
                    return self._create_fallback_results(query, max_results)

                return results

            return self._create_fallback_results(query, max_results)

        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}, using fallback")
            return self._create_fallback_results(query, max_results)

    def _create_fallback_results(self, query: str, max_results: int) -> List[Dict]:
        """Create fallback search results when external services are unavailable"""
        fallback_results = []

        # Generate helpful fallback content based on common programming queries
        if any(term in query.lower() for term in ['python', 'programming', 'code', 'function', 'tutorial']):
            fallback_results.append({
                'content': f"Web search for '{query}' - Local Firecrawl server not running and external search unavailable. For Python programming help, consider checking official documentation at python.org or popular resources like Real Python, Python.org tutorials, or Stack Overflow.",
                'metadata': {
                    'title': f"Web Search: {query}",
                    'url': 'https://python.org',
                    'source': 'web_search',
                    'provider': 'fallback'
                },
                'score': 0.6
            })

        elif any(term in query.lower() for term in ['fastapi', 'django', 'flask', 'web', 'api']):
            fallback_results.append({
                'content': f"Web search for '{query}' - For web development and API frameworks, check the official documentation: FastAPI (fastapi.tiangolo.com), Django (djangoproject.com), or Flask (flask.palletsprojects.com).",
                'metadata': {
                    'title': f"Web Development: {query}",
                    'url': 'https://fastapi.tiangolo.com',
                    'source': 'web_search',
                    'provider': 'fallback'
                },
                'score': 0.6
            })

        else:
            fallback_results.append({
                'content': f"Web search for '{query}' - External web search services are currently unavailable. The local Firecrawl server is not running. You can still search within the loaded documentation using the main search functionality.",
                'metadata': {
                    'title': f"Search Results: {query}",
                    'url': '',
                    'source': 'web_search',
                    'provider': 'fallback'
                },
                'score': 0.5
            })

        logger.info(f"Fallback search provided {len(fallback_results)} results for query: {query}")
        return fallback_results[:max_results]

    def crawl_url(self, url: str) -> Optional[Dict]:
        """
        Crawl a specific URL and extract content

        Args:
            url: URL to crawl

        Returns:
            Extracted content and metadata
        """
        if not self.firecrawl_api_key or not HAS_REQUESTS:
            return None

        try:
            crawl_url = f"{self.firecrawl_base_url}/scrape"
            payload = {
                "url": url,
                "pageOptions": {
                    "includeMarkdown": True,
                    "fetchPageContent": True
                }
            }

            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(crawl_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                content_data = data.get('data', {})

                return {
                    'content': content_data.get('markdown', content_data.get('content', '')),
                    'metadata': {
                        'title': content_data.get('title', 'Crawled Content'),
                        'url': url,
                        'source': 'web_crawl',
                        'provider': 'firecrawl'
                    },
                    'success': True
                }

            else:
                logger.error(f"URL crawling failed with status: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"URL crawling error: {e}")
            return None

    def is_web_search_available(self) -> bool:
        """Check if web search is available"""
        return getattr(settings, 'enable_web_search', True) and (
            bool(self.local_firecrawl) or HAS_REQUESTS
        )

    def get_search_status(self) -> Dict[str, bool]:
        """Get status of search providers"""
        return {
            'web_search_enabled': getattr(settings, 'enable_web_search', True),
            'local_firecrawl_available': bool(self.local_firecrawl),
            'firecrawl_api_available': bool(self.firecrawl_api_key),
            'requests_available': HAS_REQUESTS,
            'overall_available': self.is_web_search_available()
        }

# Global instance
web_search_provider = WebSearchProvider()