#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def update_tags():
    """将Apple Watch Series 3的标签从"apple"修改为"others"，同时更新两个文件"""
    # 文件路径
    api_file = 'api/data/images.json'
    frontend_file = 'project/src/data/images.json'
    
    # 修改API文件
    with open(api_file, 'r') as f:
        data = json.load(f)
    
    for item in data:
        if item['id'] == 'danicanibano-JE3ASpuEld4-unsplash':
            item['tags'] = ['others']
            print(f'已修改API文件中Apple Watch的标签: {item["tags"]}')
    
    with open(api_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # 修改前端文件
    with open(frontend_file, 'r') as f:
        data = json.load(f)
    
    for item in data:
        if item['id'] == 'danicanibano-JE3ASpuEld4-unsplash':
            item['tags'] = ['others']
            print(f'已修改前端文件中Apple Watch的标签: {item["tags"]}')
    
    with open(frontend_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print('修改完成！')

if __name__ == "__main__":
    update_tags() 