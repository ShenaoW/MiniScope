from fastNLP.io import Loader
from fastNLP import DataSet, Instance
from fastNLP import Vocabulary
from fastNLP import cache_results
from fastNLP.io import DataBundle
from fastNLP.transformers.torch import BertTokenizer
from fastNLP import Vocabulary
import re
import pickle
import config
class raw_loader(Loader):
    def _load(self, path: str) -> DataSet:
        ds = DataSet()
        with open(path, 'r', encoding='utf-8') as f:
            para = f.read()
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
        
        return ds
    
class eval_loader(Loader):
    def _load(self, path: str) -> DataSet:
        ds = DataSet()
        with open(path, 'r', encoding='utf-8') as f:
            segments = []
            for line in f:
                line = line.strip().split()
                if len(line) == 0: #空行代表一个句子的结束
                    if len(segments) != 0:
                        raw_words =  [s[0] for s in segments]
                        # 将一个 sample 插入到 DataSet中
                        ds.append(Instance(raw_words=raw_words))
                    segments = []
                else:
                    segments.append([line[0]])
        return ds
class ppLoader(Loader):
    def _load(self, path: str) -> DataSet:
        ds = DataSet()
        with open(path, 'r', encoding='utf-8') as f:
            segments = []
            for line in f:
                line = line.strip().split()
                if len(line) == 0: #空行代表一个句子的结束
                    if len(segments) != 0:
                        raw_words =  [s[0] for s in segments]
                        raw_targets = [s[1] for s in segments]
                        # 将一个 sample 插入到 DataSet中
                        # if len(set(raw_targets)) != 1:
                        ds.append(Instance(raw_words=raw_words,raw_targets=raw_targets))
                    segments = []
                else:
                    assert len(line) == 2
                    segments.append([line[0], line[1]])
        return ds

class classifyLoader(Loader):
    def _load(self, path: str) -> DataSet:
        ds = DataSet()
        with open(path, 'r', encoding='utf-8') as f:
            segments = []
            for line in f:
                line = line.strip().split()
                if len(line) == 0: #空行代表一个句子的结束
                    if len(segments) != 0:
                        raw_words =  [s[0] for s in segments]
                        raw_targets = [s[1] for s in segments]
                        # 将一个 sample 插入到 DataSet中
                        ds.append(Instance(raw_words=raw_words,raw_targets=raw_targets))
                    segments = []
                else:
                    assert len(line) == 2
                    segments.append([line[0], line[1]])
        return ds



@cache_results("cache/databundle_withvocabs.pkl")
def make_vocabulary(data_bundle, unk):
    if unk:
        words = Vocabulary()
        tags = Vocabulary(unknown=None)
    else:
        words = Vocabulary(padding=None,unknown=None)
        tags = Vocabulary(unknown=None,padding=None)

    words = words.from_dataset(data_bundle.get_dataset('train'), field_name='raw_words', no_create_entry_dataset=[data_bundle.get_dataset('dev'), data_bundle.get_dataset('test')])
    words.index_dataset(data_bundle.datasets.values(), field_name='raw_words', new_field_name='words')

    tags = tags.from_dataset(data_bundle.get_dataset('train'), field_name='raw_targets', no_create_entry_dataset=[data_bundle.get_dataset('dev'), data_bundle.get_dataset('test')])
    tags.index_dataset(data_bundle.datasets.values(), field_name='raw_targets', new_field_name='target')

    data_bundle.set_vocab(words, 'words')
    data_bundle.set_vocab(tags, 'target')
    return data_bundle

@cache_results("cache/bilstm_process.pkl")
def bilstm_process(data_bundle:DataBundle):
    data_bundle.apply_field(lambda x: len(x), field_name='raw_words', new_field_name='seq_len')
    return data_bundle

def check_length(data_bundle, length):
    data_bundle.apply_field(lambda x: x if len(x) < length else x[:length], field_name='raw_words', new_field_name='raw_words')
    data_bundle.apply_field(lambda x: x if len(x) < length else x[:length], field_name='raw_targets', new_field_name='raw_targets')
    return data_bundle




