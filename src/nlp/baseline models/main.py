from utils.data import ppLoader, make_vocabulary, bilstm_process, bert_process
from utils.params import params
from utils.util import save_model, load_model
from utils.evaluating import Metrics
from utils.util import results
from pickle import dump

# def analysis(databundle):
#     ddict = dict()
#     print('----------------------------')
#     print('train dataset')
#     print('----------------------------')
#     ddict['train'] = dict()
#     for i in databundle.get_dataset('train')['raw_targets']:
#         for j in i:
#             # if j != 'O':
#             #     j = j.split('-')[1]
#             if j not in ddict['train'].keys():
#                 ddict['train'][j] = 1
#             else:
#                 ddict['train'][j] += 1
        
#     print('----------------------------')
#     print('dev dataset')
#     print('----------------------------')
#     ddict['dev'] = dict()
#     for i in databundle.get_dataset('dev')['raw_targets']:
#         for j in i:
#             # if j != 'O':
#             #     j = j.split('-')[1]
#             if j not in ddict['dev'].keys():
#                 ddict['dev'][j] = 1
#             else:
#                 ddict['dev'][j] += 1
#     print('----------------------------')
#     print('test dataset')
#     print('----------------------------')
#     ddict['test'] = dict()
#     for i in databundle.get_dataset('test')['raw_targets']:
#         for j in i:
#             # if j != 'O':
#             #     j = j.split('-')[1]
#             if j not in ddict['test'].keys():
#                 ddict['test'][j] = 1
#             else:
#                 ddict['test'][j] += 1
#     print(ddict)
#     import pandas
#     df = pandas.DataFrame(ddict)
#     df.to_csv('analysis1.csv')

# def analysis_setz(databundle):
#     ddict = dict()
#     ddict['train'] = dict()
#     ddict['dev'] = dict()
#     ddict['test'] = dict()
#     ddict['train']['all_O'] = 0
#     ddict['dev']['all_O'] = 0
#     ddict['test']['all_O'] = 0
#     ddict['train']['no_O'] = 0
#     ddict['dev']['no_O'] = 0
#     ddict['test']['no_O'] = 0
#     for i in databundle.get_dataset('train')['raw_targets']:
#         if set(i) == set(['O']):
#             ddict['train']['all_O'] += 1
#         else:
#             ddict['train']['no_O'] += 1
#     for i in databundle.get_dataset('dev')['raw_targets']:
#         if set(i) == set(['O']):
#             ddict['dev']['all_O'] += 1
#         else:
#             ddict['dev']['no_O'] += 1
#     for i in databundle.get_dataset('test')['raw_targets']:
#         if set(i) == set(['O']):
#             ddict['test']['all_O'] += 1
#         else:
#             ddict['test']['no_O'] += 1
    
#     print(ddict)
#     import pandas
#     df = pandas.DataFrame(ddict)
#     df.to_csv('analysis2.csv')
        
def analysis_len(databundle):
    ddict = dict()
    ddict['len'] = 0
    ddict['num'] = 0
    for i in databundle.get_dataset('train')['raw_targets']:
        ddict['len'] += len(i)
        ddict['num'] += 1   
    for i in databundle.get_dataset('dev')['raw_targets']:
        ddict['len'] += len(i)
        ddict['num'] += 1   
    for i in databundle.get_dataset('test')['raw_targets']:
        ddict['len'] += len(i)
        ddict['num'] += 1   
    print(ddict)    
        

    

