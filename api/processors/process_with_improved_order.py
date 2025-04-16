#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import numpy as np
from PIL import Image
from rembg import remove
import sys
import time

# 导入现有的描边生成函数
from test_smooth_no_gap_outline import create_smooth_no_gap_outline

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
        
        print(f"裁剪完成，已保存到: {output_path}")
        print(f"原始图片尺寸: {img.width}x{img.height}")
        print(f"裁剪后尺寸: {cropped_img.width}x{cropped_img.height}")
        print(f"主体区域: 左上({x_min},{y_min}), 右下({x_max},{y_max})")
        print(f"主体尺寸: {subject_width}x{subject_height}")
        print(f"裁剪区域: 左上({left},{upper}), 右下({right},{lower})")
        print(f"安全边距: {safety_padding*100}%")
        
        return True
    except Exception as e:
        print(f"裁剪图片失败 {input_path}: {e}")
        return False

def process_image(jpg_file, output_dir, temp_dir, outline_size=40, edge_buffer=3, target_ratio=0.5, safety_padding=0.15):
    """处理单个JPG图片：抠图 -> 裁剪 -> 加白边"""
    try:
        # 确保临时目录和输出目录存在
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
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
        
        # 将裁剪后的图片复制到输出目录 - 透明背景版
        if not os.path.exists(cropped_final_png):
            print(f"保存透明背景版本到输出目录: {cropped_final_png}")
            # 读取临时目录中的裁剪图片
            temp_cropped_img = Image.open(cropped_png)
            # 保存到输出目录
            temp_cropped_img.save(cropped_final_png)
            print(f"透明背景版本已保存: {cropped_final_png}")
        else:
            print(f"透明背景版本已存在: {cropped_final_png}")
        
        # 步骤3: 添加平滑无间隙的白色描边 - 带白边版
        if not os.path.exists(outlined_png):
            print("正在执行步骤3: 添加白边")
            success = create_smooth_no_gap_outline(
                cropped_png, 
                outlined_png, 
                outline_size=outline_size,
                edge_buffer=edge_buffer
            )
            if not success:
                print(f"添加白边失败: {basename}")
                return False
        else:
            print(f"带白边版本已存在: {outlined_png}")
        
        print(f"图片处理完成: {basename}")
        print(f"- 透明背景版本: {cropped_final_png}")
        print(f"- 带白边版本: {outlined_png}")
        return True
    except Exception as e:
        print(f"处理图片过程中发生错误 {jpg_file}: {e}")
        return False

def process_images(input_dir, output_dir, temp_dir, outline_size=40, edge_buffer=3, target_ratio=0.5, safety_padding=0.15):
    """处理指定目录下的所有JPG图片"""
    # 确保输出目录和临时目录存在
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    # 获取所有JPG文件
    jpg_files = glob.glob(os.path.join(input_dir, "*.jpg"))
    
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

def main():
    # 输入、输出和临时目录
    input_dir = "unsplash-images"       # 原始JPG图片目录（修改为新的默认目录）
    temp_dir = "temp-results"           # 临时文件存储目录
    output_dir = "processed-images"     # 处理后的图片目录（替代results-photos-cropped）
    
    # 处理所有图片
    # 步骤顺序: 抠图 -> 裁剪 -> 加白边
    process_images(
        input_dir, 
        output_dir, 
        temp_dir,
        outline_size=40,           # 白边大小
        edge_buffer=3,             # 边缘缓冲区大小
        target_ratio=0.5,          # 主体占图片的面积比例
        safety_padding=0.15        # 主体周围的安全边距
    )

if __name__ == "__main__":
    main() 