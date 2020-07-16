"""
The container to hold Clusters.

This class supports the alignment of clusters as needed for scoring.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 July 2020"

from aida.object import Object
from aida.container import Container
from aida.file_handler import FileHandler
from aida.cluster import Cluster
from aida.event_or_relation_frame import EventOrRelationFrame

import sys
from munkres import Munkres

class Clusters(Object):
    """
    The container to hold Clusters.
    """

    def __init__(self, logger, gold_mentions_filename, gold_edges_filename, system_mentions_filename, system_edges_filename):
        """
        Initialize the Clusters.
        """
        super().__init__(logger)
        self.filenames = Container(logger)
        self.filenames.add(key='gold', value={'mentions': gold_mentions_filename, 'edges': gold_edges_filename})
        self.filenames.add(key='system', value={'mentions': system_mentions_filename, 'edges': system_edges_filename})
        self.clusters = {'gold': Container(logger), 'system': Container(logger)}
        self.frames = {'gold': Container(logger), 'system': Container(logger)}
        self.alignment = {'gold_to_system': {}, 'system_to_gold': {}}
        self.load()
        self.align_clusters()

    def get_cluster(self, gold_or_system, cluster_id):
        return self.get('clusters').get(gold_or_system).get(cluster_id)

    def get_entities_and_events_similarities(self):
        similarities = {}
        for gold_cluster in self.get('clusters').get('gold').values():
            if gold_cluster.get('metatype') == 'Relation':
                continue
            for system_cluster in self.get('clusters').get('system').values():
                if system_cluster.get('metatype') == 'Relation':
                    continue
                similarity = self.get('similarity', gold_cluster, system_cluster)
                if gold_cluster.get('ID') not in similarities:
                    similarities[gold_cluster.get('ID')] = {}
                similarities[gold_cluster.get('ID')][system_cluster.get('ID')] = similarity
        return similarities

    def get_intersection_over_union(self, m1, m2):
        if m1.get('document_id') == m2.get('document_id'):
            if m1.get('document_element_id') == m2.get('document_element_id'):
                intersection = 0
                dx = min(float(m1.get('span').get('end_x')), float(m2.get('span').get('end_x'))) - max(float(m1.get('span').get('start_x')), float(m2.get('span').get('start_x')))
                dy = min(float(m1.get('span').get('end_y')), float(m2.get('span').get('end_y'))) - max(float(m1.get('span').get('start_y')), float(m2.get('span').get('start_y')))
                if (dx>0) and (dy>0):
                    intersection = dx*dy
                elif dx:
                    intersection = dx
                elif dy:
                    intersection = dy

                union = 0
                for m in [m1, m2]:
                    dx = float(m.get('span').get('end_x'))-float(m.get('span').get('start_x'))
                    dy = float(m.get('span').get('end_y'))-float(m.get('span').get('start_y'))
                    if (dx>0) and (dy>0):
                        union += dx*dy
                    elif dx:
                        union += dx
                    elif dy:
                        union += dy
                union -= intersection
        intersection_over_union = intersection/union
        return intersection_over_union

    def get_relation_similarity(self, gold_frame, system_frame):
        score = 0
        gold_frame_type_elements = gold_frame.get('event_or_relation_type').split('.')
        system_frame_type_elements = system_frame.get('event_or_relation_type').split('.')
        gold_frame_type = '{}.{}'.format(gold_frame_type_elements[0], gold_frame_type_elements[1])
        system_frame_type = '{}.{}'.format(system_frame_type_elements[0], system_frame_type_elements[1])
        if gold_frame_type == system_frame_type:
            # return alignment score of zero if the roles don't match
            if len(gold_frame.get('role_fillers')) != len(set(gold_frame.get('role_fillers')) & set(system_frame.get('role_fillers'))):
                return 0
            # role match, now match the fillers of each role
            for rolename in gold_frame.get('role_fillers'):
                gold_fillers = list(gold_frame.get('role_fillers')[rolename])
                system_fillers = list(system_frame.get('role_fillers')[rolename]) if rolename in system_frame.get('role_fillers') else []
                # get the gold aligned system filler
                gold_aligned_system_fillers = []
                for filler in system_fillers:
                    filler_alignment_score = 0
                    gold_aligned_system_filler_mapping_object = self.get('alignment').get('system_to_gold').get(filler, None)
                    if gold_aligned_system_filler_mapping_object is not None:
                        gold_aligned_filler_id = gold_aligned_system_filler_mapping_object.get('aligned_to')
                        gold_aligned_filler_alignment_score = gold_aligned_system_filler_mapping_object.get('aligned_similarity')
                        gold_aligned_system_fillers.append(gold_aligned_filler_id)
                        filler_alignment_score += gold_aligned_filler_alignment_score
                # if the gold fillers do not match the gold aligned system fillers return 0
                if len(gold_fillers) == len(set(gold_fillers) & set(gold_aligned_system_fillers)):
                    score += filler_alignment_score
                else:
                    return 0
        return score

    def get_number_of_common_types(self, gold_cluster, system_cluster):
        gold_types = [full_type.split('.')[0] for full_type in gold_cluster.get('types')]
        system_types = [full_type.split('.')[0] for full_type in system_cluster.get('types')]
        return len(set(gold_types) & set(system_types))

    def get_similarity(self, gold_cluster, system_cluster):
        similarity = 0
        if self.get('number_of_common_types', gold_cluster, system_cluster) > 0:
            for gold_mention in gold_cluster.get('mentions').values():
                for system_mention in system_cluster.get('mentions').values():
                    if self.get('intersection_over_union', gold_mention, system_mention) > 0.8:
                        similarity += 1
        return similarity

    def load(self):
        """
        Load the files containing mentions and edges.
        """
        for filetype in ['gold', 'system']:
            self.load_mentions(filetype)
            self.load_frames(filetype)

    def load_mentions(self, filetype):
        logger = self.get('logger')
        clusters = self.get('clusters').get(filetype)
        for entry in FileHandler(self.get('logger'), self.get('filenames').get(filetype).get('mentions')):
            cluster_id = entry.get('?cluster')
            if not clusters.exists(cluster_id):
                clusters.add(key=cluster_id, value=Cluster(logger, cluster_id))
            cluster = clusters.get(cluster_id)
            cluster.add(entry)

    def load_frames(self, filetype):
        logger = self.get('logger')
        frames = self.get('frames').get(filetype)
        for entry in FileHandler(self.get('logger'), self.get('filenames').get(filetype).get('edges')):
            # get edge_id
            frame_id = entry.get('?subject')
            if not frames.exists(frame_id):
                frames.add(key=frame_id, value=EventOrRelationFrame(logger, frame_id))
            frame = frames.get(frame_id)
            frame.update(entry)

    def align_clusters(self):
        self.align_entities_and_events()
        self.align_relations()

    def align_entities_and_events(self):
        mappings = {}
        for filetype in ['gold', 'system']:
            mappings[filetype] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0;
            for cluster_id in sorted(self.get('clusters').get(filetype)):
                if self.get('cluster', filetype, cluster_id).get('metatype') == 'Relation':
                    continue
                mappings[filetype]['id_to_index'][cluster_id] = index
                mappings[filetype]['index_to_id'][index] = cluster_id
                index += 1
        cost_matrix = []
        similarities = self.get('entities_and_events_similarities')
        for gold_cluster_index in sorted(mappings['gold']['index_to_id']):
            cost_row = []
            gold_cluster_id = mappings['gold']['index_to_id'][gold_cluster_index]
            for system_cluster_index in sorted(mappings['system']['index_to_id']):
                system_cluster_id = mappings['system']['index_to_id'][system_cluster_index]
                similarity = similarities[gold_cluster_id][system_cluster_id]
                cost_row += [sys.maxsize - similarity]
            cost_matrix += [cost_row]
        
        for gold_cluster_index, system_cluster_index in Munkres().compute(cost_matrix):
            gold_cluster = self.get('cluster', 'gold', mappings['gold']['index_to_id'][gold_cluster_index])
            system_cluster = self.get('cluster', 'system', mappings['system']['index_to_id'][system_cluster_index])
            similarity = similarities[gold_cluster.get('ID')][system_cluster.get('ID')]
            if similarity > 0:
                self.get('alignment').get('gold_to_system')[gold_cluster.get('ID')] = {
                        'aligned_to': system_cluster.get('ID'),
                        'aligned_similarity': similarity
                    }
                self.get('alignment').get('system_to_gold')[system_cluster.get('ID')] = {
                        'aligned_to': gold_cluster.get('ID'),
                        'aligned_similarity': similarity
                    }

    def align_relations(self):
        for gold_frame in self.get('frames').get('gold').values():
            if gold_frame.get('metatype') != 'Relation':
                continue
            for system_frame in self.get('frames').get('system').values():
                if system_frame.get('metatype') != 'Relation':
                    continue
                similarity = self.get('relation_similarity', gold_frame, system_frame)
                if similarity > 0:
                    self.get('alignment').get('gold_to_system')[gold_frame.get('ID')] = {
                            'aligned_to': system_frame.get('ID'),
                            'aligned_similarity': similarity
                        }
                    self.get('alignment').get('system_to_gold')[system_frame.get('ID')] = {
                            'aligned_to': gold_frame.get('ID'),
                            'aligned_similarity': similarity
                        }
