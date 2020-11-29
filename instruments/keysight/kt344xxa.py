# Keysight Technologies

# Standard

# 3rd party

# Local
from ..multimeter import MultiMeter
from ..agilent.at344xxa import *

# For now, no specialization until we need it, see the Agilent definition
# Only variation expected is the product ID

class KT344XXA(AT344XXA):
    USB_PID = '0201'

    def __init__(self,*args, **kwargs):
        super(KT344XXA, self).__init__(*args, **kwargs)
