#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PNG图片优化工具
使用oxipng和pngquant实现高效的PNG图片压缩，同时保持透明度和良好画质

使用方法:
    python3 png_optimizer.py 输入文件/目录 [--output 输出目录] [--method oxipng|pngquant|both] [--quality 0-100]

此脚本可以单独使用，也可以被其他模块导入
"""

import os
import sys
import glob
import shutil
import logging
import argparse
import subprocess
import time
from datetime import datetime
from PIL import Image

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('png_optimizer.log')
    ]
)
logger = logging.getLogger('png_optimizer')

def ensure_dir_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建目录: {directory}")

def compress_with_oxipng(input_file, output_file=None, level=4):
    """
    使用oxipng压缩PNG文件
    
    Args:
        input_file: 输入PNG文件路径
        output_file: 输出PNG文件路径，默认为None（覆盖输入文件）
        level: 压缩级别(0-6)，默认4，数字越大压缩效果越好但越慢
        
    Returns:
        bool: 是否成功压缩
    """
    try:
        # 如果未指定输出文件，则覆盖输入文件
        if output_file is None:
            output_file = input_file
        
        # 检查输出目录是否存在
        ensure_dir_exists(os.path.dirname(output_file))
            
        # 如果输入和输出不同，先复制文件
        if input_file != output_file:
            shutil.copy2(input_file, output_file)
        
        # 使用oxipng压缩PNG
        start_time = time.time()
        original_size = os.path.getsize(output_file)
        
        logger.info(f"使用oxipng压缩PNG: {os.path.basename(input_file)}")
        
        # 构建oxipng命令
        cmd = [
            "oxipng",
            "-o", str(level),  # 压缩级别
            "--strip", "safe",  # 安全移除元数据
            "--alpha",          # 优化alpha通道
            output_file
        ]
        
        # 执行oxipng命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # 检查返回状态
        if process.returncode != 0:
            # 检查是否因为图片已经优化过
            if "already optimized" in stderr or "file already optimized" in stdout.lower() or stderr.strip() == "":
                logger.info(f"图片已经被oxipng优化过: {os.path.basename(output_file)}")
                return True
            else:
                logger.error(f"oxipng压缩失败: {stderr}")
                return False
        
        # 计算压缩结果
        new_size = os.path.getsize(output_file)
        
        # 检查是否有实际压缩效果
        if new_size >= original_size:
            logger.info(f"oxipng无法进一步压缩图片: {os.path.basename(output_file)}")
            return True
            
        compression_ratio = (original_size - new_size) / original_size * 100
        elapsed_time = time.time() - start_time
        
        logger.info(f"oxipng压缩完成: {os.path.basename(output_file)}")
        logger.info(f"  原始大小: {original_size/1024:.2f} KB")
        logger.info(f"  压缩后大小: {new_size/1024:.2f} KB")
        logger.info(f"  压缩比: {compression_ratio:.2f}%")
        logger.info(f"  耗时: {elapsed_time:.2f} 秒")
        
        return True
        
    except Exception as e:
        logger.error(f"使用oxipng压缩时出错: {str(e)}")
        return False

def compress_with_pngquant(input_file, output_file=None, quality=80):
    """
    使用pngquant压缩PNG文件
    
    Args:
        input_file: 输入PNG文件路径
        output_file: 输出PNG文件路径，默认为None（覆盖输入文件）
        quality: 输出质量(0-100)，默认80
        
    Returns:
        bool: 是否成功压缩
    """
    try:
        # 如果未指定输出文件，先创建临时文件
        temp_file = None
        if output_file is None:
            output_file = input_file
            temp_file = input_file + ".temp.png"
        else:
            # 确保输出目录存在
            ensure_dir_exists(os.path.dirname(output_file))
        
        start_time = time.time()
        original_size = os.path.getsize(input_file)
        
        logger.info(f"使用pngquant压缩PNG: {os.path.basename(input_file)}")
        
        # 转换质量范围从0-100到pngquant的1-100格式
        min_quality = max(1, int(quality * 0.8))
        max_quality = min(100, quality)
        quality_str = f"{min_quality}-{max_quality}"
        
        # 准备输出文件路径
        pngquant_output = temp_file if temp_file else output_file
        
        # 构建pngquant命令
        cmd = [
            "pngquant",
            "--quality", quality_str,  # 质量设置
            "--force",                 # 强制覆盖
            "--skip-if-larger",        # 如果压缩后更大则保留原图
            "--strip",                 # 移除元数据
            "--output", pngquant_output,  # 输出文件
            input_file                    # 输入文件
        ]
        
        # 执行pngquant命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # 检查是否因为已经压缩过导致的"失败"
        if process.returncode != 0:
            if "already optimized" in stderr or stderr.strip() == "":
                # 图片已经压缩过或无法进一步压缩
                logger.info(f"图片已经压缩过或无法进一步压缩: {os.path.basename(input_file)}")
                
                # 如果输出文件不同于输入文件，则复制原文件
                if output_file != input_file:
                    shutil.copy2(input_file, output_file)
                
                # 清理临时文件
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                
                # 虽然pngquant"失败"，但对于我们的流程来说是正常的
                return True
            else:
                # 其他错误
                logger.error(f"pngquant压缩失败: {stderr}")
                # 清理临时文件
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                return False
        
        # 如果使用临时文件，需要用临时文件替换原文件
        if temp_file:
            shutil.move(temp_file, output_file)
        
        # 计算压缩结果
        new_size = os.path.getsize(output_file)
        compression_ratio = (original_size - new_size) / original_size * 100
        elapsed_time = time.time() - start_time
        
        logger.info(f"pngquant压缩完成: {os.path.basename(output_file)}")
        logger.info(f"  原始大小: {original_size/1024:.2f} KB")
        logger.info(f"  压缩后大小: {new_size/1024:.2f} KB")
        logger.info(f"  压缩比: {compression_ratio:.2f}%")
        logger.info(f"  耗时: {elapsed_time:.2f} 秒")
        
        return True
        
    except Exception as e:
        logger.error(f"使用pngquant压缩时出错: {str(e)}")
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def compress_with_both(input_file, output_file=None, quality=80, oxipng_level=2):
    """
    使用pngquant和oxipng组合压缩PNG文件
    
    先用pngquant进行有损压缩，再用oxipng进行无损压缩
    
    Args:
        input_file: 输入PNG文件路径
        output_file: 输出PNG文件路径，默认为None（覆盖输入文件）
        quality: pngquant质量(0-100)，默认80
        oxipng_level: oxipng压缩级别(0-6)，默认2

    Returns:
        bool: 是否成功压缩
    """
    try:
        # 记录初始文件大小
        start_time = time.time()
        original_size = os.path.getsize(input_file)
        
        # 确定最终输出文件路径
        final_output = input_file if output_file is None else output_file
        
        # 创建临时文件路径
        temp_file = input_file + ".temp.png"
        
        # 第一步：使用pngquant进行有损压缩
        pngquant_success = compress_with_pngquant(input_file, temp_file, quality)
        
        # 如果pngquant成功，继续使用oxipng处理
        if pngquant_success and os.path.exists(temp_file):
            # 第二步：使用oxipng进行无损压缩
            oxipng_success = compress_with_oxipng(temp_file, final_output, oxipng_level)
            
            # 清理临时文件
            if os.path.exists(temp_file) and temp_file != final_output:
                os.remove(temp_file)
            
            if oxipng_success:
                # 计算总压缩结果
                new_size = os.path.getsize(final_output)
                compression_ratio = (original_size - new_size) / original_size * 100
                elapsed_time = time.time() - start_time
                
                logger.info(f"组合压缩完成: {os.path.basename(final_output)}")
                logger.info(f"  原始大小: {original_size/1024:.2f} KB")
                logger.info(f"  压缩后大小: {new_size/1024:.2f} KB")
                logger.info(f"  总压缩比: {compression_ratio:.2f}%")
                logger.info(f"  总耗时: {elapsed_time:.2f} 秒")
                
                return True
            else:
                # oxipng失败，但如果是因为图像已经优化过，仍然算成功
                if os.path.exists(final_output):
                    new_size = os.path.getsize(final_output)
                    if new_size <= original_size:
                        logger.info(f"组合压缩完成(只完成pngquant): {os.path.basename(final_output)}")
                        return True
                return False
        elif pngquant_success:
            # pngquant成功但可能因为已优化而没有生成文件，直接使用oxipng
            oxipng_success = compress_with_oxipng(input_file, final_output, oxipng_level)
            
            if oxipng_success:
                # 计算总结果
                new_size = os.path.getsize(final_output)
                compression_ratio = 0
                if new_size < original_size:
                    compression_ratio = (original_size - new_size) / original_size * 100
                
                elapsed_time = time.time() - start_time
                
                logger.info(f"组合压缩完成(只完成oxipng): {os.path.basename(final_output)}")
                logger.info(f"  原始大小: {original_size/1024:.2f} KB")
                logger.info(f"  压缩后大小: {new_size/1024:.2f} KB")
                logger.info(f"  总压缩比: {compression_ratio:.2f}%")
                logger.info(f"  总耗时: {elapsed_time:.2f} 秒")
                
                return True
            else:
                # 如果oxipng也失败，但结果文件等于或小于原始文件，仍然视为成功
                if os.path.exists(final_output) and os.path.getsize(final_output) <= original_size:
                    logger.info(f"图片已被充分优化，无需进一步压缩: {os.path.basename(final_output)}")
                    return True
                return False
        else:
            # pngquant失败，清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
        
    except Exception as e:
        logger.error(f"组合压缩时出错: {str(e)}")
        # 清理临时文件
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def optimize_png(input_path, output_path=None, method="both", quality=80, oxipng_level=2, force=False):
    """
    优化PNG图片
    
    Args:
        input_path: 输入PNG文件或目录路径
        output_path: 输出PNG文件或目录路径，默认为None（覆盖输入）
        method: 压缩方法，可选值为"oxipng"、"pngquant"或"both"，默认为"both"
        quality: pngquant质量(0-100)，默认80
        oxipng_level: oxipng压缩级别(0-6)，默认2
        force: 是否强制处理所有文件，即使已经被优化过，默认False
        
    Returns:
        dict: 压缩结果统计
    """
    # 初始化结果统计
    results = {
        "total_files": 0,
        "processed_files": 0,
        "skipped_files": 0,
        "total_original_size": 0,
        "total_new_size": 0,
        "compression_ratio": 0,
        "start_time": time.time()
    }
    
    # 处理目录
    if os.path.isdir(input_path):
        # 获取所有PNG文件
        png_files = glob.glob(os.path.join(input_path, "**", "*.png"), recursive=True)
        
        # 统计总文件数
        results["total_files"] = len(png_files)
        
        logger.info(f"找到 {len(png_files)} 个PNG文件需要优化")
        
        # 对每个文件进行处理
        for png_file in png_files:
            # 确定输出文件路径
            if output_path:
                # 获取相对路径，用于构建输出路径
                rel_path = os.path.relpath(png_file, input_path)
                file_output_path = os.path.join(output_path, rel_path)
                
                # 确保输出目录存在
                ensure_dir_exists(os.path.dirname(file_output_path))
            else:
                file_output_path = None  # 覆盖原文件
            
            # 记录原始文件大小
            original_size = os.path.getsize(png_file)
            results["total_original_size"] += original_size
            
            # 根据指定方法进行压缩
            success = False
            if method == "oxipng":
                success = compress_with_oxipng(png_file, file_output_path, oxipng_level)
            elif method == "pngquant":
                success = compress_with_pngquant(png_file, file_output_path, quality)
            else:  # method == "both" 或其他值
                success = compress_with_both(png_file, file_output_path, quality, oxipng_level)
            
            # 获取处理后的文件大小
            new_file_path = file_output_path or png_file
            new_size = os.path.getsize(new_file_path) if os.path.exists(new_file_path) else original_size
            
            # 更新处理结果
            if success:
                # 检查是否有实际压缩效果
                if new_size < original_size:
                    results["processed_files"] += 1
                else:
                    results["skipped_files"] += 1
                
                # 记录压缩后大小
                results["total_new_size"] += new_size
            else:
                # 处理失败，但如果文件仍然存在，记录其大小
                results["skipped_files"] += 1
                results["total_new_size"] += new_size
            
            # 打印进度
            print(f"进度: {results['processed_files'] + results['skipped_files']}/{results['total_files']} "
                  f"({(results['processed_files'] + results['skipped_files'])/results['total_files']*100:.1f}%)", 
                  end="\r")
        
        print()  # 换行
    
    # 处理单个文件
    elif os.path.isfile(input_path) and input_path.lower().endswith(".png"):
        results["total_files"] = 1
        
        # 记录原始文件大小
        original_size = os.path.getsize(input_path)
        results["total_original_size"] = original_size
        
        # 根据指定方法进行压缩
        success = False
        if method == "oxipng":
            success = compress_with_oxipng(input_path, output_path, oxipng_level)
        elif method == "pngquant":
            success = compress_with_pngquant(input_path, output_path, quality)
        else:  # method == "both" 或其他值
            success = compress_with_both(input_path, output_path, quality, oxipng_level)
        
        # 获取处理后的文件大小
        new_file_path = output_path or input_path
        new_size = os.path.getsize(new_file_path) if os.path.exists(new_file_path) else original_size
        
        # 更新处理结果
        if success:
            # 检查是否有实际压缩效果
            if new_size < original_size:
                results["processed_files"] = 1
            else:
                results["skipped_files"] = 1
            
            results["total_new_size"] = new_size
        else:
            # 处理失败，但如果文件仍然存在，记录其大小
            results["skipped_files"] = 1
            results["total_new_size"] = new_size
    
    else:
        logger.error(f"输入路径无效或非PNG文件: {input_path}")
        return results
    
    # 计算总压缩比
    if results["total_original_size"] > 0 and results["total_new_size"] > 0:
        results["compression_ratio"] = (results["total_original_size"] - results["total_new_size"]) / results["total_original_size"] * 100
    
    # 计算总耗时
    results["elapsed_time"] = time.time() - results["start_time"]
    
    # 打印总结
    logger.info(f"\n压缩结果统计:")
    logger.info(f"  处理文件数: {results['processed_files']}/{results['total_files']}")
    logger.info(f"  跳过文件数: {results['skipped_files']}/{results['total_files']}")
    logger.info(f"  原始总大小: {results['total_original_size']/1024/1024:.2f} MB")
    logger.info(f"  压缩后总大小: {results['total_new_size']/1024/1024:.2f} MB")
    logger.info(f"  总压缩比: {results['compression_ratio']:.2f}%")
    logger.info(f"  总耗时: {results['elapsed_time']:.2f} 秒")
    
    return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PNG图片优化工具')
    parser.add_argument('input', help='输入PNG文件或目录路径')
    parser.add_argument('--output', help='输出PNG文件或目录路径')
    parser.add_argument('--method', choices=['oxipng', 'pngquant', 'both'], default='both',
                      help='压缩方法，默认为both')
    parser.add_argument('--quality', type=int, default=80, help='pngquant质量(0-100)，默认80')
    parser.add_argument('--oxipng-level', type=int, default=2, help='oxipng压缩级别(0-6)，默认2')
    parser.add_argument('--force', action='store_true', help='强制处理所有文件，即使已优化过')
    
    args = parser.parse_args()
    
    # 调用优化函数
    optimize_png(args.input, args.output, args.method, args.quality, args.oxipng_level, args.force)

if __name__ == "__main__":
    main() 