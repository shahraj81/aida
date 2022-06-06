"""
AIDA assessments class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "19 November 2020"

from aida.task3_pool import Claim, ClaimMappings
from aida.container import Container
from aida.file_handler import FileHandler
from aida.file_header import FileHeader
from aida.object import Object
import glob

assessments = {
    'task2': {
        'across_documents_coreference': {
            'query_type': 'across_documents_coreference',
            'columns': ['queryid',
                        'descriptor',
                        'id',
                        'modality',
                        'docid',
                        'mention_span',
                        'assessment',
                        'mention_type',
                        'fqec']
            }
        }
    }

class Assessments(Container):
    """
    AIDA assessments class.
    """
    
    def __init__(self, logger, task, queries_to_score, assessments_dir, claim_mappings=None, claim_relations=None):
        super().__init__(logger)
        self.task = task
        self.queries_to_score = queries_to_score
        self.assessments_dir = assessments_dir
        self.claim_mappings_filename = claim_mappings
        self.claim_relations_filename = claim_relations
        self.load()

    def get_assessment(self, task, **kwargs):
        method_name = "get_{}_assessment".format(str(self.get('task')).lower())
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        return method(**kwargs)

    def get_task3_assessment(self, **kwargs):
        claim = kwargs.get('claim')
        condition = claim.get('condition')
        query_id = claim.get('query_id')
        run_id = kwargs.get('run_id')
        run_claim_id = claim.get('claim_id')
        claim_mappings = self.get('claim_mappings').get('claim_mappings',
                                                        condition=condition,
                                                        query_id=query_id,
                                                        run_id=run_id,
                                                        run_claim_id=run_claim_id)
        if len(claim_mappings) == 1:
            pool_claim_id = claim_mappings[0].get('pool_claim_uid')
            assessment = self.get('claims').get(pool_claim_id)
            return assessment
        elif len(claim_mappings) > 1:
            message = 'CRITICAL ERROR: unexpected number of matched claim mappings'
            print(message)
            self.record_event('DEFAULT_CRITICAL_ERROR', message)

    def exists(self, key):
        num_splits = len(key.split(':'))
        if num_splits == 4:
            queryid, docid, mention_span = key.split(':', 2)
            if queryid not in self.get('store'): return False
            if ':'.join([docid,mention_span]) not in self.get(queryid): return False
        else:
            if key not in self.get('store'): return False
        return True

    def normalize(self, key, value):
        normalize = {'correct': 'CORRECT', 'wrong': 'INCORRECT', 'inexact': 'INEXACT', 'yes': 'YES', 'no': 'NO'}
        keys_to_normalize = ['assessment', 'object_linkability', 'predicate_justification_correctness']
        value = normalize[value] if key in keys_to_normalize and value in normalize else value
        return value

    def load(self):
        method_name = "load_{}_assessments".format(str(self.get('task')).lower())
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        method()

    def load_task2_assessments(self):
        next_fqec_num = 1001
        generated_fqecs = {}
        path = '{}/data/zero-hop/*.tab'.format(self.assessments_dir)
        header =  FileHeader(self.logger, "\t".join(assessments.get('task2').get('across_documents_coreference').get('columns')))
        for filename in glob.glob(path):
            for entry in FileHandler(self.logger, filename, header):
                queryid, docid, mention_span, assessment_read, fqec_read, where = map(
                    lambda key: entry.get(key),
                    ['queryid', 'docid', 'mention_span', 'assessment', 'fqec', 'where']
                    )
                entity_id = self.get('queries_to_score').get(queryid).get('entity_id')
                assessment = self.normalize('assessment', assessment_read)
                query_and_document = '{}:{}'.format(queryid, docid)
                key = '{}:{}'.format(query_and_document, mention_span)
                if self.exists(key):
                    self.logger.record_event('MULTIPLE_ASSESSMENTS', key, where)
                fqec = fqec_read
                if fqec == 'NIL' and self.normalize('assessment', assessment) == 'CORRECT':
                    if key not in generated_fqecs:
                        fqec = 'NILG{}'.format(next_fqec_num)
                        generated_fqecs[key] = fqec
                    fqec = generated_fqecs[key]
                assessment_entry = Object(self.logger)
                assessment_entry.set('assessment', assessment)
                assessment_entry.set('docid', docid)
                assessment_entry.set('queryid', queryid)
                assessment_entry.set('mention_span', mention_span)
                assessment_entry.set('fqec_read', fqec_read)
                assessment_entry.set('fqec', fqec)
                assessment_entry.set('line', entry.get('line'))
                assessment_entry.set('where', where)

                if not self.exists(queryid):
                    self.add(key=queryid, value=Container(self.get('logger')))
                self.get(queryid).add(key=':'.join(key.split(':')[1:]), value=assessment_entry)

                line = 'ENTITYID={} QUERYID={} DOCID={} MENTION={} ASSESSMENT={} FQEC_READ={} FQEC={}'.format(
                    entity_id, queryid, docid, mention_span, assessment, fqec_read, fqec)
                self.logger.record_event('GROUND_TRUTH', line, where)

    def load_task3_assessments(self):
        logger = self.get('logger')
        claims = {}
        claim_mappings = ClaimMappings(logger)
        claim_mappings.load(self.get('claim_mappings_filename'))
        self.set('claim_mappings', claim_mappings)
        self.set('claims', claims)
        for claim_mapping in claim_mappings.get('mappings'):
            condition = claim_mapping.get('condition')
            query_id = claim_mapping.get('query_id')
            pool_claim_id = claim_mapping.get('pool_claim_uid')
            if pool_claim_id not in claims:
                claim = Claim(self.get('logger'),
                              conditions=set([condition]),
                              query_id=query_id,
                              path=self.get('assessments_dir'),
                              claim_id=pool_claim_id)
                claim.set('mappings', [])
                claims[pool_claim_id] = claim
            else:
                claims.get(pool_claim_id).get('conditions').add(condition)
            claim = claims.get(pool_claim_id)
            claim.get('mappings').append(claim_mapping)
        claim_relations_filename = self.get('claim_relations_filename')
        if claim_relations_filename:
            self.set('cross_claim_relations', FileHandler(logger, claim_relations_filename))

    def load_classquery_assessments(self): 
        next_fqec_num = 1001
        generated_fqecs = {}
        query_type = 'ClassQuery'
        path = '{}/data/class/*/*.tab'.format(self.assessments_dir)
        header =  FileHeader(self.logger, "\t".join(assessments.get(query_type).get('columns')))   
        for filename in glob.glob(path):
            for entry in FileHandler(self.logger, filename, header):
                queryid, docid, mention_span, assessment_read, fqec_read, where = map(
                    lambda key: entry.get(key), 
                    ['queryid', 'docid', 'mention_span', 'assessment', 'fqec', 'where']
                    )
                assessment = self.normalize('assessment', assessment_read)
                query_and_document = '{}:{}'.format(queryid, docid)
                key = '{}:{}'.format(query_and_document, mention_span)
                if self.exists(key):
                    self.logger.record_event('MULTIPLE_ASSESSMENTS', key, where)
                fqec = fqec_read
                if fqec == 'NIL' and self.normalize('assessment', assessment) == 'CORRECT':
                    if key not in generated_fqecs:
                        fqec = 'NILG{}'.format(next_fqec_num)
                        generated_fqecs[key] = fqec
                    fqec = generated_fqecs[key]
                assessment_entry = Object(self.logger)
                assessment_entry.set('assessment', assessment)
                assessment_entry.set('docid', docid)
                assessment_entry.set('queryid', queryid)
                assessment_entry.set('mention_span', mention_span)
                assessment_entry.set('fqec_read', fqec_read)
                assessment_entry.set('fqec', fqec)
                assessment_entry.set('where', where)
                if not self.exists(key):
                    self.add(key=key, value=assessment_entry)
                line = 'QUERYID={} DOCID={} MENTION={} ASSESSMENT={} FQEC_READ={} FQEC={}'.format(
                    queryid, docid, mention_span, assessment, fqec_read, fqec)
                self.logger.record_event('GROUND_TRUTH', line, where)