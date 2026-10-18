from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.services.ai_service import analyze_text
from app.services.comment_ticket_service import save_comment_and_analysis
from app.services.web_scraper import fetch_url_content, extract_text_from_html
from app.services.content_extractor import extract_comments_from_url
from app.database.session import get_db
from app.schemas.ai import (
    AIAnalysis, 
    AnalyzeRequest, 
    URLScrapeRequest, 
    URLScrapeResponse,
    ExtractedComment
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze", response_model=AIAnalysis)
def analyze_comment(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    logger = logging.getLogger(__name__)
    content = payload.content.strip() if payload.content else ""
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    try:
        analysis = analyze_text(content)
    except Exception as e:
        logger.exception("AI analysis exception")
        raise HTTPException(status_code=500, detail="AI analysis error")

    if not analysis:
        raise HTTPException(status_code=500, detail="AI analysis failed")

    # persist results; make best-effort to save and log failures without failing the request
    try:
        comment, ticket = save_comment_and_analysis(db, content, analysis.dict(), source=payload.source)
    except Exception:
        logger.exception("Failed to save analyzed comment")

    return analysis


@router.post("/scrape-url", response_model=URLScrapeResponse)
def scrape_url_for_comments(payload: URLScrapeRequest, db: Session = Depends(get_db)):
    """
    Scrape a URL and extract comments/reviews/feedback using AI.
    
    Supports various website formats - the AI intelligently identifies comments
    regardless of HTML structure.
    """
    logger = logging.getLogger(__name__)
    url = payload.url.strip() if payload.url else ""
    
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    
    try:
        # Fetch the URL
        logger.info(f"Fetching content from URL: {url}")
        html_content = fetch_url_content(url)
        
        if not html_content:
            return URLScrapeResponse(
                url=url,
                success=False,
                comments_count=0,
                comments=[],
                error="Failed to fetch URL content. Check the URL and try again."
            )
        
        # Extract text from HTML
        text_content = extract_text_from_html(html_content)
        
        if not text_content or len(text_content) < 50:
            return URLScrapeResponse(
                url=url,
                success=False,
                comments_count=0,
                comments=[],
                error="No significant text content found at URL"
            )
        
        # Extract comments using AI
        logger.info("Extracting comments from content using AI")
        extracted = extract_comments_from_url(url, text_content)
        
        if not extracted:
            return URLScrapeResponse(
                url=url,
                success=True,
                comments_count=0,
                comments=[],
                error=None
            )
        
        # Convert to ExtractedComment objects
        comments = [
            ExtractedComment(
                text=item['text'],
                source=item.get('source', 'extracted'),
                author=item.get('author')
            )
            for item in extracted
        ]
        
        # Optionally save extracted comments to database for analysis
        try:
            for comment in comments:
                save_comment_and_analysis(
                    db, 
                    comment.text, 
                    {
                        'emotion': 'neutral',  # Will be analyzed when added to queue
                        'intent': 'feedback',
                        'priority': 'Low',
                        'needs_ticket': False,
                        'suggested_response': None,
                        'confidence': 0.0
                    },
                    source=f"web_scrape:{url}"
                )
        except Exception as e:
            logger.exception("Failed to save scraped comments to database")
            # Don't fail the request - still return the comments
        
        return URLScrapeResponse(
            url=url,
            success=True,
            comments_count=len(comments),
            comments=comments,
            error=None
        )
        
    except Exception as e:
        logger.exception(f"Error scraping URL: {url}")
        return URLScrapeResponse(
            url=url,
            success=False,
            comments_count=0,
            comments=[],
            error=f"Error: {str(e)}"
        )
