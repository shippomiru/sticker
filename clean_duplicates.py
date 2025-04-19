#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clean_duplicates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('clean_duplicates')

# 目标目录
TARGET_DIR = "unsplash-images/20250418"

def main():
    """清理重复图片文件"""
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始清理 {TARGET_DIR} 中的重复文件...")
    
    # 检查目录是否存在
    if not os.path.exists(TARGET_DIR):
        logger.error(f"目录 {TARGET_DIR} 不存在")
        return
    
    # 获取目录中的所有文件
    all_files = os.listdir(TARGET_DIR)
    logger.info(f"目录中共有 {len(all_files)} 个文件")
    
    # 找出带有日期后缀的文件（如 *.jpg 23-08-03-589.jpg）
    date_suffix_pattern = re.compile(r'.*\.jpg \d{2}-\d{2}-\d{2}-\d+\.jpg$')
    duplicates = [f for f in all_files if date_suffix_pattern.match(f)]
    logger.info(f"发现 {len(duplicates)} 个带有日期后缀的重复文件")
    
    # 提取原始文件名
    removed_count = 0
    error_count = 0
    for duplicate in duplicates:
        # 提取原始文件名 (*.jpg)
        original_name = duplicate.split(" ")[0]
        if original_name in all_files:
            # 原始文件也存在，删除重复的带后缀版本
            duplicate_path = os.path.join(TARGET_DIR, duplicate)
            try:
                os.remove(duplicate_path)
                removed_count += 1
                logger.info(f"已删除重复文件: {duplicate}")
            except Exception as e:
                error_count += 1
                logger.error(f"删除文件 {duplicate} 失败: {e}")
        else:
            # 原始文件不存在，可能是命名不规范的情况
            logger.warning(f"找不到对应的原始文件: {original_name}，保留 {duplicate}")
    
    # 记录结束时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 输出结果摘要
    logger.info(f"清理完成! 耗时 {duration:.2f} 秒")
    logger.info(f"共删除 {removed_count} 个重复文件")
    if error_count > 0:
        logger.warning(f"有 {error_count} 个文件删除失败")
    
    # 再次检查文件数量
    remaining_files = len(os.listdir(TARGET_DIR))
    logger.info(f"目录中现在有 {remaining_files} 个文件")

if __name__ == "__main__":
    main() 