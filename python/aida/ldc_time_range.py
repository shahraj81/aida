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
        self.start_time = LDCTime(logger, start_date, start_date_type, where)
        self.end_time = LDCTime(logger, end_date, end_date_type, where)
        self.where = where

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
        ldc_start_time_triples = self.get('start_time').get('aif', time_iri, ldc_start_time_blank_node_iri)
        ldc_end_time_triples = self.get('end_time').get('aif', time_iri, ldc_end_time_blank_node_iri)
        ldc_time_assertion_triples = """\
            ldc:{ere_object_id} aida:ldcTime _:bldctime{ere_object_id} .
            _:bldctime{ere_object_id} a aida:LDCTime .
            _:bldctime{ere_object_id} aida:system {system} .
            {ldc_start_time_triples}
            {ldc_end_time_triples}
        """.format(ere_object_id = ere_object_id,
                   ldc_start_time_triples = ldc_start_time_triples,
                   ldc_end_time_triples = ldc_end_time_triples,
                   system = system_name)
        return ldc_time_assertion_triples