def train(args):
    # 读取数据，生成data_bundle
    print('args.data_path: ', args.data_path)
    data_bundle = ppLoader().load(args.data_path)
    print(data_bundle.get_dataset('train'))
    analysis_len(data_bundle)
    exit()
    # 构建词表
    if args.model in ['hmm', 'crf']:
        data_bundle = make_vocabulary(data_bundle, unk=False)
        dump(data_bundle.get_vocab('target'), open('ckpts/hmm_target.pkl', 'wb'))
        dump(data_bundle.get_vocab('words'), open('ckpts/hmm_words.pkl', 'wb'))
    elif args.model in ['bilstm', 'bilstm_crf']:
        data_bundle = make_vocabulary(data_bundle, unk=True)
        dump(data_bundle.get_vocab('target'), open('ckpts/bilstm_target.pkl', 'wb'))
        dump(data_bundle.get_vocab('words'), open('ckpts/bilstm_words.pkl', 'wb'))
    
    print('data_bundle: \n', data_bundle)
    print(data_bundle.get_dataset('train'))

    # 构建模型
    if args.model == 'hmm':
        from model.hmm import HMM
        print('构建HMM模型ing.....')
        model = HMM(len(data_bundle.get_vocab('target')), len(data_bundle.get_vocab('words')))
        model.train(dataset=data_bundle.get_dataset('train'))

    elif args.model == 'crf':
        from model.crf import CRFModel
        print('构建CRF模型ing.....')
        model = CRFModel()
        model.train(dataset=data_bundle.get_dataset('train'))
    
    elif args.model == 'bilstm':
        from model.bilstm import bilstm_train
        model = bilstm_train(data_bundle, args)
    
    elif args.model == 'bilstm_crf':
        from model.bilstm_crf import bilstm_crf_train
        model = bilstm_crf_train(data_bundle, args)

    elif args.model == 'bert':
        from model.bert import bert_train
        model = bert_train(data_bundle, args)
    
    elif args.model == 'bert_bilstm_crf':
        from model.bert_bilstm_crf import bert_bilstm_crf_train
        model = bert_bilstm_crf_train(data_bundle, args)

        
    model_path = args.model_path + args.model + '_no_allO.pkl'
    print(args.model,"模型训练完毕，模型已保存到", model_path)
    save_model(model, model_path)
    return model, data_bundle

def test(args, data_bundle, model):
    if not data_bundle:
        # 读取数据，生成data_bundle
        data_bundle = ppLoader().load(args.data_path)
        # 构建词表
        if args.model in ['hmm', 'crf']:
            data_bundle = make_vocabulary(data_bundle, unk=False)
        elif args.model in ['bilstm', 'bilstm_crf']:
            data_bundle = make_vocabulary(data_bundle, unk=True)

    if not model:
        model_path = args.model_path + args.model + '_no_allO.pkl'
        model = load_model(model_path)

    # 构建模型
    if args.model == 'hmm':
        print("评估模型中...")
        pred_tag_lists = model.test(data_bundle)

    elif args.model == 'crf':
        print("评估模型中...")
        pred_tag_lists = model.test(dataset=data_bundle.get_dataset('test'))
    
    elif args.model == 'bilstm':
        print("评估模型中...")
        from model.bilstm import bilstm_test
        
        data_bundle = bilstm_process(data_bundle)
        pred = results()
        bilstm_test(model, data_bundle, args)
        
        pred_tag_lists = []
        
        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq ]
            pred_tag_lists.append(pred_tag_list)
    
    elif args.model == 'bilstm_crf':
        print("评估模型中...")
        from model.bilstm_crf import bilstm_crf_test

        data_bundle = bilstm_process(data_bundle)
        pred = results()
        bilstm_crf_test(model, data_bundle, args)
        
        pred_tag_lists = []
        words_list = []

        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq]
            pred_tag_lists.append(pred_tag_list)
        
        for seq in pred.words:
            words_list.append(''.join(seq))

    elif args.model == 'bert':
        print("评估模型中...")
        from model.bert import bert_test
      
        pred = results()
        data_bundle = bert_test(model, data_bundle, args)
        
        pred_tag_lists = []
        
        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq ]
            pred_tag_lists.append(pred_tag_list)

    elif args.model == 'bert_bilstm_crf':
        print("评估模型中...")
        from model.bert_bilstm_crf import Bert_bilstm_crf__test
     
        pred = results()
        data_bundle = Bert_bilstm_crf__test(model, data_bundle, args)
        
        pred_tag_lists = []
        
        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq ]
            pred_tag_lists.append(pred_tag_list)
    # 保存预测结果
    output_path = args.output_path + args.model + '.txt'
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     for line in zip(words_list,pred_tag_lists):
    #         f.write(' '.join(line[0]) + '\n')
    #         f.write(' '.join(line[1]) + '\n')
    policy = []
    for i in zip(words_list, pred_tag_lists):
        if len(set(i[1]))>1: 
            policy.append(get_tuple(i[0], i[1]))

    print(policy)
    print("预测结果已保存到", output_path)
    # if args.eval:
    print("评估结果中...")
    metrics = Metrics(list(data_bundle.get_dataset('test')['raw_targets'])
            , pred_tag_lists, remove_O=args.O)
    metrics.report_scores()
    metrics.report_confusion_matrix()

