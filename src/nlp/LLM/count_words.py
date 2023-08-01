import re
import csv
TOTAL_FILE_NUMBER = 10

subject_list = []
verb_list = []
data_type_list = []

output_path = './mini_privacy_detial_result.csv'
f_output = open(output_path, 'w', encoding='utf-8', errors='ignore', newline='')
writer = csv.writer(f_output, delimiter=',')
writer.writerow(['appid', 'DC', 'SSoC', 'DE'])

stat_path = './sample_miniapps_stat.csv'
f_stat = open(stat_path, 'r')
stat = list(csv.reader(f_stat, delimiter=','))
pos_dict = {}
pre_file_num = 0
for idx, record in enumerate(stat):
    if idx == 0:
        continue
    curr_file_num = int(record[0])
    if curr_file_num != pre_file_num:
        count = 0
    appid = record[1]
    privacy_detail_num = int(record[2])
    for i in range(count, count+privacy_detail_num):
        if curr_file_num not in pos_dict:
            pos_dict[curr_file_num] = {}
        pos_dict[curr_file_num][i] = appid            
    count += privacy_detail_num
    pre_file_num = curr_file_num

#print(pos_dict)

files_path = './sampled_response_files/'
for i in range(TOTAL_FILE_NUMBER):
    file_path = files_path + 'response_file_' + str(i+1) + '.txt'
    f = open(file_path, 'r', encoding='utf-8', errors='ignore')
    content = f.readlines()
    print(file_path)
    for index, line in enumerate(content):
        if index < 3:
            continue
        #print(index)
        chunks = re.split(',| |"', line.strip())
        chunks = list(filter(None, chunks))
        if len(chunks) != 4:
            print("Wronng record!!!")
            continue
        privacy_detail = chunks[0]
        subject = chunks[1]
        verb = chunks[2]
        data_type = chunks[3]
        subject_list.append(subject)
        verb_list.append(verb)
        data_type_list.append(data_type)
        appid = pos_dict[i+1][index-3]
        writer.writerow([appid, subject, verb, data_type])

subject_list = list(set(subject_list))
verb_list = list(set(verb_list))
data_type_list = list(set(data_type_list))        
print(subject_list, len(subject_list))
print(verb_list, len(verb_list))
print(data_type_list, len(data_type_list))
