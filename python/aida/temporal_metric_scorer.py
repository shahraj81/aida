"""
AIDA class for temporal metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "27 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.temporal_metric_score import TemporalMetricScore
from aida.utility import multisort

import datetime

class TemporalMetricScorer(Scorer):
    """
    AIDA class for class query scores.
    """

    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'gold_cluster_id',  'header': 'GoldClusterID',   'format': 's',    'justify': 'L'},
                      {'name': 'system_cluster_id','header': 'SystemClusterID', 'format': 's',    'justify': 'L'},
                      {'name': 'similarity',       'header': 'Similarity',      'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator)

    def order(self, k):
        language, metatype = k.split(':')
        metatype = '_ALL' if metatype == 'ALL' else metatype
        language = '_ALL' if language == 'ALL' else language
        return '{language}:{metatype}'.format(metatype=metatype, language=language)

    def compute_temporal_similarity(self, gold_date_range, system_date_range):
        k = self.get('temporal_tuple', gold_date_range)
        r = self.get('temporal_tuple', system_date_range)
        c = self.get('c', k, r)
        count = 0
        similarity = 0
        for index in k:
            if k[index] is not None:
                if r[index] is not None:
                    timedelta_object = k[index] - r[index]
                    d = abs(timedelta_object.days)/365
                    similarity += c/(c+d)
                count += 1
        similarity = similarity/count if count else 0
        return similarity

    def get_c(self, k, r):
        c_overconstraining = 1/12
        c_vagueness = 1/12
        c = c_vagueness
        overconstraining = False
        overconstraining_elements = {1: False, 2: False, 3: False, 4: False}
        for i in [1,3]:
            if r[i] and k[i] and r[i] > k[i]:
                overconstraining_elements[i] = True
        for i in [2,4]:
            if r[i] and k[i] and r[i] < k[i]:
                overconstraining_elements[i] = True
        if overconstraining_elements[1] and overconstraining_elements[3]: overconstraining = True
        if overconstraining_elements[2] and overconstraining_elements[4]: overconstraining = True
        if overconstraining:
            c = c_overconstraining
        return c

    def get_temporal_similarity(self, gold_date_range, system_date_ranges):
        similarity = 0
        if len(system_date_ranges) > 0:
            count = 0
            for system_date_range in system_date_ranges:
                similarity += self.compute_temporal_similarity(gold_date_range, system_date_range)
                count += 1
            similarity = similarity / count
        return similarity

    def get_date(self, date_object):
        return datetime.date(int(date_object.get('year')), int(date_object.get('month')), int(date_object.get('day')))

    def get_temporal_tuple(self, date_range):
        index_to_name = {
            1: tuple(['start', 'after']),
            2: tuple(['start', 'before']),
            3: tuple(['end', 'after']),
            4: tuple(['end', 'before'])
            }
        temporal_tuple = {}
        for index in index_to_name:
            start_or_end, before_or_after = index_to_name[index]
            date_object = None
            if date_range is not None and date_range.get(start_or_end):
                if date_range.get(start_or_end).get(before_or_after):
                    date_object = self.get('date', date_range.get(start_or_end).get(before_or_after))
            temporal_tuple[index] = date_object
        return temporal_tuple

    def score_responses(self):
        scores = []
        mean_similarities = {}
        counts = {}
        for document_id in self.get('core_documents'):
            # add scores corresponding to all gold clusters
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            language = document.get('language')
            document_gold_to_system = self.get('cluster_alignment').get('gold_to_system').get(document_id)
            for gold_cluster_id in document_gold_to_system if document_gold_to_system else []:
                system_cluster_id = document_gold_to_system.get(gold_cluster_id).get('aligned_to')
                aligned_similarity = document_gold_to_system.get(gold_cluster_id).get('aligned_similarity')
                similarity = 0
                if gold_cluster_id == 'None': continue
                gold_cluster = self.get('cluster', 'gold', document_id, gold_cluster_id)
                metatype = gold_cluster.get('metatype')
                if metatype not in ['Event', 'Relation']: continue
                if list(gold_cluster.get('dates').values())[0] is None:
                    self.record_event('NO_TEMPORAL_CONSTRAINT', gold_cluster_id, document_id)
                    continue
                if system_cluster_id != 'None':
                    if aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                    system_cluster = self.get('cluster', 'system', document_id, system_cluster_id)
                    if system_cluster.get('metatype') != metatype:
                        self.record_event('UNEXPECTED_ALIGNED_CLUSTER_METATYPE', system_cluster.get('metatype'), system_cluster_id, metatype, gold_cluster_id)
                    if len(gold_cluster.get('dates').keys()) > 1:
                        self.record_event('UNEXPECTED_NUM_DATES', gold_cluster_id, document_id)
                    similarity = self.get('temporal_similarity', list(gold_cluster.get('dates').values())[0], list(system_cluster.get('dates').values()))
                for metatype_key in ['ALL', metatype]:
                    for language_key in ['ALL', language]:
                        key = '{language}:{metatype}'.format(metatype=metatype_key, language=language_key)
                        mean_similarities[key] = mean_similarities.get(key, 0) + similarity
                        counts[key] = counts.get(key, 0) + 1
                score = TemporalMetricScore(self.logger,
                                           self.get('runid'),
                                           document_id,
                                           language,
                                           metatype,
                                           gold_cluster_id,
                                           system_cluster_id,
                                           similarity)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs, self.separator)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False),
                                        ('gold_cluster_id', False),
                                        ('system_cluster_id', False))):
            scores_printer.add(score)
        for key in sorted(mean_similarities, key=self.order):
            mean_similarity = mean_similarities[key] / counts[key] if counts[key] else 0
            language, metatype = key.split(':')
            mean_score = TemporalMetricScore(self.logger,
                                            self.get('runid'),
                                            'Summary',
                                            language,
                                            metatype,
                                            '',
                                            '',
                                            mean_similarity,
                                            summary = True)
            scores_printer.add(mean_score)
        self.scores = scores_printer