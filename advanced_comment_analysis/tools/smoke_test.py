import os, json
os.environ.pop('OPENAI_API_KEY', None)
from app.services.ai_service import analyze_text
res = analyze_text('This is a test comment that is neutral.')
print(json.dumps({
    "emotion": res.emotion,
    "intent": res.intent,
    "priority": res.priority,
    "needs_ticket": res.needs_ticket,
    "confidence": res.confidence
}))
