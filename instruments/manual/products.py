# Manual instruments
# Just add each specialization as needed
from .manualdmm import *
from .manualla import *
from .manualps import *
from .manualoscope import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '0000'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms =                  {   MultiMeter.USB_PID     : MultiMeter,
                            'MultiMeter'           : MultiMeter
                        }

logic_analyzers =       {   LogicAnalyzer.USB_PID      : LogicAnalyzer,
                            'LogicAnalyzer'            : LogicAnalyzer
                        }

oscilloscopes =         {   Oscilloscope.USB_PID  : Oscilloscope,
                            'Oscilloscope'        : Oscilloscope
                        }

power_supplies =        {   PowerSupply.USB_PID : PowerSupply,
                            'PowerSupply'       : PowerSupply,
                            'MainPowerSupply'   : PowerSupply,
                            'AuxPowerSupply'    : PowerSupply,
                            'VarPowerSupply'    : PowerSupply
                        }
