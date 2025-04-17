#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
元数据合并脚本

将新批次的元数据合并到主元数据文件中
"""

import json
import os
from datetime import datetime

# 配置
NEW_METADATA_FILE = "metadata/metadata_20250417.json"
MAIN_METADATA_FILE = "api/data/images.json"
FRONTEND_DATA_FILE = "project/src/data/images.json"

def merge_metadata():
    """将新的元数据合并到主元数据文件中"""
    try:
        # 读取新元数据
        with open(NEW_METADATA_FILE, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        
        print(f"新元数据文件有 {len(new_data)} 条记录")
        
        # 读取主元数据
        with open(MAIN_METADATA_FILE, 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        
        print(f"主元数据文件有 {len(main_data)} 条记录")
        
        # 备份原始元数据文件
        backup_path = f"{MAIN_METADATA_FILE}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        os.rename(MAIN_METADATA_FILE, backup_path)
        print(f"已备份原始元数据文件: {backup_path}")
        
        # 提取已有的ID集合
        existing_ids = {item['id'] for item in main_data}
        
        # 添加新元数据（避免重复）
        new_items_added = 0
        for item in new_data:
            if item['id'] not in existing_ids:
                main_data.append(item)
                existing_ids.add(item['id'])
                new_items_added += 1
                print(f"添加新元数据: {item['id']} - {item['caption']}")
        
        # 写入更新后的元数据
        with open(MAIN_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        
        # 同时更新前端数据文件
        if os.path.exists(os.path.dirname(FRONTEND_DATA_FILE)):
            os.makedirs(os.path.dirname(FRONTEND_DATA_FILE), exist_ok=True)
            with open(FRONTEND_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(main_data, f, indent=2, ensure_ascii=False)
            print(f"已更新前端数据文件: {FRONTEND_DATA_FILE}")
        
        print(f"元数据合并完成！新增 {new_items_added} 条记录，当前共有 {len(main_data)} 条记录")
        return True
    except Exception as e:
        print(f"合并元数据时出错: {e}")
        return False

if __name__ == "__main__":
    merge_metadata() 