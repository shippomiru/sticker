#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从元数据文件中删除指定ID的图片信息
"""

import json
import os

def remove_image_from_metadata(image_id, metadata_files):
    """从多个元数据文件中删除特定ID的图片"""
    for metadata_file in metadata_files:
        if not os.path.exists(metadata_file):
            print(f"文件不存在: {metadata_file}")
            continue
            
        print(f"处理文件: {metadata_file}")
        
        # 读取元数据文件
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 记录原始数量
        original_count = len(metadata)
        
        # 过滤掉指定ID的图片
        metadata = [img for img in metadata if img['id'] != image_id]
        
        # 记录新数量
        new_count = len(metadata)
        
        if original_count == new_count:
            print(f"未找到ID为 {image_id} 的图片")
        else:
            print(f"已从元数据中删除 {original_count - new_count} 条记录")
            
            # 保存更新后的元数据
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"已保存更新后的元数据到 {metadata_file}")

if __name__ == "__main__":
    # 要删除的图片ID
    image_id = "stefanobaz-YXX7xyoi2Bs-unsplash"
    
    # 元数据文件路径
    metadata_files = [
        "api/data/images.json",
        "project/src/data/images.json"
    ]
    
    # 执行删除操作
    remove_image_from_metadata(image_id, metadata_files)
    
    print("操作完成！") 