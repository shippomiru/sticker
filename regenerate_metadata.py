#!/usr/bin/env python3
import os
import json
import glob
import logging
import argparse
from datetime import datetime
from pathlib import Path

from api.processors.metadata_generator import generate_metadata_for_image

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def regenerate_all_metadata(output_dir=None, batch_size=None):
    """重新生成所有图片的元数据
    
    Args:
        output_dir: 输出目录，如果为None则使用当前日期创建目录
        batch_size: 每个批次处理的图片数量，如果为None则一次处理所有图片
        
    Returns:
        str: 元数据文件路径
    """
    # 设置输出目录
    if output_dir is None:
        today = datetime.now().strftime("%Y%m%d")
        output_dir = os.path.join("metadata", today)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    
    # 查找所有处理完成的图片
    processed_images_dir = "processed-images"
    if not os.path.exists(processed_images_dir):
        logger.error(f"processed-images目录不存在: {processed_images_dir}")
        return None
    
    # 查找所有PNG图片
    png_pattern = os.path.join(processed_images_dir, "*.png")
    png_files = glob.glob(png_pattern)
    
    # 过滤出包含"outlined_cropped"的图片
    outlined_files = [f for f in png_files if "_outlined_cropped.png" in f]
    
    if not outlined_files:
        logger.warning("未找到需要处理的图片")
        return None
    
    logger.info(f"找到 {len(outlined_files)} 张需要生成元数据的图片")
    
    # 如果指定了批次大小，则分批处理
    if batch_size is not None:
        batches = [outlined_files[i:i + batch_size] for i in range(0, len(outlined_files), batch_size)]
        logger.info(f"将分 {len(batches)} 批处理，每批 {batch_size} 张图片")
    else:
        batches = [outlined_files]
        logger.info("将一次处理所有图片")
    
    # 生成元数据文件路径
    metadata_file = os.path.join(output_dir, "images.json")
    
    # 如果存在旧的元数据文件，先加载它
    all_metadata = []
    processed_filenames = set()
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)
                logger.info(f"加载了现有元数据文件，包含 {len(all_metadata)} 条记录")
                
                # 记录已处理的文件名
                for item in all_metadata:
                    if 'path' in item:
                        processed_filenames.add(os.path.basename(item['path']))
        except Exception as e:
            logger.error(f"加载元数据文件失败: {str(e)}")
            all_metadata = []
    
    # 统计信息
    total_processed = 0
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # 处理所有批次
    for batch_idx, batch in enumerate(batches):
        logger.info(f"开始处理第 {batch_idx+1}/{len(batches)} 批")
        
        # 处理批次中的每个图片
        for image_path in batch:
            filename = os.path.basename(image_path)
            
            # 如果已经处理过，跳过
            if filename in processed_filenames:
                logger.info(f"跳过已处理的图片: {filename}")
                skipped_count += 1
                continue
            
            # 生成元数据
            try:
                metadata = generate_metadata_for_image(image_path, filename)
                
                if metadata:
                    all_metadata.append(metadata)
                    success_count += 1
                    logger.info(f"已生成元数据: {filename}")
                else:
                    failed_count += 1
                    logger.warning(f"无法生成元数据: {filename}")
                
                total_processed += 1
                
                # 每处理100张图片，保存一次元数据文件
                if total_processed % 100 == 0:
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
                    logger.info(f"已保存中间结果，处理进度: {total_processed}/{len(outlined_files)}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"处理图片失败: {filename} - {str(e)}")
                total_processed += 1
        
        # 每批结束后保存元数据文件
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"批次 {batch_idx+1} 完成，已保存元数据文件")
    
    # 再次检查元数据质量
    valid_metadata = []
    for item in all_metadata:
        if 'path' in item and 'unsplash_id' in item:
            valid_metadata.append(item)
        else:
            logger.warning(f"发现不完整的元数据项: {item.get('path', '未知路径')}")
    
    # 保存最终元数据文件
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(valid_metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"元数据生成完成:")
    logger.info(f"  - 总图片数量: {len(outlined_files)}")
    logger.info(f"  - 成功处理: {success_count}")
    logger.info(f"  - 处理失败: {failed_count}")
    logger.info(f"  - 跳过已处理: {skipped_count}")
    logger.info(f"  - 有效元数据数量: {len(valid_metadata)}")
    logger.info(f"  - 元数据文件保存至: {metadata_file}")
    
    return metadata_file

