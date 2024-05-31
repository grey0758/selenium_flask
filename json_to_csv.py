import json
import csv
import os

data_dir = os.path.join(os.getcwd(), 'data')

# 定义 JSON 文件路径和输出 CSV 文件路径
json_file_path = os.path.join(data_dir, 'cached_response.json')
csv_file_path = os.path.join(data_dir, 'cached_response.csv')

# 确保文件路径存在
if not os.path.exists('data'):
    os.makedirs('data')

# 读取 JSON 文件
with open(json_file_path, 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# 筛选出包含完整数据的条目
filtered_data = [item for item in data if 'ProductTitle' in item]

# 检查数据是否为空
if not filtered_data:
    print("Filtered JSON data is empty.")
    exit()

# 获取字段名（假设所有记录都有相同的字段）
fieldnames = filtered_data[0].keys()

# 写入 CSV 文件
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered_data)
