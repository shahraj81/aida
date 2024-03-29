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

    def get_fieldvalues(self):
        names = []
        for entry in self.get('values').values():
            names.append(entry.get('value'))
        return names

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

    def get_values(self, fieldname):
        return self.get('fieldvalues').get(fieldname).get('fieldvalues')

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

    def get_values(self, fieldname):
        return self.get('fieldvalues').get('values', fieldname)

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

    def get_fieldvalues(self, fieldname):
        names = []
        for member in self.get('members').values():
            names.extend(member.get('values', fieldname))
        return names

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

    def get_fieldvalues(self, component_name, fieldname):
        return [] if not component_name in self.get('components') else self.get('components').get(component_name).get('fieldvalues', fieldname)

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
                'claimerAffiliation': 9,
                'claimMedium': 10,
                'claimLocation': 11,
                'xVariable': 12,
                'date': 13,
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

    def get_fieldvalues(self, component_name, fieldname):
        return self.get('components').get('fieldvalues', component_name, fieldname)

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

    def write_output(self, output_dir, claim_id):
        path = os.path.join(output_dir, 'pool')
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

    def write_output(self, output_dir, claim_id):
        path = os.path.join(output_dir, 'pool')
        os.makedirs(path, exist_ok=True)
        output_filename = os.path.join(path, '{}-raw-kes.tab'.format(claim_id) )
        with open(output_filename, 'w') as program_output:
            for line in self.to_string(claim_id=claim_id):
                program_output.write(line)

    def __str__(self):
        return self.to_string('xxxxxxxxxxx')

