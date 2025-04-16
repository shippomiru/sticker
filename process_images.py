#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片处理脚本 - 改进版
用于将JPG图片转换为透明背景PNG图片，并添加白色描边

使用方法:
    python3 process_images.py [输入目录] [输出目录] [--review]
    
    输入目录默认为 unsplash-images 下的当日批次目录
    输出目录默认为 processed-images 下的当日批次目录
    
    批次处理:
    python3 process_images.py --batch YYYYMMDD
    
    验收管理:
    python3 process_images.py --merge [源目录] [目标目录]
    默认将处理后的图片合并到 project/public/images
"""

import os
import glob
import numpy as np
import shutil
import argparse
import json
from PIL import Image
from rembg import remove
import sys
import time
from datetime import datetime

# 导入现有的描边生成函数
sys.path.append(os.path.abspath('api/processors'))
from test_smooth_no_gap_outline import create_smooth_no_gap_outline

# 定义常量
UNSPLASH_IMAGES_DIR = "unsplash-images"
PROCESSED_IMAGES_DIR = "processed-images"  # 替代 results-photos-cropped
TEMP_RESULTS_DIR = "temp-results"
PROJECT_IMAGES_DIR = "project/public/images"
METADATA_DIR = "metadata"
PROCESSED_RECORD_FILE = os.path.join(METADATA_DIR, "processed_images.json")

def ensure_dir_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"已创建目录: {directory}")

def get_current_date():
    """获取当前日期字符串 (YYYYMMDD)"""
    return datetime.now().strftime('%Y%m%d')

def load_processed_records():
    """加载已处理图片记录"""
    ensure_dir_exists(METADATA_DIR)
    if os.path.exists(PROCESSED_RECORD_FILE):
        with open(PROCESSED_RECORD_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"警告: 处理记录文件格式错误，将创建新记录")
                return {"processed_images": {}}
    return {"processed_images": {}}

def save_processed_records(records):
    """保存已处理图片记录"""
    with open(PROCESSED_RECORD_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def remove_background(input_path, output_path):
    """使用rembg移除图片背景，将结果保存为透明PNG"""
    try:
        # 读取输入图片
        print(f"正在处理图片: {input_path}")
        input_img = Image.open(input_path)
        
        # 移除背景
        print("正在移除背景...")
        output_img = remove(input_img)
        
        # 保存为透明PNG
        output_img.save(output_path)
        print(f"透明图片已保存: {output_path}")
        return True
    except Exception as e:
        print(f"处理图片失败 {input_path}: {e}")
        return False

def crop_to_center_main_subject(input_path, output_path, target_ratio=0.5, safety_padding=0.15):
    """
    裁剪图片使主体位于中心，并且占据图片面积的约50%
    添加安全边距确保不会裁剪到主体
    
    参数:
    - input_path: 输入的透明PNG图片路径
    - output_path: 裁剪后的输出图片路径
    - target_ratio: 目标主体在图片中的面积比例，默认0.5 (50%)
    - safety_padding: 安全边距比例，默认0.15 (15%)
    """
    try:
        print(f"正在裁剪图片: {input_path}")
        
        # 读取透明PNG图片
        img = Image.open(input_path)
        
        # 确保图片是RGBA模式
        if img.mode != 'RGBA':
            print(f"图片不是透明PNG，跳过裁剪")
            img.save(output_path)
            return False
        
        # 转换为numpy数组处理
        img_array = np.array(img)
        
        # 获取alpha通道
        alpha_channel = img_array[:, :, 3]
        
        # 找到所有非透明像素(alpha > 0)
        non_transparent_mask = alpha_channel > 0
        
        # 如果没有非透明像素，保存原图并返回
        if not np.any(non_transparent_mask):
            print(f"图片中没有可见内容，跳过裁剪")
            img.save(output_path)
            return False
        
        # 找到非透明区域的边界框
        rows = np.any(non_transparent_mask, axis=1)
        cols = np.any(non_transparent_mask, axis=0)
        
        # 获取非零行列的索引
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        # 计算主体区域的中心点
        center_y = (y_min + y_max) // 2
        center_x = (x_min + x_max) // 2
        
        # 计算主体的宽度和高度
        subject_width = x_max - x_min + 1
        subject_height = y_max - y_min + 1
        
        # 增加安全边距，确保不会裁剪到主体
        # 用于计算的主体尺寸增加safety_padding比例
        padded_width = subject_width * (1 + safety_padding)
        padded_height = subject_height * (1 + safety_padding)
        
        # 计算主体的面积（使用带安全边距的尺寸）
        padded_subject_area = padded_width * padded_height
        
        # 计算需要的总面积(使主体占比为target_ratio)
        required_area = padded_subject_area / target_ratio
        
        # 计算新的边长(输出是正方形)
        # 取宽高中的较大者作为基准
        max_side = max(padded_width, padded_height)
        
        # 计算需要的边长，使主体占据图片的target_ratio
        side_length = int(max_side / np.sqrt(target_ratio))
        
        # 确保边长是偶数
        side_length = side_length + (side_length % 2)
        
        # 计算裁剪区域，以主体中心为中心
        left = max(0, center_x - side_length // 2)
        upper = max(0, center_y - side_length // 2)
        right = min(img.width, left + side_length)
        lower = min(img.height, upper + side_length)
        
        # 当裁剪框超出图像边界时的智能调整
        # 如果右边界超出图像尺寸，向左移动裁剪框
        if right > img.width:
            shift = right - img.width
            right = img.width
            left = max(0, left - shift)
        
        # 如果下边界超出图像尺寸，向上移动裁剪框
        if lower > img.height:
            shift = lower - img.height
            lower = img.height
            upper = max(0, upper - shift)
        
        # 确保裁剪区域足够大，如果由于图像尺寸限制导致裁剪区域变小，
        # 则需要适当调整，使主体仍然位于中心
        if right - left < side_length and left > 0:
            # 如果左边有空间，向左扩展
            left = max(0, left - (side_length - (right - left)))
        if lower - upper < side_length and upper > 0:
            # 如果上边有空间，向上扩展
            upper = max(0, upper - (side_length - (lower - upper)))
        
        # 再次检查裁剪区域是否包含了整个主体（包括安全边距）
        # 如果主体边界被裁剪，则调整裁剪框
        if left > x_min or right < x_max or upper > y_min or lower < y_max:
            # 确保裁剪框至少包含主体
            left = min(left, x_min)
            upper = min(upper, y_min)
            right = max(right, x_max)
            lower = max(lower, y_max)
            
            # 调整宽高以保持正方形
            width = right - left
            height = lower - upper
            
            if width > height:
                # 高度不足，需要增加
                diff = width - height
                upper = max(0, upper - diff // 2)
                lower = min(img.height, lower + diff // 2)
                
                # 如果仍然无法保持正方形（因为边界问题），调整宽度
                if lower - upper < width:
                    diff = width - (lower - upper)
                    if left >= diff // 2:
                        left -= diff // 2
                        right -= diff // 2
                    else:
                        right -= diff
            elif height > width:
                # 宽度不足，需要增加
                diff = height - width
                left = max(0, left - diff // 2)
                right = min(img.width, right + diff // 2)
                
                # 如果仍然无法保持正方形（因为边界问题），调整高度
                if right - left < height:
                    diff = height - (right - left)
                    if upper >= diff // 2:
                        upper -= diff // 2
                        lower -= diff // 2
                    else:
                        lower -= diff
        
        # 裁剪图片
        cropped_img = img.crop((left, upper, right, lower))
        
        # 保存裁剪后的图片
        cropped_img.save(output_path)
        print(f"裁剪后的图片已保存: {output_path}")
        return True
    except Exception as e:
        print(f"裁剪图片失败 {input_path}: {e}")
        return False

def process_image(jpg_file, output_dir, temp_dir, outline_size=40, edge_buffer=3, target_ratio=0.5, safety_padding=0.15):
    """处理单个JPG图片：抠图 -> 裁剪 -> 加白边"""
    try:
        # 确保临时目录和输出目录存在
        ensure_dir_exists(temp_dir)
        ensure_dir_exists(output_dir)
        
        # 获取文件名（不含扩展名）
        basename = os.path.basename(jpg_file).replace(".jpg", "")
        
        # 定义临时文件和输出文件路径
        transparent_png = os.path.join(temp_dir, f"{basename}_transparent.png")
        cropped_png = os.path.join(temp_dir, f"{basename}_cropped_temp.png")
        # 最终输出文件 - 透明背景版和带白边版
        cropped_final_png = os.path.join(output_dir, f"{basename}_cropped.png")
        outlined_png = os.path.join(output_dir, f"{basename}_outlined_cropped.png")
        
        print(f"\n开始处理: {basename}")
        
        # 步骤1: 移除背景，生成透明PNG
        if not os.path.exists(transparent_png):
            print("正在执行步骤1: 移除背景")
            success = remove_background(jpg_file, transparent_png)
            if not success:
                print(f"移除背景失败，跳过后续处理: {basename}")
                return False
        else:
            print(f"透明PNG已存在: {transparent_png}")
        
        # 步骤2: 裁剪图片使主体居中
        if not os.path.exists(cropped_png):
            print("正在执行步骤2: 裁剪居中")
            success = crop_to_center_main_subject(
                transparent_png, 
                cropped_png, 
                target_ratio=target_ratio, 
                safety_padding=safety_padding
            )
            if not success:
                print(f"裁剪失败，使用原始透明PNG继续处理: {basename}")
                cropped_png = transparent_png
        else:
            print(f"裁剪后的PNG已存在: {cropped_png}")
        
        # 步骤3: 保存透明版本到输出目录
        if not os.path.exists(cropped_final_png):
            print("正在执行步骤3: 保存透明版本")
            shutil.copy2(cropped_png, cropped_final_png)
            print(f"透明版本已保存: {cropped_final_png}")
        else:
            print(f"透明版本已存在: {cropped_final_png}")
        
        # 步骤4: 添加白色描边
        if not os.path.exists(outlined_png):
            print("正在执行步骤4: 添加白色描边")
            create_smooth_no_gap_outline(
                cropped_png, 
                outlined_png,
                outline_size=outline_size,
                edge_buffer=edge_buffer
            )
            print(f"描边版本已保存: {outlined_png}")
        else:
            print(f"描边版本已存在: {outlined_png}")
        
        # 更新已处理图片记录
        records = load_processed_records()
        records["processed_images"][basename] = {
            "processed_at": datetime.now().isoformat(),
            "original_file": jpg_file,
            "transparent_png": cropped_final_png,
            "outlined_png": outlined_png
        }
        save_processed_records(records)
        
        print(f"图片处理完成: {basename}")
        print(f"- 透明版本: {cropped_final_png}")
        print(f"- 带白边版本: {outlined_png}")
        return True
    except Exception as e:
        print(f"处理图片过程中发生错误 {jpg_file}: {e}")
        return False

def process_images(input_dir, output_dir, temp_dir, outline_size=40, edge_buffer=3, target_ratio=0.5, safety_padding=0.15, only_new=True):
    """处理指定目录下的所有JPG图片"""
    # 确保输出目录和临时目录存在
    ensure_dir_exists(output_dir)
    ensure_dir_exists(temp_dir)
    
    # 获取所有JPG文件
    jpg_files = glob.glob(os.path.join(input_dir, "*.jpg"))
    
    if only_new:
        # 加载已处理的图片记录
        records = load_processed_records()
        processed_images = records["processed_images"]
        
        # 过滤出未处理的图片
        unprocessed_jpg_files = []
        for jpg_file in jpg_files:
            basename = os.path.basename(jpg_file).replace(".jpg", "")
            if basename not in processed_images:
                unprocessed_jpg_files.append(jpg_file)
        
        print(f"找到 {len(jpg_files)} 个JPG文件，其中 {len(unprocessed_jpg_files)} 个未处理")
        
        if not unprocessed_jpg_files:
            print("没有新图片需要处理")
            return 0
        
        # 处理每个未处理的文件
        success_count = 0
        for jpg_file in unprocessed_jpg_files:
            if process_image(
                jpg_file, 
                output_dir, 
                temp_dir, 
                outline_size=outline_size, 
                edge_buffer=edge_buffer,
                target_ratio=target_ratio,
                safety_padding=safety_padding
            ):
                success_count += 1
        
        print(f"\n所有图片处理完成! 成功处理 {success_count}/{len(unprocessed_jpg_files)} 张新图片")
    else:
        # 处理所有图片，不管是否处理过
        print(f"找到 {len(jpg_files)} 个JPG文件")
        
        # 处理每个文件
        success_count = 0
        for jpg_file in jpg_files:
            if process_image(
                jpg_file, 
                output_dir, 
                temp_dir, 
                outline_size=outline_size, 
                edge_buffer=edge_buffer,
                target_ratio=target_ratio,
                safety_padding=safety_padding
            ):
                success_count += 1
        
        print(f"\n所有图片处理完成! 成功处理 {success_count}/{len(jpg_files)} 张图片")
    
    print(f"请查看 {output_dir} 目录下的最终结果")
    return success_count

def merge_images(source_dir, target_dir):
    """将源目录中的图片合并到目标目录"""
    if not os.path.exists(source_dir):
        print(f"源目录不存在: {source_dir}")
        return 0
    
    if not os.path.exists(target_dir):
        ensure_dir_exists(target_dir)
    
    merged_count = 0
    for filename in os.listdir(source_dir):
        if filename.endswith('.png'):
            src_path = os.path.join(source_dir, filename)
            dst_path = os.path.join(target_dir, filename)
            
            # 如果目标文件已存在，默认跳过
            if os.path.exists(dst_path):
                print(f"跳过已存在文件: {filename}")
                continue
            
            # 复制文件
            shutil.copy2(src_path, dst_path)
            merged_count += 1
            print(f"合并文件: {filename}")
    
    print(f"\n合并完成! 共合并 {merged_count} 个文件到 {target_dir}")
    return merged_count

def process_batch(batch_date=None, only_new=True):
    """处理指定批次的图片"""
    # 如果未指定批次日期，使用当前日期
    if batch_date is None:
        batch_date = get_current_date()
    
    # 构建批次相关目录
    batch_input_dir = os.path.join(UNSPLASH_IMAGES_DIR, batch_date)
    batch_output_dir = os.path.join(PROCESSED_IMAGES_DIR, batch_date)
    batch_temp_dir = os.path.join(TEMP_RESULTS_DIR, batch_date)
    
    # 检查批次输入目录是否存在
    if not os.path.exists(batch_input_dir):
        print(f"批次输入目录不存在: {batch_input_dir}")
        print(f"请先创建批次: python3 batch_manager.py create --date {batch_date}")
        return 0
    
    # 处理该批次的图片
    print(f"\n===== 处理批次 {batch_date} =====")
    print(f"输入目录: {batch_input_dir}")
    print(f"输出目录: {batch_output_dir}")
    print(f"临时目录: {batch_temp_dir}")
    
    # 执行图片处理
    processed_count = process_images(
        batch_input_dir,
        batch_output_dir,
        batch_temp_dir,
        outline_size=40,
        edge_buffer=3,
        target_ratio=0.5,
        safety_padding=0.15,
        only_new=only_new
    )
    
    # 提供后续步骤提示
    if processed_count > 0:
        print(f"\n批次 {batch_date} 处理完成! 成功处理 {processed_count} 张图片")
        print(f"验收提示:")
        print(f"1. 请在 {batch_output_dir} 目录查看新处理的图片")
        print(f"2. 验收通过后，可以将图片合并到前端展示目录:")
        print(f"   python3 process_images.py --merge --merge-from {batch_output_dir} --merge-to {PROJECT_IMAGES_DIR}")
    
    return processed_count

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='图片处理工具 - 将JPG转换为透明背景PNG')
    parser.add_argument('input_dir', nargs='?', default=None, help=f'输入JPG图片目录 (默认: {UNSPLASH_IMAGES_DIR}/当前日期)')
    parser.add_argument('output_dir', nargs='?', default=None, help=f'输出PNG图片目录 (默认: {PROCESSED_IMAGES_DIR}/当前日期)')
    parser.add_argument('--batch', help='处理指定批次的图片 (YYYYMMDD格式)')
    parser.add_argument('--all', action='store_true', help='处理所有图片，包括已处理过的')
    parser.add_argument('--merge', action='store_true', help='合并验收目录的图片到最终目录')
    parser.add_argument('--merge-from', help='合并源目录 (与--merge一起使用)')
    parser.add_argument('--merge-to', help='合并目标目录 (与--merge一起使用)')
    parser.add_argument('--temp-dir', default=None, help=f'临时文件目录 (默认: {TEMP_RESULTS_DIR}/当前日期)')
    
    args = parser.parse_args()
    
    # 获取当前日期
    current_date = get_current_date()
    
    # 如果是合并模式，执行合并操作
    if args.merge:
        source_dir = args.merge_from if args.merge_from else args.input_dir
        target_dir = args.merge_to if args.merge_to else PROJECT_IMAGES_DIR
        
        if not source_dir:
            print("错误: 合并模式需要指定源目录")
            return
        
        merge_images(source_dir, target_dir)
        return
    
    # 如果指定了批次，则处理该批次
    if args.batch:
        process_batch(args.batch, not args.all)
        return
    
    # 如果指定了输入和输出目录，使用指定的目录
    # 否则，使用当前日期的批次目录
    input_dir = args.input_dir if args.input_dir else os.path.join(UNSPLASH_IMAGES_DIR, current_date)
    output_dir = args.output_dir if args.output_dir else os.path.join(PROCESSED_IMAGES_DIR, current_date)
    temp_dir = args.temp_dir if args.temp_dir else os.path.join(TEMP_RESULTS_DIR, current_date)
    
    print(f"图片处理开始")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"临时目录: {temp_dir}")
    
    # 处理所有图片
    # 步骤顺序: 抠图 -> 裁剪 -> 加白边
    processed_count = process_images(
        input_dir, 
        output_dir, 
        temp_dir,
        outline_size=40,           # 白边大小
        edge_buffer=3,             # 边缘缓冲区大小
        target_ratio=0.5,          # 主体占图片的面积比例
        safety_padding=0.15,       # 主体周围的安全边距
        only_new=not args.all      # 是否只处理新图片
    )
    
    if processed_count > 0:
        print(f"\n验收提示:")
        print(f"1. 请在 {output_dir} 目录查看新处理的图片")
        print(f"2. 验收通过后，运行以下命令将图片合并到前端展示目录:")
        print(f"   python3 process_images.py --merge --merge-from {output_dir} --merge-to {PROJECT_IMAGES_DIR}")

if __name__ == "__main__":
    main() 