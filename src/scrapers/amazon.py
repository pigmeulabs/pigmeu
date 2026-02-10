"""
Amazon.com book scraper using Playwright and BeautifulSoup.

This module:
- Navigates to Amazon book product pages
- Extracts 13 book metadata fields
- Handles dynamic content (JavaScript rendering)
- Implements rate limiting and retry logic
- Uses proxy rotation and User-Agent rotation
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import re

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from .extractors import (
    extract_text,
    extract_price,
    extract_isbn,
    extract_rating,
    extract_authors,
    extract_date,
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


class AmazonScraper:
    """Scraper for Amazon.com book product pages."""
    
    # CSS selectors for Amazon product pages
    SELECTORS = {
        "title": "span#productTitle",
        "authors": "a.a-link-normal.contributing-author-link",
        "price": "span.a-price-whole",
        "rating": "span[data-a-icon-star]",
        "reviews": "span[data-hook='social-proofing-faceout-review-count']",
        "isbn": "a:contains('ISBN')",  # Fallback: look in text
        "publisher": "a:contains('Publisher')",  # Fallback
        "pages": "span:contains('pages')",  # Fallback
        "language": "span:contains('Language')",  # Fallback
        "theme": "a.a-link-normal.a-color-tertiary",  # Category link
    }
    
    # ASIN extraction pattern (Amazon Standard Identification Number)
    ASIN_PATTERN = re.compile(r'/dp/([A-Z0-9]{10})')
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        proxy_rotator: Optional[ProxyRotator] = None,
        user_agent_rotator: Optional[UserAgentRotator] = None,
    ):
        """Initialize Amazon scraper.
        
        Args:
            rate_limiter: Rate limiter instance (creates default if None)
            proxy_rotator: Proxy rotator (optional)
            user_agent_rotator: User-Agent rotator (creates default if None)
        """
        self.rate_limiter = rate_limiter or RateLimiter(
            requests_per_second=0.5,  # 1 request every 2 seconds
            requests_per_hour=100.0,
        )
        self.proxy_rotator = proxy_rotator or ProxyRotator()
        self.user_agent_rotator = user_agent_rotator or UserAgentRotator()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser and context.
        
        This should be called before scraping to set up the browser.
        """
        logger.info("Initializing Playwright browser")
        playwright = await async_playwright().start()
        
        # Get proxy if configured
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
        logger.info("Browser and context initialized")
    
    async def cleanup(self) -> None:
        """Clean up browser and context resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser cleaned up")
    
    async def _fetch_page(
        self,
        url: str,
        config: RequestConfig,
        attempt: int = 0,
    ) -> Optional[str]:
        """Fetch page content with retries and backoff.
        
        Args:
            url: URL to fetch
            config: Request configuration
            attempt: Current attempt number (for recursion)
        
        Returns:
            HTML content or None if failed
        """
        if not self.context:
            raise RuntimeError("Scraper not initialized. Call initialize() first.")
        
        try:
            # Rate limit before request
            await self.rate_limiter.wait()
            
            logger.info(f"Fetching Amazon page (attempt {attempt + 1}): {url}")
            
            page = await self.context.new_page()
            
            try:
                # Navigate with timeout
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=config.timeout * 1000,
                )
                
                # Wait for product title to load
                await page.wait_for_selector(
                    self.SELECTORS["title"],
                    timeout=config.timeout * 1000,
                )
                
                # Get HTML content
                content = await page.content()
                logger.debug(f"Page fetched successfully: {len(content)} bytes")
                
                return content
            
            finally:
                await page.close()
        
        except Exception as e:
            logger.warning(f"Fetch error (attempt {attempt + 1}): {e}")
            
            # Retry logic
            if attempt < config.max_retries:
                delay = BackoffStrategy.exponential(attempt)
                logger.info(f"Retrying after {delay:.1f}s backoff")
                await asyncio.sleep(delay)
                return await self._fetch_page(url, config, attempt + 1)
            
            logger.error(f"Failed to fetch {url} after {config.max_retries} retries")
            return None
    
    def _extract_asin(self, url: str) -> Optional[str]:
        """Extract Amazon Standard Identification Number (ASIN) from URL.
        
        Args:
            url: Amazon product URL
        
        Returns:
            ASIN or None
        
        Example:
            >>> scraper._extract_asin("https://amazon.com/dp/B001234567")
            'B001234567'
        """
        match = self.ASIN_PATTERN.search(url)
        return match.group(1) if match else None
    
    def _parse_book_data(self, html: str) -> Dict[str, Any]:
        """Parse book metadata from HTML.
        
        Args:
            html: HTML content
        
        Returns:
            Dictionary with book data
        """
        soup = parse_html(html)
        data = {}
        
        try:
            # Extract title
            title_elem = soup.select_one(self.SELECTORS["title"])
            data["title"] = extract_text(soup, self.SELECTORS["title"]) or ""
            logger.debug(f"Title: {data['title']}")
            
            # Extract authors (multiple possible)
            authors_elems = soup.select(self.SELECTORS["authors"])
            if authors_elems:
                authors = [elem.get_text(strip=True) for elem in authors_elems]
                data["authors"] = extract_authors(" and ".join(authors))
            else:
                data["authors"] = []
            logger.debug(f"Authors: {data['authors']}")
            
            # Extract price (usually in span.a-price-whole)
            price_text = extract_text(soup, self.SELECTORS["price"])
            data["price"] = extract_price(price_text or "")
            logger.debug(f"Price: {data['price']}")
            
            # Extract rating
            rating_elem = soup.select_one(self.SELECTORS["rating"])
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                data["rating"] = extract_rating(rating_text)
            else:
                data["rating"] = None
            logger.debug(f"Rating: {data['rating']}")
            
            # Extract number of reviews
            reviews_text = extract_text(soup, self.SELECTORS["reviews"])
            data["reviews_count"] = 0
            if reviews_text:
                # Extract number from "1,234 reviews"
                match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                if match:
                    data["reviews_count"] = int(match.group(1).replace(",", ""))
            logger.debug(f"Reviews count: {data['reviews_count']}")
            
            # Extract ISBN (common pattern: "ISBN-10: 0123456789")
            isbn_text = " ".join([elem.get_text(strip=True) for elem in soup.find_all(string=re.compile(r'ISBN'))])
            data["isbn"] = extract_isbn(isbn_text)
            logger.debug(f"ISBN: {data['isbn']}")
            
            # Extract number of pages
            pages_text = extract_text(soup, self.SELECTORS["pages"])
            data["pages"] = None
            if pages_text:
                match = re.search(r'(\d+)\s*pages?', pages_text, re.IGNORECASE)
                if match:
                    data["pages"] = int(match.group(1))
            logger.debug(f"Pages: {data['pages']}")
            
            # Extract publication date (look for "Publication date: ...")
            pub_date_elem = soup.find(string=re.compile(r'Publication date'))
            data["publication_date"] = None
            if pub_date_elem:
                parent = pub_date_elem.find_parent()
                if parent:
                    date_text = parent.get_text(strip=True)
                    data["publication_date"] = extract_date(date_text)
            logger.debug(f"Publication date: {data['publication_date']}")
            
            # Extract publisher
            pub_elem = soup.find(string=re.compile(r'Publisher'))
            data["publisher"] = None
            if pub_elem:
                parent = pub_elem.find_parent()
                if parent:
                    next_text = parent.find_next()
                    if next_text:
                        data["publisher"] = clean_text(next_text.get_text())
            logger.debug(f"Publisher: {data['publisher']}")
            
            # Extract language (look for "Language: English")
            lang_elem = soup.find(string=re.compile(r'Language'))
            data["language"] = None
            if lang_elem:
                parent = lang_elem.find_parent()
                if parent:
                    lang_text = parent.get_text(strip=True)
                    data["language"] = extract_date(lang_text)  # Uses language extractor
            logger.debug(f"Language: {data['language']}")
            
            # Extract theme/category (usually in breadcrumbs)
            category_elems = soup.select("a.a-breadcrumb-link")
            data["theme"] = category_elems[-1].get_text(strip=True) if category_elems else None
            logger.debug(f"Theme: {data['theme']}")
            
        except Exception as e:
            logger.error(f"Error parsing book data: {e}", exc_info=True)
        
        return data
    
    async def scrape(
        self,
        amazon_url: str,
        config: Optional[RequestConfig] = None,
    ) -> Optional[Dict[str, Any]]:
        """Scrape book metadata from Amazon product page.
        
        Args:
            amazon_url: Amazon product URL (e.g., https://amazon.com/dp/B001234567)
            config: Request configuration (creates default if None)
        
        Returns:
            Dictionary with book data or None if failed
        
        Example:
            >>> scraper = AmazonScraper()
            >>> await scraper.initialize()
            >>> book = await scraper.scrape("https://amazon.com/dp/B001234567")
            >>> print(book['title'])
            >>> await scraper.cleanup()
        """
        if not config:
            config = RequestConfig(url=amazon_url)
        
        try:
            # Validate URL
            if "amazon.com" not in amazon_url.lower():
                logger.error(f"Invalid Amazon URL: {amazon_url}")
                return None
            
            # Fetch page
            html = await self._fetch_page(amazon_url, config)
            if not html:
                return None
            
            # Parse data
            data = self._parse_book_data(html)
            data["amazon_url"] = amazon_url
            data["asin"] = self._extract_asin(amazon_url)
            
            logger.info(f"Scraped book: {data.get('title')}")
            return data
        
        except Exception as e:
            logger.error(f"Scraping error: {e}", exc_info=True)
            return None


# Singleton instance for module-level access
_scraper_instance: Optional[AmazonScraper] = None


async def initialize_amazon_scraper() -> AmazonScraper:
    """Initialize and return Amazon scraper singleton.
    
    Returns:
        AmazonScraper instance
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = AmazonScraper()
        await _scraper_instance.initialize()
    return _scraper_instance


async def scrape_amazon_book(url: str) -> Optional[Dict[str, Any]]:
    """Module-level helper to scrape Amazon book.
    
    Args:
        url: Amazon product URL
    
    Returns:
        Book data or None
    """
    scraper = await initialize_amazon_scraper()
    return await scraper.scrape(url)
