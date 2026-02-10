"""
Generic web scraper for various websites and sources.

This module:
- Scrapes arbitrary websites using Playwright
- Extracts common metadata patterns
- Handles different HTML structures
- Implements intelligent content extraction
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import re

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from .extractors import (
    extract_text,
    extract_email,
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


class GenericWebScraper:
    """Generic web scraper for arbitrary websites."""
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        proxy_rotator: Optional[ProxyRotator] = None,
        user_agent_rotator: Optional[UserAgentRotator] = None,
    ):
        """Initialize generic web scraper.
        
        Args:
            rate_limiter: Rate limiter (creates default if None)
            proxy_rotator: Proxy rotator (optional)
            user_agent_rotator: User-Agent rotator (creates default if None)
        """
        self.rate_limiter = rate_limiter or RateLimiter(
            requests_per_second=1.0,  # 1 request per second (generous)
            requests_per_hour=200.0,
        )
        self.proxy_rotator = proxy_rotator or ProxyRotator()
        self.user_agent_rotator = user_agent_rotator or UserAgentRotator()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser and context."""
        logger.info("Initializing generic web scraper")
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
        logger.info("Generic web scraper initialized")
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Generic web scraper cleaned up")
    
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
            
            logger.info(f"Fetching page (attempt {attempt + 1}): {url}")
            
            page = await self.context.new_page()
            
            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
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
    
    def _is_author_website(self, domain: str) -> bool:
        """Check if domain looks like author website.
        
        Args:
            domain: Domain name
        
        Returns:
            True if likely author website
        """
        # Common author website patterns
        author_patterns = [
            r"(?:www\.)?[a-z-]+\.com",  # author.com, author-name.com
            r"(?:www\.)?author[s]?\..*",  # authors.*, authors.*
            r".*\.io",  # tech author sites often use .io
            r".*\.dev",  # developer sites
        ]
        
        for pattern in author_patterns:
            if re.match(pattern, domain, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_metadata_from_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract common metadata from HTML.
        
        Args:
            soup: BeautifulSoup object
        
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        try:
            # Extract title (from multiple possible locations)
            title_elem = soup.find("meta", property="og:title")
            if title_elem:
                metadata["title"] = title_elem.get("content", "")
            else:
                title_tag = soup.find("title")
                if title_tag:
                    metadata["title"] = clean_text(title_tag.get_text())
            
            # Extract description
            desc_elem = soup.find("meta", property="og:description")
            if desc_elem:
                metadata["description"] = desc_elem.get("content", "")
            else:
                desc_meta = soup.find("meta", {"name": "description"})
                if desc_meta:
                    metadata["description"] = desc_meta.get("content", "")
            
            # Extract author (from common meta tags)
            author_elem = soup.find("meta", {"name": "author"})
            if author_elem:
                metadata["author"] = author_elem.get("content", "")
            
            # Extract publication date
            date_elem = soup.find("meta", property="article:published_time")
            if date_elem:
                metadata["publication_date"] = date_elem.get("content", "")
            
            # Extract main content
            # Try article, main, or div with id=content
            main_elem = soup.find("article") or soup.find("main") or soup.find("div", {"id": "content"})
            if main_elem:
                # Get first paragraph as summary
                first_p = main_elem.find("p")
                if first_p:
                    metadata["summary"] = clean_text(first_p.get_text())
            
            # Extract email
            email_text = soup.get_text()
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email_text)
            if emails:
                metadata["email"] = emails[0]  # First email
            
            # Extract social links
            social_links = {}
            for link in soup.find_all("a", href=re.compile(r'(twitter|linkedin|github|facebook)', re.IGNORECASE)):
                href = link.get("href", "")
                platform = re.search(r'(twitter|linkedin|github|facebook)', href, re.IGNORECASE)
                if platform:
                    social_links[platform.group(1).lower()] = href
            if social_links:
                metadata["social_links"] = social_links
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return metadata
    
    async def scrape(
        self,
        url: str,
        config: Optional[RequestConfig] = None,
        detect_author_site: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Scrape generic website.
        
        Args:
            url: URL to scrape
            config: Request configuration
            detect_author_site: Whether to apply author website detection
        
        Returns:
            Dictionary with extracted data or None
        
        Example:
            >>> scraper = GenericWebScraper()
            >>> await scraper.initialize()
            >>> data = await scraper.scrape("https://example.com/author")
            >>> await scraper.cleanup()
        """
        if not config:
            config = RequestConfig(url=url)
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Fetch page
            html = await self._fetch_page(url, config)
            if not html:
                return None
            
            # Parse HTML
            soup = parse_html(html)
            
            # Extract metadata
            data = self._extract_metadata_from_html(soup)
            data["url"] = url
            
            # Detect if author website
            if detect_author_site:
                domain = urlparse(url).netloc
                data["is_author_site"] = self._is_author_website(domain)
            
            logger.info(f"Scraped metadata: {data.get('title')}")
            return data
        
        except Exception as e:
            logger.error(f"Scraping error: {e}", exc_info=True)
            return None
    
    async def extract_links(
        self,
        url: str,
        link_pattern: Optional[str] = None,
        config: Optional[RequestConfig] = None,
    ) -> list:
        """Extract links from webpage.
        
        Args:
            url: URL to scrape
            link_pattern: Optional regex pattern to filter links
            config: Request configuration
        
        Returns:
            List of links found
        """
        if not config:
            config = RequestConfig(url=url)
        
        try:
            html = await self._fetch_page(url, config)
            if not html:
                return []
            
            soup = parse_html(html)
            links = []
            
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                
                # Filter by pattern if provided
                if link_pattern and not re.search(link_pattern, href):
                    continue
                
                # Skip certain links
                if href.startswith(("#", "javascript:", "mailto:")):
                    continue
                
                links.append(href)
            
            logger.info(f"Found {len(links)} links")
            return links
        
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []


# Singleton instance
_generic_scraper: Optional[GenericWebScraper] = None


async def initialize_generic_scraper() -> GenericWebScraper:
    """Initialize generic scraper singleton.
    
    Returns:
        GenericWebScraper instance
    """
    global _generic_scraper
    if _generic_scraper is None:
        _generic_scraper = GenericWebScraper()
        await _generic_scraper.initialize()
    return _generic_scraper


async def scrape_website(url: str) -> Optional[Dict[str, Any]]:
    """Module-level helper to scrape generic website.
    
    Args:
        url: Website URL
    
    Returns:
        Extracted metadata or None
    """
    scraper = await initialize_generic_scraper()
    return await scraper.scrape(url)
