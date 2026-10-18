import time
import requests
import json

BASE='http://127.0.0.1:8000'

# Wait for server
for i in range(20):
    try:
        r = requests.get(BASE + '/health', timeout=1)
        print('/health', r.status_code, r.text)
        break
    except Exception as e:
        time.sleep(0.5)
else:
    print('server did not start')

# Test AI analyze endpoint
try:
    payload = {'comment_text': 'This is a test comment that is neutral.'}
    r = requests.post(BASE + '/ai/analyze', json=payload, timeout=10)
    print('/ai/analyze', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
except Exception as e:
    print('ai call failed', str(e))
