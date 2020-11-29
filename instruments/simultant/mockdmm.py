# Mock DMMs

# Standard

# 3rd party

# Local
from ..multimeter import MultiMeter


class MOCKDMM(MultiMeter):
    USB_PID = '1111'

    def __init__(self,*args, **kwargs):
        super(MOCKDMM, self).__init__(*args, **kwargs)

    def moderangeset(self, range = None, mode = None):
        if range is None or mode is None:
            return "Insert Response Here"

        if not isinstance(mode, self.Mode):
            raise ValueError('mode out of range')
            
    def read(self):
        return self.query_float('VOLT?')
