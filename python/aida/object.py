"""
AIDA object class to serve as the base class
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from inspect import currentframe, getouterframes

class Object(object):
    """
    This class represents an AIDA object which is envisioned to be the parent of most of the AIDA related classes.
    
    At a high level this class is a wrapper around a single dictionary object which provides support for custom getters.
    """

    def __init__(self, logger):
        self.logger = logger
            
    def get(self, key, *args):
        if key is None:
            self.logger('KEY_IS_NONE', self.get('code_location'))
        method = self.get_method("get_{}".format(key))
        if method is not None:    
            return method(*args)
        else:
            value = getattr(self, key, None)
            return value
        
    def get_method(self, method_name):
        try:
            method = getattr(self, method_name)
            if not hasattr(method, "__call__"):
                raise AttributeError()
        except AttributeError:
            method = None
        return method
    
    def get_code_location(self):
        caller_frame_info = getouterframes(currentframe(), 2)[2]
        where = {'filename': caller_frame_info.filename, 'lineno': caller_frame_info.lineno}
        return where
    
    def record_event(self, event_code, *args):
        self.get('logger').record_event(event_code, *args)
    
    def set(self, key, value):
        setattr(self, key, value)