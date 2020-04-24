"""
The class for storing mappings between Document and DocumentElement.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 January 2020"

from collections import defaultdict
from aida.object import Object
from aida.file_handler import FileHandler
from aida.document import Document
from aida.documents import Documents
from aida.document_elements import DocumentElements
from aida.document_element import DocumentElement

nested_dict = lambda: defaultdict(nested_dict)

class DocumentMappings(Object):
    """
    The class for storing mappings between Document and DocumentElement.
    """

    def __init__(self, logger, filename, encodings, core_documents=None):
        """
        Initialize the mapping between Document and DocumentElement.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            filename (str):
                the parent-children file containing mapping between documents and document-elements.
            encodings (aida.Encodings)
            core_documents (aida.CoreDocuments)
        """
        self.logger = logger
        self.filename = filename
        self.fileheader = None
        self.core_documents = core_documents
        self.documents = Documents(logger)
        self.document_elements = DocumentElements(logger)
        self.encodings = encodings
        self.load_data()
    
    def load_data(self):
        """
        Loads the data from the parent-children file into the DocumentMappings object.
        """
        mappings = nested_dict()
        fh = FileHandler(self.logger, self.filename)
        self.fileheader = fh.get('header')
        for entry in fh:
            doceid = entry.get('doceid')
            docid = entry.get('docid')
            detype = entry.get('detype')
            mappings[doceid]['docids'][docid] = 1
            mappings[doceid]['detype'] = detype
        for doceid in mappings:
            # TODO: next if doceid is n/a?
            detype = mappings[doceid]['detype']
            modality = self.encodings.get(detype)
            for docid in mappings[doceid]['docids']:
                is_core = 0
                if self.core_documents is not None and self.core_documents.exists(docid):
                    is_core = 1
                document = self.get('documents').get(docid, default=Document(self.logger, docid))
                document.set('is_core', is_core)
                document_element = self.get('document_elements').get(doceid, default=DocumentElement(self.logger, doceid))
                document_element.add_document(document)
                document_element.set('type', detype)
                document_element.set('modality', modality)
                document.add_document_element(document_element)

    def __str__(self, *args, **kwargs):
        """
        Returns the string representation of the mappings.
        """
        # p_str: printable string to be returned
        # set p_str to the header
        p_str = str(self.fileheader)
        for doceid in self.document_elements:
            document_element = self.document_elements.get(doceid)
            detype = document_element.get('type')
            for docid in document_element.get('documents'):
                # l_str: printable line
                l_str = '\t'.join([doceid, detype, docid]) 
                # append the line to the string to be returned
                p_str = '\n'.join([p_str, l_str])
        return p_str