"""
AIDA class for across documents coreference metric scorer.

V1 refers to the variant where we ignore correctness of argument assertion justification.
"""
from xmlrpc.client import MAXINT

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "23 November 2020"

from aida.across_documents_correference_metric_score import AcrossDocumentsCoreferenceMetricScore
from aida.container import Container
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.task2_pool import Task2Pool
from aida.utility import multisort, get_cost_matrix, trim_cv
from munkres import Munkres

class AcrossDocumentsCoreferenceMetricScorer(Scorer):
    """
    AIDA class for across documents coreference metric scorer.
    """

    printing_specs = [{'name': 'entity_id',                 'header': 'EntityID',              'format': 's',    'justify': 'L'},
                      {'name': 'run_id',                    'header': 'RunID',                 'format': 's',    'justify': 'L'},
                      {'name': 'query_id',                  'header': 'QueryID',               'format': 's',    'justify': 'L'},
                      {'name': 'num_rel_documents',         'header': 'Relevant',              'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_rel_documents_counted', 'header': 'RelevantCounted',       'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_submitted',             'header': 'Submitted',             'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_valid',                 'header': 'Valid',                 'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_invalid',               'header': 'Invalid',               'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_notpooled',             'header': 'NotMetPoolingCriteria', 'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_pooled',                'header': 'MetPoolingCriteria',    'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_assessed',              'header': 'Assessed',              'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_correct',               'header': 'Correct',               'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_incorrect',             'header': 'Incorrect',             'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_right',                 'header': 'Right',                 'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_wrong',                 'header': 'Wrong',                 'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'num_ignored',               'header': 'Ignored',               'format': 'd',    'justify': 'R', 'mean_format': '0.2f'},
                      {'name': 'average_precision',         'header': 'AvgPrec',               'format': '6.4f', 'justify': 'R'}]

    def __init__(self, logger, separator=None, **kwargs):
        super().__init__(logger, separator=separator, **kwargs)

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
            num_responses = 0
            num_correct = 0
            sum_precision = 0
            for response in sorted(responses.values(), key=order):
                if response.get('cluster_id') != cluster_id: continue
                if response.get('is_pooled') and response.get('valid') and response.get('assessment') is not None:
                    assessment = response.get('assessment').get('assessment')
                    response_fqec = response.get('assessment').get('fqec')
                    if TRUNCATE and num_responses == TRUNCATE:
                        break
                    num_responses += 1
                    if assessment == 'CORRECT' and fqec == response_fqec:
                        num_correct += response.get('weight')
                        sum_precision += num_correct/num_responses
                    logger.record_event('AP_RANKED_LIST', query_id, num_ground_truth, cluster_id, fqec, num_responses, response.get('mention_span_text'), assessment, response.get('weight'), sum_precision, response.get('where'))
            ap = sum_precision/num_ground_truth if num_ground_truth else 0
            logger.record_event('PAIR_WISE_AP', query_id, cluster_id, fqec, ap)
            return ap

        def lookup_AP(APs, item_a, item_b):
            if item_a in APs:
                if item_b in APs.get(item_a):
                    return APs.get(item_a).get(item_b)
            return 0

        def record_categorized_response(categorized_responses, policy, category_name, response):
            categorized_responses.get(policy).setdefault(category_name, list()).append(response)
            if response.get('categorization') is None:
                response.set('categorization', {'PRE_POLICY': set(), 'POST_POLICY': set()})
            response.get('categorization').get(policy).add(category_name)

        def categorize_responses(responses, selected_clusters, categorized_responses, ids):
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
                    post_policy_assessment = 'RIGHT' if pre_policy_assessment == 'CORRECT' else 'WRONG'
                    record_categorized_response(categorized_responses, 'PRE_POLICY', pre_policy_assessment, response)
                    record_categorized_response(categorized_responses, 'POST_POLICY', post_policy_assessment, response)
                else:
                    record_categorized_response(categorized_responses, 'PRE_POLICY', 'NOTASSESSED', response)
                    record_categorized_response(categorized_responses, 'POST_POLICY', 'IGNORED', response)
                    logger.record_event('ITEM_MET_POOLING_CRITERIA_BUT_NOT_ASSESSED', mention_span_text, response.get('where'))
                    continue
                selected_justifications = selected_cluster_justifications[response.get('cluster_id')]
                if mention_span_text in selected_justifications:
                    response.set('response_rank', selected_justifications[mention_span_text]['response_rank'])
                    response.set('cluster_rank', selected_justifications[mention_span_text]['cluster_rank'])
                    ids['clusters'].add(response.get('cluster_id'))
                    if pre_policy_assessment == 'CORRECT':
                        ids['equivalence_classes'].add(response.get('assessment').get('fqec'))
            for response in responses.values():
                logger.record_event('RESPONSE_CATEGORIZATION_INFO',
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
        assessments = self.get('entity_assessments', query_id)

        pooler = Task2Pool(logger, DONOT_VALIDATE_DESCRIPTOR=True)
        num_clusters = int(self.get('queries_to_score').get(query_id).get('clusters'))
        num_documents = int(self.get('queries_to_score').get(query_id).get('documents'))
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
        categorize_responses(responses, selected_clusters, categorized_responses, ids)

        num_rel_documents = self.get('num_rel_documents', query_id)
        num_rel_documents_counted = num_rel_documents
        truncate = False
        if self.get('cutoff'):
            truncate = num_documents
            if num_rel_documents_counted > num_documents:
                num_rel_documents_counted = num_documents

        APs = {}
        for cluster_id in ids['clusters']:
            if cluster_id not in APs:
                APs[cluster_id] = {}
            for fqec in ids['equivalence_classes']:
                APs[cluster_id][fqec] = compute_AP(logger,
                                                   query_id,
                                                   num_rel_documents_counted,
                                                   responses,
                                                   cluster_id,
                                                   fqec,
                                                   truncate)

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
                    logger.record_event('ALIGNMENT_INFO', query_id, cluster_id, fqec)

        sum_average_precision = 0
        denominator_for_mean = len(ids['equivalence_classes'])
        if denominator_for_mean > num_clusters:
            denominator_for_mean = num_clusters
        for cluster_id in alignment.get('cluster_to_fqec'):
            sum_average_precision += alignment.get('cluster_to_fqec').get(cluster_id).get('AP')
        score = sum_average_precision/denominator_for_mean if denominator_for_mean != 0 else 0

        counts = {'average_precision': score,
                  'num_rel_documents': num_rel_documents,
                  'num_rel_documents_counted': num_rel_documents_counted}
        for field_name in [s.get('name') for s in self.get('printing_specs') if s.get('name').startswith('num_')]:
            counts[field_name] = counts[field_name] if field_name in counts else self.get(field_name, categorized_responses)
        return counts

    def get_entity_id(self, query_id):
        return str(self.get('queries_to_score').get(query_id).get('entity_id'))

    def get_equivalence_classes(self, the_query_id):
        equivalence_classes = set()
        entity_id = self.get('queries_to_score').get(the_query_id).get('entity_id')
        for query_id in self.get('queries_to_score'):
            if self.get('queries_to_score').get(query_id).get('entity_id') == entity_id:
                for entry in self.get('assessments').get(query_id).values():
                    if entry.get('assessment') == 'CORRECT':
                        equivalence_classes.add(entry.get('fqec'))
        return equivalence_classes

    def get_num_rel_documents(self, the_query_id):
        relevant_documents = set()
        entity_id = self.get('queries_to_score').get(the_query_id).get('entity_id')
        for query_id in self.get('queries_to_score'):
            if self.get('queries_to_score').get(query_id).get('entity_id') == entity_id:
                for entry in self.get('assessments').get(query_id).values():
                    if entry.get('assessment') == 'CORRECT':
                        relevant_documents.add(entry.get('docid'))
        return len(relevant_documents)

    def get_num_submitted(self, cr):
        key = 'SUBMITTED'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_valid(self, cr):
        key = 'VALID'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_invalid(self, cr):
        key = 'INVALID'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_notpooled(self, cr):
        key = 'NOTMETPOOLINGCRITERIA'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_pooled(self, cr):
        key = 'METPOOLINGCRITERIA'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_assessed(self, cr):
        num_pooled = self.get('num_pooled', cr)
        num_notassessed = self.get('num_notassessed', cr)
        return num_pooled - num_notassessed

    def get_num_notassessed(self, cr):
        key = 'NOTASSESSED'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_correct(self, cr):
        key = 'CORRECT'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_incorrect(self, cr):
        key = 'INCORRECT'
        policy = 'PRE_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_right(self, cr):
        key = 'RIGHT'
        policy = 'POST_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_wrong(self, cr):
        key = 'WRONG'
        policy = 'POST_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_num_ignored(self, cr):
        key = 'IGNORED'
        policy = 'POST_POLICY'
        return 0 if key not in cr.get(policy) else len(cr.get(policy).get(key))

    def get_entity_assessments(self, the_query_id):
        entity_assessments = Container(self.get('logger'))
        entity_id = self.get('entity_id', the_query_id)
        for query_id in self.get('queries_to_score'):
            if self.get('queries_to_score').get(query_id).get('entity_id') == entity_id:
                for key in self.get('assessments').get(query_id):
                    value = self.get('assessments').get(query_id).get(key)
                    if key not in entity_assessments:
                        entity_assessments.add(value, key)
                    elif value.get('assessment') != entity_assessments.get(key).get('assessment'):
                        self.record_event('CONFLICTING_ASSESSMENTS', key, query_id, entity_assessments.get(key).get('queryid'))
        return entity_assessments

    def get_query_responses(self, query_id):
        return self.get('responses').get('{path}/{query_id}.rq.tsv'.format(path=self.get('responses').get('path'),
                                                                           query_id=query_id))

    def score_responses(self):
        scores = []
        sum_average_precision = 0
        for query_id in self.get('queries_to_score'):
            entity_id = self.get('entity_id', query_id)
            counts = self.get('counts', query_id)
            sum_average_precision += counts['average_precision']
            score = AcrossDocumentsCoreferenceMetricScore(self.get('logger'),
                                                          run_id=self.get('run_id'),
                                                          query_id=query_id,
                                                          entity_id=entity_id,
                                                          **counts)
            scores.append(score)

        macro_counts = {'average_precision': sum_average_precision/len(self.get('queries_to_score'))}
        for field_name in [s.get('name') for s in self.get('printing_specs') if s.get('name').startswith('num_')]:
            macro_counts[field_name] = macro_counts[field_name] if field_name in macro_counts else ''
        macro_average_score = AcrossDocumentsCoreferenceMetricScore(self.get('logger'),
                                                                    run_id=self.get('run_id'),
                                                                    query_id='ALL-Macro',
                                                                    entity_id='Summary',
                                                                    summary=True,
                                                                    **macro_counts)

        scores_printer = ScorePrinter(self.logger, self.printing_specs, self.separator)
        for score in multisort(scores, (('entity_id', False),
                                        ('query_id', False))):
            scores_printer.add(score)
        scores_printer.add(macro_average_score)
        self.scores = scores_printer