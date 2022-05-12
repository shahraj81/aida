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

    printing_specs = [{'name': 'condition',      'header': 'Condition',     'format': 's',    'justify': 'L'},
                      {'name': 'query_id',       'header': 'QueryID',       'format': 's',    'justify': 'L'},
                      {'name': 'claim_relation', 'header': 'ClaimRelation', 'format': 's',    'justify': 'L'},
                      {'name': 'run_id',         'header': 'RunID',         'format': 's',    'justify': 'L'},
                      {'name': 'num_of_claims',  'header': 'NumClaims',     'format': 's',    'justify': 'R'},
                      {'name': 'ndcg',           'header': 'NDCG',          'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

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

    def get_claim_relation_correctness(self, claim_relation, claim):
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
        if claim.get('assessed_claim_relation') not in ['ontopic', 'related', 'supporting', 'refuting', 'nonsupporting', 'nonrefuting']:
            return 0
        if claim.get('assessed_claim_relation') == claim_relation:
            return 1
        compatible_claim_relations = {
            'nonrefuting': 'supporting',
            'nonsupporting': 'refuting'
            }
        if claim_relation in compatible_claim_relations:
            if claim.get('assessed_claim_relation') == compatible_claim_relations.get(claim_relation):
                return 0.5
        if claim.get('condition') == 'Condition6' and claim_relation == 'ontopic':
            return 1
        self.record_event('DEFAULT_CRITICAL_ERROR', 'Unable to determine claim relation correctness', self.get('code_location'))

    def get_claim_relations(self, score, scores):
        field_name = 'claim_relation'
        values = [score.get(field_name)]
        return values

    def get_claim_to_string(self, claim):
        specs = self.get('specs')
        claim_id = claim.get('claim_id')
        string = []
        string.append('-----------')
        string.append(claim_id)
        for fieldspec in specs.values():
            field_name = fieldspec.get('fieldname')
            claim_field_values = self.get('field_values', fieldspec, claim)
            if len(claim_field_values) == 0:
                claim_field_values = set(['None'])
            string.append('{}: {}'.format(field_name, ','.join(claim_field_values)))
        return '\n'.join(string)

    def get_conditions(self, score, scores):
        field_name = 'condition'
        values = [score.get(field_name)]
        return values

    def get_field_correctness(self, fieldspec, claim):
        correctness_code = {
            'Correct': True,
            'Inexact': True,
            'Wrong': False,
            }
        correctness = claim.get('data').get(fieldspec.get('fieldname')).get('1').get(fieldspec.get('overall_assessment_fieldname'))[0].get('correctness')
        if correctness == 'NIL':
            self.record_event('DEFAULT_WARNING', 'missing assessment for claim {}; using correct as default assessment'.format(claim.get('claim_id')))
            return True
        return correctness_code.get(correctness)

    def get_field_values(self, fieldspec, claim):
        values = []
        data = claim.get('data').get(fieldspec.get('fieldname'))
        if data:
            fieldname_key = 'ec_fieldname' if fieldspec.get('component') else 'overall_assessment_fieldname'
            fieldname = fieldspec.get(fieldname_key)
            sub_fieldname = 'correctness' if fieldspec.get('component') else 'value'
            for entry in data.values():
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
            if gain > pairwise_novelty_score:
                gain = pairwise_novelty_score
        return gain

    def get_pairwise_novelty_score(self, claim_relation, the_claim, another_claim):
        score = 0
        if not self.get('required_fields_correctness', the_claim):
            return score
        claim_relation_correctness_scale = self.get('claim_relation_correctness', claim_relation, the_claim)
        if claim_relation_correctness_scale == 0:
            return score
        specs = self.get('specs')
        for fieldspec in specs.values():
            the_claim_field_values = self.get('field_values', fieldspec, the_claim)
            another_claim_field_values = self.get('field_values', fieldspec, another_claim)
            field_weight = 0
            if the_claim_field_values != another_claim_field_values:
                field_weight = fieldspec.get('weight')
            score += field_weight
        return score * claim_relation_correctness_scale

    def get_query_ids(self, score, scores):
        return ['ALL-Macro']

    def get_ranked_claims(self, query, claim_relation):
        claims = []
        for claim in self.get('claims').get(query.get('condition')).get(query.get('query_id')).values():
            if not claim.get('assessment'): continue
            if claim.get('claim_relation') != claim_relation: continue
            assessed_claim = self.get('assessed_claim', claim)
            assessed_claim_relation = self.get('assessed_claim_relation', query, assessed_claim)
            assessed_claim.set('assessed_claim_relation', assessed_claim_relation)
            assessed_claim.set('rank', claim.get('rank'))
            claims.append(assessed_claim)
        return sorted(claims, key = lambda claim: claim.get('rank'))

    def get_required_fields_correctness(self, claim):
        specs = self.get('specs')
        correctness = True
        for fieldspec in specs.values():
            if fieldspec.get('required'):
                if not self.get('field_correctness', fieldspec, claim):
                    correctness = False
        return correctness

    def get_score(self, query, claim_relation, ranked_claims):
        DCG = self.get('DCG', query, claim_relation, ranked_claims)
        IDCG = self.get('IDCG', query, claim_relation, ranked_claims)
        nDCG = DCG/IDCG if IDCG > 0 else 0
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
                'fieldname': 'claimTemplate',
                'component': False,
                'required': True,
                'max_num_of_values': 1,
                'weight': 1,
                'overall_assessment_fieldname': 'value',
                'importance_rank': 1,
                },
            'claimEpistemic': {
                'fieldname': 'claimEpistemic',
                'component': False,
                'required': True,
                'max_num_of_values': 1,
                'weight': 1,
                'overall_assessment_fieldname': 'polarity',
                'importance_rank': 2,
                },
            'xVariable': {
                'fieldname': 'xVariable',
                'component': True,
                'required': True,
                'max_num_of_values': 1,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'importance_rank': 3,
                },
            'claimer': {
                'fieldname': 'claimer',
                'component': True,
                'required': True,
                'max_num_of_values': 1,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'importance_rank': 4,
                },
            'claimerAffiliation': {
                'fieldname': 'claimerAffiliation',
                'component': True,
                'required': False,
                'max_num_of_values': 3,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'importance_rank': 5,
                },
            'claimLocation': {
                'fieldname': 'claimLocation',
                'component': True,
                'required': False,
                'max_num_of_values': 1,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'importance_rank': 6,
                },
            'claimMedium': {
                'fieldname': 'claimMedium',
                'component': True,
                'required': False,
                'max_num_of_values': 1,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'importance_rank': 7,
                },
            'date': {
                'fieldname': 'date',
                'component': True,
                'required': False,
                'max_num_of_values': 1,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'importance_rank': 8,
                },
            'claimSentiment': {
                'fieldname': 'claimSentiment',
                'component': False,
                'required': False,
                'max_num_of_values': 1,
                'ec_fieldname': 'ec_id',
                'weight': 1,
                'overall_assessment_fieldname': 'value',
                'importance_rank': 9,
                },
            }

    def get_DCG(self, query, claim_relation, ranked_claims):
        run_id = self.get('run_id')
        query_id = query.get('query_id')
        condition = query.get('condition')
        DCG = 0
        for rank in range(len(ranked_claims)):
            gain = self.get('gain', query, claim_relation, ranked_claims, rank)
            run_claim_id = ranked_claims[rank].get('run_claim_id')
            pool_claim_id = ranked_claims[rank].get('claim_id')
            self.record_event('GAIN_VALUE', run_id, condition, query_id, claim_relation, rank, run_claim_id, pool_claim_id, gain)
            DCG += (gain/math.log2(rank+2))
        return DCG

    def get_IDCG(self, query, claim_relation, ranked_claims):
        claims_set = set(ranked_claims)
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
        IDCG = self.get('DCG', query, claim_relation, ideal_claims_ranking)
        return IDCG

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
        scores = []
        claim_relations = {
            'Condition5': ['ontopic', 'related', 'refuting', 'supporting', 'nonrelated', 'nonrefuting'],
            'Condition6': ['ontopic'],
            'Condition7': ['ontopic']
            }
        queries_to_score = self.get('queries_to_score')
        for query_id, query in queries_to_score.items():
            condition = query.get('condition')
            for claim_relation in claim_relations.get(condition):
                ranked_claims = self.get('ranked_claims', query, claim_relation)
                ndcg = self.get('score', query, claim_relation, ranked_claims)
                score = NDCGScore(logger=self.logger,
                                  run_id=self.get('run_id'),
                                  condition=condition,
                                  query_id=query_id,
                                  claim_relation=claim_relation,
                                  num_of_claims=str(len(ranked_claims)),
                                  ndcg=ndcg
                                  )
                scores.append(score)
        scores_printer = ScorePrinter(self.logger, self.printing_specs, aggregate_types=['ALL-Macro'])
        for score in multisort(scores, (('condition', False),
                                        ('query_id', False),
                                        ('claim_relation', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, NDCGScore)
        self.scores = scores_printer