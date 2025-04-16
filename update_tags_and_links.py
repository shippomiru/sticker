#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新图片标签分类和内页链接

此脚本用于更新已经处理完并上传到R2的图片元数据，
根据新的标签分类系统重新对图片进行分类，
并添加标签对应的内页链接。

使用方法:
    python3 update_tags_and_links.py
"""

import os
import json
import sys
import logging
import shutil
from datetime import datetime
from api.processors.metadata_generator import classify_image_to_predefined_tags

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_tags.log')
    ]
)
logger = logging.getLogger('update_tags')

# 元数据文件路径
METADATA_FILE = 'api/data/images.json'
FRONTEND_METADATA_FILE = 'project/src/data/images.json'

# 标签和对应的内页链接
TAG_PAGES = {
    "christmas": "/clipart/christmas/",
    "flower": "/clipart/flower/",
    "book": "/clipart/book/",
    "christmas tree": "/clipart/christmas-tree/",
    "dog": "/clipart/dog/",
    "car": "/clipart/car/",
    "cat": "/clipart/cat/",
    "pumpkin": "/clipart/pumpkin/",
    "apple": "/clipart/apple/",
    "airplane": "/clipart/airplane/",
    "birthday": "/clipart/birthday/",
    "santa hat": "/png/santa-hat/",
    "crown": "/png/crown/",
    "gun": "/png/gun/",
    "books": "/clipart/book/",
    "baby": "/clipart/baby/",
    "camera": "/clipart/camera/",
    "flowers": "/clipart/flower/",
    "money": "/png/money/",
    "others": "/png/others/"
}

# 标签顺序 - 用于确保前端展示顺序一致
TAG_ORDER = [
    "christmas", "flower", "book", "christmas tree", "dog", "car", 
    "cat", "pumpkin", "apple", "airplane", "birthday", "santa hat", 
    "crown", "gun", "books", "baby", "camera", "flowers", "money", "others"
]

def backup_file(file_path):
    """备份文件"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份原始文件到: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"备份文件失败: {str(e)}")
        return False

def update_image_tags(image):
    """更新单个图片的标签和链接信息"""
    caption = image.get('caption', '')
    
    # 使用现有分类器重新对图片进行分类
    tags = classify_image_to_predefined_tags(caption)
    
    # 确保tags是有效的列表
    if not isinstance(tags, list):
        tags = []
    
    # 如果没有分类，使用"others"
    if not tags:
        tags = ["others"]
    
    # 添加tag_pages字段，包含每个标签对应的内页链接
    tag_pages = {}
    for tag in tags:
        if tag in TAG_PAGES:
            tag_pages[tag] = TAG_PAGES[tag]
    
    # 更新图片元数据
    image['tags'] = tags
    image['tag_pages'] = tag_pages
    
    return image

def update_metadata():
    """更新元数据文件中的标签和内页链接"""
    try:
        # 检查元数据文件是否存在
        if not os.path.exists(METADATA_FILE):
            logger.error(f"元数据文件不存在: {METADATA_FILE}")
            return False
        
        # 备份原始文件
        if not backup_file(METADATA_FILE):
            return False
        
        # 读取元数据文件
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        logger.info(f"开始更新 {len(metadata)} 张图片的标签分类...")
        
        # 更新每张图片的标签和链接
        for i, image in enumerate(metadata):
            metadata[i] = update_image_tags(image)
            
            # 每处理100张图片输出一次进度
            if (i+1) % 100 == 0 or i+1 == len(metadata):
                logger.info(f"已处理 {i+1}/{len(metadata)} 张图片")
        
        # 保存更新后的元数据
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 同时更新前端数据文件
        with open(FRONTEND_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"元数据更新完成，已更新 {len(metadata)} 张图片的标签分类和内页链接")
        
        # 统计各标签图片数量
        tag_counts = {}
        for image in metadata:
            for tag in image.get('tags', []):
                if tag not in tag_counts:
                    tag_counts[tag] = 0
                tag_counts[tag] += 1
        
        # 按标签顺序输出统计结果
        logger.info("各标签图片数量统计:")
        for tag in TAG_ORDER:
            if tag in tag_counts:
                logger.info(f"  - {tag}: {tag_counts[tag]} 张图片")
        
        return True
    except Exception as e:
        logger.error(f"更新元数据时出错: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始更新图片标签分类和内页链接...")
    if update_metadata():
        logger.info("更新成功!")
        sys.exit(0)
    else:
        logger.error("更新失败!")
        sys.exit(1) 