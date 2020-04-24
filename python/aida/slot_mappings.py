"""
Slots used to map between LDC's internal code for a slot, and its corresponding external slot name.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "26 December 2019"

import pandas as pd
from aida.object import Object

class SlotMappings(Object):
    """
    Slots used to map between LDC's internal code for a slot, and its corresponding external slot name.
    """

    # the dictionary used to store mappings
    mappings = {'code_to_type':{}, 'type_to_codes':{}}
    
    def __init__(self, logger, filename):
        """
        Initialize the slots object.
        
        Parameters:
            logger (logger):
                the logger object
            filename (str):
                the name of the file containing mappings between LDC 
                internal slot code, and external slot name.
            
        The file contains tab separated values with header in first line.
            
        For example,    
            slot_type_code    slot_type
            evt001arg01damagerdestroyer    ArtifactExistence.DamageDestroy_DamagerDestroyer
            evt002arg01damager    ArtifactExistence.DamageDestroy.Damage_Damager
        """
        super().__init__(logger)
        # load the data and store the mapping in a dictionary
        df = pd.read_csv(filename, delimiter="\t")
        for index, row in df.iterrows():
            linenum = index+2;
            # check if the value in column 'slot_type_code' is unique across the file
            if row.slot_type_code in self.mappings['code_to_type'].keys():
                where = {'filename': filename, 'lineno':linenum}
                logger.record_event('DUPLICATE_VALUE_IN_COLUMN', row.slot_type_code, 'slot_type_code', where)
            # store code-to-type mapping
            self.mappings['code_to_type'][row.slot_type_code] = row.slot_type
            # store type-to-codes mapping
            if row.slot_type not in self.mappings['type_to_codes'].keys():
                self.mappings['type_to_codes'][row.slot_type] = {}
            self.mappings['type_to_codes'][row.slot_type][row.slot_type_code] = 1

    def get_type_to_codes(self, slot_type):
        """
        Get the slot_codes mapped to the slot_type.
        
        Parameters:
            slot_type (str):
                the slot_type for which the mapped slot_codes are desired.
                
        Returns:
            slot_codes (list):
                the list containing slot_codes mapped to the slot_type.
                
            None is returned if no slot_codes were found.
        """
        slot_codes = None
        if slot_type in self.mappings['type_to_codes'].keys():
            slot_codes = list(self.mappings['type_to_codes'][slot_type].keys())
        return slot_codes
    
    def get_code_to_type(self, slot_code):
        """
        Get the slot_type mapped to the slot_code.
        
        Parameters:
            slot_code (str):
                the slot_code for which the mapped slot_type is desired.
                
        Returns:
            slot_type (str):
                the slot_type mapped to the slot_code.
            
            None is returned if slot_type is not found.
        """
        slot_type = None
        if slot_code in self.mappings['code_to_type'].keys():
            slot_type = self.mappings['code_to_type'][slot_code]
        return slot_type