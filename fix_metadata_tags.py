#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修正元数据标签脚本

此脚本用于修正元数据中的图片分类，将指定描述的图片标签都更改为airplane。
"""

import os
import json
import time

# 需要修正的描述列表及其对应的正确标签
CORRECTIONS = [
    {"caption": "A cathayo airplane flying in the sky", "correct_tag": "airplane"},
    {"caption": "Cathayo airplane sticker", "correct_tag": "airplane"},
    {"caption": "A view of the wing of an airplane", "correct_tag": "airplane"},
    {"caption": "A view of a plane wing from the window", "correct_tag": "airplane"},
    {"caption": "American airlines a320 - 300", "correct_tag": "airplane"},
    {"caption": "Qatar a380 - 300 - qatar airways - qatar airways", "correct_tag": "airplane"},
    
    # 添加更多航空相关关键词
    {"caption": "airplane", "correct_tag": "airplane"},
    {"caption": "plane", "correct_tag": "airplane"},
    {"caption": "aircraft", "correct_tag": "airplane"},
    {"caption": "jet", "correct_tag": "airplane"},
    {"caption": "airliner", "correct_tag": "airplane"},
    {"caption": "flight", "correct_tag": "airplane"},
    {"caption": "flying", "correct_tag": "airplane"},
    {"caption": "wing", "correct_tag": "airplane"},
    {"caption": "airport", "correct_tag": "airplane"},
    {"caption": "airline", "correct_tag": "airplane"},
    {"caption": "airways", "correct_tag": "airplane"},
    {"caption": "boeing", "correct_tag": "airplane"},
    {"caption": "airbus", "correct_tag": "airplane"},
    {"caption": "a320", "correct_tag": "airplane"},
    {"caption": "a380", "correct_tag": "airplane"},
]

# 相似度匹配函数，用于模糊匹配描述
def is_similar_caption(caption1, caption2):
    """检查两个描述是否足够相似"""
    # 转换为小写并去除多余空格
    cap1 = caption1.lower().strip()
    cap2 = caption2.lower().strip()
    
    # 完全匹配
    if cap1 == cap2:
        return True
    
    # 部分匹配（一个包含另一个）
    if cap1 in cap2 or cap2 in cap1:
        return True
    
    # 关键词匹配
    keywords1 = set(cap1.split())
    keywords2 = set(cap2.split())
    common_words = keywords1.intersection(keywords2)
    
    # 如果有足够多的共同关键词，认为是相似的
    similarity = len(common_words) / max(len(keywords1), len(keywords2))
    return similarity > 0.7  # 设定相似度阈值

def fix_metadata_tags(metadata_file):
    """修正元数据文件中的标签"""
    # 检查文件是否存在
    if not os.path.exists(metadata_file):
        print(f"错误: 元数据文件不存在: {metadata_file}")
        return False
    
    # 读取元数据文件
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"成功读取元数据文件: {metadata_file}")
        print(f"元数据项数量: {len(metadata)}")
    except Exception as e:
        print(f"读取元数据文件时出错: {e}")
        return False
    
    # 创建备份
    backup_file = f"{metadata_file}.bak.{int(time.time())}"
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"已创建元数据备份: {backup_file}")
    except Exception as e:
        print(f"创建备份时出错: {e}")
        return False
    
    # 记录修改
    changes_made = 0
    changes_details = []
    already_correct = 0
    
    # 遍历元数据
    for item in metadata:
        caption = item.get("caption", "")
        current_tags = item.get("tags", [])
        
        # 如果当前标签已经是字符串，转换为列表
        if isinstance(current_tags, str):
            current_tags = [current_tags]
        
        # 检查是否需要修正
        for correction in CORRECTIONS:
            if is_similar_caption(caption, correction["caption"]):
                correct_tag = correction["correct_tag"]
                
                # 检查是否需要修改（标签不是只有一个airplane）
                if current_tags != [correct_tag]:
                    old_tags = current_tags.copy()
                    # 修改标签为唯一的airplane
                    item["tags"] = [correct_tag]
                    changes_made += 1
                    changes_details.append({
                        "caption": caption,
                        "old_tags": old_tags,
                        "new_tags": [correct_tag]
                    })
                    print(f"已修改: '{caption}'")
                    print(f"  原标签: {old_tags}")
                    print(f"  新标签: {[correct_tag]}")
                else:
                    already_correct += 1
                    print(f"已正确标记: '{caption}'")
                    print(f"  当前标签: {current_tags}")
                break
    
    # 如果有修改，保存修改后的元数据
    if changes_made > 0:
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"\n修改总结:")
            print(f"- 元数据总项数: {len(metadata)}")
            print(f"- 修改项数: {changes_made}")
            print(f"- 已正确标记项数: {already_correct}")
            print(f"- 修改已保存到: {metadata_file}")
            
            # 保存变更记录
            changes_log = f"metadata_changes_{int(time.time())}.log"
            with open(changes_log, 'w', encoding='utf-8') as f:
                for change in changes_details:
                    f.write(f"描述: {change['caption']}\n")
                    f.write(f"原标签: {change['old_tags']}\n")
                    f.write(f"新标签: {change['new_tags']}\n")
                    f.write("-" * 50 + "\n")
            print(f"- 详细变更记录已保存到: {changes_log}")
            
            return True
        except Exception as e:
            print(f"保存修改后的元数据时出错: {e}")
            print(f"原始元数据已备份到: {backup_file}")
            return False
    else:
        if already_correct > 0:
            print(f"没有需要修改的项目，{already_correct}个项目已经正确标记")
        else:
            print("没有找到匹配的项目需要修改")
        return True

def main():
    # 元数据文件路径
    metadata_files = [
        "metadata/images.json",
        "project/src/data/images.json",
        "api/data/images.json"
    ]
    
    for file_path in metadata_files:
        if os.path.exists(file_path):
            print(f"\n处理元数据文件: {file_path}")
            success = fix_metadata_tags(file_path)
            if success:
                print(f"成功处理元数据文件: {file_path}")
            else:
                print(f"处理元数据文件失败: {file_path}")
        else:
            print(f"元数据文件不存在，跳过: {file_path}")

if __name__ == "__main__":
    main() 