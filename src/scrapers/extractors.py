"""
HTML extraction utilities using BeautifulSoup and XPath patterns.

This module provides helper functions to parse HTML and extract
specific data from web pages using CSS selectors and BeautifulSoup.
"""

from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
import re


def extract_text(
    soup: BeautifulSoup,
    selector: str,
    strip: bool = True,
) -> Optional[str]:
    """Extract text content from HTML element.
    
    Args:
        soup: BeautifulSoup object
        selector: CSS selector (e.g., ".price", "#title")
        strip: Whether to strip whitespace
    
    Returns:
        Text content or None if not found
    
    Example:
        >>> title = extract_text(soup, "h1.product-title")
        >>> "Designing Data" in title
    """
    element = soup.select_one(selector)
    if element:
        text = element.get_text()
        return text.strip() if strip else text
    return None


def extract_email(text: str) -> Optional[str]:
    """Extract first email address from text.
    
    Args:
        text: Text content to search
    
    Returns:
        Email address or None if not found
    
    Example:
        >>> extract_email("Contact: hello@example.com")
        'hello@example.com'
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_price(text: str) -> Optional[float]:
    """Extract price from text.
    
    Args:
        text: Text containing price (e.g., "$19.99", "R$ 120,00")
    
    Returns:
        Price as float or None if not found
    
    Example:
        >>> extract_price("Price: $19.99")
        19.99
        >>> extract_price("$12,345.67")
        12345.67
    """
    # Remove common currency symbols and text
    text = re.sub(r'[^\d.,\s-]', '', text)
    
    # Handle different decimal separators
    if ',' in text and '.' in text:
        # If both exist, assume last is decimal
        if text.rindex(',') > text.rindex('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        # European format (1.000,00)
        text = text.replace('.', '').replace(',', '.')
    
    # Extract first number
    match = re.search(r'\d+\.?\d*', text)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def extract_isbn(text: str) -> Optional[str]:
    """Extract ISBN (10 or 13) from text.
    
    Args:
        text: Text containing ISBN
    
    Returns:
        ISBN without hyphens or None if not found
    
    Example:
        >>> extract_isbn("ISBN-13: 978-3-319-77206-2")
        '9783319772062'
    """
    # Match 10 or 13 digit ISBN (with optional hyphens)
    patterns = [
        r'(?:ISBN-?13[:]?\s*)?(?=[0-9]{13}$|(?=(?:[0-9]+[- ]){3})[- 0-9]{17}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{13}$)[0-9\-]+',
        r'\d{9}[\dXx]',  # ISBN-10
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Remove hyphens and spaces
            isbn = re.sub(r'[\s\-]', '', match.group(0))
            # Validate length
            if len(isbn) in [10, 13]:
                return isbn
    
    return None


def extract_date(text: str) -> Optional[str]:
    """Extract date from text.
    
    Args:
        text: Text containing date
    
    Returns:
        Date as YYYY-MM-DD string or None
    
    Example:
        >>> extract_date("Published on March 28, 2017")
        '2017-03-28'
    """
    # Common date patterns
    patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY or MM-DD-YYYY
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Try to parse and format
            try:
                import dateutil.parser as parser
                date_obj = parser.parse(text, fuzzy=True)
                return date_obj.strftime('%Y-%m-%d')
            except Exception:
                pass
    
    return None


def extract_rating(text: str) -> Optional[float]:
    """Extract rating from text.
    
    Args:
        text: Text containing rating (e.g., "4.5/5", "4.5 stars")
    
    Returns:
        Rating as float (0-10 scale) or None
    
    Example:
        >>> extract_rating("Rating: 4.5 out of 5 stars")
        4.5
    """
    # Look for decimal number
    match = re.search(r'(\d+\.?\d*)\s*(?:out of|\/|-)\s*(\d+\.?\d*)', text)
    if match:
        try:
            rating = float(match.group(1))
            max_rating = float(match.group(2))
            # Normalize to 5-star scale
            return (rating / max_rating) * 5
        except ValueError:
            pass
    
    # Just look for single decimal between 0-10
    match = re.search(r'(\d{1,2}\.?\d*)', text)
    if match:
        try:
            rating = float(match.group(1))
            if 0 <= rating <= 10:
                return rating
        except ValueError:
            pass
    
    return None


def extract_authors(text: str) -> List[str]:
    """Extract author names from text.
    
    Args:
        text: Text containing author information
    
    Returns:
        List of author names
    
    Example:
        >>> extract_authors("by Martin Kleppmann and Jane Smith")
        ['Martin Kleppmann', 'Jane Smith']
    """
    # Simple heuristic: split by common separators
    authors = []
    
    # Remove common prefixes
    text = re.sub(r'(?:by|author|authors?:?)\s+', '', text, flags=re.IGNORECASE)
    
    # Split by common separators
    parts = re.split(r'\s+(?:and|,|;|\|)\s+', text)
    
    for part in parts:
        # Clean up
        part = part.strip()
        # Check if it looks like a name (has at least 2 words or specific patterns)
        if part and len(part.split()) >= 1:
            authors.append(part)
    
    return authors[:5]  # Max 5 authors


def extract_language(text: str) -> Optional[str]:
    """Extract language code from text.
    
    Args:
        text: Text containing language info (e.g., "English", "English | Portuguese")
    
    Returns:
        Language code (e.g., "en", "pt") or None
    
    Example:
        >>> extract_language("Language: Portuguese | English")
        'pt'
    """
    # Language mappings
    language_map = {
        'english': 'en',
        'spanish': 'es',
        'french': 'fr',
        'german': 'de',
        'portuguese': 'pt',
        'chinese': 'zh',
        'japanese': 'ja',
        'russian': 'ru',
        'italian': 'it',
    }
    
    text_lower = text.lower()
    
    # Check each language
    for lang_name, lang_code in language_map.items():
        if lang_name in text_lower:
            return lang_code
    
    return None


def parse_html(html: str) -> BeautifulSoup:
    """Parse HTML string to BeautifulSoup object.
    
    Args:
        html: HTML string
    
    Returns:
        BeautifulSoup object using html.parser
    """
    return BeautifulSoup(html, 'html.parser')


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """Clean and normalize text.
    
    Args:
        text: Raw text
        max_length: Maximum length (truncate if longer)
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return text
