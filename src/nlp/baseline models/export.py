from utils.data import raw_loader, bert_process
from pickle import load
from model.bilstm import bilstm_process
from utils.util import *
from pathlib import Path


class Args:
    def __init__(self, data_path, model, output_path) -> None:
        self.data_path = data_path
        self.model = model
        self.output_path = output_path
        self.batch_size = 32


class NLPAnalyze:
    def __init__(self, data_path, model, output_path) -> None:
        self.args = Args(data_path, model, output_path)
        self.eval()         


    def eval(self):
        model_path = Path(__file__).parent / "ckpts"
        data_bundle = raw_loader().load(self.args.data_path)
        # 构建词表
        # print(data_bundle)
        data_bundle.set_dataset(data_bundle.get_dataset('train'), 'test')
        data_bundle.delete_dataset('train')

        if self.args.model in ['hmm', 'crf']:
            target = load(open('ckpts/hmm_target.pkl', 'rb'))
            words = load(open('ckpts/hmm_words.pkl', 'rb'))
        else:
            target = load(open('ckpts/bilstm_target.pkl', 'rb'))
            words = load(open('ckpts/bilstm_words.pkl', 'rb'))

        data_bundle.set_vocab(target, 'target')
        data_bundle.set_vocab(words, 'words')

        words.index_dataset(data_bundle.get_dataset('test'), field_name='raw_words', new_field_name='words')

        pred_tag_lists = []


        model_path = str(model_path) + '/' + self.args.model + '.pkl'
        model = load_model(model_path)

        if self.args.model == 'hmm':
            print("评估模型中...")
            pred_tag_lists = model.test(data_bundle)

        elif self.args.model == 'crf':
            print("评估模型中...")
            pred_tag_lists = model.test(dataset=data_bundle.get_dataset('test'))

        elif self.args.model == 'bilstm':
            print("评估模型中...")
            from model.bilstm import bilstm_test

            data_bundle = bilstm_process(data_bundle)
            # data_bundle.delete_field('raw_words')
            # data_bundle.delete_field('raw_targets')
            pred = results()
            bilstm_test(model, data_bundle, self.args)

            pred_tag_lists = []
            words_list = []

            for seq in pred.result:
                pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq]
                pred_tag_lists.append(pred_tag_list)
            
            for seq in pred.words:
                words_list.append(seq)

        elif self.args.model == 'bilstm_crf':
            print("评估模型中...")
            from model.bilstm_crf import bilstm_crf_test
            data_bundle = bilstm_process(data_bundle)
            # data_bundle.delete_field('raw_words')
            # data_bundle.delete_field('raw_targets')
            pred = results()
            bilstm_crf_test(model, data_bundle, self.args)

            pred_tag_lists = []
            words_list = []

            for seq in pred.result:
                pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq]
                pred_tag_lists.append(pred_tag_list)
            
            for seq in pred.words:
                words_list.append(seq)

        elif self.args.model == 'bert':
            print("评估模型中...")
            from model.bert import bert_test
            data_bundle, tokenizer = bert_process(data_bundle, 'bert-base-chinese')
            # data_bundle.delete_field('raw_words')
            # data_bundle.delete_field('raw_targets')
            pred = results()
            bert_test(model, data_bundle, self.args)

            pred_tag_lists = []
            words_list = []

            for seq in pred.result:
                pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq]
                pred_tag_lists.append(pred_tag_list)
            
            for seq in pred.words:
                words_list.append(seq)

        for i in zip(words_list, pred_tag_lists):
            print(i[0])
            print(i[1])
            print()


        output_path = self.args.output_path + self.args.model + '.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            for i in zip(words_list, pred_tag_lists):
                f.write(''.join(i[0]) + '\n')
                f.write(str(i[1]) + '\n')
                f.write('\n')

        print("预测结果已保存到", output_path)
        return pred_tag_lists
