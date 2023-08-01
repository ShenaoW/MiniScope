import os
import config
import json
import re
import requests
from fastNLP import DataSet, Instance
from fastNLP.io import DataBundle
from utils.data import bert_process_use
from utils.util import *
import json
from fastNLP import prepare_torch_dataloader, Evaluator
from fastNLP.transformers.torch import BertModel
from fastNLP import seq_len_to_mask

class BertTextClassifier(nn.Module):
    def __init__(self, model_name):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.3)
        self.linear1 = nn.Linear(self.bert.config.hidden_size, self.bert.config.hidden_size//2)
        self.linear2 = nn.Linear(self.bert.config.hidden_size//2, 1)
        self.sigmoid = nn.Sigmoid()
        self.loss_fn = nn.BCELoss()

    def forward(self, input_ids, input_len, first):
        attention_mask = seq_len_to_mask(input_len)
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        pred = self.linear1(pooled_output)
        pred = self.linear2(pred)
        pred = self.sigmoid(pred).squeeze(-1)
        return {'pred': pred}

    def train_step(self, input_ids, input_len, first, target):
        pred = self(input_ids, input_len, first)['pred']
        loss = self.loss_fn(pred, target.to(torch.float))
        return {'loss': loss}

    def evaluate_step(self, input_ids, input_len, first):
        pred = self(input_ids, input_len, first)['pred']
        pred = torch.where(pred > 0.5, torch.tensor([1.0]).to(pred.device), torch.tensor([0.0]).to(pred.device))
        return {'pred': pred}

class Args:
    def __init__(self, model=None) -> None:
        self.model = model
        self.batch_size = 32



class PrivacyPolicy():
    def __init__(self, appID = None, Policy = None) -> None:
        self.appID = appID
        self.raw_policy = Policy
        self.args = Args()
        self.analysize_policy()
        # self.raw_guideline = self.get_guideline()
        # self.analysize_guideline()

    def get_guideline(self):
        crawler = pp_crawler()
        return crawler.crawl(self.appID)

    def analysize_guideline(self):
        self.guideline = []
        for desc in self.raw_guideline['privacy_detail_list']['item']:
            tmp = dict()
            tmp['Purpose'] = self.get_purpose(desc)
            tmp['Data_controller'] = self.get_datacontroller(desc)
            tmp['Collection'] = self.get_collection(desc)
            tmp['Data_entity'] = self.get_dataentity(desc)
            tmp['Data_receiver'] = self.raw_guideline['name']
            tmp['Condition'] = self.get_condition(desc)
            tmp['Sharing'] = self.get_sharing(tmp['Data_entity'])
            self.guideline.append(tmp)


    def classify_policy(self, data_bundle, tokenizer):
        classify_model = load_model(config.MODEL_PATH + 'bert_cls.pkl')

        def new_evaluate_step(self, input_ids, input_len, first):
            pred = self(input_ids, input_len, first)['pred']
            pred = torch.where(pred > 0.7, torch.tensor([1.0]).to(pred.device), torch.tensor([0.0]).to(pred.device))
            return {'pred': pred}
        from types import MethodType

        classify_model.evaluate_step = MethodType(new_evaluate_step, classify_model)

        print(data_bundle)
        test_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('test'), batch_size=self.args.batch_size)
        test_dataloader.set_pad('input_ids', pad_val=tokenizer.pad_token_id)

        def output_labeling(evaluator, batch):
            predd = results()
            outputs = evaluator.evaluate_step(batch)["pred"]
            predd.label.extend(outputs.cpu().numpy().tolist())
            del predd

        evaluator = Evaluator(model=classify_model, dataloaders=test_dataloader,
                        device=0, evaluate_batch_step_fn=output_labeling)
        
        evaluator.run()

        predd = results()
        for i in range(len(predd.label)-1,-1,-1):
            if predd.label[i] == 0:
                data_bundle.get_dataset('test').delete_instance(i)
        # print(data_bundle.get_dataset('test'))
        return data_bundle


    def analysize_policy(self, model = 'bert'):
        self.policy = []
        self.args.model = model

        data_bundle = self.process_policy()
        # print(data_bundle.get_dataset('test'))
        # 加载词表
        data_bundle, tokenizer, tag_vocab = bert_process_use(data_bundle)
        # print(data_bundle.get_dataset('test'))
        pred = results()
        pred.clear()

        data_bundle = self.classify_policy(data_bundle, tokenizer)

        pred_tag_lists = []

        model_path = config.MODEL_PATH + model + '_no_allO.pkl'
        model = load_model(model_path)
        
        if self.args.model == 'bert':
            print("自动分析中...")
            from model.bert import bert_test
            
            bert_test(model, data_bundle, tokenizer, self.args)

            pred_tag_lists = []
            words_list = []

            for seq in pred.result:
                pred_tag_list = [tag_vocab.idx2word[idx] for idx in seq]
                pred_tag_lists.append(pred_tag_list)
            
            for seq in pred.words:
                words_list.append(''.join(seq))

        elif self.args.model == 'bert_bilstm_crf':
            print("自动分析中...")
            from model.bert import bert_test
            data_bundle, tokenizer, tag_vocab = bert_process_use(data_bundle, 'bert-base-chinese')
            pred = results()
            bert_test(model, data_bundle, self.args)

            pred_tag_lists = []
            words_list = []

            for seq in pred.result:
                pred_tag_list = [tag_vocab.idx2word[idx] for idx in seq]
                pred_tag_lists.append(pred_tag_list)
            
            for seq in pred.words:
                words_list.append(''.join(seq))

        for i in zip(words_list, pred_tag_lists):
            if len(set(i[1]))>1: 
                self.policy.append(self.get_tuple(i[0], i[1]))


    def get_tuple(self, text, label):
        label = list(zip(label, range(len(label))))
        label = [i for i in label if i[0] != 'O' ]
        start = None
        tmp = dict()
        tmp['text'] = text

        for item in label:
            str = item[0].split('-')
            index = item[1]
            if tmp.get(str[1], None) is None:
                tmp[str[1]] = []
            if str[0] == 'B':
                start = index 
            elif str[0] == 'E':
                if start is None:
                    tmp[str[1]].append(text[index])
                else:
                    tmp[str[1]].append(text[start:index+1])
            elif str[0] == 'S':
                tmp[str[1]].append(text[index])
        return tmp 

    def process_policy(self):
        ds = DataSet()
        '''隐私政策分句'''
        def cut_sentz(para):
            para = re.sub('([。。！？\?])([^”’])', r"\1zkf\2", para)  # 单字符断句符
            para = re.sub('(\.{6})([^”’])', r"\1zkf\2", para)  # 英文省略号
            para = re.sub('(\…{2})([^”’])', r"\1zkf\2", para)  # 中文省略号
            para = re.sub('([。。！？\?][”’])([^，。。！？\?])', r'\1zkf\2', para)
            # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
            para = para.rstrip()  # 段尾如果有多余的\n就去掉它
            # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
            # while "\n\n" in para:
            #     para = para.replace("\n\n", "\n")
            return para.split("zkf")
        
        sentences = cut_sentz(self.raw_policy)
        sentences = [x.strip() for x in sentences]      
        
        for line in sentences:
            line = list(line)
            if len(line) == 0:
                continue
            else:
                ds.append(Instance(raw_words=line))
        res = DataBundle().set_dataset(ds, name='test')
        return res


    def get_purpose(self, sentence):
        if '为了' in sentence:
            return sentence.split('为了')[1].split('，')[0]
        elif '用于' in sentence:
            return sentence.split('用于')[1].split('，')[0]
    
    def get_datacontroller(self, sentence):
        if '为了' in sentence:
            return sentence.split('，')[1][:3]
        elif '用于' in sentence:
            return sentence.split('，')[0][:3]
        
    def get_collection(self, sentence):
        if '收集' in sentence:
            return ['收集']
        elif '使用' in sentence:
            return ['使用']
        elif '访问' in sentence:
            return ['访问']
        elif '获取' in sentence:
            return ['获取']
        
    def get_dataentity( sentence):
        if '收集你的' in sentence:
            if '为了' in sentence:
                return sentence.split('收集你的')[1].split('、')
            elif '用于' in sentence:
                return sentence.split('收集你的')[1].split('，')[0].split('、')
        elif '收集你选中的' in sentence:
            return sentence.split('收集你选中的')[1].split('，')[0].split('或')
        elif '获取你选择的' in sentence:
            return sentence.split('获取你选择的')[1].split('，')[0].split('或')
        elif '使用你的' in sentence:
            return sentence.split('使用你的')[1].split('，')[0].split('、')
        elif '访问你的' in sentence:
            return sentence.split('访问你的')[1].split('，')[0].split('、')
    
    def get_condition(self, sentence):
        if '开发者将在获取你的明示同意后':
            return ['开发者将在获取你的明示同意后']
    
    def get_sharing(self, data_entity):
        for i in data_entity:
            for j in self.raw_guideline['plugin_privacy_info_list']['item']:
                for k in j['privacy_wording_list']:
                    if i in k:
                        return [self.raw_guideline['plugin_privacy_info_list']['item']['plugin_biz_name']]
    

    def do_mapping(self):
        vocabs_operation = json.loads(open('vocabulary_dataoperation.json', 'r', encoding='utf-8').read())
        vocabs_datatype = json.loads(open('vocabulary_datatype.json', 'r', encoding='utf-8').read())

        for i in self.guideline:
            if not i['Collection'] is None:
                i['Operation_type'] = []
                for j in i['Collection']:
                    if j in vocabs_operation[0]['words']:
                        i['Operation_type'].append('收集')
                    elif j in vocabs_operation[1]['words']:
                        i['Operation_type'].append('使用')
                    elif j in vocabs_operation[2]['words']:
                        i['Operation_type'].append('传输')

            if not i['Data_entity'] is None:
                i['ontology'] = []
                for j in i['Data_entity']:
                    for k in vocabs_datatype:
                        for z in k['value']:
                            if j in z['words_set']:
                                i['ontology'].append(k['key'])
                                
        for i in self.policy:
            if not i['Collection'] is None:
                i['Operation_type'] = []
                for j in i['Collection']:
                    if j in vocabs_operation[0]['words']:
                        i['Operation_type'].append('收集')
                    elif j in vocabs_operation[1]['words']:
                        i['Operation_type'].append('使用')
                    elif j in vocabs_operation[2]['words']:
                        i['Operation_type'].append('传输')

            if not i['Data_entity'] is None:
                i['ontology'] = []
                for j in i['Data_entity']:
                    for k in vocabs_datatype:
                        for z in k['value']:
                            if j in z['words_set']:
                                i['ontology'].append(k['key'])
        
    def do_compare(self):
        for i in self.policy:
            i['compare'] = False
            for j in self.guideline:
                if i in j['ontology']:
                    i['compare'] = True
                    break
        
        for i in self.policy:
            if i['compare'] == False:
                print(i)



class pp_crawler(object):
    def __init__(self):
        self.cookie = {'wap_sid2': config.WAP_SID2}
        self.header = config.HEADER
        self.uin = config.UIN
        self.key = config.KEY

    def js2json(self, data_str):
        def json_replace(match):
            # 获取属性名和属性值
            name = match.group(1)
            value = match.group(2)

            # 将属性名使用双引号包裹起来
            name = '"' + name + '"'

            # 将属性值使用双引号或单引号包裹，但不要使用反斜杠转义引号
            if value.startswith("'") and value[:-1].endswith("'"):
                value = '"' + value[1:-2].replace('"', '\\"') + '"' +','
            if value == ',':
                value = '"",'
            return name + ': ' + value
        # 移除注释和多余的字符
        data_str = re.sub(r'[\s]*//\s+[^\n\r]*[\n\r]+', '\n', data_str)
        data_str = re.sub(r'\.item[^,}]*', '', data_str)
        data_str = re.sub(r'\.list[^,}]*', '', data_str)
        data_str = re.sub(r';\s*$', '', data_str)
        data_str = re.sub(r'\,[\r\n\s]*}', '\n}', data_str)
        # print(data_str)
        # 匹配属性名和属性值，并将属性名用双引号包裹，属性值用单引号或双引号包裹
        pattern = re.compile(r'([^\s:]+)\s*:\s*([^\n\r]+)')

        json_str = pattern.sub(json_replace, data_str)
        # 将字符串转换为JSON对象
        # print(json_str)
        json_obj = json.loads(json_str)
        # print(json_obj)
        return json_obj

    def crawl(self, appid):
        start = 'window.cgiData'
        end = 'window.cgiData.app_nickname'
        params = {'action': 'show'}
        params['appid'] = appid
        params['uin'] = self.uin
        params['key'] = self.key

        #构造url
        url = 'http://mp.weixin.qq.com/wxawap/waprivacyinfo'

        r = requests.get(url, params=params, headers=self.header, cookies=self.cookie)
        # print(r.text)
        if r.status_code == 200:
            index_start = r.text.index(start) + len(start) + 3 # +3是为了去掉等号
            index_end = r.text.index(end)
            privacy = r.text[index_start:index_end]
            if not os.path.exists(config.SAVE_PATH):
                os.makedirs(config.SAVE_PATH)
            with open(file=config.SAVE_PATH + appid + '.json', mode='w', encoding='utf-8') as f:
                privacy_json = self.js2json(privacy)
                json.dump(privacy_json,f,ensure_ascii=False,indent=4)

        return privacy_json
    
def get_all_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list

if __name__ == '__main__':
    import json
    file_list = get_all_files(config.POLICY_PATH)
    for file in file_list:
        with open(file, 'r', encoding='utf-8') as f:
            print(file, 'is processing')
            text = f.read()    
            test = PrivacyPolicy(Policy=text)
            json.dump(test.policy, open(config.SAVE_PATH + file[:-4] + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)