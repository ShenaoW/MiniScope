import json
import os
import csv

#MAX_ROW = 50
#SAMPLE_NUMBER = 100

QUESTION_PART = 'Here is a table where each row has 4 items. The first item is "privacy detail", and the second to fourth items are "subject", "verb", "object" for the  "privacy detail" in the same row. Please read the table and complete the table by filling "subject", "verb", "object" in Chinese of each row:\n\
"privacy detail", "subject", "verb", "object"\n\
"为了帮助您成为我们的会员，开发者将在获取你的明示同意后，收集你的微信昵称、头像", "开发者", "收集", "微信昵称、头像"\n\
"开发者访问你的蓝牙，用于能过蓝牙接口进行设备识别", "开发者", "访问", "蓝牙"\n'
#print(QUESTION_PART)

sample_path = './sample_miniapps.csv'
f_sample = open(sample_path, 'r')
sample_ids = list(csv.reader(f_sample, delimiter=','))[1:]
f_sample.close()
sample_ids = [id[0] for id in sample_ids]
#print(sample_ids)

sample_stat = './sample_miniapps_stat.csv'
f_stat = open(sample_stat, 'w', newline='')
writer = csv.writer(f_stat, delimiter=',')
writer.writerow(['file', 'appid', 'privacy_detail_number'])

dir_path = './privacy_policy_s1/privacy_policy_s1/'#'./wechat_miniapp_privacy_policy/wechat_miniapp_privacy_policy/'
files = sorted(os.listdir(dir_path))
#num_row = 0
table_content = ''
file_num = 0
sample_num = 0
for file in files:
    f = open(dir_path+file, 'r', encoding='utf-8', errors='ignore')
    content = json.load(f)
    #print(content)
    try:
        privacy_detail_list = content['privacy_detail_list']['item']
    except:
        continue
    if len(privacy_detail_list) == 0:
        continue
    appid = content['appid']
    if appid in sample_ids:
        print('mapped!', appid)
        sample_num += 1
        for privacy_detail in privacy_detail_list:
            table_content += '"'+privacy_detail+'", "", "", ""\n'
        writer.writerow([file_num+1, appid, len(privacy_detail_list)])
        if sample_num%10 == 0:
            file_num += 1
            out_file = './sampled_question_files/question_file_'+str(file_num)+'.txt'
            print(QUESTION_PART+table_content)
            f_out = open(out_file, 'w', encoding='utf-8', errors='ignore', newline='')
            f_out.writelines(QUESTION_PART+table_content)
            f_out.close()
            table_content = ''

'''
    if num_row+len(privacy_detail_list) <= MAX_ROW:
        for privacy_detail in privacy_detail_list:
            table_content += '"'+privacy_detail+'", "", "", ""\n'
        num_row += len(privacy_detail_list)
    else:
        out_file = './question_files/question_file_'+str(file_num)+'.txt'
        print(QUESTION_PART+table_content)
        f_out = open(out_file, 'w', encoding='utf-8', errors='ignore', newline='')
        f_out.writelines(QUESTION_PART+table_content)
        f_out.close()
        file_num += 1
        table_content = ''
        for privacy_detail in privacy_detail_list:
            table_content += '"'+privacy_detail+'", "", "", ""\n'
        num_row = len(privacy_detail_list)
'''
