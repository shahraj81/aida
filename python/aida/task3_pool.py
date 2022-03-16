"""
Class representing pool of task3 responses.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 March 2022"

from aida.file_handler import FileHandler
from aida.object import Object
from aida.utility import get_md5_from_string

import os

class FieldValue(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.values = {}

    def add(self, entry):
        values = self.get('values')
        value = entry.get('value')
        if value in values:
            self.record_event('DUPLICATE_VALUE', entry.get('where'))
        else:
            values[value] = entry

    def __str__(self):
        def to_string(entry):
            return '\t'.join([entry.get(f) for f in ['fieldname', 'value', 'correctness']])
        lines = []
        for entry in sorted(self.get('values').values(), key=to_string):
            lines.append(to_string(entry))
        return lines

class FieldValues(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.fieldvalues = {}

    def add(self, entry):
        fieldvalues = self.get('fieldvalues')
        fieldname = entry.get('fieldname')
        fieldvalue = fieldvalues.setdefault(fieldname, FieldValue(self.get('logger'), fieldname=fieldname))
        fieldvalue.add(entry)

    def __str__(self):
        lines = []
        for fieldvalue in self.get('fieldvalues').values():
            lines.extend(fieldvalue.__str__())
        return lines

class ClaimComponentSetMember(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.fieldvalues = FieldValues(logger)

    def add(self, entry):
        self.get('fieldvalues').add(entry)

    def get_md5(self):
        return get_md5_from_string('\n'.join(sorted(self.__str__())))

    def __str__(self):
        return self.get('fieldvalues').__str__()

class ClaimComponentSet(Object):
    """
    Class representing the outer claim components set
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.members = {}

    def add(self, entry):
        members = self.get('members')
        index = int(entry.get('id')) - 1
        member = members.setdefault(index, ClaimComponentSetMember(self.get('logger'), component_type=self.get('component_type')))
        member.add(entry)

    def __str__(self):
        members = {}
        for member in self.get('members').values():
            members[member.get('md5')] = member
        component_type = self.get('component_type')
        i = 1
        lines = []
        for md5 in sorted(members):
            member = members.get(md5)
            for member_str in member.__str__():
                line = '\t'.join([component_type, str(i), member_str])
                lines.append(line)
            i += 1
        return lines

class ClaimComponents(Object):
    """
    Class representing the outer claim components
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.components = {}
        self.load()

    def add_component_entry(self, entry):
        components = self.get('components')
        component_type = entry.get('component_type')
        component_set = components.setdefault(component_type, ClaimComponentSet(self.get('logger'), component_type=component_type))
        component_set.add(entry)

    def load(self):
        for entry in self.get('file_handler'):
            self.add_component_entry(entry)

    def __str__(self):
        def order(component_type):
            order_map = {
                'claimTopic': 1,
                'claimSubtopic': 2,
                'claimDescription': 3,
                'claimTemplate': 4,
                'claimDocument': 5,
                'claimEpistemic': 6,
                'claimSentiment': 7,
                'claimer': 8,
                'claimerAffliation': 9,
                'xVariable': 10,
                'date': 11,
                }
            if component_type not in order_map:
                print("Component type: '{}' not found in lookup".format(component_type))
                exit()
            return order_map[component_type]
        lines = []
        for component_type in sorted(self.get('components'), key=order):
            component = self.get('components').get(component_type)
            lines.extend(component.__str__())
        return lines

class OuterClaim(Object):
    """
    Class representing the outer claim
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.file_handler = FileHandler(logger, self.get('filename'))
        self.components = ClaimComponents(logger, file_handler=self.get('file_handler'))

    def to_string(self, claim_id=None):
        header = self.get('file_handler').get('header')
        lines = [header.get('line')]
        for component_line in self.get('components').__str__():
            line = '{component_line}'.format(component_line=component_line)
            if claim_id:
                line = '{claim_id}\t{line}'.format(claim_id=claim_id,
                                                   line=line)
            lines.append(line)
        return '\n'.join(lines)

    def write_output(self, output_dir, condition, query_id, claim_id):
        path = os.path.join(output_dir, condition, query_id)
        os.makedirs(path, exist_ok=True)
        output_filename = os.path.join(path, '{}-outer-claim.tab'.format(claim_id) )
        with open(output_filename, 'w') as program_output:
            for line in self.to_string(claim_id):
                program_output.write(line)

    def __str__(self):
        return self.to_string('xxxxxxxxxxx')

