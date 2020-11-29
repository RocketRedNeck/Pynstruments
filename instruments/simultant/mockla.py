# Mock DMMs

# Standard

# 3rd party

# Local
from ..analyzer import Analyzer


class MOCKANALYZER(Analyzer):
    USB_PID = '1111'

    def __init__(self,*args, **kwargs):
        super(MOCKANALYZER, self).__init__(*args, **kwargs)
