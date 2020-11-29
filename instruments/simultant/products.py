# Rigol instruments
# Just add each specialization as needed
from .mockdmm import *
from .mockps import *
from .mockoscope import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '0000'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms =                  {   MOCKDMM.USB_PID     : MOCKDMM,
                            'MOCKDMM'           : MOCKDMM
                        }

logic_analyzers =       {
                        }

oscilloscopes =         {   MOCKOSCOPE.USB_PID  : MOCKOSCOPE,
                            'MOCKOSCOPE'        : MOCKOSCOPE
                        }

power_supplies       =  {   MOCKPS.USB_PID : MOCKPS,
                            'MOCKPS'       : MOCKPS,
                            'MOCKPS_MAIN'  : MOCKPS,
                            'MOCKPS_AUX'   : MOCKPS,
                            'MOCKPS_VAR'   : MOCKPS
                        }
