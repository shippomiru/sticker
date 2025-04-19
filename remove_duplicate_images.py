#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def remove_duplicates():
    """移除重复的图片条目"""
    # 文件路径
    api_file = 'api/data/images.json'
    frontend_file = 'project/src/data/images.json'
    
    # 要移除的ID
    ids_to_remove = [
        "bobmelo-H6VxhE_x-kE-unsplash",  # 重复的苹果碗图片
        "waiheng_tobi-zLCR7RsxYGs-unsplash"  # 重复的咬了一口的红苹果图片
    ]
    
    # 修改API文件
    with open(api_file, 'r') as f:
        data = json.load(f)
    
    # 移除重复图片
    original_count = len(data)
    data = [item for item in data if item['id'] not in ids_to_remove]
    removed_count = original_count - len(data)
    
    print(f'已从API文件中移除 {removed_count} 个重复图片')
    
    # 保存修改后的API文件
    with open(api_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # 修改前端文件
    with open(frontend_file, 'r') as f:
        data = json.load(f)
    
    # 移除重复图片
    original_count = len(data)
    data = [item for item in data if item['id'] not in ids_to_remove]
    removed_count = original_count - len(data)
    
    print(f'已从前端文件中移除 {removed_count} 个重复图片')
    
    # 保存修改后的前端文件
    with open(frontend_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print('修改完成！')

if __name__ == "__main__":
    remove_duplicates() 