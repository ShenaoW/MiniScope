import argparse


def params():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--train', default=False, action="store_true", help='Whether train the model')

    parser.add_argument('--model', default='hmm', type=str, choices=['hmm', 'crf', 'bilstm', 'bert','bilstm_crf', 'bert_bilstm_crf'],help='Model to use')

    parser.add_argument('--data_path', default='./data/', type=str, help='Path of data')

    parser.add_argument('--model_path', default='./ckpts/', type=str, help='Path of model')

    parser.add_argument('--batch_size', default=64, type=int, help='Batch size')

    parser.add_argument('--epoch', default=10, type=int, help='Epoch')

    parser.add_argument('--lr', default=0.001, type=float, help='Learning rate')

    parser.add_argument('--test', default=False, action="store_true", help='Whether test the model')

    parser.add_argument('--output_path', default='./output/', type=str, help='Path of output')

    parser.add_argument('--eval', default=False, action="store_true", help='Whether evaluate the model')

    parser.add_argument('-O', default=False, action="store_true", help='Whether remove O tag')
    
    parser.add_argument('--classify', default=False, action="store_true", help='classify')

    parser.add_argument('--file_path', type=str, help='Path of file to predict')
    args = parser.parse_args()

    return args