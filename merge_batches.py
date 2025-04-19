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
        logging.FileHandler('merge_batches.log'),
        logging.StreamHandler()
    ]
)

# 合并日期
DATE_PREFIX = "20250418"
# 目标文件夹名称
TARGET_FOLDER = f"{DATE_PREFIX}_merged"
# 批次文件夹所在路径
BASE_PATH = "unsplash-images"

def main():
    # 获取所有批次文件夹
    all_folders = [d for d in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, d))]
    
    # 筛选出指定日期的批次文件夹
    target_folders = [folder for folder in all_folders if folder.startswith(DATE_PREFIX)]
    
    if not target_folders:
        logging.warning(f"没有找到以 {DATE_PREFIX} 开头的批次文件夹")
        return
    
    logging.info(f"找到以下批次文件夹: {', '.join(target_folders)}")
    
    # 创建合并文件夹
    merged_path = os.path.join(BASE_PATH, TARGET_FOLDER)
    if not os.path.exists(merged_path):
        os.makedirs(merged_path)
        logging.info(f"创建合并文件夹: {merged_path}")
    else:
        logging.info(f"合并文件夹已存在: {merged_path}")
    
    # 合并文件
    total_files = 0
    for folder in target_folders:
        folder_path = os.path.join(BASE_PATH, folder)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        for file in files:
            src_file = os.path.join(folder_path, file)
            dst_file = os.path.join(merged_path, file)
            
            # 如果目标文件存在，则跳过
            if os.path.exists(dst_file):
                logging.info(f"文件已存在，跳过: {file}")
                continue
            
            # 复制文件
            shutil.copy2(src_file, dst_file)
            total_files += 1
        
        logging.info(f"从 {folder} 合并了 {len(files)} 个文件")
    
    logging.info(f"合并完成，总共合并了 {total_files} 个文件到 {TARGET_FOLDER}")
    
    # 删除空文件夹
    empty_folders = []
    for folder in target_folders:
        folder_path = os.path.join(BASE_PATH, folder)
        if not os.listdir(folder_path):
            empty_folders.append(folder)
            shutil.rmtree(folder_path)
            logging.info(f"删除空文件夹: {folder}")
    
    logging.info(f"删除了 {len(empty_folders)} 个空文件夹")
    if empty_folders:
        logging.info(f"已删除的空文件夹: {', '.join(empty_folders)}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"开始合并批次 - {DATE_PREFIX}")
    
    main()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logging.info(f"合并批次完成，用时 {duration:.2f} 秒") 