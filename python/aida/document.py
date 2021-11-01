"""
The class for storing information about a document.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.object import Object
from aida.container import Container

class Document(Object):
    """
    The class for storing information about a document.
    """

    def __init__(self, logger, ID):
        """
        Initializes the document instance, setting the logger, and optionally its ID.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            ID (str):
                the string identifier of the document

        NOTE: the document contains a container to store document elements that
        comprise this document.
        """
        super().__init__(logger)
        self.document_elements = Container(logger)
        self.ID = ID
        self.logger = logger

    def get_language(self):
        language = None
        languages = {}
        for document_element in self.get('document_elements').values():
            de_language = document_element.get('language')
            if de_language is not None and de_language != 'N/A':
                languages[de_language] = 1
        if len(languages) > 1:
            self.record_event('DEFAULT_CRITICAL_ERROR',
                              "Unhandled case: multiple languages '{languages}' found for document {ID}".format(
                                  languages = ','.join(languages.keys()),
                                  ID = self.get('ID')
                                  ),
                              self.get('code_location'))
        elif len(languages) == 1:
            language = list(languages.keys())[0]
        return language

    def get_child_text_document(self):
        for document_element in self.get('document_elements'):
            if document_element.get('modality') == 'text':
                return document_element

    def add_document_element(self, document_element):
        """
        Adds the document element to this document.

        Arguments:
            document_element (aida.DocumentELement)
        """
        self.get('document_elements').add_member(document_element)
