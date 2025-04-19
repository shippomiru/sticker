#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('delete_folders.log'),
        logging.StreamHandler()
    ]
)

# 要删除的日期前缀
DATE_PREFIX = "20250418"
# 不删除的合并文件夹
MERGED_FOLDER = f"{DATE_PREFIX}_merged"
# 批次文件夹所在路径
BASE_PATH = "unsplash-images"

def main():
    # 获取所有批次文件夹
    all_folders = [d for d in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, d))]
    
    # 筛选出指定日期的批次文件夹，但排除合并文件夹
    folders_to_delete = [folder for folder in all_folders 
                         if folder.startswith(DATE_PREFIX) and folder != MERGED_FOLDER]
    
    if not folders_to_delete:
        logging.warning(f"没有找到需要删除的批次文件夹")
        return
    
    logging.info(f"准备删除以下批次文件夹: {', '.join(folders_to_delete)}")
    
    # 删除文件夹
    deleted_folders = []
    for folder in folders_to_delete:
        folder_path = os.path.join(BASE_PATH, folder)
        # 获取文件夹中的文件数量
        file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
        
        try:
            shutil.rmtree(folder_path)
            deleted_folders.append(folder)
            logging.info(f"已删除文件夹: {folder} (包含 {file_count} 个文件)")
        except Exception as e:
            logging.error(f"删除文件夹 {folder} 时出错: {e}")
    
    logging.info(f"删除完成，总共删除了 {len(deleted_folders)} 个批次文件夹")
    if deleted_folders:
        logging.info(f"已删除的文件夹: {', '.join(deleted_folders)}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"开始删除已合并的批次文件夹 - {DATE_PREFIX}")
    
    main()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logging.info(f"删除操作完成，用时 {duration:.2f} 秒") 