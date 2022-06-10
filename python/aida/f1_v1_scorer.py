"""
AIDA class for Task3 F1 scorer (Variant 1).
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "6 June 2022"

from aida.f1_score import F1Score
from aida.ndcg_v1_scorer import NDCGScorerV1
from aida.score_printer import ScorePrinter
from aida.utility import multisort

def trim(value):
    return '{0:6.4f}'.format(value)

class F1ScorerV1(NDCGScorerV1):
    """
    AIDA class for Task3 F1 scorer (Variant 1).
    """

    printing_specs = [{'name': 'condition',                       'header': 'Condition',                 'format': 's',    'justify': 'L'},
                      {'name': 'query_id',                        'header': 'QueryID',                   'format': 's',    'justify': 'L'},
                      {'name': 'claim_relation',                  'header': 'ClaimRelation',             'format': 's',    'justify': 'L'},
                      {'name': 'run_id',                          'header': 'RunID',                     'format': 's',    'justify': 'L'},
                      {'name': 'cutoff',                          'header': 'Cutoff',                    'format': 's',    'justify': 'R'},
                      {'name': 'num_of_unique_submitted_values',  'header': 'NumUniqueSubmittedValues',  'format': 's',    'justify': 'R'},
                      {'name': 'ground_truth',                    'header': 'GT',                        'format': 's',    'justify': 'R'},
                      {'name': 'f1',                              'header': 'F1',                        'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_score(self, query, claim_relation, ranked_claims_submitted, ranked_claims_ideal):
        unique_values_in_ideal_list = self.get('unique_values', claim_relation, ranked_claims_ideal, cutoff_rank=None)
        self.record_event('UNIQUE_VALUES', 'ideal', query.get('query_id'), claim_relation, 'EOL', ','.join(sorted(unique_values_in_ideal_list)))
        best_unique_values_in_submitted_list = None
        best_rank = None
        best_f1 = None
        for rank in range(len(ranked_claims_submitted)):
            precision, recall, f1, unique_values_in_submitted_list = self.get('score_at_cutoff', rank+1, query, claim_relation, ranked_claims_submitted, unique_values_in_ideal_list)
            self.record_event('UNIQUE_VALUES', 'submitted', query.get('query_id'), claim_relation, rank+1, ','.join(sorted(unique_values_in_submitted_list)))
            self.record_event('SCORE_AT_CUTOFF', query.get('query_id'), claim_relation, rank+1, trim(precision), trim(recall), trim(f1))
            if best_f1 is None or f1 > best_f1:
                best_f1 = f1
                best_unique_values_in_submitted_list = unique_values_in_submitted_list
                best_rank = rank + 1
        return best_f1, best_rank, best_unique_values_in_submitted_list, unique_values_in_ideal_list

    def get_score_at_cutoff(self, cutoff_rank, query, claim_relation, ranked_claims_submitted, unique_values_in_ideal_list):
        unique_values_in_submitted_list = self.get('unique_values', claim_relation, ranked_claims_submitted, cutoff_rank=cutoff_rank)
        precision = len(unique_values_in_submitted_list)/cutoff_rank
        recall_denominator = len(unique_values_in_ideal_list)
        f1 = 0
        if recall_denominator > 0:
            recall = len(unique_values_in_submitted_list)/recall_denominator
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        return precision, recall, f1, unique_values_in_submitted_list

    def get_unique_values(self, claim_relation, ranked_claims, cutoff_rank=None):
        def to_string(claim_values):
            values = []
            for fieldname in sorted(claim_values):
                field_values = claim_values.get(fieldname)
                values.append('{}:{}'.format(fieldname, ','.join(sorted(field_values))))
            return '::'.join(values)
        claims = set()
        i = len(ranked_claims) if cutoff_rank is None else cutoff_rank
        for claim in ranked_claims:
            if i == 0: break
            i -= 1
            claim_relation_correctness_scale = self.get('claim_relation_correctness', claim_relation, claim) if claim.get('condition') == 'Condition5' else 1
            are_required_fields_correct = self.get('required_fields_correctness', claim)
            if claim_relation_correctness_scale == 0 or not are_required_fields_correct: continue
            claims.add(claim)
        claims_values = {}
        for claim in claims:
            claim_id = claim.get('claim_id')
            claim_values = {}
            for fieldspec in self.get('specs').values():
                if fieldspec.get('required_for_f1'):
                    field_values = self.get('field_values', fieldspec, claim, correctness_requirement=True)
                    claim_values[fieldspec.get('fieldname')] = field_values
            claims_values[claim_id] = to_string(claim_values)
        unique_values = set(claims_values.values())
        return unique_values

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
                f1, rank, unique_values_in_submitted_list, unique_values_in_ideal_list = self.get('score', query, claim_relation, ranked_claims_submitted, ranked_claims_ideal)
                score = F1Score(logger=self.logger,
                                run_id=self.get('run_id'),
                                condition=condition,
                                query_id=query_id,
                                claim_relation=claim_relation,
                                cutoff=str(rank if rank is not None else '-'),
                                num_of_unique_submitted_values=str(len(unique_values_in_submitted_list or [])),
                                ground_truth=str(len(unique_values_in_ideal_list or [])),
                                f1=0 if f1 is None else f1
                                )
                scores.append(score)
                ranked_claims = ranked_claims_submitted.copy()
                ranked_claims.extend(ranked_claims_ideal)
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
        self.aggregate_scores(scores_printer, F1Score)
        self.scores = scores_printer