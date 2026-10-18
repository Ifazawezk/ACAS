import requests

url = "http://127.0.0.1:8000/comments?limit=500&sort_by=created_at&sort_order=desc"
print(f"Testing: {url}")
r = requests.get(url)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"First 300 chars: {r.text[:300]}")
if not r.text.startswith('[') and not r.text.startswith('{'):
    print("\n!!! NOT JSON !!!")
    print(f"Full response (first 1000):\n{r.text[:1000]}")
