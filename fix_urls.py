#!/usr/bin/env python3
"""
修复元数据文件中的重复URL问题
"""

import json
import os

def fix_duplicate_urls():
    """修复元数据文件中重复的URL前缀"""
    # 读取元数据文件
    input_file = 'project/src/data/images.json'
    with open(input_file, 'r', encoding='utf-8') as f:
        images_data = json.load(f)

    # 修复URL
    fixed_count = 0
    for image in images_data:
        # 修复png_url
        png_url = image['png_url']
        if 'r2.dev/https://' in png_url:
            # 提取文件名
            filename = png_url.split('/')[-1]
            # 创建新的正确URL
            image['png_url'] = f'https://pub-ee5efd5217f84e8e8d4d7e15827887c7.r2.dev/{filename}'
            fixed_count += 1
        
        # 修复sticker_url
        sticker_url = image['sticker_url']
        if 'r2.dev/https://' in sticker_url:
            # 提取文件名
            filename = sticker_url.split('/')[-1]
            # 创建新的正确URL
            image['sticker_url'] = f'https://pub-ee5efd5217f84e8e8d4d7e15827887c7.r2.dev/{filename}'
            fixed_count += 1

    # 保存修复后的元数据
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(images_data, f, indent=2, ensure_ascii=False)

    # 同时更新api目录中的元数据
    api_file = 'api/data/images.json'
    if os.path.exists(api_file):
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, indent=2, ensure_ascii=False)
        print(f'已修复元数据文件中的重复URL，共修复了{fixed_count}个URL。更新了以下文件：')
        print(f'- {input_file}')
        print(f'- {api_file}')
    else:
        print(f'已修复元数据文件中的重复URL，共修复了{fixed_count}个URL：{input_file}')

if __name__ == "__main__":
    fix_duplicate_urls() 