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
    'argument_assertion_confidence': {
        'name': 'argument_assertion_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020],
        },
    'cluster_id': {
        'name': 'cluster_id',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'cluster_membership_confidence': {
        'name': 'cluster_membership_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020],
        },
    'cluster_type': {
        'name': 'cluster_type',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'document_id': {
        'name': 'document_id',
        'tasks': ['task1'],
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'validate': 'validate_document_id',
        'generate': 'generate_document_id',
        'years': [2020],
        },
    'end_before_day': {
        'name': 'end_before_day',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'end_before_month': {
        'name': 'end_before_month',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'end_before_year': {
        'name': 'end_before_year',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'end_after_day': {
        'name': 'end_after_day',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'end_after_month': {
        'name': 'end_after_month',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'end_after_year': {
        'name': 'end_after_year',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'justification_confidence': {
        'name': 'justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020],
        },
    'kb_document_id': {
        'name': 'kb_document_id',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'generate': 'generate_kb_document_id',
        'validate': 'validate_kb_document_id',
        'years': [2020],
        },
    'mention_span': {
        'name': 'mention_span',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020],
        },
    'metatype': {
        'name': 'metatype',
        'years': [2020],
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_metatype',
        },
    'object_cluster_id': {
        'name': 'object_cluster_id',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'object_informative_justification': {
        'name' : 'object_informative_justification',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020],
        },
    'object_justification_confidence': {
        'name' : 'object_justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020],
        },
    'predicate': {
        'name': 'predicate',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_predicate',
        'years': [2020],
        },
    'predicate_justification': {
        'name': 'predicate_justification',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020],
        },
    'predicate_justification_confidence': {
        'name': 'predicate_justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020],
        },
    'start_before_day': {
        'name': 'start_before_day',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'start_before_month': {
        'name': 'start_before_month',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'start_before_year': {
        'name': 'start_before_year',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'start_after_day': {
        'name': 'start_after_day',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'start_after_month': {
        'name': 'start_after_month',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'start_after_year': {
        'name': 'start_after_year',
        'schemas': ['AIDA_PHASE2_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'subject_cluster_id': {
        'name': 'subject_cluster_id',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'years': [2020],
        },
    'type_confidence': {
        'name': 'type_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020],
        },
    }

schemas = {
    'AIDA_PHASE2_TASK1_AM_RESPONSE': {
        'name': 'AIDA_PHASE2_TASK1_AM_RESPONSE',
        'year': 2020,
        'task': 'task1',
        'header': ['?metatype', '?subject', '?predicate', '?object', '?object_inf_j_span', '?ej_span', '?edge_cj_cv', '?edge_cv', '?obj_inf_j_cv'],
        'columns': [
            'metatype',
            'subject_cluster_id',
            'predicate',
            'object_cluster_id',
            'object_informative_justification',
            'predicate_justification',
            'predicate_justification_confidence',
            'argument_assertion_confidence',
            'object_justification_confidence'
            ]
        },
    'AIDA_PHASE2_TASK1_CM_RESPONSE': {
        'name': 'AIDA_PHASE2_TASK1_CM_RESPONSE',
        'year': 2020,
        'task': 'task1',
        'header': ['?cluster', '?metatype', '?type', '?mention_span', '?t_cv', '?cm_cv', '?j_cv'],
        'columns': [
            'cluster_id',
            'metatype',
            'cluster_type',
            'mention_span',
            'type_confidence',
            'cluster_membership_confidence',
            'justification_confidence'
            ]
        },
    'AIDA_PHASE2_TASK1_TM_RESPONSE': {
        'name': 'AIDA_PHASE2_TASK1_TM_RESPONSE',
        'year': 2020,
        'task': 'task1',
        'header': ['?cluster', '?sa_month', '?sa_day', '?sa_year', '?sb_month', '?sb_day', '?sb_year', '?ea_month', '?ea_day', '?ea_year', '?eb_month', '?eb_day', '?eb_year'],
        'columns': [
            'cluster_id',
            'start_after_month',
            'start_after_day',
            'start_after_year',
            'start_before_month',
            'start_before_day',
            'start_before_year',
            'end_after_month',
            'end_after_day',
            'end_after_year',
            'end_before_month',
            'end_before_day',
            'end_before_year'
            ]
        }
    }

def identify_file_schema(fh):
    for schema in schemas.values():
        found = 1
        if len(schema['header']) == len(fh.get('header').get('columns')):
            for i in range(len(schema['header'])):
                if schema['header'][i] != fh.get('header').get('columns')[i]:
                    found = 0
                    break
            if found: return schema
    return None

class ResponseSet(Container):
    """
    Set of responses for AIDA.
    """

    def __init__(self, logger, document_mappings, document_boundaries, path, runid):
        super().__init__(logger)
        self.document_mappings = document_mappings
        self.document_boundaries = document_boundaries
        self.validator = Validator(logger)
        self.generator = Generator(logger)
        self.normalizer = Normalizer(logger)
        self.responses = Container(logger)
        self.runid = runid
        self.path = path
        self.load_responses()

    def load_responses(self):
        logger = self.get('logger')
        for subdir in ['{}/{}'.format(self.get('path'), d) for d in os.listdir(self.get('path'))]:
            for filename in os.listdir(subdir):
                filename_including_path = '{}/{}'.format(subdir, filename)
                fh = FileHandler(logger, filename_including_path)
                schema = identify_file_schema(fh)
                if schema is None:
                    logger.record_event('UNKNOWN_RESPONSE_FILE_TYPE', filename_including_path, self.get('code_location'))
                self.load_file(fh, schema)

    def load_file(self, fh, schema):
        logger = self.get('logger')
        for entry in fh:
            filename = entry.get('filename')
            lineno = entry.get('lineno')
            entry.set('runid', self.get('runid'))
            entry.set('schema', schema)
            for i in range(len(schema.get('columns'))):
                entry.set(schema.get('columns')[i], entry.get(entry.get('header').get('columns')[i]))
            valid = True
            for attribute_name in attributes:
                attribute = attributes[attribute_name]
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
            if not self.exists(filename):
                self.add(key=filename, value=Container(logger))
            self.get(filename).add(key=str(lineno), value=entry)

    def attribute_required(self, attribute, schema):
        year = schema.get('year')
        task = schema.get('task')
        if year not in attribute.get('years'): return False
        if task not in attribute.get('tasks'): return False
        if schema.get('name') not in attribute.get('schemas'): return False
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

    def write_valid_responses(self, output_dir):
        os.mkdir(output_dir)
        for input_filename in self:
            output_filename = input_filename.replace(self.get('path'), output_dir)
            dirname = os.path.dirname(output_filename)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            output_fh = open(output_filename, 'w')
            header_printed = False
            for linenum in sorted(self.get(input_filename), key=int):
                entry = self.get(input_filename).get(str(linenum))
                if not header_printed:
                    output_fh.write('{}\n'.format(entry.get('header').get('line')))
                    header_printed = True
                output_fh.write(entry.__str__())
            output_fh.close()