class ReadableKEs(Object):
    """
    Class representing the readable KEs
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.file_handler = FileHandler(logger, self.get('filename'))

    def to_string(self):
        with open(self.get('filename')) as fh:
            return fh.read()

    def write_output(self, output_dir, claim_id):
        path = os.path.join(output_dir, 'pool')
        os.makedirs(path, exist_ok=True)
        output_filename = os.path.join(path, '{}-readable-kes.txt'.format(claim_id) )
        with open(output_filename, 'w') as program_output:
            program_output.write(self.to_string())

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
        self.readable_kes = None
        self.load()

    def get_uid(self):
        return get_md5_from_string(self.__str__())

    def get_human_readable(self):
        def get_polarity(epistemic):
            polarity = {
                'EpistemicTrueCertain': 'TRUE',
                'EpistemicTrueUncertain': 'TRUE',
                'EpistemicFalseCertain': 'FALSE',
                'EpistemicFalseUncertain': 'FALSE',
                'EpistemicUnknown': 'UNKNOWN'
                }
            return polarity.get(epistemic)
        outer_claim = self.get('outer_claim')
        claimer = outer_claim.get('fieldvalues', 'claimer', 'name')
        claimEpistemic = outer_claim.get('fieldvalues', 'claimEpistemic', 'polarity')
        claimLocation = outer_claim.get('fieldvalues', 'claimLocation', 'name')
        claimMedium = outer_claim.get('fieldvalues', 'claimMedium', 'name')
        claimTemplate = ','.join(outer_claim.get('fieldvalues', 'claimTemplate', 'value'))
        if claimTemplate == '':
            return
        claimTemplate = claimTemplate.replace('x', '<{xVariable}>')
        claimTemplate = claimTemplate.replace('X', '<{xVariable}>')
        xVariable = ','.join(outer_claim.get('fieldvalues', 'xVariable', 'name'))
        date = outer_claim.get('fieldvalues', 'date', 'range')
        template = 'At <{place}> place using <{medium}> medium during <{date}> date, <{claimer}> claims it is <{epistemic}> that {claimTemplate}'
        human_readable = template.format(
            place = ','.join(claimLocation),
            medium = ','.join(claimMedium),
            date = ','.join(date),
            claimer = ','.join(claimer),
            epistemic = get_polarity(','.join(claimEpistemic)),
            claimTemplate = claimTemplate.format(xVariable=xVariable)
            )
        return human_readable

    def load(self):
        logger = self.get('logger')
        path = self.get('path')
        claim_id = self.get('claim_id')
        self.set('outer_claim', OuterClaim(logger, filename=os.path.join(path, '{}-outer-claim.tab'.format(claim_id))))
        self.set('claim_edges', ClaimEdges(logger, filename=os.path.join(path, '{}-raw-kes.tab'.format(claim_id))))
        self.set('readable_kes', ReadableKEs(logger, filename=os.path.join(path, '{}-readable-kes.txt'.format(claim_id))))

    def write_output(self, output_dir):
        self.get('outer_claim').write_output(output_dir, self.get('uid'))
        self.get('claim_edges').write_output(output_dir, self.get('uid'))
        self.get('readable_kes').write_output(output_dir, self.get('uid'))

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

    def add(self, condition, query_id, run_id, rank, claim_id, runs_directory, claim_uid, claim_relations, in_previous_pools):
        def order(claim_relation):
            lookup = {
                'ontopic': 1,
                'supporting': 2,
                'refuting': 3,
                'related': 4,
                'nonrefuting': 5,
                'nonsupporting': 6
                }
            return lookup.get(claim_relation)
        mappings = self.get('mappings')
        mapping = ClaimMapping(self.get('logger'),
                               condition=condition,
                               query_id=query_id,
                               run_id=run_id,
                               runs_directory=runs_directory,
                               rank=str(rank),
                               run_claim_id=claim_id,
                               pool_claim_uid=claim_uid,
                               claim_relations=','.join(sorted(claim_relations, key=order)),
                               in_previous_pools=str(in_previous_pools))
        mapping.set('header', self.get('header'))
        mappings.append(mapping)

    def get_header(self):
        return ['pool_claim_uid', 'condition', 'query_id', 'claim_relations', 'rank', 'run_claim_id', 'run_id', 'runs_directory', 'in_previous_pools']

    def get_claim_mappings(self, **kwargs):
        mappings = []
        for mapping in self.get('mappings'):
            matched = True
            for k,v in kwargs.items():
                if not mapping.get(k) == v:
                    matched = False
            if matched:
                mappings.append(mapping)
        return mappings

    def load(self, filename):
        self.filename = filename
        for entry in FileHandler(self.get('logger'), filename):
            self.add(entry.get('condition'),
                     entry.get('query_id'),
                     entry.get('run_id'),
                     entry.get('rank'),
                     entry.get('run_claim_id'),
                     entry.get('runs_directory'),
                     entry.get('pool_claim_uid'),
                     [entry.get('claim_relations')],
                     entry.get('in_previous_pools'))

    def write_output(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
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

    def add(self, condition, query_id, run_id, rank, claim_id, runs_directory, condition_and_query_dir, claim_relations):
        claims = self.get('claims')
        claim = Claim(self.get('logger'), condition=condition, query_id=query_id, path=condition_and_query_dir, claim_id=claim_id)
        claim_uid = claim.get('uid')
        if claim_uid not in claims:
            claims[claim_uid] = claim
        in_previous_pools = True if self.get('previous_pools').contains(claim_uid) else False
        self.get('mappings').add(condition, query_id, run_id, rank, claim_id, runs_directory, claim_uid, claim_relations, in_previous_pools)

    def write_output(self, output_dir):
        header = '{condition}\t{query}\t{run_id}\t{rank}\t{run_claim_id}\t{claim_relations}'
        for claim_uid, claim in self.get('claims').items():
            if not self.get('previous_pools').contains(claim_uid):
                claim.write_output(output_dir)
        self.get('mappings').write_output(output_dir)
        with open(os.path.join(output_dir, 'human-readable-format.tab'), 'w') as program_output:
            lines = []
            for claim_uid in sorted(self.get('claims')):
                claim_lines = ['--------------']
                claim_lines.append('claim: {}'.format(claim_uid))
                claim_lines.append('\n')
                claim_lines.append(header.replace('{','').replace('}',''))
                claim_mappings = self.get('mappings').get('claim_mappings', pool_claim_uid=claim_uid)
                for claim_mapping in claim_mappings:
                    condition = claim_mapping.get('condition')
                    query_id = claim_mapping.get('query_id')
                    rank = claim_mapping.get('rank')
                    run_id = claim_mapping.get('run_id')
                    run_claim_id = claim_mapping.get('run_claim_id')
                    claim_relations = claim_mapping.get('claim_relations')
                    line = str(header)
                    line = line.format(condition=condition,
                                       query=query_id,
                                       run_id=run_id,
                                       rank=rank,
                                       run_claim_id=run_claim_id,
                                       claim_relations=claim_relations)
                    claim_lines.append(line)
                human_readable = self.get('claims').get(claim_uid).get('human_readable')
                readable_kes = self.get('claims').get(claim_uid).get('readable_kes').to_string()
                if human_readable:
                    claim_lines.append('\n')
                    claim_lines.append(human_readable)
                    claim_lines.append('\n')
                    claim_lines.append(readable_kes)
                    claim_lines.append('\n')
                    lines.extend(claim_lines)
            program_output.write('\n'.join(lines))

class PreviousPools(Object):
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.claims = set()
        self.load()

    def contains(self, claim_uid):
        if claim_uid in self.get('claims'):
            return True
        return False

    def load(self):
        if self.get('previous_pools'):
            for path in self.get('previous_pools').split(','):
                for filename in os.listdir(os.path.join(path, 'pool')):
                    if filename.endswith('-outer-claim.tab'):
                        claim_uid = filename.split('-')[0]
                        self.get('claims').add(claim_uid)

class Task3Pool(Object):
    """
    Class representing pool of task3 responses.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.claims = Claims(logger, previous_pools=PreviousPools(logger, previous_pools=self.get('previous_pools')))
        self.load_responses()

    def load_responses(self):
        def get_expanded_claim_relations(provided=None):
            claimrelations = set(['ontopic'])
            if provided is not None:
                claimrelations.add(provided)
                lookup = {
                    'refuting':         ['nonsupporting'],
                    'supporting':       ['nonrefuting'],
                    'nonrefuting':      ['supporting'],
                    'nonsupporting':    ['refuting'],
                    'related':          ['nonsupporting', 'nonrefuting']
                    }
                claimrelations.update(lookup.get(provided))
            return claimrelations
        logger = self.get('logger')
        queries_to_pool = {}
        for entry in FileHandler(logger, self.get('queries_to_pool_file')):
            condition = entry.get('condition')
            query_id = entry.get('query_id')
            depth = entry.get('depth')
            queries_to_pool['{}:{}'.format(condition, query_id)] = depth
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
                        depth_left = {}
                        for claim_relation_and_depth in queries_to_pool.get(condition_and_query).split(','):
                            c, d = claim_relation_and_depth.split(':')
                            depth_left[c] = int(d)
                        ranking_file = '{path}/{query_id}.ranking.tsv'.format(path=condition_and_query_dir.replace('ARF-output', 'SPARQL-VALID-output'),
                                                                              query_id=query_id)
                        ranks = {}
                        with open(ranking_file) as fh:
                            lineno = 0
                            for line in fh.readlines():
                                lineno += 1
                                elements = line.strip().split('\t')
                                claim_id, rank = elements[1], int(elements[2])
                                provided = elements[3] if condition == 'Condition5' else None
                                claim_relations = get_expanded_claim_relations(provided=provided)
                                if rank in ranks:
                                    # critical error
                                    self.record_event('DUPLICATE_RANK', {'filename':ranking_file, 'lineno':lineno})
                                ranks[rank] = {
                                    'claim_id': claim_id,
                                    'claim_relations': claim_relations
                                    }
                        for rank in sorted(ranks):
                            claim_id = ranks.get(rank).get('claim_id')
                            claim_relations = ranks.get(rank).get('claim_relations')
                            include_in_pool = False
                            for claim_relation in claim_relations:
                                if depth_left.get(claim_relation) > 0:
                                    include_in_pool = True
                            if include_in_pool:
                                self.get('claims').add(condition, query_id, run_id, rank, claim_id, runs_directory, condition_and_query_dir, claim_relations)
                                for claim_relation in claim_relations:
                                    if depth_left.get(claim_relation) > 0:
                                        depth_left[claim_relation] -= 1

    def write_output(self, output_dir):
        self.get('claims').write_output(output_dir)