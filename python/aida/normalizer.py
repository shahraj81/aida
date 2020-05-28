"""
Normalizer for values in AIDA response.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "24 January 2020"

from aida.object import Object

import re

class Normalizer(Object):
    """
    Normalizer for values in AIDA response.
    """

    def __init__(self, logger):
        super().__init__(logger)

    def normalize(self, responses, method_name, entry, attribute):
        method = self.get_method(method_name)
        method(responses, entry, attribute)

    def normalize_entity_type(self, responses, entry, attribute):
        attribute_name = attribute.get('name')
        value = entry.get(attribute_name)
        pattern = re.compile('^<.*?#(.*?)>$')
        match = pattern.match(value)
        if match:
            value = match.group(1)
            entry.set(attribute_name, value)