# Mock DMMs

# Standard

# 3rd party

# Local
from ..powersupply import PowerSupply


class MOCKPS(PowerSupply):
    USB_PID = '3333'

    def __init__(self,*args, **kwargs):
        super(MOCKPS, self).__init__(*args, **kwargs)
