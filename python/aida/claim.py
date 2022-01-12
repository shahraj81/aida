"""
AIDA claim class.

"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 January 2022"

from aida.object import Object

class Claim(Object):
    def __init__(self, logger, claim_id):
        super().__init__(logger)
        self.claim_id = claim_id
        self.outer_claim = None
        self.claim_components = []
        self.claim_edge_assertions = []
        self.claim_edge_subject_times = []
        self.claim_time = None

    def add(self, *args, **kwargs):
        key = args[0]
        if key is None:
            self.get('logger').record_event('KEY_IS_NONE', self.get('code_location'))
        method_name = "add_{}".format(key)
        method = self.get_method(method_name)
        if method is not None:
            args = args[1:]
            method(*args, **kwargs)
            return self
        else:
            self.record_event('METHOD_NOT_FOUND', method_name)

    def add_claim_component(self, entry):
        self.get('claim_components').append(entry)

    def add_claim_edge_assertion(self, entry):
        self.get('claim_edge_assertions').append(entry)

    def add_claim_edge_subject_time(self, entry):
        self.get('claim_edge_subject_times').append(entry)

    def add_claim_time(self, entry):
        if self.get('claim_time') is None:
            self.set('claim_time', entry)
        else:
            self.record_event('MULTIPLE_CLAIM_TIME', entry.get('claim_id'), entry.get('where'))

    def update(self, entry):
        if entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_OC_RESPONSE':
            self.set('outer_claim', entry)
        elif entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_CC_RESPONSE':
            self.add('claim_component', entry)
        elif entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_CT_RESPONSE':
            self.add('claim_time', entry)
        elif entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_GR_RESPONSE':
            self.add('claim_edge_assertion', entry)
        elif entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_TM_RESPONSE':
            self.add('claim_edge_subject_time', entry)
        else:
            self.record_event('UNEXPECTED_ENTRY', entry.get('where'))