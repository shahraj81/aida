"""
Utility functions for AIDA
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "28 January 2020"

import hashlib

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