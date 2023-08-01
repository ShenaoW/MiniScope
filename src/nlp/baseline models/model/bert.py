from utils.data import bert_process
from fastNLP import prepare_torch_dataloader
from torch import optim
from fastNLP import Trainer, LoadBestModelCallback, TorchWarmupCallback
from fastNLP import SpanFPreRecMetric

import torch
from torch import nn
from fastNLP.transformers.torch import BertModel
from fastNLP import seq_len_to_mask
import torch.nn.functional as F
from utils.util import results



class BertNER(nn.Module):
    def __init__(self, model_name, num_class):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.mlp = nn.Sequential(nn.Linear(self.bert.config.hidden_size, self.bert.config.hidden_size),
                                nn.Dropout(0.3),
                                nn.Linear(self.bert.config.hidden_size, num_class))

    def forward(self, input_ids, input_len, first):
        attention_mask = seq_len_to_mask(input_len)
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state
        first = first.unsqueeze(-1).repeat(1, 1, last_hidden_state.size(-1))
        first_bpe_state = last_hidden_state.gather(dim=1, index=first)
        first_bpe_state = first_bpe_state[:, 1:-1]  # 删除 cls 和 sep

        pred = self.mlp(first_bpe_state)
        return {'pred': pred}

    def train_step(self, input_ids, input_len, first, target):
        pred = self(input_ids, input_len, first)['pred']
        loss = F.cross_entropy(pred.transpose(1, 2), target)
        return {'loss': loss}

    def evaluate_step(self, input_ids, input_len, first):
        pred = self(input_ids, input_len, first)['pred'].argmax(dim=-1)
        return {'pred': pred}




def bert_train(data_bundle, args):
    data_bundle, tokenizer = bert_process(data_bundle, 'bert-base-chinese')

    train_data_loader = prepare_torch_dataloader(data_bundle.get_dataset('train'), batch_size=args.batch_size, shuffle=True)
    dev_data_loader = prepare_torch_dataloader(data_bundle.get_dataset('dev'), batch_size=args.batch_size)

    train_data_loader.set_pad('input_ids', pad_val=tokenizer.pad_token_id)
    train_data_loader.set_pad('target', pad_val=-100)

    dev_data_loader.set_pad('input_ids', pad_val=tokenizer.pad_token_id)
    dev_data_loader.set_pad('target', pad_val=-100)

    model = BertNER('bert-base-chinese', len(data_bundle.get_vocab('target')))

    optimizer = optim.Adam(model.parameters(), lr=2e-5)
    callbacks = [
        LoadBestModelCallback(),
        TorchWarmupCallback(),
    ]
    metrics = {
        "f": SpanFPreRecMetric(tag_vocab=data_bundle.get_vocab('target')),
    }

    trainer = Trainer(model=model, train_dataloader=train_data_loader, optimizers=optimizer,
                    evaluate_dataloaders=dev_data_loader,
                    metrics=metrics, n_epochs=args.epoch, callbacks=callbacks,
                    device=0, monitor='f#f')
    trainer.run()

    return model 

def bert_test(model, data_bundle, tokenizer, args):
    
    def output_labeling(evaluator, batch):
        predd = results()
        outputs = evaluator.evaluate_step(batch)["pred"].tolist()
        for i in range(len(outputs)):
            predd.result.append(outputs[i][:int(batch['seq_len'][i])])
            predd.words.append(batch['raw_words'][i][:int(batch['seq_len'][i])])
        del predd

    test_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('test'), batch_size=args.batch_size)

    test_dataloader.set_pad('input_ids', pad_val=tokenizer.pad_token_id)


    from fastNLP import Evaluator

    evaluator = Evaluator(model=model, dataloaders=test_dataloader,
                        device=0, evaluate_batch_step_fn=output_labeling)
    evaluator.run()

    return data_bundle