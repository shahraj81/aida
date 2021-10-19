"""
Script for generating AIF from LDCs annotations
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2019.0.1"
__date__    = "7 February 2020"

from aida.object import Object
from aida.logger import Logger
from aida.excel_workbook import ExcelWorkbook
from calendar import monthrange
from rdflib import Graph
from re import findall, compile
import argparse
import datetime
import hashlib
import os
import re
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

class AIFObject(Object):
    def __init__(self, logger):
        super().__init__(logger)

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

    def get(self, *args, **kwargs):
        """
        Gets the value for the key using the given args.

        If method get_{key} is defined for this object, call that method with
        args as its arguments, and return what it returns, otherwise if there
        is an attribute whose name matches the value stored in key then return
        it. None is returned otherwise.
        """
        key = args[0]
        if key is None:
            self.get('logger').record_event('KEY_IS_NONE', self.get('code_location'))
        method = self.get_method("get_{}".format(key))
        if method is not None:
            args = args[1:]
            return method(*args, **kwargs)
        else:
            value = getattr(self, key, None)
            if value is None and getattr(self, 'entry', None):
                    value = self.entry.get(key)
            return value

    def get_classname(self):
        return self.__class__.__name__

    def get_coreAIF(self, predicates):
        AIF_triples = []
        AIF_subject = self.get('IRI')
        for predicate, AIF_object in predicates.items():
            if AIF_object:
                if isinstance(AIF_object, list):
                    for o in AIF_object:
                        if not isinstance(o, str):
                            o = o.get('IRI')
                        AIF_triple = '{} {} {} .'.format(AIF_subject, predicate, o)
                        AIF_triples.append(AIF_triple)
                else:
                    if not isinstance(AIF_object, str):
                        AIF_object = AIF_object.get('IRI')
                    AIF_triple = '{} {} {} .'.format(AIF_subject, predicate, AIF_object)
                    AIF_triples.append(AIF_triple)
        return AIF_triples

class AIFStatement(AIFObject):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger)
        for k,v in kwargs.items():
            self.set(key=k, value=v)

    def __str__(self):
        return self.get('id')

class AIFScalar(AIFStatement):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger, *args, **kwargs)

    def get_IRI(self):
        return '"{}"'.format(self.__str__())

class ClaimComponent(AIFStatement):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger, *args, **kwargs)
        componentTypes_ = self.get('componentTypes').split(',')
        componentTypes = []
        for componentType in componentTypes_:
            componentTypes.append(AIFScalar(logger, id=componentType))
        self.set('componentTypes', componentTypes)

    def get_AIF(self):
        componentProvenance = self.get('componentProvenance')
        if componentProvenance is not None:
            componentProvenance = None if componentProvenance == 'EMPTY_NA' else componentProvenance
            componentProvenance = None if componentProvenance is None else '"{}"'.format(componentProvenance)
        predicates = {
            'a': 'aida:ClaimComponent',
            'aida:componentName': '"{}"'.format(self.get('componentName')),
            'aida:componentIdentity': '"{}"'.format(self.get('componentIdentity')),
            'aida:componentType': self.get('componentTypes'),
            'aida:componentProvenance': componentProvenance,
            }
        return self.get('coreAIF', predicates)

    def get_id(self):
        classname = self.get('classname')
        componentName = self.get('componentName')
        componentIdentity = self.get('componentIdentity')
        componentTypes = ','.join([t.__str__() for t in self.get('componentTypes')])
        componentProvenance = self.get('componentProvenance')
        return '{}-{}-{}-{}-{}'.format(
            classname,
            componentName,
            componentIdentity,
            componentTypes,
            componentProvenance)

    def get_IRI(self):
        return '_:cc{}'.format(
            hashlib.md5(
                self.__str__().encode('utf-8')).hexdigest())

class ClusterMembershipStatement(AIFStatement):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger, *args, **kwargs)

    def get_AIF(self):
        predicates = {
            'a': 'aida:ClusterMembership',
            'aida:cluster': self.get('cluster'),
            'aida:clusterMember': self.get('clusterMember'),
            'aida:confidence': self.get('confidence'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('confidence').get('AIF'))
        return AIF_triples

    def get_IRI(self):
        s = '{}-{}-{}'.format(
            'clusterMembership',
            self.get('cluster').get('IRI'),
            self.get('clusterMember').get('IRI')).encode('utf-8')
        return '_:bcm-{}'.format(hashlib.md5(s).hexdigest())

class TypeStatement(AIFStatement):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger, *args, **kwargs)

    def get_AIF(self):
        predicates = {
            'a': 'rdf:Statement',
            'rdf:object': '"{}"'.format(self.get('type')),
            'rdf:predicate': 'rdf:type',
            'rdf:subject': self.get('subject'),
            'aida:confidence': self.get('confidence'),
            'aida:justifiedBy': self.get('justifiedBy'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('confidence').get('AIF'))
        AIF_triples.extend(self.get('justifiedBy').get('AIF'))
        return AIF_triples

    def get_IRI(self):
        s = '{}-{}-{}'.format(
            'typeStatement',
            self.get('subject').get('IRI'),
            self.get('type')).encode('utf-8')
        return '_:bcm-{}'.format(hashlib.md5(s).hexdigest())

class Annotations(AIFObject):
    def __init__(self, logger, filename, include_worksheets=None):
        super().__init__(logger)
        self.filename = filename
        workbook = ExcelWorkbook(self.get('logger'), self.get('filename'))
        self.worksheets = workbook.get('worksheets')
        if include_worksheets is not None:
            worksheets = {}
            for worksheet in include_worksheets:
                mapped_name = include_worksheets.get(worksheet)
                if worksheet not in workbook.get('worksheets'):
                    self.record_event('WORKSHEET_NOT_FOUND', worksheet, where={'filename': filename})
                worksheets[mapped_name] = workbook.get('worksheets').get(worksheet)
            self.worksheets = worksheets

class ERECluster(AIFObject):
    def __init__(self, logger, cluster_id):
        super().__init__(logger)
        self.system = System(logger)
        self.id = cluster_id
        self.mentions = []
        self.mentionframes = []

    def add_link(self, link):
        if self.get('link') is not None:
            if link.get('qnode_kb_id_identity') != self.get('link').get('qnode_kb_id_identity'):
                self.record_event('MULTIPLE_REFKB_LINKS_ON_CLUSTER', self.get('id'))
        self.set('link', link)

    def add_mention(self, mention):
        self.get('mentions').append(mention)

    def add_frame(self, mentionframe):
        self.get('mentionframes').append(mentionframe)

    def get_mention(self, mention_id):
        for mention in self.get('mentions'):
            if mention.get('id') == mention_id:
                return mention
        return

    def get_prototype(self):
        return ClusterPrototype(self.get('logger'), self)

    def get_IRI(self):
        return 'ldc:cluster-{}'.format(self.get('id'))

    def get_AIF(self):
        logger = self.get('logger')
        predicates = {
            'a': 'aida:SameAsCluster',
            'aida:prototype': self.get('prototype'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        for mention in self.get('mentions'):
            AIF_triples.extend(mention.get('AIF'))
            AIF_triples.extend(
                ClusterMembershipStatement(
                    logger,
                    cluster=self,
                    clusterMember=mention,
                    confidence=Confidence(logger),
                    system=System(logger)).get('AIF'))
        mentionframes = self.get('mentionframes')
        if mentionframes and len(mentionframes):
            for frame in mentionframes:
                for rolename in frame:
                    for argument in frame.get(rolename):
                        AIF_triples.extend(argument.get('AIF'))
        AIF_triples.extend(self.get('prototype').get('AIF'))
        return AIF_triples

class EventCluster(ERECluster):
    def __init__(self, logger, cluster_id):
        super().__init__(logger, cluster_id)

class RelationCluster(ERECluster):
    def __init__(self, logger, cluster_id):
        super().__init__(logger, cluster_id)

class EntityCluster(ERECluster):
    def __init__(self, logger, cluster_id):
        super().__init__(logger, cluster_id)
        del self.mentionframes

class ClusterPrototype(AIFObject):
    def __init__(self, logger, cluster):
        super().__init__(logger)
        self.cluster = cluster
        self.attributes = []
        self.set_attributes()

    def get_id(self):
        return '{}-prototype'.format(self.get('cluster').get('id'))

    def get_informativejustifications(self):
        document_informativejustifications = {}
        for mention in self.get('cluster').get('mentions'):
            document_informativejustifications[mention.get('document_id')] = mention.get('justifiedBy')
        return list(document_informativejustifications.values())

    def get_link(self):
        return self.get('cluster').get('link')

    def get_mentionframes(self):
        return self.get('cluster').get('mentionframes')

    def get_prototypeargument(self, argument):
        logger = self.get('logger')
        entry = argument.get('entry')
        if isinstance(argument, RelationArgument):
            return RelationPrototypeArgument(logger, entry)
        if isinstance(argument, EventArgument):
            return EventPrototypeArgument(logger, entry)

    def get_time(self, document_id=None):
        if isinstance(self.get('cluster'), EntityCluster):
            return
        time_prototype = None
        for mention in self.get('cluster').get('mentions'):
            if document_id is not None and document_id!=mention.get('document_id'):
                continue
            time_mention = mention.get('time')
            if time_prototype is None:
                time_prototype = time_mention
            else:
                if time_mention != time_prototype:
                    mention_T1 = time_mention.get('start_time_after')
                    mention_T2 = time_mention.get('start_time_before')
                    mention_T3 = time_mention.get('end_time_after')
                    mention_T4 = time_mention.get('end_time_before')
                    prototype_T1 = time_prototype.get('start_time_after')
                    prototype_T2 = time_prototype.get('start_time_before')
                    prototype_T3 = time_prototype.get('end_time_after')
                    prototype_T4 = time_prototype.get('end_time_before')

                    # if any of the time in prototype is infinity but not in the mention,
                    # then update the time in prototype using that in the mention
                    for (prototype_T, mention_T, field_name) in [(prototype_T1, mention_T1, 'start_time_after'),
                                                 (prototype_T2, mention_T2, 'start_time_before'),
                                                 (prototype_T3, mention_T3, 'end_time_after'),
                                                 (prototype_T4, mention_T4, 'end_time_before')]:
                        if prototype_T.is_infinity() and not mention_T.is_infinity():
                            time_prototype.set(field_name, mention_T.get('copy'))

                    if mention_T1 < prototype_T1 and not mention_T1.is_negative_infinity():
                        time_prototype.set('start_time_after', mention_T1.get('copy'))
                    if mention_T2 < prototype_T2:
                        time_prototype.set('start_time_before', mention_T2.get('copy'))
                    if mention_T3 > prototype_T3:
                        time_prototype.set('end_time_after', mention_T3.get('copy'))
                    if mention_T4 > prototype_T4 and not mention_T4.is_positive_infinity():
                        time_prototype.set('end_time_before', mention_T4.get('copy'))
        return time_prototype

    def get_types(self):
        types = []
        for mention in self.get('cluster').get('mentions'):
            mention_type = mention.get('type')
            mention_type_justification = mention.get('justifiedBy')
            types.append({'type': mention_type,
                          'justifiedBy': mention_type_justification})
        return types

    def get_AIF(self):
        logger = self.get('logger')
        predicates = {
            'a': 'aida:{}'.format(self.get('EREType')),
            'aida:attributes': self.get('attributes'),
            'aida:informativeJustification': self.get('informativejustifications'),
            'aida:link': self.get('link'),
            'aida:ldcTime': self.get('time'),
            'aida:system': System(self.get('logger'))
            }
        AIF_triples = self.get('coreAIF', predicates)
        for cluster_type_and_justification in self.get('types'):
            AIF_triples.extend(
                TypeStatement(logger,
                              subject=self,
                              type=cluster_type_and_justification.get('type'),
                              justifiedBy=cluster_type_and_justification.get('justifiedBy'),
                              confidence=Confidence(logger),
                              system=System(logger)).get('AIF'))
        mentionframes = self.get('mentionframes')
        if mentionframes and len(mentionframes):
            for frame in mentionframes:
                for rolename in frame:
                    for argument in frame.get(rolename):
                        prototypeargument = self.get('prototypeargument', argument)
                        AIF_triples.extend(prototypeargument.get('AIF'))
        if self.get('link') is not None:
            AIF_triples.extend(self.get('link').get('AIF'))
        return AIF_triples

    def get_EREType(self):
        instances = {
            EntityCluster: 'Entity',
            RelationCluster: 'Relation',
            EventCluster: 'Event',
            }
        for classname in instances:
            if isinstance(self.get('cluster'), classname):
                return instances[classname]

    def get_IRI(self):
        return 'ldc:{}'.format(self.get('id'))

    def set_attributes(self):
        # TODO: set attributes here
        self.get('attributes').append(Attribute(self.get('logger')))

class EREMention(AIFObject):
    def __init__(self, logger, entry):
        super().__init__(logger)
        self.entry = entry
        self.clusters = []
        self.attributes = []
        self.set_attributes()

    def add_cluster(self, cluster):
        self.get('clusters').append(cluster)

    def get_document_id(self):
        return self.get('root_uid')

    def get_type(self):
        return self.get('qnode_type_id')

    def get_justifiedBy(self):
        return DocumentJustification(self.get('logger'),
                                     documentID=self.get('root_uid'),
                                     confidence=Confidence(self.get('logger'))
                                     )

    def get_AIF(self):
        logger = self.get('logger')
        handle = self.get('handle')
        predicates = {
            'a': 'aida:{}'.format(self.get('EREtype')),
            'aida:informativeJustification': self.get('justifiedBy'),
            'aida:justifiedBy': self.get('justifiedBy'),
            'aida:handle': '"{}"'.format(handle) if handle is not None else None,
            'aida:attributes': self.get('attributes'),
            'aida:ldcTime': self.get('time'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(
            TypeStatement(logger,
                          subject=self,
                          type=self.get('type'),
                          justifiedBy=self.get('justifiedBy'),
                          confidence=Confidence(logger),
                          system=System(logger)).get('AIF'))
        AIF_triples.extend(self.get('justifiedBy').get('AIF'))
        if self.get('time'):
            AIF_triples.extend(self.get('time').get('AIF'))
        return AIF_triples

    def get_IRI(self):
        return 'ldc:{}'.format(self.get('id'))

    def set_attributes(self):
        # TODO: set attributes here
        self.get('attributes').append(Attribute(self.get('logger')))

    def __str__(self):
        return self.get('id')

class EventMention(EREMention):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_EREtype(self):
        return 'Event'

    def get_id(self):
        return self.get('eventmention_id')

    def get_time(self):
        return LDCTimeRange(self.get('logger'), self)

class RelationMention(EREMention):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_EREtype(self):
        return 'Relation'

    def get_id(self):
        return self.get('relationmention_id')

    def get_time(self):
        return LDCTimeRange(self.get('logger'), self)

class EntityMention(EREMention):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_EREtype(self):
        return 'Entity'

    def get_id(self):
        return self.get('argmention_id')

    def get_handle(self):
        omits = ['EMPTY_NA']
        handle = self.get('text_string')
        handle = None if isinstance(handle, float) else handle
        handle = None if handle in omits else handle
        return handle

class EventOrRelationArgument(AIFObject):
    def __init__(self, logger, entry):
        super().__init__(logger)
        self.entry = entry
        self.attributes = []
        self.set_attributes()

    def get_prototypeAIF(self):
        AIF_triples = []
        for subject_cluster in self.get('subject').get('clusters'):
            for object_cluster in self.get('object').get('clusters'):
                predicates = {
                    'a': 'aida:ArgumentStatement',
                    'aida:object': object_cluster.get('prototype'),
                    'aida:predicate': self.get('predicate'),
                    'aida:subject': subject_cluster.get('prototype'),
                    'aida:attributes': self.get('attributes'),
                    'aida:justifiedBy': self.get('justifiedBy'),
                    'aida:confidence': self.get('confidence'),
                    'aida:system': self.get('system'),
                    }
                AIF_triples.extend(self.get('coreAIF', predicates))
                AIF_triples.extend(self.get('justifiedBy').get('AIF'))
                AIF_triples.extend(self.get('confidence').get('AIF'))
        return AIF_triples

    def get_AIF(self):
        predicates = {
            'a': 'aida:ArgumentStatement',
            'aida:object': self.get('object'),
            'aida:predicate': self.get('predicate'),
            'aida:subject': self.get('subject'),
            'aida:attributes': self.get('attributes'),
            'aida:justifiedBy': self.get('justifiedBy'),
            'aida:confidence': self.get('confidence'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('justifiedBy').get('AIF'))
        AIF_triples.extend(self.get('confidence').get('AIF'))
        return AIF_triples

    def get_confidence(self):
        return Confidence(self.get('logger'))

    def get_id(self):
        return '{}-{}-{}-{}'.format(
            self.get('object').get('id'),
            self.get('predicate').get('id'),
            self.get('subject').get('id'),
            self.get('justifiedBy').get('id'))

    def get_justifiedBy(self):
        return CompoundJustification(self.get('logger'),
                                     justification1=DocumentJustification(
                                         self.get('logger'),
                                         documentID=self.get('root_uid'),
                                         confidence=Confidence(self.get('logger'))),
                                     justification2=None,
                                     confidence=Confidence(self.get('logger')))

    def get_predicate(self):
        return Predicate(self.get('logger'),
                         self.get('subject').get('qnode_type_id'),
                         self.get('general_slot_type'))

    def get_prototypeid(self):
        return 'prototype{}-{}-prototype{}-{}'.format(
            self.get('object').get('id'),
            self.get('predicate').get('id'),
            self.get('subject').get('id'),
            self.get('justifiedBy').get('id'))

    def get_system(self):
        return System(self.get('logger'))

    def get_IRI(self):
        return '_:aa-{}'.format(hashlib.md5(self.get('id').encode('utf-8')).hexdigest())

    def set_attributes(self):
        # TODO: set attributes here
        self.get('attributes').append(Attribute(self.get('logger')))

class EventArgument(EventOrRelationArgument):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_subjectmention_id(self):
        return self.get('eventmention_id')

class RelationArgument(EventOrRelationArgument):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_subjectmention_id(self):
        return self.get('relationmention_id')

class EventPrototypeArgument(EventArgument):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_id(self):
        return self.get('prototypeid')

    def get_AIF(self):
        return self.get('prototypeAIF')

class RelationPrototypeArgument(RelationArgument):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)

    def get_id(self):
        return self.get('prototypeid')

    def get_AIF(self):
        return self.get('prototypeAIF')

class Justification(AIFObject):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger)
        for k,v in kwargs.items():
            self.set(key=k, value=v)

    def get_system(self):
        return System(self.get('logger'))

    def __str__(self):
        return self.get('id')

class DocumentJustification(Justification):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger, *args, **kwargs)

    def get_id(self):
        return '{}-{}'.format(
            'documentJustification',
            self.get('documentID'))

    def get_AIF(self):
        predicates = {
            'a': 'aida:DocumentJustification',
            'aida:sourceDocument': '"{}"'.format(self.get('documentID')),
            'aida:confidence': self.get('confidence'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('confidence').get('AIF'))
        return AIF_triples

    def get_IRI(self):
        return '_:bdj-{}'.format(hashlib.md5(self.__str__().encode('utf-8')).hexdigest())

class CompoundJustification(Justification):
    def __init__(self, logger, *args, **kwargs):
        super().__init__(logger, *args, **kwargs)
        self.containedJustifications = [self.get(j) for j in ['justification1', 'justification2'] if self.get(j) is not None]

    def get_id(self):
        return '-'.join(
            sorted(
                [j.__str__() for j in self.get('containedJustifications')]))

    def get_AIF(self):
        predicates = {
            'a': 'aida:CompoundJustification',
            'aida:containedJustification': self.get('containedJustifications'),
            'aida:confidence': self.get('confidence'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('confidence').get('AIF'))
        return AIF_triples

    def get_IRI(self):
        return '_:bcj-{}'.format(hashlib.md5(self.__str__().encode('utf-8')).hexdigest())

class Claim(AIFObject):
    def __init__(self, logger, entry):
        super().__init__(logger)
        self.entry = entry
        self.claimSemantics = []
        self.associatedKEs = []
        self.identicalClaims = []
        self.relatedClaims = []
        self.supportingClaims = []
        self.refutingClaims = []

    def add_claimSemantics(self, node):
        self.get('claimSemantics').append(node)

    def add_associatedKEs(self, node):
        self.get('associatedKEs').append(node)

    def add_identicalClaims(self, claim):
        self.get('identicalClaims').append(claim)

    def add_relatedClaims(self, claim):
        self.get('relatedClaims').append(claim)

    def add_supportingClaims(self, claim):
        self.get('supportingClaims').append(claim)

    def add_refutingClaims(self, claim):
        self.get('refutingClaims').append(claim)

    def get_claimer_claimcomponent(self):
        return ClaimComponent(self.get('logger'),
                              componentName=self.get('claimer'),
                              componentIdentity=self.get('qnode_claimer_identity'),
                              componentTypes=self.get('qnode_claimer_type'),
                              componentProvenance=self.get('claimer_provenance'))

    def get_claimerAffiliations(self):
        claimerAffiliations = []
        postfixes = ['', '_1', '_2']
        for postfix in postfixes:
            componentName = self.get('claimer_affiliation{}'.format(postfix))
            componentIdentity = self.get('qnode_claimer_affiliation_identity{}'.format(postfix))
            componentType = self.get('qnode_claimer_affiliation_type{}'.format(postfix))
            if componentName != 'EMPTY_NA':
                claimerAffiliations.append(ClaimComponent(self.get('logger'),
                                                          componentName=componentName,
                                                          componentIdentity=componentIdentity,
                                                          componentTypes=componentType))
        return claimerAffiliations

    def get_claimDateTime(self):
        logger = self.get('logger')
        elements = self.get('claim_datetime').split(' ')
        attribute = elements[0]
        if attribute == 'unknown':
            attribute = 'unk'
        datestring = elements[1] if len(elements) == 2 else 'EMPTY_NA'
        time =  Object(logger)
        time.set('start_date', datestring)
        time.set('start_date_type', 'start{}'.format(attribute))
        time.set('end_date', datestring)
        time.set('end_date_type', 'end{}'.format(attribute))
        time.set('where', self.get('where'))
        return LDCTimeRange(logger, time)

    def get_claimLocation(self):
        return ClaimComponent(self.get('logger'),
                              componentName=self.get('claim_location'),
                              componentIdentity=self.get('qnode_claim_location_identity'),
                              componentTypes=self.get('qnode_claim_location_type'),
                              componentProvenance=self.get('claim_location_provenance'))

    def get_document_id(self):
        return self.get('root_uid')

    def get_epistemic(self):
        return self.get('epistemic_status')

    def get_id(self):
        return self.get('claim_id')

    def get_importance(self):
        return "'XSD_DOUBLE(1.0)'"

    def get_naturalLanguageDescription(self):
        return self.get('description')

    def get_queryid(self):
        return '"TBD"'

    def get_sentiment(self):
        return self.get('sentiment_status')

    def get_xVariable(self):
        return ClaimComponent(self.get('logger'),
                              componentName=self.get('x_variable'),
                              componentIdentity=self.get('qnode_x_variable_identity'),
                              componentTypes=self.get('qnode_x_variable_type'))

    def get_AIF(self):
        predicates = {
            'a': 'aida:Claim',
            'aida:sourceDocument': '"{}"'.format(self.get('document_id')),
            'aida:claimId': '"{}"'.format(self.get('id')),
            'aida:queryId': self.get('queryid'),
            'aida:importance': self.get('importance'),
            'aida:topic': '"{}"'.format(self.get('topic')),
            'aida:subtopic': '"{}"'.format(self.get('subtopic')),
            'aida:claimTemplate': '"{}"'.format(self.get('claim_template')),
            'aida:xVariable': self.get('xVariable'),
            'aida:naturalLanguageDescription': '"{}"'.format(self.get('naturalLanguageDescription')),
            'aida:claimSemantics': self.get('claimSemantics'),
            'aida:claimer': self.get('claimer_claimcomponent'),
            'aida:claimerAffiliation': self.get('claimerAffiliations'),
            'aida:epistemic': '"{}"'.format(self.get('epistemic')),
            'aida:sentiment': '"{}"'.format(self.get('sentiment')),
            'aida:claimDateTime': self.get('claimDateTime'),
            'aida:claimLocation': '"{}"'.format(self.get('claimLocation')),
            'aida:associatedKEs': self.get('associatedKEs'),
            # 'aida:originalClaimProvenance': self.get('originalClaimProvenance'),
            # 'aida:identicalClaimSemantics': self.get('identicalClaimSemantics'),
            'aida:identicalClaims': self.get('identicalClaims'),
            'aida:relatedClaims': self.get('relatedClaims'),
            'aida:supportingClaims': self.get('supportingClaims'),
            'aida:refutingClaims': self.get('refutingClaims')
            
            # 'aida:confidence': self.get('confidence'),
            # 'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('xVariable').get('AIF'))
        AIF_triples.extend(self.get('claimer_claimcomponent').get('AIF'))
        AIF_triples.extend(self.get('claimDateTime').get('AIF'))
        AIF_triples.extend(self.get('claimLocation').get('AIF'))
        list_fields = ['claimerAffiliations', 'associatedKEs']
        for list_field in list_fields:
            for item in self.get(list_field):
                AIF_triples.extend(item.get('AIF'))
        return AIF_triples

    def get_IRI(self):
        return 'ldc:claim-{}'.format(self.get('id'))

class System(AIFObject):
    def __init__(self, logger, system='LDCModelGenerator'):
        super().__init__(logger)
        self.system = system

    def get_id(self):
        return self.get('system')

    def get_AIF(self):
        predicates = {
            'a': 'aida:System',
            }
        return self.get('coreAIF', predicates)

    def get_IRI(self):
        return 'ldc:{}'.format(self.get('id'))

class ReferenceKBLink(AIFObject):
    def __init__(self, logger, entry):
        super().__init__(logger)
        self.entry = entry

    def get_id(self):
        retVal = self.get('linkTarget')
        if self.get('referenceKB') is not None:
            retVal = '{}:{}'.format(self.get('referenceKB'), self.get('linkTarget'))
        return retVal

    def get_confidence(self):
        return Confidence(self.get('logger'))

    def get_linkTarget(self):
        return 'TBD'

    def get_referenceKB(self):
        return

    def get_AIF(self):
        predicates = {
            'a': 'aida:LinkAssertion',
            'aida:linkTarget': '"{}"'.format(self.get('id')),
            'aida:confidence': self.get('confidence'),
            'aida:system': self.get('system'),
            }
        AIF_triples = self.get('coreAIF', predicates)
        AIF_triples.extend(self.get('confidence').get('AIF'))
        return AIF_triples

    def get_IRI(self):
        return '_:lt-{}'.format(hashlib.md5(self.__str__().encode('utf-8')).hexdigest())

    def __str__(self):
        return self.get('id')

class Confidence(AIFObject):
    def __init__(self, logger, confidenceValue="'XSD_DOUBLE(1.0)'"):
        super().__init__(logger)
        self.confidenceValue = confidenceValue
        self.system = System(logger)

    def get_AIF(self):
        predicates = {
            'a': 'aida:Confidence',
            'aida:confidenceValue': self.get('confidenceValue'),
            'aida:system': self.get('system'),
            }
        return self.get('coreAIF', predicates)

    def get_IRI(self):
        return 'ldc:confidence'

class TBD(AIFObject):
    def __init__(self, logger, tbd_id):
        super().__init__(logger)
        self.id = tbd_id

    def get_IRI(self):
        return 'aida:{}'.format(self.get('id'))

class Attribute(AIFObject):
    def __init__(self, logger):
        super().__init__(logger)

    def get_IRI(self):
        return 'aida:{}'.format(self.__str__())

    def __str__(self):
        if isinstance(self, Attribute):
            return 'TBD'
        return self.get('classname')

class Negated(Attribute):
    def __init__(self, logger):
        super().__init__(logger)

class Hedged(Attribute):
    def __init__(self, logger):
        super().__init__(logger)

class Irrealis(Attribute):
    def __init__(self, logger):
        super().__init__(logger)

class Generic(Attribute):
    def __init__(self, logger):
        super().__init__(logger)

class LDCTimeField(AIFObject):
    """
    The class represents a time field like day, month, and year.
    
    This class also support generating AIF corresponding to the time field.
    """

    def __init__(self, logger, field_name, field_value, where):
        """
        Initialize a LDC time field instance.

        Parameters:
            logger (aida.Logger)
            field_name (str)
            field_value (str)
            where (dict):
                a dictionary containing the following two keys representing the file location:
                    filename
                    lineno
        """
        super().__init__(logger)
        self.logger = logger
        self.field_name = field_name
        self.field_value = field_value
        self.where = where

    def is_specified(self):
        return not self.is_unspecified()

    def is_unspecified(self):
        unspecified = {'day':'xx', 'month':'xx', 'year':'xxxx'}

        field_name = self.get('field_name')
        field_value = self.get('field_value')
        if field_value == unspecified[field_name]:
            return True
        return False

    def get_IRI(self):
        dashes = {'day':'---', 'month':'--', 'year':''}
        field_name = self.get('field_name')
        field_value = self.get('field_value')
        if self.is_specified():
            return '"{dashes}{fv}"^^xsd:g{ufn}'.format(
                        dashes = dashes[field_name],
                        fn=field_name,
                        fv=field_value,
                        ufn=field_name.capitalize())

    def __str__(self):
        return self.get('field_value')

class LDCTime(AIFObject):
    """
    The class representing LDC time of an event or relation.
    """

    def __init__(self, logger, date, start_or_end, before_or_after, where):
        """
        Initialize a LDC date instance.

        Parameters:
            logger (aida.Logger)
            date (str)
            start_or_end (str)
            before_or_after (str)
            where (dict):
                a dictionary containing the following two keys representing the file location:
                    filename
                    lineno
        """
        super().__init__(logger)
        self.logger = logger
        self.date = date
        self.start_or_end = start_or_end
        self.before_or_after = before_or_after
        self.where = where
        self.load()
        self.fix_unspecified_information()

    def set_negative_infinity(self):
        self.get('year').set('field_value', '0001')
        self.get('month').set('field_value', '01')
        self.get('day').set('field_value', '01')

    def set_positive_infinity(self):
        self.get('year').set('field_value', '9999')
        self.get('month').set('field_value', '12')
        self.get('day').set('field_value', '31')

    def set_first_day_of_the_year(self):
        self.get('month').set('field_value', '01')
        self.get('day').set('field_value', '01')

    def set_last_day_of_the_year(self):
        self.get('month').set('field_value', '12')
        self.get('day').set('field_value', '31')

    def is_negative_infinity(self):
        if self.__str__() == '0001-01-01':
            return True
        return False

    def is_positive_infinity(self):
        if self.__str__() == '9999-12-31':
            return True
        return False

    def is_infinity(self):
        return self.is_positive_infinity() or self.is_negative_infinity()

    def get_copy(self):
        return LDCTime(self.get('logger'), self.get('date'), self.get('start_or_end'), self.get('before_or_after'), self.get('where'))

    def fix_unspecified_information(self):
        self.get('method', 'fix_unspecified_information_{}'.format(self.get('time_type')))()

    def fix_unspecified_information_startafter(self):
        if self.get('year').is_unspecified():
            self.set_negative_infinity()
        if self.get('month').is_unspecified():
            self.set_first_day_of_the_year()
        if self.get('day').is_unspecified():
            self.get('day').set('field_value', '01')

    def fix_unspecified_information_startbefore(self):
        if self.get('year').is_unspecified():
            self.set_positive_infinity()
        if self.get('month').is_unspecified():
            self.set_last_day_of_the_year()
        if self.get('day').is_unspecified():
            self.get('day').set('field_value', str(monthrange(self.get('int_year'), self.get('int_month'))[1]))

    def fix_unspecified_information_endafter(self):
        if self.get('year').is_unspecified():
            self.set_negative_infinity()
        if self.get('month').is_unspecified():
            self.set_first_day_of_the_year()
        if self.get('day').is_unspecified():
            self.get('day').set('field_value', '01')

    def fix_unspecified_information_endbefore(self):
        if self.get('year').is_unspecified():
            self.set_positive_infinity()
        if self.get('month').is_unspecified():
            self.set_last_day_of_the_year()
        if self.get('day').is_unspecified():
            self.get('day').set('field_value', str(monthrange(self.get('int_year'), self.get('int_month'))[1]))

    def load(self):
        """
        Parse the date string, extract and store different fields
        """
        if self.get('date') == 'EMPTY_NA':
            return
        group_nums = {'year':1, 'month':2, 'day':3}
        pattern = re.compile('^(....)-(..)-(..).*?$')
        match = pattern.match(str(self.get('date')))
        if match:
            for field_name in group_nums:
                self.set(field_name, LDCTimeField(
                                        self.get('logger'),
                                        field_name,
                                        match.group(group_nums[field_name]),
                                        self.get('where')))
        else:
            self.get('logger').record_event('UNEXPECTED_DATE_FORMAT', self.get('date'), self.get('where'))

    def get_int_year(self):
        return int(self.get('year').get('field_value'))

    def get_int_month(self):
        return int(self.get('month').get('field_value'))

    def get_int_day(self):
        return int(self.get('day').get('field_value'))

    def get_date_object(self):
        return datetime.date(self.get('int_year'), self.get('int_month'), self.get('int_day'))

    def get_time_type(self):
        return '{}{}'.format(self.get('start_or_end').lower(), self.get('before_or_after').lower())

    def get_AIF(self):
        predicates = {
            'a': 'aida:LDCTimeComponent',
            'aida:timeType': '"{}"'.format(self.get('before_or_after').upper()),
            'aida:day': self.get('day').get('IRI'),
            'aida:month': self.get('month').get('IRI'),
            'aida:year': self.get('year').get('IRI'),
            }
        return self.get('coreAIF', predicates)

    def get_IRI(self):
        return '_:tc-{}'.format(hashlib.md5(self.__str__().encode('utf-8')).hexdigest())

    def __lt__(self, other):
        return self.get('date_object') < other.get('date_object')

    def __le__(self, other):
        return self.get('date_object') <= other.get('date_object')

    def __gt__(self, other):
        return self.get('date_object') > other.get('date_object')

    def __ge__(self, other):
        return self.get('date_object') >= other.get('date_object')

    def __eq__(self, other):
        return self.get('date_object') == other.get('date_object')

    def __ne__(self, other):
        return self.get('date_object') != other.get('date_object')

    def __str__(self):
        return '{}-{}-{}-{}'.format(self.get('before_or_after'), self.get('year'), self.get('month'), self.get('day'))

class LDCTimeRange(AIFObject):
    def __init__(self, logger, time):
        super().__init__(logger)
        self.start_date = time.get('start_date')
        self.start_date_type = time.get('start_date_type')
        self.end_date = time.get('end_date')
        self.end_date_type = time.get('end_date_type')
        self.where = time.get('where')
        self.load()

    def load(self):
        self.start_time_before, self.start_time_after = self.get('time_range', 'start')
        self.end_time_before, self.end_time_after = self.get('time_range', 'end')

    def get_copy(self):
        return LDCTimeRange(self.get('logger'),
                            self.get('start_date'),
                            self.get('start_date_type'),
                            self.get('end_date'),
                            self.get('end_date_type'),
                            self.get('where'))

    def get_time_range(self, start_or_end):
        logger = self.get('logger')
        where = self.get('where')
        date_type = self.get('{}_date_type'.format(start_or_end))
        if date_type == '{}after'.format(start_or_end):
            date_after = self.get('{}_date'.format(start_or_end))
            date_before = '9999-12-31'
        elif date_type == '{}before'.format(start_or_end):
            date_after = '0001-01-01'
            date_before = self.get('{}_date'.format(start_or_end))
        elif date_type == '{}on'.format(start_or_end):
            date_after = self.get('{}_date'.format(start_or_end))
            date_before = self.get('{}_date'.format(start_or_end))
        elif date_type == '{}unk'.format(start_or_end):
            date_after = '0001-01-01'
            date_before = '9999-12-31'
        return [LDCTime(logger, date_before, start_or_end, 'BEFORE', where), LDCTime(logger, date_after, start_or_end, 'AFTER', where)]

    def get_starts(self):
        return [self.get('start_time_before'), self.get('start_time_after')]

    def get_ends(self):
        return [self.get('end_time_before'), self.get('end_time_after')]

    def get_AIF(self):
        AIF_triples = []
        if not self.is_invalid():
            predicates = {
                'a': 'aida:LDCTime',
                'aida:start': self.get('starts'),
                'aida:end': self.get('ends'),
                'aida:system': System(self.get('logger'))
                }
            AIF_triples = self.get('coreAIF', predicates)
            if self.get('starts'):
                for start in self.get('starts'):
                        AIF_triples.extend(start.get('AIF'))
            if self.get('ends'):
                for end in self.get('ends'):
                        AIF_triples.extend(end.get('AIF'))
        return AIF_triples

    def get_IRI(self):
        return '_:bcm-{}'.format(hashlib.md5(self.__str__().encode('utf-8')).hexdigest())

    def is_invalid(self):
        T1 = self.get('start_time_after')
        T2 = self.get('start_time_before')
        T3 = self.get('end_time_after')
        T4 = self.get('end_time_before')
        if T1 > T2 or T3 > T4 or T4 < T1:
            return True
        return False

    def __str__(self):
        return "({},{})-({},{})".format(self.get('start_time_after'),
                                        self.get('start_time_before'),
                                        self.get('end_time_after'),
                                        self.get('end_time_before'))

    def __ne__(self, other):
        return self.__str__() != other.__str__()

class Predicate(AIFObject):
    def __init__(self, logger, subject_type, rolename):
        super().__init__(logger)
        self.subject_type = subject_type
        self.rolename = rolename

    def get_IRI(self):
        return self.__str__()

    def __str__(self):
        return '"{}:{}"'.format(
            self.get('subject_type'),
            self.get('rolename'))

class AIF(Object):
    def __init__(self, logger, annotations):
        super().__init__(logger)
        self.annotations = annotations
        self.system = System(logger)
        self.claims = {}
        self.clusters = {}
        self.links = {}
        self.mentions = {}
        self.mentionframes = {}
        self.generate()

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

    def add_annotation_entry(self, sheet_name, entry):
        methods = {
            'argument_KEs':   {'method': EntityMention, 'entry_type': 'mention'},
            'event_KEs':      {'method': EventMention, 'entry_type': 'mention'},
            'relation_KEs':   {'method': RelationMention, 'entry_type': 'mention'},
            'event_slots':    {'method': EventArgument, 'entry_type': 'argument'},
            'relation_slots': {'method': RelationArgument, 'entry_type': 'argument'},
            'kb_links':       {'method': ReferenceKBLink, 'entry_type': 'link'},
            'claims':         {'method': Claim, 'entry_type': 'claim'}
            }
        method = methods[sheet_name]['method'] if sheet_name in methods else None
        if method:
                self.add(methods[sheet_name]['entry_type'], method(self.get('logger'), entry))
        else:
            self.record_event('METHOD_NOT_FOUND', methods[sheet_name]['method'], self.get('code_location'))

    def add_mention(self, mention):
        self.get('mentions')[mention.get('id')] = mention

    def add_argument(self, argument):
        subjectmention_id = argument.get('subjectmention_id')
        slot_type = argument.get('general_slot_type')
        argmention_id = argument.get('argmention_id')
        subjectmention = self.get('mention', subjectmention_id)
        argmention = self.get('mention', argmention_id)
        argument.get('entry').set('subject', subjectmention)
        argument.get('entry').set('object', argmention)
        if subjectmention_id not in self.get('mentionframes'):
            self.get('mentionframes')[subjectmention_id] = {}
        if slot_type not in self.get('mentionframes').get(subjectmention_id):
            self.get('mentionframes')[subjectmention_id][slot_type] = []
        self.get('mentionframes').get(subjectmention_id).get(slot_type).append(argument)

    def add_claim(self, claim):
        self.get('claims')[claim.get('claim_id')] = claim

    def add_link(self, link):
        links = self.get('links')
        qnode_kb_id_entity = link.get('qnode_kb_id_identity')
        if qnode_kb_id_entity not in links:
            links[qnode_kb_id_entity] = []
        links[qnode_kb_id_entity].append(link)

    def augment_claims(self):
        for claim in self.get('claims').values():
            for mention_id in claim.get('claim_semantics').split(','):
                mention_id = mention_id.strip()
                for cluster in self.get('mention', mention_id).get('clusters'):
                    claim.add('claimSemantics', cluster)
            for mention_id in claim.get('associated_kes').split(','):
                mention_id = mention_id.strip()
                for cluster in self.get('mention', mention_id).get('clusters'):
                    claim.add('associatedKEs', cluster)
            print('--TODO: add identicalClaims, relatedClaims, supportingClaims, refutingClaims')
            relatedness = ['identical', 'related', 'supporting', 'refuting']
            for relatedness_type in relatedness:
                for related_claim in self.get('{}Claims'.format(relatedness_type), claim):
                    claim.add('{}Claims'.format(relatedness_type), related_claim)

    def get_mention(self, mention_id):
        return self.get('mentions').get(mention_id)

    def get_mentionframe(self, mention_id):
        return self.get('mentionframes').get(mention_id)

    def get_identicalClaims(self, claim):
        print('--TODO: get_identicalClaims')
        return [TBD(self.get('logger'), 'TBD1'),
                TBD(self.get('logger'), 'TBD2')]

    def get_relatedClaims(self, claim):
        print('--TODO: get_relatedClaims')
        return [TBD(self.get('logger'), 'TBD1'),
                TBD(self.get('logger'), 'TBD3')]

    def get_supportingClaims(self, claim):
        print('--TODO: get_supportingClaims')
        return [TBD(self.get('logger'), 'TBD2'),
                TBD(self.get('logger'), 'TBD3')]

    def get_refutingClaims(self, claim):
        print('--TODO: get_refutingClaims')
        return [TBD(self.get('logger'), 'TBD1'),
                TBD(self.get('logger'), 'TBD4')]

    def get_AIF(self):
        AIF_triples = self.get('system').get('AIF')
        AIF_triples.extend(self.get('prefix_triples'))
        for cluster in self.get('clusters').values():
            AIF_triples.extend(cluster.get('AIF'))
        for claim in self.get('claims').values():
            AIF_triples.extend(claim.get('AIF'))
        return AIF_triples

    def get_prefix_triples(self):
        """
        Gets the prefix triples.
        """
        triple_block = """\
            @prefix aida:  <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/InterchangeOntology#> .
            @prefix ldc:   <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/LdcAnnotations#> .
            @prefix ldcOnt: <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/LDCOntologyM36#> .
            @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
        """
        AIF_triples = []
        for line in triple_block.split('\n'):
            line = line.strip()
            if line != '':
                AIF_triples.append(line)
        return AIF_triples

    def get_cluster(self, cluster_id):
        return self.get('clusters').get(cluster_id) if cluster_id in self.get('clusters') else None

    def get_worksheets(self):
        return self.get('annotations').get('worksheets')

    def get_worksheet(self, sheet_name):
        return self.get('annotations').get('worksheets').get(sheet_name)

    def generate_clusters(self):
        # generate clusters for all mentions in kb_linking table
        for cluster_id in self.get('links'):
            for link in self.get('links').get(cluster_id):
                mention_id = link.get('mention_id')
                mention = self.get('mention', mention_id)
                mentionframe = self.get('mentionframe', mention_id)
                if mention.get('cluster') is not None:
                    self.record_event('MENTION_CLUSTER_EXISTS', mention_id, cluster_id, link.get('where'))
                cluster = self.get('cluster', cluster_id)
                if cluster:
                    cluster.add('mention', mention)
                    cluster.add('link', link)
                    if mentionframe:
                        cluster.add('frame', mentionframe)
                else:
                    if isinstance(mention, EventMention):
                        cluster = EventCluster(self.get('logger'), cluster_id)  \
                                    .add('mention', mention) \
                                    .add('frame', mentionframe)
                    elif isinstance(mention, RelationMention):
                        cluster = RelationCluster(self.get('logger'), cluster_id)  \
                                    .add('mention', mention) \
                                    .add('frame', mentionframe)
                    elif isinstance(mention, EntityMention):
                        cluster = EntityCluster(self.get('logger'), cluster_id)  \
                                    .add('mention', mention)
                    self.get('clusters')[cluster.get('id')] = cluster
                mention.add('cluster', cluster)
        for mention in self.get('mentions').values():
            if not len(mention.get('clusters')):
                self.record_event('MENTION_NOT_IN_CLUSTER', mention.get('id'))

    def generate(self):
        print('--TODO: generate a file per claim in output')
        print('--TODO: generate a single cluster prototype by accumulation attributes from members')
        print('--TODO: add attributes using the set_attributes methods (note there are three such methods)')
        print('--TODO: handle case where componentType is a list - determine exactly how LDC will represent it')
        print('--TODO: pick prototype informative justification not arbitrarily')
        print('--TODO: determine how LDC would specify multiple X variables in the annotations; handle accordingly')
        print('--TODO: determine if claimSemantics/associatedKEs would include cluster IDs or mentiosn')
        for sheet_name in self.get('worksheets'):
            for entry in self.get('worksheet', sheet_name):
                self.add('annotation_entry', sheet_name, entry)
        self.generate_clusters()
        self.augment_claims()

    def patch(self, serialized_output):
        """
        Applies patch to the serialized output, and returns the updated string.
        """
        print('--patching output')
        # apply patch to year in the output
        patched_output = serialized_output.replace('-01-01"^^xsd:gYear', '"^^xsd:gYear')
        # apply patch to xsd:double in the output
        pattern = compile('XSD_DOUBLE\((.*?)\)')
        double_values = {}
        for (double_val) in findall(pattern, patched_output):
            double_values[double_val] = 1
        for double_val in double_values:
            str_to_replace = '"XSD_DOUBLE({double_val})"'.format(double_val=double_val)
            str_to_replace_by = '"{double_val}"^^xsd:double'.format(double_val=double_val)
            patched_output = patched_output.replace(str_to_replace, str_to_replace_by)
        return patched_output

    def write_output(self, filename):
        with open(filename, 'w') as program_output:
            raw = False
            graph = '\n'.join(sorted({e:1 for e in self.get('AIF')}))
            if not raw:
                g = Graph()
                g.parse(data=graph, format="turtle")
                # graph = self.patch(g.serialize(format="turtle").decode('utf-8'))
                graph = self.patch(g.serialize(format="turtle"))
            program_output.write(graph)

def check_paths(args):
    check_for_paths_existance([
                 args.errors, 
                 args.annotations
                 ])
    check_for_paths_non_existance([args.output])

def check_for_paths_existance(paths):
    """
    Checks if the required files and directories were present,
    exit with an error code if any of the required file or directories
    were not found.
    """
    for path in paths:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)

def check_for_paths_non_existance(paths):
    """
    Checks if the required files and directories were not present,
    exit with an error code if any of the required file or directories
    were not found.
    """
    for path in paths:
        if os.path.exists(path):
            print('Error: Path {} exists'.format(path))
            exit(ERROR_EXIT_CODE)

def main(args):
    """
    The main program for generating AIF
    """
    check_paths(args)
    logger = Logger(args.log, args.errors, sys.argv)
    include_worksheets = {
        'TA3_arg_KEs':                 'argument_KEs',
        'TA3_evt_KEs':                 'event_KEs',
        'TA3_rel_KEs':                 'relation_KEs',
        'TA3_evt_slots':               'event_slots',
        'TA3_rel_slots':               'relation_slots',
        'TA3_kb_linking':              'kb_links',
        'ClaimFrameTemplate Examples': 'claims'
        }
    annotations = Annotations(logger, args.annotations, include_worksheets=include_worksheets)
    aif = AIF(logger, annotations)
    aif.write_output(args.output)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    # create a parse and add command line arguments
    parser = argparse.ArgumentParser(description="Generate AIF")
    parser.add_argument('-l', '--log', default='log.txt', 
                        help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, 
                        help='Print version number and exit')
    parser.add_argument('errors', type=str,
                        help='File containing error specifications')
    parser.add_argument('annotations', type=str,
                        help='Directory containing annotations package as received from LDC')
    parser.add_argument('output', type=str,
                        help='Specify a directory to which output should be written')
    # parse the argument and call main
    args = parser.parse_args()
    main(args)