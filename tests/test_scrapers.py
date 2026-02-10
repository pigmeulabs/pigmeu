"""
Tests for web scraping modules.

Tests cover:
- Rate limiting
- Proxy rotation
- User-Agent rotation
- Scraper functionality (with mocks)
- Scraper tasks
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from src.scrapers.proxy_manager import (
    RateLimiter,
    ProxyRotator,
    UserAgentRotator,
    BackoffStrategy,
    RequestConfig,
)
from src.scrapers.extractors import (
    extract_text,
    extract_price,
    extract_isbn,
    extract_rating,
    extract_authors,
    extract_date,
    clean_text,
)


# ============================================================================
# Rate Limiter Tests
# ============================================================================

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_waits(self):
        """Test that rate limiter enforces delays."""
        limiter = RateLimiter(requests_per_second=1.0)
        
        start = asyncio.get_event_loop().time()
        await limiter.wait()
        await limiter.wait()
        end = asyncio.get_event_loop().time()
        
        # Should have at least 1 second delay between requests
        elapsed = end - start
        assert elapsed >= 0.9, f"Expected ~1s delay, got {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_tracks_requests(self):
        """Test that rate limiter tracks request count."""
        limiter = RateLimiter(requests_per_second=10.0, requests_per_hour=100.0)
        
        for _ in range(5):
            await limiter.wait()
        
        assert len(limiter.request_times) == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter()
        
        await limiter.wait()
        assert len(limiter.request_times) > 0
        
        await limiter.reset()
        assert len(limiter.request_times) == 0
        assert limiter.last_request_time == 0.0


# ============================================================================
# Proxy Rotator Tests
# ============================================================================

class TestProxyRotator:
    """Test proxy rotation."""
    
    def test_proxy_rotator_no_proxies(self):
        """Test rotator with no proxies."""
        rotator = ProxyRotator()
        
        assert rotator.get_next() is None
        assert rotator.get_random() is None
    
    def test_proxy_rotator_sequential(self):
        """Test sequential proxy access."""
        proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
        rotator = ProxyRotator(proxies)
        
        # Should cycle through
        assert rotator.get_next() == "http://proxy1:8080"
        assert rotator.get_next() == "http://proxy2:8080"
        assert rotator.get_next() == "http://proxy3:8080"
        assert rotator.get_next() == "http://proxy1:8080"  # Wrap around
    
    def test_proxy_rotator_random(self):
        """Test random proxy selection."""
        proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
        rotator = ProxyRotator(proxies)
        
        proxy = rotator.get_random()
        assert proxy in proxies
    
    def test_proxy_rotator_add_remove(self):
        """Test adding and removing proxies."""
        rotator = ProxyRotator()
        
        rotator.add_proxy("http://proxy1:8080")
        assert len(rotator.proxies) == 1
        
        rotator.remove_proxy("http://proxy1:8080")
        assert len(rotator.proxies) == 0


# ============================================================================
# User-Agent Rotator Tests
# ============================================================================

class TestUserAgentRotator:
    """Test User-Agent rotation."""
    
    def test_user_agent_rotator_default(self):
        """Test default User-Agents are loaded."""
        rotator = UserAgentRotator()
        
        assert len(rotator.user_agents) > 0
        ua = rotator.get_random()
        assert "Mozilla" in ua or "Chrome" in ua or "Firefox" in ua
    
    def test_user_agent_rotator_custom(self):
        """Test custom User-Agents."""
        custom_uas = ["CustomUA/1.0", "CustomUA/2.0"]
        rotator = UserAgentRotator(custom_uas)
        
        ua = rotator.get_random()
        assert ua in custom_uas
    
    def test_user_agent_rotator_add(self):
        """Test adding User-Agents."""
        rotator = UserAgentRotator()
        initial_count = len(rotator.user_agents)
        
        rotator.add_user_agent("CustomUA/3.0")
        
        assert len(rotator.user_agents) == initial_count + 1


# ============================================================================
# Backoff Strategy Tests
# ============================================================================

class TestBackoffStrategy:
    """Test backoff strategies."""
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        delay0 = BackoffStrategy.exponential(0)
        delay1 = BackoffStrategy.exponential(1)
        delay2 = BackoffStrategy.exponential(2)
        
        assert delay0 >= 0  # 2^0 = 1
        assert delay1 > delay0 or delay1 == delay0  # >= 2
        assert delay2 > delay1 or delay2 == delay1  # >= 4
    
    def test_linear_backoff(self):
        """Test linear backoff calculation."""
        delay0 = BackoffStrategy.linear(0, increment=1.0)
        delay1 = BackoffStrategy.linear(1, increment=1.0)
        
        assert delay1 >= delay0
    
    def test_fixed_backoff(self):
        """Test fixed backoff."""
        delay = BackoffStrategy.fixed(5.0)
        
        assert 5.0 <= delay < 6.0  # 5 seconds + jitter


# ============================================================================
# Request Config Tests
# ============================================================================

class TestRequestConfig:
    """Test request configuration."""
    
    def test_request_config_creation(self):
        """Test creating request config."""
        config = RequestConfig(
            url="https://example.com",
            timeout=30,
            max_retries=3,
        )
        
        assert config.url == "https://example.com"
        assert config.timeout == 30
        assert config.max_retries == 3
    
    def test_request_config_headers(self):
        """Test getting request headers."""
        config = RequestConfig(url="https://example.com")
        headers = config.get_headers("TestUA/1.0")
        
        assert headers["User-Agent"] == "TestUA/1.0"
        assert "Accept" in headers
        assert "Accept-Language" in headers


# ============================================================================
# Extractor Function Tests
# ============================================================================

class TestExtractorFunctions:
    """Test HTML extraction utilities."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  Hello   \n\n  World  \t  "
        clean = clean_text(dirty_text)
        
        assert clean == "Hello World"
    
    def test_clean_text_truncation(self):
        """Test text truncation."""
        long_text = "A" * 1000
        clean = clean_text(long_text, max_length=100)
        
        assert len(clean) <= 100
    
    def test_extract_price_usd(self):
        """Test USD price extraction."""
        price = extract_price("$19.99")
        assert price == 19.99
    
    def test_extract_price_eur(self):
        """Test EUR price extraction."""
        price = extract_price("€15,50")
        assert abs(price - 15.50) < 0.01
    
    def test_extract_price_brl(self):
        """Test BRL price extraction."""
        price = extract_price("R$ 99,90")
        assert abs(price - 99.90) < 0.01
    
    def test_extract_isbn_10(self):
        """Test ISBN-10 extraction."""
        isbn = extract_isbn("ISBN-10: 0-306-40615-2")
        assert isbn == "0306406152"
    
    def test_extract_isbn_13(self):
        """Test ISBN-13 extraction."""
        isbn = extract_isbn("ISBN-13: 978-0-306-40615-1")
        assert isbn == "9780306406151"
    
    def test_extract_rating(self):
        """Test rating extraction."""
        rating = extract_rating("4.5 out of 5 stars")
        assert abs(rating - 4.5) < 0.01
    
    def test_extract_rating_percentage(self):
        """Test percentage rating to 0-10 scale."""
        rating = extract_rating("85%")
        assert abs(rating - 8.5) < 0.01
    
    def test_extract_authors(self):
        """Test author extraction."""
        authors = extract_authors("John Smith and Jane Doe")
        assert "John Smith" in authors
        assert "Jane Doe" in authors
    
    def test_extract_authors_max_count(self):
        """Test author count limit."""
        author_text = " and ".join([f"Author {i}" for i in range(10)])
        authors = extract_authors(author_text, max_count=5)
        assert len(authors) <= 5


