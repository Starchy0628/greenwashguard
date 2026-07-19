import urllib.request
import json

# 直接访问后端
r = urllib.request.urlopen('http://localhost:8001/api/companies/3216/sentences/all')
print('Status:', r.status)
data = json.loads(r.read())
print('Year groups:', len(data.get('year_groups', [])))
print('First group:', data.get('year_groups', [{}])[0] if data.get('year_groups') else 'empty')
