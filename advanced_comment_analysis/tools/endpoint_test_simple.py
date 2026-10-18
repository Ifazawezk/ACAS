import json, urllib.request, urllib.error
BASE='http://127.0.0.1:8000'
results=[]
# health
try:
    req=urllib.request.Request(BASE + '/health')
    with urllib.request.urlopen(req, timeout=5) as r:
        results.append(f"/health {r.status} {r.read().decode()}")
except Exception as e:
    results.append(f"/health ERROR {e!r}")
# ai analyze
try:
    data=json.dumps({'comment_text':'This is a test comment that is neutral.'}).encode('utf-8')
    req=urllib.request.Request(BASE + '/ai/analyze', data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r:
        results.append(f"/ai/analyze {r.status} {r.read().decode()}")
except Exception as e:
    results.append(f"/ai/analyze ERROR {e!r}")
# write results
open('tools/endpoint_results.txt','w', encoding='utf-8').write('\n'.join(results))
print('WROTE endpoint_results.txt')
