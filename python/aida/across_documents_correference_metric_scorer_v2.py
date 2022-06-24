"""
AIDA class for across documents coreference metric scorer.

Phase3-V2 refers to the variant where scores are based on pseudo-query i.e. original query + fqec
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "22 June 2022"

from aida.across_documents_correference_metric_score import AcrossDocumentsCoreferenceMetricScore
from aida.container import Container
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.task2_pool import Task2Pool
from aida.utility import multisort, get_cost_matrix, trim_cv
from munkres import Munkres

from xmlrpc.client import MAXINT

class AcrossDocumentsCoreferenceMetricScorerV2(Scorer):
    """
    AIDA class for across documents coreference metric scorer.
    """

    printing_specs = [{'name': 'entity_id',                 'header': 'SctdEntity', 'format': 's',    'justify': 'L'},
                      {'name': 'run_id',                    'header': 'RunID',      'format': 's',    'justify': 'L'},
                      {'name': 'query_id',                  'header': 'QueryID',    'format': 's',    'justify': 'L'},
                      {'name': 'fqec',                      'header': 'AssdEntity', 'format': 's',    'justify': 'L'},
                      {'name': 'num_rel_documents',         'header': 'Rel',        'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_rel_documents_counted', 'header': 'RelCntd',    'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_submitted',             'header': 'Sub',        'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_valid',                 'header': 'Valid',      'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_invalid',               'header': 'Invld',      'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_notpooled',             'header': 'NtMtPlgCrt', 'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_pooled',                'header': 'MtPlgCrt',   'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_assessed',              'header': 'Assd',       'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_notassessed',           'header': 'NtAssd',     'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_correct',               'header': 'Crct',       'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_inexact',               'header': 'Inexct',     'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_incorrect',             'header': 'Incrct',     'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_right',                 'header': 'Right',      'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_wrong',                 'header': 'Wrong',      'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_ignored',               'header': 'Ignrd',      'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'average_precision',         'header': 'AP',         'format': '6.4f', 'justify': 'R'},
                      {'name': 'cluster_id',                'header': 'ClusterID',  'format': 's',    'justify': 'L'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def aggregate_scores(self, scores, score_class):
        aggregate = score_class(self.get('logger'),
                                aggregate=True,
                                run_id=self.get('run_id'),
                                summary=True,
                                entity_id='Summary',
                                query_id='ALL-Macro',
                                elements=Container(self.get('logger')))
        for score in scores.values():
            aggregate.get('elements').add(score)
        scores.add(aggregate)

    def order(self, k):
        return k

    def get_counts(self, query_id):
        def apply_normalization_and_compute_weights(responses, cluster_id, APPLY_NORMALIZATION, APPLY_WEIGHTS):
            def compute_weights(responses, APPLY_NORMALIZATION, APPLY_WEIGHTS):
                for response in responses.values():
                    weight = 1
                    if APPLY_WEIGHTS:
                        if APPLY_NORMALIZATION:
                            weight = response.get('normalized_justification_confidence')
                        else:
                            weight = trim_cv(response.get('justification_confidence'))
                    response.set('weight', weight)
            def normalize_confidences(responses, cluster_id):
                max_confidence = None
                for response in responses.values():
                    if response.get('cluster_id') != cluster_id: continue
                    justification_confidence = trim_cv(response.get('justification_confidence'))
                    if max_confidence is None:
                        max_confidence = justification_confidence
                    if justification_confidence > max_confidence:
                        max_confidence = justification_confidence
                for response in responses.values():
                    normalized_confidence_value = trim_cv(response.get('justification_confidence'))/max_confidence
                    response.set('normalized_justification_confidence', normalized_confidence_value)
            if APPLY_NORMALIZATION:
                normalize_confidences(responses, cluster_id)
            compute_weights(responses, APPLY_NORMALIZATION, APPLY_WEIGHTS)

        def order(r):
            if r.get('is_pooled') and r.get('assessment') is not None:
                return r.get('response_rank')
            return MAXINT

        def compute_AP(logger, query_id, num_ground_truth, responses, cluster_id, fqec, TRUNCATE):
            # update
            # how is response.get('assessment') populated
            num_responses = 0
            num_right = 0
            sum_precision = 0
            for response in sorted(responses.values(), key=order):
                if response.get('cluster_id') != cluster_id: continue
                if response.get('is_pooled') and response.get('valid') and response.get('assessment') is not None:
                    post_policy_assessment = response.get('categorization').get('POST_POLICY')
                    response_fqec = response.get('assessment').get('fqec')
                    if TRUNCATE and num_responses == TRUNCATE:
                        break
                    num_responses += 1
                    if post_policy_assessment == 'RIGHT' and fqec == response_fqec:
                        num_right += response.get('weight')
                        sum_precision += num_right/num_responses
                    self.record_event('AP_RANKED_LIST', query_id, num_ground_truth, cluster_id, fqec, num_responses, response.get('mention_span_text'), post_policy_assessment, response.get('weight'), sum_precision, response.get('where'))
            ap = sum_precision/num_ground_truth if num_ground_truth else 0
            self.record_event('PAIR_WISE_AP', query_id, cluster_id, fqec, ap)
            return ap

        def lookup_AP(APs, item_a, item_b):
            if item_a in APs:
                if item_b in APs.get(item_a):
                    return APs.get(item_a).get(item_b)
            return 0

        def record_categorized_response(categorized_responses, policy, category_name, response):
            categorized_responses.get(policy).setdefault(category_name, list()).append(response)
            if response.get('categorization') is None:
                response.set('categorization', {'PRE_POLICY': set(), 'POST_POLICY': None})
            if policy == 'PRE_POLICY':
                response.get('categorization').get(policy).add(category_name)
            else:
                # ['RIGHT', 'WRONG', 'IGNORE'] are the only allowed values
                if category_name not in ['RIGHT', 'WRONG', 'IGNORED']:
                    response.record_event('INVALID_POSTPOLICY_CATEGORIZATION', category_name, response.get('where'))
                if response.get('categorization').get(policy) is None:
                    response.get('categorization')['POST_POLICY'] = category_name
                # Overwriting POST_POLICY assessment with a different value is not allowed
                elif response.get('categorization').get(policy) != category_name:
                    response.record_event('OVERWRITING_POSTPOLICY_CATEGORIZATION', response.get('categorization').get(policy), category_name, response.get('where'))

        def categorize_responses(responses, assessments, selected_clusters, categorized_responses, ids):
            if responses is None: return
            selected_cluster_justifications = {}
            for cluster_id in selected_clusters:
                selected_cluster_justifications[cluster_id] = pooler.get('top_K_cluster_justifications', selected_clusters[cluster_id], K=num_documents)
            for response in responses.values():
                record_categorized_response(categorized_responses, 'PRE_POLICY', 'SUBMITTED', response)
                if response.get('cluster_id') in selected_clusters:
                    if response.get('valid'):
                        record_categorized_response(categorized_responses, 'PRE_POLICY', 'VALID', response)
                        if response.get('is_pooled'):
                            record_categorized_response(categorized_responses, 'PRE_POLICY', 'METPOOLINGCRITERIA', response)
                        else:
                            record_categorized_response(categorized_responses, 'PRE_POLICY', 'NOTMETPOOLINGCRITERIA', response)
                            record_categorized_response(categorized_responses, 'POST_POLICY', 'IGNORED', response)
                            continue
                    else:
                        record_categorized_response(categorized_responses, 'PRE_POLICY', 'INVALID', response)
                        record_categorized_response(categorized_responses, 'PRE_POLICY', 'NOTMETPOOLINGCRITERIA', response)
                        record_categorized_response(categorized_responses, 'POST_POLICY', 'IGNORED', response)
                        continue
                else:
                    if response.get('valid'):
                        record_categorized_response(categorized_responses, 'PRE_POLICY', 'VALID', response)
                    else:
                        record_categorized_response(categorized_responses, 'PRE_POLICY', 'INVALID', response)
                    record_categorized_response(categorized_responses, 'PRE_POLICY', 'NOTMETPOOLINGCRITERIA', response)
                    record_categorized_response(categorized_responses, 'POST_POLICY', 'IGNORED', response)
                    continue
                mention_span_text = response.get('mention_span_text')

                pre_policy_assessment = None
                if mention_span_text in assessments:
                    response.set('assessment', assessments.get(mention_span_text))
                    pre_policy_assessment = assessments.get(mention_span_text).get('assessment')
                    post_policy_assessment = 'RIGHT' if pre_policy_assessment in ['CORRECT', 'INEXACT'] else 'WRONG'
                    record_categorized_response(categorized_responses, 'PRE_POLICY', pre_policy_assessment, response)
                    record_categorized_response(categorized_responses, 'POST_POLICY', post_policy_assessment, response)
                else:
                    record_categorized_response(categorized_responses, 'PRE_POLICY', 'NOTASSESSED', response)
                    record_categorized_response(categorized_responses, 'POST_POLICY', 'IGNORED', response)
                    self.record_event('ITEM_MET_POOLING_CRITERIA_BUT_NOT_ASSESSED', mention_span_text, response.get('where'))
                    continue
                selected_justifications = selected_cluster_justifications[response.get('cluster_id')]
                if mention_span_text in selected_justifications:
                    response.set('response_rank', selected_justifications[mention_span_text]['response_rank'])
                    response.set('cluster_rank', selected_justifications[mention_span_text]['cluster_rank'])
                    ids['clusters'].add(response.get('cluster_id'))
                    if post_policy_assessment == 'RIGHT':
                        ids['equivalence_classes'].add(response.get('assessment').get('fqec'))
            for response in responses.values():
                self.record_event('RESPONSE_CATEGORIZATION_INFO',
                                    query_id,
                                    response.get('cluster_id'),
                                    response.get('mention_span_text'),
                                    response.get('linking_confidence'),
                                    response.get('cluster_rank'),
                                    response.get('justification_confidence'),
                                    response.get('weight'),
                                    response.get('response_rank'),
                                    ','.join(sorted(response.get('categorization').get('PRE_POLICY'))),
                                    ','.join(sorted(response.get('categorization').get('POST_POLICY'))),
                                    response.get('where')
                                    )

        logger = self.get('logger')
        responses = self.get('query_responses', query_id)
        assessments = self.get('assessments_map')
        pooler = Task2Pool(logger, DONOT_VALIDATE_DESCRIPTOR=True)
        num_clusters = self.get('num_clusters', query_id)
        num_documents = self.get('num_documents', query_id)
        selected_clusters = pooler.get('top_C_clusters', responses, C=num_clusters) if responses else []
        for cluster_id in selected_clusters:
            apply_normalization_and_compute_weights(responses,
                                                    cluster_id,
                                                    APPLY_NORMALIZATION=self.get('normalize'),
                                                    APPLY_WEIGHTS=self.get('weighted'))
        ids = {
            'clusters': set(),
            'equivalence_classes': self.get('equivalence_classes', query_id)
            }
        categorized_responses = {'PRE_POLICY': {}, 'POST_POLICY': {}}
        categorize_responses(responses, assessments, selected_clusters, categorized_responses, ids)

        APs = {}
        for cluster_id in ids['clusters']:
            if cluster_id not in APs:
                APs[cluster_id] = {}
            for fqec in ids['equivalence_classes']:
                num_rel_documents_counted = self.get('num_rel_documents_counted', query_id, fqec)
                APs[cluster_id][fqec] = compute_AP(logger,
                                                   query_id,
                                                   num_rel_documents_counted,
                                                   responses,
                                                   cluster_id,
                                                   fqec,
                                                   num_documents if self.get('cutoff') else False)

        mappings = {}
        for item_type in ['clusters', 'equivalence_classes']:
            mappings[item_type] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0
            for item_id in sorted(ids.get(item_type)):
                mappings[item_type]['id_to_index'][item_id] = index
                mappings[item_type]['index_to_id'][index] = item_id
                index += 1
        alignment = {'cluster_to_fqec': {}, 'fqec_to_cluster': {}}
        if len(APs):
            cost_matrix = get_cost_matrix(APs, mappings, type_a='clusters', type_b='equivalence_classes')
            for cluster_index, fqec_index in Munkres().compute(cost_matrix):
                cluster_id = mappings['clusters']['index_to_id'][cluster_index]
                fqec = mappings['equivalence_classes']['index_to_id'][fqec_index]
                AP = lookup_AP(APs, cluster_id, fqec)
                if AP > 0:
                    alignment.get('cluster_to_fqec')[cluster_id] = {
                            'aligned_to': fqec,
                            'AP': AP
                        }
                    alignment.get('fqec_to_cluster')[fqec] = {
                            'aligned_to': cluster_id,
                            'AP': AP
                        }
                    self.record_event('ALIGNMENT_INFO', query_id, cluster_id, fqec)

        countss = []
        for fqec in self.get('equivalence_classes', query_id):
            cluster_id = None
            average_precision = 0
            if fqec in alignment.get('fqec_to_cluster'):
                average_precision = alignment.get('fqec_to_cluster').get(fqec).get('AP')
                cluster_id = alignment.get('fqec_to_cluster').get(fqec).get('aligned_to')
            counts = {'average_precision': average_precision,
                      'num_rel_documents': self.get('num_rel_documents', fqec),
                      'num_rel_documents_counted': self.get('num_rel_documents_counted', query_id, fqec),
                      'fqec': fqec,
                      'cluster_id': str(cluster_id)}
            for field_name in [s.get('name') for s in self.get('printing_specs') if s.get('name').startswith('num_')]:
                counts[field_name] = counts[field_name] if field_name in counts else self.get(field_name, cluster_id, categorized_responses)
            countss.append(counts)
        return countss

    def get_entity_id(self, query_id):
        return str(self.get('queries_to_score').get(query_id).get('entity_id'))

    def get_equivalence_classes(self, query_id):
        equivalence_classes = set()
        for entry in self.get('assessments').get(query_id).values():
            if entry.get('assessment') in ['CORRECT', 'INEXACT']:
                equivalence_classes.add(entry.get('fqec'))
        entity_id = self.get('queries_to_score').get(query_id).get('entity_id')
        for query_id in self.get('queries_to_score'):
            if self.get('queries_to_score').get(query_id).get('entity_id') == entity_id:
                entry = self.get('queries_to_score').get(query_id)
                if entry.get('entrypoint_type') == 'kbid':
                    equivalence_classes.add(entry.get('entrypoint'))
        return equivalence_classes

    def get_num_clusters(self, query_id):
        return int(self.get('queries_to_score').get(query_id).get('clusters'))

    def get_num_documents(self, query_id):
        return int(self.get('queries_to_score').get(query_id).get('documents'))

    def get_num_rel_documents(self, fqec):
        relevant_documents = set()
        for query_id in self.get('queries_to_score'):
            for entry in self.get('assessments').get(query_id).values():
                if entry.get('fqec') == fqec and entry.get('assessment') in ['CORRECT', 'INEXACT']:
                    relevant_documents.add(entry.get('docid'))
        return len(relevant_documents)

    def get_num_rel_documents_counted(self, query_id, fqec):
        num_documents = self.get('num_documents', query_id)
        num_rel_documents_counted = self.get('num_rel_documents', fqec)
        if self.get('cutoff') and num_rel_documents_counted > num_documents:
            num_rel_documents_counted = num_documents
        return num_rel_documents_counted

    def get_num_submitted(self, cluster_id, cr):
        key = 'SUBMITTED'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_valid(self, cluster_id, cr):
        key = 'VALID'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_inexact(self, cluster_id, cr):
        key = 'INEXACT'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_invalid(self, cluster_id, cr):
        key = 'INVALID'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_notpooled(self, cluster_id, cr):
        key = 'NOTMETPOOLINGCRITERIA'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_pooled(self, cluster_id, cr):
        key = 'METPOOLINGCRITERIA'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_assessed(self, cluster_id, cr):
        num_pooled = self.get('num_pooled', cluster_id, cr)
        num_notassessed = self.get('num_notassessed', cluster_id, cr)
        return num_pooled - num_notassessed

    def get_num_notassessed(self, cluster_id, cr):
        key = 'NOTASSESSED'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_correct(self, cluster_id, cr):
        key = 'CORRECT'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_incorrect(self, cluster_id, cr):
        key = 'INCORRECT'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_right(self, cluster_id, cr):
        key = 'RIGHT'
        policy = 'POST_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_wrong(self, cluster_id, cr):
        key = 'WRONG'
        policy = 'POST_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_num_ignored(self, cluster_id, cr):
        key = 'IGNORED'
        policy = 'POST_POLICY'
        return 0 if key not in cr.get(policy) else len(
            [e for e in cr.get(policy).get(key) if e.get('cluster_id') == cluster_id])

    def get_assessments_map(self):
        assessments = Container(self.get('logger'))
        for query_id in self.get('queries_to_score'):
            for key in self.get('assessments').get(query_id):
                value = self.get('assessments').get(query_id).get(key)
                if key not in assessments:
                    assessments.add(value, key)
                elif value.get('assessment') != assessments.get(key).get('assessment'):
                    self.record_event('CONFLICTING_ASSESSMENTS', key, query_id, assessments.get(key).get('queryid'))
        return assessments

    def get_query_responses(self, query_id):
        return self.get('responses').get('{path}/{query_id}.rq.tsv'.format(path=self.get('responses').get('path'),
                                                                           query_id=query_id))

    def score_responses(self):
        scores = []
        sum_average_precision = 0
        for query_id in self.get('queries_to_score'):
            entity_id = self.get('entity_id', query_id)
            countss = self.get('counts', query_id)
            for counts in countss:
                sum_average_precision += counts['average_precision']
                score = AcrossDocumentsCoreferenceMetricScore(self.get('logger'),
                                                              run_id=self.get('run_id'),
                                                              query_id=query_id,
                                                              entity_id=entity_id,
                                                              **counts)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs, aggregate_types=['ALL-Macro'])
        for score in multisort(scores, (('entity_id', False),
                                        ('query_id', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, AcrossDocumentsCoreferenceMetricScore)
        self.scores = scores_printer