#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单修正元数据标签脚本
将指定的图片标题对应的标签设置为airplane
"""

import os
import json

# 需要修正的图片标题
TARGET_CAPTIONS = [
    "A cathayo airplane flying in the sky",
    "Cathayo airplane sticker",
    "A view of the wing of an airplane",
    "A view of a plane wing from the window",
    "American airlines a320 - 300",
    "Qatar a380 - 300 - qatar airways - qatar airways"
]

# 要设置的标签
TARGET_TAG = "airplane"

# 元数据文件路径
METADATA_FILES = [
    "metadata/images.json",
    "project/src/data/images.json",
    "api/data/images.json"
]

def fix_metadata_file(file_path):
    """修正指定元数据文件中的标签"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建备份
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已创建备份: {backup_path}")
    
    # 计数器
    modified_count = 0
    
    # 遍历所有元数据项
    for item in data:
        caption = item.get("caption", "")
        
        # 检查是否是目标标题
        if caption in TARGET_CAPTIONS:
            # 记录旧标签
            old_tags = item.get("tags", [])
            if isinstance(old_tags, str):
                old_tags = [old_tags]
            
            # 设置新标签
            item["tags"] = [TARGET_TAG]
            
            modified_count += 1
            print(f"已修改: '{caption}'")
            print(f"  旧标签: {old_tags}")
            print(f"  新标签: ['{TARGET_TAG}']")
    
    # 保存修改后的文件
    if modified_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存修改，共修改 {modified_count} 项")
    else:
        print("未找到需要修改的项目")

def main():
    """主函数"""
    print("开始修正元数据标签...")
    
    for file_path in METADATA_FILES:
        print(f"\n处理文件: {file_path}")
        fix_metadata_file(file_path)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main() 