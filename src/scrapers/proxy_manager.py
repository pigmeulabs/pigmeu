"""
Rate limiting, proxy rotation, and user-agent management for web scraping.

This module handles:
- Rate limiting (delays between requests)
- Proxy rotation (rotating through proxy list)
- User-Agent rotation (browser fingerprinting)
- Backoff strategies (exponential, linear)
"""

import asyncio
import random
import time
from typing import Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# Common desktop User-Agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


class RateLimiter:
    """Rate limiter to control request frequency.
    
    Implements token bucket algorithm for smooth rate limiting.
    """
    
    def __init__(
        self,
        requests_per_second: float = 0.5,
        requests_per_hour: float = 100.0,
    ):
        """Initialize rate limiter.
        
        Args:
            requests_per_second: Max requests per second (default: 0.5 = 1 req/2s)
            requests_per_hour: Max requests per hour (burst limit)
        """
        self.requests_per_second = requests_per_second
        self.requests_per_hour = requests_per_hour
        
        self.last_request_time = 0.0
        self.request_times: List[float] = []  # Track last hour of requests
        
        # Calculate min delay between requests
        self.min_delay = 1.0 / requests_per_second if requests_per_second > 0 else 0
    
    async def wait(self) -> None:
        """Wait if necessary to respect rate limit.
        
        This coroutine:
        1. Checks requests in last second
        2. Checks requests in last hour
        3. Sleeps if either limit exceeded
        """
        now = time.time()
        
        # Clean old entries (older than 1 hour)
        cutoff = now - 3600
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        # Check hour limit
        if len(self.request_times) >= self.requests_per_hour:
            # Wait until oldest request is >1 hour old
            wait_until = self.request_times[0] + 3600
            delay = wait_until - now
            if delay > 0:
                logger.warning(f"Hour limit reached. Waiting {delay:.1f}s")
                await asyncio.sleep(delay)
                now = time.time()
        
        # Check second limit
        delay_needed = self.min_delay - (now - self.last_request_time)
        if delay_needed > 0:
            await asyncio.sleep(delay_needed)
            now = time.time()
        
        # Record this request
        self.last_request_time = now
        self.request_times.append(now)
        
        logger.debug(f"Rate limit: {len(self.request_times)}/{self.requests_per_hour} requests this hour")
    
    async def reset(self) -> None:
        """Reset rate limiter (useful for testing)."""
        self.last_request_time = 0.0
        self.request_times = []


class ProxyRotator:
    """Rotate through proxy list for distributed requests.
    
    Helps avoid IP bans by distributing requests across multiple IPs.
    """
    
    def __init__(self, proxies: Optional[List[str]] = None):
        """Initialize proxy rotator.
        
        Args:
            proxies: List of proxy URLs (e.g., ["http://proxy1:8080", ...])
                    If None, no proxy will be used (local requests only)
        """
        self.proxies = proxies or []
        self.current_index = 0
    
    def get_next(self) -> Optional[str]:
        """Get next proxy in rotation.
        
        Returns:
            Proxy URL or None if no proxies configured
        """
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        logger.debug(f"Using proxy: {proxy}")
        return proxy
    
    def get_random(self) -> Optional[str]:
        """Get random proxy (better for parallel requests).
        
        Returns:
            Random proxy URL or None if no proxies configured
        """
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        logger.debug(f"Using proxy: {proxy}")
        return proxy
    
    def add_proxy(self, proxy: str) -> None:
        """Add a proxy to rotation.
        
        Args:
            proxy: Proxy URL
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.info(f"Added proxy: {proxy}")
    
    def remove_proxy(self, proxy: str) -> None:
        """Remove a proxy from rotation (useful if it fails).
        
        Args:
            proxy: Proxy URL
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.warning(f"Removed proxy: {proxy}")


class UserAgentRotator:
    """Rotate through User-Agent strings for browser fingerprinting.
    
    Helps avoid detection by rotating browser identities.
    """
    
    def __init__(self, user_agents: Optional[List[str]] = None):
        """Initialize User-Agent rotator.
        
        Args:
            user_agents: List of User-Agent strings
                        If None, uses predefined list
        """
        self.user_agents = user_agents or USER_AGENTS
    
    def get_random(self) -> str:
        """Get random User-Agent.
        
        Returns:
            Random User-Agent string
        """
        ua = random.choice(self.user_agents)
        logger.debug(f"Using User-Agent: {ua[:50]}...")
        return ua
    
    def add_user_agent(self, user_agent: str) -> None:
        """Add a User-Agent to pool.
        
        Args:
            user_agent: User-Agent string
        """
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)


class BackoffStrategy:
    """Backoff strategy for retries (exponential, linear, fixed).
    
    Implements different backoff strategies for failed requests.
    """
    
    @staticmethod
    def exponential(
        attempt: int,
        base: float = 2.0,
        max_delay: float = 300.0,
    ) -> float:
        """Calculate exponential backoff delay.
        
        Args:
            attempt: Attempt number (0-based)
            base: Base multiplier (default: 2.0)
            max_delay: Maximum delay in seconds
        
        Returns:
            Delay in seconds
        
        Example:
            >>> BackoffStrategy.exponential(0)
            1.0
            >>> BackoffStrategy.exponential(1)
            2.0
            >>> BackoffStrategy.exponential(2)
            4.0
        """
        delay = (base ** attempt) + random.uniform(0, 1)  # Add jitter
        return min(delay, max_delay)
    
    @staticmethod
    def linear(
        attempt: int,
        increment: float = 1.0,
        max_delay: float = 300.0,
    ) -> float:
        """Calculate linear backoff delay.
        
        Args:
            attempt: Attempt number (0-based)
            increment: Increment per attempt in seconds
            max_delay: Maximum delay in seconds
        
        Returns:
            Delay in seconds
        """
        delay = (attempt + 1) * increment + random.uniform(0, 1)
        return min(delay, max_delay)
    
    @staticmethod
    def fixed(delay: float = 5.0) -> float:
        """Fixed delay (no backoff).
        
        Args:
            delay: Fixed delay in seconds
        
        Returns:
            Delay in seconds
        """
        return delay + random.uniform(0, 1)


class RequestConfig:
    """Configuration for a scraping request.
    
    Groups all scraping settings in one object.
    """
    
    def __init__(
        self,
        url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_strategy: str = "exponential",
        use_proxy: bool = False,
        use_javascript: bool = False,
    ):
        """Initialize request configuration.
        
        Args:
            url: URL to scrape
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            backoff_strategy: "exponential", "linear", or "fixed"
            use_proxy: Whether to use proxy
            use_javascript: Whether to render JavaScript (requires Playwright)
        """
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_strategy = backoff_strategy
        self.use_proxy = use_proxy
        self.use_javascript = use_javascript
        self.headers: dict = {}
    
    def get_headers(self, user_agent: str) -> dict:
        """Get HTTP headers with User-Agent.
        
        Args:
            user_agent: User-Agent string
        
        Returns:
            Dictionary of headers
        """
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            **self.headers,
        }
