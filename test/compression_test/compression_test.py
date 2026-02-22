#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PNG压缩测试脚本
比较两种压缩方法:
1. pngquant + oxipng (原项目方法)
2. pngquant + oxipng + squoosh (改进方法)

对比:
- 压缩前后大小
- 处理耗时
- 画质评估 (使用SSIM)
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
METHOD1_DIR = os.path.join(BASE_DIR, "results_method1")  # pngquant + oxipng
METHOD2_DIR = os.path.join(BASE_DIR, "results_method2")  # pngquant + oxipng + squoosh
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# 确保目录存在
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(METHOD1_DIR, exist_ok=True)
os.makedirs(METHOD2_DIR, exist_ok=True)

# 压缩参数
PNGQUANT_QUALITY = 80
OXIPNG_LEVEL = 3
SQUOOSH_QUALITY = 75  # 可以调整以获得更好的平衡

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
    return process.returncode == 0

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

def compress_with_squoosh(input_file, output_file, quality=SQUOOSH_QUALITY):
    """使用squoosh压缩PNG文件"""
    cmd = [
        "squoosh-cli",
        "--oxipng", json.dumps({"level": 3}),
        "-d", os.path.dirname(output_file),
        input_file
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    # squoosh输出文件使用原始文件名，如果输出路径不同，需要重命名
    output_basename = os.path.basename(input_file)
    squoosh_output = os.path.join(os.path.dirname(output_file), output_basename)
    
    if squoosh_output != output_file and os.path.exists(squoosh_output):
        os.rename(squoosh_output, output_file)
        
    return process.returncode == 0 and os.path.exists(output_file)

def calculate_ssim(original_path, compressed_path):
    """计算两张图片的结构相似性 (SSIM)"""
    try:
        img1 = np.array(Image.open(original_path).convert("RGB"))
        img2 = np.array(Image.open(compressed_path).convert("RGB"))
        
        # 确保两个图片尺寸相同
        if img1.shape != img2.shape:
            # 调整第二个图片尺寸以匹配第一个
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

def method1_compression(input_jpg, output_png):
    """方法1: pngquant + oxipng"""
    # 步骤1: JPG转PNG
    temp_png = os.path.join(TEMP_DIR, os.path.basename(input_jpg).replace(".jpg", ".png"))
    convert_jpg_to_png(input_jpg, temp_png)
    
    # 步骤2: pngquant压缩
    temp_pngquant = os.path.join(TEMP_DIR, os.path.basename(temp_png).replace(".png", "_pngquant.png"))
    if not compress_with_pngquant(temp_png, temp_pngquant):
        print(f"pngquant压缩失败: {input_jpg}")
        shutil.copy2(temp_png, temp_pngquant)  # 失败则使用原始PNG
    
    # 步骤3: oxipng进一步压缩
    compress_with_oxipng(temp_pngquant, output_png)
    
    # 清理临时文件
    os.remove(temp_png)
    os.remove(temp_pngquant)

def method2_compression(input_jpg, output_png):
    """方法2: pngquant + oxipng + squoosh"""
    # 步骤1-3: 与方法1相同
    method1_output = os.path.join(TEMP_DIR, os.path.basename(input_jpg).replace(".jpg", "_method1.png"))
    method1_compression(input_jpg, method1_output)
    
    # 步骤4: 使用squoosh进一步压缩
    compress_with_squoosh(method1_output, output_png)
    
    # 如果squoosh失败，使用方法1的结果
    if not os.path.exists(output_png):
        shutil.copy2(method1_output, output_png)
    
    # 清理临时文件
    os.remove(method1_output)

def process_images():
    """处理所有测试图片"""
    # 获取所有原始图片
    jpg_files = glob.glob(os.path.join(ORIGINAL_DIR, "*.jpg"))
    
    print(f"找到 {len(jpg_files)} 张图片进行测试")
    
    # 处理每一张图片
    for idx, jpg_file in enumerate(jpg_files):
        filename = os.path.basename(jpg_file)
        print(f"\n处理图片 [{idx+1}/{len(jpg_files)}]: {filename}")
        
        # 准备输出文件路径
        png_name = filename.replace(".jpg", ".png")
        method1_output = os.path.join(METHOD1_DIR, png_name)
        method2_output = os.path.join(METHOD2_DIR, png_name)
        
        # 记录原始文件大小
        original_size = os.path.getsize(jpg_file)
        
        # 方法1: pngquant + oxipng
        print(f"应用方法1 (pngquant + oxipng) 到 {filename}...")
        start_time = time.time()
        method1_compression(jpg_file, method1_output)
        method1_time = time.time() - start_time
        method1_size = os.path.getsize(method1_output)
        
        # 方法2: pngquant + oxipng + squoosh
        print(f"应用方法2 (pngquant + oxipng + squoosh) 到 {filename}...")
        start_time = time.time()
        method2_compression(jpg_file, method2_output)
        method2_time = time.time() - start_time
        method2_size = os.path.getsize(method2_output)
        
        # 转换参考PNG用于SSIM比较
        reference_png = os.path.join(TEMP_DIR, png_name)
        convert_jpg_to_png(jpg_file, reference_png)
        
        # 计算SSIM (结构相似度)
        method1_ssim = calculate_ssim(reference_png, method1_output)
        method2_ssim = calculate_ssim(reference_png, method2_output)
        
        # 清理临时文件
        os.remove(reference_png)
        
        # 记录结果
        image_result = {
            "filename": filename,
            "original_size_kb": round(original_size / 1024, 2),
            "method1": {
                "size_kb": round(method1_size / 1024, 2),
                "compression_ratio": round((original_size - method1_size) / original_size * 100, 2),
                "processing_time_s": round(method1_time, 2),
                "ssim": round(method1_ssim * 100, 2)  # 转为百分比
            },
            "method2": {
                "size_kb": round(method2_size / 1024, 2),
                "compression_ratio": round((original_size - method2_size) / original_size * 100, 2),
                "processing_time_s": round(method2_time, 2),
                "ssim": round(method2_ssim * 100, 2)  # 转为百分比
            }
        }
        
        results["images"].append(image_result)
        
        # 打印当前图片结果
        print(f"原始大小: {image_result['original_size_kb']} KB")
        print(f"方法1: {image_result['method1']['size_kb']} KB " 
              f"(压缩率: {image_result['method1']['compression_ratio']}%, "
              f"SSIM: {image_result['method1']['ssim']}%, "
              f"耗时: {image_result['method1']['processing_time_s']}s)")
        print(f"方法2: {image_result['method2']['size_kb']} KB " 
              f"(压缩率: {image_result['method2']['compression_ratio']}%, "
              f"SSIM: {image_result['method2']['ssim']}%, "
              f"耗时: {image_result['method2']['processing_time_s']}s)")

def summarize_results():
    """汇总并打印测试结果"""
    if not results["images"]:
        print("没有测试结果可以汇总")
        return
    
    # 计算平均值
    avg_original_size = sum(img["original_size_kb"] for img in results["images"]) / len(results["images"])
    
    avg_method1_size = sum(img["method1"]["size_kb"] for img in results["images"]) / len(results["images"])
    avg_method1_ratio = sum(img["method1"]["compression_ratio"] for img in results["images"]) / len(results["images"])
    avg_method1_time = sum(img["method1"]["processing_time_s"] for img in results["images"]) / len(results["images"])
    avg_method1_ssim = sum(img["method1"]["ssim"] for img in results["images"]) / len(results["images"])
    
    avg_method2_size = sum(img["method2"]["size_kb"] for img in results["images"]) / len(results["images"])
    avg_method2_ratio = sum(img["method2"]["compression_ratio"] for img in results["images"]) / len(results["images"])
    avg_method2_time = sum(img["method2"]["processing_time_s"] for img in results["images"]) / len(results["images"])
    avg_method2_ssim = sum(img["method2"]["ssim"] for img in results["images"]) / len(results["images"])
    
    # 添加汇总信息到结果
    results["summary"] = {
        "avg_original_size_kb": round(avg_original_size, 2),
        "method1": {
            "avg_size_kb": round(avg_method1_size, 2),
            "avg_compression_ratio": round(avg_method1_ratio, 2),
            "avg_processing_time_s": round(avg_method1_time, 2),
            "avg_ssim": round(avg_method1_ssim, 2)
        },
        "method2": {
            "avg_size_kb": round(avg_method2_size, 2),
            "avg_compression_ratio": round(avg_method2_ratio, 2),
            "avg_processing_time_s": round(avg_method2_time, 2),
            "avg_ssim": round(avg_method2_ssim, 2)
        },
        "improvement": {
            "size_reduction_percent": round((avg_method1_size - avg_method2_size) / avg_method1_size * 100, 2),
            "ssim_diff": round(avg_method2_ssim - avg_method1_ssim, 2),
            "time_increase_percent": round((avg_method2_time - avg_method1_time) / avg_method1_time * 100, 2)
        }
    }
    
    # 打印汇总结果
    print("\n" + "="*60)
    print("压缩测试结果汇总")
    print("="*60)
    print(f"测试图片数量: {len(results['images'])}")
    print(f"原始平均大小: {results['summary']['avg_original_size_kb']} KB")
    print("\n方法1 (pngquant + oxipng):")
    print(f"- 平均大小: {results['summary']['method1']['avg_size_kb']} KB")
    print(f"- 平均压缩率: {results['summary']['method1']['avg_compression_ratio']}%")
    print(f"- 平均处理时间: {results['summary']['method1']['avg_processing_time_s']} 秒")
    print(f"- 平均SSIM质量: {results['summary']['method1']['avg_ssim']}%")
    
    print("\n方法2 (pngquant + oxipng + squoosh):")
    print(f"- 平均大小: {results['summary']['method2']['avg_size_kb']} KB")
    print(f"- 平均压缩率: {results['summary']['method2']['avg_compression_ratio']}%")
    print(f"- 平均处理时间: {results['summary']['method2']['avg_processing_time_s']} 秒")
    print(f"- 平均SSIM质量: {results['summary']['method2']['avg_ssim']}%")
    
    print("\n方法2相对于方法1的改进:")
    size_imp = results['summary']['improvement']['size_reduction_percent']
    ssim_imp = results['summary']['improvement']['ssim_diff']
    time_imp = results['summary']['improvement']['time_increase_percent']
    
    print(f"- 文件大小减少: {size_imp}%")
    print(f"- SSIM质量变化: {ssim_imp}% ({'提高' if ssim_imp >= 0 else '降低'})")
    print(f"- 处理时间增加: {time_imp}%")
    
    # 结论
    print("\n结论:")
    if size_imp > 2 and ssim_imp > -2:
        print("方法2 (添加squoosh) 在文件大小上有明显改进，且画质损失可接受")
        if time_imp > 50:
            print("但处理时间显著增加，可能需要权衡效率和压缩率")
    elif size_imp > 0 and ssim_imp >= 0:
        print("方法2 (添加squoosh) 提供了更好的压缩率和相同或更好的画质")
    elif size_imp <= 0:
        print("方法2 (添加squoosh) 没有提供更好的压缩率，不建议使用")
    else:
        print("需要根据具体需求在压缩率、画质和处理时间之间进行权衡")
    
    # 保存详细结果到JSON文件
    results_file = os.path.join(BASE_DIR, "compression_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n详细结果已保存到: {results_file}")

def main():
    """主函数"""
    print("开始PNG压缩测试...")
    
    # 清理之前的结果
    for file in glob.glob(os.path.join(METHOD1_DIR, "*.png")):
        os.remove(file)
    for file in glob.glob(os.path.join(METHOD2_DIR, "*.png")):
        os.remove(file)
    for file in glob.glob(os.path.join(TEMP_DIR, "*.png")):
        os.remove(file)
    
    # 处理所有图片
    process_images()
    
    # 汇总结果
    summarize_results()

if __name__ == "__main__":
    main() 