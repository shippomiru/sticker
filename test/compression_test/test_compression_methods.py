#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PNG压缩方法比较测试脚本
正确比较三种不同的压缩方法:
1. pngquant - 有损压缩
2. oxipng - 无损压缩
3. squoosh-cli - Google的图像压缩工具

每种方法独立测试，不混合使用
"""

import os
import time
import subprocess
import shutil
import glob
import json
from PIL import Image
import numpy as np
from datetime import datetime
from skimage.metrics import structural_similarity as ssim

# 测试目录配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_DIR = os.path.join(BASE_DIR, "original")
PNGQUANT_DIR = os.path.join(BASE_DIR, "results_pngquant")
OXIPNG_DIR = os.path.join(BASE_DIR, "results_oxipng")
SQUOOSH_DIR = os.path.join(BASE_DIR, "results_squoosh")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# 确保目录存在
for dir_path in [TEMP_DIR, PNGQUANT_DIR, OXIPNG_DIR, SQUOOSH_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 压缩参数
PNGQUANT_QUALITY = 75  # 稍微降低质量以获得更好的压缩率
OXIPNG_LEVEL = 3
SQUOOSH_OPTION = "auto"  # 使用自动模式让squoosh决定最佳参数

# 结果记录
results = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "images": []
}

def convert_jpg_to_png(jpg_path, png_path):
    """将JPG转换为PNG (使用PIL库实现)"""
    try:
        img = Image.open(jpg_path)
        img.save(png_path, "PNG")
        return True
    except Exception as e:
        print(f"转换JPG到PNG失败: {e}")
        return False

def compress_with_pngquant(input_file, output_file, quality=PNGQUANT_QUALITY):
    """使用pngquant压缩PNG文件"""
    min_quality = max(1, int(quality * 0.8))
    max_quality = min(100, quality)
    quality_str = f"{min_quality}-{max_quality}"
    
    cmd = [
        "pngquant",
        "--quality", quality_str,
        "--force",
        "--skip-if-larger",
        "--strip",
        "--speed", "3",  # 速度3，平衡质量和速度
        "--output", output_file,
        input_file
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"pngquant压缩失败 ({stderr.strip()}): {input_file}")
        if os.path.exists(output_file):
            return True
        shutil.copy2(input_file, output_file)
        return False
    return True

def compress_with_oxipng(input_file, output_file, level=OXIPNG_LEVEL):
    """使用oxipng压缩PNG文件"""
    # 如果输入和输出相同，先复制文件
    if input_file != output_file:
        shutil.copy2(input_file, output_file)
    
    cmd = [
        "oxipng",
        "-o", str(level),
        "--strip", "safe",
        "--alpha",
        "-Z",  # 使用zopfli算法获得更好的压缩率
        output_file
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    return process.returncode == 0

def compress_with_squoosh(input_file, output_file, option=SQUOOSH_OPTION):
    """使用squoosh-cli压缩PNG文件"""
    temp_dir = os.path.dirname(output_file)
    
    if option == "auto":
        # 为PNG使用正确的squoosh参数
        cmd = [
            "squoosh-cli", 
            "--oxipng", 
            "{}",  # 使用默认oxipng参数
            "-d", temp_dir,
            input_file
        ]
    else:
        # 使用自定义参数
        cmd = [
            "squoosh-cli",
            "--oxipng",
            '{"level":3,"interlace":false}',  # 自定义oxipng参数
            "-d", temp_dir,
            input_file
        ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    # squoosh输出文件可能有不同扩展名，需要找到并重命名
    base_name = os.path.basename(input_file).split('.')[0]
    output_files = glob.glob(os.path.join(temp_dir, f"{base_name}.*"))
    
    if output_files:
        # 找到输出文件，重命名为目标文件
        shutil.move(output_files[0], output_file)
        return True
    else:
        # 未找到输出文件，复制原始文件
        print(f"Squoosh未生成输出文件: {stderr}")
        shutil.copy2(input_file, output_file)
        return False

def calculate_ssim(original_path, compressed_path):
    """计算两张图片的结构相似性 (SSIM)"""
    try:
        # 先确保两张图片都存在
        if not os.path.exists(original_path) or not os.path.exists(compressed_path):
            print(f"SSIM计算失败: 文件不存在")
            return -1
            
        img1 = np.array(Image.open(original_path).convert("RGB"))
        img2 = np.array(Image.open(compressed_path).convert("RGB"))
        
        # 确保两个图片尺寸相同
        if img1.shape != img2.shape:
            img2_pil = Image.open(compressed_path).convert("RGB")
            img2_pil = img2_pil.resize((img1.shape[1], img1.shape[0]), Image.LANCZOS)
            img2 = np.array(img2_pil)
        
        # 计算每个通道的SSIM，然后取平均值
        ssim_value = 0
        for channel in range(3):  # RGB三个通道
            ssim_channel = ssim(img1[:,:,channel], img2[:,:,channel], data_range=255)
            ssim_value += ssim_channel
            
        return ssim_value / 3  # 取平均
    except Exception as e:
        print(f"计算SSIM时出错: {e}")
        return -1

def process_images():
    """处理所有测试图片"""
    # 获取所有原始图片
    jpg_files = glob.glob(os.path.join(ORIGINAL_DIR, "*.jpg"))
    
    print(f"找到 {len(jpg_files)} 张JPG图片进行测试")
    
    # 处理每一张图片
    for idx, jpg_file in enumerate(jpg_files):
        filename = os.path.basename(jpg_file)
        print(f"\n处理图片 [{idx+1}/{len(jpg_files)}]: {filename}")
        
        # 先转换为PNG作为基准
        png_name = filename.replace(".jpg", ".png")
        reference_png = os.path.join(TEMP_DIR, png_name)
        convert_jpg_to_png(jpg_file, reference_png)
        
        # 准备各方法输出文件路径
        pngquant_output = os.path.join(PNGQUANT_DIR, png_name)
        oxipng_output = os.path.join(OXIPNG_DIR, png_name)
        squoosh_output = os.path.join(SQUOOSH_DIR, png_name)
        
        # 记录基准PNG大小
        reference_size = os.path.getsize(reference_png)
        
        # 1. pngquant压缩
        print(f"应用pngquant压缩 {filename}...")
        start_time = time.time()
        pngquant_success = compress_with_pngquant(reference_png, pngquant_output)
        pngquant_time = time.time() - start_time
        pngquant_size = os.path.getsize(pngquant_output) if os.path.exists(pngquant_output) else reference_size
        
        # 2. oxipng压缩
        print(f"应用oxipng压缩 {filename}...")
        start_time = time.time()
        oxipng_success = compress_with_oxipng(reference_png, oxipng_output)
        oxipng_time = time.time() - start_time
        oxipng_size = os.path.getsize(oxipng_output) if os.path.exists(oxipng_output) else reference_size
        
        # 3. squoosh压缩
        print(f"应用squoosh压缩 {filename}...")
        start_time = time.time()
        squoosh_success = compress_with_squoosh(reference_png, squoosh_output)
        squoosh_time = time.time() - start_time
        squoosh_size = os.path.getsize(squoosh_output) if os.path.exists(squoosh_output) else reference_size
        
        # 计算SSIM (结构相似度)
        pngquant_ssim = calculate_ssim(reference_png, pngquant_output)
        oxipng_ssim = calculate_ssim(reference_png, oxipng_output)
        squoosh_ssim = calculate_ssim(reference_png, squoosh_output)
        
        # 记录原始JPG大小供参考
        jpg_size = os.path.getsize(jpg_file)
        
        # 记录结果
        image_result = {
            "filename": filename,
            "jpg_size_kb": round(jpg_size / 1024, 2),
            "reference_png_size_kb": round(reference_size / 1024, 2),
            "pngquant": {
                "size_kb": round(pngquant_size / 1024, 2),
                "compression_ratio": round((reference_size - pngquant_size) / reference_size * 100, 2),
                "processing_time_s": round(pngquant_time, 2),
                "ssim": round(pngquant_ssim * 100, 2)  # 转为百分比
            },
            "oxipng": {
                "size_kb": round(oxipng_size / 1024, 2),
                "compression_ratio": round((reference_size - oxipng_size) / reference_size * 100, 2),
                "processing_time_s": round(oxipng_time, 2),
                "ssim": round(oxipng_ssim * 100, 2)  # 转为百分比
            },
            "squoosh": {
                "size_kb": round(squoosh_size / 1024, 2),
                "compression_ratio": round((reference_size - squoosh_size) / reference_size * 100, 2),
                "processing_time_s": round(squoosh_time, 2),
                "ssim": round(squoosh_ssim * 100, 2)  # 转为百分比
            }
        }
        
        results["images"].append(image_result)
        
        # 打印当前图片结果
        print(f"原始JPG大小: {image_result['jpg_size_kb']} KB")
        print(f"基准PNG大小: {image_result['reference_png_size_kb']} KB")
        print(f"pngquant: {image_result['pngquant']['size_kb']} KB " 
              f"(压缩率: {image_result['pngquant']['compression_ratio']}%, "
              f"SSIM: {image_result['pngquant']['ssim']}%, "
              f"耗时: {image_result['pngquant']['processing_time_s']}s)")
        print(f"oxipng: {image_result['oxipng']['size_kb']} KB " 
              f"(压缩率: {image_result['oxipng']['compression_ratio']}%, "
              f"SSIM: {image_result['oxipng']['ssim']}%, "
              f"耗时: {image_result['oxipng']['processing_time_s']}s)")
        print(f"squoosh: {image_result['squoosh']['size_kb']} KB " 
              f"(压缩率: {image_result['squoosh']['compression_ratio']}%, "
              f"SSIM: {image_result['squoosh']['ssim']}%, "
              f"耗时: {image_result['squoosh']['processing_time_s']}s)")

def summarize_results():
    """汇总并打印测试结果"""
    if not results["images"]:
        print("没有测试结果可以汇总")
        return
    
    # 计算平均值
    avg_jpg_size = sum(img["jpg_size_kb"] for img in results["images"]) / len(results["images"])
    avg_ref_size = sum(img["reference_png_size_kb"] for img in results["images"]) / len(results["images"])
    
    avg_pngquant_size = sum(img["pngquant"]["size_kb"] for img in results["images"]) / len(results["images"])
    avg_pngquant_ratio = sum(img["pngquant"]["compression_ratio"] for img in results["images"]) / len(results["images"])
    avg_pngquant_time = sum(img["pngquant"]["processing_time_s"] for img in results["images"]) / len(results["images"])
    avg_pngquant_ssim = sum(img["pngquant"]["ssim"] for img in results["images"]) / len(results["images"])
    
    avg_oxipng_size = sum(img["oxipng"]["size_kb"] for img in results["images"]) / len(results["images"])
    avg_oxipng_ratio = sum(img["oxipng"]["compression_ratio"] for img in results["images"]) / len(results["images"])
    avg_oxipng_time = sum(img["oxipng"]["processing_time_s"] for img in results["images"]) / len(results["images"])
    avg_oxipng_ssim = sum(img["oxipng"]["ssim"] for img in results["images"]) / len(results["images"])
    
    avg_squoosh_size = sum(img["squoosh"]["size_kb"] for img in results["images"]) / len(results["images"])
    avg_squoosh_ratio = sum(img["squoosh"]["compression_ratio"] for img in results["images"]) / len(results["images"])
    avg_squoosh_time = sum(img["squoosh"]["processing_time_s"] for img in results["images"]) / len(results["images"])
    avg_squoosh_ssim = sum(img["squoosh"]["ssim"] for img in results["images"]) / len(results["images"])
    
    # 添加汇总信息到结果
    results["summary"] = {
        "avg_jpg_size_kb": round(avg_jpg_size, 2),
        "avg_reference_png_size_kb": round(avg_ref_size, 2),
        "pngquant": {
            "avg_size_kb": round(avg_pngquant_size, 2),
            "avg_compression_ratio": round(avg_pngquant_ratio, 2),
            "avg_processing_time_s": round(avg_pngquant_time, 2),
            "avg_ssim": round(avg_pngquant_ssim, 2)
        },
        "oxipng": {
            "avg_size_kb": round(avg_oxipng_size, 2),
            "avg_compression_ratio": round(avg_oxipng_ratio, 2),
            "avg_processing_time_s": round(avg_oxipng_time, 2),
            "avg_ssim": round(avg_oxipng_ssim, 2)
        },
        "squoosh": {
            "avg_size_kb": round(avg_squoosh_size, 2),
            "avg_compression_ratio": round(avg_squoosh_ratio, 2),
            "avg_processing_time_s": round(avg_squoosh_time, 2),
            "avg_ssim": round(avg_squoosh_ssim, 2)
        },
        "comparisons": {
            "pngquant_vs_oxipng": {
                "size_diff_percent": round((avg_oxipng_size - avg_pngquant_size) / avg_oxipng_size * 100, 2),
                "ssim_diff": round(avg_pngquant_ssim - avg_oxipng_ssim, 2),
                "time_diff_percent": round((avg_pngquant_time - avg_oxipng_time) / avg_oxipng_time * 100, 2)
            },
            "pngquant_vs_squoosh": {
                "size_diff_percent": round((avg_squoosh_size - avg_pngquant_size) / avg_squoosh_size * 100, 2),
                "ssim_diff": round(avg_pngquant_ssim - avg_squoosh_ssim, 2),
                "time_diff_percent": round((avg_pngquant_time - avg_squoosh_time) / avg_squoosh_time * 100, 2)
            },
            "oxipng_vs_squoosh": {
                "size_diff_percent": round((avg_squoosh_size - avg_oxipng_size) / avg_squoosh_size * 100, 2),
                "ssim_diff": round(avg_oxipng_ssim - avg_squoosh_ssim, 2),
                "time_diff_percent": round((avg_oxipng_time - avg_squoosh_time) / avg_squoosh_time * 100, 2)
            }
        }
    }
    
    # 打印汇总结果
    print("\n" + "="*70)
    print("压缩方法比较测试结果汇总")
    print("="*70)
    print(f"测试图片数量: {len(results['images'])}")
    print(f"原始JPG平均大小: {results['summary']['avg_jpg_size_kb']} KB")
    print(f"基准PNG平均大小: {results['summary']['avg_reference_png_size_kb']} KB")
    
    print("\npngquant压缩结果:")
    print(f"- 平均大小: {results['summary']['pngquant']['avg_size_kb']} KB")
    print(f"- 平均压缩率: {results['summary']['pngquant']['avg_compression_ratio']}%")
    print(f"- 平均处理时间: {results['summary']['pngquant']['avg_processing_time_s']} 秒")
    print(f"- 平均SSIM质量: {results['summary']['pngquant']['avg_ssim']}%")
    
    print("\noxipng压缩结果:")
    print(f"- 平均大小: {results['summary']['oxipng']['avg_size_kb']} KB")
    print(f"- 平均压缩率: {results['summary']['oxipng']['avg_compression_ratio']}%")
    print(f"- 平均处理时间: {results['summary']['oxipng']['avg_processing_time_s']} 秒")
    print(f"- 平均SSIM质量: {results['summary']['oxipng']['avg_ssim']}%")
    
    print("\nsquoosh压缩结果:")
    print(f"- 平均大小: {results['summary']['squoosh']['avg_size_kb']} KB")
    print(f"- 平均压缩率: {results['summary']['squoosh']['avg_compression_ratio']}%")
    print(f"- 平均处理时间: {results['summary']['squoosh']['avg_processing_time_s']} 秒")
    print(f"- 平均SSIM质量: {results['summary']['squoosh']['avg_ssim']}%")
    
    print("\n方法对比:")
    # pngquant vs oxipng
    pq_ox_size = results['summary']['comparisons']['pngquant_vs_oxipng']['size_diff_percent']
    pq_ox_ssim = results['summary']['comparisons']['pngquant_vs_oxipng']['ssim_diff']
    pq_ox_time = results['summary']['comparisons']['pngquant_vs_oxipng']['time_diff_percent']
    
    print(f"pngquant与oxipng比较:")
    print(f"- 文件大小差异: {abs(pq_ox_size)}% ({'pngquant更小' if pq_ox_size > 0 else 'oxipng更小'})")
    print(f"- 画质差异: {abs(pq_ox_ssim)} ({'pngquant更好' if pq_ox_ssim > 0 else 'oxipng更好'})")
    print(f"- 处理时间差异: {abs(pq_ox_time)}% ({'pngquant更慢' if pq_ox_time > 0 else 'oxipng更慢'})")
    
    # pngquant vs squoosh
    pq_sq_size = results['summary']['comparisons']['pngquant_vs_squoosh']['size_diff_percent']
    pq_sq_ssim = results['summary']['comparisons']['pngquant_vs_squoosh']['ssim_diff']
    pq_sq_time = results['summary']['comparisons']['pngquant_vs_squoosh']['time_diff_percent']
    
    print(f"\npngquant与squoosh比较:")
    print(f"- 文件大小差异: {abs(pq_sq_size)}% ({'pngquant更小' if pq_sq_size > 0 else 'squoosh更小'})")
    print(f"- 画质差异: {abs(pq_sq_ssim)} ({'pngquant更好' if pq_sq_ssim > 0 else 'squoosh更好'})")
    print(f"- 处理时间差异: {abs(pq_sq_time)}% ({'pngquant更慢' if pq_sq_time > 0 else 'squoosh更慢'})")
    
    # oxipng vs squoosh
    ox_sq_size = results['summary']['comparisons']['oxipng_vs_squoosh']['size_diff_percent']
    ox_sq_ssim = results['summary']['comparisons']['oxipng_vs_squoosh']['ssim_diff']
    ox_sq_time = results['summary']['comparisons']['oxipng_vs_squoosh']['time_diff_percent']
    
    print(f"\noxipng与squoosh比较:")
    print(f"- 文件大小差异: {abs(ox_sq_size)}% ({'oxipng更小' if ox_sq_size > 0 else 'squoosh更小'})")
    print(f"- 画质差异: {abs(ox_sq_ssim)} ({'oxipng更好' if ox_sq_ssim > 0 else 'squoosh更好'})")
    print(f"- 处理时间差异: {abs(ox_sq_time)}% ({'oxipng更慢' if ox_sq_time > 0 else 'squoosh更慢'})")
    
    # 识别最佳方法
    best_method = None
    best_reason = None
    
    # 根据压缩率和质量的平衡确定最佳方法
    if avg_pngquant_ratio >= avg_oxipng_ratio and avg_pngquant_ratio >= avg_squoosh_ratio:
        if avg_pngquant_ssim >= 90:  # 质量足够好
            best_method = "pngquant"
            best_reason = "提供最佳压缩率且保持良好画质"
        else:
            # 如果pngquant质量不够好，比较其他两种
            if avg_oxipng_ratio >= avg_squoosh_ratio:
                best_method = "oxipng"
                best_reason = "在保持无损质量的同时提供良好压缩率"
            else:
                best_method = "squoosh"
                best_reason = "提供比oxipng更好的压缩率且保持高质量"
    elif avg_oxipng_ratio >= avg_squoosh_ratio:
        best_method = "oxipng"
        best_reason = "在保持无损质量的同时提供良好压缩率"
    else:
        best_method = "squoosh"
        best_reason = "提供最佳的压缩率与质量平衡"
    
    # 综合最佳组合
    print("\n结论:")
    print(f"单一工具中，{best_method}是最佳选择，{best_reason}")
    
    # 分析组合方案
    if avg_pngquant_ratio > avg_oxipng_ratio and avg_oxipng_ssim > avg_pngquant_ssim:
        print("oxipng + pngquant的组合可能是最佳方案：先用oxipng减小体积，再用pngquant进一步压缩")
    
    if avg_squoosh_ratio > 0 and avg_squoosh_ratio > avg_oxipng_ratio:
        print("对于需要极致压缩的场景，squoosh是不错的选择")
        
    if avg_oxipng_ssim > avg_pngquant_ssim and avg_oxipng_ssim > avg_squoosh_ssim:
        print("对于需要完全无损处理的场景，oxipng是最佳选择")
    
    # 保存详细结果到JSON文件
    results_file = os.path.join(BASE_DIR, "compression_methods_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n详细结果已保存到: {results_file}")

def main():
    """主函数"""
    print("开始压缩方法比较测试...")
    
    # 清理之前的结果
    for dir_path in [PNGQUANT_DIR, OXIPNG_DIR, SQUOOSH_DIR, TEMP_DIR]:
        for file in glob.glob(os.path.join(dir_path, "*.png")):
            os.remove(file)
    
    # 处理所有图片
    process_images()
    
    # 汇总结果
    summarize_results()

if __name__ == "__main__":
    main() 