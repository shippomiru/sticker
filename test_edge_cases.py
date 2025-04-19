#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：测试classify_image_to_predefined_tags函数对特定边缘案例的处理

这个脚本会测试以下特定案例：
1. "A cathayo airplane flying in the sky" - 可能的标签: cat, airplane
2. "Cathayo airplane sticker" - 可能的标签: cat, airplane
3. "A view of the wing of an airplane" - 可能的标签: airplane, bird
4. "A view of a plane wing from the window" - 可能的标签: airplane, bird
"""

import sys
from api.processors.metadata_generator import classify_image_to_predefined_tags

def test_case(caption, options, extracted_noun=None):
    """测试指定的案例"""
    print(f"\n测试案例: '{caption}'")
    print(f"可能的标签: {', '.join(options)}")
    if extracted_noun:
        print(f"提供的主体名词: {extracted_noun}")
    
    # 测试不提供extracted_noun的情况
    result1 = classify_image_to_predefined_tags(caption)
    print(f"结果 (不提供主体名词): {result1}")
    
    # 为每个可能的选项测试
    results = {}
    for option in options:
        result = classify_image_to_predefined_tags(caption, option)
        results[option] = result
        print(f"结果 (主体名词={option}): {result}")
    
    return {
        "不提供主体名词": result1,
        "提供主体名词": results
    }

def run_tests():
    """运行所有测试案例"""
    print("开始测试特定边缘案例...\n")
    
    results = {}
    
    # 案例1：包含"cathayo airplane"的描述
    results["案例1"] = test_case(
        "A cathayo airplane flying in the sky", 
        ["cat", "airplane"]
    )
    
    # 案例2：Cathayo airplane贴纸
    results["案例2"] = test_case(
        "Cathayo airplane sticker", 
        ["cat", "airplane"]
    )
    
    # 案例3：飞机翼的景色
    results["案例3"] = test_case(
        "A view of the wing of an airplane", 
        ["airplane", "bird"]
    )
    
    # 案例4：从窗户看飞机翼
    results["案例4"] = test_case(
        "A view of a plane wing from the window", 
        ["airplane", "bird"]
    )
    
    # 打印结果摘要
    print("\n\n测试结果摘要:")
    for case_name, case_results in results.items():
        print(f"\n{case_name}:")
        print(f"  自动分类: {case_results['不提供主体名词']}")
        print("  提供主体名词的结果:")
        for noun, tag in case_results['提供主体名词'].items():
            print(f"    • 主体名词={noun}: {tag}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    run_tests() 