import requests

API = 'http://127.0.0.1:8000'

try:
	r = requests.get(f"{API}/health", timeout=3)
	print('/health', r.status_code, r.json())
except Exception as e:
	print('/health error', e)

try:
	r = requests.post(f"{API}/ai/analyze", json={'content':'This is a test comment that is neutral.'}, timeout=5)
	print('/ai/analyze', r.status_code, r.json())
except Exception as e:
	print('/ai/analyze error', e)
