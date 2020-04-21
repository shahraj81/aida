"""
Utility functions for AIDA
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "28 January 2020"

import hashlib

def get_kb_document_id_from_filename(filename):
    return filename.split(r'/')[-2][:-4]

def get_md5_from_string(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_query_id_from_filename(filename):
    return filename.split(r'/')[-1][:-7]

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