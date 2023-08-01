import pickle
from model.bert import BertNER
import torch

target = pickle.load(open('ckpts/bert_target.pkl', 'rb'))

model = BertNER('bert-base-chinese', len(target))
model_path = 'ckpts/bert_no_allO.pkl'
model.load_state_dict(torch.load(model_path,map_location={'cuda:1': 'cuda:0'}))  #将对应的gpu编号映射到正确的gpu上
