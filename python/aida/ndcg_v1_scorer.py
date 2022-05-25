"""
AIDA class for Task3 scorer.
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

class OuterClaim(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
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
    AIDA class for Task3 scorer.
    """

    printing_specs = [{'name': 'condition',              'header': 'Condition',          'format': 's',    'justify': 'L'},
                      {'name': 'query_id',               'header': 'QueryID',            'format': 's',    'justify': 'L'},
                      {'name': 'claim_relation',         'header': 'ClaimRelation',      'format': 's',    'justify': 'L'},
                      {'name': 'run_id',                 'header': 'RunID',              'format': 's',    'justify': 'L'},
                      {'name': 'num_of_claims',          'header': 'NumSubmittedClaims', 'format': 's',    'justify': 'R'},
                      {'name': 'num_of_assessed_claims', 'header': 'NumAssessedClaims',  'format': 's',    'justify': 'R'},
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
            pool_claim_id = entry.get('claim_id_1')
            query_claim_id = entry.get('claim_id_2')
            claim_relation = entry.get('relation')
            if query.get('query_id') == query_claim_id and claim.get('claim_id') == pool_claim_id:
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
        if claim.get('assessed_claim_relation') == ranked_list_claim_relation:
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
        # otherwise, raise an error
        self.record_event('DEFAULT_CRITICAL_ERROR', 'Unable to determine claim relation correctness', self.get('code_location'))

    def get_claim_relations(self, score, scores):
        field_name = 'claim_relation'
        values = [score.get(field_name)]
        return values

    def get_claim_to_string(self, claim):
        specs = self.get('specs')
        claim_id = claim.get('claim_id')
        string = ['claim_id:{}'.format(claim_id)]
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
        correctness_code = {
            'Correct': True,
            'Inexact': True,
            'Wrong': False,
            'N/A': False
            }
        correctness = claim.get('data').get(fieldspec.get('fieldname')).get(component_id).get(fieldspec.get('overall_assessment_fieldname'))[0].get('correctness')
        if correctness == 'NIL':
            self.record_event('DEFAULT_WARNING', 'missing assessment for claim {}; using correct as default assessment'.format(claim.get('claim_id')))
            return True
        return correctness_code.get(correctness)

    def get_field_values(self, fieldspec, claim, correctness_requirement=False):
        # TODO: return only correct values if correctness_requirement=True otherwise return all values
        values = []
        data = claim.get('data').get(fieldspec.get('fieldname'))
        if data:
            fieldname, sub_fieldname = fieldspec.get('value_fieldnames').split(':')
            for component_id, entry in data.items():
                if (not correctness_requirement) or self.get('field_correctness', fieldspec, claim, component_id):
                    values.append(entry.get(fieldname)[0].get(sub_fieldname))
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
        gain = 1 if query_claim_frame is None else self.get('pairwise_novelty_score', claim_relation, the_claim, query_claim_frame)
        for i in range(rank):
            pairwise_novelty_score = self.get('pairwise_novelty_score', claim_relation, the_claim, ranked_claims[i])
            if pairwise_novelty_score == 0:
                return 0
            if gain > pairwise_novelty_score:
                gain = pairwise_novelty_score
        return gain

    def get_pairwise_novelty_score(self, claim_relation, the_claim, previous_claim):
        pairwise_novelty_scores = self.get('pairwise_novelty_scores')
        lookup_key = '-'.join([the_claim.get('claim_id'), previous_claim.get('claim_id')])
        claim_relation_correctness_scale = self.get('claim_relation_correctness', claim_relation, the_claim) if the_claim.get('condition') == 'Condition5' else 1
        if claim_relation_correctness_scale == 0:
            return 0
        if lookup_key not in pairwise_novelty_scores:
            score = 0
            if not self.get('required_fields_correctness', the_claim):
                return score
            specs = self.get('specs')
            for fieldspec in specs.values():
                field_pairwise_novelty_weight = self.get('field_pairwise_novelty_weight', fieldspec, the_claim, previous_claim, correctness_requirement=True)
                score += (fieldspec.get('weight') * field_pairwise_novelty_weight)
            pairwise_novelty_scores[lookup_key] = score
        score = pairwise_novelty_scores.get(lookup_key)
        return claim_relation_correctness_scale * score

    def get_field_pairwise_novelty_weight(self, fieldspec, the_claim, previous_claim, correctness_requirement=True, stack=[]):
        the_claim_field_values = self.get('field_values', fieldspec, the_claim, correctness_requirement=True)
        previous_claim_field_values = self.get('field_values', fieldspec, previous_claim, correctness_requirement=True)
        weight = 0
        if len(the_claim_field_values):
            weight = len(the_claim_field_values - previous_claim_field_values)
            if fieldspec.get('fieldname') == 'date':
                weight = self.get('field_pairwise_novelty_weight_date', the_claim_field_values, previous_claim_field_values)
            if weight == 0:
                if fieldspec.get('fieldname') in stack:
                    return 0
                dependent_fieldnames = fieldspec.get('dependents')
                for dependent_fieldname in dependent_fieldnames:
                    dependent_fieldspec = self.get('specs').get(dependent_fieldname)
                    dependent_field_novelty_weight = self.get('field_pairwise_novelty_weight', dependent_fieldspec, the_claim, previous_claim, correctness_requirement, list(stack).append(fieldspec.get('fieldname')))
                    if dependent_field_novelty_weight:
                        # TODO: determine the weight
                        weight = dependent_fieldspec.get('dependents_weight')
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

    def get_query_ids(self, score, scores):
        return ['ALL-Macro']

    def get_ranked_claims(self, query, ranked_list_claim_relation):
        def is_compatible(the_claim_relation, ranked_list_claim_relation):
            if the_claim_relation == ranked_list_claim_relation:
                return True
            compatible = {
                'nonrefuting': ['related', 'supporting'],
                'nonsupporting': ['related', 'refuting'],
                'ontopic': ['related', 'refuting', 'supporting']
                }
            if ranked_list_claim_relation in compatible and the_claim_relation in compatible.get(ranked_list_claim_relation):
                return True
            return False
        run_id = self.get('run_id')
        condition = query.get('condition')
        query_id = query.get('query_id')
        claims = []
        for claim in self.get('claims').get(query.get('condition')).get(query.get('query_id')).values():
            rank = claim.get('rank')
            run_claim_id = claim.get('claim_id')
            run_claim_relation = claim.get('claim_relation')
            # record if skipping the claim because it was not assessed
            if not claim.get('assessment'):
                self.record_event('SKIPPING_CLAIM_NOT_ASSESSED', run_id, condition, query_id, ranked_list_claim_relation, rank, run_claim_id)
                continue
            # record if skipping the claim because the claim relation is not compatible to the ranked list claim relation
            if not is_compatible(run_claim_relation, ranked_list_claim_relation):
                self.record_event('SKIPPING_CLAIM_INCOMPATIBLE', run_id, condition, query_id, ranked_list_claim_relation, rank, run_claim_id, run_claim_relation)
                continue
            assessed_claim = self.get('assessed_claim', claim)
            assessed_claim_relation = self.get('assessed_claim_relation', query, assessed_claim)
            assessed_claim.set('assessed_claim_relation', assessed_claim_relation)
            assessed_claim.set('rank', claim.get('rank'))
            claims.append(assessed_claim)
        return sorted(claims, key = lambda claim: claim.get('rank'))

    def get_required_fields_correctness(self, claim):
        specs = self.get('specs')
        for fieldspec in specs.values():
            if fieldspec.get('required'):
                if not self.get('field_correctness', fieldspec, claim):
                    return False
        return True

    def get_score(self, query, claim_relation, ranked_claims):
        DCG = self.get('DCG', query, claim_relation, ranked_claims)
        IDCG, num_assessed_claims = self.get('IDCG', query, claim_relation)
        nDCG = DCG/IDCG if IDCG > 0 else 0
        run_id = self.get('run_id')
        condition = query.get('condition')
        query_id = query.get('query_id')
        self.record_event('SCORE_VALUE', run_id, condition, query_id, claim_relation, 'DCG', DCG)
        self.record_event('SCORE_VALUE', run_id, condition, query_id, claim_relation, 'IDCG', IDCG)
        self.record_event('SCORE_VALUE', run_id, condition, query_id, claim_relation, 'nDCG', nDCG)
        return nDCG, num_assessed_claims

    def get_specs(self):
        return {
            'claimTemplate': {
                'component': False,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimTemplate',
                'importance_rank': 1,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'value',
                'required': True,
                'value_fieldnames': 'value:value',
                'weight': 1,
                },
            'claimEpistemic': {
                'component': False,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimEpistemic',
                'importance_rank': 2,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'polarity',
                'required': True,
                'value_fieldnames': 'polarity:value',
                'weight': 1,
                },
            'xVariable': {
                'component': True,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'xVariable',
                'importance_rank': 3,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': True,
                'value_fieldnames': 'ec_id:correctness',
                'weight': 1,
                },
            'claimer': {
                'component': True,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimer',
                'importance_rank': 4,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': True,
                'value_fieldnames': 'ec_id:correctness',
                'weight': 1,
                },
            'claimerAffiliation': {
                'component': True,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimerAffiliation',
                'importance_rank': 5,
                'max_num_of_values': 3,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'value_fieldnames': 'ec_id:correctness',
                'weight': 1,
                },
            'claimLocation': {
                'component': True,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimLocation',
                'importance_rank': 6,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'value_fieldnames': 'ec_id:correctness',
                'weight': 1,
                },
            'claimMedium': {
                'component': True,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimMedium',
                'importance_rank': 7,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'value_fieldnames': 'ec_id:correctness',
                'weight': 1,
                },
            'date': {
                'component': True,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'date',
                'importance_rank': 8,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'range',
                'required': False,
                'value_fieldnames': 'range:value',
                'weight': 1,
                },
            'claimSentiment': {
                'component': False,
                'dependents': [],
                'dependents_weight': 1,
                'fieldname': 'claimSentiment',
                'importance_rank': 9,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'value',
                'required': False,
                'value_fieldnames': 'value:value',
                'weight': 1,
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
            DCG += (gain/math.log2(rank+2))
        return DCG

    def get_IDCG(self, query, claim_relation):
        def get_outer_claim(claim, rank):
            outer_claim_filename = claim.get('outer_claim').get('filename')
            path = os.path.dirname(outer_claim_filename)
            claim_id = os.path.basename(outer_claim_filename).replace('-outer-claim.tab', '')
            outer_claim = OuterClaim(self.get('logger'),
                                     condition=claim.get('condition'),
                                     query_id=claim.get('query_id'),
                                     path=path,
                                     claim_id=claim_id,
                                     run_claim_path=claim.get('path'),
                                     run_claim_id=claim.get('claim_id'),
                                     run_claim_relation=claim_relation,
                                     run_claim_rank=rank)
            return outer_claim
        compatible_claim_relations = {
            'nonrefuting': ['supporting', 'related'],
            'nonsupporting': ['refuting', 'related'],
            'ontopic': ['supporting', 'related', 'refuting'],
            'refuting': ['refuting'],
            'related': ['related'],
            'supporting': ['supporting'],
            }
        related_claim_ids = set()
        for entry in self.get('assessments').get('cross_claim_relations'):
            if entry.get('relation') in compatible_claim_relations.get(claim_relation):
                claim_id_1 = entry.get('claim_id_1')
                claim_id_2 = entry.get('claim_id_2')
                if claim_id_1 == query.get('query_id'):
                    related_claim_ids.add(claim_id_2)
                elif claim_id_2 == query.get('query_id'):
                    related_claim_ids.add(claim_id_1)
        claims_set = set()
        rank = 1
        for claim in self.get('assessments').get('claims').values():
            if claim.get('claim_id') in related_claim_ids:
                outer_claim = get_outer_claim(claim, rank)
                outer_claim.set('assessed_claim_relation', self.get('assessed_claim_relation', query, outer_claim))
                claims_set.add(outer_claim)
                rank += 1
        ideal_claims_ranking = []
        while(len(claims_set)):
            best_next_claim = None
            max_gain_of_next_claim = None
            for the_claim in claims_set:
                test_ranked_list = list(ideal_claims_ranking[:])
                test_ranked_list.append(the_claim)
                rank = len(test_ranked_list) - 1
                gain_of_the_claim = self.get('gain', query, claim_relation, test_ranked_list, rank)
                if max_gain_of_next_claim is None or gain_of_the_claim > max_gain_of_next_claim:
                    max_gain_of_next_claim = gain_of_the_claim
                    best_next_claim = the_claim
            ideal_claims_ranking.append(best_next_claim)
            claims_set.remove(best_next_claim)
        IDCG = self.get('DCG', query, claim_relation, ideal_claims_ranking, ideal=True)
        return IDCG, len(ideal_claims_ranking)

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
                claim = OuterClaim(self.get('logger'),
                                   condition='Condition5',
                                   path='{}/ARF-output/Condition5/{}'.format(self.get('query_claim_frames_dir'), query_id),
                                   claim_id=query_id)
                claim.set('rank', -1000000)
                query.set('query_claim_frame', claim)
                self.record_event('CLAIM_STRING', self.get('claim_to_string', claim))

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
                ranked_claims = self.get('ranked_claims', query, claim_relation)
                ndcg, num_assessed_claims = self.get('score', query, claim_relation, ranked_claims)
                score = NDCGScore(logger=self.logger,
                                  run_id=self.get('run_id'),
                                  condition=condition,
                                  query_id=query_id,
                                  claim_relation=claim_relation,
                                  num_of_claims=str(len(ranked_claims)),
                                  num_of_assessed_claims=str(num_assessed_claims),
                                  ndcg=ndcg
                                  )
                scores.append(score)
                for claim in ranked_claims:
                    claim_id = claim.get('claim_id')
                    if claim_id not in printed:
                        self.record_event('CLAIM_STRING', self.get('claim_to_string', claim))
                        printed.add(claim_id)
        scores_printer = ScorePrinter(self.logger, self.printing_specs, aggregate_types=['ALL-Macro'])
        for score in multisort(scores, (('condition', False),
                                        ('query_id', False),
                                        ('claim_relation', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, NDCGScore)
        self.scores = scores_printer