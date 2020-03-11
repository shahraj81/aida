"""
Set of responses for AIDA.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "22 January 2020"

from aida.container import Container
from aida.file_handler import FileHandler
from aida.generator import Generator
from aida.validator import Validator
from aida.normalizer import Normalizer
from aida.utility import get_md5_from_string
from aida.utility import get_kb_document_id_from_filename
from aida.utility import get_query_id_from_filename

import os
  
attributes = {
    'cluster_membership_confidence': {
        'name': 'cluster_membership_confidence',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_confidence'      
        },
    'document_id': {
        'name': 'document_id',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_document_id',
        'dependencies': ['kb_document_id']
        },
    'justification_confidence': {
        'name': 'justification_confidence',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_confidence'      
        },
    'kb_document_id': {
        'name': 'kb_document_id',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'generate': 'generate_kb_document_id',
        'validate': 'validate_kb_document_id',
        },
    'entity_type_in_response': {
        'name': 'entity_type_in_response',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_entity_type_in_response',
        'normalize': 'normalize_entity_type',
        'dependencies': ['query']
        },
    'query': {
        'name': 'query',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'generate': 'generate_query',
        'dependencies': ['query_id']
        },
    'entity_type_in_query': {
        'name': 'entity_type_in_query',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_entity_type_in_query',
        'normalize': 'normalize_entity_type',
        'dependencies': ['query']
        },
    'query_id': {
        'name': 'query_id',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'generate': 'generate_query_id',
        'required': 1,
        },
    'type_confidence': {
        'name': 'type_confidence',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_confidence'      
        },
    'value_provenance_triple': {
        'name': 'value_provenance_triple',
        'years': [2019],
        'tasks': ['task1'],
        'query_types': ['ClassQuery'],
        'validate': 'validate_value_provenance_triple'        
        }
    }

schemas = {
    '2019_TA1_CL_SUBMISSION': {
        'year': 2019,
        'task': 'task1',
        'query_type': 'ClassQuery',
        'file_type': 'submission',
        'header': ['?docid', '?query_type', '?cluster', '?type', '?infj_span', '?t_cv', '?cm_cv', '?j_cv'],
        'columns': [
            'document_id',
            'entity_type_in_query',
            'cluster_id',
            'entity_type_in_response',
            'value_provenance_triple',
            'type_confidence',
            'cluster_membership_confidence',
            'justification_confidence'
            ]
        }
    }

def identify_file_schema(query_id):
    schema_name = None
    if 'AIDA_TA1_CL_2019' in query_id: schema_name = '2019_TA1_CL_SUBMISSION'
    return schema_name

class ResponseSet(Container):
    """
    Set of responses for AIDA.
    """

    def __init__(self, logger, queries, document_mappings, text_boundaries, image_boundaries, keyframe_boundaries, queries_to_score, path, runid):
        super().__init__(logger)
        self.queries = queries
        self.document_mappings = document_mappings
        self.text_boundaries = text_boundaries
        self.image_boundaries = image_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.queries_to_score = queries_to_score
        self.validator = Validator(logger)
        self.generator = Generator(logger)
        self.normalizer = Normalizer(logger)
        self.categorized_responses = Container(logger)
        self.runid = runid
        self.path = path
        self.run_dir = '{}/{}/sparql-valid-output'.format(path, runid)
        self.cas_dir = '{}/{}/valid-ca-output'.format(path, runid)
        for subdir_name in os.listdir(self.run_dir):
            subdir = '{}/{}'.format(self.run_dir, subdir_name)
            if not os.path.isdir(subdir): continue
            for filename in os.listdir(subdir):
                sparql_output_filename = '{}/{}/{}'.format(self.run_dir, subdir_name, filename)
                ca_output_filename = '{}/{}/{}'.format(self.cas_dir, subdir_name, filename)
                query_id = filename.rstrip()
                query_id = query_id[:-7]
                # skip the query if the query is not in the queries file,
                #   or if it is not to be used for scoring
                if query_id not in queries or query_id not in queries_to_score:
                    logger.record_event('SKIPPING_FILE', sparql_output_filename, self.get('code_location'))
                    continue
                schema_name = identify_file_schema(query_id)
                if schema_name not in schemas:
                    logger.record_event('UNKNOWN_RESPONSE_FILE_TYPE', sparql_output_filename, self.get('code_location'))
                schema = schemas[schema_name]
                self.load_sparql_output_file(schema, sparql_output_filename)
                self.load_ca_output_file(ca_output_filename)

    def load_sparql_output_file(self, schema, filename):
        logger = self.logger
        fh = FileHandler(logger, filename)
        expected_columns = schema.get('header')
        provided_columns = fh.get('header').get('columns')
        if len(expected_columns) != len(provided_columns):
            logger.record_event('UNEXPECTED_NUM_OF_COLUMNS', len(expected_columns),len(provided_columns),
                                {'filename': filename, 'lineno': 1})
        for i in range(len(expected_columns)):
            if expected_columns[i] != provided_columns[i]:
                logger.record_event('UNEXPECTED_COLUMN_HEADER', i+1, expected_columns[i], provided_columns[i],
                                    {'filename': filename, 'lineno': 1})
        for entry in fh:
            filename_and_lineno = '{}:{}'.format(entry.get('filename'), entry.get('lineno'))
            entry.set('runid', self.get('runid'))
            entry.set('schema', schema)
            for i in range(len(expected_columns)):
                entry.set(schema.get('columns')[i], entry.get(expected_columns[i]))
            valid = True
            for attribute_name in attributes:
                attribute = attributes[attribute_name]
                if attribute is None:
                    self.record_event('NO_SPECS', attribute_name, self.get_code_location())
                # skip if the attribute is not required for the given schema
                if not self.attribute_required(attribute, schema): continue
                # generate value for the attribute, if needed
                self.generate_value(attribute, entry)
                # normalize value
                normalizer_name = attribute.get('normalize')
                if normalizer_name:
                    self.get('normalizer').normalize(self, normalizer_name, entry, attribute)
                # validate value
                validator_name = attribute.get('validate')
                if validator_name:
                    valid_attribute = self.get('validator').validate(self, validator_name, schema, entry, attribute)
                    if not valid_attribute: valid = False
            entry.set('valid', valid)
            self.add(key=filename_and_lineno, value=entry)
            # categorize responses in order to make it easy for attaching confidence aggregation values later
            code = self.queries.get('TASK_AND_TYPE_CODE')
            if code == 'TA1_CL':
                query_id = entry.get('query_id')
                kb_document_id = entry.get('kb_document_id')
                cluster_id = entry.get('cluster_id')
                key = '::'.join([query_id, kb_document_id, cluster_id])
                self.get('categorized_responses').get(key, default=Container(self.logger)).add(key=key, value=entry)
            elif code == 'TA1_GR':
                uuid = get_md5_from_string(entry.get('line'))
                if self.get('categorized_responses').exists(uuid):
                    self.record_event('DUPLICATE_VALUE', entry.get('line'), entry.get('where'))
                self.get('categorized_responses').add(key=uuid, value=entry)
            
    
    def load_ca_output_file(self, filename):
        code = self.queries.get('TASK_AND_TYPE_CODE')
        method_name = 'load_ca_output_file_{}'.format(code)
        method = self.get_method(method_name)
        if method is None:
            self.logger('UNDEFINED_METHOD', method_name, self.get_code_location())
        method(filename)
    
    def load_ca_output_file_TA1_CL(self, filename):
        kb_document_id = get_kb_document_id_from_filename(filename)
        query_id = get_query_id_from_filename(filename)
        for entry in FileHandler(self.logger, filename):
            cluster_id = entry.get('?cluster')
            rank = entry.get('?rank')
            key = '::'.join([query_id, kb_document_id, cluster_id])
            for response in self.get('categorized_responses').get(key).values():
                response.set('cluster_rank', rank)
    
    def attribute_required(self, attribute, schema):
        year = schema.get('year')
        task = schema.get('task')
        query_type = schema.get('query_type')
        if year not in attribute.get('years'): return False
        if task not in attribute.get('tasks'): return False
        if query_type not in attribute.get('query_types'): return False
        return True

    def generate_value(self, attribute, entry):
        dependencies = attribute.get('dependencies')
        if dependencies:
            for dependency_name in dependencies:
                dependency = attributes[dependency_name]
                self.generate_value(dependency, entry)
        if entry.get(attribute.get('name')):
            return
        generator_name = attribute.get('generate')
        if generator_name:
            self.get('generator').generate(self, generator_name, entry)