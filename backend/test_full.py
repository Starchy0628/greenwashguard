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
            print('Has yearGroups:', 'yearGroups' in res)
            print('yearGroups length:', len(res.get('yearGroups', [])))
            print('Has trend:', 'trend' in res)
            print('trend length:', len(res.get('trend', [])))
            if 'trend' in res:
                print('trend years:', [t['year'] for t in res['trend']])
            break
