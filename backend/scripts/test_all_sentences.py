import urllib.request
import json

r = urllib.request.urlopen('http://localhost:8001/api/analysis/stream?stock_code=600519&force_refresh=false')
data = r.read().decode('utf-8')

lines = data.split('\n')
for line in lines:
    if line.startswith('event: result'):
        continue
    if line.startswith('data: '):
        result_data = json.loads(line[6:])
        if 'result' in result_data:
            res = result_data['result']
            if 'yearGroups' in res:
                for group in res['yearGroups']:
                    print(f"Year: {group['year']}, Env: {group['env_sentences']}, Sentences: {len(group['sentences'])}")
            break
