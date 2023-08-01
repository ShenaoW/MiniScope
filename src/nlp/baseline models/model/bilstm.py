import torch
import torch.nn as nn

from fastNLP.modules.torch import LSTM, MLP
from fastNLP.embeddings.torch import Embedding
from fastNLP import prepare_torch_dataloader
from torch import optim
from fastNLP import Trainer, LoadBestModelCallback, TorchWarmupCallback
from fastNLP import SpanFPreRecMetric
from fastNLP import Trainer
from utils.data import bilstm_process
from utils.util import results

class bilstm(nn.Module):
    def __init__(self, vocab_size, out_size, emb_size=100, hidden_size=128, num_layers=2, dropout=0.5):
        """初始化参数：
            vocab_size:字典的大小
            emb_size:词向量的维数
            hidden_size：隐向量的维数
            out_size:标注的种类
        """
        super(bilstm, self).__init__()
        
        self.embedding = Embedding((vocab_size, emb_size))
        self.lstm = LSTM(emb_size, hidden_size, num_layers=num_layers, bidirectional=True)
        self.mlp = MLP([hidden_size * 2, out_size], dropout=dropout)

        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, words, seq_len, target=None):
        output = self.embedding(words)
        output, (hidden, cell) = self.lstm(output, seq_len=seq_len)
        pred = self.mlp(output)
        if target == None:
            return {"pred": pred}
        else:
            loss = self.loss_fn(pred.transpose(1, 2), target)
            return {"loss": loss}
    
    def train_step(self, words, seq_len, target):
        return self(words, seq_len, target)
    
    def evaluate_step(self, words, seq_len):
        return self(words, seq_len)



def bilstm_train(data_bundle, args):
        print('构建BiLSTM模型ing.....')
        model = bilstm(len(data_bundle.get_vocab('words')), len(data_bundle.get_vocab('target')))
        data_bundle = bilstm_process(data_bundle)
        data_bundle.delete_field('raw_words')
        data_bundle.delete_field('raw_targets')
        # print(data_bundle.get_dataset('train'))

        # print('data_bundle: \n', data_bundle.get_dataset('train'))

        train_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('train'), batch_size=args.batch_size, shuffle=True)
        # print('train_dataloader: \n', list(train_dataloader))
        evaluate_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('dev'), batch_size=args.batch_size)

        train_dataloader.set_pad(field_name='words', pad_val=data_bundle.get_vocab('words').padding_idx)
        train_dataloader.set_pad(field_name='target', pad_val=data_bundle.get_vocab('target').padding_idx)

        optimizer = optim.Adam(model.parameters(), lr=2e-3)

        callbacks = [
            LoadBestModelCallback(),
            TorchWarmupCallback(),
        ]

        # ignore_labels = ['"', "''", '#', '$', '(', ')', ',', '.', ':', '``', ]

        # print(list(data_bundle.get_vocab('target')))
        callbacks = [
            LoadBestModelCallback()
        ]

        trainer = Trainer(
            model=model,
            driver='torch',
            device=[0,1],  # 'cuda'
            n_epochs=args.epoch,
            optimizers=optimizer,
            train_dataloader=train_dataloader,
            evaluate_dataloaders=evaluate_dataloader,
            metrics={'F1': SpanFPreRecMetric(tag_vocab=data_bundle.get_vocab('target'))},
            callbacks=callbacks, monitor='f#F1'
        )

        trainer.run(num_eval_batch_per_dl=10)
        print('BiLSTM模型训练完成！')
        return model


        
def bilstm_test(model, data_bundle, args):

    def output_labeling(evaluator, batch):
        predd = results()
        outputs = evaluator.evaluate_step(batch)["pred"].argmax(-1).tolist()
        for i in range(len(outputs)):
            predd.result.append(outputs[i][:int(batch['seq_len'][i])])
            predd.words.append(batch['raw_words'][i][:int(batch['seq_len'][i])])
        del predd

    test_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('test'), batch_size=args.batch_size)
    test_dataloader.set_pad(field_name='words', pad_val=data_bundle.get_vocab('words').padding_idx)

    from fastNLP import Evaluator

    evaluator = Evaluator(model=model, dataloaders=test_dataloader,
                        device=0, evaluate_batch_step_fn=output_labeling)
    evaluator.run()
