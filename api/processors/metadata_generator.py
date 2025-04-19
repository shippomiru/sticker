#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import re
import glob
from pathlib import Path
from slugify import slugify
import torch
import numpy as np
from PIL import Image
import spacy
from transformers import CLIPProcessor, CLIPModel, pipeline
import nltk
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API元数据目录
API_METADATA_DIR = "metadata/api_metadata"

# 加载spaCy模型（全局加载一次，避免重复加载）
try:
    nlp = spacy.load("en_core_web_sm")
    print("spaCy模型加载成功!")
except Exception as e:
    print(f"spaCy模型加载失败: {e}")
    print("将使用备用方法提取名词...")
    nlp = None

def identify_main_subject(image_path):
    """使用CLIP模型识别图像内容，生成更全面的描述而非从预设列表中选择"""
    try:
        print(f"识别图像内容: {image_path}")
        
        # 加载图像描述模型
        print("加载图像描述模型...")
        image_to_text = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
        
        # 打开图像
        image = Image.open(image_path)
        
        # 为透明图像创建白色背景（确保模型能正确处理）
        if image.mode == 'RGBA':
            background = Image.new('RGBA', image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(background, image)
            image = image.convert('RGB')
        
        # 生成图像描述
        print("正在分析图像...")
        result = image_to_text(image)
        
        # 获取描述文本
        description = result[0]['generated_text'] if result else "An image"
        
        # 确保描述的首字母大写
        description = description.strip()
        if len(description) > 0:
            description = description[0].upper() + description[1:]
        
        print(f"识别结果: {description}")
        return description
    
    except Exception as e:
        print(f"识别图像内容失败: {e}")
        # 返回默认描述
        return "An image"

def slugify_text(text):
    """将文本转换为URL友好的slug形式"""
    # 确保文本全部小写
    text = text.lower()
    # 使用python-slugify库处理整个文本
    return slugify(text)

def extract_id_from_filename(filename):
    """从文件名中提取Unsplash ID"""
    # 提取基本文件名（移除扩展名和处理后缀）
    base_name = filename.replace("_outlined_cropped.png", "").replace("_cropped.png", "")
    
    # 寻找Unsplash ID格式的部分（通常在文件名末尾，由字母和数字组成的长字符串）
    # Unsplash ID通常是10-11个字符
    pattern = r'[-_]([a-zA-Z0-9]{9,13})(?:-|$)'
    match = re.search(pattern, base_name)
    
    if match:
        # 返回完整的文件名前部分（一般包含作者和描述）
        return base_name
    else:
        # 如果找不到符合格式的ID，直接使用文件名
        return base_name

def load_api_metadata(unsplash_id):
    """从保存的API响应中加载元数据
    
    Args:
        unsplash_id: Unsplash图片ID
        
    Returns:
        dict: API元数据，加载失败则返回None
    """
    if not unsplash_id:
        return None
        
    metadata_path = os.path.join(API_METADATA_DIR, f"{unsplash_id}.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"加载API元数据文件失败: {metadata_path}")
    return None

def extract_unsplash_id(filename):
    """从文件名中提取Unsplash ID
    
    Args:
        filename: 图片文件名
        
    Returns:
        str: Unsplash图片ID，如果无法提取则返回None
    """
    # 尝试多种可能的格式提取ID
    patterns = [
        r'(?:^|-)([a-zA-Z0-9_-]{11})(?:-|$)',  # 匹配"-ID-"格式
        r'([a-zA-Z0-9_-]{11})\.(?:jpe?g|png)',  # 匹配"ID.jpg"格式
        r'_([a-zA-Z0-9_-]{11})(?:_|\.)'        # 匹配"_ID_"或"_ID."格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    logger.warning(f"无法从文件名提取Unsplash ID: {filename}")
    return None

def find_original_image(processed_image_path):
    """根据处理后的图片路径找到原始图片路径，只通过Unsplash ID精确匹配"""
    filename = os.path.basename(processed_image_path)
    base_name = filename.replace("_outlined_cropped.png", "").replace("_cropped.png", "")
    
    # 提取唯一识别码(Unsplash ID)
    unsplash_id = extract_unsplash_id(filename)
    
    print(f"正在查找原始图片: {filename}")
    print(f"  基础名称: {base_name}")
    print(f"  Unsplash ID: {unsplash_id if unsplash_id else '未找到'}")
    
    # 如果未找到ID，直接记录日志并返回处理后的图片路径
    if not unsplash_id:
        print(f"  ✗ 未能提取Unsplash ID，无法执行精确匹配")
        return processed_image_path
    
    # 可能的原始图片目录
    original_dirs = [
        "unsplash-images",
        "api/photos",
        "test/api/photos",
        "results",
        "input"
    ]
    
    # 支持的图片格式
    extensions = ['.jpg', '.jpeg', '.png']
    
    # 使用Unsplash ID进行精确匹配（唯一允许的匹配方法）
    for original_dir in original_dirs:
        if not os.path.exists(original_dir):
            continue
            
        print(f"  在目录中搜索ID '{unsplash_id}': {original_dir}")
        
        # 搜索包含此ID的所有文件
        id_pattern = f"*{unsplash_id}*.*"
        id_matches = glob.glob(os.path.join(original_dir, id_pattern))
        
        if id_matches:
            for match in id_matches:
                if match.lower().endswith(tuple(extensions)):
                    print(f"  ✓ 通过ID '{unsplash_id}'成功匹配: {match}")
                    return match
    
    # 如果找不到匹配，记录详细日志
    print(f"  ✗ 未能找到ID为'{unsplash_id}'的原始图片")
    print(f"    - 已搜索目录: {', '.join([d for d in original_dirs if os.path.exists(d)])}")
    
    # 返回处理后的图片路径
    print(f"  ! 未匹配成功，将使用处理后的图片路径")
    return processed_image_path

def extract_main_noun(caption):
    """使用spaCy提取描述中的主体名词"""
    print(f"分析描述: '{caption}'")
    
    # 如果spaCy加载失败，使用备用方法
    if nlp is None:
        return extract_main_noun_fallback(caption)
    
    try:
        # 特殊情况处理 - 识别常见的模式
        lower_caption = caption.lower()
        if "close up of" in lower_caption and "flower" in lower_caption:
            print("检测到特殊模式: 花卉特写")
            return "flower"
        
        # 处理文本
        doc = nlp(caption.lower())
        
        # 提取所有名词
        nouns = [token.text for token in doc if token.pos_ == "NOUN"]
        print(f"检测到的名词: {nouns}")
        
        # 优先选择重要名词（假设重要名词在最后）
        priority_nouns = ["flower", "pumpkin", "puppy", "dog", "cat", 
                          "gun", "jet", "plane", "fruit", "bird"]
        
        for pnoun in priority_nouns:
            if pnoun in nouns:
                print(f"找到优先名词: {pnoun}")
                return pnoun
        
        # 规范化一些特殊名词
        noun_mapping = {
            "revolver": "gun",
            "pistol": "gun", 
            "rifle": "gun",
            "firearm": "gun",
            "handgun": "gun",
            "aircraft": "plane",
            "airplane": "plane",
            "jetliner": "plane",
            "passenger": "plane",  # "passenger jet" 应该识别为 "plane"
            "close": "flower",  # "close up" 通常指代花卉特写
            "pumpk": "pumpkin"
        }
        
        # 尝试获取核心主语
        subjects = [token.text for token in doc if token.dep_ in ("nsubj", "dobj") and token.pos_ == "NOUN"]
        print(f"检测到的主语/宾语: {subjects}")
        
        # 首选主语作为标签
        if subjects:
            main_noun = subjects[0]
        # 其次是名词
        elif nouns:
            main_noun = nouns[0]
        # 最后是第一个词
        else:
            words = caption.lower().split()
            main_noun = words[0] if words else "object"
            for prefix in ["a ", "an ", "the "]:
                if main_noun.startswith(prefix):
                    main_noun = main_noun[len(prefix):]
        
        # 应用规范化映射
        if main_noun in noun_mapping:
            main_noun = noun_mapping[main_noun]
            
        print(f"提取的主体名词: {main_noun}")
        return main_noun
        
    except Exception as e:
        print(f"使用spaCy提取名词失败: {e}")
        print("使用备用方法...")
        return extract_main_noun_fallback(caption)
        
def extract_main_noun_fallback(caption):
    """备用方法：基于规则提取主体名词"""
    # 将描述转为小写
    clean_caption = caption.lower()
    
    # 移除冠词
    for prefix in ["a ", "an ", "the "]:
        clean_caption = clean_caption.replace(prefix, "")
    
    # 常见的修饰词模式，通常可以忽略
    modifiers = ["small ", "large ", "big ", "tiny ", "huge ", "little ", "close up of ", "close-up of "]
    for mod in modifiers:
        clean_caption = clean_caption.replace(mod, "")
    
    # 处理介词短语
    prepositions = [" on ", " in ", " with ", " at ", " by ", " from ", " to ", " of ", " and "]
    main_part = clean_caption
    for prep in prepositions:
        if prep in main_part:
            main_part = main_part.split(prep)[0].strip()
    
    # 分词
    words = main_part.split()
    
    # 常见名词列表
    common_nouns = ["puppy", "dog", "cat", "flower", "jet", "plane", "gun", "revolver", 
                     "aircraft", "animal", "bird", "tree", "plant", "fruit", "pumpkin", 
                     "table", "chair", "car", "vehicle", "person", "food", "phone"]
    
    # 寻找主要名词
    main_noun = ""
    for word in words:
        word = word.strip(".,;:!?")
        if word in common_nouns:
            main_noun = word
            break
    
    # 特殊映射
    special_cases = {
        "revolver": "gun",
        "pistol": "gun", 
        "aircraft": "plane",
        "pumpk": "pumpkin",
        "close": "flower"
    }
    
    # 如果没找到或需要特殊处理
    if not main_noun and words:
        main_noun = words[-1]  # 取最后一个词（通常是名词）
    elif not main_noun:
        main_noun = "object"
        
    # 应用特殊映射
    if main_noun in special_cases:
        main_noun = special_cases[main_noun]
    
    print(f"提取的主体名词(备用方法): {main_noun}")
    return main_noun

def classify_image_to_predefined_tags(caption, extracted_noun=None):
    """将图片基于描述分类到预定义的标签列表中"""
    # 更新的标签列表
    predefined_tags = [
        "christmas", "flower", "book", "dog", "car", "cat", "pumpkin", 
        "apple", "airplane", "birthday", "crown", "gun", "baby", 
        "camera", "money", "bird", "others"
    ]
    
    # 同义词映射，帮助匹配更多变体
    synonyms = {
        "car": ["vehicle", "truck", "automobile", "jeep", "suv"],
        "airplane": ["plane", "aircraft", "jet", "airliner"],
        "flower": ["rose", "tulip", "floral", "blossom", "petal"],
        "book": ["novel", "textbook", "journal"],
        "dog": ["puppy", "canine", "hound"],
        "cat": ["kitten", "feline", "kitty"],
        "baby": ["infant", "newborn", "child", "toddler"],
        "camera": ["dslr", "photography", "lens", "digital camera"],
        "gun": ["pistol", "rifle", "firearm", "revolver", "weapon"],
        "money": ["cash", "currency", "dollars", "bills", "coins"],
        "christmas": ["xmas", "holiday", "santa", "december"],
        "crown": ["tiara", "diadem", "coronet", "royal"],
        "bird": ["sparrow", "parrot", "avian", "wing", "feather"]
    }
    
    # 将描述转为小写便于匹配
    caption_lower = caption.lower()
    matched_tags = []
    
    # 将描述文本分词
    words = re.findall(r'\b\w+\b', caption_lower)
    
    # 1. 首先尝试使用提取的主体名词进行匹配（提高优先级）
    if extracted_noun:
        # 安全处理extracted_noun，确保是字符串类型
        extracted_lower = ""
        if isinstance(extracted_noun, list):
            # 如果是非空列表则取第一个元素
            if extracted_noun and len(extracted_noun) > 0:
                # 确保元素是字符串类型
                if isinstance(extracted_noun[0], str):
                    extracted_lower = extracted_noun[0].lower()
                else:
                    extracted_lower = str(extracted_noun[0]).lower()
        else:
            # 如果是字符串则直接使用，否则转为字符串
            if isinstance(extracted_noun, str):
                extracted_lower = extracted_noun.lower()
            else:
                extracted_lower = str(extracted_noun).lower()
        
        # 直接匹配标签
        if extracted_lower in predefined_tags and extracted_lower != "others":
            matched_tags.append(extracted_lower)
        else:
            # 匹配同义词
            for tag, tag_synonyms in synonyms.items():
                if extracted_lower in tag_synonyms:
                    matched_tags.append(tag)
                    break
    
    # 2. 如果主体名词没有匹配成功，使用单词边界匹配
    if not matched_tags:
        for tag in predefined_tags:
            if tag != "others" and tag in words:  # 检查完整单词匹配
                matched_tags.append(tag)
                break
                
        # 3. 检查同义词（使用单词边界匹配）
        if not matched_tags:
            for tag in predefined_tags:
                if tag in synonyms:
                    for synonym in synonyms[tag]:
                        if synonym in words:  # 检查完整单词匹配
                            matched_tags.append(tag)
                            break
                    if matched_tags:
                        break
    
    # 4. 如果仍未匹配到标签，使用语义相似度检测
    if not matched_tags:
        # 先检查是否是鸟类图片（避免将鸟错误分类为飞机）
        if "bird" in words or any(word in words for word in ["feather", "nest", "beak"]):
            matched_tags.append("bird")
        # 简单语义规则 - 基于关键词
        elif any(word in words for word in ["vehicle", "driving", "road"]):
            matched_tags.append("car")
        elif any(word in words for word in ["flying", "sky", "airport", "airline","airway"]) and "bird" not in words:
            matched_tags.append("airplane")
        elif any(word in words for word in ["reading", "pages", "studying"]):
            matched_tags.append("book")
        elif any(word in words for word in ["pet", "furry", "animal"]):
            if "meow" in caption_lower or "whiskers" in caption_lower:
                matched_tags.append("cat")
            else:
                matched_tags.append("dog")
        elif any(word in words for word in ["shoot", "military", "hunting"]):
            matched_tags.append("gun")
        elif any(word in words for word in ["photo", "picture", "photographer"]):
            matched_tags.append("camera")
        elif any(word in words for word in ["celebration", "party", "cake"]):
            matched_tags.append("birthday")
        elif any(word in words for word in ["cash", "bank", "finance"]):
            matched_tags.append("money")
    
    # 5. 如果仍未匹配任何标签，使用"others"标签
    if not matched_tags:
        matched_tags.append("others")
    
    print(f"将图片分类为标签: {matched_tags}")
    # 只返回第一个匹配到的标签
    return matched_tags[0] if matched_tags else "others"

def generate_metadata_for_image(image_path, image_name):
    """为单个图片生成元数据
    
    Args:
        image_path: 图片完整路径
        image_name: 图片名称（不含路径）
        
    Returns:
        dict: 图片的元数据
    """
    # 提取Unsplash ID
    unsplash_id = extract_unsplash_id(image_name)
    
    # 尝试从API元数据中加载信息
    api_metadata = load_api_metadata(unsplash_id) if unsplash_id else None
    
    # 如果有API元数据，优先使用
    if api_metadata:
        logger.info(f"使用API元数据生成图片 {image_name} 的信息")
        
        # 构建元数据
        metadata = {
            "id": image_name.replace(".png", ""),
            "caption": api_metadata.get("description") or api_metadata.get("alt_description") or "",
            "tags": [],  # API中没有明确的tags字段，可以在前端添加
            "author": api_metadata.get("author", ""),
            "unsplash_id": api_metadata.get("unsplash_id", unsplash_id),
            "original_url": f"https://unsplash.com/photos/{unsplash_id}",
            "download_location": api_metadata.get("download_location", ""),
            "username": api_metadata.get("username", "")
        }
        
        # 确保图片URL正确（增加/images/前缀如果需要）
        if not image_path.startswith("/images/"):
            image_path = f"/images/{image_path}"
        metadata["image"] = image_path
        
        return metadata
    
    # 如果没有API元数据，回退到传统解析方式
    logger.info(f"使用传统方式解析图片 {image_name} 的信息")
    
    # 从文件名解析作者（标准命名格式：作者名-ID-unsplash）
    author = ""
    if "-" in image_name and unsplash_id:
        parts = image_name.split("-")
        if len(parts) >= 3:
            author = parts[0].replace("-", " ").title()  # 将短横线替换为空格并首字母大写
    
    # 构建元数据
    metadata = {
        "id": image_name.replace(".png", ""),
        "caption": "",  # 没有来源信息时无法获取说明
        "tags": [],
        "author": author,
        "unsplash_id": unsplash_id
    }
    
    # 如果有unsplash_id，添加原始URL和下载链接
    if unsplash_id:
        metadata["original_url"] = f"https://unsplash.com/photos/{unsplash_id}"
        # 构造一个基础下载链接
        metadata["download_location"] = f"https://api.unsplash.com/photos/{unsplash_id}/download"
    
    # 确保图片URL正确（增加/images/前缀如果需要）
    if not image_path.startswith("/images/"):
        image_path = f"/images/{image_path}"
    metadata["image"] = image_path
    
    return metadata

def process_images_batch(input_dir, output_file, limit=None):
    """处理目录中的所有图片并生成元数据JSON文件"""
    # 确保输入目录存在
    if not os.path.exists(input_dir):
        print(f"输入目录不存在: {input_dir}")
        return
    
    # 获取所有PNG图片路径
    # 只处理一种类型的图片（透明或带白边），避免重复处理
    png_files = []
    for file in os.listdir(input_dir):
        if file.endswith("_outlined_cropped.png"):
            png_files.append(os.path.join(input_dir, file))
    
    print(f"找到 {len(png_files)} 个带白边的PNG图片")
    
    # 限制处理数量（如果指定）
    if limit and limit > 0:
        png_files = png_files[:limit]
        print(f"将处理前 {limit} 个图片")
    
    # 处理每个图片并生成元数据
    all_metadata = []
    used_slugs = set()  # 用于追踪已使用的slug
    missing_originals = []  # 跟踪未找到原始图片的条目
    
    for image_path in png_files:
        metadata = generate_metadata_for_image(image_path, os.path.basename(image_path))
        if metadata:
            # 检查slug是否重复，如果重复则添加后缀
            original_slug = metadata["slug"]
            unique_slug = original_slug
            counter = 1
            
            while unique_slug in used_slugs:
                print(f"警告: 检测到重复的slug: {unique_slug}")
                unique_slug = f"{original_slug}-{counter}"
                counter += 1
                print(f"修改为: {unique_slug}")
            
            # 更新metadata中的slug并记录
            metadata["slug"] = unique_slug
            used_slugs.add(unique_slug)
            all_metadata.append(metadata)
            
            # 检查是否需要记录缺失的原始图片
            if image_path == find_original_image(image_path):
                missing_originals.append(metadata["id"])
    
    # 记录重复slug处理结果
    if len(used_slugs) < len(all_metadata):
        print(f"\n注意: 检测并处理了 {len(all_metadata) - len(used_slugs)} 个重复的slug值")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存元数据到主数据源目录 (api/data)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    # 同时保存到前端项目目录
    project_data_dir = "project/src/data"
    os.makedirs(project_data_dir, exist_ok=True)
    project_output_file = os.path.join(project_data_dir, "images.json")
    with open(project_output_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    # 记录缺失原始图片的条目
    if missing_originals:
        missing_log = os.path.join(os.path.dirname(output_file), "missing_originals.log")
        with open(missing_log, 'w', encoding='utf-8') as f:
            for item in missing_originals:
                f.write(f"{item}\n")
    
    print(f"\n元数据生成完成! 共处理 {len(all_metadata)} 个图片")
    print(f"元数据已保存到: {output_file}")
    print(f"元数据同时保存到: {project_output_file} (前端使用)")
    
    if missing_originals:
        print(f"\n未找到原始图片的记录已保存到 {missing_log}")
    
    return all_metadata

def test_extract_unsplash_id():
    """测试Unsplash ID提取函数"""
    test_cases = [
        # 标准格式
        ("aaron-huber-V09Io5ln-Qo-unsplash.jpg", "V09Io5ln-Qo"),
        ("alex-lvrs-ZRTd9_Fk6rc-unsplash.jpg", "ZRTd9_Fk6rc"),
        ("alexander-andrews-VLGWE_SumrA-unsplash.jpg", "VLGWE_SumrA"),
        # 非标准格式
        ("ayako-h7Dw2hF4e0A-unsplash.jpg", "h7Dw2hF4e0A"),
        # 带处理后缀的格式
        ("arkin-si-nkIIbgOVyl4-unsplash_outlined_cropped.png", "nkIIbgOVyl4"),
        ("luis-domenech-LSu04HMpL7A-unsplash_cropped.png", "LSu04HMpL7A"),
        # 带下划线的ID
        ("cody-board-tnNVJd_nrw8-unsplash.jpg", "tnNVJd_nrw8"),
        ("nikhita-singhal-4m1qd_DjAx0-unsplash.jpg", "4m1qd_DjAx0"),
        # 无效格式
        ("not-a-unsplash-photo.jpg", None),
        ("invalid-format.png", None),
    ]
    
    print("开始测试Unsplash ID提取函数...")
    
    for filename, expected_id in test_cases:
        extracted_id = extract_unsplash_id(filename)
        if extracted_id == expected_id:
            print(f"✓ {filename} -> {extracted_id}")
        else:
            print(f"✗ {filename} -> 提取结果: {extracted_id}，期望结果: {expected_id}")
    
    print("Unsplash ID提取函数测试完成")

def main():
    # 首先运行ID提取测试
    test_extract_unsplash_id()
    
    # 输入目录（带白边的PNG图片目录）
    input_dir = "project/public/images"
    
    # 输出元数据JSON文件路径
    output_file = "metadata/images.json"
    
    # 处理所有图片并生成元数据
    process_images_batch(input_dir, output_file)

if __name__ == "__main__":
    main() 