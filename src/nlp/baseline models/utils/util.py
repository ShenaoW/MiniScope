import pickle
import torch
import torch.nn.functional as F
import torch.nn as nn
from torch.nn.utils.rnn import pad_packed_sequence, pack_padded_sequence





def save_model(model, file_name):
    with open(file_name, 'wb') as f:
        pickle.dump(model, f)

def load_model(file_name):
    with open(file_name, 'rb') as f:
        model = pickle.load(f)
    return model

def flatten_lists(lists):
    flatten_list = []
    for l in lists:
        flatten_list.extend([i.split('-')[-1] for i in l])
        # flatten_list.extend(l)
    return flatten_list

def word2features(sent, i):
    """抽取单个字的特征"""
    word = sent[i]
    prev_word = "<s>" if i == 0 else sent[i-1]
    next_word = "</s>" if i == (len(sent)-1) else sent[i+1]
    # 使用的特征：
    # 前一个词，当前词，后一个词，
    # 前一个词+当前词， 当前词+后一个词
    features = {
        'w': word,
        'w-1': prev_word,
        'w+1': next_word,
        'w-1:w': prev_word+word,
        'w:w+1': word+next_word,
        'bias': 1
    }
    return features

def sent2features(sent):
    """抽取序列特征"""
    return [word2features(sent, i) for i in range(len(sent))]


class results():
    result = []
    words = []
    label = []

    def app(self, output):
        self.result.extend(output)
    
    def app_words(self, labell):
        self.label.extend(labell)
    
    def clear(self):
        del self.result[:]
        del self.words[:]
        del self.label[:]

def todict(text,label):
    dict={}
    dict["text"]=text
    dict["label"]={}

    label = list(zip(label, range(len(label))))
    label = [i for i in label if i[0] != 'O' ]

    print(label)
    
    for item in label:
        str = item[0].split('-')
        index = item[1]
        if dict["label"].get(str[1], None) is None:
            dict["label"][str[1]]=[]
        if str[0] == 'B':
            start = index 
        elif str[0] == 'E':
            dict["label"][str[1]].append([start,index])
    return dict