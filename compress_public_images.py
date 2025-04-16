#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
压缩public文件夹中的PNG图片

此脚本用于压缩project/public/images目录中的所有PNG图片，
使得用于网站展示的图片尺寸更小，加载更快。

使用方法:
    python3 compress_public_images.py [--quality 85] [--method both] [--oxipng-level 3]
"""

import os
import sys
import logging
import argparse
import shutil
import tempfile
from datetime import datetime
from png_optimizer import optimize_png

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('compress_public_images.log')
    ]
)
logger = logging.getLogger('compress_public_images')

# 定义常量
PUBLIC_IMAGES_DIR = "project/public/images"
BACKUP_DIR = "backups/public_images"

def ensure_dir_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建目录: {directory}")

def backup_images():
    """备份原始图片"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, timestamp)
    
    # 确保备份目录存在
    ensure_dir_exists(backup_path)
    
    # 复制所有图片到备份目录
    logger.info(f"开始备份 {PUBLIC_IMAGES_DIR} 目录到 {backup_path}")
    
    # 检查源目录是否存在
    if not os.path.exists(PUBLIC_IMAGES_DIR):
        logger.error(f"源目录不存在: {PUBLIC_IMAGES_DIR}")
        return None
    
    # 复制文件
    copied_files = 0
    for file in os.listdir(PUBLIC_IMAGES_DIR):
        if file.endswith('.png'):
            src_file = os.path.join(PUBLIC_IMAGES_DIR, file)
            dst_file = os.path.join(backup_path, file)
            shutil.copy2(src_file, dst_file)
            copied_files += 1
    
    logger.info(f"已备份 {copied_files} 个PNG文件到 {backup_path}")
    return backup_path

def compress_public_images(method="both", quality=85, oxipng_level=3):
    """压缩public目录中的所有PNG图片
    
    Args:
        method: 压缩方法，可选值为"oxipng"、"pngquant"或"both"，默认为"both"
        quality: pngquant质量(0-100)，默认85
        oxipng_level: oxipng压缩级别(0-6)，默认3
        
    Returns:
        dict: 压缩结果统计
    """
    logger.info(f"开始压缩 {PUBLIC_IMAGES_DIR} 目录中的PNG图片...")
    logger.info(f"使用方法: {method}, 质量: {quality}, oxipng级别: {oxipng_level}")
    
    # 备份原始图片
    backup_path = backup_images()
    if not backup_path:
        return None
    
    # 压缩图片
    try:
        # 使用png_optimizer模块进行压缩
        results = optimize_png(
            PUBLIC_IMAGES_DIR,  # 输入目录
            None,               # 直接覆盖原文件
            method,
            quality,
            oxipng_level,
            force=True          # 强制处理所有文件，即使已经优化过
        )
        
        # 输出压缩统计结果
        logger.info("压缩完成！统计结果：")
        logger.info(f"- 处理文件数: {results['processed_files']}/{results['total_files']}")
        logger.info(f"- 跳过文件数: {results['skipped_files']}/{results['total_files']}")
        logger.info(f"- 原始总大小: {results['total_original_size']/1024/1024:.2f} MB")
        logger.info(f"- 压缩后总大小: {results['total_new_size']/1024/1024:.2f} MB")
        logger.info(f"- 总压缩比: {results['compression_ratio']:.2f}%")
        logger.info(f"- 总耗时: {results['elapsed_time']:.2f} 秒")
        logger.info(f"- 原始图片备份在: {backup_path}")
        
        return results
    
    except Exception as e:
        logger.error(f"压缩图片时出错: {str(e)}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='压缩public文件夹中的PNG图片')
    parser.add_argument('--method', choices=['oxipng', 'pngquant', 'both'], default='both',
                      help='压缩方法，默认为both')
    parser.add_argument('--quality', type=int, default=85, help='pngquant质量(0-100)，默认85')
    parser.add_argument('--oxipng-level', type=int, default=3, help='oxipng压缩级别(0-6)，默认3')
    
    args = parser.parse_args()
    
    # 运行压缩
    compress_public_images(args.method, args.quality, args.oxipng_level)
    
    # 提示可以上传到R2
    logger.info("\n提示: 压缩完成后，可以使用以下命令将优化后的图片上传到R2:")
    logger.info("python3 api/processors/upload_to_r2.py --clear")
    logger.info("python3 api/processors/upload_to_r2.py --dir project/public/images --auto-update")

if __name__ == "__main__":
    main() 