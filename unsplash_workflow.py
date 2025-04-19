#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unsplash 图片处理工作流

此脚本整合了从 Unsplash 获取图片到最终发布的完整流程：
1. 从 Unsplash API 获取指定 ID 或关键词的图片
2. 导入图片到批次并运行图像处理
3. 压缩PNG图片以减小体积
4. 提供人工验收环节
5. 生成/更新元数据
6. 上传到 R2 存储
7. 更新网站数据

使用方法:
  python3 unsplash_workflow.py start --id ID1,ID2,... [--batch YYYYMMDD]
  python3 unsplash_workflow.py start --query "search term" --count 5 [--batch YYYYMMDD]
  python3 unsplash_workflow.py process --batch YYYYMMDD
  python3 unsplash_workflow.py compress --batch YYYYMMDD [--method both|oxipng|pngquant] [--quality 80]
  python3 unsplash_workflow.py verify --batch YYYYMMDD
  python3 unsplash_workflow.py metadata --batch YYYYMMDD
  python3 unsplash_workflow.py upload-r2 --batch YYYYMMDD
  python3 unsplash_workflow.py publish --batch YYYYMMDD
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import shutil
from datetime import datetime
import glob

# 导入项目中的其他模块
import unsplash_importer
from batch_manager import (
    UNSPLASH_IMAGES_DIR, 
    PROCESSED_IMAGES_DIR, 
    TEMP_RESULTS_DIR,
    METADATA_DIR,
    ensure_dir_exists,
    get_current_date,
    create_batch,
    get_batch_status,
    load_batch_records,
    save_batch_records
)
from png_optimizer import optimize_png

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unsplash_workflow.log')
    ]
)
logger = logging.getLogger('unsplash_workflow')

# 工作流状态文件
WORKFLOW_STATE_DIR = os.path.join(METADATA_DIR, "workflow_states")
ensure_dir_exists(WORKFLOW_STATE_DIR)

# 工作流阶段定义
WORKFLOW_STAGES = [
    "imported",        # 图片已从Unsplash导入
    "processed",       # 图片已处理（抠图、添加白边等）
    "compressed",      # 已压缩PNG图片
    "verified",        # 图片已通过人工验收
    "metadata_added",  # 已添加元数据
    "uploaded_r2",     # 已上传到R2
    "published"        # 已发布到网站
]

def get_workflow_state_file(batch_date):
    """获取工作流状态文件路径"""
    return os.path.join(WORKFLOW_STATE_DIR, f"workflow_state_{batch_date}.json")

def load_workflow_state(batch_date):
    """加载工作流状态"""
    state_file = get_workflow_state_file(batch_date)
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"工作流状态文件格式错误，创建新状态")
    
    # 初始化新的工作流状态
    return {
        "batch_date": batch_date,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "current_stage": "",
        "stages": {
            stage: {
                "completed": False,
                "timestamp": None,
                "details": {}
            } for stage in WORKFLOW_STAGES
        }
    }

def save_workflow_state(state):
    """保存工作流状态"""
    batch_date = state["batch_date"]
    state["updated_at"] = datetime.now().isoformat()
    
    state_file = get_workflow_state_file(batch_date)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    logger.info(f"工作流状态已保存到: {state_file}")

def update_workflow_stage(state, stage, details=None):
    """更新工作流状态
    
    Args:
        state: 工作流状态对象
        stage: 当前阶段名称
        details: 阶段详细信息，默认为None
        
    Returns:
        更新后的工作流状态对象
    """
    # 确保状态对象有效
    if not state:
        state = create_new_workflow_state()
    
    # 确保stages字段存在
    if "stages" not in state:
        state["stages"] = {}
    
    # 确保每个阶段都有对应的条目
    for workflow_stage in WORKFLOW_STAGES:
        if workflow_stage not in state["stages"]:
            state["stages"][workflow_stage] = {
                "completed": False,
                "timestamp": None,
                "details": None
            }
    
    # 更新当前阶段状态
    state["stages"][stage]["completed"] = True
    state["stages"][stage]["timestamp"] = datetime.now().isoformat()
    if details:
        state["stages"][stage]["details"] = details
    
    # 设置当前阶段为最新完成的阶段
    state["current_stage"] = stage
    
    # 保存状态
    save_workflow_state(state)
    
    return state

