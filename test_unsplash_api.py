#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unsplash API 测试脚本

此脚本用于测试 Unsplash API 的基本功能，包括：
1. 验证 API 访问凭证
2. 获取随机图片
3. 获取图片详细信息
4. 下载示例图片

使用前请设置环境变量 UNSPLASH_ACCESS_KEY 或在下方直接填写您的访问密钥
"""

import os
import sys
import json
import requests
import time
from urllib.parse import urlencode
from datetime import datetime

# 设置 Unsplash API 访问密钥
# 请替换为您的实际访问密钥，或设置环境变量 UNSPLASH_ACCESS_KEY
UNSPLASH_ACCESS_KEY = os.environ.get('UNSPLASH_ACCESS_KEY', 'UNexRajSsADsyMXrFwKf9UJmNryJOohrFXpJoRwqR_8')

# API 基础 URL
UNSPLASH_API_URL = 'https://api.unsplash.com'

def validate_credentials():
    """验证 API 访问凭证是否有效"""
    if not UNSPLASH_ACCESS_KEY:
        print("错误: 缺少 Unsplash API 访问密钥")
        print("请设置环境变量 UNSPLASH_ACCESS_KEY 或在脚本中直接填写")
        return False
    
    # 尝试获取随机图片以验证凭证（不使用/me端点，因为它需要OAuth认证）
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    try:
        response = requests.get(f'{UNSPLASH_API_URL}/photos/random?count=1', headers=headers)
        
        if response.status_code == 200:
            print("API 访问凭证有效")
            return True
        elif response.status_code == 401:
            print("API 访问凭证无效")
            print(response.text)
            return False
        else:
            print(f"API 返回未知状态: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"验证凭证时发生错误: {e}")
        return False

def get_random_photos(count=1, query=None):
    """获取随机图片"""
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    params = {
        'count': count
    }
    
    if query:
        params['query'] = query
    
    try:
        url = f'{UNSPLASH_API_URL}/photos/random?{urlencode(params)}'
        print(f"请求URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            photos = response.json()
            print(f"成功获取 {len(photos)} 张随机图片")
            return photos
        else:
            print(f"获取随机图片失败，状态码: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"获取随机图片时发生错误: {e}")
        return None

def get_photo_details(photo_id):
    """获取指定图片的详细信息"""
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    try:
        response = requests.get(f'{UNSPLASH_API_URL}/photos/{photo_id}', headers=headers)
        
        if response.status_code == 200:
            photo = response.json()
            print(f"成功获取图片 {photo_id} 的详细信息")
            return photo
        else:
            print(f"获取图片详细信息失败，状态码: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"获取图片详细信息时发生错误: {e}")
        return None

def download_photo(download_url, save_path):
    """下载图片并保存到本地"""
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    try:
        # 获取下载链接
        response = requests.get(download_url, headers=headers)
        
        if response.status_code == 200:
            download_data = response.json()
            actual_download_url = download_data['url']
            
            # 下载实际图片
            img_response = requests.get(actual_download_url, stream=True)
            
            if img_response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in img_response.iter_content(1024):
                        f.write(chunk)
                print(f"图片已下载到: {save_path}")
                return True
            else:
                print(f"下载图片失败，状态码: {img_response.status_code}")
                return False
        else:
            print(f"获取下载链接失败，状态码: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"下载图片时发生错误: {e}")
        return False

def search_photos(query, page=1, per_page=10):
    """搜索图片"""
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    params = {
        'query': query,
        'page': page,
        'per_page': per_page
    }
    
    try:
        url = f'{UNSPLASH_API_URL}/search/photos?{urlencode(params)}'
        print(f"搜索URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"搜索结果: 共找到 {result['total']} 张匹配 '{query}' 的图片")
            return result
        else:
            print(f"搜索图片失败，状态码: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"搜索图片时发生错误: {e}")
        return None

def run_api_tests():
    """运行一系列API测试"""
    print("\n===== Unsplash API 测试开始 =====")
    
    # 1. 验证凭证
    if not validate_credentials():
        print("凭证验证失败，无法继续测试")
        return False
    
    # 2. 获取随机图片
    print("\n2. 获取随机图片测试")
    random_photos = get_random_photos(count=2)
    if not random_photos:
        print("获取随机图片失败，无法继续测试")
        return False
    
    # 保存示例数据
    with open('unsplash_random_sample.json', 'w', encoding='utf-8') as f:
        json.dump(random_photos, f, indent=2)
    print(f"随机图片示例已保存到 unsplash_random_sample.json")
    
    # 3. 获取图片详情
    print("\n3. 获取图片详情测试")
    photo_id = random_photos[0]['id']
    photo_details = get_photo_details(photo_id)
    if not photo_details:
        print("获取图片详情失败")
    else:
        with open('unsplash_photo_details_sample.json', 'w', encoding='utf-8') as f:
            json.dump(photo_details, f, indent=2)
        print(f"图片详情示例已保存到 unsplash_photo_details_sample.json")
    
    # 4. 搜索图片
    print("\n4. 搜索图片测试")
    search_terms = ["cat", "dog", "car", "flower"]
    for term in search_terms:
        print(f"\n搜索关键词: {term}")
        search_result = search_photos(term, per_page=5)
        if search_result and search_result['results']:
            print(f"找到 {len(search_result['results'])} 张匹配图片")
            # 保存第一个搜索结果的示例
            if term == search_terms[0]:
                with open(f'unsplash_search_sample.json', 'w', encoding='utf-8') as f:
                    json.dump(search_result, f, indent=2)
                print(f"搜索结果示例已保存到 unsplash_search_sample.json")
        time.sleep(1)  # 减少 API 请求频率
    
    # 5. 下载图片测试
    print("\n5. 下载图片测试")
    if random_photos and len(random_photos) > 0:
        photo = random_photos[0]
        photo_id = photo['id']
        download_url = photo['links']['download_location']
        save_path = f"unsplash-images/test_{photo_id}.jpg"
        
        download_success = download_photo(download_url, save_path)
        if download_success:
            print(f"图片下载测试成功: {save_path}")
        else:
            print("图片下载测试失败")
    
    print("\n===== Unsplash API 测试结束 =====")
    return True

def print_usage():
    """打印使用帮助"""
    print(f"Unsplash API 测试工具")
    print(f"用法: python3 {os.path.basename(__file__)} [命令]")
    print("")
    print(f"可用命令:")
    print(f"  random     - 获取随机图片")
    print(f"  search     - 搜索图片")
    print(f"  details    - 获取图片详情")
    print(f"  tests      - 运行所有测试")
    print("")
    print(f"示例:")
    print(f"  python3 {os.path.basename(__file__)} random")
    print(f"  python3 {os.path.basename(__file__)} search cat")
    print(f"  python3 {os.path.basename(__file__)} details abcd1234")
    print(f"  python3 {os.path.basename(__file__)} tests")

def main():
    """主函数"""
    # 检查访问密钥
    if not UNSPLASH_ACCESS_KEY:
        print("错误: 未设置 Unsplash API 访问密钥")
        print("请在环境变量中设置 UNSPLASH_ACCESS_KEY 或直接修改脚本")
        return 1
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print_usage()
        return 0
    
    command = sys.argv[1].lower()
    
    if command == 'random':
        count = 1
        query = None
        
        if len(sys.argv) > 2:
            try:
                count = int(sys.argv[2])
            except ValueError:
                query = sys.argv[2]
        
        if len(sys.argv) > 3 and query:
            try:
                count = int(sys.argv[3])
            except ValueError:
                pass
        
        random_photos = get_random_photos(count, query)
        if random_photos:
            print(json.dumps(random_photos, indent=2))
    
    elif command == 'search':
        if len(sys.argv) < 3:
            print("错误: 缺少搜索关键词")
            print("用法: python3 test_unsplash_api.py search <关键词> [页码] [每页数量]")
            return 1
        
        query = sys.argv[2]
        page = 1
        per_page = 10
        
        if len(sys.argv) > 3:
            try:
                page = int(sys.argv[3])
            except ValueError:
                pass
        
        if len(sys.argv) > 4:
            try:
                per_page = int(sys.argv[4])
            except ValueError:
                pass
        
        search_result = search_photos(query, page, per_page)
        if search_result:
            print(json.dumps(search_result, indent=2))
    
    elif command == 'details':
        if len(sys.argv) < 3:
            print("错误: 缺少图片ID")
            print("用法: python3 test_unsplash_api.py details <图片ID>")
            return 1
        
        photo_id = sys.argv[2]
        photo_details = get_photo_details(photo_id)
        if photo_details:
            print(json.dumps(photo_details, indent=2))
    
    elif command == 'tests':
        run_api_tests()
    
    else:
        print(f"未知命令: {command}")
        print_usage()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 