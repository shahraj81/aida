"""
Generator for generated-values in AIDA response.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "24 January 2020"

from aida.object import Object
from aida.utility import get_kb_document_id_from_filename
from aida.utility import get_query_id_from_filename

class Generator(Object):
    """
    Generator for generated-values in AIDA response.
    """

    def __init__(self, logger):
        super().__init__(logger)

    def generate(self, responses, method_name, entry):
        method = self.get_method(method_name)
        method(responses, entry)

    def generate_document_id(self, responses, entry):
        if entry.get('kb_document_id'):
            entry.set('document_id', entry.get('kb_document_id'))

    def generate_kb_document_id(self, responses, entry):
        kb_document_id = get_kb_document_id_from_filename(entry.get('filename'))
        entry.set('kb_document_id', kb_document_id)

    def generate_query_id(self, responses, entry):
        query_id = get_query_id_from_filename(entry.get('filename'))
        entry.set('query_id', query_id)
    
    def generate_query(self, responses, entry):
        entry.set('query', responses.get('queries').get(entry.get('query_id')))