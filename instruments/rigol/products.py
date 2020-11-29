# Rigol instruments
# Just add each specialization as needed
from .ds1000z import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '1AB1'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms = {}

logic_analyzers = {}

oscilloscopes =   {     DS1000Z.USB_PID   : DS1000Z,
                        'DS1000Z'         : DS1000Z,
                        'DS1054Z'         : DS1000Z,
                        'DS1074Z Plus'    : DS1000Z,
                        'DS1104Z Plus'    : DS1000Z,
                        'DS1074Z-S Plus'  : DS1000Z,
                        'DS1104Z-S Plus'  : DS1000Z,
                        'MSO1074Z'        : DS1000Z,
                        'MSO1104Z'        : DS1000Z,
                        'MSO1074Z-S'      : DS1000Z,
                        'MSO1104Z-S'      : DS1000Z
            }

power_supplies          = {}
