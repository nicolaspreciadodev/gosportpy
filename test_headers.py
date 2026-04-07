import urllib.request
url = 'http://127.0.0.1:8000/canchas/reporte/pdf/'
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    print(response.headers)
    print("Content length:", len(response.read()))
