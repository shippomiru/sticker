#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：测试classify_image_to_predefined_tags函数对不同类型的extracted_noun的处理

这个脚本会测试以下情况：
1. extracted_noun是字符串
2. extracted_noun是列表（非空）
3. extracted_noun是空列表
4. extracted_noun是None
5. extracted_noun是数字
6. extracted_noun是字典
"""

import sys
from api.processors.metadata_generator import classify_image_to_predefined_tags

def test_with_string():
    """测试使用字符串类型的extracted_noun"""
    print("\n测试案例1: extracted_noun是字符串")
    caption = "A beautiful flower in the garden"
    extracted_noun = "flower"
    result = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"输入: caption='{caption}', extracted_noun='{extracted_noun}' (类型: {type(extracted_noun).__name__})")
    print(f"输出: {result}")
    return result

def test_with_list():
    """测试使用列表类型的extracted_noun"""
    print("\n测试案例2: extracted_noun是非空列表")
    caption = "A dog running in the park"
    extracted_noun = ["dog", "park"]
    result = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"输入: caption='{caption}', extracted_noun={extracted_noun} (类型: {type(extracted_noun).__name__})")
    print(f"输出: {result}")
    return result

def test_with_empty_list():
    """测试使用空列表作为extracted_noun"""
    print("\n测试案例3: extracted_noun是空列表")
    caption = "A car parked on the street"
    extracted_noun = []
    result = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"输入: caption='{caption}', extracted_noun={extracted_noun} (类型: {type(extracted_noun).__name__})")
    print(f"输出: {result}")
    return result

def test_with_none():
    """测试使用None作为extracted_noun"""
    print("\n测试案例4: extracted_noun是None")
    caption = "A cat sleeping on the couch"
    extracted_noun = None
    result = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"输入: caption='{caption}', extracted_noun={extracted_noun} (类型: {type(extracted_noun).__name__ if extracted_noun is not None else 'NoneType'})")
    print(f"输出: {result}")
    return result

def test_with_number():
    """测试使用数字作为extracted_noun"""
    print("\n测试案例5: extracted_noun是数字")
    caption = "An airplane flying in the sky"
    extracted_noun = 123
    result = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"输入: caption='{caption}', extracted_noun={extracted_noun} (类型: {type(extracted_noun).__name__})")
    print(f"输出: {result}")
    return result

def test_with_dict():
    """测试使用字典作为extracted_noun"""
    print("\n测试案例6: extracted_noun是字典")
    caption = "A book on the table"
    extracted_noun = {"main": "book", "secondary": "table"}
    result = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"输入: caption='{caption}', extracted_noun={extracted_noun} (类型: {type(extracted_noun).__name__})")
    print(f"输出: {result}")
    return result

def run_all_tests():
    """运行所有测试案例"""
    print("开始测试classify_image_to_predefined_tags函数...")
    
    results = {
        "字符串": test_with_string(),
        "列表": test_with_list(),
        "空列表": test_with_empty_list(),
        "None": test_with_none(),
        "数字": test_with_number(),
        "字典": test_with_dict()
    }
    
    # 打印测试结果摘要
    print("\n测试结果摘要:")
    for test_name, result in results.items():
        print(f"  • {test_name}: {result}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    run_all_tests() 