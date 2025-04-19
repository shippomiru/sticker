#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unsplash 元数据更新工具

此脚本通过已有的Unsplash ID调用API获取完整元数据，更新images.json并保存API响应
"""

import os
import sys
import json
import time
import logging
import argparse
import re
from datetime import datetime

# 导入unsplash_importer模块中的函数
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from unsplash_importer import (
    get_photo_by_id, 
    load_id_index,
    extract_unsplash_id,
    ensure_dir_exists,
    METADATA_DIR
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_metadata.log')
    ]
)
logger = logging.getLogger('update_metadata')

# 图片元数据文件
IMAGES_JSON_FILE = "api/data/images.json"
API_METADATA_DIR = os.path.join(METADATA_DIR, "api_metadata")

# 执行结果记录文件
SUCCESS_LOG_FILE = "metadata/update_success.json"
FAILED_LOG_FILE = "metadata/update_failed.json"

def load_images_metadata():
    """加载图片元数据"""
    if os.path.exists(IMAGES_JSON_FILE):
        try:
            with open(IMAGES_JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"images.json 格式错误")
            return []
    logger.warning(f"images.json 不存在")
    return []

def save_images_metadata(images_data):
    """保存图片元数据"""
    # 备份原文件
    if os.path.exists(IMAGES_JSON_FILE):
        backup_file = f"{IMAGES_JSON_FILE}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            with open(IMAGES_JSON_FILE, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            logger.info(f"已备份原始元数据文件: {backup_file}")
        except Exception as e:
            logger.error(f"备份元数据文件失败: {e}")
    
    # 保存新文件
    try:
        with open(IMAGES_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, indent=2, ensure_ascii=False)
        logger.info(f"图片元数据已保存到: {IMAGES_JSON_FILE}")
    except Exception as e:
        logger.error(f"保存元数据文件失败: {e}")

def load_result_log(log_file):
    """加载结果日志文件"""
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"结果日志文件 {log_file} 格式错误，创建新文件")
            return {"ids": [], "timestamps": {}, "details": {}}
    return {"ids": [], "timestamps": {}, "details": {}}

def save_result_log(log_file, log_data):
    """保存结果日志文件"""
    ensure_dir_exists(os.path.dirname(log_file))
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存结果日志文件 {log_file} 失败: {e}")

def add_to_result_log(log_file, unsplash_id, image_id, reason=""):
    """添加ID到结果日志"""
    log_data = load_result_log(log_file)
    
    # 如果ID不在列表中，添加它
    if unsplash_id not in log_data["ids"]:
        log_data["ids"].append(unsplash_id)
    
    # 更新时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_data["timestamps"][unsplash_id] = timestamp
    
    # 添加详细信息
    if "details" not in log_data:
        log_data["details"] = {}
    
    log_data["details"][unsplash_id] = {
        "image_id": image_id,
        "timestamp": timestamp,
        "reason": reason
    }
    
    # 保存日志
    save_result_log(log_file, log_data)

def extract_real_unsplash_id(image_id):
    """从图片ID中提取真实的Unsplash ID
    
    images.json中的ID格式通常是: username-photoId-unsplash
    真实的Unsplash ID仅为中间部分
    """
    # 如果已经是纯ID格式，直接返回
    if re.match(r'^[A-Za-z0-9_-]{11}$', image_id):
        return image_id
    
    # 处理标准格式: username-photoID-unsplash
    match = re.search(r'[-_]([A-Za-z0-9_-]{11})(?:-unsplash)?$', image_id)
    if match:
        return match.group(1)
    
    # 尝试在ID中查找11位ID
    match = re.search(r'([A-Za-z0-9_-]{11})', image_id)
    if match:
        return match.group(1)
    
    # 没有找到合适的ID，返回原始ID
    return image_id

def update_image_with_api_data(image, api_data):
    """用API返回的数据更新图片元数据"""
    # 更新基本字段
    if not image.get("unsplash_id"):
        image["unsplash_id"] = api_data["id"]
    
    if not image.get("download_location") and "links" in api_data and "download_location" in api_data["links"]:
        image["download_location"] = api_data["links"]["download_location"]
    
    # 更新作者信息
    if not image.get("author") and "user" in api_data and "name" in api_data["user"]:
        image["author"] = api_data["user"]["name"]
    
    # 添加用户名，用于构建归属链接
    if not image.get("username") and "user" in api_data and "username" in api_data["user"]:
        image["username"] = api_data["user"]["username"]
    
    # 添加摄影师主页链接
    if not image.get("photographer_url") and "user" in api_data and "links" in api_data["user"] and "html" in api_data["user"]["links"]:
        image["photographer_url"] = api_data["user"]["links"]["html"]
    
    # 更新描述
    if not image.get("caption") and api_data.get("description"):
        image["caption"] = api_data["description"]
    elif not image.get("caption") and api_data.get("alt_description"):
        image["caption"] = api_data["alt_description"]
    
    # 更新原始URL
    if not image.get("original_url"):
        image["original_url"] = f"https://unsplash.com/photos/{api_data['id']}"
    
    return image

def save_api_metadata(unsplash_id, api_data):
    """保存API返回的完整元数据"""
    if not api_data:
        return False
    
    ensure_dir_exists(API_METADATA_DIR)
    
    # 提取需要的字段
    api_metadata = {
        'unsplash_id': unsplash_id,
        'download_location': api_data['links']['download_location'],
        'author': api_data['user']['name'],
        'username': api_data['user']['username'],
        'photographer_url': api_data['user']['links']['html'],
        'description': api_data.get('description', ''),
        'alt_description': api_data.get('alt_description', ''),
        'created_at': api_data.get('created_at', ''),
        'updated_at': api_data.get('updated_at', ''),
        'api_data': api_data  # 保存完整响应
    }
    
    metadata_path = os.path.join(API_METADATA_DIR, f"{unsplash_id}.json")
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(api_metadata, f, indent=2, ensure_ascii=False)
        logger.debug(f"已保存API元数据: {metadata_path}")
        return True
    except Exception as e:
        logger.error(f"保存API元数据失败: {e}")
        return False

def update_metadata_via_api(limit=None, delay=1.0, force=False, filter_missing=False):
    """通过API更新图片元数据
    
    Args:
        limit: 最多处理的图片数量，None为全部处理
        delay: API请求之间的延迟秒数
        force: 是否强制更新已有元数据的图片
        filter_missing: 是否只处理缺少unsplash_id或download_location的图片
    """
    # 加载图片元数据和ID索引
    images_data = load_images_metadata()
    if not images_data:
        logger.error("无法加载图片元数据")
        return 0, 0
    
    # 确保API元数据目录存在
    ensure_dir_exists(API_METADATA_DIR)
    
    # 统计需要处理的图片
    images_to_update = []
    
    for image in images_data:
        # 获取图片ID，并尝试提取真实的Unsplash ID
        image_id = image.get("id", "")
        
        # 从id中提取真实unsplash_id
        unsplash_id = extract_real_unsplash_id(image_id)
        
        # 如果没有找到ID，尝试从文件名中提取
        if not unsplash_id and "path" in image:
            filename = os.path.basename(image["path"])
            unsplash_id = extract_unsplash_id(filename)
        
        if unsplash_id:
            # 保存提取出的ID
            if not image.get("unsplash_id"):
                image["unsplash_id"] = unsplash_id
                logger.debug(f"从ID '{image_id}' 提取到Unsplash ID: {unsplash_id}")
            
            # 判断是否需要更新
            need_update = False
            if force:
                need_update = True
            elif filter_missing:
                # 只处理缺少关键字段的图片
                if not image.get("download_location") or not image.get("author") or not image.get("username") or not image.get("photographer_url"):
                    need_update = True
            else:
                # 检查是否已有API元数据
                metadata_path = os.path.join(API_METADATA_DIR, f"{unsplash_id}.json")
                if not os.path.exists(metadata_path):
                    need_update = True
            
            if need_update:
                images_to_update.append((image, unsplash_id, image_id))
    
    # 如果设置了处理数量限制
    if limit and limit > 0:
        images_to_update = images_to_update[:limit]
    
    logger.info(f"需要通过API更新的图片: {len(images_to_update)}/{len(images_data)} 张")
    
    # 开始批量更新
    success_count = 0
    fail_count = 0
    
    for i, (image, unsplash_id, image_id) in enumerate(images_to_update):
        # 输出进度
        logger.info(f"处理进度: [{i+1}/{len(images_to_update)}] 更新 ID: {unsplash_id}")
        
        # 通过API获取详细信息
        api_data = get_photo_by_id(unsplash_id)
        
        if api_data:
            # 更新图片元数据
            image = update_image_with_api_data(image, api_data)
            
            # 保存API元数据
            if save_api_metadata(unsplash_id, api_data):
                success_count += 1
                logger.info(f"成功更新图片元数据: {unsplash_id}")
                add_to_result_log(SUCCESS_LOG_FILE, unsplash_id, image_id)
            else:
                fail_count += 1
                error_reason = "保存API元数据失败"
                logger.error(f"{error_reason}: {unsplash_id}")
                add_to_result_log(FAILED_LOG_FILE, unsplash_id, image_id, error_reason)
        else:
            fail_count += 1
            error_reason = "无法获取图片API数据"
            logger.error(f"{error_reason}: {unsplash_id}")
            add_to_result_log(FAILED_LOG_FILE, unsplash_id, image_id, error_reason)
        
        # 延迟避免API限制
        if i < len(images_to_update) - 1:  # 最后一个不需要延迟
            time.sleep(delay)
    
    # 保存更新后的元数据
    if success_count > 0:
        save_images_metadata(images_data)
    
    return success_count, fail_count

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Unsplash 元数据更新工具')
    parser.add_argument('--limit', type=int, default=None, 
                        help='最多处理的图片数量，默认处理全部')
    parser.add_argument('--delay', type=float, default=1.0, 
                        help='API请求间的延迟，单位秒，默认1秒')
    parser.add_argument('--force', action='store_true', 
                        help='强制更新所有图片，即使已有元数据')
    parser.add_argument('--filter-missing', action='store_true', 
                        help='只处理缺少关键字段的图片')
    parser.add_argument('--retry-failed', action='store_true',
                        help='重试之前失败的图片')
    
    args = parser.parse_args()
    
    logger.info("==== Unsplash 元数据更新工具 ====")
    logger.info(f"参数: limit={args.limit}, delay={args.delay}s, force={args.force}, filter_missing={args.filter_missing}, retry_failed={args.retry_failed}")
    
    # 如果请求重试失败的图片
    if args.retry_failed and os.path.exists(FAILED_LOG_FILE):
        logger.info("开始重试之前失败的图片...")
        try:
            with open(FAILED_LOG_FILE, 'r', encoding='utf-8') as f:
                failed_data = json.load(f)
                failed_ids = failed_data.get("ids", [])
                logger.info(f"找到 {len(failed_ids)} 个之前失败的ID")
                
                # 加载图片元数据
                images_data = load_images_metadata()
                
                # 收集需要重试的图片信息
                images_to_retry = []
                for image in images_data:
                    unsplash_id = image.get("unsplash_id") or extract_real_unsplash_id(image.get("id", ""))
                    if unsplash_id in failed_ids:
                        images_to_retry.append((image, unsplash_id, image.get("id", "")))
                
                # 设置处理限制
                if args.limit and args.limit > 0:
                    images_to_retry = images_to_retry[:args.limit]
                
                # 开始重试
                success_count = 0
                fail_count = 0
                
                logger.info(f"准备重试 {len(images_to_retry)} 张图片")
                
                for i, (image, unsplash_id, image_id) in enumerate(images_to_retry):
                    logger.info(f"重试进度: [{i+1}/{len(images_to_retry)}] 更新 ID: {unsplash_id}")
                    
                    # 调用API更新
                    api_data = get_photo_by_id(unsplash_id)
                    
                    if api_data:
                        # 更新图片元数据
                        image = update_image_with_api_data(image, api_data)
                        
                        # 保存API元数据
                        if save_api_metadata(unsplash_id, api_data):
                            success_count += 1
                            logger.info(f"成功更新图片元数据: {unsplash_id}")
                            add_to_result_log(SUCCESS_LOG_FILE, unsplash_id, image_id)
                            
                            # 从失败日志中移除
                            if unsplash_id in failed_data["ids"]:
                                failed_data["ids"].remove(unsplash_id)
                                if unsplash_id in failed_data["timestamps"]:
                                    del failed_data["timestamps"][unsplash_id]
                                if "details" in failed_data and unsplash_id in failed_data["details"]:
                                    del failed_data["details"][unsplash_id]
                        else:
                            fail_count += 1
                            error_reason = "保存API元数据失败"
                            logger.error(f"{error_reason}: {unsplash_id}")
                            add_to_result_log(FAILED_LOG_FILE, unsplash_id, image_id, error_reason)
                    else:
                        fail_count += 1
                        error_reason = "无法获取图片API数据"
                        logger.error(f"{error_reason}: {unsplash_id}")
                        add_to_result_log(FAILED_LOG_FILE, unsplash_id, image_id, error_reason)
                    
                    # 延迟避免API限制
                    if i < len(images_to_retry) - 1:  # 最后一个不需要延迟
                        time.sleep(args.delay)
                
                # 保存更新后的元数据
                if success_count > 0:
                    save_images_metadata(images_data)
                
                # 更新失败日志
                save_result_log(FAILED_LOG_FILE, failed_data)
                
                logger.info(f"==== 重试完成 ====")
                logger.info(f"成功: {success_count} 张图片")
                logger.info(f"失败: {fail_count} 张图片")
                
                return success_count, fail_count
                
        except Exception as e:
            logger.error(f"重试失败的图片时出错: {e}")
            # 继续执行正常的更新流程
    
    # 开始更新
    start_time = time.time()
    success, fail = update_metadata_via_api(
        limit=args.limit,
        delay=args.delay,
        force=args.force,
        filter_missing=args.filter_missing
    )
    
    # 输出统计
    elapsed = time.time() - start_time
    logger.info(f"==== 更新完成 ====")
    logger.info(f"成功: {success} 张图片")
    logger.info(f"失败: {fail} 张图片")
    logger.info(f"耗时: {elapsed:.1f} 秒")
    
    if fail > 0:
        logger.info(f"失败的图片ID已记录到: {FAILED_LOG_FILE}")
        logger.info(f"可以使用 --retry-failed 参数重试这些图片")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 