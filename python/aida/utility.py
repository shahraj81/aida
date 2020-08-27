"""
Utility functions for AIDA
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "28 January 2020"

from aida.span import Span
from aida.object import Object
import copy
import hashlib
import re
import sys

def get_max_similarity(similarities):
    max_similarity = -1 * sys.maxsize
    for i in similarities:
        for j in similarities[i]:
            if similarities[i][j] > max_similarity:
                max_similarity = similarities[i][j]
    return max_similarity

def get_cost_matrix(similarities, mappings):
    max_similarity = get_max_similarity(similarities)
    cost_matrix = []
    for gold_index in sorted(mappings['gold']['index_to_id']):
        cost_row = []
        gold_id = mappings['gold']['index_to_id'][gold_index]
        for system_index in sorted(mappings['system']['index_to_id']):
            system_id = mappings['system']['index_to_id'][system_index]
            similarity = 0
            if gold_id in similarities and system_id in similarities[gold_id]:
                similarity = similarities[gold_id][system_id]
            cost_row += [max_similarity - similarity]
        cost_matrix += [cost_row]
    return cost_matrix

def get_expanded_types(metatype, cluster_type):
    """
    If the cluster represents an entity:
        If the type is:
            'A.B.C' return ['A', 'A.B', 'A.B.C']
            'A.B'   return ['A', A.B']
            'A'     return ['A']
    If the cluster represents an event or a relation:
        If the type is:
            'A.B.C' return [A.B', 'A.B.C']
            'A.B'   return [A.B']
    """
    expanded_types = {}
    elements = cluster_type.split('.')
    for end_index in range(len(elements)):
        if metatype != 'Entity' and end_index == 0: continue
        start_index = 0
        expanded_type_elements = []
        while start_index <= end_index:
            expanded_type_elements.append(elements[start_index])
            start_index += 1
        if len(expanded_type_elements):
            expanded_types['.'.join(expanded_type_elements)] = 1
    return list(expanded_types.keys())

def spanstring_to_object(logger, span_string, where=None):
    pattern = re.compile('^(.*?):(.*?):\((\S+),(\S+)\)-\((\S+),(\S+)\)$')
    match = pattern.match(span_string)
    mention = Object(logger)
    if match:
        document_id = match.group(1)
        document_element_id, keyframe_id = parse_document_element_id(match.group(2))
        span = Span(logger, match.group(3), match.group(4), match.group(5), match.group(6))
        mention.set('span_string', span_string)
        mention.set('document_id', document_id)
        mention.set('document_element_id', document_element_id)
        mention.set('keyframe_id', keyframe_id)
        mention.set('span', span)
        mention.set('where', where)
    else:
        logger.record_event('UNEXPECTED_SPAN_FORMAT', span_string, where)
    return mention

def string_to_span(logger, span_string, where=None):
    pattern = re.compile('^\((\S+),(\S+)\)-\((\S+),(\S+)\)$')
    match = pattern.match(span_string)
    span = None
    if match:
        span = Span(logger, match.group(1), match.group(2), match.group(3), match.group(4))
    else:
        logger.record_event('UNEXPECTED_SPAN_FORMAT', span_string, where)
    return span

def trim_cv(cv):
    return float(trim(cv))

def trim(value):
    return value.replace('"','')

def parse_document_element_id(s):
    document_element_id = s
    keyframe_id = None
    pattern = re.compile('^(.*)_(\d+)$')
    match = pattern.match(s)
    if match:
        document_element_id = match.group(1)
        keyframe_id = s
    return document_element_id, keyframe_id

def get_deepcopy_of_mention_object(m):
    # this function is a hack around the error thrown by
    # copy.deepcopy() inside the docker container.
    mc = spanstring_to_object(m.get('logger'), m.get('span_string'), m.get('where'))
    mc.set('boundary', m.get('boundary').get('copy'))
    for copy_attribure in ['ID', 'cm_cv', 'j_cv', 'modality', 't_cv']:
        mc.set(copy_attribure, m.get(copy_attribure))
    return mc

def get_kb_document_id_from_filename(filename):
    """
    Gets the source document ID of the KB from filename provided as argument.
    """
    return filename.split(r'/')[-2][:-4]

def get_md5_from_string(text):
    """
    Gets the MD5 sum of a string passed as argument provided as argument.
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_query_id_from_filename(filename):
    """
    Gets the queryid from filename.
    """
    return filename.split(r'/')[-1][:-7]

def get_linear_overlap(start1, end1, start2, end2, text_modality=False):
    s1 = float(start1)
    e1 = float(end1)
    s2 = float(start2)
    e2 = float(end2)
    overlap = 0
    if s2 <= s1 <= e2 or s2 <= e1 <= e2 or s1 <= s2 <= e1 or s1 <= e2 <= e1:
        overlap = min(e1, e2) - max(s1, s2) + (1 if text_modality else 0)
    return overlap

def get_intersection(m1, m2):
    intersection = 0
    dx = get_linear_overlap(m1.get('span').get('start_x'), m1.get('span').get('end_x'), m2.get('span').get('start_x'), m2.get('span').get('end_x'))
    dy = get_linear_overlap(m1.get('span').get('start_y'), m1.get('span').get('end_y'), m2.get('span').get('start_y'), m2.get('span').get('end_y'))
    if dx and dy:
        intersection = dx*dy
    elif dx:
        intersection = dx
    elif dy:
        intersection = dy
    return intersection

def get_union(m1, m2):
    union = 0
    for m in [m1, m2]:
        union += get_intersection(m, m)
    union -= get_intersection(m1, m2)
    return union

def get_augmented_type(region_types, cluster_type):
    if cluster_type is None:
        return
    if cluster_type in region_types:
        return cluster_type
    coarse_grain_type = None
    if "." in cluster_type:
        type_elements = cluster_type.split('.')
        type_elements.pop()
        coarse_grain_type = '.'.join(type_elements)
    return get_augmented_type(region_types, coarse_grain_type)

def get_augmented_types_utility(region_types, types):
    augmented_types = {}
    for cluster_type in types:
        augmented_type = get_augmented_type(region_types, cluster_type)
        augmented_types[augmented_type] = 1
    return set(list(augmented_types.keys()))

def get_intersection_over_union(m1, m2):
    logger = m1.get('logger')
    intersection_over_union = 0
    if m1.get('document_id') == m2.get('document_id'):
        if m1.get('document_element_id') == m2.get('document_element_id'):
            modality = m1.get('modality')
            if modality == 'text':
                intersection_over_union = get_intersection_over_union_text(m1, m2)
            elif modality == 'image':
                intersection_over_union = get_intersection_over_union_image(m1, m2)
            elif modality == 'video':
                if m1.get('keyframe_id'):
                    intersection_over_union = get_intersection_over_union_image(m1, m2)
                else:
                    intersection_over_union = get_intersection_over_union_video(m1, m2)
            else:
                logger.record_event('DEFAULT_CRITICAL', 'Code does not handle modality: {}'.format(modality), m1.get('code_location'))
    return intersection_over_union

def get_intersection_over_union_text(m1, m2):
    start1, end1 = [float(m1.get('span').get(f)) for f in ['start_x', 'end_x']]
    start2, end2 = [float(m2.get('span').get(f)) for f in ['start_x', 'end_x']]
    intersection = get_linear_overlap(start1, end1, start2, end2, text_modality=True)
    union = (end1-start1+1) + (end2-start2+1) - intersection
    intersection_over_union = 0 if union == 0 else intersection/union
    return intersection_over_union

def get_intersection_over_union_image(m1, m2, collar = 1):
    m1c = get_deepcopy_of_mention_object(m1)
    m2c = get_deepcopy_of_mention_object(m2)
    for m in [m1c, m2c]:
        for d in ['x', 'y']:
            start_fieldname = 'start_{}'.format(d)
            end_fieldname = 'end_{}'.format(d)
            start, end = [float(m.get('span').get(k)) for k in [start_fieldname, end_fieldname]]
            min, max = [float(m.get('boundary').get(k)) for k in [start_fieldname, end_fieldname]]
            start -= collar
            end += collar
            if start < min:
                start = min
            if end > max:
                end = max
            m.get('span').set(start_fieldname, start)
            m.get('span').set(end_fieldname, end)
    intersection = get_intersection(m1c, m2c)
    union = get_union(m1c, m2c)
    intersection_over_union = 0 if union == 0 else intersection/union
    return intersection_over_union

def get_intersection_over_union_video(m1, m2, collar = 0.01):
    m1c = get_deepcopy_of_mention_object(m1)
    m2c = get_deepcopy_of_mention_object(m2)
    for m in [m1c, m2c]:
        start, end = [float(m.get('span').get(k)) for k in ['start_x', 'end_x']]
        min, max = [float(m.get('boundary').get(k)) for k in ['start_x', 'end_x']]
        start -= collar
        end += collar
        if start < min:
            start = min
        if end > max:
            end = max
        m.get('span').set('start_x', start)
        m.get('span').set('end_x', end)
    intersection = get_intersection(m1c, m2c)
    union = get_union(m1c, m2c)
    intersection_over_union = 0 if union == 0 else intersection/union
    return intersection_over_union

def get_precision_recall_and_f1(relevant, retrieved):
    precision = len(relevant & retrieved) / len(retrieved) if len(retrieved) else 0
    recall = len(relevant & retrieved) / len(relevant)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return precision, recall, f1

def is_number(s):
    """
    Checks if the argument is numeric.

    Return True if the argument is a number, False otherwise.
    """
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True

def types_are_compatible(entity_type_in_query, entity_type_in_response):
    """
    Determine if two types 'entity_type_in_query' and 'entity_type_in_response',
    provided as argument, are compatible.

    Conclude the types to be compatible if they were the same, or if the type in
    response was a fine-grain instance of that in the query. A type (say, TYPEA) is
    said to be a fine-grain instance of another type (say, TYPEB) if the former has
    the latter as its proper-prefix, i.e. TYPEA can be written as TYPEB.TYPEC, where
    TYPEC is some fine type of TYPEB.
    """
    if entity_type_in_query == entity_type_in_response:
        return True
    if entity_type_in_response.startswith('{}.'.format(entity_type_in_query)):
        return True
    return False