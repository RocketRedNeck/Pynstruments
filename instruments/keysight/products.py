# Keysight instruments
# Just add each specialization as needed
from .kt344xxa import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '2A8D'    # Rebranding from Agilent and HP

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms                    = { KT344XXA.USB_PID        : KT344XXA,
                            '34460A'                : KT344XXA,
                            '34471A'                : KT344XXA,
                            '34465A'                : KT344XXA,
                            '34470A'                : KT344XXA,
                          }

logic_analyzers         = {}

oscilloscopes           = {}

power_supplies          = {}
