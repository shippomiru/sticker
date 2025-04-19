#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批次管理工具 - 用于创建和管理图片处理批次

使用方法:
    创建新批次: python3 batch_manager.py create [--date YYYYMMDD]
    列出所有批次: python3 batch_manager.py list
    检查批次状态: python3 batch_manager.py status [batch_date]
    导入图片到批次: python3 batch_manager.py import [图片目录] [--date YYYYMMDD]
    重置批次: python3 batch_manager.py reset YYYYMMDD [--confirm]
"""

import os
import sys
import glob
import json
import shutil
import argparse
import logging
from datetime import datetime
import uuid
import unsplash_importer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_manager.log')
    ]
)
logger = logging.getLogger('batch_manager')

# 定义常量
UNSPLASH_IMAGES_DIR = "unsplash-images"
PROCESSED_IMAGES_DIR = "processed-images"  # 替代 results-photos-cropped
TEMP_RESULTS_DIR = "temp-results"
METADATA_DIR = "metadata"
BATCH_RECORD_FILE = os.path.join(METADATA_DIR, "batches.json")

def ensure_dir_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建目录: {directory}")

def get_current_date():
    """获取当前日期字符串 (YYYYMMDD)"""
    return datetime.now().strftime('%Y%m%d')

def load_batch_records():
    """加载批次记录文件"""
    ensure_dir_exists(METADATA_DIR)
    if os.path.exists(BATCH_RECORD_FILE):
        with open(BATCH_RECORD_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"警告: 批次记录文件格式错误，将创建新记录")
                return {"batches": []}
    return {"batches": []}

def save_batch_records(records):
    """保存批次记录"""
    with open(BATCH_RECORD_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info(f"批次记录已保存到: {BATCH_RECORD_FILE}")

def create_batch(batch_date=None):
    """创建新批次"""
    # 如果未指定日期，使用当前日期
    if batch_date is None:
        batch_date = get_current_date()
    
    # 移除任何已有的后缀，只保留日期部分 (YYYYMMDD)
    # 例如: 20250418_1 -> 20250418
    if '_' in batch_date:
        batch_date = batch_date.split('_')[0]
        logger.info(f"已移除批次名称中的后缀，使用纯日期: {batch_date}")
    
    # 加载现有批次记录
    records = load_batch_records()
    
    # 检查批次是否已存在，如果存在则直接返回现有批次ID
    for existing_batch in records["batches"]:
        if existing_batch["date"] == batch_date:
            logger.info(f"批次 {batch_date} 已存在，将使用现有批次")
            return batch_date
    
    # 创建批次目录
    batch_input_dir = os.path.join(UNSPLASH_IMAGES_DIR, batch_date)
    batch_output_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
    batch_temp_dir = os.path.join(TEMP_RESULTS_DIR, batch_date)
    
    # 确保目录存在
    ensure_dir_exists(batch_input_dir)
    ensure_dir_exists(batch_output_dir)
    ensure_dir_exists(batch_temp_dir)
    
    # 添加新批次记录
    records["batches"].append({
        "date": batch_date,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "input_dir": batch_input_dir,
        "output_dir": batch_output_dir,
        "temp_dir": batch_temp_dir,
        "image_count": 0,
        "processed_count": 0
    })
    
    save_batch_records(records)
    logger.info(f"已创建新批次: {batch_date}")
    logger.info(f"原始图片目录: {batch_input_dir}")
    logger.info(f"输出图片目录: {batch_output_dir}")
    
    return batch_date

def list_batches():
    """列出所有批次"""
    records = load_batch_records()
    
    if not records["batches"]:
        print("没有找到任何批次记录")
        return
    
    print("\n===== 批次列表 =====")
    for batch in sorted(records["batches"], key=lambda x: x["date"], reverse=True):
        print(f"批次日期: {batch['date']}")
        print(f"  创建时间: {batch['created_at']}")
        print(f"  状态: {batch['status']}")
        print(f"  图片数量: {batch['image_count']}")
        print(f"  已处理: {batch['processed_count']}")
        print(f"  输入目录: {batch['input_dir']}")
        print(f"  输出目录: {batch['output_dir']}")
        print("-" * 30)

def get_batch_status(batch_date):
    """获取指定批次的状态"""
    if batch_date is None:
        batch_date = get_current_date()
    
    records = load_batch_records()
    
    # 查找批次
    batch = None
    for b in records["batches"]:
        if b["date"] == batch_date:
            batch = b
            break
    
    if not batch:
        print(f"未找到批次: {batch_date}")
        return
    
    # 更新当前状态
    batch_input_dir = batch["input_dir"]
    batch_output_dir = batch["output_dir"]
    
    # 统计原始图片数量
    jpg_files = glob.glob(os.path.join(batch_input_dir, "*.jpg"))
    batch["image_count"] = len(jpg_files)
    
    # 统计已处理图片数量
    processed_files = glob.glob(os.path.join(batch_output_dir, "*_cropped.png"))
    batch["processed_count"] = len(processed_files)
    
    # 更新状态
    if batch["processed_count"] == 0:
        batch["status"] = "created"
    elif batch["processed_count"] < batch["image_count"]:
        batch["status"] = "processing"
    else:
        batch["status"] = "completed"
    
    # 保存更新后的记录
    save_batch_records(records)
    
    # 显示状态
    print(f"\n===== 批次 {batch_date} 状态 =====")
    print(f"图片总数: {batch['image_count']}")
    print(f"已处理数: {batch['processed_count']}")
    print(f"处理进度: {batch['processed_count']}/{batch['image_count']} ({round(batch['processed_count']*100/max(1, batch['image_count']), 1)}%)")
    print(f"当前状态: {batch['status']}")
    print(f"输入目录: {batch['input_dir']}")
    print(f"输出目录: {batch['output_dir']}")
    
    return batch

def import_images(source_dir, batch_date=None):
    """导入图片到批次"""
    if batch_date is None:
        batch_date = get_current_date()
    
    # 确保批次存在
    create_batch(batch_date)
    
    # 获取批次输入目录
    records = load_batch_records()
    batch = None
    for b in records["batches"]:
        if b["date"] == batch_date:
            batch = b
            break
    
    if not batch:
        print(f"未找到批次: {batch_date}")
        return 0
    
    batch_input_dir = batch["input_dir"]
    
    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"源目录不存在: {source_dir}")
        return 0
    
    # 复制图片到批次目录
    copied_count = 0
    for file in os.listdir(source_dir):
        if file.lower().endswith(('.jpg', '.jpeg')):
            src_path = os.path.join(source_dir, file)
            dst_path = os.path.join(batch_input_dir, file)
            
            # 如果目标文件已存在，添加时间戳避免覆盖
            if os.path.exists(dst_path):
                file_name, file_ext = os.path.splitext(file)
                time_suffix = datetime.now().strftime('%H%M%S')
                dst_path = os.path.join(batch_input_dir, f"{file_name}_{time_suffix}{file_ext}")
            
            # 复制文件
            shutil.copy2(src_path, dst_path)
            copied_count += 1
            print(f"已导入: {os.path.basename(dst_path)}")
    
    # 更新批次记录
    batch["image_count"] = len(glob.glob(os.path.join(batch_input_dir, "*.jpg")))
    save_batch_records(records)
    
    print(f"\n导入完成! 共导入 {copied_count} 张图片到批次 {batch_date}")
    print(f"批次目录: {batch_input_dir}")
    print(f"图片总数: {batch['image_count']}")
    
    return copied_count

def reset_batch(batch_date, confirm=False):
    """重置批次，删除所有批次相关数据
    
    Args:
        batch_date: 批次日期
        confirm: 是否已确认操作
    """
    # 检查批次是否存在
    records = load_batch_records()
    batch_exists = False
    
    for batch in records["batches"]:
        if batch["date"] == batch_date:
            batch_exists = True
            break
    
    if not batch_exists:
        print(f"批次 {batch_date} 不存在")
        return False
    
    # 获取批次目录
    unsplash_dir = os.path.join(UNSPLASH_IMAGES_DIR, batch_date)
    processed_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
    temp_dir = os.path.join(TEMP_RESULTS_DIR, batch_date)
    
    # 检查目录是否存在
    dirs_to_clean = []
    if os.path.exists(unsplash_dir):
        dirs_to_clean.append(unsplash_dir)
    if os.path.exists(processed_dir):
        dirs_to_clean.append(processed_dir)
    if os.path.exists(temp_dir):
        dirs_to_clean.append(temp_dir)
    
    if not dirs_to_clean:
        print(f"批次 {batch_date} 目录不存在，无需清理")
        
        # 从记录中删除批次
        records["batches"] = [b for b in records["batches"] if b["date"] != batch_date]
        save_batch_records(records)
        print(f"已从记录中删除批次 {batch_date}")
        
        return True
    
    # 如果没有确认，请求确认
    if not confirm:
        print(f"\n警告: 这将删除批次 {batch_date} 的所有数据，包括:")
        for dir_path in dirs_to_clean:
            file_count = len(os.listdir(dir_path))
            print(f"- {dir_path} (包含 {file_count} 个文件)")
        
        user_confirm = input("\n请输入批次日期以确认删除操作 (或按Enter取消): ")
        
        if user_confirm != batch_date:
            print("操作已取消")
            return False
    
    # 清空目录
    for dir_path in dirs_to_clean:
        try:
            shutil.rmtree(dir_path)
            print(f"已删除目录: {dir_path}")
        except Exception as e:
            print(f"删除目录失败 {dir_path}: {e}")
    
    # 从记录中删除批次
    records["batches"] = [b for b in records["batches"] if b["date"] != batch_date]
    save_batch_records(records)
    
    print(f"已重置批次 {batch_date}")
    
    # 重新创建空目录
    create_batch(batch_date)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='图片批次管理工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 创建批次命令
    create_parser = subparsers.add_parser('create', help='创建新批次')
    create_parser.add_argument('--date', help='指定批次日期 (YYYYMMDD格式)')
    
    # 列出批次命令
    subparsers.add_parser('list', help='列出所有批次')
    
    # 查看批次状态命令
    status_parser = subparsers.add_parser('status', help='查看批次状态')
    status_parser.add_argument('batch_date', nargs='?', help='批次日期 (YYYYMMDD格式，默认为当前日期)')
    
    # 导入图片命令
    import_parser = subparsers.add_parser('import', help='导入图片到批次')
    import_parser.add_argument('source_dir', help='源图片目录')
    import_parser.add_argument('--date', help='指定批次日期 (YYYYMMDD格式，默认为当前日期)')
    
    # 从Unsplash导入图片命令
    import_unsplash_parser = subparsers.add_parser('import-unsplash', help='从Unsplash导入图片到批次')
    import_unsplash_parser.add_argument('--id', help='Unsplash图片ID，多个用逗号分隔')
    import_unsplash_parser.add_argument('--query', help='搜索关键词')
    import_unsplash_parser.add_argument('--count', type=int, default=5, help='搜索导入数量 (默认: 5)')
    import_unsplash_parser.add_argument('--date', help='指定批次日期 (YYYYMMDD格式，默认为当前日期)')
    
    # 重置批次命令
    reset_parser = subparsers.add_parser('reset', help='重置批次数据')
    reset_parser.add_argument('date', help='批次日期 (YYYYMMDD)')
    reset_parser.add_argument('--confirm', action='store_true', help='确认重置操作，不再提示')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return
    
    # 执行相应的命令
    if args.command == 'create':
        create_batch(args.date)
    
    elif args.command == 'list':
        list_batches()
    
    elif args.command == 'status':
        get_batch_status(args.batch_date)
    
    elif args.command == 'import':
        import_images(args.source_dir, args.date)
    
    elif args.command == 'import-unsplash':
        # 确保至少提供了ID或关键词
        if not args.id and not args.query:
            print("错误: 必须提供图片ID (--id) 或搜索关键词 (--query)")
            return
        
        # 确保批次存在
        batch_date = args.date if args.date else get_current_date()
        create_batch(batch_date)
        
        # 从Unsplash导入图片
        if args.id:
            photo_ids = args.id.split(',')
            imported_paths = unsplash_importer.import_to_batch(batch_date, photo_ids=photo_ids)
        else:
            imported_paths = unsplash_importer.import_to_batch(batch_date, query=args.query, count=args.count)
        
        if imported_paths:
            print(f"\n成功从Unsplash导入 {len(imported_paths)} 张图片到批次 {batch_date}")
            
            # 更新批次记录
            batch = get_batch_status(batch_date)
    
    elif args.command == 'reset':
        reset_batch(args.date, args.confirm)

if __name__ == "__main__":
    main() 