def get_next_stage(current_stage):
    """获取下一个工作流阶段"""
    if not current_stage:
        return WORKFLOW_STAGES[0]
    
    try:
        current_index = WORKFLOW_STAGES.index(current_stage)
        if current_index < len(WORKFLOW_STAGES) - 1:
            next_stage = WORKFLOW_STAGES[current_index + 1]
            
            # 将工作流阶段名称转换为对应的命令名称
            stage_to_command = {
                "imported": "start",
                "processed": "process",
                "compressed": "compress",
                "verified": "verify",
                "metadata_added": "metadata",
                "uploaded_r2": "upload-r2",
                "published": "publish"
            }
            
            return stage_to_command.get(next_stage, next_stage)
    except ValueError:
        pass
    
    return None

def print_workflow_status(state):
    """打印工作流状态"""
    print(f"\n===== 批次 {state['batch_date']} 工作流状态 =====")
    print(f"创建时间: {state['created_at']}")
    print(f"当前阶段: {state['current_stage'] or '未开始'}")
    
    print("\n阶段完成情况:")
    for stage in WORKFLOW_STAGES:
        stage_info = state["stages"][stage]
        status = "✓ 已完成" if stage_info["completed"] else "✗ 未完成"
        timestamp = f" ({stage_info['timestamp']})" if stage_info["timestamp"] else ""
        print(f"- {stage}: {status}{timestamp}")
    
    # 查看批次状态
    print("\n批次详情:")
    batch = get_batch_status(state["batch_date"])
    if not batch:
        print("未找到批次信息")
    
    # 显示下一步操作
    next_stage = get_next_stage(state["current_stage"])
    if next_stage:
        print(f"\n下一步: {next_stage}")
        print(f"运行命令: python3 {os.path.basename(__file__)} {next_stage} --batch {state['batch_date']}")
    else:
        print("\n所有阶段已完成!")
    
    print("\n" + "="*50)

# 工作流处理函数
def import_unsplash_images(batch_date, photo_ids=None, query=None, count=5, order_by='relevant', per_page=10, page=1):
    """从Unsplash导入图片到批次
    
    Args:
        batch_date: 批次日期
        photo_ids: Unsplash图片ID列表
        query: 搜索关键词
        count: 搜索导入数量
        order_by: 搜索结果排序方式
        per_page: 每页获取数量
        page: 起始页码
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始从Unsplash导入图片到批次 {batch_date}...")
    
    # 确保批次存在
    create_batch(batch_date)
    
    # 导入图片
    try:
        if photo_ids:
            logger.info(f"通过ID导入图片: {', '.join(photo_ids)}")
            imported_paths = unsplash_importer.import_to_batch(batch_date, photo_ids=photo_ids)
        elif query:
            logger.info(f"通过关键词导入图片: {query}, count={count}, order_by={order_by}, per_page={per_page}, page={page}")
            imported_paths = unsplash_importer.import_to_batch(batch_date, query=query, count=count, 
                                                              order_by=order_by, per_page=per_page, page=page)
        else:
            logger.error("未指定图片ID或搜索关键词")
            return False, {"error": "未指定图片ID或搜索关键词"}
        
        # 检查导入结果
        if not imported_paths:
            logger.warning("没有新图片导入")
            return False, {"warning": "没有新图片导入，可能图片已存在或搜索未找到结果"}
        
        # 获取批次状态
        batch = get_batch_status(batch_date)
        
        # 返回结果
        result = {
            "imported_count": len(imported_paths),
            "imported_paths": imported_paths,
            "batch_status": {
                "image_count": batch["image_count"] if batch else 0,
                "processed_count": batch["processed_count"] if batch else 0
            }
        }
        
        logger.info(f"成功导入 {len(imported_paths)} 张图片到批次 {batch_date}")
        return True, result
        
    except Exception as e:
        logger.error(f"导入图片时出错: {str(e)}")
        return False, {"error": str(e)}

def process_images(batch_date):
    """处理批次中的图片
    
    Args:
        batch_date: 批次日期
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始处理批次 {batch_date} 中的图片...")
    
    # 检查批次是否存在
    batch = get_batch_status(batch_date)
    if not batch:
        logger.error(f"批次 {batch_date} 不存在")
        return False, {"error": f"批次 {batch_date} 不存在"}
    
    # 检查是否有图片需要处理
    if batch["image_count"] == 0:
        logger.warning(f"批次 {batch_date} 中没有图片")
        return False, {"warning": "批次中没有图片"}
    
    # 检查是否已全部处理完成
    if batch["processed_count"] >= batch["image_count"]:
        logger.info(f"批次 {batch_date} 中的图片已全部处理完成")
        return True, {"status": "已完成", "processed_count": batch["processed_count"]}
    
    # 调用图像处理脚本
    try:
        cmd = ["python3", "process_images.py", "--batch", batch_date]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 实时输出处理日志
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"处理图片失败: {stderr}")
            return False, {"error": stderr}
        
        # 获取更新后的批次状态
        updated_batch = get_batch_status(batch_date)
        
        # 返回结果
        result = {
            "processed_count": updated_batch["processed_count"],
            "total_count": updated_batch["image_count"],
            "output_dir": updated_batch["output_dir"]
        }
        
        logger.info(f"成功处理批次 {batch_date} 中的图片，已处理 {updated_batch['processed_count']}/{updated_batch['image_count']} 张图片")
        return True, result
        
    except Exception as e:
        logger.error(f"处理图片时出错: {str(e)}")
        return False, {"error": str(e)}

