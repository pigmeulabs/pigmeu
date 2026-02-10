"""
Goodreads.com book scraper using Playwright and BeautifulSoup.

This module:
- Searches Goodreads for books by title and author
- Extracts book ratings, reviews, and metadata
- Handles rate limiting and authentication (if needed)
- Implements retry logic and proxy rotation
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, quote_plus
import re

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from .extractors import (
    extract_text,
    extract_rating,
    extract_authors,
    clean_text,
    parse_html,
)
from .proxy_manager import (
    RateLimiter,
    ProxyRotator,
    UserAgentRotator,
    BackoffStrategy,
    RequestConfig,
)

logger = logging.getLogger(__name__)


class GoodreadsScraper:
    """Scraper for Goodreads.com book information."""
    
    API_BASE = "https://www.goodreads.com"
    SEARCH_PATH = "/search"
    
    # CSS selectors for Goodreads
    SELECTORS = {
        "book_title": "h3.bookTitle span[itemprop='name']",
        "book_author": "span.authorName span[itemprop='name']",
        "book_rating": "span.stars span[aria-label]",
        "book_ratings_count": "span.ratingsCount",
        "book_reviews_count": "span.reviewsCount",
        "book_pages": "span[itemprop='numberOfPages']",
        "book_language": "span[itemprop='inLanguage']",
        "book_publisher": "span[itemprop='publisher']",
        "book_publication_date": "span[itemprop='datePublished']",
        "book_description": "span[itemprop='description']",
    }
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        proxy_rotator: Optional[ProxyRotator] = None,
        user_agent_rotator: Optional[UserAgentRotator] = None,
    ):
        """Initialize Goodreads scraper.
        
        Args:
            rate_limiter: Rate limiter (creates default if None)
            proxy_rotator: Proxy rotator (optional)
            user_agent_rotator: User-Agent rotator (creates default if None)
        """
        self.rate_limiter = rate_limiter or RateLimiter(
            requests_per_second=0.3,  # Goodreads is stricter: 1 request per 3s
            requests_per_hour=60.0,
        )
        self.proxy_rotator = proxy_rotator or ProxyRotator()
        self.user_agent_rotator = user_agent_rotator or UserAgentRotator()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser and context."""
        logger.info("Initializing Playwright browser for Goodreads")
        playwright = await async_playwright().start()
        
        proxy = self.proxy_rotator.get_random()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        
        context_args = {
            "user_agent": self.user_agent_rotator.get_random(),
            "locale": "en-US",
        }
        
        if proxy:
            context_args["proxy"] = {"server": proxy}
        
        self.context = await self.browser.new_context(**context_args)
        logger.info("Goodreads browser initialized")
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Goodreads browser cleaned up")
    
    async def _fetch_page(
        self,
        url: str,
        config: RequestConfig,
        attempt: int = 0,
    ) -> Optional[str]:
        """Fetch page content with retries.
        
        Args:
            url: URL to fetch
            config: Request configuration
            attempt: Current attempt number
        
        Returns:
            HTML content or None
        """
        if not self.context:
            raise RuntimeError("Scraper not initialized. Call initialize() first.")
        
        try:
            await self.rate_limiter.wait()
            
            logger.info(f"Fetching Goodreads page (attempt {attempt + 1}): {url}")
            
            page = await self.context.new_page()
            
            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=config.timeout * 1000,
                )
                
                # Wait for content to load
                await page.wait_for_selector(
                    "div[role='main']",
                    timeout=config.timeout * 1000,
                )
                
                content = await page.content()
                logger.debug(f"Page fetched: {len(content)} bytes")
                
                return content
            
            finally:
                await page.close()
        
        except Exception as e:
            logger.warning(f"Fetch error (attempt {attempt + 1}): {e}")
            
            if attempt < config.max_retries:
                delay = BackoffStrategy.exponential(attempt)
                logger.info(f"Retrying after {delay:.1f}s")
                await asyncio.sleep(delay)
                return await self._fetch_page(url, config, attempt + 1)
            
            logger.error(f"Failed to fetch {url}")
            return None
    
    async def search(
        self,
        title: str,
        author: Optional[str] = None,
        config: Optional[RequestConfig] = None,
    ) -> List[Dict[str, Any]]:
        """Search Goodreads for books.
        
        Args:
            title: Book title to search
            author: Author name (optional, improves accuracy)
            config: Request configuration
        
        Returns:
            List of book results (title, author, rating, url, etc.)
        
        Example:
            >>> scraper = GoodreadsScraper()
            >>> await scraper.initialize()
            >>> results = await scraper.search("Clean Code", "Robert Martin")
            >>> await scraper.cleanup()
        """
        if not config:
            config = RequestConfig(url="")
        
        try:
            # Build search query
            query_parts = [title]
            if author:
                query_parts.append(author)
            search_query = " ".join(query_parts)
            
            # Build search URL
            search_url = f"{self.API_BASE}{self.SEARCH_PATH}?q={quote_plus(search_query)}"
            logger.info(f"Searching Goodreads: {search_query}")
            
            # Fetch search results
            html = await self._fetch_page(search_url, config)
            if not html:
                return []
            
            # Parse results
            soup = parse_html(html)
            results = self._parse_search_results(soup)
            
            logger.info(f"Found {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return []
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse Goodreads search results.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            List of book results
        """
        results = []
        
        try:
            # Find all book entries in search results
            book_elements = soup.find_all("div", class_=re.compile("bookRow"))
            
            for idx, book_elem in enumerate(book_elements[:10]):  # Limit to top 10
                try:
                    book_data = {}
                    
                    # Extract title
                    title_elem = book_elem.find("span", class_="bookTitle")
                    if title_elem:
                        title_link = title_elem.find("a")
                        if title_link:
                            book_data["title"] = title_link.get_text(strip=True)
                            book_data["goodreads_url"] = title_link.get("href")
                    
                    # Extract author
                    author_elem = book_elem.find("div", class_="authorName")
                    if author_elem:
                        author_link = author_elem.find("a")
                        if author_link:
                            book_data["author"] = author_link.get_text(strip=True)
                    
                    # Extract rating
                    rating_elem = book_elem.find("div", class_="stars")
                    if rating_elem:
                        rating_text = rating_elem.get("aria-label")
                        if rating_text:
                            book_data["rating"] = extract_rating(rating_text)
                    
                    # Extract ratings count
                    ratings_count_elem = book_elem.find("span", class_="ratingsCount")
                    if ratings_count_elem:
                        count_text = ratings_count_elem.get_text(strip=True)
                        match = re.search(r'(\d+(?:,\d+)?)', count_text)
                        if match:
                            book_data["ratings_count"] = int(match.group(1).replace(",", ""))
                    
                    # Extract reviews count
                    reviews_elem = book_elem.find("span", class_="reviewsCount")
                    if reviews_elem:
                        reviews_text = reviews_elem.get_text(strip=True)
                        match = re.search(r'(\d+(?:,\d+)?)', reviews_text)
                        if match:
                            book_data["reviews_count"] = int(match.group(1).replace(",", ""))
                    
                    if "title" in book_data:
                        results.append(book_data)
                        logger.debug(f"Result {idx + 1}: {book_data.get('title')}")
                
                except Exception as e:
                    logger.warning(f"Error parsing result {idx + 1}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return results
    
    async def get_book_details(
        self,
        goodreads_url: str,
        config: Optional[RequestConfig] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed book information from Goodreads product page.
        
        Args:
            goodreads_url: Goodreads book URL
            config: Request configuration
        
        Returns:
            Detailed book data or None
        """
        if not config:
            config = RequestConfig(url=goodreads_url)
        
        try:
            logger.info(f"Fetching book details: {goodreads_url}")
            
            html = await self._fetch_page(goodreads_url, config)
            if not html:
                return None
            
            soup = parse_html(html)
            book_data = self._parse_book_details(soup)
            book_data["goodreads_url"] = goodreads_url
            
            logger.info(f"Fetched details for: {book_data.get('title')}")
            return book_data
        
        except Exception as e:
            logger.error(f"Error getting book details: {e}", exc_info=True)
            return None
    
    def _parse_book_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse detailed book information.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Dictionary with book data
        """
        data = {}
        
        try:
            # Extract title
            title_elem = soup.find("h1", class_=re.compile("BookTitle"))
            data["title"] = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract author
            author_elem = soup.find("span", class_="ContributorLink")
            data["author"] = author_elem.get_text(strip=True) if author_elem else None
            
            # Extract rating
            rating_elem = soup.find("div", class_="RatingStatistics")
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                data["rating"] = extract_rating(rating_text)
            
            # Extract description
            desc_elem = soup.find("span", {"data-height": "130"})
            data["description"] = clean_text(desc_elem.get_text(strip=True)) if desc_elem else None
            
            # Extract publication date
            pub_elem = soup.find("span", {"data-testid": "publicationDate"})
            data["publication_date"] = pub_elem.get_text(strip=True) if pub_elem else None
            
            # Extract publisher
            pub_data_elem = soup.find("div", {"data-testid": "publicationInfo"})
            if pub_data_elem:
                pub_text = pub_data_elem.get_text(strip=True)
                # Format: "Publisher: Name Published: Date"
                match = re.search(r'Publisher:\s*([^\n]+)', pub_text)
                data["publisher"] = match.group(1).strip() if match else None
            
            # Extract pages
            pages_elem = soup.find(string=re.compile(r"\d+\s+pages"))
            if pages_elem:
                match = re.search(r'(\d+)\s+pages', pages_elem.get_text())
                data["pages"] = int(match.group(1)) if match else None
            
            # Extract language
            lang_elem = soup.find(string="Language:")
            if lang_elem:
                next_elem = lang_elem.find_next()
                data["language"] = next_elem.get_text(strip=True) if next_elem else None
            
            logger.debug(f"Parsed details for: {data.get('title')}")
        
        except Exception as e:
            logger.error(f"Error parsing details: {e}", exc_info=True)
        
        return data


# Singleton instance
_goodreads_scraper: Optional[GoodreadsScraper] = None


async def initialize_goodreads_scraper() -> GoodreadsScraper:
    """Initialize Goodreads scraper singleton.
    
    Returns:
        GoodreadsScraper instance
    """
    global _goodreads_scraper
    if _goodreads_scraper is None:
        _goodreads_scraper = GoodreadsScraper()
        await _goodreads_scraper.initialize()
    return _goodreads_scraper


async def search_goodreads(
    title: str,
    author: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Module-level helper to search Goodreads.
    
    Args:
        title: Book title
        author: Author name (optional)
    
    Returns:
        List of search results
    """
    scraper = await initialize_goodreads_scraper()
    return await scraper.search(title, author)
