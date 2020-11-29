# Standard imports
from enum import Enum
import time

# 3rd party imports

# local imports
from .deprecate import deprecated
from .scpi import Device

# Base class for all multimeters to help guide a common API
# Each brand will be different in syntax but the core functionality will be the same

class MultiMeter(Device):
    def __init__(self,*args, **kwargs):
        super(MultiMeter, self).__init__(*args, **kwargs)
        self._settling_delay_sec = 0.1
    
    @property
    def settling_delay_sec(self):
        return self._settling_delay_sec
    
    @settling_delay_sec.setter
    def settling_delay_sec(self,delay):
        if not isinstance(delay,(int,float)):
            raise TypeError('Delay Must be Numeric')
        self._settling_delay_sec = delay

    class Mode(Enum):
        DC_VOLT    = 0
        DC_AMP     = 1
        AC_VOLT    = 2
        AC_AMP     = 3
        RESISTANCE = 4
        FREQUENCY  = 5
        PERIOD     = 6

    @deprecated('Use set_mode_range')
    def moderangeset(self, range, mode):
        self.set_mode_range(range = range, mode = mode)

    def set_mode_range(self, range, mode):
        ''' sets the mode and range of the multimeter

        range : the upper limit for the specified mode

        mode : the operating mode based on MultiMeter.Mode
        ''' 
        raise NotImplementedError

    def get_mode_range(self):
        ''' returns current settings (mode and range) of the multimeter
        ''' 
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def read_until(self,value,tolerance): 
        ''' Reads until measurement is value within tolerance 
            or timeout as defined by settling delay

            Returns True if value is withing tolerance before settling delay
        '''  
        start = time.perf_counter()
        while not ((value - tolerance) <= self.read() <= (value + tolerance)) and (time.perf_counter() - start <= self.settling_delay_sec):
            pass
        return  ((value - tolerance) <= self.read() <= (value + tolerance))
