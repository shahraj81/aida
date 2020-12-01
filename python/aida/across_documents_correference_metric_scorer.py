"""
AIDA class for across documents coreference metric scorer.

V1 refers to the variant where we ignore correctness of argument assertion justification.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "23 November 2020"

from aida.across_documents_correference_metric_score import AcrossDocumentsCoreferenceMetricScore
from aida.container import Container
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.task2_pool import Task2Pool
from aida.utility import multisort

class AcrossDocumentsCoreferenceMetricScorer(Scorer):
    """
    AIDA class for across documents coreference metric scorer.
    """

    printing_specs = [{'name': 'entity_id',         'header': 'EntityID', 'format': 's',    'justify': 'L'},
                      {'name': 'run_id',            'header': 'RunID',    'format': 's',    'justify': 'L'},
                      {'name': 'query_id',          'header': 'QueryID',  'format': 's',    'justify': 'L'},
                      {'name': 'average_precision', 'header': 'AvgPrec',  'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, separator=None, **kwargs):
        super().__init__(logger, separator=separator, **kwargs)

    def order(self, k):
        return k

    def get_score(self, query_id):
        logger = self.get('logger')
        responses = self.get('query_responses', query_id)
        assessments = self.get('query_assessments', query_id)

        # bind assessment to responses
        for response in responses.values():
            assessment = None
            mention_span_text = response.get('mention_span_text')
            if mention_span_text in assessments:
                assessment = assessments.get(mention_span_text)
            response.set('ASSESSMENT', assessment)
            response.set('POOLED', False)

        # set if the response was pooled
        # this should be independent of what the assessment file says
        # because LDC might have accidently removed an entry
        pooler = Task2Pool(logger, DONOT_VALIDATE_DESCRIPTOR=True)
        num_clusters = int(self.get('queries_to_score').get(query_id).get('clusters'))
        num_documents = int(self.get('queries_to_score').get(query_id).get('documents'))
        selected_clusters = pooler.get('top_C_clusters', responses, C=num_clusters)
        for cluster_id in selected_clusters:
                cluster_responses = selected_clusters[cluster_id]
                selected_justifications = pooler.get('top_K_cluster_justifications', cluster_responses, K=num_documents)
                for selected_justification in selected_justifications:
                    for response in responses.values():
                        if response.get('mention_span_text') == selected_justification and response.get('cluster_id') == cluster_id:
                            response.set('POOLED', True)

        # Dummy method
        # TODO: write actual method
        print("TODO: finish get_score")

        average_precision = int(query_id[-4:])*0.0001
        return average_precision

    def get_entity_id(self, query_id):
        return str(self.get('queries_to_score').get(query_id).get('entity_id'))

    def get_query_assessments(self, query_id):
        return self.get('assessments').get(query_id)

    def get_query_responses(self, query_id):
        return self.get('responses').get('{path}/{query_id}.rq.tsv'.format(path=self.get('responses').get('path'),
                                                                           query_id=query_id))

    def score_responses(self):
        scores = []
        mean_average_precisions = {}
        counts = {}
        for query_id in self.get('queries_to_score'):
            entity_id = self.get('entity_id', query_id)
            average_precision = self.get('score', query_id)
            for query_id_key in ['ALL-Micro', query_id]:
                for entity_id_key in ['Summary', entity_id]:
                    aggregate_key = '{entity_id_key}:{query_id_key}'.format(entity_id_key=entity_id_key, query_id_key=query_id_key)
                    mean_average_precisions[aggregate_key] = mean_average_precisions.get(aggregate_key, 0) + average_precision
                    counts[aggregate_key] = counts.get(aggregate_key, 0) + 1
            score = AcrossDocumentsCoreferenceMetricScore(self.get('logger'),
                                                          self.get('run_id'),
                                                          query_id,
                                                          entity_id,
                                                          average_precision)
            scores.append(score)

        macro_average_precision = 0
        macro_average_precision_count = 0
        for key in sorted(mean_average_precisions, key=self.order):
            entity_id_key, query_id_key = key.split(':')
            if query_id_key != 'ALL-Micro': continue
            mean_average_precision = mean_average_precisions[key] / counts[key] if counts[key] else 0
            if entity_id_key != 'Summary':
                macro_average_precision += mean_average_precision
                macro_average_precision_count += 1
            mean_score = AcrossDocumentsCoreferenceMetricScore(self.get('logger'),
                                                               self.get('run_id'),
                                                               query_id_key,
                                                               entity_id_key,
                                                               mean_average_precision,
                                                               summary = True)
            scores.append(mean_score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs, self.separator)
        for score in multisort(scores, (('entity_id', False),
                                        ('query_id', False))):
            scores_printer.add(score)

        macro_average_precision = macro_average_precision/macro_average_precision_count if macro_average_precision_count else 0
        macro_average_score = AcrossDocumentsCoreferenceMetricScore(self.get('logger'),
                                                                    self.get('run_id'),
                                                                    'ALL-Macro',
                                                                    entity_id_key,
                                                                    macro_average_precision,
                                                                    summary = True)
        scores_printer.add(macro_average_score)

        self.scores = scores_printer