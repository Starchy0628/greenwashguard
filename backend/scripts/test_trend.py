import urllib.request
import json

# 测试主分析API返回的trend字段
r = urllib.request.urlopen('http://localhost:8001/api/companies/3216')
data = json.loads(r.read())
print('Trend field:', data.get('trend'))
print('YearGroups length:', len(data.get('yearGroups', [])))
