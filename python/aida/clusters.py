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
from aida.annotated_regions import AnnotatedRegions
from aida.event_or_relation_frame import EventOrRelationFrame
from aida.utility import get_cost_matrix, get_intersection_over_union
from munkres import Munkres

class Clusters(Object):
    """
    The container to hold Clusters.
    """

    def __init__(self, logger, regions_filename, gold_mentions_filename, gold_edges_filename, system_mentions_filename, system_edges_filename):
        """
        Initialize the Clusters.
        """
        super().__init__(logger)
        self.annotated_regions = AnnotatedRegions(logger, regions_filename)
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
            if gold_cluster.is_invalid_for_alignment(self.get('annotated_regions')):
                continue
            for system_cluster in self.get('clusters').get('system').values():
                if system_cluster.is_invalid_for_alignment(self.get('annotated_regions')):
                    continue
                similarity = self.get('similarity', gold_cluster, system_cluster)
                if gold_cluster.get('ID') not in similarities:
                    similarities[gold_cluster.get('ID')] = {}
                similarities[gold_cluster.get('ID')][system_cluster.get('ID')] = similarity
        return similarities

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

    def get_metatype(self, gold_or_system, cluster_or_frame_id):
        cluster_id = self.get('clusters').get(gold_or_system).get(cluster_or_frame_id)
        frame_id = self.get('frames').get(gold_or_system).get(cluster_or_frame_id)
        if cluster_id and frame_id:
            self.get('logger').record_event('AMBIGUOUS_CLUSTERID', cluster_or_frame_id)
        cluster_or_frame = cluster_id or frame_id
        return cluster_or_frame.get('metatype')

    def get_number_of_common_types(self, gold_cluster, system_cluster):
        gold_types = gold_cluster.get('top_level_types')
        system_types = system_cluster.get('top_level_types')
        return len(set(gold_types) & set(system_types))

    def get_similarity(self, gold_cluster, system_cluster):
        similarity = 0
        if self.get('number_of_common_types', gold_cluster, system_cluster) > 0:
            mentions = {'gold': list(gold_cluster.get('mentions').values()),
                        'system': list(system_cluster.get('mentions').values())}
            mappings = {}
            for filetype in mentions:
                mappings[filetype] = {'id_to_index': {}, 'index_to_id': {}}
                index = 0;
                for mention in mentions[filetype]:
                    mappings[filetype]['id_to_index'][mention.get('ID')] = index
                    mappings[filetype]['index_to_id'][index] = mention.get('ID')
                    index += 1
            similarities = {}
            for gold_mention in mentions['gold']:
                for system_mention in mentions['system']:
                    if gold_mention.get('ID') not in similarities:
                        similarities[gold_mention.get('ID')] = {}
                    similarities[gold_mention.get('ID')][system_mention.get('ID')] = get_intersection_over_union(gold_mention.get('span'), system_mention.get('span'))
            cost_matrix = get_cost_matrix(similarities, mappings)
            alignment = {'gold_mention': {}, 'system_mention': {}}
            for gold_mention_index, system_mention_index in Munkres().compute(cost_matrix):
                gold_mention_id = mappings['gold']['index_to_id'][gold_mention_index]
                system_mention_id = mappings['system']['index_to_id'][system_mention_index]
                alignment['gold_mention'][gold_mention_id] = {'system_mention': system_mention_id, 'score': similarities[gold_mention_id][system_mention_id]}
                alignment['system_mention'][system_mention_id] = {'gold_mention': gold_mention_id, 'score': similarities[gold_mention_id][system_mention_id]}
                if similarities[gold_mention_id][system_mention_id] > 0.8:
                    # lenient similarity computation
                    similarity += 1
                    # alternative would be to add up the amount of overlap
                    # similarity += similarities[gold_mention_id][system_mention_id]
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
        similarities = self.get('entities_and_events_similarities')
        cost_matrix = get_cost_matrix(similarities, mappings)
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

    def print_alignment(self, filename):
        program_output = open(filename, 'w')
        program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(metatype='metatype',
                                                                                        system_cluster='system_cluster',
                                                                                        gold_cluster='gold_cluster',
                                                                                        similarity='similarity'))
        self.print_entities_and_events_alignment(program_output)
        self.print_relations_alignment(program_output)
        program_output.close()

    def print_entities_and_events_alignment(self, program_output):
        for gold_cluster_id in sorted(self.get('clusters').get('gold')):
            gold_cluster_metatype = self.get('metatype', 'gold', gold_cluster_id)
            system_cluster_id = 'None'
            similarity = 0
            if gold_cluster_id in self.get('alignment').get('gold_to_system'):
                system_cluster_id = self.get('alignment').get('gold_to_system')[gold_cluster_id]['aligned_to']
                system_cluster_metatype = self.get('metatype', 'system', system_cluster_id)
                if gold_cluster_metatype != system_cluster_metatype:
                    self.get('logger').record_event('METATYPE_MISMATCH', system_cluster_id, gold_cluster_metatype, system_cluster_metatype)
                similarity = self.get('alignment').get('gold_to_system')[gold_cluster_id]['aligned_similarity']
            program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(metatype=gold_cluster_metatype,
                                                                                        system_cluster=system_cluster_id,
                                                                                        gold_cluster=gold_cluster_id,
                                                                                        similarity=similarity))

        for system_cluster_id in sorted(self.get('clusters').get('system')):
            if system_cluster_id not in self.get('alignment').get('system_to_gold'):
                program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(
                    metatype=self.get('metatype', 'system', system_cluster_id),
                    system_cluster=system_cluster_id, gold_cluster='None', similarity=0))

    def print_relations_alignment(self, program_output):
        for gold_cluster_id in sorted(self.get('frames').get('gold')):
            gold_cluster_metatype = self.get('metatype', 'gold', gold_cluster_id)
            system_cluster_id = 'None'
            similarity = 0
            if gold_cluster_id in self.get('alignment').get('gold_to_system'):
                system_cluster_id = self.get('alignment').get('gold_to_system')[gold_cluster_id]['aligned_to']
                system_cluster_metatype = self.get('metatype', 'system', system_cluster_id)
                if gold_cluster_metatype != system_cluster_metatype:
                    self.get('logger').record_event('METATYPE_MISMATCH', system_cluster_id, gold_cluster_metatype, system_cluster_metatype)
                similarity = self.get('alignment').get('gold_to_system')[gold_cluster_id]['aligned_similarity']
            program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(metatype=gold_cluster_metatype,
                                                                                       system_cluster=system_cluster_id,
                                                                                       gold_cluster=gold_cluster_id,
                                                                                       similarity=similarity))

        for system_cluster_id in sorted(self.get('frames').get('system')):
            if system_cluster_id not in self.get('alignment').get('system_to_gold'):
                program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(
                    metatype = self.get('metatype', 'system', system_cluster_id),
                    system_cluster=system_cluster_id, gold_cluster='None', similarity=0))

    def print_similarities(self, output_file):
        program_output = open(output_file, 'w')
        program_output.write('{metatype}\t{system_or_gold}\t{cluster1}\t{cluster2}\t{similarity}\n'.format(metatype='metatype',
                                                                                        system_or_gold='system_or_gold',
                                                                                        cluster1='cluster1',
                                                                                        cluster2='cluster2',
                                                                                        similarity='similarity'))
        for system_or_gold in ['system', 'gold']:
            for cluster1 in self.get('clusters').get(system_or_gold).values():
                for cluster2 in self.get('clusters').get(system_or_gold).values():
                    if cluster1.get('metatype') == cluster2.get('metatype'):
                        similarity = self.get('similarity', cluster1, cluster2)
                        program_output.write('{metatype}\t{system_or_gold}\t{cluster1}\t{cluster2}\t{similarity}\n'.format(metatype=cluster1.get('metatype'),
                                                                                system_or_gold=system_or_gold,
                                                                                cluster1=cluster1.get('ID'),
                                                                                cluster2=cluster2.get('ID'),
                                                                                similarity=similarity))
        program_output.close()