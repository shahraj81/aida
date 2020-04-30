"""
Query set for AIDA.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 January 2020"

from aida.container import Container
from aida.class_query import ClassQuery
from aida.graph_query import GraphQuery
import xml.etree.ElementTree as ET
import os

class QuerySet(Container):
    """
    Query set for AIDA.
    """

    def __init__(self, logger, filename):
        super().__init__(logger)
        self.filename = filename
        self.set_query_type()
        self.load_file()
        
    def set_query_type(self):
        query_types = {
            'task1_class_queries.xml': 'ClassQuery',
            'task1_graph_queries.xml': 'ClassQuery',
            'task2_zerohop_queries.xml': 'ZerohopQuery',
            'task2_graph_queries.xml': 'GraphQuery',            
            }
        self.query_type = query_types[os.path.basename(self.filename)]
    
    def load_file(self):
        tree = ET.parse(self.filename)
        root = tree.getroot()
        if self.query_type == 'ClassQuery':
            for query_xml_object in root.findall('class_query'):
                query_id = query_xml_object.get('id').strip()
                entity_type = query_xml_object.find('enttype').text.strip()
                sparql = query_xml_object.find('sparql').text
                query = ClassQuery(self.logger, query_id, entity_type, sparql)
                self.add(key=query_id, value=query)
        elif self.query_type == 'GraphQuery':
            for query_xml_object in root.findall(self.query_type):
                query_id = query_xml_object.get('id').strip()
                predicate = query_xml_object.find('predicate').text.strip()
                object_id = query_xml_object.find('object').text.strip()
                sparql = query_xml_object.find('sparql').text
                query = GraphQuery(self.logger, query_id, predicate, object_id, sparql)
                self.add(key=query_id, value=query)
    
    def get_TASK_AND_TYPE_CODE(self):
        code = None
        for query in self.values():
            query_code = query.get('TASK_AND_TYPE_CODE')
            if query_code is None:
                self.logger.record_event('MISSING_TASK_AND_TYPE_CODE', query.get('id'))
            code = query_code if code is None else code
            if query_code != code:
                self.logger.record_event('MULTIPLE_TASK_AND_TYPE_CODE', code, query_code)
        return code