"""
Utility functions for AIDA
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "28 January 2020"

from aida.span import Span
from aida.object import Object
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

def spanstring_to_object(logger, span_string, where=None):
    pattern = re.compile('^(.*?):(.*?):\((\S+),(\S+)\)-\((\S+),(\S+)\)$')
    match = pattern.match(span_string)
    mention = Object(logger)
    if match:
        document_id = match.group(1)
        document_element_id, keyframe_id = parse_document_element_id(match.group(2))
        span = Span(logger, match.group(3), match.group(4), match.group(5), match.group(6))
        mention.set('document_id', document_id)
        mention.set('document_element_id', document_element_id)
        mention.set('keyframe_id', keyframe_id)
        mention.set('span', span)
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
    return float(cv.replace('"',''))

def parse_document_element_id(s):
    document_element_id = s
    keyframe_id = None
    pattern = re.compile('^(.*)_(\d+)$')
    match = pattern.match(s)
    if match:
        document_element_id = match.group(1)
        keyframe_id = s
    return document_element_id, keyframe_id

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

def get_delta(start1, end1, start2, end2):
    s1 = float(start1)
    e1 = float(end1)
    s2 = float(start2)
    e2 = float(end2)
    delta = 0
    if s2 <= s1 <= e2 or s2 <= e1 <= e2 or s1 <= s2 <= e1 or s1 <= e2 <= e1:
        delta = min(e1, e2) - max(s1, s2)
    return delta

def get_intersection_over_union(m1, m2):
    if m1.get('document_id') == m2.get('document_id'):
        if m1.get('document_element_id') == m2.get('document_element_id'):
            intersection = 0
            dx = get_delta(m1.get('span').get('start_x'), m1.get('span').get('end_x'), m2.get('span').get('start_x'), m2.get('span').get('end_x'))
            dy = get_delta(m1.get('span').get('start_y'), m1.get('span').get('end_y'), m2.get('span').get('start_y'), m2.get('span').get('end_y'))
            if (dx>0) and (dy>0):
                intersection = dx*dy
            elif dx:
                intersection = dx
            elif dy:
                intersection = dy

            union = 0
            for m in [m1, m2]:
                dx = get_delta(m.get('span').get('start_x'), m.get('span').get('end_x'), m.get('span').get('start_x'), m.get('span').get('end_x'))
                dy = get_delta(m.get('span').get('start_y'), m.get('span').get('end_y'), m.get('span').get('start_y'), m.get('span').get('end_y'))
                if (dx>0) and (dy>0):
                    union += dx*dy
                elif dx:
                    union += dx
                elif dy:
                    union += dy
            union -= intersection
    intersection_over_union = intersection/union
    return intersection_over_union

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