def get_tuple( text, label):
    label = list(zip(label, range(len(label))))
    label = [i for i in label if i[0] != 'O' ]
    start = None
    tmp = dict()
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

    
def eval(args, data_bundle, model):
        
    from utils.data import eval_loader
    from pickle import load
    data_bundle = eval_loader().load(args.data_path)
    # 构建词表
    # print(data_bundle)
    data_bundle.set_dataset(data_bundle.get_dataset('train'), 'test')
    data_bundle.delete_dataset('train')

    if args.model in ['hmm', 'crf']:
        target = load(open('ckpts/hmm_target.pkl', 'rb'))
        words = load(open('ckpts/hmm_words.pkl', 'rb'))
    else:
        target = load(open('ckpts/bilstm_target.pkl', 'rb'))
        words = load(open('ckpts/bilstm_words.pkl', 'rb'))

    data_bundle.set_vocab(target, 'target')
    data_bundle.set_vocab(words, 'words')

    words.index_dataset(data_bundle.get_dataset('test'), field_name='raw_words', new_field_name='words')

    if not model:
        model_path = args.model_path + args.model + '.pkl'
        model = load_model(model_path)
    
    if args.model == 'hmm':
        print("评估模型中...")
        pred_tag_lists = model.test(data_bundle)

    elif args.model == 'crf':
        print("评估模型中...")
        pred_tag_lists = model.test(dataset=data_bundle.get_dataset('test'))
    
    elif args.model == 'bilstm':
        print("评估模型中...")
        from model.bilstm import bilstm_test
        
        data_bundle = bilstm_process(data_bundle)
        # data_bundle.delete_field('raw_words')
        # data_bundle.delete_field('raw_targets')
        pred = results()
        bilstm_test(model, data_bundle, args)
        
        pred_tag_lists = []
        
        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq ]
            pred_tag_lists.append(pred_tag_list)
    
    elif args.model == 'bilstm_crf':
        print("评估模型中...")
        from model.bilstm_crf import bilstm_crf_test
        data_bundle = bilstm_process(data_bundle)
        # data_bundle.delete_field('raw_words')
        # data_bundle.delete_field('raw_targets')
        pred = results()
        bilstm_crf_test(model, data_bundle, args)
        
        pred_tag_lists = []
        
        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq ]
            pred_tag_lists.append(pred_tag_list)

    elif args.model == 'bert':
        print("评估模型中...")
        from model.bert import bert_test
        data_bundle, tokenizer = bert_process(data_bundle, 'bert-base-chinese')
        # data_bundle.delete_field('raw_words')
        # data_bundle.delete_field('raw_targets')
        pred = results()
        bert_test(model, data_bundle, args)
        
        pred_tag_lists = []
        
        for seq in pred.result:
            pred_tag_list = [data_bundle.get_vocab("target").idx2word[idx] for idx in seq ]
            pred_tag_lists.append(pred_tag_list)
    
    
    
    print(pred_tag_lists)

    output_path = args.output_path + args.model + '.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in pred_tag_lists:
            f.write(' '.join(line) + '\n')


    print("预测结果已保存到", output_path)


def main():
    # 读取参数
    config = params()
    data_bundle = False
    model = False

    # print(config.train, config.test, config.eval)
    if config.train:
        model, data_bundle = train(args=config)
    
    if config.test:
        test(config, data_bundle, model)

    if config.eval:
        eval(config, data_bundle, model)




if __name__ == '__main__':
    # import torch
    # torch.cuda.set_device(1)
    # torch.cuda.empty_cache()
    main()

    
