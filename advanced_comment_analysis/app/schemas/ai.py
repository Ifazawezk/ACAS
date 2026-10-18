from pydantic import BaseModel, Field, validator
from typing import Optional, List


class AIAnalysis(BaseModel):
    emotion: str = Field(..., description="Emotion expressed in the comment, e.g., angry, sad, neutral")
    intent: str = Field(..., description="User intent, e.g., complaint, question, praise")
    priority: str = Field(..., description='Priority: Low, Medium, High, Critical')
    needs_ticket: bool
    suggested_response: Optional[str]
    confidence: float = Field(..., ge=0.0, le=1.0)

    @validator('priority')
    def priority_must_be_valid(cls, v):
        allowed = {"Low", "Medium", "High", "Critical"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v


class AnalyzeRequest(BaseModel):
    """Request to analyze a comment"""
    content: str = Field(..., min_length=1, description="Comment text to analyze")
    source: Optional[str] = Field(default="manual", description="Source of the comment")


class URLScrapeRequest(BaseModel):
    """Request to scrape and extract comments from a URL"""
    url: str = Field(..., min_length=1, description="URL to scrape for comments")
    context: Optional[str] = Field(default=None, description="Additional context about the page (e.g., 'product reviews')")


class ExtractedComment(BaseModel):
    """A comment extracted from a URL"""
    text: str = Field(..., description="The comment text")
    source: Optional[str] = Field(default="extracted", description="Source type (e.g., review, comment, feedback)")
    author: Optional[str] = Field(default=None, description="Author name if available")


class URLScrapeResponse(BaseModel):
    """Response from URL scraping and comment extraction"""
    url: str = Field(..., description="The URL that was scraped")
    success: bool = Field(..., description="Whether scraping was successful")
    comments_count: int = Field(..., description="Number of comments extracted")
    comments: List[ExtractedComment] = Field(default_factory=list, description="List of extracted comments")
    error: Optional[str] = Field(default=None, description="Error message if scraping failed")
