#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unsplash关键词图片下载器

该脚本按顺序下载指定关键词的图片，每个关键词下载200张，默认每次下载50张。
使用4小时一个批次的方式，将同一时间段下载的图片归入同一个批次。

使用方法:
  python3 unsplash_keywords_downloader.py [--timeout 超时秒数]

配置说明:
  - 使用YYYYMMDD_N格式的批次标识（N为1-6，对应一天中的6个4小时时段）
  - 默认每次下载50张图片，每个关键词总共下载200张
  - 按列表顺序下载关键词图片
  - 为每个关键词维护单独的页码，避免重复下载
  - 使用order_by=relevant获取相关度最高的图片
  - 每次请求完成后自动增加页码，避免重复请求相同页面内容
"""

import os
import json
import time
import logging
import subprocess
import datetime
import argparse
import glob

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unsplash_keywords_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('unsplash_downloader')

# 配置参数
KEYWORDS_STATE_FILE = "metadata/keywords_state.json"
IMAGES_PER_KEYWORD = 100  # 每个关键词目标下载数量，从200改为100
BATCH_SIZE = 50  # 每次下载的默认图片数量
MAX_PER_PAGE = 30  # Unsplash API最大支持每页30张图片
UNSPLASH_IMAGES_DIR = "unsplash-images"  # 图片存储目录

# 关键词列表
KEYWORDS = [
    "airplane", "apple", "baby", "bird", "birthday", 
    "book", "camera", "car", "cat", "christmas", 
    "crown", "dog", "flower", "gun", "money", "pumpkin"
]

def ensure_dir_exists(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建目录: {directory}")

def load_keywords_state():
    """加载关键词状态"""
    ensure_dir_exists(os.path.dirname(KEYWORDS_STATE_FILE))
    
    if os.path.exists(KEYWORDS_STATE_FILE):
        try:
            with open(KEYWORDS_STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("关键词状态文件格式错误，创建新状态")
    
    # 初始化新的关键词状态
    state = {
        "current_index": 0,  # 当前处理的关键词索引
        "keywords": {keyword: 0 for keyword in KEYWORDS},  # 每个关键词已下载的数量
        "pages": {keyword: 1 for keyword in KEYWORDS},  # 每个关键词的当前页码
        "total_downloaded": 0,
        "last_run": None
    }
    
    save_keywords_state(state)
    return state

def save_keywords_state(state):
    """保存关键词状态"""
    with open(KEYWORDS_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info(f"关键词状态已保存到: {KEYWORDS_STATE_FILE}")

def get_current_batch_id():
    """获取当前批次标识符，格式为YYYYMMDD"""
    # 只使用日期作为批次ID，不再细分时段
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    return current_date

def count_files_in_batch(batch_dir):
    """统计批次目录中的图片文件数量"""
    if not os.path.exists(batch_dir):
        return 0
    image_files = glob.glob(os.path.join(batch_dir, "*.jpg"))
    return len(image_files)

def download_images(keyword, timeout=600):
    """调用unsplash_workflow.py下载指定关键词的图片
    
    Args:
        keyword: 搜索关键词
        timeout: 下载超时时间（秒）
        
    Returns:
        tuple: (批次ID, 下载数量)
    """
    batch_id = get_current_batch_id()
    batch_dir = os.path.join(UNSPLASH_IMAGES_DIR, batch_id)
    
    # 确保批次目录存在
    ensure_dir_exists(batch_dir)
    
    # 记录下载前批次目录中的文件数量
    files_before = count_files_in_batch(batch_dir)
    logger.info(f"下载前批次目录中有 {files_before} 张图片")
    
    # 加载关键词状态以获取当前页码和已下载数量
    state = load_keywords_state()
    if "pages" not in state:
        state["pages"] = {k: 1 for k in KEYWORDS}
    
    if keyword not in state["pages"]:
        state["pages"][keyword] = 1
    
    current_page = state["pages"][keyword]
    current_downloaded = state["keywords"].get(keyword, 0)
    
    # 计算还需下载的数量
    remaining_count = max(0, IMAGES_PER_KEYWORD - current_downloaded)
    if remaining_count == 0:
        logger.info(f"关键词 '{keyword}' 已达到目标下载数量 {IMAGES_PER_KEYWORD} 张，无需继续下载")
        return batch_id, 0
    
    # 如果剩余数量小于批次大小，调整本次下载数量
    count_this_batch = min(BATCH_SIZE, remaining_count)
    count_per_page = count_this_batch // 2 or 1  # 确保至少为1
    
    total_downloaded_count = 0
    pages_to_request = 2  # 默认请求两页
    
    # 如果剩余数量很少，可能只需请求一页
    if count_this_batch <= MAX_PER_PAGE // 2:
        pages_to_request = 1
    
    # 连续请求页面内容
    for page_offset in range(pages_to_request):
        # 如果已经达到了目标，跳过后续页面
        if total_downloaded_count >= remaining_count:
            break
            
        page_to_request = current_page + page_offset
        
        # 计算当前页需要下载的数量
        remaining_for_this_page = remaining_count - total_downloaded_count
        count_for_this_page = min(count_per_page, remaining_for_this_page)
        
        if count_for_this_page <= 0:
            break
        
        cmd = [
            "python3", "unsplash_workflow.py", 
            "start", 
            "--query", keyword, 
            "--count", str(count_for_this_page),
            "--batch", batch_id,
            "--order-by", "relevant",  # 使用relevant获取相关度最高的图片
            "--per-page", str(MAX_PER_PAGE),  # 使用最大每页数量
            "--page", str(page_to_request)
        ]
        
        logger.info(f"开始下载关键词 '{keyword}' 的图片 [第{page_offset+1}/{pages_to_request}页]，批次 {batch_id}，数量 {count_for_this_page}，页码 {page_to_request}")
        logger.info(f"使用参数: per_page={MAX_PER_PAGE}, order_by=relevant")
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 执行命令并捕获输出
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout
            )
            
            # 尝试从输出中解析下载数量
            page_downloaded_count = 0
            
            # 搜索标准输出和标准错误中的多种可能格式
            for output in [result.stdout, result.stderr]:
                for line in output.splitlines():
                    # 尝试多种可能的格式
                    if "成功导入:" in line or "成功导入 " in line:
                        try:
                            # 第一种格式: 成功导入: XX 张图片
                            if "成功导入:" in line:
                                part = line.split("成功导入:")[1]
                            # 第二种格式: 成功导入 XX 张图片
                            else:
                                part = line.split("成功导入 ")[1]
                                
                            if "张图片" in part:
                                num_str = part.split("张图片")[0].strip()
                                page_downloaded_count = int(num_str)
                                logger.info(f"从stderr解析出下载数量: {page_downloaded_count}")
                                break
                        except Exception as e:
                            logger.warning(f"解析'成功导入'行时出错: {e}, 行内容: {line}")
                
                # 如果已找到下载数量，跳出外层循环
                if page_downloaded_count > 0:
                    break
            
            # 如果通常的格式没有找到，尝试从importer日志中解析
            if page_downloaded_count == 0:
                # 检查unsplash_importer.log最新内容
                try:
                    with open("unsplash_importer.log", "r") as f:
                        log_content = f.readlines()[-50:]  # 读取最后50行
                        for line in log_content:
                            if "成功导入" in line and "张图片" in line:
                                try:
                                    parts = line.split("成功导入")[1].split("张图片")[0].strip()
                                    page_downloaded_count = int(parts)
                                    logger.info(f"从importer日志解析出下载数量: {page_downloaded_count}")
                                    break
                                except:
                                    pass
                except Exception as e:
                    logger.warning(f"读取importer日志失败: {e}")
            
            # 更新总下载数量
            total_downloaded_count += page_downloaded_count
            
            # 更新下一页码
            state["pages"][keyword] = page_to_request + 1
            logger.info(f"已完成页码 {page_to_request} 的请求，下载了 {page_downloaded_count} 张图片")
            
            # 如果当前页没有下载到图片，可能是已经到达最后一页
            if page_downloaded_count == 0:
                logger.info(f"页码 {page_to_request} 未下载到图片，结束当前请求循环")
                # 跳过下一个页码，尝试更远的页码
                state["pages"][keyword] = page_to_request + 2
                break
            
        except subprocess.TimeoutExpired:
            logger.error(f"下载操作超时（超过{timeout}秒）")
            # 将页码加2以避免卡在超时页面
            state["pages"][keyword] = page_to_request + 2
            logger.info(f"更新页码: 下次将使用页码 {state['pages'][keyword]}")
            break
            
        except Exception as e:
            logger.error(f"执行命令时出错: {e}")
            break
        
        # 保存当前状态以记录页码
        save_keywords_state(state)
    
    # 更新关键词状态
    state = load_keywords_state()  # 重新加载，确保获取最新状态
    state["keywords"][keyword] = current_downloaded + total_downloaded_count
    state["total_downloaded"] = state.get("total_downloaded", 0) + total_downloaded_count
    state["last_run"] = datetime.datetime.now().isoformat()
    
    logger.info(f"更新页码: 下次将使用页码 {state['pages'][keyword]}")
    save_keywords_state(state)
    
    logger.info(f"下载完成，本次共成功获取 {total_downloaded_count} 张图片")
    
    return batch_id, total_downloaded_count

def print_download_summary(state):
    """打印下载状态摘要"""
    # 获取当前关键词
    current_index = state["current_index"]
    if current_index >= len(KEYWORDS):
        current_index = len(KEYWORDS) - 1
    
    current_keyword = KEYWORDS[current_index]
    
    # 获取当前批次
    batch_id = get_current_batch_id()
    
    # 获取最近下载增量（通过比较total_downloaded）
    total_downloaded = state["total_downloaded"]
    
    logger.info("=== 下载状态摘要 ===")
    logger.info(f"当前关键词: {current_keyword} ({current_index+1}/{len(KEYWORDS)})")
    logger.info(f"当前批次: {batch_id}")
    
    if "last_total" in state:
        recent_increment = total_downloaded - state["last_total"]
        logger.info(f"本次新增: {recent_increment} 张图片")
    else:
        logger.info(f"本次新增: {0} 张图片")
    
    logger.info(f"累计下载: {total_downloaded} 张图片")
    
    # 如果有页码信息，显示
    if "pages" in state and state["pages"].get(current_keyword):
        logger.info(f"下次页码: {state['pages'][current_keyword]}")
    
    logger.info("各关键词下载状态:")
    
    # 计算每个关键词的下载状态
    for keyword in KEYWORDS:
        downloaded = state["keywords"].get(keyword, 0)
        percentage = (downloaded / IMAGES_PER_KEYWORD) * 100
        
        # 确定状态标签
        if downloaded >= IMAGES_PER_KEYWORD:
            status = "[完成]"
        elif keyword == current_keyword:
            status = "[当前]"
        else:
            status = "[等待]"
        
        next_page = state["pages"].get(keyword, 1)
        page_info = f"- 下次页码: {next_page}" if next_page else ""
        
        logger.info(f"{status} {keyword}: {downloaded}/{IMAGES_PER_KEYWORD} 张图片 ({percentage:.1f}%) {page_info}")
    
    # 保存当前总数，用于下次计算增量
    state["last_total"] = total_downloaded
    save_keywords_state(state)

def should_continue_keyword(state, keyword):
    """检查是否应该继续下载当前关键词的图片"""
    downloaded = state["keywords"].get(keyword, 0)
    return downloaded < IMAGES_PER_KEYWORD

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Unsplash关键词图片下载器")
    parser.add_argument("--timeout", type=int, default=600, help="下载超时时间（秒）")
    args = parser.parse_args()
    
    timeout = args.timeout
    logger.info(f"开始运行，超时时间 {timeout} 秒")
    
    # 加载关键词状态
    state = load_keywords_state()
    
    # 获取当前关键词索引和关键词
    current_index = state["current_index"]
    if current_index >= len(KEYWORDS):
        logger.info("所有关键词都已完成下载！")
        return
    
    current_keyword = KEYWORDS[current_index]
    
    # 检查当前关键词是否已完成
    if not should_continue_keyword(state, current_keyword):
        # 更新索引到下一个未完成的关键词
        next_index = current_index
        for i, keyword in enumerate(KEYWORDS[current_index:], start=current_index):
            if should_continue_keyword(state, keyword):
                next_index = i
                break
        
        # 如果找到了下一个要处理的关键词
        if next_index != current_index:
            state["current_index"] = next_index
            current_index = next_index
            current_keyword = KEYWORDS[current_index]
            logger.info(f"关键词 '{KEYWORDS[current_index-1]}' 已完成，切换到下一个关键词 '{current_keyword}'")
            save_keywords_state(state)
        else:
            # 所有关键词都已完成
            logger.info("所有关键词都已完成下载！")
            save_keywords_state(state)
            return
    
    # 获取当前批次ID
    batch_id = get_current_batch_id()
    
    # 执行下载
    _, downloaded_count = download_images(current_keyword, timeout=timeout)
    
    # 重新加载状态以获取最新信息
    state = load_keywords_state()
    
    # 检查是否下载完成
    if not should_continue_keyword(state, current_keyword):
        # 更新到下一个关键词
        state["current_index"] = current_index + 1
        logger.info(f"关键词 '{current_keyword}' 已达到目标下载数量，下次将处理下一个关键词")
        save_keywords_state(state)
    
    # 打印状态摘要
    print_download_summary(state)

if __name__ == "__main__":
    main() 