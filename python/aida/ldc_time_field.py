"""
The class representing a time field like day, month, and year.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 May 2020"

from aida.object import Object

unspecified = {'day':'xx', 'month':'xx', 'year':'xxxx'}

class LDCTimeField(Object):
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
        field_name = self.get('field_name')
        field_value = self.get('field_value')
        if field_value == unspecified[field_name]:
            return True
        return False


    def get_aif(self, iri):
        """
        Gets the AIF corresponding to the LDC Time Field.

        Parameters:
            iri (str):
                The IRI of the LDCTime field.
        """
        dashes = {'day':'---', 'month':'--', 'year':''}
        field_name = self.get('field_name')
        field_value = self.get('field_value')
        triple = ''
        if self.is_specified():
            triple = '{iri} aida:{fn} "{dashes}{fv}"^^xsd:g{ufn} .'.format(
                        iri=iri,
                        dashes = dashes[field_name],
                        fn=field_name,
                        fv=field_value,
                        ufn=field_name.capitalize())
        return triple

    def __str__(self):
        return self.get('field_value')