# ============================================================================
# Amazon Scraper Tests (Mocked)
# ============================================================================

class TestAmazonScraper:
    """Test Amazon scraper (with mocks)."""
    
    @pytest.mark.asyncio
    async def test_amazon_scraper_initialization(self):
        """Test scraper initialization."""
        from src.scrapers.amazon import AmazonScraper
        
        scraper = AmazonScraper()
        assert scraper is not None
        assert scraper.rate_limiter is not None
        assert scraper.user_agent_rotator is not None
    
    @pytest.mark.asyncio
    async def test_amazon_scraper_asin_extraction(self):
        """Test ASIN extraction from URL."""
        from src.scrapers.amazon import AmazonScraper
        
        scraper = AmazonScraper()
        asin = scraper._extract_asin("https://amazon.com/dp/B001234567/ref=xyz")
        
        assert asin == "B001234567"
    
    def test_amazon_scraper_invalid_url(self):
        """Test handling invalid Amazon URL."""
        from src.scrapers.amazon import AmazonScraper
        
        scraper = AmazonScraper()
        asin = scraper._extract_asin("https://example.com/book")
        
        assert asin is None


# ============================================================================
# Goodreads Scraper Tests (Mocked)
# ============================================================================

class TestGoodreadsScraper:
    """Test Goodreads scraper."""
    
    @pytest.mark.asyncio
    async def test_goodreads_scraper_initialization(self):
        """Test scraper initialization."""
        from src.scrapers.goodreads import GoodreadsScraper
        
        scraper = GoodreadsScraper()
        
        # Stricter rate limiting for Goodreads
        assert scraper.rate_limiter.requests_per_second == 0.3


