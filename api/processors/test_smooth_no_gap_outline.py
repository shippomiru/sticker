#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from PIL import Image, ImageFilter, ImageChops

def create_smooth_no_gap_outline(input_path, output_path, outline_size=40, edge_buffer=3):
    """创建平滑圆润且无间隙的白色描边"""
    try:
        # 打开透明PNG图片
        original = Image.open(input_path)
        
        # 记录原始尺寸
        width, height = original.size
        
        # 创建足够大的画布以容纳描边
        new_size = (width + 2*outline_size, height + 2*outline_size)
        result = Image.new('RGBA', new_size, (0, 0, 0, 0))
        
        # ===== 结合无间隙和平滑圆润边缘的描边算法 =====
        
        # 1. 获取原始alpha通道
        r, g, b, alpha = original.split()
        
        # 2. 创建二值化的alpha通道
        binary_alpha = alpha.point(lambda p: 255 if p > 20 else 0)
        
        # 3. 收缩alpha，创建干净的内部区域
        shrunk_alpha = binary_alpha.copy()
        for i in range(edge_buffer):
            shrunk_alpha = shrunk_alpha.filter(ImageFilter.MinFilter(3))
        
        # 4. 创建基于收缩alpha的内部形状
        inner_shape = Image.new('L', shrunk_alpha.size, 0)
        inner_shape.paste(255, (0, 0), shrunk_alpha)
        
        # 5. 创建扩展的外部形状（描边外缘）
        outer_shape = inner_shape.copy()
        
        # 第一阶段：快速扩展主要轮廓，使用更大的滤波器尺寸
        for i in range(8):  # 增加迭代次数确保足够宽
            outer_shape = outer_shape.filter(ImageFilter.MaxFilter(9))
        
        # 6. 平滑处理外部轮廓边缘
        # 关键改进：多重高斯模糊和平滑处理，使边缘更加圆润
        smooth_mask = outer_shape.filter(ImageFilter.GaussianBlur(radius=4))  # 较大半径的高斯模糊
        
        # 第二阶段：阈值化处理，创建平滑过渡
        def smooth_threshold(pixel):
            if pixel > 220:  # 高阈值区域为纯白
                return 255
            elif pixel > 50:  # 中间过渡区域保持渐变效果
                return pixel
            else:
                return 0
                
        smooth_mask = smooth_mask.point(smooth_threshold)
        
        # 第三阶段：额外的平滑处理
        smooth_mask = smooth_mask.filter(ImageFilter.GaussianBlur(radius=2))
        smooth_mask = smooth_mask.filter(ImageFilter.SMOOTH_MORE)
        
        # 第四阶段：确保内部区域保持纯白色
        final_mask = Image.composite(Image.new('L', smooth_mask.size, 255), smooth_mask, inner_shape)
        
        # 7. 创建一个白色图像
        white_fill = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        
        # 8. 粘贴白色区域到结果画布
        result.paste(white_fill, (outline_size, outline_size), final_mask)
        
        # 9. 处理原图的边缘，确保没有半透明区域
        # 创建白色填充版的原图，用于边缘处理
        white_rgb = Image.new('RGB', original.size, (255, 255, 255))
        
        # 计算半透明边缘区域
        edge_alpha = alpha.point(lambda p: 255 if 20 < p < 240 else 0)
        
        # 为半透明区域使用白色填充
        final_r = Image.composite(white_rgb.split()[0], r, edge_alpha)
        final_g = Image.composite(white_rgb.split()[1], g, edge_alpha)
        final_b = Image.composite(white_rgb.split()[2], b, edge_alpha)
        
        # 10. 创建最终的干净原图
        clean_original = Image.merge('RGBA', (final_r, final_g, final_b, shrunk_alpha))
        
        # 11. 将原图粘贴到结果上
        result.paste(clean_original, (outline_size, outline_size), shrunk_alpha)
        
        # 保存结果
        result.save(output_path)
        
        print(f"添加平滑圆润无间隙的白色描边完成，已保存到: {output_path}")
        return True
    except Exception as e:
        print(f"创建描边失败: {e}")
        print(f"错误详情: {e}")
        return False

def main():
    # 确保结果目录存在
    os.makedirs("results", exist_ok=True)
    
    # 获取已有的透明PNG图片
    input_files = [
        "results/andrew-small-EfhCUc_fjrU-unsplash_transparent.png",
        "results/han-chenxu-YdAqiUkUoWA-unsplash_transparent.png",
        "results/cat_transparent.png",
        "results/tran-mau-tri-tam-7QjU_u2vGDs-unsplash_transparent.png",
        "results/gabriel-martin-MV0P_nciHVk-unsplash_transparent.png"
    ]
    
    # 处理所有图片
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"文件不存在: {input_file}")
            continue
            
        # 输出文件名
        basename = os.path.basename(input_file).replace("_transparent.png", "")
        output_file = f"results/{basename}_smooth_no_gap_outline.png"
        
        print(f"\n处理文件: {input_file}")
        create_smooth_no_gap_outline(input_file, output_file, outline_size=40, edge_buffer=3)
    
    print("\n处理完成! 所有图片都已添加平滑圆润无间隙的白色描边")
    print("请查看 *_smooth_no_gap_outline.png 文件")

if __name__ == "__main__":
    main() 