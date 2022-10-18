"""
AIDA class for Argument Extraction evaluation metric scorer.

V1 refers to the variant where we ignore correctness of argument assertion justification.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.container import Container
from aida.object import Object
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.argument_metric_score import ArgumentMetricScore
from aida.utility import multisort

class ArgumentMetricScorerV1(Scorer):
    """
    AIDA class for Argument Extraction evaluation metric scorer.

    V1 refers to the variant where we ignore correctness of argument assertion justification.
    """

    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',            'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',          'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',              'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def align_trfs(self, document_id, gold_trfs, system_trfs):
        for gold_trf in gold_trfs.values():
            if gold_trf.get('aligned'): continue
            for system_trf in system_trfs.values():
                if system_trf.get('aligned'): continue
                if self.are_trfs_aligned(document_id, gold_trf, system_trf):
                    gold_trf.set('aligned', True)
                    gold_trf.set('aligned_to', system_trf)
                    system_trf.set('aligned', True)
                    system_trf.set('aligned_to', gold_trf)

    def are_trfs_aligned(self, document_id, gold_trf, system_trf):
        if gold_trf.get('type') != system_trf.get('type'): return False
        if gold_trf.get('role_name') != system_trf.get('role_name'): return False

        gold_to_system_alignment = self.get('cluster_alignment').get('gold_to_system').get(document_id)
        system_cluster_id_gold_filler_aligned_to = gold_to_system_alignment.get(gold_trf.get('filler_cluster_id')).get('aligned_to')
        if system_cluster_id_gold_filler_aligned_to != system_trf.get('filler_cluster_id'): return False

        if self.is_predicate_justification_correct(system_trf.get('predicate_justifications'),
                                                   gold_trf.get('predicate_justifications')):
            return True
        return False

    def is_predicate_justification_correct(self, system_predicate_justifications, gold_predicate_justifications):
        return True

    def is_valid_slot(self, slot_name):
        if slot_name in self.get('gold_responses').get('slot_mappings').get('mappings').get('type_to_codes'):
            return True
        return False

    def get_document_types_role_fillers(self, system_or_gold, document_id):
        logger = self.get('logger')
        types_role_fillers = Container(logger)
        responses = self.get('{}_responses'.format(system_or_gold))
        if document_id in responses.get('document_frames'):
            for frame in responses.get('document_frames').get(document_id).values():
                metatype = frame.get('metatype')
                role_fillers = frame.get('role_fillers')
                for role_name in role_fillers:
                    for filler_cluster_id in role_fillers.get(role_name):
                        for predicate_justification in role_fillers.get(role_name).get(filler_cluster_id):
                            types = self.get('types', frame)
                            types_role_filler_string = '{types}_{role_name}:{filler_cluster_id}'.format(types=types,
                                                                                                       role_name=role_name,
                                                                                                       filler_cluster_id=filler_cluster_id)
                            types_role_filler = types_role_fillers.get(types_role_filler_string, default=Object(logger))
                            types_role_filler.set('metatype', metatype)
                            types_role_filler.set('types', types)
                            types_role_filler.set('role_name', role_name)
                            types_role_filler.set('filler_cluster_id', filler_cluster_id)
                            if types_role_filler.get('predicate_justifications') is None:
                                types_role_filler.set('predicate_justifications', Container(logger))
                            types_role_filler.get('predicate_justifications').add(predicate_justification)
        return types_role_fillers

    def get_score(self, gold_trfs, system_trfs, metatypes):
        num_true_positive = 0
        num_false_positive = 0
        num_false_negative = 0
        num_gold_trf = 0
        num_system_trf = 0
        for trf in gold_trfs.values():
            if trf.get('metatype') not in metatypes: continue
            num_gold_trf += 1
            if trf.get('aligned'):
                num_true_positive += 1
            else:
                num_false_negative += 1
        for trf in system_trfs.values():
            if trf.get('metatype') not in metatypes: continue
            num_system_trf += 1
            if not trf.get('aligned'):
                num_false_positive += 1
        precision = num_true_positive / (num_true_positive + num_false_positive) if num_true_positive + num_false_positive else 0
        recall = num_true_positive / (num_true_positive + num_false_negative) if num_true_positive + num_false_negative else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        return num_gold_trf, num_system_trf, precision, recall, f1

    def get_types(self, frame):
        return '{}{}{}'.format('{', ','.join(sorted(frame.get('types'))), '}')

    def score_responses(self):
        metatypes = {
            'ALL': ['Event', 'Relation'],
            'Event': ['Event'],
            'Relation': ['Relation']
            }
        scores = []
        for document_id in self.get('core_documents'):
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            # skip those core documents that do not have an entry in the parent-children table
            if document is None: continue
            language = document.get('language')
            gold_trfs = self.get('document_types_role_fillers', 'gold', document_id)
            system_trfs = self.get('document_types_role_fillers', 'system', document_id)
            self.align_trfs(document_id, gold_trfs, system_trfs)
            for metatype_key in metatypes:
                num_gold_trf, num_system_trf, precision, recall, f1 = self.get('score', gold_trfs, system_trfs, metatypes[metatype_key])
                if num_gold_trf + num_system_trf == 0: continue
                score = ArgumentMetricScore(logger=self.logger,
                                            run_id=self.get('run_id'),
                                            document_id=document_id,
                                            language=language,
                                            metatype=metatype_key,
                                            precision=precision,
                                            recall=recall,
                                            f1=f1)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype_sortkey', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, ArgumentMetricScore)
        self.scores = scores_printer