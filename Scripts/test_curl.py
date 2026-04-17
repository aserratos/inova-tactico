import urllib.request
try:
    req = urllib.request.Request('http://127.0.0.1:8000/dashboard')
    resp = urllib.request.urlopen(req)
    print("STATUS:", resp.status)
    print("REDIRECT URL:", resp.geturl())
except Exception as e:
    print("CONNECTION ERROR:", e)
