"""
AIDA container class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object

class Container(Object):
    """
    The AIDA container class.

    Internally, the objects of this class store objects in a dictionary. 
    """

    def __init__(self, logger):
        super().__init__(logger)
        self.store = {}
    
    def __iter__(self):
        return iter(self.store)
        
    def get(self, key, *args, default=None):
        value = super().get(key, *args)
        if value:
            return value
        elif key in self.store:
            return self.store[key]
        else:
            if value is None and default is not None:
                value = default
                self.add(key=key, value=value)
            return value
        
    def set(self, key, value):
        if key in self.store:
            self.store[key] = value
        else:
            super().set(key, value)
            
    def exists(self, key):
        return key in self.store

    def add(self, value, key=None):
        if key is None:
            self.store[len(self.store)] = value
        else:
            self.store[key] = value

    def dict(self):
        return self.store

    def keys(self):
        return self.store.keys()
    
    def values(self):
        return self.store.values()