@cache_results("cache/bert_process.pkl")
def bert_process(data_bundle, model_name):

    data_bundle = check_length(data_bundle, 500)
    tokenizer = BertTokenizer.from_pretrained(model_name)
    def bpe(raw_words):
        bpes = [tokenizer.cls_token_id]
        first = [0]
        first_index = 1  # 记录第一个bpe的位置
        for word in raw_words:
            bpe = tokenizer.encode(word, add_special_tokens=False)
            bpes.extend(bpe)
            first.append(first_index)
            first_index += len(bpe)
        bpes.append(tokenizer.sep_token_id)
        first.append(first_index)
        return {'input_ids': bpes, 'input_len': len(bpes), 'first': first, 'seq_len': len(raw_words)}
    # 对data_bundle中每个dataset的每一条数据中的raw_words使用bpe函数，并且将返回的结果加入到每条数据中。
    data_bundle.apply_field_more(bpe, field_name='raw_words')

    # tag的词表，由于这是词表，所以不需要有padding和unk
    tag_vocab = Vocabulary(padding=None, unknown=None)
    # 从 train 数据的 raw_target 中获取建立词表
    tag_vocab.from_dataset(data_bundle.get_dataset('train'), field_name='raw_targets')
    # 使用词表将每个 dataset 中的raw_target转为数字，并且将写入到target这个field中
    tag_vocab.index_dataset(data_bundle.datasets.values(), field_name='raw_targets', new_field_name='target')

    # 可以将 vocabulary 绑定到 data_bundle 上，方便之后使用。
    data_bundle.set_vocab(tag_vocab, field_name='target')

    return data_bundle, tokenizer



@cache_results("cache/bert_cls_process.pkl")
def bert_process_cls(data_bundle, model_name):

    data_bundle = check_length(data_bundle, 500)
    tokenizer = BertTokenizer.from_pretrained(model_name)

    def bpe(raw_words):
        bpes = [tokenizer.cls_token_id]
        first = [0]
        first_index = 1  # 记录第一个bpe的位置
        for word in raw_words:
            bpe = tokenizer.encode(word, add_special_tokens=False)
            bpes.extend(bpe)
            first.append(first_index)
            first_index += len(bpe)
        bpes.append(tokenizer.sep_token_id)
        first.append(first_index)
        return {'input_ids': bpes, 'input_len': len(bpes), 'first': first, 'seq_len': len(raw_words)}
    # 对data_bundle中每个dataset的每一条数据中的raw_words使用bpe函数，并且将返回的结果加入到每条数据中。
    data_bundle.apply_field_more(bpe, field_name='raw_words')


    return data_bundle, tokenizer

# @cache_results("cache/bert_use_process.pkl")
def bert_process_use(data_bundle):

    data_bundle = check_length(data_bundle, 500)
    tokenizer = pickle.load(open(config.MODEL_PATH + 'bert_tokenizer.pkl', 'rb'))

    def bpe(raw_words):
        bpes = [tokenizer.cls_token_id]
        first = [0]
        first_index = 1  # 记录第一个bpe的位置
        for word in raw_words:
            bpe = tokenizer.encode(word, add_special_tokens=False)
            bpes.extend(bpe)
            first.append(first_index)
            first_index += len(bpe)
        bpes.append(tokenizer.sep_token_id)
        first.append(first_index)
        return {'input_ids': bpes, 'input_len': len(bpes), 'first': first, 'seq_len': len(raw_words)}
    # 对data_bundle中每个dataset的每一条数据中的raw_words使用bpe函数，并且将返回的结果加入到每条数据中。
    data_bundle.apply_field_more(bpe, field_name='raw_words')
    tag_vocab = pickle.load(open(config.MODEL_PATH + 'bert_target.pkl', 'rb'))

    return data_bundle, tokenizer, tag_vocab