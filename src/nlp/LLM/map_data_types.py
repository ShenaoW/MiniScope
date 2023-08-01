import csv
import os
import json

data_mapping = {"照片或视频信息":"选中的照片或视频信息", "文件":"选中的文件", '发布内容':'', '邮箱':'', '设备信息':'', '订单信息':'', '所关注的账号':'', '剪切板':'', '身份证号码':''}
verb_mapping = {'获取、收集':'收集', '获取、访问': '访问', '获取、使用':'使用'}
id_name_mapping = {}

id_name_mapping_path = './appid_nickname_mapping.json'
f_mapping = open(id_name_mapping_path, 'w', encoding='utf-8', errors='ignore')

samples_dir_path = './privacy_policy_s1/privacy_policy_s1/'
files = os.listdir(samples_dir_path)
for file in files:
    file_path = samples_dir_path + file
    f = open(file_path, 'r', encoding='utf-8', errors='ignore')
    content = json.load(f)
    id = content['appid']
    name = content['app_nickname']
    id_name_mapping[id] = name
    f.close()
f_mapping.write(json.dumps(id_name_mapping))
f_mapping.close()

result_path = './mini_privacy_detial_result.csv'
f_result = open(result_path, 'r', encoding='utf-8', errors='ignore')
records = list(csv.reader(f_result, delimiter=','))

final_result_path = './miniapps_privacy_detial_final_results.csv'
f_final = open(final_result_path, 'w', encoding='utf-8', errors='ignore', newline='')
writer = csv.writer(f_final, delimiter=',')
writer.writerow(['app_id', 'app_nickname', 'DC', 'SSoC', 'DE'])

for index, record in enumerate(records):
    if index == 0:
        continue
    appid = record[0]
    nickname = id_name_mapping[appid]
    dc = record[1]
    ssoc = record[2]
    de = record[3]
    if ssoc in verb_mapping:
        ssoc = verb_mapping[ssoc]
    if de in data_mapping:
        de = data_mapping[de]
    if de == '':
        continue
    writer.writerow([appid, nickname, dc, ssoc, de])

f_final.close()