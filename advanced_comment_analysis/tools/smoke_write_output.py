import os
import sys
import json
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure we use the simulated fallback
os.environ.pop('OPENAI_API_KEY', None)

from app.services.ai_service import analyze_text

out = analyze_text('This is a test comment that is neutral.')

out_json = {
    'emotion': out.emotion,
    'intent': out.intent,
    'priority': out.priority,
    'needs_ticket': out.needs_ticket,
    'confidence': out.confidence,
}

out_path = project_root / 'tools' / 'smoke_output.txt'
out_path.write_text(json.dumps(out_json))
print(f'WROTE {out_path}')
