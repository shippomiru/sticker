#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新标签分类脚本
用于批量更新所有图片的标签分类，使用新的分类规则

使用方法:
    python3 update_tags.py [--force]
"""

import os
import json
import time
import argparse
import logging
from datetime import datetime
from generate_metadata import classify_image_to_predefined_tags, extract_main_noun

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_tags.log')
    ]
)
logger = logging.getLogger('update_tags')

# 定义常量
API_DATA_DIR = "api/data"
PROJECT_DATA_DIR = "project/src/data"
METADATA_FILE = os.path.join(API_DATA_DIR, "images.json")
PROJECT_METADATA_FILE = os.path.join(PROJECT_DATA_DIR, "images.json")

def load_metadata(file_path):
    """加载元数据文件"""
    if not os.path.exists(file_path):
        logger.error(f"元数据文件不存在: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            logger.info(f"成功加载元数据文件: {file_path}, 包含 {len(metadata)} 条记录")
            return metadata
    except Exception as e:
        logger.error(f"加载元数据文件失败: {e}")
        return []

def save_metadata(metadata, file_path):
    """保存元数据文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"已保存元数据到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存元数据文件失败: {e}")
        return False

def update_tags(force=False):
    """更新所有图片的标签分类"""
    # 加载API元数据
    api_metadata = load_metadata(METADATA_FILE)
    if not api_metadata:
        return False
    
    # 先备份原始数据
    backup_file = f"backups/images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("backups", exist_ok=True)
    save_metadata(api_metadata, backup_file)
    logger.info(f"已创建元数据备份: {backup_file}")
    
    total_count = len(api_metadata)
    updated_count = 0
    logger.info(f"开始更新 {total_count} 条图片记录的标签...")
    
    # 遍历所有图片记录，更新标签
    for item in api_metadata:
        if "caption" not in item:
            logger.warning(f"图片记录缺少caption字段: {item.get('id', 'unknown')}")
            continue
        
        caption = item["caption"]
        original_tags = item.get("tags", [])
        
        # 如果force=False且标签不是默认列表中的"others"或"flower"，则跳过
        if not force and original_tags and original_tags[0] not in ["others", "flower"]:
            logger.debug(f"跳过图片 {item.get('id', 'unknown')}: 已有有效标签 {original_tags}")
            continue
        
        # 提取主体名词并重新分类
        main_noun = extract_main_noun(caption)
        new_tags = classify_image_to_predefined_tags(caption, main_noun)
        
        # 更新标签
        if original_tags != new_tags:
            logger.info(f"更新图片 {item.get('id', 'unknown')} 的标签: {original_tags} -> {new_tags}")
            item["tags"] = new_tags
            updated_count += 1
    
    # 保存更新后的元数据
    if updated_count > 0:
        logger.info(f"共更新了 {updated_count}/{total_count} 条图片记录的标签")
        
        # 保存到API元数据目录
        if save_metadata(api_metadata, METADATA_FILE):
            logger.info(f"成功保存更新后的API元数据到: {METADATA_FILE}")
        
        # 同步到前端数据目录
        if save_metadata(api_metadata, PROJECT_METADATA_FILE):
            logger.info(f"成功同步更新后的元数据到前端: {PROJECT_METADATA_FILE}")
        
        return True
    else:
        logger.info("没有图片记录需要更新标签")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='更新所有图片的标签分类')
    parser.add_argument('--force', action='store_true', help='强制更新所有图片的标签，即使已有有效标签')
    
    args = parser.parse_args()
    
    start_time = time.time()
    success = update_tags(args.force)
    elapsed_time = time.time() - start_time
    
    logger.info(f"更新标签分类{'成功' if success else '失败'}, 耗时: {elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main() 