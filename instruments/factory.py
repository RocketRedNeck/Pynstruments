# NOTE: NOTE: NOTE: NOTE:
# Most folks should never need to edit below this point for adding in new vendors and products

# Vendors are imported automatically as the ini-file is parsed
# So there is now no need to add them explicitly here
# Simply add the new vendor folder and a product.py module such that the following
# semantics will be valid:
#     from instruments.{vendor} import products as {vendor} 

import configparser
import sys
import os
import ipaddress

# 3rd party imports

# Local imports - Assumed to be up one directory from this module
# path_here = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(1, path_here)
#sys.path.insert(1, os.path.join(path_here,'..'))

from .tee import Tee   # For testing if there is a re-routing of console output

ini = configparser.ConfigParser()
inifile = os.path.join('.','instruments.ini')
if os.path.exists(inifile):
    ini.read(inifile)
else:
    raise FileExistsError(f'{inifile} is missing')

def getConfig(parser, section, name, default):
    retval = default
    try:
        retval = parser.get(section, name)
    except Exception as e:
        pass
    return retval

def makeConfigList(parser, section, namebase):
    i = 0
    done = False
    retlist = []
    while not done:
        x = getConfig(  parser, section, f'{namebase}{i}', None)
        if x is not None:
            retlist.append(x)
            i+=1
        else:
            break

    return retlist

# Fetch the INSTRUMENT CONFIGURATION if available

dmms_config                 = makeConfigList(ini, 'dmms',                 'id')
logic_analyzers_config      = makeConfigList(ini, 'logic_analyzers',      'id')
oscilloscopes_config        = makeConfigList(ini, 'oscilloscopes',        'id')
power_supplies_config       = makeConfigList(ini, 'power_supplies',       'id')

# For each configuration list attempt to instantiate the correct class and place in object lists

dmms                        = []
logic_analyzers             = []
oscilloscopes               = []
power_supplies              = []

def instantiate(label):
    i = 0
    config = eval(f'{label}_config')
   
    objlist = eval(f'{label}')

    for o in config:
        x = o.split('::')
        if len(x) == 5:
            vendor       = x[0]
            product      = x[1]
            serialnumber = x[2]
            ipaddr       = x[3]
            visabackend  = x[4]

            if 'NONE' == serialnumber.upper():
                serialnumber = None
            
            if 'NONE' == ipaddr.upper():
                ipaddr = None

            if 'NONE' == visabackend.upper():
                visabackend = None
            
            exec(f'from .{vendor} import products as {vendor}', globals(), locals())
            try:
                exec(f'from .{vendor} import products as {vendor}', globals(), locals())
            except ImportError:
                print(f'[{label:21s}] id{i}: {o} [ERROR] Unknown vendor "{vendor}"')
                sys.exit()

            try:
                usb_vid = eval(f'{vendor}.USB_VID')
            except NameError:
                print(f'[{label:21s}] id{i}: {o} [ERROR] Missing {vendor}.USB_VID')
                sys.exit()

            try:
                insttype = eval(f'{vendor}.{label}["{product}"]')
            except KeyError:
                print(f'[{label:21s}] id{i}: {o} [ERROR] Unknown product "{product}"')
                sys.exit()

            if ipaddr is not None:
                try:
                    iplist = ipaddr.split(':')
                    if 'localhost' not in iplist[0]:
                        ipaddress.ip_address(iplist[0])
                except ValueError as e:
                    print(f'[{label:21s}] id{i}: {o} ----> {e.args[0]}')
                    ipaddr = None

            tmp = None
            
            if isinstance(sys.stdout,Tee):
                timestamp = sys.stdout.timestamp

            try:
                print(f'[{label:21s}] id{i}: {o}: ',end='')
                if isinstance(sys.stdout,Tee):
                    sys.stdout.timestamp = False
                tmp = insttype(vid = usb_vid, pid = insttype.USB_PID, sn = serialnumber, ipaddr = ipaddr, visabackend = visabackend)
                print('<g>Found</g>')
            except LookupError:
                print('<y>NOT FOUND</y>')
            except ConnectionError as e:
                print(f'<r>NOT CONNECTED</r>: {e.args[0]}')
            except UserWarning as e:
                print(f'<y>IGNORED</y>: {e.args[0]}')

            if isinstance(sys.stdout,Tee):
                sys.stdout.timestamp = timestamp

            if tmp is not None:
                objlist.append(tmp)
 
            i += 1
        else:
            raise SyntaxWarning(f'[{label}] id{i}: "{o}" must be 5 parts: vendor::product::serialnumber::ipaddr::visabackend')

instantiate('dmms')
instantiate('logic_analyzers')
instantiate('oscilloscopes')
instantiate('power_supplies')

# Find first valid instrument of each type
# for convenience
dmm = None
logic_analyzer = None
oscilloscope = None
power_supply = None

# Find first as primary instrument (convenience for users)
for i in dmms:
    if i is not None:
        dmm = i
        break

for i in logic_analyzers:
    if i is not None:
        logic_analyzer = i
        break

for i in oscilloscopes:
    if i is not None:
        oscilloscope = i
        break

for i in power_supplies:
    if i is not None:
        power_supply = i
        break

def close():
    for i in dmms:
        if i is not None:
            print(f'Close DMM: {i.id}')
            i.close()
    for i in logic_analyzers:
        if i is not None:
            print(f'Close LOGIC ANALYZER: {i.id}')
            i.close()
    for i in oscilloscopes:
        if i is not None:
            print(f'Close OSCOPE: {i.id}')
            i.close()
    for i in power_supplies:
        if i is not None:
            print(f'Close POWER SUPPLY: {i.id}')
            i.close()

