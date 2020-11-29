# Rohde & Schwarz instruments
# Just add each specialization as needed
from .hmc804x import *
from .ngx200  import *

# USB Vendor ID
# There may be better sources but this one was a good start on USB Vendor IDs
# https://devicehunt.com/all-usb-vendors
USB_VID = '0AAD'

# Dictionary of product/model ID (PID) and model name to allow look up of derived Device types

dmms                    = {}

logic_analyzers         = {}

oscilloscopes           = {}

power_supplies          = { NGX200.USB_PID      : NGX200,   # Should default to mock behaviors
                            'NGX200'            : NGX200,   # Should default to mock behaviors
                            NGL201.USB_PID      : NGL201,
                            'NGL201'            : NGL201,
                            NGL202.USB_PID      : NGL202,
                            'NGL202'            : NGL202,
                            NGM201.USB_PID      : NGM201,
                            'NGM201'            : NGM201,
                            NGM202.USB_PID      : NGM202,
                            'NGM202'            : NGM202,
                            HMC804X.USB_PID     : HMC804X,  # Should default to mock behaviors
                            'HMC804X'           : HMC804X,  # Should default to mock behaviors
                            HMC8041.USB_PID     : HMC8041,
                            'HMC8041'           : HMC8041,
                            HMC8042.USB_PID     : HMC8042,
                            'HMC8042'           : HMC8042,
                            HMC8043.USB_PID     : HMC8043,
                            'HMC8043'           : HMC8043
                          }
