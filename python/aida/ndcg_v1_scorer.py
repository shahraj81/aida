"""
AIDA class for Task3 NDCG scorer V1.

V1 refers to the variant where all the submitted claims are considered for scoring regardless of the pooling depth.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "20 April 2022"

from aida.container import Container
from aida.file_header import FileHeader
from aida.file_handler import FileHandler
from aida.ndcg_score import NDCGScore
from aida.object import Object
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.task3_pool import Claim
from aida.utility import multisort

from datetime import datetime
import math
import os

def normalize_claim_relation(relation):
    apply_patch = {
        'refuted_by': 'refuting',
        'related': 'related',
        'supported_by': 'supporting'
        }
    return apply_patch.get(relation)

class OuterClaim(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        self.is_query_claim_frame = False
        for key in kwargs:
            self.set(key, kwargs[key])
        self.data = {}
        self.load()

    def add(self, component_type, idnum, fieldname, value, correctness):
        self.get('data').setdefault(component_type, {}).setdefault(idnum, {}).setdefault(fieldname, []).append({'value': value,
                                                                                                        'correctness': correctness})

    def load(self):
        filename = os.path.join(self.get('path'), '{}-outer-claim.tab'.format(self.get('claim_id')))
        for entry in FileHandler(self.get('logger'), filename):
            self.add(entry.get('component_type'),
                     entry.get('id'),
                     entry.get('fieldname'),
                     entry.get('value'),
                     entry.get('correctness'))

class NDCGScorerV1(Scorer):
    """
    AIDA class for Task3 NDCG scorer V1.

    V1 refers to the variant where all the submitted claims are considered for scoring regarless of the pooling depth.
    """

    printing_specs = [{'name': 'condition',              'header': 'Condition',          'format': 's',    'justify': 'L'},
                      {'name': 'query_id',               'header': 'QueryID',            'format': 's',    'justify': 'L'},
                      {'name': 'claim_relation',         'header': 'ClaimRelation',      'format': 's',    'justify': 'L'},
                      {'name': 'run_id',                 'header': 'RunID',              'format': 's',    'justify': 'L'},
                      {'name': 'num_of_claims',          'header': 'NumAssessedClaims',  'format': 's',    'justify': 'R'},
                      {'name': 'ground_truth',           'header': 'GT',                 'format': 's',    'justify': 'R'},
                      {'name': 'ndcg',                   'header': 'NDCG',               'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_assessed_claim(self, claim):
        outer_claim_filename = claim.get('assessment').get('outer_claim').get('filename')
        path = os.path.dirname(outer_claim_filename)
        claim_id = os.path.basename(outer_claim_filename).replace('-outer-claim.tab', '')
        outer_claim = OuterClaim(self.get('logger'),
                                 condition=claim.get('condition'),
                                 query_id=claim.get('query_id'),
                                 path=path,
                                 claim_id=claim_id,
                                 run_claim_path=claim.get('path'),
                                 run_claim_id=claim.get('claim_id'),
                                 run_claim_relation=claim.get('claim_relation'),
                                 run_claim_rank=claim.get('rank'))
        return outer_claim

    def get_assessed_claim_relation(self, query, claim):
        claim_relation = None
        for entry in self.get('assessments').get('cross_claim_relations'):
            system_claim_id = entry.get('system_claim_id')
            query_claim_id = entry.get('query_claim_id')
            claim_relation = normalize_claim_relation(entry.get('relation'))
            if query.get('query_id') == query_claim_id and claim.get('claim_id') == system_claim_id:
                return claim_relation
        return claim_relation

    def get_claim_relation_correctness(self, ranked_list_claim_relation, claim):
        """
        In order to have correct claim relation, the claim frame must always be on topic.

        Furthermore, when the ranked list is restricted to one of {Supporting, Refuting, Related}
        in Condition 5, the relation tagged by the system must match the relation manually
        assigned by the assessor.

        When the ranked list is restricted to one of {Non-refuting, Non-supporting}, the relation
        tagged by the system must be compatible with the relation manually assigned by the assessor;
        however, compatible but non-matching relation tags result in partial credit (in particular,
        the claim frame gets only half credit if the system tag is “related” but the gold tag is
        “supporting” in List 5 or “refuting” in List 6).
        """
        # LDC will not provide cross claim relation for incorrect claims, return 0
        if claim.get('assessed_claim_relation') is None:
            return 0
        # if assessed cross claim relations from LDC is not one of the following, raise an error
        if claim.get('assessed_claim_relation') not in ['related', 'supporting', 'refuting']:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'Unexpected value', claim.get('assessed_claim_relation'))
            return 0
        # if claim relations match, return 1
        if claim.get('assessed_claim_relation') == ranked_list_claim_relation or ranked_list_claim_relation == 'ontopic':
            return 1
        # if claim relations did not match but are compatible return 0.5
        compatible_claim_relations = {
            'nonrefuting': ['supporting', 'related'],
            'nonsupporting': ['refuting', 'related'],
            'ontopic': ['supporting', 'related', 'refuting']
            }
        if ranked_list_claim_relation in compatible_claim_relations:
            if claim.get('assessed_claim_relation') in compatible_claim_relations.get(ranked_list_claim_relation):
                return 0.5
        return 0

    def get_claim_relations(self, score, scores):
        field_name = 'claim_relation'
        values = [score.get(field_name)]
        return values

    def get_claim_to_string(self, query, claim):
        specs = self.get('specs')
        claim_id = claim.get('claim_id')
        query_claim_frame_id = None
        if claim.get('is_query_claim_frame') and query.get('condition') == 'Condition5':
            if claim.get('query_id') != query.get('query_id'):
                self.record_event('DEFAULT_CRITICAL_ERROR', 'unexpected query_id')
            query_claim_frame_id = claim.get('query_id')
        string = ['claim_id:{}'.format(claim_id),
                  'is_query_claim_frame:{}'.format(claim.get('is_query_claim_frame')),
                  'query_claim_frame_id:{}'.format(query_claim_frame_id)]
        for fieldspec in specs.values():
            field_name = fieldspec.get('fieldname')
            claim_field_values = self.get('field_values', fieldspec, claim)
            if len(claim_field_values) == 0:
                claim_field_values = set(['None'])
            string.append('{}:{}'.format(field_name, ','.join(claim_field_values)))
        return '::'.join(string)

    def get_conditions(self, score, scores):
        field_name = 'condition'
        values = [score.get(field_name)]
        return values

    def get_field_correctness(self, fieldspec, claim, component_id='1'):
        if claim.get('is_query_claim_frame'):
            return True
        correctness_code = {
            'Correct': True,
            'Incorrect': False,
            'Inexact': True,
            'Wrong': False,
            'N/A': False,
            }
        correctness = claim.get('data').get(fieldspec.get('fieldname')).get(component_id).get(fieldspec.get('overall_assessment_fieldname'))[0].get('correctness')
        if correctness not in correctness_code:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'Unexpected value \'{}\' for correctness'.format(correctness))
        return correctness_code.get(correctness)

    def get_field_values(self, fieldspec, claim, correctness_requirement=False):
        def normalize(value):
            mapping = {
                'EpistemicTrueCertain': 'True',
                'EpistemicTrueUncertain': 'True',
                'EpistemicFalseCertain': 'False',
                'EpistemicFalseUncertain': 'False',
                'EpistemicUnknown': 'Unknown'
                }
            return mapping[value] if value in mapping else value
        values = []
        if claim is not None:
            data = claim.get('data').get(fieldspec.get('fieldname'))
            if data:
                fieldname, sub_fieldname = fieldspec.get('value_fieldnames').split(':')
                for component_id, entry in data.items():
                    field_correctness = self.get('field_correctness', fieldspec, claim, component_id)
                    fieldvalue = normalize(entry.get(fieldname)[0].get(sub_fieldname))
                    self.record_event('CLAIM_FIELD_CORRECTNESS', claim.get('claim_id'), fieldspec.get('fieldname'), fieldvalue, field_correctness)
                    if (not correctness_requirement) or field_correctness:
                        values.append(fieldvalue)
        retVals = set()
        max_num_of_values = fieldspec.get('max_num_of_values')
        for value in sorted(values):
            retVals.add(value)
            max_num_of_values -= 1
            if not max_num_of_values: break
        return retVals

    def get_gain(self, query, claim_relation, ranked_claims, rank):
        query_claim_frame = query.get('query_claim_frame')
        the_claim = ranked_claims[rank]
        gain = self.get('pairwise_novelty_score', query, claim_relation, the_claim, query_claim_frame)
        for i in range(rank):
            pairwise_novelty_score = self.get('pairwise_novelty_score', query, claim_relation, the_claim, ranked_claims[i])
            if pairwise_novelty_score == 0:
                return 0
            if gain > pairwise_novelty_score:
                gain = pairwise_novelty_score
        return gain

    def get_pairwise_novelty_score(self, query, claim_relation, the_claim, previous_claim):
        pairwise_novelty_scores = self.get('pairwise_novelty_scores')
        lookup_key = '-'.join([the_claim.get('claim_id'), previous_claim.get('claim_id') if previous_claim else 'None'])
        claim_relation_correctness_scale = self.get('claim_relation_correctness', claim_relation, the_claim) if query.get('condition') == 'Condition5' else 1
        self.record_event('CLAIM_RELATION_CORRECTNESS', query.get('query_id'), the_claim.get('claim_id'), claim_relation, claim_relation_correctness_scale)
        if claim_relation_correctness_scale == 0:
            return 0
        if lookup_key not in pairwise_novelty_scores:
            score = 0
            required_fields_correctness = self.get('required_fields_correctness', the_claim)
            self.record_event('CLAIM_CORRECTNESS', the_claim.get('claim_id'), required_fields_correctness)
            if not required_fields_correctness:
                return score
            specs = self.get('specs')
            for fieldspec in specs.values():
                field_pairwise_novelty_weight = self.get('field_pairwise_novelty_weight', fieldspec, the_claim, previous_claim, correctness_requirement=True)
                score += (fieldspec.get('weight') * field_pairwise_novelty_weight)
            pairwise_novelty_scores[lookup_key] = score
        score = pairwise_novelty_scores.get(lookup_key)
        return claim_relation_correctness_scale * score

    def get_field_pairwise_novelty_weight(self, fieldspec, the_claim, previous_claim, correctness_requirement=True, dependents_stack=[]):
        the_claim_field_values = self.get('field_values', fieldspec, the_claim, correctness_requirement=True)
        previous_claim_field_values = self.get('field_values', fieldspec, previous_claim, correctness_requirement=True)
        weight = 0
        if len(the_claim_field_values):
            weight = len(the_claim_field_values - previous_claim_field_values)
            if fieldspec.get('fieldname') == 'date':
                weight = self.get('field_pairwise_novelty_weight_date', the_claim_field_values, previous_claim_field_values)
            if weight == 0 or fieldspec.get('max_num_of_values') > 1:
                if fieldspec.get('fieldname') in dependents_stack:
                    return 0
                dependent_fieldnames = fieldspec.get('dependents')
                for dependent_fieldname in dependent_fieldnames:
                    dependent_fieldspec = self.get('specs').get(dependent_fieldname)
                    updated_dependents_stack = list(dependents_stack[:])
                    updated_dependents_stack.append(fieldspec.get('fieldname'))
                    dependent_field_novelty_weight = self.get('field_pairwise_novelty_weight', dependent_fieldspec, the_claim, previous_claim, correctness_requirement, updated_dependents_stack)
                    if dependent_field_novelty_weight:
                        weight = len(the_claim_field_values)
                        break
        return weight

    def get_field_pairwise_novelty_weight_date(self, the_claim_field_values, previous_claim_field_values):
        def different(date_string_1, date_string_2):
            different = False
            if date_string_1 == '--' and date_string_2 == '--':
                different = False
            elif date_string_1 == '--' or date_string_2 == '--':
                different = True
            else:
                date1 = datetime.fromisoformat(date_string_1)
                date2 = datetime.fromisoformat(date_string_2)
                delta = date1 - date2 if date1 > date2 else date2 - date1
                if delta.days > 30:
                    different = True
            return different
        def parse(date_range):
            start, end = [e.replace('(','').replace(')','') for e in date_range.split(')-(')]
            start_after, start_before = start.split(',')
            end_after, end_before = end.split(',')
            return [start_after, start_before, end_after, end_before]
        weight = len(the_claim_field_values)
        if len(previous_claim_field_values):
            if len(the_claim_field_values) != 1 and len(previous_claim_field_values) != 1:
                self.record_event('DEFAULT_CRITIAL_ERROR', 'unexpected number of date field values')
            the_claim_times = parse(list(the_claim_field_values)[0])
            previous_claim_times = parse(list(previous_claim_field_values)[0])
            weight = 0
            for i in range(4):
                if different(the_claim_times[i], previous_claim_times[i]):
                    weight = 1
        return weight

    def get_pooling_depth(self, query, claim_relation):
        query_claim_relation_pooling_depth = None
        for query_claim_relation_and_depth in query.get('depth').split(','):
            query_claim_relation, query_pooling_depth = query_claim_relation_and_depth.split(':')
            if query_claim_relation == claim_relation:
                query_claim_relation_pooling_depth = query_pooling_depth
                break
        if query_claim_relation_pooling_depth is None:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'pooling depth is None')
        return int(query_claim_relation_pooling_depth)

    def get_query_ids(self, score, scores):
        return ['ALL-Macro']

    def get_ranked_claims(self, query, claim_relation, ranked_list_type):
        ranked_claims = None
        if ranked_list_type == 'submitted':
            ranked_claims = self.get('ranked_claims_submitted', query, claim_relation)
        elif ranked_list_type == 'ideal':
            ranked_claims = self.get('ranked_claims_ideal', query, claim_relation)
        rank = 1
        for claim in ranked_claims:
            self.record_event('RANKED_CLAIMS', ranked_list_type, query.get('query_id'), claim_relation, rank, claim.get('claim_id'))
            rank += 1
        return ranked_claims

    def get_ranked_claims_ideal(self, query, claim_relation, LIMITED_TO_POOLING_DEPTH=False):
        def condition6_filter(queries_to_score, query, claim):
            if query.get('condition') != 'Condition6':
                return False
            for claim_mapping in claim.get('mappings'):
                claim_mapping_query_id = claim_mapping.get('query_id')
                claim_mapping_query_topic_id = queries_to_score.get(claim_mapping_query_id).get('topic_id')
                if query.get('topic_id') == claim_mapping_query_topic_id:
                    return True
            return False
        def get_outer_claim(query_id, claim, rank):
            def is_query_claim_frame(claim):
                for claim_mapping in claim.get('mappings'):
                    if claim_mapping.get('run_id') == 'query_claim_frames':
                        return True
                return False
            outer_claim_filename = claim.get('outer_claim').get('filename')
            path = os.path.dirname(outer_claim_filename)
            claim_id = os.path.basename(outer_claim_filename).replace('-outer-claim.tab', '')
            outer_claim = OuterClaim(self.get('logger'),
                                     conditions=claim.get('conditions'),
                                     query_id=query_id,
                                     path=path,
                                     claim_id=claim_id,
                                     is_query_claim_frame=is_query_claim_frame(claim),
                                     rank=-1000000,
                                     run_claim_path=claim.get('path'),
                                     run_claim_id=claim.get('claim_id'),
                                     run_claim_relation=claim_relation,
                                     run_claim_rank=rank)
            return outer_claim
        def on_same_topic(query_id_1, query_id_2):
            def get_topic_id(query_id):
                return self.get('queries_to_score').get(query_id).get('topic_id')
            return get_topic_id(query_id_1) == get_topic_id(query_id_2)
        compatible_claim_relations = {
            'nonrefuting': ['supporting', 'related'],
            'nonsupporting': ['refuting', 'related'],
            'ontopic': ['supporting', 'related', 'refuting'],
            'refuting': ['refuting'],
            'related': ['related'],
            'supporting': ['supporting'],
            }
        identical_claims = set()
        for entry in self.get('assessments').get('cross_claim_relations'):
            if entry.get('relation') == 'identical' and entry.get('query_claim_id') == query.get('query_id'):
                identical_claims.add(entry.get('system_claim_id'))
        related_claim_ids = set()
        for entry in self.get('assessments').get('cross_claim_relations'):
            if entry.get('system_claim_id') in identical_claims: continue
            cross_claim_relation = normalize_claim_relation(entry.get('relation'))
            if cross_claim_relation in compatible_claim_relations.get(claim_relation):
                query_claim_id = entry.get('query_claim_id')
                if claim_relation == 'ontopic' and on_same_topic(query_claim_id, query.get('query_id')):
                    related_claim_ids.add(entry.get('system_claim_id'))
                elif claim_relation != 'ontopic' and query_claim_id == query.get('query_id'):
                    related_claim_ids.add(entry.get('system_claim_id'))
        claims_set = set()
        rank = 1
        for claim in self.get('assessments').get('claims').values():
            if claim.get('claim_id') in related_claim_ids or condition6_filter(self.get('queries_to_score'), query, claim):
                outer_claim = get_outer_claim(query.get('query_id'), claim, rank)
                outer_claim.set('assessed_claim_relation', self.get('assessed_claim_relation', query, outer_claim))
                if self.get('required_fields_correctness', outer_claim):
                    claims_set.add(outer_claim)
                    rank += 1
        ideal_claims_ranking = []
        sorted_claims_set = list(sorted(claims_set, key=lambda c: c.get('claim_id')))
        while(len(sorted_claims_set)):
            best_next_claim = None
            max_gain_of_next_claim = None
            for the_claim in sorted_claims_set:
                test_ranked_list = list(ideal_claims_ranking[:])
                test_ranked_list.append(the_claim)
                rank = len(test_ranked_list) - 1
                gain_of_the_claim = self.get('gain', query, claim_relation, test_ranked_list, rank)
                if max_gain_of_next_claim is None or gain_of_the_claim > max_gain_of_next_claim:
                    max_gain_of_next_claim = gain_of_the_claim
                    best_next_claim = the_claim
            ideal_claims_ranking.append(best_next_claim)
            sorted_claims_set.remove(best_next_claim)
        return ideal_claims_ranking[0:self.get('pooling_depth', query, claim_relation)] if LIMITED_TO_POOLING_DEPTH else ideal_claims_ranking

    def get_ranked_claims_submitted(self, query, claim_relation, LIMITED_TO_POOLING_DEPTH=False):
        def is_compatible(the_claim_relation, claim_relation):
            if the_claim_relation == claim_relation:
                return True
            compatible = {
                'nonrefuting': ['related', 'supporting'],
                'nonsupporting': ['related', 'refuting'],
                'ontopic': ['related', 'refuting', 'supporting']
                }
            if claim_relation in compatible and the_claim_relation in compatible.get(claim_relation):
                return True
            return False
        run_id = self.get('run_id')
        condition = query.get('condition')
        query_id = query.get('query_id')
        claims = []
        if self.get('claims').get(query.get('condition')).get(query.get('query_id')) is not None:
            for claim in self.get('claims').get(query.get('condition')).get(query.get('query_id')).values():
                rank = claim.get('rank')
                run_claim_id = claim.get('claim_id')
                run_claim_relation = claim.get('claim_relation')
                # record if skipping the claim because it was not assessed
                if not claim.get('assessment'):
                    self.record_event('SKIPPING_CLAIM_NOT_ASSESSED', run_id, condition, query_id, claim_relation, rank, run_claim_id)
                    continue
                # record if skipping the claim because the claim relation is not compatible to the ranked list claim relation
                if not is_compatible(run_claim_relation, claim_relation):
                    self.record_event('SKIPPING_CLAIM_INCOMPATIBLE', run_id, condition, query_id, claim_relation, rank, run_claim_id, run_claim_relation)
                    continue
                assessed_claim = self.get('assessed_claim', claim)
                assessed_claim_relation = self.get('assessed_claim_relation', query, assessed_claim)
                assessed_claim.set('assessed_claim_relation', assessed_claim_relation)
                assessed_claim.set('rank', claim.get('rank'))
                claims.append(assessed_claim)
        sorted_claims = sorted(claims, key = lambda claim: claim.get('rank'))
        return sorted_claims[0:self.get('pooling_depth', query, claim_relation)] if LIMITED_TO_POOLING_DEPTH else sorted_claims

    def get_required_fields_correctness(self, claim):
        specs = self.get('specs')
        for fieldspec in specs.values():
            if fieldspec.get('required'):
                if not self.get('field_correctness', fieldspec, claim):
                    return False
        return True

    def get_score(self, query, claim_relation, ranked_claims_submitted, ranked_claims_ideal):
        DCG = self.get('DCG', query, claim_relation, ranked_claims_submitted, ideal=False)
        IDCG = self.get('DCG', query, claim_relation, ranked_claims_ideal, ideal=True)
        nDCG = DCG/IDCG if IDCG > 0 else 0
        if nDCG > 1:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'nDCG > 1')
        run_id = self.get('run_id')
        condition = query.get('condition')
        query_id = query.get('query_id')
        self.record_event('SCORE_VALUE', run_id, condition, query_id, claim_relation, 'DCG', DCG)
        self.record_event('SCORE_VALUE', run_id, condition, query_id, claim_relation, 'IDCG', IDCG)
        self.record_event('SCORE_VALUE', run_id, condition, query_id, claim_relation, 'nDCG', nDCG)
        return nDCG

    def get_specs(self):
        return {
            'claimTemplate': {
                'component': False,
                'dependents': ['claimEpistemic', 'xVariable'],
                'fieldname': 'claimTemplate',
                'importance_rank': 1,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'value',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'value:value',
                'weight': 32,
                },
            'claimEpistemic': {
                'component': False,
                'dependents': ['claimTemplate', 'xVariable'],
                'fieldname': 'claimEpistemic',
                'importance_rank': 2,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'polarity',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'polarity:value',
                'weight': 32,
                },
            'xVariable': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic'],
                'fieldname': 'xVariable',
                'importance_rank': 3,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 32,
                },
            'claimer': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable'],
                'fieldname': 'claimer',
                'importance_rank': 4,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 16,
                },
            'claimerAffiliation': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimerAffiliation',
                'importance_rank': 5,
                'max_num_of_values': 3,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 4,
                },
            'claimLocation': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimLocation',
                'importance_rank': 6,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 1,
                },
            'claimMedium': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimMedium',
                'importance_rank': 7,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 1,
                },
            'date': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'date',
                'importance_rank': 8,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'range',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'range:value',
                'weight': 1,
                },
            'claimSentiment': {
                'component': False,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimSentiment',
                'importance_rank': 9,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'value',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'value:value',
                'weight': 0.5,
                },
            }

    def get_DCG(self, query, claim_relation, ranked_claims, ideal=False):
        run_id = self.get('run_id')
        query_id = query.get('query_id')
        condition = query.get('condition')
        ranking_type = 'submitted' if not ideal else 'ideal'
        DCG = 0
        for rank in range(len(ranked_claims)):
            gain = self.get('gain', query, claim_relation, ranked_claims, rank)
            run_claim_id = ranked_claims[rank].get('run_claim_id')
            pool_claim_id = ranked_claims[rank].get('claim_id')
            self.record_event('GAIN_VALUE', ranking_type, run_id, condition, query_id, claim_relation, rank, run_claim_id, pool_claim_id, gain)
            discounted_gain = gain/math.log2(rank+2)
            DCG += discounted_gain
        return DCG

    def aggregate_scores(self, scores, score_class):
        aggregates = {}
        for score in scores.values():
            conditions = self.get('conditions', score, scores)
            query_ids = self.get('query_ids', score, scores)
            claim_relations = self.get('claim_relations', score, scores)
            for condition in conditions:
                for query_id in query_ids:
                    for claim_relation in claim_relations:
                        group_by = ','.join([condition, query_id, claim_relation])
                        if group_by not in aggregates:
                            aggregates[group_by] = score_class(self.get('logger'),
                                                               aggregate=True,
                                                               condition=condition,
                                                               query_id=query_id,
                                                               claim_relation=claim_relation,
                                                               run_id=self.get('run_id'),
                                                               num_of_claims='',
                                                               summary=True,
                                                               elements=Container(self.get('logger')))
                        aggregate_scores = aggregates[group_by]
                        aggregate_scores.get('elements').add(score)
        for score in sorted(aggregates.values(), key=self.order):
            scores.add(score)

    def load_query_claim_frames(self):
        for query_id, query in self.get('queries_to_score').items():
            if query.get('condition') == 'Condition5':
                claim_mappings = self.get('assessments').get('claim_mappings').get('claim_mappings', query_id=query_id, run_claim_id=query_id)
                pool_claim_id = claim_mappings[0].get('pool_claim_uid')
                path = self.get('assessments').get('claims').get(pool_claim_id).get('path')
                claim = OuterClaim(self.get('logger'),
                                   conditions=['Condition5'],
                                   claim_id=pool_claim_id,
                                   is_query_claim_frame=True,
                                   path=path,
                                   query_id=query_id,
                                   query=query,
                                   rank=-1000000)
                query.set('query_claim_frame', claim)
                self.record_event('CLAIM_STRING', self.get('claim_to_string', query, claim))

    def load_responses(self):
        logger = self.get('logger')
        claims = {}
        for root, _, files in os.walk(os.path.join(self.get('responses_dir'), 'ARF-output')):
            for filename in files:
                if not filename.endswith('-outer-claim.tab'): continue
                condition = os.path.basename(os.path.dirname(root))
                query_id = os.path.basename(root)
                claim_id = str(filename).replace('-outer-claim.tab','')
                claim = Claim(self.get('logger'),
                              condition=condition,
                              query_id=query_id,
                              path=root,
                              claim_id=claim_id)
                claims.setdefault(condition, {}).setdefault(query_id,{})[claim_id] = claim
        headers = {
            'Condition5': ['?query_claim_id', '?claim_id', '?rank', '?claim_relation'],
            'Condition6': ['?query_topic', '?claim_id', '?rank'],
            'Condition7': ['?query_topic', '?claim_id', '?rank'],
            }
        for root, _, files in os.walk(os.path.join(self.get('responses_dir'), 'SPARQL-AUGMENTED-output')):
            for filename in files:
                if not filename.endswith('ranking.tsv'): continue
                condition = os.path.basename(os.path.dirname(root))
                query_id = os.path.basename(root)
                ranking_filename = os.path.join(root, filename)
                header = FileHeader(logger, header_line='\t'.join(headers.get(condition)))
                for entry in FileHandler(logger, ranking_filename, header=header):
                    claim = claims.get(condition).get(query_id).get(entry.get('?claim_id'))
                    claim.set('rank_entry', entry)
                    claim.set('rank', int(entry.get('?rank')))
                    claim.set('claim_relation', entry.get('?claim_relation') if condition=='Condition5' else 'ontopic')
                    claim.set('assessment', self.get('assessments').get('assessment', 'task3', claim=claim, run_id=self.get('run_id')))
        self.claims = claims

    def order(self, k):
        condition, claim_relation = k.get('condition'), k.get('claim_relation')
        return '{}:{}'.format(condition, claim_relation)

    def score_responses(self):
        self.load_responses()
        self.load_query_claim_frames()
        self.pairwise_novelty_scores = {}
        scores = []
        claim_relations = {
            'Condition5': ['ontopic', 'related', 'refuting', 'supporting', 'nonsupporting', 'nonrefuting'],
            'Condition6': ['ontopic'],
            'Condition7': ['ontopic']
            }
        queries_to_score = self.get('queries_to_score')
        printed = set()
        for query_id, query in queries_to_score.items():
            condition = query.get('condition')
            for claim_relation in claim_relations.get(condition):
                ranked_claims_submitted = self.get('ranked_claims', query, claim_relation, ranked_list_type='submitted')
                ranked_claims_ideal = self.get('ranked_claims', query, claim_relation, ranked_list_type='ideal')
                ndcg = self.get('score', query, claim_relation, ranked_claims_submitted, ranked_claims_ideal)
                score = NDCGScore(logger=self.logger,
                                  run_id=self.get('run_id'),
                                  condition=condition,
                                  query_id=query_id,
                                  claim_relation=claim_relation,
                                  num_of_claims=str(len(ranked_claims_submitted)),
                                  ground_truth=str(len(ranked_claims_ideal)),
                                  ndcg=ndcg
                                  )
                scores.append(score)
                ranked_claims = ranked_claims_submitted.copy()
                ranked_claims.extend(ranked_claims_ideal)
                for claim in ranked_claims:
                    claim_id = claim.get('claim_id')
                    if claim_id not in printed:
                        self.record_event('CLAIM_STRING', self.get('claim_to_string', query, claim))
                        printed.add(claim_id)
        scores_printer = ScorePrinter(self.logger, self.printing_specs, aggregate_types=['ALL-Macro'])
        for score in multisort(scores, (('condition', False),
                                        ('query_id', False),
                                        ('claim_relation', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, NDCGScore)
        self.scores = scores_printer