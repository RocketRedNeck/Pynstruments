# Agilent instruments
# Just add each specialization as needed
from .at344xxa import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '0957'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms                    = { AT344XXA.USB_PID        : AT344XXA,
                            'AT34460A'              : AT344XXA,
                            'AT34471A'              : AT344XXA,
                            'AT34465A'              : AT344XXA,
                            'AT34470A'              : AT344XXA,
                          }

logic_analyzers         = {}

oscilloscopes           = {}

power_supplies          = {}
