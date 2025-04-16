#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新元信息URL脚本

将元信息文件中的图片URL更新为R2 CDN URL
"""

import os
import json
from datetime import datetime

# R2 公共URL
r2_public_url = os.environ.get("R2_PUBLIC_URL", "https://pub-ee5efd5217f84e8e8d4d7e15827887c7.r2.dev")

# 配置
METADATA_FILE = "api/data/images.json"
FRONTEND_DATA_FILE = "project/src/data/images.json"

def update_metadata_with_r2_urls(images_json_path=METADATA_FILE):
    """更新元数据文件中的URL为R2 CDN URL"""
    try:
        # 读取现有的元数据
        with open(images_json_path, 'r', encoding='utf-8') as f:
            images_data = json.load(f)
        
        print(f"开始更新元数据中的URL为R2 CDN URL...")
        print(f"原始元数据条目数量: {len(images_data)}")
        
        # 创建修改后的副本
        updated_images = []
        update_count = 0
        
        for image in images_data:
            original_png_url = image["png_url"]
            original_sticker_url = image["sticker_url"]
            
            # 清理现有URL
            png_url = original_png_url
            sticker_url = original_sticker_url
            
            # 移除前导/images/
            if png_url.startswith('/images/'):
                png_url = png_url[8:]
                update_count += 1
            elif png_url.startswith('https://'):
                # 如果已经是https链接，提取文件名
                if r2_public_url in png_url:
                    # 如果已经是R2 URL，不需要更新
                    pass
                else:
                    png_url = png_url.split('/')[-1]
                    update_count += 1
            
            if sticker_url.startswith('/images/'):
                sticker_url = sticker_url[8:]
                update_count += 1
            elif sticker_url.startswith('https://'):
                # 如果已经是https链接，提取文件名
                if r2_public_url in sticker_url:
                    # 如果已经是R2 URL，不需要更新
                    pass
                else:
                    sticker_url = sticker_url.split('/')[-1]
                    update_count += 1
            
            # 添加R2 CDN URL前缀
            if not png_url.startswith(r2_public_url):
                image["png_url"] = f"{r2_public_url}/{png_url}"
            
            if not sticker_url.startswith(r2_public_url):
                image["sticker_url"] = f"{r2_public_url}/{sticker_url}"
            
            # 打印更新示例（仅展示前几条）
            if update_count <= 5:
                print(f"更新URL示例 #{update_count}:")
                print(f"  原始PNG URL: {original_png_url}")
                print(f"  新PNG URL: {image['png_url']}")
                print(f"  原始贴纸URL: {original_sticker_url}")
                print(f"  新贴纸URL: {image['sticker_url']}")
                print()
            
            updated_images.append(image)
        
        # 备份原始文件
        backup_path = f"{images_json_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        os.rename(images_json_path, backup_path)
        print(f"已备份原始元数据文件: {backup_path}")
        
        # 写入更新后的元数据
        with open(images_json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_images, f, indent=2, ensure_ascii=False)
        
        # 同时更新前端数据文件
        frontend_path = FRONTEND_DATA_FILE
        if os.path.exists(os.path.dirname(frontend_path)):
            os.makedirs(os.path.dirname(frontend_path), exist_ok=True)
            with open(frontend_path, 'w', encoding='utf-8') as f:
                json.dump(updated_images, f, indent=2, ensure_ascii=False)
            print(f"已更新前端数据文件: {frontend_path}")
        
        print(f"已更新元数据文件中的URL为R2 CDN: {images_json_path}")
        print(f"更新的URL数量: {update_count}")
        return True
    except Exception as e:
        print(f"更新元数据文件失败: {e}")
        return False

if __name__ == "__main__":
    update_metadata_with_r2_urls() 