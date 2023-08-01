from fastNLP.models.torch import BiLSTMCRF
from utils.data import bilstm_process
from fastNLP import prepare_torch_dataloader
from fastNLP import SpanFPreRecMetric
from fastNLP import Trainer, LoadBestModelCallback, TorchWarmupCallback
from torch.optim import AdamW
from utils.util import results

def bilstm_crf_train(data_bundle, args):
    print('构建BiLSTM-CRF模型ing.....')
    # 数据预处理
    data_bundle = bilstm_process(data_bundle)
    # data_bundle.delete_field('raw_words')
    # data_bundle.delete_field('raw_targets')

    train_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('train'), batch_size=args.batch_size, shuffle=True)
    # print('train_dataloader: \n', list(train_dataloader))
    evaluate_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('dev'), batch_size=args.batch_size)
    
    model = BiLSTMCRF(embed=(len(data_bundle.get_vocab('words')), 128), 
                      num_classes=len(data_bundle.get_vocab('target')), 
                      num_layers=2,
                      hidden_size=128,
                      dropout=0.5,)

    optimizers = AdamW(params=model.parameters(), lr=0.001)
    callbacks = [
            LoadBestModelCallback()   # 用于在训练结束之后加载性能最好的model的权重

        ]
    
    trainer = Trainer(
    model=model,
    driver='torch',
    device=[0,1],  # 'cuda'
    n_epochs=args.epoch,
    optimizers=optimizers,
    train_dataloader=train_dataloader,
    evaluate_dataloaders=evaluate_dataloader,
    metrics={'F1': SpanFPreRecMetric(tag_vocab=data_bundle.get_vocab('target'))},
    callbacks=callbacks, monitor='f#F1'
    )

    trainer.run(num_eval_batch_per_dl=10)

    trainer.evaluator.run()
    return model

def bilstm_crf_test(model, data_bundle, args):

    def output_labeling(evaluator, batch):
        predd = results()
        outputs = evaluator.evaluate_step(batch)["pred"].tolist()
        for i in range(len(outputs)):
            predd.result.append(outputs[i][:int(batch['seq_len'][i])])
            predd.words.append(batch['raw_words'][i][:int(batch['seq_len'][i])])
        del predd

    test_dataloader = prepare_torch_dataloader(data_bundle.get_dataset('test'), batch_size=16)

    from fastNLP import Evaluator

    evaluator = Evaluator(model=model, dataloaders=test_dataloader,
                        device=0, evaluate_batch_step_fn=output_labeling)
    evaluator.run()