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
IMAGES_PER_KEYWORD = 200  # 每个关键词目标下载数量
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
    
    # 加载关键词状态以获取当前页码
    state = load_keywords_state()
    if "pages" not in state:
        state["pages"] = {k: 1 for k in KEYWORDS}
    
    if keyword not in state["pages"]:
        state["pages"][keyword] = 1
    
    current_page = state["pages"][keyword]
    total_downloaded_count = 0
    
    # 连续请求两页内容
    for page_offset in range(2):  # 请求当前页和下一页
        page_to_request = current_page + page_offset
        
        cmd = [
            "python3", "unsplash_workflow.py", 
            "start", 
            "--query", keyword, 
            "--count", str(BATCH_SIZE // 2),  # 每页请求数量减半，两页合计仍为BATCH_SIZE
            "--batch", batch_id,
            "--order-by", "relevant",  # 使用relevant获取相关度最高的图片
            "--per-page", str(MAX_PER_PAGE),  # 使用最大每页数量
            "--page", str(page_to_request)
        ]
        
        logger.info(f"开始下载关键词 '{keyword}' 的图片 [第{page_offset+1}/2页]，批次 {batch_id}，数量 {BATCH_SIZE // 2}，页码 {page_to_request}")
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
            
            # 搜索标准输出中的多种可能格式
            for line in result.stdout.splitlines():
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
                            logger.info(f"解析出下载数量: {page_downloaded_count}")
                            break
                    except Exception as e:
                        logger.warning(f"解析'成功导入'行时出错: {e}, 行内容: {line}")
                
                # 导入完成信息格式
                elif "导入完成:" in line and "成功导入:" in result.stdout:
                    try:
                        for detail_line in result.stdout.splitlines():
                            if "- 成功导入:" in detail_line or "- 成功导入 " in detail_line:
                                if "- 成功导入:" in detail_line:
                                    part = detail_line.split("- 成功导入:")[1]
                                else:
                                    part = detail_line.split("- 成功导入 ")[1]
                                    
                                if "张新图片" in part:
                                    num_str = part.split("张新图片")[0].strip()
                                    page_downloaded_count = int(num_str)
                                    logger.info(f"从导入完成信息中解析出下载数量: {page_downloaded_count}")
                                    break
                    except Exception as e:
                        logger.warning(f"解析'导入完成'部分时出错: {e}")
            
            # 如果stdout没有找到，尝试从stderr中查找
            if page_downloaded_count == 0 and result.stderr:
                try:
                    for line in result.stderr.splitlines():
                        if ("成功导入:" in line or "成功导入 " in line) and "张图片" in line:
                            if "成功导入:" in line:
                                part = line.split("成功导入:")[1]
                            else:
                                part = line.split("成功导入 ")[1]
                                
                            if "张图片" in part:
                                num_str = part.split("张图片")[0].strip()
                                page_downloaded_count = int(num_str)
                                logger.info(f"从stderr解析出下载数量: {page_downloaded_count}")
                                break
                except Exception as e:
                    logger.warning(f"从stderr解析时出错: {e}")
            
            # 如果上述方法都失败，检查日志文件中最近的导入信息
            if page_downloaded_count == 0:
                try:
                    # 检查unsplash_importer.log的最后几行
                    importer_log = "unsplash_importer.log"
                    if os.path.exists(importer_log):
                        with open(importer_log, 'r') as f:
                            # 读取最后1000个字符，应该足够捕获最近的导入信息
                            f.seek(0, os.SEEK_END)
                            pos = f.tell() - 1000 if f.tell() > 1000 else 0
                            f.seek(pos)
                            log_tail = f.read()
                            
                            for line in log_tail.splitlines():
                                if "成功导入:" in line and "张新图片" in line:
                                    part = line.split("成功导入:")[1]
                                    if "张新图片" in part:
                                        num_str = part.split("张新图片")[0].strip()
                                        try:
                                            page_downloaded_count = int(num_str)
                                            logger.info(f"从importer日志解析出下载数量: {page_downloaded_count}")
                                            break
                                        except ValueError:
                                            continue
                except Exception as e:
                    logger.warning(f"尝试从日志文件解析时出错: {e}")
            
            # 累加本页下载的数量
            total_downloaded_count += page_downloaded_count
            logger.info(f"已完成页码 {page_to_request} 的请求，下载了 {page_downloaded_count} 张图片")
            
            # 如果这一页没有下载到任何图片，可能到达了结尾或者遇到了API限制，结束循环
            if page_downloaded_count == 0:
                logger.info(f"页码 {page_to_request} 未下载到图片，结束当前请求循环")
                break
            
        except subprocess.TimeoutExpired:
            logger.error(f"下载操作超时（超过{timeout}秒）")
            break
        except subprocess.CalledProcessError as e:
            logger.error(f"下载失败: {e}")
            if e.stderr:
                logger.error(f"错误输出: {e.stderr}")
            break
        except Exception as e:
            logger.error(f"下载过程中发生异常: {str(e)}")
            break
    
    # 更新页码到最后请求的页面之后，避免重复请求
    state["pages"][keyword] = current_page + 2  # 无论请求了多少页，下次都从后面两页开始
    logger.info(f"更新页码: 下次将使用页码 {state['pages'][keyword]}")
    save_keywords_state(state)
    
    # 如果通过解析文本获取的下载数量为0，尝试通过文件计数确定实际下载的数量
    if total_downloaded_count == 0:
        files_after = count_files_in_batch(batch_dir)
        actual_downloaded = files_after - files_before
        if actual_downloaded > 0:
            logger.info(f"通过文件计数检测到实际下载了 {actual_downloaded} 张图片")
            total_downloaded_count = actual_downloaded
    
    logger.info(f"下载完成，本次共成功获取 {total_downloaded_count} 张图片")
    return batch_id, total_downloaded_count

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Unsplash关键词图片下载器')
    parser.add_argument('--timeout', type=int, default=600, help='下载超时时间(秒) (默认: 600)')
    args = parser.parse_args()
    
    timeout = args.timeout
    
    logger.info(f"开始运行，超时时间 {timeout} 秒")
    
    # 加载关键词状态
    state = load_keywords_state()
    
    # 检查当前关键词是否已下载完成
    current_index = state["current_index"]
    if current_index >= len(KEYWORDS):
        logger.info("所有关键词都已处理完毕")
        return
    
    current_keyword = KEYWORDS[current_index]
    current_downloaded = state["keywords"].get(current_keyword, 0)
    
    # 如果当前关键词已下载完成，移动到下一个关键词
    if current_downloaded >= IMAGES_PER_KEYWORD:
        logger.info(f"关键词 '{current_keyword}' 已下载 {current_downloaded} 张图片，已达到目标数量")
        state["current_index"] = current_index + 1
        save_keywords_state(state)
        
        # 递归调用自身，处理下一个关键词
        main()
        return
    
    # 下载图片
    batch_id, downloaded_count = download_images(current_keyword, timeout=timeout)
    
    # 重新加载状态，以确保获取最新的页码信息
    state = load_keywords_state()
    
    # 更新状态
    state["keywords"][current_keyword] = current_downloaded + downloaded_count
    state["total_downloaded"] += downloaded_count
    state["last_run"] = datetime.datetime.now().isoformat()
    
    # 如果当前关键词已下载完成，移动到下一个关键词
    if state["keywords"][current_keyword] >= IMAGES_PER_KEYWORD:
        logger.info(f"关键词 '{current_keyword}' 已下载完成，共 {state['keywords'][current_keyword]} 张图片")
        state["current_index"] = current_index + 1
    
    # 保存状态
    save_keywords_state(state)
    
    # 打印状态摘要
    logger.info("=== 下载状态摘要 ===")
    logger.info(f"当前关键词: {current_keyword} ({current_index+1}/{len(KEYWORDS)})")
    logger.info(f"当前批次: {batch_id}")
    logger.info(f"下次页码: {state['pages'][current_keyword]}")
    logger.info(f"本次新增: {downloaded_count} 张图片")
    logger.info(f"累计下载: {state['total_downloaded']} 张图片")
    
    # 打印所有关键词的下载状态
    logger.info("各关键词下载状态:")
    for i, kw in enumerate(KEYWORDS):
        status = "[当前]" if i == current_index else "[完成]" if state["keywords"].get(kw, 0) >= IMAGES_PER_KEYWORD else "[等待]"
        downloaded = state["keywords"].get(kw, 0)
        percentage = round(downloaded * 100 / IMAGES_PER_KEYWORD, 1)
        next_page = state["pages"].get(kw, 1)
        logger.info(f"{status} {kw}: {downloaded}/{IMAGES_PER_KEYWORD} 张图片 ({percentage}%) - 下次页码: {next_page}")

if __name__ == "__main__":
    main() 