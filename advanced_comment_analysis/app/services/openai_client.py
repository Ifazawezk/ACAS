import os
import time
import json
import re
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Note: read the key at call time so tests / local runs can override env after import
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def analyze_sentiment_locally(text: str) -> dict:
    """
    Perform local NLP-based sentiment analysis using VADER.
    Returns a dictionary with emotion, intent, priority, confidence, and response.
    """
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
        import nltk
        
        # Ensure VADER lexicon is downloaded
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        
        sia = SentimentIntensityAnalyzer()
        scores = sia.polarity_scores(text)
        compound = scores['compound']  # ranges from -1 (negative) to 1 (positive)
        
    except Exception:
        # Fallback: simple word-based analysis if NLTK fails
        compound = simple_sentiment_score(text)
    
    # Determine emotion from compound score
    text_lower = text.lower()
    
    if compound >= 0.5:
        emotion = "joy"
        suggested_response = "Thank you for the positive feedback! We appreciate your support."
    elif compound >= 0.1:
        emotion = "neutral"
        suggested_response = "Thanks for your input. We'll consider your feedback."
    elif compound >= -0.3:
        emotion = "sadness"
        suggested_response = "We're sorry you had this experience. We're working to improve."
    else:
        emotion = "anger"
        suggested_response = "We sincerely apologize for this issue. Our team will investigate immediately."
    
    # Detect intent from keywords
    intent = detect_intent(text_lower)
    
    # Determine priority based on emotion and intent
    priority = determine_priority(emotion, intent)
    
    # Confidence: higher for strong emotions, lower for neutral
    confidence = min(0.95, 0.5 + abs(compound) * 0.45)
    
    # Decide if ticket is needed
    needs_ticket = (
        emotion in ["anger", "sadness"] or 
        intent in ["complaint", "bug_report"] or
        priority in ["High", "Critical"]
    )
    
    return {
        "emotion": emotion,
        "intent": intent,
        "priority": priority,
        "needs_ticket": needs_ticket,
        "suggested_response": suggested_response,
        "confidence": round(confidence, 2),
    }


def simple_sentiment_score(text: str) -> float:
    """Fallback sentiment scoring using simple word lists"""
    text_lower = text.lower()
    
    positive_words = {"good", "great", "excellent", "amazing", "love", "perfect", "best", "awesome"}
    negative_words = {"bad", "terrible", "awful", "hate", "worst", "poor", "horrible", "broken"}
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total


def detect_intent(text_lower: str) -> str:
    """Detect intent from comment text using keyword matching"""
    
    complaint_keywords = ["bad", "terrible", "awful", "broken", "doesn't work", "issue", "problem", "error", "bug", "hate", "worst", "poor", "wrong"]
    praise_keywords = ["good", "great", "excellent", "amazing", "love", "perfect", "best", "awesome", "thank", "appreciate"]
    bug_keywords = ["bug", "error", "crash", "broken", "doesn't work", "fails", "issue", "glitch"]
    suggestion_keywords = ["suggest", "could", "should", "would be nice", "feature", "why not", "improvement"]
    question_keywords = ["?", "what", "how", "why", "where", "when", "can you", "could you"]
    
    # Check for bug reports first (most specific)
    if any(kw in text_lower for kw in bug_keywords):
        return "bug_report"
    
    # Check for complaints
    if any(kw in text_lower for kw in complaint_keywords):
        return "complaint"
    
    # Check for praise
    if any(kw in text_lower for kw in praise_keywords):
        return "praise"
    
    # Check for suggestions
    if any(kw in text_lower for kw in suggestion_keywords):
        return "suggestion"
    
    # Check for questions
    if any(kw in text_lower for kw in question_keywords):
        return "question"
    
    # Default to feedback
    return "feedback"


def determine_priority(emotion: str, intent: str) -> str:
    """Determine priority level based on emotion and intent"""
    
    # Critical: angry with bug report or complaint
    if emotion == "anger" and intent in ["bug_report", "complaint"]:
        return "Critical"
    
    # High: angry, or bug report, or sadness with complaint
    if emotion == "anger" or intent == "bug_report" or (emotion == "sadness" and intent == "complaint"):
        return "High"
    
    # Medium: sadness, or complaint without anger
    if emotion == "sadness" or intent == "complaint":
        return "Medium"
    
    # Low: everything else (neutral, praise, questions, feedback)
    return "Low"


def call_openai(prompt: str, max_retries: int = 3, timeout: int = 10) -> Optional[str]:
    """
    Call the OpenAI API and return the raw text response.
    Falls back to local NLP-based sentiment analysis when API key is missing.
    This function checks the environment at call time so a running process can disable the
    real API by unsetting `OPENAI_API_KEY`.
    """
    # Respect FORCE_LOCAL (developer preference) to always use local analysis.
    force_local = os.getenv("FORCE_LOCAL", "false").lower() in ("1", "true", "yes")
    key = os.getenv("OPENAI_API_KEY")
    
    if force_local:
        key = None
    
    # Extract comment text from prompt (it comes after "COMMENT:\n")
    comment_text = extract_comment_from_prompt(prompt)
    
    if not key:
        # Local analysis: use NLP-based sentiment analysis
        result = analyze_sentiment_locally(comment_text)
        return json.dumps(result)
    
    # Try to call real OpenAI API with retries
    try:
        import openai
        openai.api_key = key
        attempt = 0
        while attempt < max_retries:
            try:
                resp = openai.ChatCompletion.create(
                    model=DEFAULT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=400,
                )
                # Extract text (compat with different client versions)
                out = None
                if hasattr(resp, 'choices') and resp.choices:
                    choice = resp.choices[0]
                    # new style
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        out = choice.message.content
                    # older style
                    elif hasattr(choice, 'text'):
                        out = choice.text
                if out is not None:
                    return out
                attempt += 1
                time.sleep(1 + attempt)
            except Exception:
                attempt += 1
                time.sleep(1 + attempt)
        
        # No usable output from the real API after retries -> fall back to local analysis
        result = analyze_sentiment_locally(comment_text)
        return json.dumps(result)
    except Exception:
        # Import/network error -> fall back to local analysis
        result = analyze_sentiment_locally(comment_text)
        return json.dumps(result)


def extract_comment_from_prompt(prompt: str) -> str:
    """Extract the comment text from the prompt by finding text after 'COMMENT:'"""
    if "COMMENT:" in prompt:
        parts = prompt.split("COMMENT:")
        if len(parts) > 1:
            return parts[1].strip()
    return prompt
