"""
The class representing LDC time of an event or relation.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 May 2020"

from aida.object import Object
from aida.ldc_time_field import LDCTimeField
import re

class LDCTime(Object):
    """
    The class representing LDC time of an event or relation.
    """

    def __init__(self, logger, date, date_type, where):
        """
        Initialize a LDC date instance.

        Parameters:
            logger (aida.Logger)
            time (str)
            date_type(str)
            where (dict):
                a dictionary containing the following two keys representing the file location:
                    filename
                    lineno
        """
        super().__init__(logger)
        self.logger = logger
        self.date = date
        self.date_type = date_type
        self.where = where
        self.load()

    def load(self):
        """
        Parse the date string, extract and store different fields
        """
        if self.get('date') == 'EMPTY_NA':
            return
        group_nums = {'year':1, 'month':2, 'day':3}
        pattern = re.compile('^(....)-(..)-(..)$')
        match = pattern.match(self.get('date'))
        if match:
            for field_name in group_nums:
                self.set(field_name, LDCTimeField(
                                        self.get('logger'),
                                        field_name,
                                        match.group(group_nums[field_name]),
                                        self.get('where')))
        else:
            self.get('logger').record_event('UNEXPECTED_DATE_FORMAT', self.get('date'), self.get('where'))

    def get_aif(self, parent_iri, iri):
        """
        Gets the AIF corresponding to the LDCTime.

        Parameters:
            parent_iri (str):
                The IRI of the ERE object to which the LDCTime node be attached.
            iri (str):
                The IRI of the LDCTime node.
        """
        if self.get('date') == 'EMPTY_NA':
            return ''
        type_map = {
                'starton' : 'ON',
                'endon' : 'ON',
                'startbefore' : 'BEFORE',
                'endbefore' : 'BEFORE',
                'endunk' : 'UNKNOWN',
                'endafter' : 'AFTER',
                'startafter' : 'AFTER',
                'startunk' : 'UNKNOWN'
            }
        start_or_end = {
                'starton' : 'start',
                'endon' : 'end',
                'startbefore' : 'start',
                'endbefore' : 'end',
                'endunk' : 'end',
                'endafter' : 'end',
                'startafter' : 'start',
                'startunk' : 'start'
            }
        date_type = self.get('date_type')
        ldc_time_type_triple = '{iri} aida:timeType "{type}" .'.format(iri = iri, type = type_map[date_type])
        ldc_time_triples = """\
            {parent_iri} aida:{start_or_end} {iri} .
            {iri} a aida:LDCTimeComponent .
            {ldc_time_day_triples}
            {ldc_time_month_triples}
            {ldc_time_year_triples}
            {ldc_time_type_triple}
        """.format(parent_iri = parent_iri,
                   start_or_end = start_or_end[date_type],
                   iri = iri,
                   ldc_time_day_triples = self.get('day').get('aif', iri),
                   ldc_time_month_triples = self.get('month').get('aif', iri),
                   ldc_time_year_triples = self.get('year').get('aif', iri),
                   ldc_time_type_triple = ldc_time_type_triple)
        return ldc_time_triples