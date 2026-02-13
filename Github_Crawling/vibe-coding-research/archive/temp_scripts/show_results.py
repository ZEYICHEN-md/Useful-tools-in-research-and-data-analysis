import csv
from collections import Counter

with open('sample_repos_20260210_180552.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    repos = list(reader)

print("="*70)
print("SAMPLE RESULTS - 109 Vibe Coding Related Repos")
print("="*70)

print(f"\nTotal repos: {len(repos)}\n")

# 语言分布
langs = Counter([r['language'] for r in repos])
print("Language distribution:")
for lang, cnt in langs.most_common():
    print(f"  {lang}: {cnt}")

# 按 stars 排序
repos.sort(key=lambda x: int(x['stars']), reverse=True)

print("\n" + "="*70)
print("TOP 15 REPOSITORIES (by stars)")
print("="*70 + "\n")

for i, r in enumerate(repos[:15], 1):
    try:
        print(f"{i}. {r['full_name']}")
        print(f"   Stars: {r['stars']} | Lang: {r['language']} | Created: {r['created_at'][:10]}")
        if r['description']:
            # 清理不可打印字符
            desc = r['description'][:100].encode('ascii', 'ignore').decode('ascii')
            print(f"   Desc: {desc}...")
        print(f"   Link: {r['html_url']}")
        print()
    except:
        pass
