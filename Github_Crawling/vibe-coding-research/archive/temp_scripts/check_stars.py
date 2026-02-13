#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv

with open('unbiased_all_20260210_220138_fixed.csv','r',encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
    # 统计stars分布
    stars_list = [int(r['stars']) for r in rows]
    stars_list.sort(reverse=True)
    
    print('=== Stars 分布统计 ===')
    print(f'总项目数: {len(stars_list)}')
    print(f'最高stars: {max(stars_list)}')
    print(f'最低stars: {min(stars_list)}')
    print(f'平均stars: {sum(stars_list)/len(stars_list):.1f}')
    
    print('\n=== Stars 分段统计 ===')
    ranges = [
        (0, 0, '0★'),
        (1, 5, '1-5★'),
        (6, 10, '6-10★'),
        (11, 20, '11-20★'),
        (21, 50, '21-50★'),
        (51, 100, '51-100★'),
        (101, 200, '101-200★'),
    ]
    for min_s, max_s, label in ranges:
        count = sum(1 for s in stars_list if min_s <= s <= max_s)
        pct = count / len(stars_list) * 100
        bar = '█' * int(count / len(stars_list) * 30)
        print(f'{label:10} {count:4} ({pct:5.1f}%) {bar}')
    
    print('\n=== 最高Stars的前10个项目 ===')
    top10 = sorted(rows, key=lambda x: int(x['stars']), reverse=True)[:10]
    for r in top10:
        stars = r['stars']
        name = r['full_name']
        desc = r['description'][:50] if r['description'] else ''
        print(f'  {stars:>3}★ {name}')
        if desc:
            print(f'       {desc}...')
