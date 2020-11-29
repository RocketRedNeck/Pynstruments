# Mock DMMs

# Standard
from enum import Enum

# 3rd party

# Local
from instruments.manual import manual


class MultiMeter(manual.Device):
    USB_PID = '0000'

    class Mode(Enum):   # Duplicates MultiMeter for the moment
        DC_VOLT    = 0
        DC_AMP     = 1
        AC_VOLT    = 2
        AC_AMP     = 3
        RESISTANCE = 4
        FREQUENCY  = 5
        PERIOD     = 6

    def __init__(self,*args, **kwargs):
        super(MultiMeter, self).__init__('DMM')

    def moderangeset(self, dmmrange = None, mode = None):
        if dmmrange is None or mode is None:
            mode = self.menu(self.Mode)
            dmmrange = self.query(f'ENTER Current Range Setting: ')
            return dmmrange, mode

        if not isinstance(mode, self.Mode):
            raise ValueError('mode out of range')
            
        self.command(f'SET Mode to {mode}')
        self.command(f'SET Range to {dmmrange}')
                     
    def read(self):
        return self.query_float('ENTER Value on Display')
