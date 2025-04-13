#!/usr/bin/env python3
"""
Cloudflare R2图片上传工具

此脚本用于将处理后的图片上传到Cloudflare R2存储桶，
作为Free-PNG项目的CDN图片源。
"""

import boto3
import os
import json
import sys
from botocore.config import Config
from datetime import datetime

# 从环境变量获取R2凭证（如果没有则使用默认值）
r2_account_id = os.environ.get("R2_ACCOUNT_ID", "eee5ee0e6f10e25f8307eed29ac2eef7")
r2_access_key_id = os.environ.get("R2_ACCESS_KEY_ID", "2acb10f86d217ef811c5cba5a175c853")
r2_secret_access_key = os.environ.get("R2_SECRET_ACCESS_KEY", "ad99b43bb195fa59dad9b94ddf92ec78a3e8efd6531fcf7364c4871bd0f0852a")
r2_bucket_name = os.environ.get("R2_BUCKET_NAME", "free-png")
r2_public_url = os.environ.get("R2_PUBLIC_URL", "https://pub-ee5efd5217f84e8e8d4d7e15827887c7.r2.dev")

# R2端点URL
endpoint_url = f"https://{r2_account_id}.r2.cloudflarestorage.com"


def init_s3_client():
    """初始化S3客户端（R2兼容S3 API）"""
    try:
        return boto3.client('s3',
                       endpoint_url=endpoint_url,
                       aws_access_key_id=r2_access_key_id,
                       aws_secret_access_key=r2_secret_access_key,
                       config=Config(signature_version='s3v4'))
    except Exception as e:
        print(f"初始化S3客户端失败: {e}")
        return None


def upload_file(client, local_path, s3_key, content_type="image/png"):
    """上传单个文件到R2"""
    try:
        print(f"上传: {local_path} -> {s3_key}")
        client.upload_file(
            local_path, 
            r2_bucket_name, 
            s3_key, 
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'public, max-age=31536000',  # 一年缓存
            }
        )
        return True
    except Exception as e:
        print(f"上传失败 {local_path}: {e}")
        return False


def upload_directory(client, local_directory, prefix="", limit=None):
    """上传整个目录到R2存储桶
    
    Args:
        client: S3客户端
        local_directory: 本地图片目录
        prefix: 对象前缀
        limit: 限制上传的图片数量，用于测试
    """
    success_count = 0
    failed_count = 0
    
    if not os.path.exists(local_directory):
        print(f"目录不存在: {local_directory}")
        return success_count, failed_count
    
    for root, dirs, files in os.walk(local_directory):
        png_files = [f for f in files if f.endswith('.png')]
        # 如果设置了限制，只处理指定数量的图片
        if limit is not None:
            png_files = png_files[:limit]
            print(f"测试模式：仅上传前{limit}张图片")
        
        for file in png_files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_key = os.path.join(prefix, relative_path).replace("\\", "/")
            
            if upload_file(client, local_path, s3_key):
                success_count += 1
            else:
                failed_count += 1
            
            # 如果达到限制数量，退出处理
            if limit is not None and success_count + failed_count >= limit:
                print(f"已达到测试限制（{limit}张图片），停止上传")
                break
    
    return success_count, failed_count


def update_metadata_with_r2_urls(images_json_path="api/data/images.json"):
    """更新元数据文件中的URL为R2 CDN URL"""
    try:
        # 读取现有的元数据
        with open(images_json_path, 'r', encoding='utf-8') as f:
            images_data = json.load(f)
        
        # 创建修改后的副本
        updated_images = []
        
        for image in images_data:
            # 清理现有URL
            png_url = image["png_url"]
            sticker_url = image["sticker_url"]
            
            # 移除前导/images/
            if png_url.startswith('/images/'):
                png_url = png_url[8:]
            elif png_url.startswith('https://'):
                # 如果已经是https链接，提取文件名
                png_url = png_url.split('/')[-1]
                
            if sticker_url.startswith('/images/'):
                sticker_url = sticker_url[8:]
            elif sticker_url.startswith('https://'):
                # 如果已经是https链接，提取文件名
                sticker_url = sticker_url.split('/')[-1]
            
            # 添加R2 CDN URL前缀
            image["png_url"] = f"{r2_public_url}/{png_url}"
            image["sticker_url"] = f"{r2_public_url}/{sticker_url}"
            
            updated_images.append(image)
        
        # 备份原始文件
        backup_path = f"{images_json_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        os.rename(images_json_path, backup_path)
        print(f"已备份原始元数据文件: {backup_path}")
        
        # 写入更新后的元数据
        with open(images_json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_images, f, indent=2, ensure_ascii=False)
        
        # 同时更新前端数据文件
        frontend_path = "project/src/data/images.json"
        if os.path.exists(frontend_path):
            with open(frontend_path, 'w', encoding='utf-8') as f:
                json.dump(updated_images, f, indent=2, ensure_ascii=False)
            print(f"已更新前端数据文件: {frontend_path}")
        
        print(f"已更新元数据文件中的URL为R2 CDN: {images_json_path}")
        return True
    except Exception as e:
        print(f"更新元数据文件失败: {e}")
        return False


def main():
    """主函数"""
    # 检查凭证是否已配置
    if r2_account_id == "请替换为您的账户ID":
        print("错误: 未配置R2凭证。请设置环境变量或直接在脚本中修改凭证。")
        print("所需环境变量: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
        print("可选环境变量: R2_BUCKET_NAME, R2_PUBLIC_URL")
        return 1
    
    # 初始化S3客户端
    s3_client = init_s3_client()
    if s3_client is None:
        return 1
    
    # 上传透明背景和白边图片
    print(f"\n开始上传图片到 {r2_bucket_name} 存储桶...")
    images_dir = "results-photos-cropped"
    success, failed = upload_directory(s3_client, images_dir)
    print(f"图片上传完成! 成功: {success}, 失败: {failed}")
    
    # 如果需要，更新元数据中的URL
    if input("\n是否更新元数据文件中的URL为R2 CDN URL? (y/n): ").lower() == 'y':
        update_metadata_with_r2_urls()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 