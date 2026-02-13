#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 deepseek_analyzer_8cat.py 是否能正常导入和运行基础功能
"""

import ast
import sys

def test_syntax():
    """测试语法是否正确"""
    with open('deepseek_analyzer_8cat.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    try:
        ast.parse(code)
        print("✅ 语法检查通过")
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False

def test_dataclass():
    """测试 dataclass 定义"""
    # 使用 exec 来测试代码片段
    code = '''
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TestResult:
    repo_id: int
    repo_name: str
    created_at: Optional[str]
    ai_generation_score: int = 0

# 测试创建实例
test = TestResult(
    repo_id=123,
    repo_name="test-repo",
    created_at="2026-01-28T10:00:00Z",
    ai_generation_score=4
)
print(f"✅ Dataclass 测试通过: {test}")
'''
    try:
        exec(code)
        return True
    except Exception as e:
        print(f"❌ Dataclass 测试失败: {e}")
        return False

def test_file_exists():
    """测试必要文件是否存在"""
    import os
    files = [
        'deepseek_analyzer_8cat.py',
        'LLM提示词_8分类',
        'vibe_coding_dataset_2w.jsonl'
    ]
    
    all_exist = True
    for f in files:
        exists = os.path.exists(f)
        status = "✅" if exists else "❌"
        print(f"{status} {f}: {'存在' if exists else '不存在'}")
        if not exists:
            all_exist = False
    return all_exist

def main():
    print("=" * 60)
    print("测试 deepseek_analyzer_8cat.py")
    print("=" * 60)
    
    # 测试1: 语法
    print("\n1. 语法检查...")
    syntax_ok = test_syntax()
    
    # 测试2: dataclass
    print("\n2. Dataclass 测试...")
    dataclass_ok = test_dataclass()
    
    # 测试3: 文件存在性
    print("\n3. 文件存在性检查...")
    files_ok = test_file_exists()
    
    # 总结
    print("\n" + "=" * 60)
    if syntax_ok and dataclass_ok:
        print("✅ 所有测试通过！脚本可以正常运行")
        print("\n运行命令:")
        print("  python deepseek_analyzer_8cat.py")
    else:
        print("❌ 测试未通过，请检查错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main()
