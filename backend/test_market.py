import urllib.request
import json

r = urllib.request.urlopen('http://localhost:8001/api/companies/market/trend')
data = json.loads(r.read())
print('Market trend data:', data)
