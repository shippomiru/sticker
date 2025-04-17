#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unsplash 图片导入模块

此模块用于从 Unsplash API 获取图片并导入到批次目录，包含以下功能：
1. 根据 ID、关键词或收藏集获取图片
2. 检查图片是否已存在（基于 Unsplash ID）
3. 下载图片到指定批次目录
4. 维护 Unsplash ID 索引

使用前请设置环境变量 UNSPLASH_ACCESS_KEY 或在配置部分填写 API 密钥
"""

import os
import sys
import json
import re
import glob
import requests
import time
import logging
from datetime import datetime
from urllib.parse import urlencode
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unsplash_importer.log')
    ]
)
logger = logging.getLogger('unsplash_importer')

# 配置 Unsplash API
UNSPLASH_ACCESS_KEY = os.environ.get('UNSPLASH_ACCESS_KEY', 'UNexRajSsADsyMXrFwKf9UJmNryJOohrFXpJoRwqR_8')
UNSPLASH_API_URL = 'https://api.unsplash.com'

# 配置目录和文件路径
UNSPLASH_IMAGES_DIR = "unsplash-images"
METADATA_DIR = "metadata"
ID_INDEX_FILE = os.path.join(METADATA_DIR, "unsplash_id_index.json")

# 确保必要的目录存在
def ensure_dir_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建目录: {directory}")

# Unsplash ID 索引管理
def load_id_index():
    """加载 Unsplash ID 索引"""
    ensure_dir_exists(METADATA_DIR)
    
    if os.path.exists(ID_INDEX_FILE):
        try:
            with open(ID_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"ID 索引文件格式错误，创建新索引")
            return {"unsplash_ids": {}}
    return {"unsplash_ids": {}}

def save_id_index(index_data):
    """保存 Unsplash ID 索引"""
    with open(ID_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    logger.info(f"ID 索引已保存到: {ID_INDEX_FILE}")

def extract_unsplash_id(filename):
    """从文件名中提取 Unsplash ID
    
    支持的格式:
    1. standard-name-{ID}-unsplash.jpg 
    2. test_{ID}.jpg
    3. {ID}.jpg 
    """
    # 尝试匹配 standard-name-{ID}-unsplash.jpg 格式
    pattern1 = r'[-_]([a-zA-Z0-9_-]{11})(?:-unsplash|\.[a-z]+$)'
    match = re.search(pattern1, filename)
    if match:
        return match.group(1)
    
    # 尝试匹配 test_{ID}.jpg 格式
    pattern2 = r'test_([a-zA-Z0-9_-]{11})\.[a-z]+'
    match = re.search(pattern2, filename)
    if match:
        return match.group(1)
    
    # 尝试匹配纯 ID 格式
    pattern3 = r'^([a-zA-Z0-9_-]{11})\.[a-z]+$'
    match = re.search(pattern3, filename)
    if match:
        return match.group(1)
    
    return None

def build_id_index(force_rebuild=False):
    """构建或更新 Unsplash ID 索引
    
    Args:
        force_rebuild: 是否强制重建索引
    """
    if not force_rebuild and os.path.exists(ID_INDEX_FILE):
        logger.info("使用现有索引文件")
        return load_id_index()
    
    logger.info("开始构建 Unsplash ID 索引...")
    index_data = {"unsplash_ids": {}}
    
    # 扫描 unsplash-images 目录及其所有子目录
    for root, dirs, files in os.walk(UNSPLASH_IMAGES_DIR):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(root, file)
                unsplash_id = extract_unsplash_id(file)
                
                if unsplash_id:
                    # 使用相对路径存储
                    rel_path = os.path.relpath(file_path)
                    index_data["unsplash_ids"][unsplash_id] = rel_path
                    logger.debug(f"已添加 ID: {unsplash_id} -> {rel_path}")
    
    # 保存索引
    save_id_index(index_data)
    logger.info(f"ID 索引构建完成，共 {len(index_data['unsplash_ids'])} 条记录")
    
    return index_data

def add_to_index(unsplash_id, file_path):
    """添加新图片到索引"""
    if not unsplash_id:
        logger.warning(f"无法添加到索引：ID 为空")
        return False
    
    index_data = load_id_index()
    
    # 转换为相对路径
    rel_path = os.path.relpath(file_path)
    index_data["unsplash_ids"][unsplash_id] = rel_path
    
    save_id_index(index_data)
    logger.info(f"已添加 ID: {unsplash_id} -> {rel_path}")
    return True

def check_id_exists(unsplash_id):
    """检查 Unsplash ID 是否已存在
    
    Returns:
        tuple: (是否存在, 如果存在则返回文件路径)
    """
    if not unsplash_id:
        return False, None
    
    index_data = load_id_index()
    
    if unsplash_id in index_data["unsplash_ids"]:
        file_path = index_data["unsplash_ids"][unsplash_id]
        
        # 验证文件是否真实存在
        if os.path.exists(file_path):
            logger.info(f"ID {unsplash_id} 已存在: {file_path}")
            return True, file_path
        else:
            # 文件不存在，从索引中移除
            logger.warning(f"ID {unsplash_id} 索引存在但文件缺失: {file_path}")
            del index_data["unsplash_ids"][unsplash_id]
            save_id_index(index_data)
    
    return False, None

# Unsplash API 相关功能
def get_photo_by_id(photo_id):
    """通过 ID 获取 Unsplash 图片信息"""
    if not UNSPLASH_ACCESS_KEY:
        logger.error("缺少 Unsplash API 访问密钥")
        return None
    
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    try:
        url = f'{UNSPLASH_API_URL}/photos/{photo_id}'
        logger.info(f"获取图片信息: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            photo_data = response.json()
            logger.info(f"成功获取图片信息: {photo_id}")
            return photo_data
        else:
            logger.error(f"获取图片信息失败，状态码: {response.status_code}")
            logger.error(response.text)
            return None
    except Exception as e:
        logger.error(f"获取图片信息时发生错误: {e}")
        return None

def search_photos(query, per_page=10, page=1):
    """搜索 Unsplash 图片
    
    Args:
        query: 搜索关键词
        per_page: 每页结果数，默认10
        page: 页码，默认1
        
    Returns:
        list: 图片数据列表
    """
    if not UNSPLASH_ACCESS_KEY:
        logger.error("缺少 Unsplash API 访问密钥")
        return []
    
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    params = {
        'query': query,
        'per_page': per_page,
        'page': page
    }
    
    try:
        url = f'{UNSPLASH_API_URL}/search/photos?{urlencode(params)}'
        logger.info(f"搜索图片: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            search_data = response.json()
            photos = search_data.get('results', [])
            total_pages = search_data.get('total_pages', 0)
            total_results = search_data.get('total', 0)
            
            logger.info(f"搜索 '{query}' 成功，找到 {total_results} 个结果，共 {total_pages} 页")
            return photos, total_pages, total_results
        elif response.status_code == 429:
            logger.error(f"API速率限制，请稍后再试")
            return [], 0, 0
        else:
            logger.error(f"搜索图片失败，状态码: {response.status_code}")
            logger.error(response.text)
            return [], 0, 0
    
    except Exception as e:
        logger.error(f"搜索图片时出错: {str(e)}")
        return [], 0, 0

def download_photo(photo_data, save_dir):
    """下载 Unsplash 图片
    
    Args:
        photo_data: Unsplash 图片数据
        save_dir: 保存目录
        
    Returns:
        str: 保存的文件路径，失败则返回 None
    """
    ensure_dir_exists(save_dir)
    
    try:
        photo_id = photo_data['id']
        download_url = photo_data['urls']['full']
        
        # 先检查是否已存在
        exists, existing_path = check_id_exists(photo_id)
        if exists:
            logger.info(f"图片 {photo_id} 已存在: {existing_path}")
            return existing_path
        
        # 构造保存文件名：原始用户名-ID-unsplash.jpg
        user_name = photo_data['user']['username'].lower()
        file_name = f"{user_name}-{photo_id}-unsplash.jpg"
        save_path = os.path.join(save_dir, file_name)
        
        logger.info(f"下载图片: {download_url}")
        logger.info(f"保存路径: {save_path}")
        
        # 下载图片
        headers = {
            'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
        }
        
        # 触发 Unsplash 下载统计
        download_location = photo_data['links']['download_location']
        requests.get(download_location, headers=headers)
        
        # 实际下载图片
        response = requests.get(download_url, stream=True)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            # 添加到索引
            add_to_index(photo_id, save_path)
            
            logger.info(f"图片已下载: {save_path}")
            return save_path
        else:
            logger.error(f"下载图片失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"下载图片时发生错误: {e}")
        return None

# 图片导入功能
def import_photo_by_id(photo_id, batch_dir):
    """通过 ID 导入单张 Unsplash 图片
    
    Args:
        photo_id: Unsplash 图片 ID
        batch_dir: 批次目录
        
    Returns:
        str: 保存的文件路径，失败则返回 None
    """
    # 检查是否已存在
    exists, existing_path = check_id_exists(photo_id)
    if exists:
        logger.info(f"图片 {photo_id} 已存在: {existing_path}")
        return existing_path
    
    # 获取图片信息
    photo_data = get_photo_by_id(photo_id)
    if not photo_data:
        logger.error(f"无法获取图片 {photo_id} 的信息")
        return None
    
    # 下载图片
    return download_photo(photo_data, batch_dir)

def import_photos_by_ids(photo_ids, batch_dir):
    """通过 ID 列表导入多张 Unsplash 图片
    
    Args:
        photo_ids: Unsplash 图片 ID 列表
        batch_dir: 批次目录
        
    Returns:
        list: 成功导入的图片路径列表
    """
    ensure_dir_exists(batch_dir)
    
    imported_paths = []
    skipped_ids = []
    failed_ids = []
    
    for photo_id in photo_ids:
        # 检查是否已存在
        exists, existing_path = check_id_exists(photo_id)
        if exists:
            logger.info(f"图片 {photo_id} 已存在: {existing_path}")
            skipped_ids.append(photo_id)
            continue
        
        # 添加延迟，遵循 API 限制
        time.sleep(1)
        
        # 导入图片
        file_path = import_photo_by_id(photo_id, batch_dir)
        if file_path:
            imported_paths.append(file_path)
        else:
            failed_ids.append(photo_id)
    
    # 输出总结
    logger.info(f"导入完成:")
    logger.info(f"- 成功导入: {len(imported_paths)} 张图片")
    logger.info(f"- 已存在跳过: {len(skipped_ids)} 张图片")
    logger.info(f"- 导入失败: {len(failed_ids)} 张图片")
    
    if failed_ids:
        logger.warning(f"导入失败的 ID: {', '.join(failed_ids)}")
    
    return imported_paths

def import_photos_by_query(query, count, batch_dir):
    """通过关键词搜索导入 Unsplash 图片，确保获取到指定数量的新图片
    
    Args:
        query: 搜索关键词
        count: 需要导入的新图片数量
        batch_dir: 批次目录
        
    Returns:
        list: 成功导入的图片路径列表
    """
    ensure_dir_exists(batch_dir)
    
    # 导入统计
    imported_paths = []
    skipped_count = 0
    failed_count = 0
    total_attempts = 0
    
    # API调用限制监控
    api_limit_reached = False
    
    # 初始化分页参数
    current_page = 1
    per_page = min(30, count)  # 每页获取数量，Unsplash官方建议最大30
    
    # 当还需要更多图片且没有达到API限制时继续获取
    while len(imported_paths) < count and not api_limit_reached and total_attempts < 100:
        logger.info(f"尝试获取第{current_page}页搜索结果，每页{per_page}张图片")
        
        # 搜索图片
        photo_data_list, total_pages, total_results = search_photos(query, per_page=per_page, page=current_page)
        
        # 检查是否到达结果末尾或API限制
        if not photo_data_list:
            if total_pages == 0 and total_results == 0:
                logger.error(f"可能已达到API限制或搜索无结果")
                api_limit_reached = True
                break
            elif current_page > total_pages:
                logger.info(f"已浏览完所有搜索结果（共{total_pages}页）")
                break
        
        logger.info(f"找到第{current_page}页的 {len(photo_data_list)} 张匹配 '{query}' 的图片")
        
        # 导入图片
        for photo_data in photo_data_list:
            total_attempts += 1
            photo_id = photo_data['id']
            
            # 检查是否已存在
            exists, existing_path = check_id_exists(photo_id)
            if exists:
                logger.info(f"图片 {photo_id} 已存在: {existing_path}")
                skipped_count += 1
                continue
            
            # 添加延迟，遵循 API 限制
            time.sleep(1)
            
            # 下载图片
            file_path = download_photo(photo_data, batch_dir)
            if file_path:
                imported_paths.append(file_path)
                if len(imported_paths) >= count:
                    break  # 已获取足够数量，退出循环
            else:
                failed_count += 1
        
        # 如果已经获取到足够数量，或者已到达搜索结果末尾，退出循环
        if len(imported_paths) >= count or current_page >= total_pages:
            break
        
        # 继续下一页
        current_page += 1
    
    # 记录API限制情况
    if api_limit_reached:
        logger.warning(f"由于Unsplash API限制，无法获取更多图片。已获取: {len(imported_paths)}/{count}")
    
    # 输出总结
    logger.info(f"导入完成:")
    logger.info(f"- 成功导入: {len(imported_paths)} 张新图片")
    logger.info(f"- 已存在跳过: {skipped_count} 张图片")
    logger.info(f"- 导入失败: {failed_count} 张图片")
    logger.info(f"- 总尝试数: {total_attempts} 张图片")
    
    if len(imported_paths) < count:
        if api_limit_reached:
            logger.warning(f"由于API限制，未能获取到要求的{count}张新图片")
        else:
            logger.warning(f"无法获取到足够的新图片，可能是因为大多数搜索结果已存在或搜索结果总数不足")
    
    return imported_paths

def import_to_batch(batch_date=None, photo_ids=None, query=None, count=5):
    """导入图片到指定批次
    
    Args:
        batch_date: 批次日期 (YYYYMMDD)，如未指定则使用当前日期
        photo_ids: Unsplash 图片 ID 列表
        query: 搜索关键词
        count: 搜索导入数量
        
    Returns:
        list: 成功导入的图片路径列表
    """
    # 如果未指定批次日期，使用当前日期
    if not batch_date:
        batch_date = datetime.now().strftime('%Y%m%d')
    
    # 构建批次目录
    batch_dir = os.path.join(UNSPLASH_IMAGES_DIR, batch_date)
    ensure_dir_exists(batch_dir)
    
    # 确保索引最新
    build_id_index()
    
    # 根据提供的参数选择导入方式
    if photo_ids:
        logger.info(f"开始导入指定 ID 的图片到批次 {batch_date}")
        return import_photos_by_ids(photo_ids, batch_dir)
    
    elif query:
        logger.info(f"开始导入关键词 '{query}' 的图片到批次 {batch_date}")
        return import_photos_by_query(query, count, batch_dir)
    
    else:
        logger.error("未指定图片 ID 或搜索关键词")
        return []

def print_usage():
    """打印使用帮助"""
    print(f"Unsplash 图片导入工具")
    print(f"用法: python3 {os.path.basename(__file__)} [命令] [参数]")
    print("")
    print(f"可用命令:")
    print(f"  import-id    - 通过 ID 导入图片")
    print(f"  import-query - 通过关键词导入图片")
    print(f"  build-index  - 重建 ID 索引")
    print(f"  check-id     - 检查 ID 是否存在")
    print("")
    print(f"示例:")
    print(f"  python3 {os.path.basename(__file__)} import-id MiO4zCxACFE [--batch 20240601]")
    print(f"  python3 {os.path.basename(__file__)} import-id MiO4zCxACFE,ZRTd9_Fk6rc [--batch 20240601]")
    print(f"  python3 {os.path.basename(__file__)} import-query cat --count 5 [--batch 20240601]")
    print(f"  python3 {os.path.basename(__file__)} build-index --force")
    print(f"  python3 {os.path.basename(__file__)} check-id MiO4zCxACFE")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unsplash 图片导入工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 通过 ID 导入图片
    import_id_parser = subparsers.add_parser('import-id', help='通过 ID 导入图片')
    import_id_parser.add_argument('photo_ids', help='Unsplash 图片 ID，多个用逗号分隔')
    import_id_parser.add_argument('--batch', help='批次日期 (YYYYMMDD格式)')
    
    # 通过关键词导入图片
    import_query_parser = subparsers.add_parser('import-query', help='通过关键词导入图片')
    import_query_parser.add_argument('query', help='搜索关键词')
    import_query_parser.add_argument('--count', type=int, default=5, help='导入数量 (默认: 5)')
    import_query_parser.add_argument('--batch', help='批次日期 (YYYYMMDD格式)')
    
    # 重建 ID 索引
    build_index_parser = subparsers.add_parser('build-index', help='重建 ID 索引')
    build_index_parser.add_argument('--force', action='store_true', help='强制重建索引')
    
    # 检查 ID 是否存在
    check_id_parser = subparsers.add_parser('check-id', help='检查 ID 是否存在')
    check_id_parser.add_argument('photo_id', help='Unsplash 图片 ID')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        print_usage()
        return 0
    
    # 执行相应的命令
    if args.command == 'import-id':
        photo_ids = args.photo_ids.split(',')
        imported_paths = import_to_batch(args.batch, photo_ids=photo_ids)
        logger.info(f"成功导入 {len(imported_paths)} 张图片")
    
    elif args.command == 'import-query':
        imported_paths = import_to_batch(args.batch, query=args.query, count=args.count)
        logger.info(f"成功导入 {len(imported_paths)} 张图片")
    
    elif args.command == 'build-index':
        build_id_index(force_rebuild=args.force)
    
    elif args.command == 'check-id':
        exists, path = check_id_exists(args.photo_id)
        if exists:
            print(f"ID {args.photo_id} 存在: {path}")
        else:
            print(f"ID {args.photo_id} 不存在")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 