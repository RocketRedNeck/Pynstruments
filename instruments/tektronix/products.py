# Tektronix instruments
# Just add each specialization as needed
from .mso456 import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '0699'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms = {}

logic_analyzers = {}

oscilloscopes =         {   MSO456.USB_PID      : MSO456,
                            'MSO456'            : MSO456,
                            'MSO58'             : MSO58
                        }

power_supplies     = {}
