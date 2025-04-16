#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查找缺少元信息的图片

此脚本会比较project/public/images目录中的图片和api/data/images.json中的元信息，
找出缺少元信息的图片，并输出需要为这些图片生成元信息的命令。
"""

import os
import json
import glob
import re

# 配置
IMAGES_DIR = "project/public/images"
METADATA_FILE = "api/data/images.json"

def extract_id_from_filename(filename):
    """从文件名中提取ID"""
    # 移除路径和扩展名
    base_name = os.path.basename(filename)
    # 移除 _cropped.png 或 _outlined_cropped.png 后缀
    id_part = re.sub(r'_(outlined_)?cropped\.png$', '', base_name)
    return id_part

def print_sample_files(files, count=5):
    """打印样本文件"""
    print(f"样本文件 (显示前{min(count, len(files))}个):")
    for i, f in enumerate(sorted(files)[:count]):
        print(f"  {i+1}. {os.path.basename(f)}")

def main():
    print("开始查找缺少元信息的图片...")
    
    # 加载现有的元信息
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 提取已有元信息的ID
    existing_ids = set()
    for item in metadata:
        existing_ids.add(item['id'])
    
    print(f"元信息文件中已有 {len(existing_ids)} 个图片ID")
    
    # 直接列出目录中的所有PNG文件
    all_png_files = []
    for root, dirs, files in os.walk(IMAGES_DIR):
        for file in files:
            if file.endswith(".png"):
                all_png_files.append(os.path.join(root, file))
    
    print(f"在{IMAGES_DIR}目录中找到 {len(all_png_files)} 个PNG图片")
    print_sample_files(all_png_files)
    
    # 分类文件
    cropped_files = [f for f in all_png_files if f.endswith("_cropped.png") and not "_outlined_cropped.png" in f]
    outlined_files = [f for f in all_png_files if "_outlined_cropped.png" in f]
    
    print(f"其中 {len(cropped_files)} 个普通图片和 {len(outlined_files)} 个轮廓图片")
    print_sample_files(cropped_files)
    print_sample_files(outlined_files)
    
    # 提取所有图片的ID
    all_image_ids = set(extract_id_from_filename(f) for f in all_png_files)
    cropped_ids = set(extract_id_from_filename(f) for f in cropped_files)
    outlined_ids = set(extract_id_from_filename(f) for f in outlined_files)
    
    print(f"总共找到 {len(all_image_ids)} 个不同的图片ID")
    print(f"普通图片ID: {len(cropped_ids)}, 轮廓图片ID: {len(outlined_ids)}")
    
    # 找出有对应轮廓版本的图片ID
    paired_ids = cropped_ids.intersection(outlined_ids)
    print(f"找到 {len(paired_ids)} 对完整的图片对（普通版+轮廓版）")
    
    # 检查所有图片是否都有元信息
    missing_ids = all_image_ids - existing_ids
    print(f"其中有 {len(missing_ids)} 个图片ID缺少元信息")
    
    # 检查是否有单独的图片（没有配对）
    single_cropped_ids = cropped_ids - outlined_ids
    single_outlined_ids = outlined_ids - cropped_ids
    print(f"发现 {len(single_cropped_ids)} 个只有普通版的图片")
    print(f"发现 {len(single_outlined_ids)} 个只有轮廓版的图片")
    
    # 检查单独图片是否有元信息
    missing_single_cropped = single_cropped_ids - existing_ids
    missing_single_outlined = single_outlined_ids - existing_ids
    print(f"其中 {len(missing_single_cropped)} 个只有普通版的图片缺少元信息")
    print(f"其中 {len(missing_single_outlined)} 个只有轮廓版的图片缺少元信息")
    
    if missing_ids:
        print("\n缺少元信息的图片ID:")
        for id in sorted(missing_ids):
            print(f"  {id}")
        
        print("\n要为这些图片生成元信息，可以运行以下命令:")
        print(f"python3 generate_metadata.py {IMAGES_DIR} {METADATA_FILE}")
        
        # 或者也可以提供一个具体ID的列表给元数据生成脚本
        # 如果元数据生成脚本支持指定ID列表的话
        print("\n如果元数据生成脚本支持指定ID列表，可以运行:")
        ids_arg = ",".join(sorted(missing_ids))
        print(f"python3 generate_metadata.py {IMAGES_DIR} {METADATA_FILE} --ids={ids_arg}")
    
    return missing_ids

if __name__ == "__main__":
    main() 