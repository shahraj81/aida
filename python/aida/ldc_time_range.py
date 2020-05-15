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

    def __init__(self, logger, ere_object_id, start_date, start_date_type, end_date, end_date_type, where):
        """
        Initialize a LDCTimeRange instance.

        Parameters:
            logger (aida.Logger)
            ere_object_id (str)
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
        self.ere_object_id = ere_object_id
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
            date_before = '9999-01-01'
        elif date_type == '{}before'.format(start_or_end):
            date_after = '-9999-01-01'
            date_before = self.get('{}_date'.format(start_or_end))
        elif date_type == '{}on'.format(start_or_end):
            date_after = self.get('{}_date'.format(start_or_end))
            date_before = self.get('{}_date'.format(start_or_end))
        elif date_type == '{}unk'.format(start_or_end):
            date_after = '-9999-01-01'
            date_before = '9999-01-01'
        return [LDCTime(logger, date_before, start_or_end, 'BEFORE', where), LDCTime(logger, date_after, start_or_end, 'AFTER', where)]

    def get_aif(self, system_name):
        """
        Gets the AIF corresponding to the LDCTimeRange.
        
        Parameters:
            system_name (str)
        """
        ere_object_id = self.get('ere_object_id')
        ldc_start_time_blank_node_iri = '_:bldctime{ere_object_id}-start'.format(ere_object_id = ere_object_id)
        ldc_end_time_blank_node_iri = '_:bldctime{ere_object_id}-end'.format(ere_object_id = ere_object_id)
        time_iri = '_:bldctime{ere_object_id}'.format(ere_object_id = ere_object_id)
        ldc_start_time_before_triples = self.get('start_time_before').get('aif', time_iri, '{}-before'.format(ldc_start_time_blank_node_iri))
        ldc_end_time_before_triples = self.get('end_time_before').get('aif', time_iri, '{}-before'.format(ldc_end_time_blank_node_iri))
        ldc_start_time_after_triples = self.get('start_time_after').get('aif', time_iri, '{}-after'.format(ldc_start_time_blank_node_iri))
        ldc_end_time_after_triples = self.get('end_time_after').get('aif', time_iri, '{}-after'.format(ldc_end_time_blank_node_iri))
        ldc_time_assertion_triples = """\
            ldc:{ere_object_id} aida:ldcTime _:bldctime{ere_object_id} .
            _:bldctime{ere_object_id} a aida:LDCTime .
            _:bldctime{ere_object_id} aida:system {system} .
            {ldc_start_time_before_triples}
            {ldc_start_time_after_triples}
            {ldc_end_time_before_triples}
            {ldc_end_time_after_triples}
        """.format(ere_object_id = ere_object_id,
                   ldc_start_time_before_triples = ldc_start_time_before_triples,
                   ldc_start_time_after_triples = ldc_start_time_after_triples,
                   ldc_end_time_before_triples = ldc_end_time_before_triples,
                   ldc_end_time_after_triples = ldc_end_time_after_triples,
                   system = system_name)
        return ldc_time_assertion_triples