class ClaimEdges(Object):
    """
    Class representing the claim edges
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.file_handler = FileHandler(logger, self.get('filename'))

    def to_string(self, claim_id=None):
        def order(entry):
            header = list(entry.get('header').get('columns'))
            header.remove('ClaimID')
            header.remove('JustificationNum')
            return '\t'.join(entry.get(f) for f in header)
        header = self.get('file_handler').get('header')
        retVal = header.get('line')
        i = 1
        for entry in sorted(self.get('file_handler'), key=order):
            if claim_id:
                entry.set('ClaimID', claim_id)
            entry.set('JustificationNum', str(i))
            line = '\t'.join([entry.get(f) for f in header.get('columns')])
            retVal = '{retVal}\n{line}'.format(retVal=retVal, line=line)
            i += 1
        return retVal

    def write_output(self, output_dir, condition, query_id, claim_id):
        path = os.path.join(output_dir, condition, query_id)
        os.makedirs(path, exist_ok=True)
        output_filename = os.path.join(path, '{}-raw-kes.tab'.format(claim_id) )
        with open(output_filename, 'w') as program_output:
            for line in self.to_string(claim_id=claim_id):
                program_output.write(line)

    def __str__(self):
        return self.to_string('xxxxxxxxxxx')

class Claim(Object):
    """
    Class representing a claim
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.outer_claim = None
        self.claim_edges = None
        self.load()

    def get_uid(self):
        return get_md5_from_string(self.__str__())

    def load(self):
        logger = self.get('logger')
        path = self.get('path')
        claim_id = self.get('claim_id')
        self.set('outer_claim', OuterClaim(logger, filename=os.path.join(path, '{}-outer-claim.tab'.format(claim_id))))
        self.set('claim_edges', ClaimEdges(logger, filename=os.path.join(path, '{}-raw-kes.tab'.format(claim_id))))

    def write_output(self, output_dir, condition, query_id):
        self.get('outer_claim').write_output(output_dir, condition, query_id, self.get('uid'))
        self.get('claim_edges').write_output(output_dir, condition, query_id, self.get('uid'))

    def __eq__(self, other):
        return self.get('uid') == other.get('uid')

    def __str__(self):
        outer_claim_str = self.get('outer_claim').__str__()
        claim_edges_str = self.get('claim_edges').__str__()
        return '{}\n{}'.format(outer_claim_str, claim_edges_str)

class ClaimMapping(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])

    def __str__(self):
        return '\t'.join([self.get(f) for f in self.get('header')])

class ClaimMappings(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.mappings = []

    def add(self, condition, query_id, run_id, claim_id, runs_directory, claim_uid):
        mappings = self.get('mappings')
        mapping = ClaimMapping(self.get('logger'),
                               condition=condition,
                               query_id=query_id,
                               run_id=run_id,
                               runs_directory=runs_directory,
                               system_claim_id=claim_id,
                               pool_claim_uid=claim_uid)
        mapping.set('header', self.get('header'))
        mappings.append(mapping)

    def get_header(self):
        return ['pool_claim_uid', 'condition', 'query_id', 'run_id', 'runs_directory', 'system_claim_id']

    def write_output(self, output_dir):
        def order(mapping):
            return mapping.__str__()
        lines = ['\t'.join(self.get('header'))]
        for mapping in sorted(self.get('mappings'), key=order):
            lines.append(mapping.__str__())
        with open(os.path.join(output_dir, 'claim-mappings.tab'), 'w') as program_output:
            program_output.write('\n'.join(lines))

class Claims(Object):
    """
    Class representing the set of claims
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.claims = {}
        self.mappings = ClaimMappings(logger)

    def add(self, condition, query_id, run_id, claim_id, runs_directory, condition_and_query_dir):
        claims = self.get('claims')
        claim = Claim(self.get('logger'), condition=condition, query_id=query_id, path=condition_and_query_dir, claim_id=claim_id)
        claim_uid = claim.get('uid')
        if claim_uid not in claims:
            claims[claim_uid] = claim
        self.get('mappings').add(condition, query_id, run_id, claim_id, runs_directory, claim_uid)

    def write_output(self, output_dir):
        for claim in self.get('claims').values():
            claim.write_output(output_dir, claim.get('condition'), claim.get('query_id'))
        self.get('mappings').write_output(output_dir)

class Task3Pool(Object):
    """
    Class representing pool of task3 responses.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.claims = Claims(logger)
        self.load_responses()

    def load_responses(self):
        logger = self.get('logger')
        queries_to_pool = {}
        for entry in FileHandler(logger, self.get('queries_to_pool_file')):
            condition = entry.get('condition')
            query_id = entry.get('query_id')
            depth = int(entry.get('depth'))
            queries_to_pool['{}:{}'.format(condition, query_id)] = int(depth)
        runs_directory = self.get('input_dir')
        for entry in FileHandler(logger, self.get('runs_to_pool_file')):
            run_id = entry.get('run_id')
            arf_directory = os.path.join(runs_directory, run_id, 'ARF-output')
            for condition in os.listdir(arf_directory):
                condition_dir = os.path.join(arf_directory, condition)
                for query_id in os.listdir(condition_dir):
                    condition_and_query = '{}:{}'.format(condition, query_id)
                    if condition_and_query in queries_to_pool:
                        condition_and_query_dir = os.path.join(condition_dir, query_id)
                        depth = queries_to_pool.get(condition_and_query)
                        ranking_file = '{path}/{query_id}.ranking.tsv'.format(path=condition_and_query_dir.replace('ARF-output', 'SPARQL-VALID-output'),
                                                                              query_id=query_id)
                        ranks = {}
                        with open(ranking_file) as fh:
                            lineno = 0
                            for line in fh.readlines():
                                lineno += 1
                                elements = line.strip().split('\t')
                                claim_id, rank = elements[1], int(elements[2])
                                if rank in ranks:
                                    # critical error
                                    self.record_event('DUPLICATE_RANK', {'filename':ranking_file, 'lineno':lineno})
                                ranks[rank] = claim_id
                        for rank in sorted(ranks):
                            if rank <= depth:
                                claim_id = ranks.get(rank)
                                self.get('claims').add(condition, query_id, run_id, claim_id, runs_directory, condition_and_query_dir)

    def write_output(self, output_dir):
        self.get('claims').write_output(output_dir)