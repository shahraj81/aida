"""
AIDA class for Event/Relation frame evaluation metric scorer.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.container import Container
from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.frame_metric_score import FrameMetricScore
from aida.utility import multisort, get_cost_matrix
from aida.type_role_filler import TypeRoleFiller
from munkres import Munkres

class FrameMetricScorer(Scorer):
    """
    AIDA class for Event/Relation frame evaluation metric scorer.
    """
    
    printing_specs = [{'name': 'document_id',        'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',             'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',           'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',           'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'gold_cluster_id',    'header': 'GoldClusterID',   'format': 's',    'justify': 'L'},
                      {'name': 'system_cluster_id',  'header': 'SystemClusterID', 'format': 's',    'justify': 'L'},
                      {'name': 'average_edge_score', 'header': 'AvgEdgeScore',    'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def align_edges(self, document_id, gold_edges, system_edges):
        edges = {'gold': gold_edges, 'system': system_edges}
        # build the mapping table
        mappings = {}
        for system_or_gold in edges:
            if len(edges.get(system_or_gold)) == 0: return
            mappings[system_or_gold] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0;
            for edge_id in edges.get(system_or_gold):
                mappings[system_or_gold]['id_to_index'][edge_id] = index
                mappings[system_or_gold]['index_to_id'][index] = edge_id
                index += 1
        # build the similarities table
        similarities = {}
        for gold_edge_id in gold_edges:
            gold_edge = gold_edges.get(gold_edge_id)
            for system_edge_id in system_edges:
                system_edge = system_edges.get(system_edge_id)
                similarities.setdefault(gold_edge_id, {})[system_edge_id] = self.get('Edgescore', document_id, gold_edge, system_edge)

        cost_matrix = get_cost_matrix(similarities, mappings)
        for gold_edge_index, system_edge_index in Munkres().compute(cost_matrix):
            gold_edge_id = mappings['gold']['index_to_id'][gold_edge_index]
            system_edge_id = mappings['system']['index_to_id'][system_edge_index]
            gold_edge = gold_edges.get(gold_edge_id)
            system_edge = system_edges.get(system_edge_id)
            gold_edge.set('aligned', True)
            gold_edge.set('aligned_to', system_edge)
            gold_edge.set('Edgescore', similarities.get(gold_edge_id).get(system_edge_id))
            system_edge.set('aligned', True)
            system_edge.set('aligned_to', gold_edge)
            system_edge.set('Edgescore', similarities.get(gold_edge_id).get(system_edge_id))

    def get_AverageEdgeScore(self, document_id, system_cluster_id, gold_cluster_id):
        edges = {
            'gold': self.get('edges', 'gold', document_id, gold_cluster_id),
            'system': self.get('edges', 'system', document_id, system_cluster_id)}
        self.align_edges(document_id, edges.get('gold'), edges.get('system'))
        # log the edges and alignment information
        for system_or_gold in edges:
            for edge in edges.get(system_or_gold).values():
                edge_id = edge.get('edge_id')
                subject_cluster_id = edge.get('subject_cluster_id')
                role_names = ','.join(sorted(edge.get('role_name')))
                subject_types = ','.join(sorted(edge.get('subject_types')))
                is_aligned = edge.get('aligned')
                aligned_to = edge.get('aligned_to').get('edge_id') if is_aligned else 'None'
                edge_score = edge.get('Edgescore')
                self.record_event('DOCUMENT_EDGE_INFO', document_id, system_or_gold, edge_id, subject_cluster_id, role_names, subject_types, is_aligned, aligned_to, edge_score)
        # compute the score
        sumEdgescore = 0
        count = 0
        for system_edge in edges.get('system').values():
            if system_edge.get('aligned'):
                sumEdgescore += system_edge.get('Edgescore')
                count += 1
        for system_or_gold in edges:
            for edge in edges.get(system_or_gold).values():
                if edge.get('aligned') is None:
                    count += 1
        return sumEdgescore/count if count else 0

    def get_ClusterSim(self, document_id, gold_edge, system_edge, cluster_type):
        # normalized similarity
        def get_number_of_mentions(document_id, cluster_type, system_or_gold, edge):
            cluster_keys = {
                'subject': 'subject_cluster_id',
                'object': 'filler_cluster_id'
                }
            cluster_id = edge.get(cluster_keys.get(cluster_type))
            cluster = self.get('cluster', system_or_gold, document_id, cluster_id)
            return len(cluster.get('mentions'))
        sim = self.get('Sim', document_id, gold_edge, system_edge, cluster_type)
        precision = sim/get_number_of_mentions(document_id, cluster_type, 'system', system_edge)
        recall = sim/get_number_of_mentions(document_id, cluster_type, 'gold', gold_edge)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        return f1

    def get_edges(self, system_or_gold, document_id, cluster_id):
        frame = self.get('frame', system_or_gold, document_id, cluster_id)
        logger = self.get('logger')
        edges = Container(logger)
        edges.set('document_id', document_id)
        if frame is not None:
            subject_metatype = frame.get('metatype')
            role_fillers = frame.get('role_fillers')
            for role_name in role_fillers:
                for filler_cluster_id in role_fillers.get(role_name):
                    for predicate_justification in role_fillers.get(role_name).get(filler_cluster_id):
                        subject_types = set(frame.get('types').keys())
                        # in this version of the scorer, an edge is uniquely identified by (subject_cluster_id,
                        # object_cluster_id)
                        #
                        # defined this way, the rolenames on the edge are a union of all the rolename
                        # that go between the pair of clusters
                        #
                        # given the frame (of the subject cluster), number of unique edges correspond to the 
                        # number of unique object cluster IDs
                        edge_key = filler_cluster_id
                        edge = edges.get(edge_key, default=TypeRoleFiller(logger))
                        edge.update('edge_id', edge_key, single_valued=True)
                        edge.update('negation_status', predicate_justification.get('is_assertion_negated'))
                        edge.update('subject_cluster_id', frame.get('ID'), single_valued=True)
                        edge.update('subject_types', subject_types)
                        edge.update('metatype', subject_metatype, single_valued=True)
                        edge.update('role_name', role_name)
                        edge.update('filler_cluster_id', filler_cluster_id, single_valued=True)
                        edge.update('predicate_justifications', predicate_justification)
        return edges

    def get_RoleSim(self, gold_edge, system_edge):
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
        edge = {'gold': gold_edge, 'system': system_edge}
        trimmed_roles = {}
        for system_or_gold in edge:
            trimmed_roles[system_or_gold] = set([trim(r) for r in edge.get(system_or_gold).get('role_name')])
        return len(trimmed_roles.get('system') & trimmed_roles.get('gold')) / len(trimmed_roles.get('system')) if len(trimmed_roles.get('system')) else 0

    def get_Sim(self, document_id, gold_edge, system_edge, cluster_type):
        cluster_keys = {
            'subject': 'subject_cluster_id',
            'object': 'filler_cluster_id'
            }
        edges = {'system': system_edge, 'gold': gold_edge}
        cluster_id = {}
        for system_or_gold in edges:
            cluster_id[system_or_gold] = edges.get(system_or_gold).get(cluster_keys.get(cluster_type))
        document_cluster_alignment = self.get('cluster_alignment').get('system_to_gold').get(document_id)
        if cluster_id.get('system') in document_cluster_alignment:
            aligned_gold_cluster_id = document_cluster_alignment.get(cluster_id.get('system')).get('aligned_to')
            if cluster_id.get('gold') == aligned_gold_cluster_id:
                return float(document_cluster_alignment.get(cluster_id.get('system')).get('aligned_similarity'))
        return 0

    def get_Edgescore(self, document_id, gold_edge, system_edge):
        subject_cluster_sim = self.get('ClusterSim', document_id, gold_edge, system_edge, cluster_type='subject')
        role_sim = self.get('RoleSim', gold_edge, gold_edge)
        object_cluster_sim = self.get('ClusterSim', document_id, gold_edge, system_edge, cluster_type='object')
        edge_score = subject_cluster_sim * role_sim * object_cluster_sim
        self.record_event('CLUSTER_SIM_INFO', document_id, gold_edge.get('edge_id'), system_edge.get('edge_id'), 'subject', subject_cluster_sim)
        self.record_event('ROLE_SIM_INFO', document_id, gold_edge.get('edge_id'), system_edge.get('edge_id'), role_sim)
        self.record_event('CLUSTER_SIM_INFO', document_id, gold_edge.get('edge_id'), system_edge.get('edge_id'), 'object', object_cluster_sim)
        self.record_event('EDGE_SCORE_INFO', document_id, gold_edge.get('edge_id'), system_edge.get('edge_id'), edge_score)
        return edge_score

    def get_num_edges(self, system_or_gold, document_id, cluster_id):
        return len(self.get('edges', system_or_gold, document_id, cluster_id))

    def score_responses(self):
        scores = []
        for document_id in self.get('core_documents'):
            # add scores corresponding to all gold clusters
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            # skip those core documents that do not have an entry in the parent-children table
            if document is None: continue
            language = document.get('language')
            document_gold_to_system = self.get('cluster_alignment').get('gold_to_system').get(document_id)
            counted = {'gold': set(), 'system': set()}
            for gold_cluster_id in document_gold_to_system if document_gold_to_system else []:
                system_cluster_id = document_gold_to_system.get(gold_cluster_id).get('aligned_to')
                aligned_similarity = document_gold_to_system.get(gold_cluster_id).get('aligned_similarity')
                num_gold_edges = 0
                average_edge_score = 0
                if gold_cluster_id == 'None': continue
                gold_cluster = self.get('cluster', 'gold', document_id, gold_cluster_id)
                metatype = gold_cluster.get('metatype')
                if metatype not in ['Event', 'Relation']: continue
                if system_cluster_id != 'None':
                    if aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                    system_cluster = self.get('cluster', 'system', document_id, system_cluster_id)
                    if system_cluster.get('metatype') != metatype:
                        self.record_event('UNEXPECTED_ALIGNED_CLUSTER_METATYPE', system_cluster.get('metatype'), system_cluster_id, metatype, gold_cluster_id)
                    num_gold_edges = self.get('num_edges', 'gold', document_id, gold_cluster_id)
                    average_edge_score = self.get('AverageEdgeScore', document_id, system_cluster_id, gold_cluster_id)
                    counted.get('system').add(system_cluster_id)
                    counted.get('gold').add(gold_cluster_id)
                if num_gold_edges == 0: continue
                score = FrameMetricScore(logger=self.logger,
                                         run_id=self.get('run_id'),
                                         document_id=document_id,
                                         language=language,
                                         metatype=metatype,
                                         gold_cluster_id=gold_cluster_id,
                                         system_cluster_id=system_cluster_id,
                                         average_edge_score=average_edge_score)
                scores.append(score)
            # add scores corresponding to unaligned system clusters
            document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
            for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                aligned_similarity = document_system_to_gold.get(system_cluster_id).get('aligned_similarity')
                if system_cluster_id != 'None':
                    if gold_cluster_id == 'None':
                        metatype = self.get('cluster', 'system', document_id, system_cluster_id).get('metatype')
                        if metatype not in ['Event', 'Relation']: continue
                        score = FrameMetricScore(logger=self.logger,
                                                 run_id=self.get('run_id'),
                                                 document_id=document_id,
                                                 language=language,
                                                 metatype=metatype,
                                                 gold_cluster_id=gold_cluster_id,
                                                 system_cluster_id=system_cluster_id,
                                                 average_edge_score=0)
                        scores.append(score)
                    elif aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False),
                                        ('gold_cluster_id', False),
                                        ('system_cluster_id', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, FrameMetricScore)
        self.scores = scores_printer