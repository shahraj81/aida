"""
Query class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 January 2020"

from aida.object import Object

class Query(Object):
    """
    Query class.
    """

    def __init__(self, logger):
        super().__init__(logger)
    
    def get_TASK_AND_TYPE_CODE(self):
        task_code, type_code = self.get('id').split('_')[1:3]
        code = "{}_{}".format(task_code, type_code)
        return code