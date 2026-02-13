import requests
import os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('GITHUB_TOKEN')
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

# 测试不同的搜索条件
searches = [
    'filename:.cursorrules',
    'filename:CLAUDE.md',
    'filename:mcp.json',
    'filename:.cursorrules created:>2024-06-01',
]

for query in searches:
    url = 'https://api.github.com/search/code'
    params = {'q': query, 'per_page': 3}
    
    resp = requests.get(url, headers=headers, params=params)
    remaining = resp.headers.get("X-RateLimit-Remaining")
    
    data = resp.json()
    total = data.get("total_count", 0)
    
    print(f"Query: {query}")
    print(f"  Total: {total}")
    print(f"  Rate remaining: {remaining}")
    
    if data.get('items'):
        for item in data['items'][:2]:
            repo = item['repository']
            print(f"    - {repo['full_name']}")
    print()
