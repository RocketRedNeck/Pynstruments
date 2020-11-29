# Saleae Instruments
# Just add each specialization as needed
from .logic import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '21A9'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms                    = {}

logic_analyzers         = {Logic4.USB_PID       : Logic4,
                           'Logic4'             : Logic4,
                            Logic8.USB_PID      : Logic8,
                           'Logic8'             : LogicPro8,
                           LogicPro8.USB_PID    : LogicPro8,
                           'LogicPro8'          : LogicPro8,
                           LogicPro16.USB_PID   : LogicPro16,
                           'LogicPro16'         : LogicPro16                           
                          }

oscilloscopes           = {}

power_supplies          = {}
