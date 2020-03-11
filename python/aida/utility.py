"""
Utility functions for AIDA
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "28 January 2020"

# from collections import defaultdict
# from math import sqrt
# from copy import deepcopy
import hashlib
# import re
            
#             sorted_spans = {}
#             for span in document_spans[document_id]:
#                 if span.get('span_type') == 'text':
#                     code_map = {'nam':'named', 'nom':'others', 'pro':'pronominal', 'EMPTY_NA':'pronominal'}
#                     mention_type = mention.get('entry').get('level')
#                     key = code_map[mention_type]                    
#                 else:
#                     key = 'others'
#                 if key not in sorted_spans:
#                     sorted_spans[key] = []
#                 sorted_spans[key].append(span)
#             selected_mention_type = None
#             if 'named' in sorted_spans:
#                 selected_mention_type = 'named'
#             elif 'others' in sorted_spans:
#                 selected_mention_type = 'others'
#             elif 'pronominal' in sorted_spans:
#                 selected_mention_type = 'pronominal'
#             candidate_spans = sorted_spans[selected_mention_type] if selected_mention_type is not None else []
#             informative_justification_span = get_informative_justification_span(candidate_spans)
#             informative_justification_spans[document_id] = informative_justification_span

# def get_distance_from_origin(start_or_end, span):
#     return sqrt(float(span.get('span').get('{}_x'.format(start_or_end)))**2 + float(span.get('span').get('{}_y'.format(start_or_end)))**2)

# def get_informative_justification_span(object_id, mention_spans):
#     default_priority = {
#         'named':        1,
#         'image':        2,
#         'nominal':      3,
#         'picture':      4,
#         'sound':        5,
#         'keyframe':     6,
#         'audio':        7,
#         'pronominal':   8,
#         }
#     for mention_span in mention_spans:
#         logger = mention_span.get('logger')
#         mention = mention_span.get('mention')
#         span = mention_span.get('span')
#         ere_type = mention.get('node_metatype')
#         priority = deepcopy(default_priority)
#         # for an entity we would prefer keyframe mentions over start
#         # and end time offsets
#         if ere_type == 'entity':
#             priority['keyframe'] = 4
#             priority['picture'] = 5
#             priority['sound'] = 6
#         
# 
# def get_informative_justification_span_alpha(object_id, mention_spans):
#     """
#     get informative justification span from those provided as part of the argument.
#     'mention_spans' contains a list of 'mention_span' from a document
#     'mention_span' contains a 'mention' and a 'span'
#     
#     If the function is called with the following:
#         --------|-----|----
#         modality level span
#         --------|-----|----
#         text     nam   IC001L3WL:IC001L4P1:(11,0)-(15,0)
#         text     nam   IC001L3WL:IC001L4P1:(21,0)-(28,0)
#         text     nam   IC001L3WL:IC001L4P1:(31,0)-(35,0)
#         text     nam   IC001L3WL:IC001L4P1:(41,0)-(48,0)
#         text     nom   IC001L3WL:IC001L4P1:(51,0)-(53,0)
#         text     nom   IC001L3WL:IC001L4P1:(61,0)-(63,0)
#         text     nom   IC001L3WL:IC001L4P1:(71,0)-(80,0)
#         text     pro   IC001L3WL:IC001L4P1:(85,0)-(88,0)
#         text     pro   IC001L3WL:IC001L4P1:(95,0)-(98,0)
#         text     pro   IC001L3WL:IC001L4P1:(105,0)-(106,0)
#         image    nil   IC001L3WL:IC001L3UT:(10,20)-(30,40)
#         image    nil   IC001L3WL:IC001L3UT:(50,60)-(70,80)
#         image    nil   IC001L3WL:IC001L3UR:(10,20)-(30,40)
#         image    nil   IC001L3WL:IC001L3UR:(50,60)-(80,80)
#         picture  nil   IC001L3WL:IC001L3U3:(5.3,0)-(10.8,0)
#         picture  nil   IC001L3WL:IC001L3U3:(15.3,0)-(20.8,0)
#         sound    nil   IC001L3WL:IC001L3U3:(25.3,0)-(34.8,0)
#         sound    nil   IC001L3WL:IC001L3U3:(55.3,0)-(58.8,0)
#         picture  nil   IC001L3WL:IC001IAKD:(5.3,0)-(10.8,0)
#         picture  nil   IC001L3WL:IC001IAKD:(15.3,0)-(20.8,0)
#         sound    nil   IC001L3WL:IC001IAKD:(25.3,0)-(34.8,0)
#         sound    nil   IC001L3WL:IC001IAKD:(55.3,0)-(58.8,0)
#         keyframe nil   IC001L3WL:IC001IAKD_1:(10,20)-(30,40)
#         keyframe nil   IC001L3WL:IC001IAKD_2:(50,60)-(70,80)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(10,20)-(30,40)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(50,60)-(80,80)
#         
#     It should return the longest named mention which is closest to the origin which in this case is
#     IC001L3WL:IC001L4P1:(21,0)-(28,0)
# 
#     If the function is called with the following:
#         --------|-----|----
#         modality level span
#         --------|-----|----
#         text     nom   IC001L3WL:IC001L4P1:(51,0)-(53,0)
#         text     nom   IC001L3WL:IC001L4P1:(61,0)-(63,0)
#         text     nom   IC001L3WL:IC001L4P1:(71,0)-(80,0)
#         text     pro   IC001L3WL:IC001L4P1:(85,0)-(88,0)
#         text     pro   IC001L3WL:IC001L4P1:(95,0)-(98,0)
#         text     pro   IC001L3WL:IC001L4P1:(105,0)-(106,0)
#         image    nil   IC001L3WL:IC001L3UT:(10,20)-(30,40)
#         image    nil   IC001L3WL:IC001L3UT:(50,60)-(70,80)
#         image    nil   IC001L3WL:IC001L3UR:(10,20)-(30,40)
#         image    nil   IC001L3WL:IC001L3UR:(50,60)-(80,80)
#         picture  nil   IC001L3WL:IC001L3U3:(5.3,0)-(10.8,0)
#         picture  nil   IC001L3WL:IC001L3U3:(15.3,0)-(20.8,0)
#         sound    nil   IC001L3WL:IC001L3U3:(25.3,0)-(34.8,0)
#         sound    nil   IC001L3WL:IC001L3U3:(55.3,0)-(58.8,0)
#         picture  nil   IC001L3WL:IC001IAKD:(5.3,0)-(10.8,0)
#         picture  nil   IC001L3WL:IC001IAKD:(15.3,0)-(20.8,0)
#         sound    nil   IC001L3WL:IC001IAKD:(25.3,0)-(34.8,0)
#         sound    nil   IC001L3WL:IC001IAKD:(55.3,0)-(58.8,0)
#         keyframe nil   IC001L3WL:IC001IAKD_1:(10,20)-(30,40)
#         keyframe nil   IC001L3WL:IC001IAKD_2:(50,60)-(70,80)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(10,20)-(30,40)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(50,60)-(80,80)
#         
#     It should return IC001L3WL:IC001L3U3_4:(50,60)-(80,80)
#     """
# 
# 
# 
# 
#     from aida.document_span import DocumentSpan
#     from aida.object import Object
#     test_spans = """text     nom   IC001L3WL:IC001L4P1:(51,0)-(53,0)
#         text     nom   IC001L3WL:IC001L4P1:(61,0)-(63,0)
#         text     nom   IC001L3WL:IC001L4P1:(71,0)-(80,0)
#         text     pro   IC001L3WL:IC001L4P1:(85,0)-(88,0)
#         text     pro   IC001L3WL:IC001L4P1:(95,0)-(98,0)
#         text     pro   IC001L3WL:IC001L4P1:(105,0)-(106,0)
#         image    nil   IC001L3WL:IC001L3UT:(10,20)-(30,40)
#         image    nil   IC001L3WL:IC001L3UT:(50,60)-(80,80)
#         image    nil   IC001L3WL:IC001L3UR:(10,20)-(30,40)
#         image    nil   IC001L3WL:IC001L3UR:(50,60)-(80,80)
#         picture  nil   IC001L3WL:IC001L3U3:(5.3,0)-(10.8,0)
#         picture  nil   IC001L3WL:IC001L3U3:(15.3,0)-(20.8,0)
#         sound    nil   IC001L3WL:IC001L3U3:(25.3,0)-(34.8,0)
#         sound    nil   IC001L3WL:IC001L3U3:(55.3,0)-(58.8,0)
#         picture  nil   IC001L3WL:IC001IAKD:(5.3,0)-(10.8,0)
#         picture  nil   IC001L3WL:IC001IAKD:(15.3,0)-(20.8,0)
#         sound    nil   IC001L3WL:IC001IAKD:(25.3,0)-(34.8,0)
#         sound    nil   IC001L3WL:IC001IAKD:(55.3,0)-(58.8,0)
#         keyframe nil   IC001L3WL:IC001IAKD_1:(10,20)-(30,40)
#         keyframe nil   IC001L3WL:IC001IAKD_2:(50,60)-(70,80)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(10,20)-(30,40)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(50,60)-(80,80)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(50,65)-(80,85)
#         keyframe nil   IC001L3WL:IC001L3U3_4:(50,60)-(70,90)"""
#      
#     #logger, document_id, document_element_id, keyframe_id, document_element_modality, span_type, start_x, start_y, end_x, end_y, where
#     logger = mention_spans[0].get('logger')
#     mention_spans = []
#     for line in test_spans.split('\n'):
#         print('line is: {}'.format(line))
#         span_type, mention_type, document_span_text = line.split()
#         document_id, document_element_id, span_text = document_span_text.split(':')
#         pattern = re.compile('^\((.*?),(.*?)\)-\((.*?),(.*?)\)$')
#         match = pattern.match(span_text)
#         start_x, start_y, end_x, end_y = map(lambda i : match.group(i), range(1, 5))
#         document_element_modality = '{}'.format(span_type)
#         document_element_modality = 'video' if document_element_modality != 'text' and document_element_modality != 'image' else document_element_modality
#         keyframe_id = None
#         if '_' in document_element_id:
#             keyframe_id = '{}'.format(document_element_id)
#             document_element_id = keyframe_id.split('_')[0]
#         where = None
#         document_span = DocumentSpan(logger, document_id, document_element_id, keyframe_id, document_element_modality, span_type, start_x, start_y, end_x, end_y, where)
#         mention = Object(logger)
#         entry = Object(logger)
#         entry.set(key='level', value=mention_type)
#         mention.set(key='entry', value=entry)
#         mention_span = Object(logger)
#         mention_span.set(key='mention', value=mention)
#         mention_span.set(key='span', value=document_span)
#         mention_spans.append(mention_span)
#         print('moving on...')
# 
# 
# 
# 
# 
#     
#     sorted_spans = {}
#     # sort the spans into named, pronominals or others
#     # informative justification is selected according to the following selection priority:
#     #   first priority: named mention
#     #   second priority: others (nominal, image, video, audio)
#     #   last priority: pronominal
#     for mention_span in mention_spans:
#         mention = mention_span.get('mention')
#         mention_type = mention.get('entry').get('level')
#         span = mention_span.get('span')
#         if span.get('span_type') == 'text':
#             code_map = {'nam':'named', 'nom':'others', 'pro':'pronominal', 'EMPTY_NA':'pronominal'}
#             key = code_map[mention_type]                    
#         else:
#             key = 'others'
#         if key not in sorted_spans:
#             sorted_spans[key] = []
#         sorted_spans[key].append(span)
#     candidate_spans = sorted_spans.get('named', None)
#     candidate_spans = sorted_spans['others'] if 'others' in sorted_spans and candidate_spans is None else candidate_spans
#     candidate_spans = sorted_spans['pronominal'] if 'pronominal' in sorted_spans and candidate_spans is None else candidate_spans
#     # once candidate spans have been found, get the one with the largest area, breaking the ties by picking the first document element by 
#     # sorting the document element IDs alphabetically, and then by picking the span closer to the origin in that document element
#     # (if multiple were available)
#     
#     # select all spans with the largest length/area
#     spans_by_length_or_area = defaultdict(list)
#     for span in candidate_spans:
#         length_or_area = get_span_length_or_area(span)
#         spans_by_length_or_area[length_or_area].append(span)
#     selected_length_or_area = sorted(spans_by_length_or_area, reverse=True)[0]
#     selected_spans_by_length_or_area = spans_by_length_or_area[selected_length_or_area]
#     
#     # if there is exactly one largest span, return it
#     if len(selected_spans_by_length_or_area) == 1:
#         return selected_spans_by_length_or_area[0]
#     
#     # otherwise, break ties by selecting the spans from the document element that is ranked first among all 
#     # document elements when sorted alphabetically
#     spans_by_document_element_or_keyframe_id = defaultdict(list)
#     for span in selected_spans_by_length_or_area:
#         document_element_or_keyframe_id = span.get('document_element_id') if span.get('keyframe_id') is None else span.get('keyframe_id')
#         spans_by_document_element_or_keyframe_id[document_element_or_keyframe_id].append(span)
#     selected_document_element_or_keyframe_id = sorted(spans_by_document_element_or_keyframe_id)[0]
#     selected_spans_by_document_element_or_keyframe_id = spans_by_document_element_or_keyframe_id[selected_document_element_or_keyframe_id]
#     
#     # if there is exactly one span in the selected document, return it
#     if len(selected_spans_by_document_element_or_keyframe_id) == 1:
#         return selected_spans_by_document_element_or_keyframe_id[0]
#     
#     # otherwise, break ties by selecting the spans that has the start closest to the origin
#     spans_by_distance_of_start_from_origin = defaultdict(list)
#     for span in selected_spans_by_document_element_or_keyframe_id:
#         distance_of_start_from_origin = get_distance_from_origin('start', span)
#         spans_by_distance_of_start_from_origin[distance_of_start_from_origin].append(span)
#     selected_distance_of_start_from_origin = sorted(spans_by_distance_of_start_from_origin)[0]
#     selected_spans_by_distance_of_start_from_origin = spans_by_distance_of_start_from_origin[selected_distance_of_start_from_origin]
#     
#     # if there is exactly one span that is the closest to the origin, return it
#     if len(selected_spans_by_distance_of_start_from_origin) == 1:
#         return selected_spans_by_distance_of_start_from_origin[0]
#     
#     # otherwise, in the rare event, when there are multiple spans at this stage,
#     # return the one with the closest x coordinate
#     spans_by_x_corrdinate = defaultdict(list)
#     for span in selected_spans_by_distance_of_start_from_origin:
#         x_coordinate = span.get('span').get('start_x')
#         spans_by_x_corrdinate[x_coordinate].append(span)
#     selected_x_coordinate = sorted(spans_by_x_corrdinate)[0]
#     selected_spans_by_x_coordinate = spans_by_x_corrdinate[selected_x_coordinate]
#     
#     # if there is exactly one span, return it
#     if len(selected_spans_by_x_coordinate) == 1:
#         return selected_spans_by_x_coordinate[0]
#     
#     # otherwise, in the case of possible bug in the code, report this case in logger, and 
#     # return an arbitrary span
#     mention_spans[0].get('logger').record_event('ARBITRARY_INF_JUSTIFICATION', object_id)
#     return selected_spans_by_x_coordinate[0]

def get_kb_document_id_from_filename(filename):
    return filename.split(r'/')[-2][:-4]

def get_md5_from_string(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_query_id_from_filename(filename):
    return filename.split(r'/')[-1][:-7]

# def get_span_length_or_area(span):
#     width = float(span.get('span').get('end_x')) - float(span.get('span').get('start_x'))
#     height = float(span.get('span').get('end_y')) - float(span.get('span').get('start_y'))
#     if height == 0: return width
#     return width * height

def is_number(s):
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True

def types_are_compatible(entity_type_in_query, entity_type_in_response):
    if entity_type_in_query == entity_type_in_response:
        return True
    if entity_type_in_response.startswith('{}.'.format(entity_type_in_query)):
        return True
    return False    