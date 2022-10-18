"""
AIDA class for Argument Extraction evaluation metric scorer.

This class serves as the base class all the Argument Extraction evaluation metric scorer variants used in Phase 3.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 September 2022"

from aida.container import Container
from aida.type_role_filler import TypeRoleFiller
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.argument_metric_score import ArgumentMetricScore
from aida.utility import multisort, get_cost_matrix
from munkres import Munkres
from tqdm import tqdm

class ArgumentMetricScorerV3(Scorer):
    """
    AIDA class for Argument Extraction evaluation metric scorer.

    This class serves as the base class all the Argument Extraction evaluation metric scorer variants used in Phase 3.
    """

    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'trf_score',        'header': 'TRFscore',        'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def align_trfs(self, document_id, gold_trfs, system_trfs):
        trfs = {'gold': gold_trfs, 'system': system_trfs}
        # build the mapping table
        mappings = {}
        for system_or_gold in trfs:
            if len(trfs.get(system_or_gold)) == 0: return
            mappings[system_or_gold] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0;
            for trf_id in trfs.get(system_or_gold):
                mappings[system_or_gold]['id_to_index'][trf_id] = index
                mappings[system_or_gold]['index_to_id'][index] = trf_id
                index += 1
        # build the similarities table
        similarities = {}
        for gold_trf_id in gold_trfs:
            gold_trf = gold_trfs.get(gold_trf_id)
            for system_trf_id in system_trfs:
                system_trf = system_trfs.get(system_trf_id)
                similarities.setdefault(gold_trf_id, {})[system_trf_id] = self.get('TRFscore', document_id, gold_trf, system_trf)

        cost_matrix = get_cost_matrix(similarities, mappings)
        for gold_trf_index, system_trf_index in Munkres().compute(cost_matrix):
            gold_trf_id = mappings['gold']['index_to_id'][gold_trf_index]
            system_trf_id = mappings['system']['index_to_id'][system_trf_index]
            trf_score = similarities.get(gold_trf_id).get(system_trf_id)
            if trf_score > 0:
                gold_trf = gold_trfs.get(gold_trf_id)
                system_trf = system_trfs.get(system_trf_id)
                gold_trf.set('aligned', True)
                gold_trf.set('aligned_to', system_trf)
                gold_trf.set('TRFscore', similarities.get(gold_trf_id).get(system_trf_id))
                system_trf.set('aligned', True)
                system_trf.set('aligned_to', gold_trf)
                system_trf.set('TRFscore', trf_score)

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

    def is_valid_slot(self, slot_name):
        if slot_name in self.get('gold_responses').get('slot_mappings').get('mappings').get('type_to_codes'):
            return True
        return False

    def get_ClusterSim(self, document_id, gold_trf, system_trf):
        # normalized similarity
        def get_number_of_mentions(document_id, system_or_gold, trf):
            cluster_id = trf.get('filler_cluster_id')
            cluster = self.get('cluster', system_or_gold, document_id, cluster_id)
            return len(cluster.get('mentions'))
        sim = self.get('Sim', document_id, gold_trf, system_trf)
        precision = sim/get_number_of_mentions(document_id, 'system', system_trf)
        recall = sim/get_number_of_mentions(document_id, 'gold', gold_trf)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        return f1

    def get_document_types_role_fillers(self, system_or_gold, document_id):
        def types_tostring(types):
            return '{}{}{}'.format('{', ','.join(sorted(types)), '}')
        logger = self.get('logger')
        types_role_fillers = Container(logger)
        responses = self.get('{}_responses'.format(system_or_gold))
        if document_id in responses.get('document_frames'):
            for frame in responses.get('document_frames').get(document_id).values():
                subject_metatype = frame.get('metatype')
                role_fillers = frame.get('role_fillers')
                for role_name in role_fillers:
                    for filler_cluster_id in role_fillers.get(role_name):
                        for predicate_justification in role_fillers.get(role_name).get(filler_cluster_id):
                            subject_types = set(frame.get('types').keys())
                            trf_key = '{subject_cluster_id}:{filler_cluster_id}'.format(subject_cluster_id=frame.get('ID'),
                                                                                        filler_cluster_id=filler_cluster_id)
                            types_role_filler = types_role_fillers.get(trf_key, default=TypeRoleFiller(logger))
                            types_role_filler.update('trf_id', trf_key, single_valued=True)
                            types_role_filler.update('document_id', document_id, single_valued=True)
                            types_role_filler.update('negation_status', predicate_justification.get('is_assertion_negated'))
                            types_role_filler.update('subject_cluster_id', frame.get('ID'), single_valued=True)
                            types_role_filler.update('subject_types', subject_types)
                            types_role_filler.update('metatype', subject_metatype, single_valued=True)
                            types_role_filler.update('role_name', role_name)
                            types_role_filler.update('filler_cluster_id', filler_cluster_id, single_valued=True)
                            types_role_filler.update('predicate_justifications', predicate_justification)
        return types_role_fillers

    def get_RolesPrecision(self, document_id, gold_trf, system_trf):
        def trim(rolename):
            parts = rolename.split('_')
            num_parts = 2
            selected_parts = list()
            for part in parts:
                if num_parts:
                    selected_parts.append(part)
                else:
                    break
                num_parts -= 1
            return '_'.join(selected_parts)
        trfs = {'gold': gold_trf, 'system': system_trf}
        trimmed_roles = {}
        for system_or_gold in trfs:
            trimmed_roles[system_or_gold] = set([trim(r) for r in trfs.get(system_or_gold).get('role_name')])
        return len(trimmed_roles.get('system') & trimmed_roles.get('gold')) / len(trimmed_roles.get('system')) if len(trimmed_roles.get('system')) else 0

    def get_score(self, document_id, gold_trfs, system_trfs, metatypes):
        sumTRFscore = 0
        count = 0
        trfs = {'gold': gold_trfs, 'system': system_trfs}
        for system_trf in trfs.get('system').values():
            if system_trf.get('aligned') and system_trf.get('metatype') in metatypes:
                sumTRFscore += system_trf.get('TRFscore')
                count += 1
        for system_or_gold in trfs:
            for trf in trfs.get(system_or_gold).values():
                # log TRF information
                trf_id = trf.get('trf_id')
                metatype = trf.get('metatype')
                role_names = ','.join(sorted(trf.get('role_name')))
                is_aligned = trf.get('aligned')
                aligned_to = trf.get('aligned_to').get('trf_id') if is_aligned else 'None'
                trf_score = trf.get('TRFscore')
                self.record_event('DOCUMENT_TRF_INFO', document_id, system_or_gold, trf_id, metatype, role_names, is_aligned, aligned_to, trf_score)
                if trf.get('aligned') is None and trf.get('metatype') in metatypes:
                    count += 1
        return sumTRFscore/count if count else 0

    def get_Sim(self, document_id, gold_trf, system_trf):
        gold_filler_cluster_id = gold_trf.get('filler_cluster_id')
        system_filler_cluster_id = system_trf.get('filler_cluster_id')
        document_cluster_alignment = self.get('cluster_alignment').get('system_to_gold').get(document_id)
        if system_filler_cluster_id in document_cluster_alignment:
            aligned_gold_cluster_id = document_cluster_alignment.get(system_filler_cluster_id).get('aligned_to')
            if gold_filler_cluster_id == aligned_gold_cluster_id:
                return float(document_cluster_alignment.get(system_filler_cluster_id).get('aligned_similarity'))
        return 0

    def get_type_similarity(self, document_id, system_cluster_id, gold_cluster_id):
        return float(self.get('type_similarities').get('type_similarity', document_id, system_cluster_id, gold_cluster_id))

    def get_TypeSim(self, document_id, gold_trf, system_trf):
        return self.get('type_similarity', document_id, system_trf.get('subject_cluster_id'), gold_trf.get('subject_cluster_id'))

    def get_TRFscore(self, document_id, gold_trf, system_trf):
        if gold_trf.get('metatype') != system_trf.get('metatype'):
            return 0
        type_sim = self.get('TypeSim', document_id, gold_trf, system_trf)
        roles_precision = self.get('RolesPrecision', document_id, gold_trf, system_trf)
        cluster_sim = self.get('ClusterSim', document_id, gold_trf, system_trf)
        trf_score = type_sim * roles_precision * cluster_sim
        self.record_event('TYPE_SIM_INFO', document_id, gold_trf.get('trf_id'), system_trf.get('trf_id'), type_sim)
        self.record_event('CLUSTER_SIM_INFO', document_id, gold_trf.get('trf_id'), system_trf.get('trf_id'), 'object', cluster_sim)
        self.record_event('ROLES_PRECISION_INFO', document_id, gold_trf.get('trf_id'), system_trf.get('trf_id'), roles_precision)
        self.record_event('TRF_SCORE_INFO', document_id, gold_trf.get('trf_id'), system_trf.get('trf_id'), trf_score)
        return trf_score

    def score_responses(self):
        metatypes = {
            'ALL': ['Event', 'Relation'],
            'Event': ['Event'],
            'Relation': ['Relation']
            }
        scores = []
        for document_id in tqdm(self.get('core_documents'), desc='scoring {}'.format(self.__class__.__name__)):
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            # skip those core documents that do not have an entry in the parent-children table
            if document is None: continue
            language = document.get('language')
            gold_trfs = self.filter(self.get('document_types_role_fillers', 'gold', document_id))
            system_trfs = self.filter(self.get('document_types_role_fillers', 'system', document_id))
            self.align_trfs(document_id, gold_trfs, system_trfs)
            for metatype_key in metatypes:
                counted_trfs = 0
                for gold_trf in gold_trfs.values():
                    if gold_trf.get('metatype') in metatypes.get(metatype_key):
                        counted_trfs += 1
                if not counted_trfs: continue
                averageTRFscore = self.get('score', document_id, gold_trfs, system_trfs, metatypes[metatype_key])
                score = ArgumentMetricScore(logger=self.logger,
                                            run_id=self.get('run_id'),
                                            document_id=document_id,
                                            language=language,
                                            metatype=metatype_key,
                                            trf_score=averageTRFscore)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype_sortkey', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, ArgumentMetricScore)
        self.scores = scores_printer