# Standard

# 3rd party

# Local
from instruments.manual import manual


class LogicAnalyzer(manual.Device):
    USB_PID = '0000'

    def __init__(self,*args, **kwargs):
        super(LogicAnalyzer, self).__init__('LOGIC ANALYZER')
