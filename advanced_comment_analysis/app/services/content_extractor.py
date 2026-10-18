"""
AI-powered content extractor for identifying and extracting comments from web content
"""
import json
import time
import os
import re
from typing import Optional, List
import logging

from app.services.openai_client import call_openai

logger = logging.getLogger(__name__)


EXTRACTOR_SYSTEM_PROMPT = '''
You are an advanced content extraction AI. Your task is to analyze text content and identify user **comments, reviews, feedback, or opinions**.

You MUST return a valid JSON array with this structure:
[
  {
    "text": "extracted comment text",
    "source": "inferred source (e.g., review, comment, feedback, testimonial, forum_post)",
    "author": "author name if found, else null"
  },
  ...
]

Guidelines:
1. Extract ONLY actual user comments/reviews/feedback - skip navigation, headers, ads, technical content
2. Each comment should be a meaningful piece of user feedback (at least 5 words)
3. Remove duplicate or near-duplicate comments
4. Clean up HTML tags, URLs, and special characters from comments
5. Preserve the original meaning and tone
6. Limit extraction to max 20 most relevant comments
7. Return empty array [] if no comments found

Example:
Input text: "Product Review: Great quality! 5 stars. - Jane D. | Another user: Terrible customer service. Never again."
Output: [{"text": "Great quality!", "source": "review", "author": "Jane D."}, {"text": "Terrible customer service. Never again.", "source": "review", "author": "Another user"}]

Return ONLY valid JSON, nothing else.
'''


def build_extraction_prompt(content: str, context: str = "") -> str:
    """Build the extraction prompt with content"""
    prompt = EXTRACTOR_SYSTEM_PROMPT + f"\n\nContext: {context}\n\nContent to analyze:\n{content}"
    return prompt


def simple_extract_comments(text: str) -> List[dict]:
    """
    Fallback comment extraction using simple heuristics when AI is not available.
    Extracts sentences that look like comments/reviews.
    """
    comments = []
    
    # Split by common delimiters and sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Patterns that indicate a comment
    comment_patterns = [
        r'(?:review|comment|feedback|say|says|said|opinion|think|thought)',
        r'(?:great|good|amazing|excellent|terrible|bad|awful|love|hate|poor)',
        r'(?:stars?|✓|✗|recommend|not recommend)',
    ]
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Skip very short sentences
        if len(sentence) < 10 or len(sentence.split()) < 3:
            continue
        
        # Skip navigation/header text
        if any(skip in sentence.lower() for skip in ['click here', 'menu', 'navigation', 'subscribe', 'follow', 'like us']):
            continue
        
        # Check if sentence looks like a comment
        is_comment = any(
            re.search(pattern, sentence.lower()) 
            for pattern in comment_patterns
        )
        
        if is_comment or len(sentence) > 30:  # Include longer sentences that might be comments
            comments.append({
                'text': sentence,
                'source': 'extracted',
                'author': None
            })
    
    # Limit to top 20
    return comments[:20]


def extract_comments_from_text(text: str, context: str = "", max_retries: int = 2) -> Optional[List[dict]]:
    """
    Use AI to extract comments from text content
    
    Args:
        text: Text content to extract comments from
        context: Additional context about the source (e.g., "from a product review page")
        max_retries: Number of retries if JSON parsing fails
        
    Returns:
        List of extracted comments with structure: [{"text": str, "source": str, "author": str|null}, ...]
    """
    if not text or len(text.strip()) < 50:
        logger.warning('Text too short for extraction')
        return []
    
    # Limit text length to avoid token limits
    max_length = 5000
    if len(text) > max_length:
        text = text[:max_length]
    
    # Check if we have API key
    has_api_key = os.getenv("OPENAI_API_KEY") is not None
    
    if not has_api_key:
        # Use simple heuristic extraction when no API
        logger.info('Using heuristic extraction (no API key available)')
        return simple_extract_comments(text)
    
    prompt = build_extraction_prompt(text, context)
    attempt = 0
    
    while attempt < max_retries:
        try:
            raw = call_openai(prompt)
            
            if not raw:
                logger.warning('AI client returned no response, attempt %d', attempt)
                attempt += 1
                time.sleep(1)
                continue
            
            # Try to parse JSON response
            parsed = json.loads(raw)
            
            # Validate response is a list
            if not isinstance(parsed, list):
                logger.warning('Expected list response, got type: %s', type(parsed))
                attempt += 1
                time.sleep(1)
                continue
            
            # Validate and clean up each comment
            comments = []
            for item in parsed:
                if isinstance(item, dict) and 'text' in item:
                    comment = {
                        'text': str(item.get('text', '')).strip(),
                        'source': str(item.get('source', 'feedback')).strip(),
                        'author': item.get('author'),  # Can be None
                    }
                    # Only include non-empty comments
                    if comment['text'] and len(comment['text']) > 5:
                        comments.append(comment)
            
            logger.info('Extracted %d comments from content', len(comments))
            return comments
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning('Error parsing AI response, attempt %d: %s', attempt, str(e))
            attempt += 1
            time.sleep(1 + attempt)
            continue
    
    # If all retries failed, fall back to heuristic extraction
    logger.warning('Failed to extract comments with AI, using heuristic fallback')
    return simple_extract_comments(text)


def extract_comments_from_url(url: str, html_content: str) -> Optional[List[dict]]:
    """
    Extract comments from URL content
    
    Args:
        url: The URL (for context)
        html_content: The HTML/text content from the page
        
    Returns:
        List of extracted comments
    """
    context = f"from URL: {url}"
    return extract_comments_from_text(html_content, context)