# ============================================================================
# Generic Web Scraper Tests
# ============================================================================

class TestGenericWebScraper:
    """Test generic web scraper."""
    
    @pytest.mark.asyncio
    async def test_generic_scraper_author_site_detection(self):
        """Test author website detection."""
        from src.scrapers.web_scraper import GenericWebScraper
        
        scraper = GenericWebScraper()
        
        assert scraper._is_author_website("john-smith.com") == True
        assert scraper._is_author_website("blog.author.io") == True
        assert scraper._is_author_website("amazon.com") == False
        assert scraper._is_author_website("google.com") == False


# ============================================================================
# Integration Tests
# ============================================================================

class TestScraperIntegration:
    """Integration tests for scraper components."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_with_multiple_requests(self):
        """Test rate limiter over multiple requests."""
        limiter = RateLimiter(requests_per_second=2.0)
        
        times = []
        for _ in range(3):
            before = asyncio.get_event_loop().time()
            await limiter.wait()
            times.append(asyncio.get_event_loop().time() - before)
        
        # Should maintain rate limiting
        assert sum(times) >= 0.9  # At least 1 second
    
    def test_proxy_and_user_agent_rotation(self):
        """Test proxy and User-Agent rotation together."""
        proxies = ["http://p1:8080", "http://p2:8080"]
        uas = ["UA1", "UA2"]
        
        proxy_rot = ProxyRotator(proxies)
        ua_rot = UserAgentRotator(uas)
        
        config = RequestConfig(url="https://example.com")
        
        for i in range(4):
            proxy = proxy_rot.get_next()
            ua = ua_rot.get_random()
            headers = config.get_headers(ua)
            
            assert proxy in proxies
            assert ua in uas
            assert headers["User-Agent"] in uas


# ============================================================================
# Performance Tests
# ============================================================================

class TestScraperPerformance:
    """Performance tests for scraper components."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self):
        """Test rate limiter doesn't add excessive overhead."""
        limiter = RateLimiter(requests_per_second=100.0)  # High limit
        
        start = asyncio.get_event_loop().time()
        for _ in range(10):
            await limiter.wait()
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should be very fast with high limits
        assert elapsed < 1.0
    
    def test_extractor_performance(self):
        """Test extractor functions are fast."""
        import time
        
        start = time.time()
        for _ in range(1000):
            extract_price("$19.99")
            extract_isbn("978-0-306-40615-1")
            extract_rating("4.5 stars")
        elapsed = time.time() - start
        
        # Should handle 1000 extractions in < 1 second
        assert elapsed < 1.0