def verify_images(batch_date):
    """人工验收批次中的图片
    
    Args:
        batch_date: 批次日期
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始人工验收批次 {batch_date} 中的图片...")
    
    # 检查批次是否存在
    batch = get_batch_status(batch_date)
    if not batch:
        logger.error(f"批次 {batch_date} 不存在")
        return False, {"error": f"批次 {batch_date} 不存在"}
    
    # 检查图片是否已处理
    if batch["processed_count"] == 0:
        logger.warning(f"批次 {batch_date} 中没有已处理的图片")
        return False, {"warning": "批次中没有已处理的图片，请先处理图片"}
    
    # 处理未完成的情况
    if batch["processed_count"] < batch["image_count"]:
        logger.warning(f"批次 {batch_date} 中有 {batch['image_count'] - batch['processed_count']} 张图片尚未处理")
        proceed = input(f"是否继续验收已处理的 {batch['processed_count']} 张图片？(y/n): ")
        if proceed.lower() != 'y':
            logger.info("验收已取消")
            return False, {"status": "已取消"}
    
    # 展示图片并等待验收
    output_dir = batch["output_dir"]
    print(f"\n请验收批次 {batch_date} 中的图片")
    print(f"图片位置: {output_dir}")
    print("目录中包含以下处理结果:")
    print("1. 原始图片: *.jpg")
    print("2. 透明背景图片: *_transparent.png")
    print("3. 白边贴纸风格图片: *_cropped.png")
    
    # 提示用户打开文件浏览器查看图片
    print("\n请在文件浏览器中查看图片并验收")
    open_explorer = input("是否打开文件浏览器查看图片？(y/n): ")
    if open_explorer.lower() == 'y':
        try:
            # 根据操作系统打开文件浏览器
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', output_dir])
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['explorer', output_dir])
            else:  # Linux
                subprocess.run(['xdg-open', output_dir])
        except Exception as e:
            logger.error(f"打开文件浏览器失败: {str(e)}")
    
    # 用户验收确认
    confirm = input("\n请确认所有图片是否合格？(y/n): ")
    if confirm.lower() != 'y':
        logger.warning("验收未通过")
        reason = input("请简要说明未通过原因: ")
        return False, {"status": "未通过", "reason": reason}
    
    # 验收通过，标记批次为已验收
    # 获取记录
    records = load_batch_records()
    for b in records["batches"]:
        if b["date"] == batch_date:
            # 设置已验收标志
            b["verified"] = True
            # 更新验收后图片数量
            processed_files = glob.glob(os.path.join(output_dir, "*_cropped.png"))
            unique_base_names = set()
            for file in processed_files:
                base_name = os.path.basename(file).replace("_cropped.png", "").replace("_outlined", "")
                unique_base_names.add(base_name)
            b["verified_image_count"] = len(unique_base_names)
            break
    
    # 保存更新后的记录
    save_batch_records(records)
    
    logger.info(f"批次 {batch_date} 中的图片验收通过")
    # 重新获取更新后的批次状态
    updated_batch = get_batch_status(batch_date)
    return True, {
        "status": "已通过", 
        "processed_count": updated_batch["processed_count"],
        "verified_image_count": updated_batch["verified_image_count"]
    }

def generate_metadata(batch_date):
    """为批次生成元数据
    
    1. 查找所有处理后的图片
    2. 提取图片信息
    3. 生成描述和标签
    4. 更新元数据文件
    
    Args:
        batch_date: 批次日期
    """
    logger.info(f"正在为批次 {batch_date} 生成元数据...")
    processed_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
    
    if not os.path.exists(processed_dir):
        logger.error(f"处理后的图片目录不存在: {processed_dir}")
        return False
    
    # 确保api_metadata目录存在
    api_metadata_dir = os.path.join(METADATA_DIR, "api_metadata")
    ensure_dir_exists(api_metadata_dir)
    
    # 查找所有处理后的图片
    png_files = []
    for root, dirs, files in os.walk(processed_dir):
        for file in files:
            if file.endswith("_outlined_cropped.png"):
                png_files.append(os.path.join(root, file))
    
    if not png_files:
        logger.error(f"找不到处理后的图片")
        return False
    
    logger.info(f"找到 {len(png_files)} 个待处理图片")
    
    # 使用metadata_generator模块生成元数据
    from api.processors.metadata_generator import generate_metadata_for_image
    
    # 重写元数据生成函数，优先使用保存的API数据
    def generate_with_api_data(image_path):
        # 首先使用标准函数生成元数据
        metadata = generate_metadata_for_image(image_path)
        
        if metadata and metadata.get('unsplash_id'):
            # 尝试查找对应的API元数据
            unsplash_id = metadata['unsplash_id']
            api_metadata_path = os.path.join(api_metadata_dir, f"{unsplash_id}.json")
            
            if os.path.exists(api_metadata_path):
                try:
                    with open(api_metadata_path, 'r', encoding='utf-8') as f:
                        api_data = json.load(f)
                    
                    logger.info(f"找到并使用API元数据: {unsplash_id}")
                    
                    # 使用API数据更新元数据
                    if api_data.get('download_location'):
                        metadata['download_location'] = api_data['download_location']
                    
                    if api_data.get('author'):
                        metadata['author'] = api_data['author']
                    
                    # 可以根据需要更新更多字段
                    # ...
                    
                    logger.info(f"已使用API数据更新元数据: {unsplash_id}")
                except Exception as e:
                    logger.error(f"读取API元数据失败: {e}")
        
        return metadata
    
    # 处理所有图片并生成元数据
    all_metadata = []
    for image_path in png_files:
        try:
            metadata = generate_with_api_data(image_path)
            if metadata:
                all_metadata.append(metadata)
                logger.info(f"已生成元数据: {metadata.get('id')}")
            else:
                logger.warning(f"无法为图片生成元数据: {image_path}")
        except Exception as e:
            logger.error(f"处理图片时出错: {image_path} - {str(e)}")
    
    if not all_metadata:
        logger.error("没有生成任何元数据")
        return False
    
    # 保存元数据到文件
    batch_metadata_dir = os.path.join(METADATA_DIR, batch_date)
    ensure_dir_exists(batch_metadata_dir)
    batch_metadata_file = os.path.join(batch_metadata_dir, "metadata.json")
    
    with open(batch_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"已生成 {len(all_metadata)} 条元数据，保存到: {batch_metadata_file}")
    
    # 更新工作流状态
    update_workflow_stage(load_workflow_state(batch_date), "metadata_added", {
        "count": len(all_metadata),
        "metadata_file": batch_metadata_file
    })
    
    return True

def compress_png_images(batch_date, method="both", quality=80, oxipng_level=2):
    """压缩批次中的PNG图片
    
    Args:
        batch_date: 批次日期
        method: 压缩方法，可选值为"oxipng"、"pngquant"或"both"，默认为"both"
        quality: 压缩质量(0-100)，默认80
        oxipng_level: oxipng压缩级别(0-6)，默认2
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始压缩批次 {batch_date} 中的PNG图片...")
    
    # 获取批次输出目录
    batch_output_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
    
    # 检查批次输出目录是否存在
    if not os.path.exists(batch_output_dir):
        logger.error(f"批次输出目录不存在: {batch_output_dir}")
        return False, {"error": f"批次输出目录不存在: {batch_output_dir}"}
    
    try:
        # 调用PNG优化工具
        logger.info(f"使用方法 '{method}' 压缩PNG图片，质量级别为 {quality}，oxipng级别为 {oxipng_level}")
        
        # 优化PNG图片
        results = optimize_png(
            batch_output_dir,
            None,  # 覆盖原文件
            method,
            quality,
            oxipng_level
        )
        
        # 检查结果 - 包括是否所有文件都被跳过(已经压缩过)
        if results["processed_files"] == 0 and results["skipped_files"] == 0:
            logger.warning("没有PNG图片被处理")
            return False, {"warning": "没有PNG图片被处理"}
        
        # 返回压缩结果，即使所有文件都已经最优化，也视为成功
        compression_details = {
            "processed_files": results["processed_files"],
            "skipped_files": results["skipped_files"],
            "original_size_mb": round(results["total_original_size"] / (1024 * 1024), 2),
            "compressed_size_mb": round(results["total_new_size"] / (1024 * 1024), 2),
            "compression_ratio": round(results["compression_ratio"], 2),
            "processing_time": round(results["elapsed_time"], 2)
        }
        
        # 如果有处理的文件，记录压缩比
        if results["processed_files"] > 0:
            logger.info(f"PNG压缩完成: 处理了 {results['processed_files']} 个文件，"
                        f"压缩比 {results['compression_ratio']:.2f}%")
        # 如果所有文件都已经优化，也视为成功
        elif results["skipped_files"] > 0:
            logger.info(f"PNG检查完成: {results['skipped_files']} 个文件已经是最优状态，无需进一步压缩")
        
        return True, compression_details
    
    except Exception as e:
        logger.error(f"压缩PNG图片时出错: {str(e)}")
        return False, {"error": str(e)}

