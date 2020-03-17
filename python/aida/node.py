"""
AIDA node class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 January 2020"

from aida.object import Object
from aida.utility import get_md5_from_string
from math import sqrt

class Node(Object):
    """
    AIDA node class.
    """

    def __init__(self, logger, kb_id, metatype, mention):
        super().__init__(logger)
        self.kb_id = kb_id
        self.mentions = {}
        self.metatype = metatype
        if mention is not None:
            self.add_mention(mention)

    def get_prototype(self):
        return list(self.get('mentions').values())[0]

    def add_mention(self, mention):
        node_metatype_from_mention = mention.get('node_metatype')
        if node_metatype_from_mention != self.metatype:
            self.logger.record_event('METATYPE_MISMATCH',
                                     self.kb_id,
                                     self.metatype,
                                     node_metatype_from_mention,
                                     mention.get('where'))
        self.mentions[mention.get('id')] = mention 
    
#     def get_md5(self):
#         return get_md5_from_string(self.get('id'))
    
    def get_id(self):
        return self.get('kb_id')
    
    def get_name(self):
        return self.get('id').replace('|', '-')
        
    def get_informative_justification_spans(self):
        informative_justification_mention_spans = {}
        for mention in self.get('mentions').values():
            for span in mention.get('document_spans').values():
                mention_span = {'mention': mention,
                                'span': span}
                document_id = span.get('document_id')
                if document_id not in informative_justification_mention_spans:
                    informative_justification_mention_spans[document_id] = mention_span
                else:
                    informative_justification_mention_spans[document_id] = self.get('preferred_span', informative_justification_mention_spans[document_id], mention_span)
        informative_justification_spans = {}
        for document_id in informative_justification_mention_spans:
            mention_span = informative_justification_mention_spans[document_id]
            span = mention_span['span']
            informative_justification_spans[document_id] = span
        return informative_justification_spans
    
    def get_preferred_span(self, mention_span1, mention_span2):
        
        def length_of(span):
            return float(span.get('span').get('end_x')) - float(span.get('span').get('start_x'))
        
        def area_of(span):
            width = float(span.get('span').get('end_x')) - float(span.get('span').get('start_x'))
            height = float(span.get('span').get('end_y')) - float(span.get('span').get('start_y'))
            if width == height == 0:
                return float("inf")
            if height == 0: return width
            if width == 0: return height
            return width * height
        
        def category_of(mention, span):
            modality = span.get('document_element_modality')
            level = mention.get('entry').get('level')
            mediamention_signaltype = mention.get('entry').get('mediamention_signaltype')
            if modality == 'text':
                if level == 'nam': return 'named'
                if level == 'nom': return 'nominal'
                return 'pronominal'
            if modality == 'image': return 'image'
            if modality == 'audio': return 'audio'
            if modality == 'video':
                if span.get('keyframe_id'): return 'keyframe'
                if mediamention_signaltype == 'sound_channel_video': return 'sound_channel_video'
                return 'picture_channel_video'
            return
        
        def distance_to_origin_of(span, start_or_end):
            return sqrt(float(span.get('span').get('{}_x'.format(start_or_end)))**2 + float(span.get('span').get('{}_y'.format(start_or_end)))**2)
        
        mention1 = mention_span1['mention']
        span1 = mention_span1['span']
        mention2 = mention_span2['mention']
        span2 = mention_span2['span']
        
        if span1.__str__() == span2.__str__():
            return mention_span1
        priority = {
            'named':                      1,
            'image':                      2,
            'nominal':                    3,
            'picture_channel_video':      4,
            'sound_channel_video':        5,
            'keyframe':                   6,
            'audio':                      7,
            'pronominal':                 8,
            }
        if self.get('metatype') == 'entity':
            priority['keyframe'] = 4
            priority['picture_channel_video'] = 5
            priority['sound_channel_video'] = 6
        span1_priority = priority[category_of(mention1, span1)]
        span2_priority = priority[category_of(mention2, span2)]
        if span1_priority < span2_priority: return mention_span1
        if span2_priority < span1_priority: return mention_span2
        # the spans have the same priority
        # break ties according to other criteria
        modality = span1.get('document_element_modality')
        if modality == 'text':
            # if both spans are from text modality, select the longer
            # of the two to be a candidate informative justification
            if length_of(span1) > length_of(span2): return mention_span1
            if length_of(span2) > length_of(span1): return mention_span2
            # if both spans have the same length, select the one closer
            # to the start of the document
            start_x_span1 = float(span1.get('span').get('start_x'))
            start_x_span2 = float(span2.get('span').get('start_x'))
            if start_x_span1 < start_x_span2: return mention_span1
            return mention_span2
        else:
            # if both spans are from non-text modality, select the
            # span that is more precise
            if area_of(span1) < area_of(span2): return mention_span1
            if area_of(span2) < area_of(span1): return mention_span2
            # both spans have the same area, breaks ties using document element id
            document_element_or_keyframe_id_span1 = span1.get('keyframe_id') if span1.get('keyframe_id') is not None else span1.get('document_element_id')
            document_element_or_keyframe_id_span2 = span2.get('keyframe_id') if span2.get('keyframe_id') is not None else span2.get('document_element_id')
            if document_element_or_keyframe_id_span1 < document_element_or_keyframe_id_span2:
                return mention_span1
            if document_element_or_keyframe_id_span2 < document_element_or_keyframe_id_span1:
                return mention_span2
            # both spans have the same document element id
            if distance_to_origin_of(span1, 'start') < distance_to_origin_of(span2, 'start'):
                return mention_span1
            if distance_to_origin_of(span2, 'start') < distance_to_origin_of(span2, 'start'):
                return mention_span2
            if distance_to_origin_of(span1, 'end') < distance_to_origin_of(span2, 'end'):
                return mention_span1
            if distance_to_origin_of(span2, 'end') < distance_to_origin_of(span2, 'end'):
                return mention_span2
            return
    
#     def get_informative_justification_spans_alpha(self):
#         """
#         returns a list containing one (arbitrarily picked) span per document
#         """
#         document_spans = {}
#         for mention in self.get('mentions').values():
#             for span in mention.get('document_spans').values():
#                 document_id = span.get('document_id')
#                 if document_id not in document_spans:
#                     document_spans[document_id] = []
#                 mention_span = Object(self.get('logger'))
#                 mention_span.set(key='mention', value=mention)
#                 mention_span.set(key='span', value=span)
#                 document_spans[document_id].append(mention_span)
#         informative_justification_spans = {}
#         for document_id in document_spans:
#             informative_justification_span = get_informative_justification_span(self.get('id'), document_spans[document_id])
#             informative_justification_spans[document_id] = informative_justification_span
#         return informative_justification_spans.values()