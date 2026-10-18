from fastapi.testclient import TestClient
from app.main import app
import json
import os
from pathlib import Path

client = TestClient(app)
results = []

r = client.get('/health')
results.append({'path':'/health','status': r.status_code, 'body': r.json()})

r = client.post('/ai/analyze', json={'comment_text':'This is a test comment that is neutral.'})
try:
    body = r.json()
except Exception:
    body = r.text
results.append({'path':'/ai/analyze','status': r.status_code, 'body': body})

project_root = Path(__file__).resolve().parent.parent
out_path = project_root / 'tools' / 'inprocess_output.txt'
out_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f'WROTE {out_path}')