def upload_to_r2(batch_date):
    """上传批次图片和元数据到 R2 存储
    
    Args:
        batch_date: 批次日期
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始上传批次 {batch_date} 数据到 R2 存储...")
    
    # 检查批次是否存在
    batch = get_batch_status(batch_date)
    if not batch:
        logger.error(f"批次 {batch_date} 不存在")
        return False, {"error": f"批次 {batch_date} 不存在"}
    
    # 检查 R2 上传工具是否配置
    try:
        import boto3
        # 调用实际的R2上传工具
        logger.info(f"正在调用R2上传工具...")
        
        # 批次目录
        batch_output_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
        
        # 检查批次输出目录是否存在
        if not os.path.exists(batch_output_dir):
            logger.error(f"批次输出目录不存在: {batch_output_dir}")
            return False, {"error": f"批次输出目录不存在: {batch_output_dir}"}
        
        # 执行增量上传命令
        cmd = ["python3", "api/processors/upload_to_r2.py", "--dir", batch_output_dir, "--auto-update"]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 实时输出处理日志
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"上传到R2失败: {stderr}")
            return False, {"error": stderr}
        
        # 解析输出中的上传结果
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 尝试从输出中提取上传统计信息
        import re
        success_match = re.search(r"成功: (\d+)", stdout)
        if success_match:
            success_count = int(success_match.group(1))
            
        skipped_match = re.search(r"跳过: (\d+)", stdout)
        if skipped_match:
            skipped_count = int(skipped_match.group(1))
            
        failed_match = re.search(r"失败: (\d+)", stdout)
        if failed_match:
            failed_count = int(failed_match.group(1))
        
        logger.info(f"成功上传批次 {batch_date} 数据到 R2 存储")
        
        # 返回上传结果
        return True, {
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "status": "已完成"
        }
    except Exception as e:
        logger.error(f"上传到R2时出错: {str(e)}")
        return False, {"error": str(e)}

def copy_to_public(batch_date):
    """将批次图片复制到public/images目录
    
    Args:
        batch_date: 批次日期
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始将批次 {batch_date} 图片复制到public/images目录...")
    
    # 检查批次是否存在
    batch = get_batch_status(batch_date)
    if not batch:
        logger.error(f"批次 {batch_date} 不存在")
        return False, {"error": f"批次 {batch_date} 不存在"}
    
    # 设置源目录和目标目录
    src_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
    dest_dir = "project/public/images"
    
    # 确保目标目录存在
    ensure_dir_exists(dest_dir)
    
    try:
        # 统计计数
        copied_count = 0
        skipped_count = 0
        
        # 遍历源目录中的所有PNG文件
        for file in os.listdir(src_dir):
            if file.endswith('.png'):
                src_file = os.path.join(src_dir, file)
                dest_file = os.path.join(dest_dir, file)
                
                # 检查目标文件是否已存在
                if os.path.exists(dest_file):
                    # 如果已存在，检查是否完全相同
                    if os.path.getsize(src_file) == os.path.getsize(dest_file):
                        logger.info(f"文件已存在且大小相同，跳过: {file}")
                        skipped_count += 1
                        continue
                
                # 复制文件
                logger.info(f"复制文件: {file}")
                shutil.copy2(src_file, dest_file)
                copied_count += 1
        
        # 记录结果
        logger.info(f"复制完成! 新复制: {copied_count}, 跳过: {skipped_count}")
        
        return True, {
            "status": "已完成",
            "copied_count": copied_count,
            "skipped_count": skipped_count
        }
        
    except Exception as e:
        logger.error(f"复制图片到public目录时出错: {str(e)}")
        return False, {"error": str(e)}

