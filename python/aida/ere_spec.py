"""
AIDA ERESpec for Ontology files to serve as base class for the following classes: EntitySpec, EventSpec and RelationSpec
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 February 2020"

from aida.object import Object

def unspecified(ere_type):
    """
    Determine if the ere_type provided as argument is unspecified. Return True if so,
    False otherwise.

    Note: Current implementation considers an ERE type to be unspecified if it's one
    of the following:

        unspecified
        n/a
        none
        not present
    """
    if ere_type.lower() in ['unspecified', 'n/a', 'none', 'not present']:
        return True
    return False

class ERESpec(Object):
    """
    AIDA ERESpec for Ontology files to serve as base class for the following classes:

        EntitySpec
        EventSpec
        RelationSpec
    """

    def __init__(self, logger, entry):
        """
        Initializes the ERESpec instance using the entry corresponding to the line from the ontology file.

        Note: the constructor calls the constructor of EntitySpec, RelationSpec, and EventSpec for
        populating type, subtype, and subsubtype. Methods defined in this class get type, subtype, and
        subsubtype from the corresponding derived classes.
        """
        super().__init__(logger)
        self.entry = entry

    def get_raw_full_type(self):
        """
        Gets the full raw type code, corresponding to the entry, by concatenating type, subtype, and subsubtype,
        separated by '.' (a period).
        """
        return '{}.{}.{}'.format(self.get('type'), self.get('subtype'), self.get('subsubtype'))

    def get_raw_full_type_ov(self):
        """
        Gets the full raw OV (i.e. output value) type, corresponding to the entry, by concatenating type, subtype,
        and subsubtype, separated by '.' (a period).
        """
        return '{}.{}.{}'.format(self.get('type_ov'), self.get('subtype_ov'), self.get('subsubtype_ov'))

    def get_cleaned_full_type(self):
        """
        Gets the full type code, corresponding to the entry, by concatenating type, subtype, and subsubtype,
        separated by '.' (a period) after omitting the trailing unspecified types.
        """
        if unspecified(self.get('type')):
            return
        full_type = self.get('type')
        if not unspecified(self.get('subtype')):
            full_type = '{}.{}'.format(self.get('type'), self.get('subtype'))
        if not unspecified(self.get('subtype')) and not unspecified(self.get('subsubtype')):
            full_type = '{}.{}.{}'.format(self.get('type'), self.get('subtype'), self.get('subsubtype'))
        return full_type

    def get_cleaned_full_type_ov(self):
        """
        Gets the full raw OV (i.e. output value) type, corresponding to the entry, by concatenating type, subtype,
        and subsubtype, separated by '.' (a period) after omitting the trailing unspecified types.
        """
        if unspecified(self.get('type')):
            return
        full_type = self.get('type_ov')
        if not unspecified(self.get('subtype_ov')):
            full_type = '{}.{}'.format(self.get('type_ov'), self.get('subtype_ov'))
        if not unspecified(self.get('subtype_ov')) and not unspecified(self.get('subsubtype_ov')):
            full_type = '{}.{}.{}'.format(self.get('type_ov'), self.get('subtype_ov'), self.get('subsubtype_ov'))
        return full_type