def verify_api_metadata_coverage():
    """检查已保存的API元数据覆盖率"""
    # 检查API元数据目录
    api_metadata_dir = os.path.join("metadata", "api_metadata")
    if not os.path.exists(api_metadata_dir):
        logger.error(f"API元数据目录不存在: {api_metadata_dir}")
        return
    
    # 获取所有API元数据文件
    api_metadata_files = glob.glob(os.path.join(api_metadata_dir, "*.json"))
    api_ids = set([os.path.splitext(os.path.basename(f))[0] for f in api_metadata_files])
    
    logger.info(f"找到 {len(api_ids)} 个已保存的API元数据文件")
    
    # 加载图片元数据
    latest_metadata_dir = find_latest_metadata_dir()
    if not latest_metadata_dir:
        logger.error("未找到最新的元数据目录")
        return
    
    metadata_file = os.path.join(latest_metadata_dir, "images.json")
    if not os.path.exists(metadata_file):
        logger.error(f"元数据文件不存在: {metadata_file}")
        return
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            all_metadata = json.load(f)
    except Exception as e:
        logger.error(f"加载元数据文件失败: {str(e)}")
        return
    
    # 统计API ID覆盖率
    total_images = len(all_metadata)
    images_with_id = 0
    images_with_api_metadata = 0
    
    for item in all_metadata:
        if 'unsplash_id' in item and item['unsplash_id']:
            images_with_id += 1
            if item['unsplash_id'] in api_ids:
                images_with_api_metadata += 1
    
    # 输出统计信息
    logger.info(f"API元数据覆盖率统计:")
    logger.info(f"  - 总图片数量: {total_images}")
    logger.info(f"  - 带有Unsplash ID的图片: {images_with_id} ({images_with_id/total_images*100:.2f}%)")
    logger.info(f"  - 有API元数据的图片: {images_with_api_metadata} ({images_with_api_metadata/total_images*100:.2f}%)")
    
    if images_with_id > 0:
        logger.info(f"  - ID中有API元数据的占比: {images_with_api_metadata/images_with_id*100:.2f}%")
    
    # 返回统计信息
    return {
        "total_images": total_images,
        "images_with_id": images_with_id,
        "images_with_api_metadata": images_with_api_metadata
    }

def find_latest_metadata_dir():
    """查找最新的元数据目录"""
    metadata_base = "metadata"
    if not os.path.exists(metadata_base):
        return None
    
    # 查找所有日期命名的目录
    date_dirs = []
    for item in os.listdir(metadata_base):
        dir_path = os.path.join(metadata_base, item)
        if os.path.isdir(dir_path) and item.isdigit() and len(item) == 8:
            date_dirs.append(item)
    
    if not date_dirs:
        return None
    
    # 按日期排序
    latest_dir = sorted(date_dirs, reverse=True)[0]
    return os.path.join(metadata_base, latest_dir)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='重新生成图片元数据')
    parser.add_argument('--output-dir', type=str, help='输出目录，默认使用当前日期')
    parser.add_argument('--batch-size', type=int, help='每个批次处理的图片数量')
    parser.add_argument('--verify-only', action='store_true', help='仅验证API元数据覆盖率，不重新生成元数据')
    
    args = parser.parse_args()
    
    if args.verify_only:
        logger.info("仅验证API元数据覆盖率")
        verify_api_metadata_coverage()
    else:
        logger.info("开始重新生成图片元数据")
        regenerate_all_metadata(args.output_dir, args.batch_size)
        
        # 验证API元数据覆盖率
        logger.info("验证API元数据覆盖率")
        verify_api_metadata_coverage()

if __name__ == "__main__":
    main() 