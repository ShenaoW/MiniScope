import sys
sys.path.append('..')
from sklearn_crfsuite import CRF
from utils.util import sent2features


class CRFModel(object):
    def __init__(self,
                 algorithm='lbfgs',
                 c1=0.1,
                 c2=0.1,
                 max_iterations=100,
                 all_possible_transitions=False
                 ):

        self.model = CRF(algorithm=algorithm,
                         c1=c1,
                         c2=c2,
                         max_iterations=max_iterations,
                         all_possible_transitions=all_possible_transitions)

    def train(self, dataset):
        features = [sent2features(s) for s in dataset['raw_words']]
        self.model.fit(features, list(dataset['raw_targets']))

    def test(self, dataset):
        features = [sent2features(s) for s in dataset['raw_words']]
        pred_tag_lists = self.model.predict(features)
        return pred_tag_lists
