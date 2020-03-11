"""
AIDA argument specs for ontology files
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 February 2020"

from aida.object import Object

class ArgumentSpec(Object):
    def __init__(self, logger, entry, arg_num):
        self.logger = logger
        self.entry = entry
        self.argument_num = arg_num
        self.label = entry.get('arg{} label'.format(arg_num))
        self.output_value = entry.get('Output value for arg{}'.format(arg_num))