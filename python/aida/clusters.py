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
from aida.utility import get_cost_matrix, get_intersection_over_union
from munkres import Munkres

class Clusters(Object):
    """
    The container to hold Clusters.
    """

    def __init__(self, logger, document_mappings, document_boundaries, annotated_regions, gold_mentions_filename, gold_edges_filename, system_mentions_filename, system_edges_filename, thresholds, weighted='no'):
        """
        Initialize the Clusters.
        """
        super().__init__(logger)
        self.document_mappings = document_mappings
        self.document_boundaries = document_boundaries
        self.annotated_regions = annotated_regions
        self.filenames = Container(logger)
        self.filenames.add(key='gold', value={'mentions': gold_mentions_filename, 'edges': gold_edges_filename})
        self.filenames.add(key='system', value={'mentions': system_mentions_filename, 'edges': system_edges_filename})
        self.clusters = {'gold': Container(logger), 'system': Container(logger)}
        self.frames = {'gold': Container(logger), 'system': Container(logger)}
        self.alignment = {'gold_to_system': {}, 'system_to_gold': {}}
        self.thresholds = thresholds
        self.weighted = weighted
        self.load()
        self.align_clusters()

    def get_cluster(self, gold_or_system, cluster_id):
        return self.get('clusters').get(gold_or_system).get(cluster_id)

    def get_frame(self, gold_or_system, frame_id):
        return self.get('frames').get(gold_or_system).get(frame_id)

    def get_entities_and_events_similarities(self):
        similarities = {}
        for gold_cluster in self.get('clusters').get('gold').values():
            if not gold_cluster.is_alignable_entity_or_event(self.get('annotated_regions')): continue
            for system_cluster in self.get('clusters').get('system').values():
                if not system_cluster.is_alignable_entity_or_event(self.get('annotated_regions')): continue
                similarity = 0
                if gold_cluster.get('metatype') == system_cluster.get('metatype'):
                    similarity = self.get('similarity', 'gold', gold_cluster, 'system', system_cluster)
                if gold_cluster.get('ID') not in similarities:
                    similarities[gold_cluster.get('ID')] = {}
                similarities[gold_cluster.get('ID')][system_cluster.get('ID')] = similarity
        return similarities

    def get_relation_similarities(self):
        similarities = {}
        for gold_frame in self.get('frames').get('gold').values():
            if not gold_frame.is_alignable_relation(): continue
            for system_frame in self.get('frames').get('system').values():
                if not system_frame.is_alignable_relation(): continue
                if gold_frame.get('ID') not in similarities:
                    similarities[gold_frame.get('ID')] = {}
                similarities[gold_frame.get('ID')][system_frame.get('ID')] = self.get('similarity', 'gold', gold_frame, 'system', system_frame)
        return similarities

    def get_similarity(self, system_or_gold1, cluster_or_frame1, system_or_gold2, cluster_or_frame2):
        if cluster_or_frame1.get('metatype') == 'Relation' and cluster_or_frame2.get('metatype') == 'Relation':
            if isinstance(cluster_or_frame1, Cluster):
                cluster_or_frame1 = self.get('frame', system_or_gold1, cluster_or_frame1.get('ID'))
            if isinstance(cluster_or_frame2, Cluster):
                cluster_or_frame2 = self.get('frame', system_or_gold2, cluster_or_frame2.get('ID'))
            if cluster_or_frame1 and cluster_or_frame2:
                if cluster_or_frame1.is_alignable_relation() and cluster_or_frame2.is_alignable_relation():
                    return self.get('relation_similarity', system_or_gold1, cluster_or_frame1, system_or_gold2, cluster_or_frame2)
            return 0
        elif cluster_or_frame1.get('metatype') in ['Entity', 'Event'] and cluster_or_frame2.get('metatype') in ['Entity', 'Event'] and cluster_or_frame1.get('metatype') == cluster_or_frame2.get('metatype'):
            return self.get('entity_and_event_similarity', cluster_or_frame1, cluster_or_frame2)
        else:
            self.record_event('DEFAULT_CRITICAL_ERROR', "unexpected combination of gold and system", self.get('code_location'))

    def get_relation_similarity(self, system_or_gold1, frame1, system_or_gold2, frame2):
        options = {'gold': 1, 'system': 1}
        for system_or_gold in [system_or_gold1, system_or_gold2]:
            if system_or_gold not in options:
                self.record_event('DEFAULT_CRITICAL_ERROR', 'Unexpected value for system_or_gold: {}'.format(system_or_gold))
        if system_or_gold1 != system_or_gold2:
            gold_frame = frame2
            system_frame = frame1
            if system_or_gold1 == 'gold' and system_or_gold2 == 'system':
                gold_frame = frame1
                system_frame = frame2
            return self.get('gold_system_relation_similarity', gold_frame, system_frame)
        else:
            return self.get('relation_self_similarity', system_or_gold1, frame1, frame2)

    def get_relation_self_similarity(self, system_or_gold, frame1, frame2):
        num_fillers_aligned = 0
        if self.get('number_of_matching_types', frame1.get('top_level_types'), frame2.get('top_level_types')):
            found = {}
            for rolename in frame1.get('role_fillers') if frame1.get('role_fillers') else []:
                frame1_fillers = list(frame1.get('role_fillers')[rolename])
                for frame1_filler_id in frame1_fillers:
                    rolename_and_filler = '{}:{}'.format(rolename, frame1_filler_id)
                    found[rolename_and_filler] = 0
                frame2_fillers = list(frame2.get('role_fillers')[rolename]) if rolename in frame2.get('role_fillers') else []
                for frame2_filler_id in frame2_fillers:
                    rolename_and_filler = '{}:{}'.format(rolename, frame2_filler_id)
                    if rolename_and_filler in found:
                        found[rolename_and_filler] = 1
                    else:
                        found[rolename_and_filler] = 0
            for rolename_and_filler in found:
                if found[rolename_and_filler] == 1:
                    num_fillers_aligned += 1
        if num_fillers_aligned > 2 and system_or_gold == 'gold' :
                self.record_event('DEFAULT_CRITICAL_ERROR', 'num_fillers_aligned > 2: Gold frames: {} and {}'.format(frame1.get('ID'), frame2.get('ID')))
        return 0 if num_fillers_aligned <= 1 else 1

    def get_gold_system_relation_similarity(self, gold_frame, system_frame):
        num_fillers_aligned = 0
        if self.get('number_of_matching_types', gold_frame.get('top_level_types'), system_frame.get('top_level_types')):
            found = {}
            for rolename in gold_frame.get('role_fillers') if gold_frame.get('role_fillers') else []:
                gold_fillers = list(gold_frame.get('role_fillers')[rolename])
                for gold_filler_id in gold_fillers:
                    rolename_and_filler = '{}:{}'.format(rolename, gold_filler_id)
                    found[rolename_and_filler] = 0
                system_fillers = list(system_frame.get('role_fillers')[rolename]) if rolename in system_frame.get('role_fillers') else []
                for system_filler_id in system_fillers:
                    gold_aligned_system_filler_mapping_object = self.get('alignment').get('system_to_gold').get(system_filler_id, None)
                    if gold_aligned_system_filler_mapping_object:
                        aligned_gold_id = gold_aligned_system_filler_mapping_object.get('aligned_to')
                        rolename_and_filler = '{}:{}'.format(rolename, aligned_gold_id)
                        if rolename_and_filler in found:
                            found[rolename_and_filler] = 1
            for rolename_and_filler in found:
                if found[rolename_and_filler] == 1:
                    num_fillers_aligned += 1
        if num_fillers_aligned > 2:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'num_fillers_aligned > 2: Gold frame: {}'.format(gold_frame.get('ID')))
        return 0 if num_fillers_aligned <= 1 else 1

    def get_metatype(self, gold_or_system, cluster_or_frame_id):
        cluster_id = self.get('clusters').get(gold_or_system).get(cluster_or_frame_id)
        frame_id = self.get('frames').get(gold_or_system).get(cluster_or_frame_id)
        metatype = None
        if cluster_id and frame_id:
            if cluster_id.get('metatype') != frame_id.get('metatype'):
                self.get('logger').record_event('METATYPE_MISMATCH', cluster_or_frame_id, cluster_id.get('metatype'), frame_id.get('metatype'))
            else:
                metatype = cluster_id.get('metatype')
        else:
            cluster_or_frame = cluster_id or frame_id
            metatype = cluster_or_frame.get('metatype')
        return metatype

    def get_number_of_matching_types(self, gold_types, system_types):
        return len(set(gold_types) & set(system_types))

    def get_threshold(self, modality, language):
        threshold = None
        if modality == 'text':
            threshold = self.get('thresholds').get(language)
        else:
            threshold = self.get('thresholds').get(modality)
        if threshold is None:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'Unable to determine threshold for modality \'{}\' and language \'{}\''.format(modality, language))
        return threshold

    def get_entity_and_event_similarity(self, gold_cluster, system_cluster):
        similarity = 0
        if self.get('number_of_matching_types', gold_cluster.get('top_level_types'), system_cluster.get('top_level_types')):
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
                document_element_id = gold_mention.get('document_element_id')
                modality = self.get('document_mappings').get('modality', document_element_id)
                language = self.get('document_mappings').get('language', document_element_id)
                for system_mention in mentions['system']:
                    if gold_mention.get('ID') not in similarities:
                        similarities[gold_mention.get('ID')] = {}
                    iou = get_intersection_over_union(gold_mention, system_mention)
                    iou = 0 if iou < self.get('threshold', modality, language) else iou
                    similarities[gold_mention.get('ID')][system_mention.get('ID')] = iou
            cost_matrix = get_cost_matrix(similarities, mappings)
            alignment = {'gold_mention': {}, 'system_mention': {}}
            for gold_mention_index, system_mention_index in Munkres().compute(cost_matrix):
                gold_mention_id = mappings['gold']['index_to_id'][gold_mention_index]
                system_mention_id = mappings['system']['index_to_id'][system_mention_index]
                alignment['gold_mention'][gold_mention_id] = {'system_mention': system_mention_id, 'score': similarities[gold_mention_id][system_mention_id]}
                alignment['system_mention'][system_mention_id] = {'gold_mention': gold_mention_id, 'score': similarities[gold_mention_id][system_mention_id]}
                if similarities[gold_mention_id][system_mention_id] > 0:
                    # lenient similarity computation
                    if self.get('weighted') == 'no':
                        # total mentions
                        similarity += 1
                    elif self.get('weighted') == 'yes':
                        # total iou
                        similarity += similarities[gold_mention_id][system_mention_id]
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
        if self.get('filenames').get(filetype).get('mentions') is None: return
        for entry in FileHandler(self.get('logger'), self.get('filenames').get(filetype).get('mentions')):
            cluster_id = entry.get('?cluster')
            if not clusters.exists(cluster_id):
                clusters.add(key=cluster_id, value=Cluster(logger, self.get('document_mappings'), self.get('document_boundaries'), cluster_id))
            cluster = clusters.get(cluster_id)
            cluster.add(entry)

    def load_frames(self, filetype):
        logger = self.get('logger')
        frames = self.get('frames').get(filetype)
        if self.get('filenames').get(filetype).get('edges') is None: return
        for entry in FileHandler(self.get('logger'), self.get('filenames').get(filetype).get('edges')):
            # get edge_id
            frame_id = entry.get('?subject')
            if not frames.exists(frame_id):
                frames.add(key=frame_id, value=EventOrRelationFrame(logger, frame_id, entry.get('where')))
            frame = frames.get(frame_id)
            frame.update(entry)

    def align_clusters(self):
        self.align_entities_and_events()
        self.align_relations()

    def record_alignment(self, similarities, mappings):
        if len(similarities) == 0:
            return
        cost_matrix = get_cost_matrix(similarities, mappings)
        for gold_cluster_index, system_cluster_index in Munkres().compute(cost_matrix):
            gold_cluster = self.get('cluster', 'gold', mappings['gold']['index_to_id'][gold_cluster_index])
            system_cluster = self.get('cluster', 'system', mappings['system']['index_to_id'][system_cluster_index])
            similarity = self.lookup_similarity(similarities, gold_cluster.get('ID'), system_cluster.get('ID'))
            if similarity > 0:
                self.get('alignment').get('gold_to_system')[gold_cluster.get('ID')] = {
                        'aligned_to': system_cluster.get('ID'),
                        'aligned_similarity': similarity
                    }
                self.get('alignment').get('system_to_gold')[system_cluster.get('ID')] = {
                        'aligned_to': gold_cluster.get('ID'),
                        'aligned_similarity': similarity
                    }

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
        self.record_alignment(self.get('entities_and_events_similarities'), mappings)

    def align_relations(self):
        mappings = {}
        for filetype in ['gold', 'system']:
            mappings[filetype] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0;
            for frame_id in sorted(self.get('frames').get(filetype)):
                if self.get('frame', filetype, frame_id).is_alignable_relation():
                    mappings[filetype]['id_to_index'][frame_id] = index
                    mappings[filetype]['index_to_id'][index] = frame_id
                    index += 1
        self.record_alignment(self.get('relation_similarities'), mappings)

    def lookup_similarity(self, similarities, gold_cluster_id, system_cluster_id):
        if gold_cluster_id in similarities:
            if system_cluster_id in similarities.get(gold_cluster_id):
                return similarities.get(gold_cluster_id).get(system_cluster_id)
        return 0

    def print_alignment(self, filename):
        program_output = open(filename, 'w')
        program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(metatype='metatype',
                                                                                        system_cluster='system_cluster',
                                                                                        gold_cluster='gold_cluster',
                                                                                        similarity='similarity'))
        for gold_cluster_id in sorted(self.get('clusters').get('gold')):
            gold_cluster_metatype = self.get('metatype', 'gold', gold_cluster_id)
            if gold_cluster_metatype == 'Relation':
                if gold_cluster_id not in self.get('frames').get('gold'): continue
                if not self.get('frame', 'gold', gold_cluster_id).is_alignable_relation(): continue
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
            system_cluster_metatype = self.get('metatype', 'system', system_cluster_id)
            if system_cluster_metatype == 'Relation':
                if system_cluster_id not in self.get('frames').get('system'): continue
                if not self.get('frame', 'system', system_cluster_id).is_alignable_relation(): continue
            if system_cluster_id not in self.get('alignment').get('system_to_gold'):
                program_output.write('{metatype}\t{system_cluster}\t{gold_cluster}\t{similarity}\n'.format(
                    metatype=self.get('metatype', 'system', system_cluster_id),
                    system_cluster=system_cluster_id, gold_cluster='None', similarity=0))
        program_output.close()

    def print_similarities(self, output_file):
        program_output = open(output_file, 'w')
        program_output.write('{metatype}\t{system_or_gold1}\t{cluster1}\t{system_or_gold2}\t{cluster2}\t{similarity}\n'.format(metatype='metatype',
                                                                                        system_or_gold1='system_or_gold1',
                                                                                        system_or_gold2='system_or_gold2',
                                                                                        cluster1='cluster1',
                                                                                        cluster2='cluster2',
                                                                                        similarity='similarity'))
        for system_or_gold1, system_or_gold2 in [('system', 'system'), ('system', 'gold'), ('gold', 'gold')]:
            for cluster1 in self.get('clusters').get(system_or_gold1).values():
                for cluster2 in self.get('clusters').get(system_or_gold2).values():
                    if cluster1.get('metatype') == cluster2.get('metatype'):
                        similarity = self.get('similarity', system_or_gold1, cluster1, system_or_gold2, cluster2)
                        program_output.write('{metatype}\t{system_or_gold1}\t{cluster1}\t{system_or_gold2}\t{cluster2}\t{similarity}\n'.format(metatype=cluster1.get('metatype'),
                                                                                                                                               system_or_gold1=system_or_gold1,
                                                                                                                                               system_or_gold2=system_or_gold2,
                                                                                                                                               cluster1=cluster1.get('ID'),
                                                                                                                                               cluster2=cluster2.get('ID'),
                                                                                                                                               similarity=similarity))
        program_output.close()