def publish_to_website(batch_date, skip_git=False):
    """将批次数据发布到网站
    
    Args:
        batch_date: 批次日期
        skip_git: 是否跳过Git提交和推送
        
    Returns:
        tuple: (成功状态, 详细信息)
    """
    logger.info(f"开始将批次 {batch_date} 数据发布到网站...")
    
    # 检查批次是否存在
    batch = get_batch_status(batch_date)
    if not batch:
        logger.error(f"批次 {batch_date} 不存在")
        return False, {"error": f"批次 {batch_date} 不存在"}
    
    # 检查元数据是否生成
    metadata_file = os.path.join(METADATA_DIR, f"metadata_{batch_date}.json")
    if not os.path.exists(metadata_file):
        logger.error(f"元数据文件未找到: {metadata_file}")
        return False, {"error": "元数据文件未生成，请先生成元数据"}
    
    try:
        # 0. 首先确保图片复制到public目录 (不需要再次压缩，因为批次图片已在compressed阶段压缩过)
        logger.info("确保批次图片已复制到public目录...")
        copy_success, copy_details = copy_to_public(batch_date)
        if not copy_success:
            logger.error(f"复制图片到public目录失败: {copy_details.get('error', '')}")
            return False, {"error": f"复制图片到public目录失败: {copy_details.get('error', '')}"}
        
        # 1. 配置 merge_metadata.py 的元数据文件路径
        # 先备份当前配置
        with open("merge_metadata.py", "r", encoding="utf-8") as f:
            merge_metadata_content = f.read()
            
        # 替换配置为当前批次
        import re
        new_content = re.sub(
            r'NEW_METADATA_FILE = ".*"', 
            f'NEW_METADATA_FILE = "{metadata_file}"',
            merge_metadata_content
        )
        
        # 保存临时修改
        with open("merge_metadata.py", "w", encoding="utf-8") as f:
            f.write(new_content)
            
        # 2. 执行元数据合并
        logger.info(f"合并元数据文件: {metadata_file}")
        
        cmd = ["python3", "merge_metadata.py"]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 实时输出处理日志
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"合并元数据失败: {stderr}")
            # 恢复原始配置
            with open("merge_metadata.py", "w", encoding="utf-8") as f:
                f.write(merge_metadata_content)
            return False, {"error": stderr}
        
        # 3. 恢复原始配置
        with open("merge_metadata.py", "w", encoding="utf-8") as f:
            f.write(merge_metadata_content)
            
        # 4. 更新元数据URL为R2 CDN链接 
        logger.info("更新元数据URL为R2 CDN链接...")
        
        cmd = ["python3", "update_metadata_urls.py"]
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 实时输出处理日志
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"更新元数据URL失败: {stderr}")
            return False, {"error": stderr}
        
        # 5. 解析输出中的更新结果
        updated_count = 0
        
        # 尝试从输出中提取更新统计信息
        import re
        updated_match = re.search(r"更新的URL数量: (\d+)", stdout)
        if updated_match:
            updated_count = int(updated_match.group(1))
        
        # 6. 提交更改到GitHub
        git_committed = False
        current_branch = None
        
        if skip_git:
            logger.info("跳过Git提交和推送步骤")
        else:
            logger.info("将更改提交到GitHub...")
            
            # 获取当前日期作为提交信息
            commit_date = datetime.now().strftime("%Y-%m-%d")
            commit_message = f"添加批次 {batch_date} 的图片和元数据 [{commit_date}]"
            
            # 检查git状态
            git_status_cmd = ["git", "status", "--porcelain"]
            git_status_process = subprocess.Popen(
                git_status_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            git_status_stdout, git_status_stderr = git_status_process.communicate()
            
            # 检查git状态命令是否成功执行
            if git_status_process.returncode != 0:
                logger.error(f"git status 命令执行失败: {git_status_stderr}")
                return False, {"error": f"git status 失败: {git_status_stderr}"}
            
            if not git_status_stdout:
                logger.info("没有需要提交的更改")
            else:
                # 有更改需要提交
                logger.info(f"发现需要提交的更改: \n{git_status_stdout}")
                
                # 获取当前分支
                git_branch_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
                git_branch_process = subprocess.Popen(
                    git_branch_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                current_branch, git_branch_stderr = git_branch_process.communicate()
                current_branch = current_branch.strip()
                
                if git_branch_process.returncode != 0:
                    logger.error(f"获取当前分支失败: {git_branch_stderr}")
                    return False, {"error": f"获取当前分支失败: {git_branch_stderr}"}
                
                logger.info(f"当前Git分支: {current_branch}")
                
                # 添加所有更改
                git_add_cmd = ["git", "add", "."]
                git_add_process = subprocess.Popen(
                    git_add_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                git_add_stdout, git_add_stderr = git_add_process.communicate()
                
                if git_add_process.returncode != 0:
                    logger.error(f"git add 失败: {git_add_stderr}")
                    return False, {"error": f"git add 失败: {git_add_stderr}"}
                
                logger.info("成功添加更改到暂存区")
                
                # 提交更改
                git_commit_cmd = ["git", "commit", "-m", commit_message]
                git_commit_process = subprocess.Popen(
                    git_commit_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                git_commit_stdout, git_commit_stderr = git_commit_process.communicate()
                
                if git_commit_process.returncode != 0:
                    logger.error(f"git commit 失败: {git_commit_stderr}")
                    return False, {"error": f"git commit 失败: {git_commit_stderr}"}
                
                logger.info(f"成功提交更改: {git_commit_stdout}")
                
                # 推送到远程仓库（使用当前分支而不是硬编码main）
                git_push_cmd = ["git", "push", "origin", current_branch]
                logger.info(f"正在推送到远程仓库: {' '.join(git_push_cmd)}")
                
                git_push_process = subprocess.Popen(
                    git_push_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                git_push_stdout, git_push_stderr = git_push_process.communicate()
                
                if git_push_process.returncode != 0:
                    logger.error(f"git push 失败: {git_push_stderr}")
                    logger.warning("请手动推送更改到远程仓库")
                    return False, {"error": f"git push 失败: {git_push_stderr}", "commit_success": True}
                
                logger.info(f"成功推送更改到GitHub分支 {current_branch}")
                git_committed = True
        
        logger.info(f"成功将批次 {batch_date} 数据发布到网站")
        
        # 返回发布结果
        return True, {
            "status": "已完成",
            "updated_count": updated_count,
            "git_committed": git_committed,
            "git_branch": current_branch,
            "skipped_git": skip_git
        }
    except Exception as e:
        logger.error(f"发布到网站时出错: {str(e)}")
        return False, {"error": str(e)}

# 命令行处理
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Unsplash 图片处理工作流')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 启动流程命令
    start_parser = subparsers.add_parser('start', help='启动新的处理流程')
    start_parser.add_argument('--id', help='Unsplash 图片 ID，多个用逗号分隔')
    start_parser.add_argument('--query', help='搜索关键词')
    start_parser.add_argument('--count', type=int, default=5, help='搜索导入数量 (默认: 5)')
    start_parser.add_argument('--batch', help='批次日期 (YYYYMMDD 格式，默认为当前日期)')
    start_parser.add_argument('--process', action='store_true', help='导入后自动处理图片')
    start_parser.add_argument('--order-by', choices=['relevant', 'latest', 'popular', 'oldest', 'views', 'downloads'], 
                            default='relevant', help='搜索结果排序方式 (默认: relevant)')
    start_parser.add_argument('--per-page', type=int, default=10, help='每页获取数量 (默认: 10, 最大: 30)')
    start_parser.add_argument('--page', type=int, default=1, help='起始页码 (默认: 1)')
    
    # 处理图片命令
    process_parser = subparsers.add_parser('process', help='处理批次中的图片')
    process_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    
    # 压缩图片命令
    compress_parser = subparsers.add_parser('compress', help='压缩批次中的PNG图片')
    compress_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    compress_parser.add_argument('--method', choices=['oxipng', 'pngquant', 'both'], default='both',
                              help='压缩方法，默认为both')
    compress_parser.add_argument('--quality', type=int, default=80, help='pngquant质量(0-100)，默认80')
    compress_parser.add_argument('--oxipng-level', type=int, default=2, help='oxipng压缩级别(0-6)，默认2')
    
    # 验证图片命令
    verify_parser = subparsers.add_parser('verify', help='人工验收批次中的图片')
    verify_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    
    # 生成元数据命令
    metadata_parser = subparsers.add_parser('metadata', help='生成批次图片的元数据')
    metadata_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    
    # 复制到public目录命令
    copy_parser = subparsers.add_parser('copy-to-public', help='将批次图片复制到public/images目录')
    copy_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    
    # 上传到 R2 命令
    upload_parser = subparsers.add_parser('upload-r2', help='上传批次图片和元数据到 R2 存储')
    upload_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    
    # 发布到网站命令
    publish_parser = subparsers.add_parser('publish', help='将批次数据发布到网站')
    publish_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    publish_parser.add_argument('--skip-git', action='store_true', help='跳过Git提交和推送步骤')
    
    # 查看状态命令
    status_parser = subparsers.add_parser('status', help='查看工作流状态')
    status_parser.add_argument('--batch', required=True, help='批次日期 (YYYYMMDD 格式)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return
    
    # 获取批次日期
    batch_date = args.batch if hasattr(args, 'batch') and args.batch else get_current_date()
    
    # 加载工作流状态
    state = load_workflow_state(batch_date)
    
    # 执行相应的命令
    if args.command == 'start':
        photo_ids = args.id.split(',') if args.id else None
        
        # 从 Unsplash 导入图片
        success, details = import_unsplash_images(
            batch_date, 
            photo_ids, 
            args.query, 
            args.count,
            args.order_by,
            args.per_page,
            args.page
        )
        
        if success:
            # 更新工作流状态
            update_workflow_stage(state, "imported", details)
            
            # 如果指定了自动处理，继续处理图片
            if args.process:
                success, details = process_images(batch_date)
                if success:
                    update_workflow_stage(state, "processed", details)
            
            # 显示工作流状态
            print_workflow_status(state)
        else:
            print(f"导入失败: {details.get('error', '') or details.get('warning', '')}")
    
    elif args.command == 'process':
        success, details = process_images(batch_date)
        
        if success:
            update_workflow_stage(state, "processed", details)
            print_workflow_status(state)
        else:
            print(f"处理失败: {details.get('error', '') or details.get('warning', '')}")
    
    elif args.command == 'verify':
        success, details = verify_images(batch_date)
        
        if success:
            update_workflow_stage(state, "verified", details)
            print_workflow_status(state)
        else:
            if details.get('status') == '已取消':
                print("验收已取消")
            else:
                print(f"验收未通过: {details.get('reason', '')}")
    
    elif args.command == 'metadata':
        success = generate_metadata(batch_date)
        
        if success:
            update_workflow_stage(state, "metadata_added")
            print_workflow_status(state)
        else:
            print(f"生成元数据失败")
    
    elif args.command == 'compress':
        success, details = compress_png_images(
            batch_date,
            args.method,
            args.quality,
            args.oxipng_level
        )
        
        if success:
            update_workflow_stage(state, "compressed", details)
            print_workflow_status(state)
        else:
            print(f"压缩PNG图片失败: {details.get('error', '') or details.get('warning', '')}")
    
    elif args.command == 'copy-to-public':
        # 复制图片到public目录
        success, details = copy_to_public(batch_date)
        
        if success:
            print(f"成功将批次 {batch_date} 图片复制到public目录")
            print(f"新复制: {details.get('copied_count', 0)}, 跳过: {details.get('skipped_count', 0)}")
        else:
            print(f"复制到public目录失败: {details.get('error', '')}")
    
    elif args.command == 'upload-r2':
        success, details = upload_to_r2(batch_date)
        
        if success:
            update_workflow_stage(state, "uploaded_r2", details)
            print_workflow_status(state)
        else:
            print(f"上传到 R2 失败: {details.get('error', '') or details.get('warning', '')}")
    
    elif args.command == 'publish':
        success, details = publish_to_website(batch_date, args.skip_git)
        
        if success:
            update_workflow_stage(state, "published", details)
            print_workflow_status(state)
            print(f"\n发布结果: ")
            print(f"- 更新的URL数量: {details.get('updated_count', 0)}")
            if details.get('skipped_git'):
                print(f"- Git操作: 已跳过")
            elif details.get('git_committed'):
                print(f"- Git提交: 成功 (分支: {details.get('git_branch', 'unknown')})")
            else:
                print(f"- Git提交: 未发现更改")
        else:
            if details.get('commit_success'):
                print(f"部分成功: 已提交到本地Git，但推送到远程仓库失败")
                print(f"请手动执行: git push origin {details.get('git_branch', '当前分支')}")
            else:
                print(f"发布失败: {details.get('error', '')}")
    
    elif args.command == 'status':
        print_workflow_status(state)

if __name__ == "__main__":
    main() 