import urllib.request
import json

r = urllib.request.urlopen('http://localhost:8001/api/companies/3216/sentences/all')
data = json.loads(r.read())
print('Groups:', len(data.get('year_groups', [])))
for g in data.get('year_groups', []):
    print(f"Y:{g['year']}, E:{g['env_sentences']}, S:{len(g['sentences'])}")
