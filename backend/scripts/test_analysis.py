import urllib.request
import json

# 测试分析API返回的数据（使用cache）
r = urllib.request.urlopen('http://localhost:8001/api/analysis/stream?stock_code=600519&force_refresh=false')
data = r.read().decode('utf-8')
print('Raw response:')
print(data[:2000])
