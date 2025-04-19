import os
import json
import time
import logging
from glob import glob
from datetime import datetime
from pathlib import Path

from ..processors.image_processor import process_image, crop_to_square, add_white_outline
from ..processors.background_remover import remove_background_from_image
from ..processors.metadata_generator import generate_metadata_for_image
from ..importers.unsplash_importer import import_photo_by_id, download_photo, check_image_exists_by_api_id

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnsplashWorkflow:
    """Unsplash图片处理工作流"""
    
    def __init__(self, batch_date=None):
        """初始化工作流
        
        Args:
            batch_date: 批次日期，如果未提供则使用当前日期
        """
        # 设置批次日期
        self.batch_date = batch_date or datetime.now().strftime("%Y%m%d")
        
        # 创建工作目录
        self.base_dir = os.path.abspath("batch")
        self.batch_dir = os.path.join(self.base_dir, self.batch_date)
        os.makedirs(self.batch_dir, exist_ok=True)
        
        # 设置各阶段目录
        self.original_dir = os.path.join(self.batch_dir, "original")
        self.no_bg_dir = os.path.join(self.batch_dir, "no-background")
        self.cropped_dir = os.path.join(self.batch_dir, "cropped")
        self.outlined_dir = os.path.join(self.batch_dir, "outlined")
        self.metadata_dir = os.path.join(self.batch_dir, "metadata")
        
        # 创建所有必要的目录
        for directory in [self.original_dir, self.no_bg_dir, self.cropped_dir, 
                         self.outlined_dir, self.metadata_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 初始化工作流状态
        self.state_file = os.path.join(self.batch_dir, "workflow_state.json")
        self.state = self.load_state() or {
            "imported_photos": [],
            "processed_no_bg": [],
            "processed_cropped": [],
            "processed_outlined": [],
            "generated_metadata": False,
            "moved_to_public": False,
            "api_metadata": {}  # 保存API返回的元数据
        }
        
        # 创建API元数据目录（用于保存完整API响应）
        self.api_metadata_dir = os.path.join("metadata", "api_metadata")
        os.makedirs(self.api_metadata_dir, exist_ok=True)
        
        # 验证processed-images目录存在
        self.processed_images_dir = "processed-images"
        if not os.path.exists(self.processed_images_dir):
            os.makedirs(self.processed_images_dir, exist_ok=True)
            logger.info(f"创建processed-images目录: {self.processed_images_dir}")
    
    def load_state(self):
        """加载工作流状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"无法解析工作流状态文件: {self.state_file}")
        return None
    
    def save_state(self):
        """保存工作流状态"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        logger.info(f"已保存工作流状态: {self.state_file}")
    
    def import_photos(self, photo_ids):
        """导入Unsplash照片
        
        Args:
            photo_ids: Unsplash照片ID列表
            
        Returns:
            list: 成功导入的照片路径列表
        """
        logger.info(f"开始导入 {len(photo_ids)} 张Unsplash照片")
        imported = []
        
        for photo_id in photo_ids:
            # 检查照片是否已存在
            if check_image_exists_by_api_id(photo_id):
                logger.info(f"照片 {photo_id} 已存在，跳过导入")
                continue
                
            # 导入照片
            try:
                result = import_photo_by_id(photo_id, self.original_dir)
                if result[0]:  # 如果导入成功
                    saved_file, metadata = result
                    
                    # 记录已导入的照片
                    self.state["imported_photos"].append(saved_file)
                    
                    # 如果有API元数据，保存它
                    if metadata:
                        # 记录在工作流状态中
                        if "api_metadata" not in self.state:
                            self.state["api_metadata"] = {}
                        
                        # 使用Unsplash ID作为键
                        if "unsplash_id" in metadata:
                            unsplash_id = metadata["unsplash_id"]
                            self.state["api_metadata"][unsplash_id] = metadata
                            
                            # 同时单独保存API元数据文件
                            metadata_file = os.path.join(self.api_metadata_dir, f"{unsplash_id}.json")
                            with open(metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, indent=2, ensure_ascii=False)
                            logger.info(f"已保存API元数据: {metadata_file}")
                    
                    imported.append(saved_file)
                    logger.info(f"成功导入照片: {saved_file}")
                else:
                    logger.error(f"导入照片失败: {photo_id}")
            except Exception as e:
                logger.error(f"导入照片 {photo_id} 时出错: {str(e)}")
        
        # 保存工作流状态
        self.save_state()
        logger.info(f"共导入 {len(imported)} 张照片")
        return imported
    
    def remove_backgrounds(self):
        """为所有导入的照片去除背景"""
        logger.info("开始去除背景")
        processed = []
        
        # 获取已导入但尚未处理的照片
        to_process = [p for p in self.state["imported_photos"] 
                    if p not in self.state["processed_no_bg"]]
        
        logger.info(f"需要处理 {len(to_process)} 张照片")
        for image_path in to_process:
            try:
                # 生成输出路径
                filename = os.path.basename(image_path)
                output_path = os.path.join(self.no_bg_dir, filename)
                
                # 移除背景
                remove_background_from_image(image_path, output_path)
                
                # 记录已处理的照片
                self.state["processed_no_bg"].append(image_path)
                processed.append(output_path)
                logger.info(f"成功去除背景: {output_path}")
            except Exception as e:
                logger.error(f"去除背景失败: {image_path} - {str(e)}")
        
        # 保存工作流状态
        self.save_state()
        logger.info(f"共处理 {len(processed)} 张照片背景")
        return processed
    
    def crop_images(self):
        """将无背景图片裁剪成正方形"""
        logger.info("开始裁剪图片")
        processed = []
        
        # 获取已去除背景但尚未裁剪的照片
        original_to_process = [p for p in self.state["imported_photos"] 
                             if p not in self.state["processed_cropped"]]
        
        # 根据原始图片路径找到对应的无背景图片路径
        to_process = []
        for orig in original_to_process:
            filename = os.path.basename(orig)
            no_bg_path = os.path.join(self.no_bg_dir, filename)
            if os.path.exists(no_bg_path):
                to_process.append((orig, no_bg_path))
            else:
                logger.warning(f"无背景图片不存在: {no_bg_path}")
        
        logger.info(f"需要裁剪 {len(to_process)} 张照片")
        for orig_path, no_bg_path in to_process:
            try:
                # 生成输出路径
                filename = os.path.basename(no_bg_path)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(self.cropped_dir, f"{base_name}_cropped.png")
                
                # 裁剪图片
                crop_to_square(no_bg_path, output_path)
                
                # 记录已处理的照片
                self.state["processed_cropped"].append(orig_path)
                processed.append(output_path)
                logger.info(f"成功裁剪图片: {output_path}")
            except Exception as e:
                logger.error(f"裁剪图片失败: {no_bg_path} - {str(e)}")
        
        # 保存工作流状态
        self.save_state()
        logger.info(f"共裁剪 {len(processed)} 张照片")
        return processed
    
    def add_outlines(self):
        """为裁剪后的图片添加白色轮廓"""
        logger.info("开始添加白色轮廓")
        processed = []
        
        # 获取已裁剪但尚未添加轮廓的照片
        original_to_process = [p for p in self.state["imported_photos"] 
                             if p not in self.state["processed_outlined"]]
        
        # 寻找对应的裁剪后图片
        to_process = []
        for orig in original_to_process:
            filename = os.path.basename(orig)
            base_name = os.path.splitext(filename)[0]
            cropped_path = os.path.join(self.cropped_dir, f"{base_name}_cropped.png")
            if os.path.exists(cropped_path):
                to_process.append((orig, cropped_path))
            else:
                logger.warning(f"裁剪后图片不存在: {cropped_path}")
        
        logger.info(f"需要添加轮廓 {len(to_process)} 张照片")
        for orig_path, cropped_path in to_process:
            try:
                # 生成输出路径
                filename = os.path.basename(cropped_path)
                base_name = filename.replace("_cropped.png", "")
                output_path = os.path.join(self.outlined_dir, f"{base_name}_outlined_cropped.png")
                
                # 添加白色轮廓
                add_white_outline(cropped_path, output_path)
                
                # 记录已处理的照片
                self.state["processed_outlined"].append(orig_path)
                processed.append(output_path)
                logger.info(f"成功添加白色轮廓: {output_path}")
            except Exception as e:
                logger.error(f"添加白色轮廓失败: {cropped_path} - {str(e)}")
        
        # 保存工作流状态
        self.save_state()
        logger.info(f"共添加轮廓 {len(processed)} 张照片")
        return processed
    
    def move_to_public(self):
        """将处理后的图片移动到public目录"""
        logger.info("开始移动图片到processed-images目录")
        moved = []
        
        # 查找所有处理完成的图片
        cropped_pattern = os.path.join(self.cropped_dir, "*_cropped.png")
        outlined_pattern = os.path.join(self.outlined_dir, "*_outlined_cropped.png")
        
        cropped_files = glob(cropped_pattern)
        outlined_files = glob(outlined_pattern)
        
        logger.info(f"找到 {len(cropped_files)} 张裁剪图片和 {len(outlined_files)} 张轮廓图片")
        
        # 移动裁剪图片
        for src_path in cropped_files:
            filename = os.path.basename(src_path)
            dst_path = os.path.join(self.processed_images_dir, filename)
            try:
                # 如果目标文件已存在，先删除
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                
                # 复制文件
                with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
                    dst.write(src.read())
                
                moved.append(dst_path)
                logger.info(f"已移动裁剪图片: {dst_path}")
            except Exception as e:
                logger.error(f"移动裁剪图片失败: {src_path} - {str(e)}")
        
        # 移动轮廓图片
        for src_path in outlined_files:
            filename = os.path.basename(src_path)
            dst_path = os.path.join(self.processed_images_dir, filename)
            try:
                # 如果目标文件已存在，先删除
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                
                # 复制文件
                with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
                    dst.write(src.read())
                
                moved.append(dst_path)
                logger.info(f"已移动轮廓图片: {dst_path}")
            except Exception as e:
                logger.error(f"移动轮廓图片失败: {src_path} - {str(e)}")
        
        # 标记为已移动
        self.state["moved_to_public"] = True
        self.save_state()
        
        logger.info(f"共移动 {len(moved)} 张图片到processed-images目录")
        return moved
    
    def generate_metadata(self):
        """为处理后的图片生成元数据"""
        logger.info("开始生成元数据")
        
        # 检查processed-images目录是否存在
        if not os.path.exists(self.processed_images_dir):
            logger.error(f"processed-images目录不存在: {self.processed_images_dir}")
            return None
        
        # 查找所有处理完成的图片
        processed_pattern = os.path.join(self.processed_images_dir, "*_outlined_cropped.png")
        png_files = glob(processed_pattern)
        
        if not png_files:
            logger.warning("未找到需要处理的图片")
            return None
        
        logger.info(f"找到 {len(png_files)} 张需要生成元数据的图片")
        
        # 准备存储目录
        metadata_dir = os.path.join("metadata", self.batch_date)
        os.makedirs(metadata_dir, exist_ok=True)
        
        # 生成metadata.json文件路径
        metadata_file = os.path.join(metadata_dir, "images.json")
        
        # 生成所有图片的元数据
        all_metadata = []
        for image_path in png_files:
            filename = os.path.basename(image_path)
            rel_path = os.path.join(self.processed_images_dir, filename)
            
            # 生成元数据
            metadata = generate_metadata_for_image(rel_path, filename)
            
            if metadata:
                all_metadata.append(metadata)
                logger.info(f"已生成元数据: {filename}")
            else:
                logger.warning(f"无法生成元数据: {filename}")
        
        # 保存元数据文件
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, indent=2, ensure_ascii=False)
        
        # 标记为已生成元数据
        self.state["generated_metadata"] = True
        self.save_state()
        
        logger.info(f"共生成 {len(all_metadata)} 条元数据，保存至: {metadata_file}")
        return metadata_file
    
    def run_complete_workflow(self, photo_ids):
        """运行完整的工作流程
        
        Args:
            photo_ids: Unsplash照片ID列表
            
        Returns:
            dict: 工作流结果
        """
        logger.info(f"开始运行完整工作流，批次日期: {self.batch_date}")
        
        # 1. 导入照片
        imported = self.import_photos(photo_ids)
        
        # 如果没有导入任何照片，则工作流结束
        if not imported:
            logger.warning("没有导入任何照片，工作流结束")
            return {"status": "no_images", "batch_date": self.batch_date}
        
        # 2. 移除背景
        no_bg = self.remove_backgrounds()
        
        # 3. 裁剪图片
        cropped = self.crop_images()
        
        # 4. 添加白色轮廓
        outlined = self.add_outlines()
        
        # 5. 移动到public目录
        moved = self.move_to_public()
        
        # 6. 生成元数据
        metadata_file = self.generate_metadata()
        
        # 返回工作流结果
        result = {
            "status": "success",
            "batch_date": self.batch_date,
            "imported": len(imported),
            "no_bg": len(no_bg),
            "cropped": len(cropped),
            "outlined": len(outlined),
            "moved": len(moved),
            "metadata_file": metadata_file
        }
        
        logger.info(f"工作流完成: {json.dumps(result, indent=2)}")
        return result 