# Mock DMMs

# Standard

# 3rd party

# Local
from ..oscope import Oscilloscope


class MOCKOSCOPE(Oscilloscope):
    USB_PID = '4444'

    def __init__(self,*args, **kwargs):
        super(MOCKOSCOPE, self).__init__(*args, **kwargs)
