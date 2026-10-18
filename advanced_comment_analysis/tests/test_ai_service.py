import os
import json
from app.services.ai_service import analyze_text


def test_analyze_text_simulated():
    # using simulated fallback without OPENAI_API_KEY
    os.environ.pop('OPENAI_API_KEY', None)
    res = analyze_text('This is a test comment that is neutral.')
    assert res is not None
    assert hasattr(res, 'emotion')
    assert 0.0 <= res.confidence <= 1.0
