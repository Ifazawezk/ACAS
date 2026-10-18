"""
Web scraper service for extracting HTML content from URLs
"""
import requests
from typing import Optional
import logging
from html.parser import HTMLParser
import re

logger = logging.getLogger(__name__)


class TextExtractor(HTMLParser):
    """Extract text content from HTML while preserving some structure"""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.in_script = False
        self.in_style = False
        self.in_comment = False
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in ('script', 'style', 'noscript'):
            if tag == 'script':
                self.in_script = True
            elif tag == 'style':
                self.in_style = True
        # Add line breaks for block elements
        elif tag in ('p', 'div', 'article', 'section', 'header', 'footer', 'li', 'tr', 'td', 'th'):
            if self.text_content and self.text_content[-1] != '\n':
                self.text_content.append('\n')
                
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
        # Add line breaks after block elements
        if tag in ('p', 'div', 'article', 'section', 'header', 'footer', 'li', 'tr', 'td', 'th', 'h1', 'h2', 'h3'):
            if self.text_content and self.text_content[-1] != '\n':
                self.text_content.append('\n')
                
    def handle_data(self, data):
        if not (self.in_script or self.in_style):
            # Clean up whitespace but preserve intentional line breaks
            text = data.strip()
            if text:
                self.text_content.append(text + ' ')
                
    def get_text(self):
        # Join and clean up
        text = ''.join(self.text_content)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s+\n', '\n\n', text)
        return text.strip()


def fetch_url_content(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch HTML content from a URL
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string, or None if fetch failed
    """
    try:
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        
        return response.text
        
    except requests.exceptions.Timeout:
        logger.error(f'Timeout fetching URL: {url}')
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f'Connection error fetching URL: {url}')
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f'HTTP error fetching URL {url}: {e}')
        return None
    except Exception as e:
        logger.error(f'Error fetching URL {url}: {e}')
        return None


def extract_text_from_html(html_content: str) -> str:
    """
    Extract clean text from HTML content
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        Cleaned text content
    """
    try:
        parser = TextExtractor()
        parser.feed(html_content)
        return parser.get_text()
    except Exception as e:
        logger.error(f'Error parsing HTML: {e}')
        return ''


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text"""
    # Remove HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text
