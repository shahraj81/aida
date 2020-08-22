"""
Slots used to map between LDC's internal code for a slot, and its corresponding external slot name.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.2"
__date__    = "26 December 2019"

from aida.container import Container
from aida.object import Object
from aida.file_handler import FileHandler

class SlotMappings(Object):
    """
    Slots used to map between LDC's internal code for a slot, and its corresponding external slot name.
    """
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
        self.mappings = {
            'code_to_type': Container(logger),
            'type_to_codes': Container(logger)
            }
        # load the data and store the mapping in a dictionary
        for entry in FileHandler(logger, filename):
            slot_type_code = entry.get('slot_type_code')
            slot_type = entry.get('slot_type')
            if slot_type_code in self.get('mappings').get('code_to_type'):
                logger.record_event('DUPLICATE_VALUE_IN_COLUMN', slot_type_code, 'slot_type_code', entry.get('where'))
            self.get('mappings').get('code_to_type').add(key=slot_type_code, value=slot_type)
            self.get('mappings').get('type_to_codes').get(slot_type, default=Container(logger)).add(key=slot_type_code, value=slot_type_code)

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
        if slot_type in self.get('mappings').get('type_to_codes'):
            slot_codes = list(self.get('mappings').get('type_to_codes').get(slot_type).values())
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
        if slot_code in self.get('mappings').get('code_to_type'):
            slot_type = self.get('mappings').get('code_to_type').get(slot_code)
        return slot_type