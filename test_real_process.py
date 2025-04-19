#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：模拟实际的图片分类处理流程

这个脚本会模拟metadata_generator.py中的实际处理流程：
1. 识别主体（假设已经得到了caption）
2. 从caption中提取主体名词
3. 使用主体名词和caption进行分类

测试案例：
1. "A cathayo airplane flying in the sky"
2. "Cathayo airplane sticker"
3. "A view of the wing of an airplane"
4. "A view of a plane wing from the window"
"""

import sys
from api.processors.metadata_generator import extract_main_noun, classify_image_to_predefined_tags

def simulate_real_process(caption):
    """模拟实际的处理流程"""
    print(f"\n分析描述: '{caption}'")
    
    # 步骤1：从描述中提取主体名词
    extracted_noun = extract_main_noun(caption)
    print(f"提取的主体名词: {extracted_noun}")
    
    # 步骤2：使用主体名词和描述进行分类
    tag = classify_image_to_predefined_tags(caption, extracted_noun)
    print(f"最终分类标签: {tag}")
    
    return {
        "描述": caption,
        "提取的主体名词": extracted_noun,
        "分类标签": tag
    }

def run_real_process_tests():
    """运行模拟实际流程的测试"""
    print("模拟实际图片元数据生成流程...\n")
    
    test_captions = [
        "A cathayo airplane flying in the sky",
        "Cathayo airplane sticker",
        "A view of the wing of an airplane",
        "A view of a plane wing from the window"
    ]
    
    results = []
    for caption in test_captions:
        result = simulate_real_process(caption)
        results.append(result)
    
    # 打印结果摘要
    print("\n\n实际处理流程结果摘要:")
    for i, result in enumerate(results, 1):
        print(f"\n案例{i}:")
        print(f"  描述: '{result['描述']}'")
        print(f"  提取的主体名词: {result['提取的主体名词']}")
        print(f"  最终分类标签: {result['分类标签']}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    run_real_process_tests() 