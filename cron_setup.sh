#!/bin/bash

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 创建临时crontab文件
TEMP_CRONTAB=$(mktemp)

# 导出当前的crontab配置
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# 新建crontab配置" > "$TEMP_CRONTAB"

# 检查是否已经有相同的cron任务
if ! grep -q "unsplash_keywords_downloader.py" "$TEMP_CRONTAB"; then
    # 添加新的cron任务，模拟每1小时15分钟（75分钟）执行一次
    echo "# 下载Unsplash图片，每次50张，每个关键词总共200张" >> "$TEMP_CRONTAB"
    # 这个设置将在以下时间点执行：0:00, 1:15, 2:30, 3:45, 5:00, 6:15等，近似每75分钟一次
    echo "0 0,3,6,9,12,15,18,21 * * * cd ${SCRIPT_DIR} && python3 unsplash_keywords_downloader.py >> unsplash_cron.log 2>&1" >> "$TEMP_CRONTAB"
    echo "15 1,4,7,10,13,16,19,22 * * * cd ${SCRIPT_DIR} && python3 unsplash_keywords_downloader.py >> unsplash_cron.log 2>&1" >> "$TEMP_CRONTAB"
    echo "30 2,5,8,11,14,17,20,23 * * * cd ${SCRIPT_DIR} && python3 unsplash_keywords_downloader.py >> unsplash_cron.log 2>&1" >> "$TEMP_CRONTAB"
    
    # 应用新的crontab配置
    crontab "$TEMP_CRONTAB"
    echo "已成功设置cron任务，将近似每1小时15分钟执行一次图片下载"
else
    echo "cron任务已存在，无需重复添加"
fi

# 清理临时文件
rm "$TEMP_CRONTAB"

echo "----------"
echo "查看当前cron任务："
crontab -l | grep -v "^#"
echo "----------"
echo "可以通过以下命令手动运行脚本："
echo "python3 ${SCRIPT_DIR}/unsplash_keywords_downloader.py"
echo "----------"
echo "每次运行将：" 
echo "1. 下载当前关键词的50张图片"
echo "2. 每个关键词总共下载200张图片"
echo "3. 自动保存状态，下次继续从上次的位置继续下载" 
echo "4. 可以设置超时时间：--timeout 秒数" 