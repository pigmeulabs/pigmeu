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
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import re
import unicodedata

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from .extractors import (
    extract_text,
    extract_price,
    extract_isbn,
    extract_rating,
    extract_authors,
    extract_date,
    extract_language,
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
        "title": "#productTitle",
        "authors": "#bylineInfo span.author a.a-link-normal",
        "rating_popover": "#acrPopover",
        "price_container": "#corePriceDisplay_desktop_feature_div",
        "ebook_price": "#tmm-grid-swatch-KINDLE span.slot-price span[aria-label]",
        "cover_image": "#landingImage",
        "breadcrumbs": "a.a-breadcrumb-link",
        "detail_bullets": "#detailBullets_feature_div li, #detailBulletsWrapper_feature_div li",
        "product_tables": "#productDetails_detailBullets_sections1 tr, #productDetails_techSpec_section_1 tr",
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
        self._playwright = None
    
    async def initialize(self) -> None:
        """Initialize Playwright browser and context.
        
        This should be called before scraping to set up the browser.
        """
        logger.info("Initializing Playwright browser")
        self._playwright = await async_playwright().start()
        
        # Get proxy if configured
        proxy = self.proxy_rotator.get_random()
        
        self.browser = await self._playwright.chromium.launch(
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
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
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
                    wait_until="domcontentloaded",
                    timeout=config.timeout * 1000,
                )
                
                # Give the page a moment to render dynamic product sections.
                await page.wait_for_timeout(1200)

                # Wait for a likely product selector, but don't fail hard if not found.
                try:
                    await page.wait_for_selector(self.SELECTORS["title"], timeout=min(config.timeout, 15) * 1000)
                except Exception:
                    logger.warning("Amazon product title selector not found for %s. Parsing best-effort HTML.", url)
                
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
        patterns = [
            re.compile(r"/dp/([A-Z0-9]{10})"),
            re.compile(r"/gp/product/([A-Z0-9]{10})"),
        ]
        for pattern in patterns:
            match = pattern.search(url)
            if match:
                return match.group(1)

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if "asin" in query and query["asin"]:
            candidate = str(query["asin"][0]).strip().upper()
            if re.fullmatch(r"[A-Z0-9]{10}", candidate):
                return candidate
        return None

    def _is_amazon_url(self, amazon_url: str) -> bool:
        try:
            host = (urlparse(amazon_url).netloc or "").lower()
        except Exception:
            return False

        if not host:
            return False
        if host.startswith("www."):
            host = host[4:]

        # Accept regional Amazon domains (amazon.com, amazon.com.br, amazon.co.uk, etc.).
        return host == "amazon.com" or host.startswith("amazon.") or ".amazon." in host

    @staticmethod
    def _normalize_label(text: str) -> str:
        cleaned = clean_text(str(text or ""))
        cleaned = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", cleaned)
        cleaned = cleaned.replace(":", " ")
        cleaned = "".join(ch for ch in unicodedata.normalize("NFKD", cleaned) if not unicodedata.combining(ch))
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    @staticmethod
    def _parse_number(text: str) -> Optional[float]:
        value = str(text or "")
        match = re.search(r"(\d+(?:[.,]\d+)?)", value)
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", "."))
        except Exception:
            return None

    @staticmethod
    def _parse_pages(text: str) -> Optional[int]:
        if not text:
            return None
        match = re.search(r"(\d{1,5})", str(text))
        if not match:
            return None
        try:
            return int(match.group(1))
        except Exception:
            return None

    @staticmethod
    def _pick_bullet_value(
        detail_map: Dict[str, str],
        terms: list[str],
        exclude_terms: Optional[list[str]] = None,
    ) -> Optional[str]:
        excludes = exclude_terms or []
        for term in terms:
            for label, value in detail_map.items():
                if term in label and not any(ex in label for ex in excludes):
                    text = clean_text(value)
                    if text:
                        return text
        return None

    def _extract_detail_map(self, soup: BeautifulSoup) -> Dict[str, str]:
        detail_map: Dict[str, str] = {}

        for li in soup.select(self.SELECTORS["detail_bullets"]):
            bold = li.select_one("span.a-text-bold")
            label = ""
            value = ""

            if bold:
                label = bold.get_text(" ", strip=True)
                sibling = bold.find_next_sibling("span")
                if sibling:
                    value = sibling.get_text(" ", strip=True)
                else:
                    line = li.get_text(" ", strip=True)
                    if ":" in line:
                        _, right = line.split(":", 1)
                        value = right.strip()
            else:
                line = li.get_text(" ", strip=True)
                if ":" in line:
                    left, right = line.split(":", 1)
                    label, value = left.strip(), right.strip()

            key = self._normalize_label(label)
            value_clean = clean_text(value)
            if key and value_clean and key not in detail_map:
                detail_map[key] = value_clean

        for row in soup.select(self.SELECTORS["product_tables"]):
            th = row.select_one("th")
            td = row.select_one("td")
            if not th or not td:
                continue
            key = self._normalize_label(th.get_text(" ", strip=True))
            value_clean = clean_text(td.get_text(" ", strip=True))
            if key and value_clean and key not in detail_map:
                detail_map[key] = value_clean

        return detail_map
    
    def _parse_book_data(self, html: str) -> Dict[str, Any]:
        """Parse book metadata from HTML.
        
        Args:
            html: HTML content
        
        Returns:
            Dictionary with book data
        """
        soup = parse_html(html)
        data: Dict[str, Any] = {}
        
        try:
            detail_map = self._extract_detail_map(soup)

            title = extract_text(soup, self.SELECTORS["title"]) or extract_text(soup, "#ebooksProductTitle") or ""
            title = clean_text(title)
            if not title:
                doc_title = clean_text((soup.title.get_text(" ", strip=True) if soup.title else "") or "")
                lowered_doc_title = doc_title.lower()
                is_error_title = "nao foi possivel encontrar esta pagina" in self._normalize_label(doc_title) or (
                    "sorry" in lowered_doc_title and "find that page" in lowered_doc_title
                )
                if doc_title and not is_error_title:
                    title = re.split(r"\|\s*amazon", doc_title, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            data["title"] = title
            logger.debug("Title: %s", data["title"])

            author_nodes = soup.select(self.SELECTORS["authors"]) or soup.select("#bylineInfo span.author a")
            dedup_authors = []
            for node in author_nodes:
                text = clean_text(node.get_text(" ", strip=True))
                if text and text.lower() not in {a.lower() for a in dedup_authors}:
                    dedup_authors.append(text)
            if not dedup_authors:
                byline_text = extract_text(soup, "#bylineInfo") or ""
                dedup_authors = extract_authors(byline_text)
            data["authors"] = dedup_authors
            logger.debug("Authors: %s", data["authors"])

            original_title = self._pick_bullet_value(
                detail_map,
                terms=["titulo original", "original title"],
            )
            language = self._pick_bullet_value(
                detail_map,
                terms=["idioma", "language"],
                exclude_terms=["idioma original", "original language"],
            )
            original_language = self._pick_bullet_value(
                detail_map,
                terms=["idioma original", "original language"],
            )
            edition = self._pick_bullet_value(detail_map, terms=["edicao", "edition"])
            pages_raw = self._pick_bullet_value(
                detail_map,
                terms=["numero de paginas", "print length", "page count", "pages"],
            )
            publisher_raw = self._pick_bullet_value(detail_map, terms=["editora", "publisher"])
            publication_date_raw = self._pick_bullet_value(
                detail_map,
                terms=["data da publicacao", "publication date"],
            )
            asin_bullet = self._pick_bullet_value(detail_map, terms=["asin"])
            isbn_10_raw = self._pick_bullet_value(detail_map, terms=["isbn-10", "isbn 10"])
            isbn_13_raw = self._pick_bullet_value(detail_map, terms=["isbn-13", "isbn 13"])

            rating = None
            rating_pop = soup.select_one(self.SELECTORS["rating_popover"])
            if rating_pop:
                rating = self._parse_number(rating_pop.get("title") or rating_pop.get_text(" ", strip=True))
            if rating is None:
                rating = extract_rating(extract_text(soup, "span[data-hook='rating-out-of-text']") or "")

            price_book = None
            whole = soup.select_one("#corePriceDisplay_desktop_feature_div span.priceToPay span.a-price-whole")
            fraction = soup.select_one("#corePriceDisplay_desktop_feature_div span.priceToPay span.a-price-fraction")
            if whole:
                assembled = f"{whole.get_text(strip=True)}.{fraction.get_text(strip=True) if fraction else '00'}"
                price_book = extract_price(assembled)
            if price_book is None:
                offscreen = extract_text(soup, "#corePriceDisplay_desktop_feature_div span.a-price .a-offscreen")
                price_book = extract_price(offscreen or "")

            price_ebook = None
            ebook_node = soup.select_one(self.SELECTORS["ebook_price"])
            if ebook_node:
                price_ebook = extract_price((ebook_node.get("aria-label") or ebook_node.get_text(" ", strip=True)))

            cover_image_url = None
            cover_img = soup.select_one(self.SELECTORS["cover_image"])
            if cover_img:
                cover_image_url = cover_img.get("data-old-hires") or cover_img.get("src")
                if not cover_image_url:
                    dynamic_image_raw = cover_img.get("data-a-dynamic-image")
                    if dynamic_image_raw:
                        try:
                            dynamic_data = json.loads(dynamic_image_raw)
                            if isinstance(dynamic_data, dict) and dynamic_data:
                                cover_image_url = next(iter(dynamic_data.keys()))
                        except Exception:
                            cover_image_url = None

            theme = None
            category_elems = soup.select(self.SELECTORS["breadcrumbs"])
            if category_elems:
                theme = clean_text(category_elems[-1].get_text(" ", strip=True))

            publication_date = extract_date(publication_date_raw or "") or clean_text(publication_date_raw or "")
            language = extract_language(language or "") or clean_text(language or "")
            original_language = extract_language(original_language or "") or clean_text(original_language or "")

            isbn_10 = extract_isbn(isbn_10_raw or "") or clean_text(isbn_10_raw or "")
            isbn_13 = extract_isbn(isbn_13_raw or "") or clean_text(isbn_13_raw or "")
            if isbn_13 and len(re.sub(r"[^0-9]", "", isbn_13)) != 13:
                isbn_13 = None
            if isbn_10 and len(re.sub(r"[^0-9X]", "", isbn_10.upper())) != 10:
                isbn_10 = None

            pages = self._parse_pages(pages_raw or "")
            publisher = clean_text(publisher_raw or "")
            asin = clean_text(asin_bullet or "")

            data.update(
                {
                    "original_title": original_title,
                    "title_original": original_title,
                    "language": language,
                    "original_language": original_language,
                    "lang_edition": language,
                    "lang_original": original_language,
                    "edition": edition,
                    "average_rating": rating,
                    "rating": rating,
                    "amazon_rating": rating,
                    "pages": pages,
                    "publisher": publisher,
                    "publication_date": publication_date,
                    "pub_date": publication_date,
                    "asin": asin,
                    "isbn_10": isbn_10,
                    "isbn_13": isbn_13,
                    "isbn": isbn_13 or isbn_10,
                    "price_book": price_book,
                    "price": price_book,
                    "price_physical": price_book,
                    "price_ebook": price_ebook,
                    "ebook_price": price_ebook,
                    "cover_image_url": cover_image_url,
                    "theme": theme,
                }
            )
            data = {key: value for key, value in data.items() if value not in (None, "", [])}
        
        except Exception as e:
            logger.error(f"Error parsing book data: {e}", exc_info=True)
        
        return data

    @staticmethod
    def _looks_like_error_or_block_page(html: str) -> bool:
        text = (html or "").lower()
        markers = [
            "não foi possível encontrar esta página",
            "nao foi possivel encontrar esta pagina",
            "sorry! we couldn't find that page",
            "robot check",
            "captchacharacters",
            "api-services-support@amazon.com",
        ]
        return any(marker in text for marker in markers)
    
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
            if not self._is_amazon_url(amazon_url):
                logger.error(f"Invalid Amazon URL: {amazon_url}")
                return None
            
            # Fetch page
            html = await self._fetch_page(amazon_url, config)
            if not html:
                return None
            if self._looks_like_error_or_block_page(html):
                logger.warning("Amazon returned error/blocked page for URL: %s", amazon_url)
                return None
            
            # Parse data
            data = self._parse_book_data(html)
            data["amazon_url"] = amazon_url
            data["asin"] = data.get("asin") or self._extract_asin(amazon_url)
            if not data.get("title"):
                logger.warning("Amazon scrape produced no title for URL: %s", amazon_url)
                return None
            
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
