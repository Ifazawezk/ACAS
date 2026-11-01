import logging
import os
import time
import json
import re
from typing import Optional

from dotenv import load_dotenv

from app.services.local_analyzer import analyze_sentiment_locally

load_dotenv()

logger = logging.getLogger(__name__)

# Note: read the key at call time so tests / local runs can override env after import
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def _openai_client(key: str, timeout: int):
    from openai import OpenAI

    # Retries live in call_openai so that a failed call can fall back to the local analyzer.
    return OpenAI(api_key=key, timeout=timeout, max_retries=0)


def _local_result(comment_text: str) -> str:
    return json.dumps({**analyze_sentiment_locally(comment_text), "analyzer": "local"})


def call_openai(prompt: str, max_retries: int = 3, timeout: int = 10) -> Optional[str]:
    """
    Call the OpenAI API and return the raw text response.
    Falls back to local analysis when no key is set or the API cannot be reached.
    A local result carries "analyzer": "local", so a fallback is visible to the caller.
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
        return _local_result(comment_text)

    try:
        client = _openai_client(key, timeout)
    except Exception:
        logger.exception("Could not create the OpenAI client, using the local analyzer")
        return _local_result(comment_text)

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=400,
            )
            out = resp.choices[0].message.content
            if out:
                return out
            logger.warning("OpenAI returned an empty message, attempt %s of %s", attempt, max_retries)
        except Exception as e:
            logger.warning("OpenAI call failed, attempt %s of %s: %s", attempt, max_retries, e)
        if attempt < max_retries:
            time.sleep(attempt)

    logger.error("No usable answer from OpenAI after %s attempts, using the local analyzer", max_retries)
    return _local_result(comment_text)


def extract_comment_from_prompt(prompt: str) -> str:
    """Return the text after the 'COMMENT:' marker, which the comment itself may also contain."""
    if "COMMENT:\n" in prompt:
        return prompt.split("COMMENT:\n", 1)[1].strip()
    return prompt
