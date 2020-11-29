# Siglent instruments
# Just add each specialization as needed
from .spd3303x import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '0483'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms                    = {}

logic_analyzers         = {}

oscilloscopes           = {}

power_supplies          = { SPD3303X.USB_PID    : SPD3303X,
                            'SPD3303X'          : SPD3303X,
                            'SPD3303X-E'        : SPD3303X,
                          }
