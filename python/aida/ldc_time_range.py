"""
The class representing a time range.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 May 2020"

from aida.object import Object
from aida.ldc_time import LDCTime

class LDCTimeRange(Object):
    """
    The class represents a time range.
    """

    def __init__(self, logger, start_date, start_date_type, end_date, end_date_type, where):
        """
        Initialize a LDCTimeRange instance.

        Parameters:
            logger (aida.Logger)
            start_date (str)
            start_date_type (str)
            end_date (str)
            end_date_type (str)
            where (dict):
                a dictionary containing the following two keys representing the file location:
                    filename
                    lineno
        """
        super().__init__(logger)
        self.logger = logger
        self.start_date = start_date
        self.start_date_type = start_date_type
        self.end_date = end_date
        self.end_date_type = end_date_type
        self.load()
        self.where = where

    def load(self):
        self.start_time_before, self.start_time_after = self.get('time_range', 'start')
        self.end_time_before, self.end_time_after = self.get('time_range', 'end')

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

    def get_aif(self, parent_iri, iri, system_name):
        """
        Gets the AIF corresponding to the LDCTimeRange.
        
        Parameters:
            system_name (str)
        """
        if self.is_invalid():
            return ''
        ldc_start_time_blank_node_iri = '{iri}-start'.format(iri = iri)
        ldc_end_time_blank_node_iri = '{iri}-end'.format(iri = iri)
        ldc_start_time_before_triples = self.get('start_time_before').get('aif', iri, '{}-before'.format(ldc_start_time_blank_node_iri))
        ldc_end_time_before_triples = self.get('end_time_before').get('aif', iri, '{}-before'.format(ldc_end_time_blank_node_iri))
        ldc_start_time_after_triples = self.get('start_time_after').get('aif', iri, '{}-after'.format(ldc_start_time_blank_node_iri))
        ldc_end_time_after_triples = self.get('end_time_after').get('aif', iri, '{}-after'.format(ldc_end_time_blank_node_iri))
        ldc_time_assertion_triples = """\
            {parent_iri} aida:ldcTime {iri} .
            {iri} a aida:LDCTime .
            {iri} aida:system {system} .
            {ldc_start_time_before_triples}
            {ldc_start_time_after_triples}
            {ldc_end_time_before_triples}
            {ldc_end_time_after_triples}
        """.format(iri = iri,
                   parent_iri = parent_iri,
                   ldc_start_time_before_triples = ldc_start_time_before_triples,
                   ldc_start_time_after_triples = ldc_start_time_after_triples,
                   ldc_end_time_before_triples = ldc_end_time_before_triples,
                   ldc_end_time_after_triples = ldc_end_time_after_triples,
                   system = system_name)
        return ldc_time_assertion_triples

    def get_copy(self):
        return LDCTimeRange(self.get('logger'),
                            self.get('start_date'),
                            self.get('start_date_type'),
                            self.get('end_date'),
                            self.get('end_date_type'),
                            self.get('where'))

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