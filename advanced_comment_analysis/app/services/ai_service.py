import json
import time
import os
from typing import Optional

from pydantic import ValidationError
import logging

from app.services.openai_client import call_openai
from app.schemas.ai import AIAnalysis

# Confidence threshold: below this value, automatically flag needs_ticket=True
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.5"))


SYSTEM_PROMPT = '''
You are an assistant that MUST return a single JSON object only with these fields:
emotion, intent, priority (Low|Medium|High|Critical), needs_ticket (true/false), suggested_response, confidence (0.0-1.0)
Return strictly valid JSON, nothing else. Example:
{"emotion":"angry","intent":"complaint","priority":"High","needs_ticket":true,"suggested_response":"...","confidence":0.92}
'''


def build_prompt(comment_text: str) -> str:
    return SYSTEM_PROMPT + "\nCOMMENT:\n" + comment_text


def analyze_text(comment_text: str, max_retries: int = 3) -> Optional[AIAnalysis]:
    prompt = build_prompt(comment_text)
    attempt = 0
    last_err = None
    logger = logging.getLogger(__name__)
    while attempt < max_retries:
        raw = call_openai(prompt)
        if not raw:
            logger.warning('AI client returned no response, attempt %s', attempt)
            attempt += 1
            time.sleep(1)
            continue
        # Try to parse JSON strictly
        try:
            parsed = json.loads(raw)
            analysis = AIAnalysis(**parsed)
            logger.info('AI analysis parsed: %s', analysis.dict())
            # Confidence threshold handling: if below threshold, ensure a ticket is created
            if analysis.confidence < AI_CONFIDENCE_THRESHOLD:
                analysis.needs_ticket = True
            return analysis
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = e
            attempt += 1
            time.sleep(1 + attempt)
            continue
    # If we get here, return None
    return None
