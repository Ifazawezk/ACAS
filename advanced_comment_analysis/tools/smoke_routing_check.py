import requests, json
urls=['http://127.0.0.1:8000/dashboard/metrics','http://127.0.0.1:8000/comments?limit=50','http://127.0.0.1:8000/admin/rules']
for u in urls:
    try:
        r=requests.get(u, timeout=5)
        print('\nURL:',u,'Status:',r.status_code)
        ct = r.headers.get('Content-Type','')
        if 'application/json' in ct:
            print(json.dumps(r.json(), indent=2))
        else:
            print(r.text[:400])
    except Exception as e:
        print('\nURL:',u,'ERROR',e)
