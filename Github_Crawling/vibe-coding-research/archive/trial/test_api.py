import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('GITHUB_TOKEN')
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

# 测试搜索
url = 'https://api.github.com/search/code'
params = {
    'q': 'filename:.cursorrules created:>2025-01-01',
    'per_page': 5
}

resp = requests.get(url, headers=headers, params=params)
print(f'Status: {resp.status_code}')
print(f'Rate Limit Remaining: {resp.headers.get("X-RateLimit-Remaining")}')
print(f'Rate Limit Total: {resp.headers.get("X-RateLimit-Limit")}')

data = resp.json()
print(f'Total count: {data.get("total_count", 0)}')

if data.get('items'):
    for item in data['items'][:3]:
        repo = item['repository']
        print(f"  - {repo['full_name']} (created: {repo['created_at']})")
else:
    print("No items found")
    print(f"Response message: {data.get('message', 'N/A')}")
