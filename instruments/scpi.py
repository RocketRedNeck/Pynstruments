# Standard imports
import ipaddress
from math import nan
import os
import platform
import time

# 3rd party imports
import pyvisa as visa

# local imports

# Keep one default resource manager for general query of real devices
scpirm =  visa.ResourceManager()

# 'alias' some functions in the resource manager for convenience
list_resources = scpirm.list_resources
open_resource = scpirm.open_resource

class Device:
    """SCPI Device Base - simplification of an already simple interface (just the minimum needed)

    :vid: Vendor ID as integer or hex-like string

    :pid: Product ID as integer or hex-like string

    :sn:  (Optional) Serial Number as string

    :ipaddr: (Optional) TCPIP address of device for alternate connections when USB not available

    :visabackend: (Optional) to change the backend from the local default, useful for simulations
    """
    def __init__(self, vid, pid, sn = None, ipaddr = None, visabackend = None, write_termination='\n', read_termination='\n', query_delay=0.1):
        self._resource = None
        self._inst = None
        self._id = None
        self._ipaddr = ipaddr
        self._verbose = False
        self._visabackend = visabackend
        self._touched = False # Used to determine if this instrument was used, right now don't care how

        self._datastorage_path = '.'  # Common default for all instruments until defined otherwise

        # Default terminators for connections
        self._write_termination = write_termination
        self._read_termination = read_termination

        # Default query delay that pyvisa uses between write and read for query
        # Will also be added after commands and at end of query to ensure that
        # all transactions are spaced (some instruments require some time between commands)
        # NOTE: If we need finer control over the timing we will work that out as needed
        # but for now a "short" delay of 100 ms (default) should be adequate for most
        self.query_delay = query_delay
    
        try:
            if self._visabackend is None:
                 self._rm = visa.ResourceManager()
            else:
                self._rm = visa.ResourceManager(self._visabackend)
        except FileNotFoundError:
            raise ConnectionError('Bad VISA Backend - Missing File')
        except Exception as e:
            raise ConnectionError(f'Bad VISA Backend {repr(e)}')

        if self._ipaddr is not None:
            ipaddress.ip_address(self._ipaddr)

        # convert vid and pid into hex strings if not already and possible
        # following will raise ValueError if the string is not hex-like or non-integer
        if isinstance(vid, str):
            vid = int(vid,16)

        if isinstance(vid, int):
            vid = '0x{:04X}'.format(vid)
        else:
            raise ValueError('vid must be hex str or int')

        if isinstance(pid, str):
            pid = int(pid,16)
        
        if isinstance(pid, int):
            pid = '0x{:04X}'.format(pid)
        else:
            raise ValueError('pid must be hex str or int')


        self._vid_pid = vid + "::" + pid
        if sn:
            if isinstance(sn, str):
                self._vid_pid += "::" + sn.upper()
            else:
                raise ValueError('sn must be a str or None')

        # If we got this far then we have something to look for our vid/pid in the resource list
        for r in self._rm.list_resources():
            if self._vid_pid in r:
                self._resource = r
                break
        
        # NOTE: If the resource was not found in the resouce list then
        # it is likely that the version PyVISA being used has not had
        # the following fixed: https://github.com/pyvisa/pyvisa-py/issues/165
        # The above issue indicated that the PyVISA does not fully implement
        # NI-VISA usage so that list_resources provides the complete list
        #
        # Our workaround is to check for an IP address passed to this Device
        if self._resource is None and self._ipaddr is not None:
            self._resource = f'TCPIP0::{self._ipaddr}::INSTR'

        if self._resource:
            try:
                # We found a matching resource attemp to open it
                # NOTE: the termination characters can be changed after if needed but
                # it is generally better to know this at construction to support
                # identification
                self._inst = self._rm.open_resource(self._resource, write_termination=self._write_termination, read_termination=self._read_termination)

                # Set up the delay between the write and read for general queries
                # Some instruments require this
                self.query_delay = self.query_delay

                # Attempt to query the ID to validate the connection
                # NOTE: The self._inst should already have the information (vendor, model, serial number, etc)
                # but this steps helps us see if there is something wrong with the connection
                # early on. Usually if the terminator or query delay is wrong then a backend timeout
                # will occur, and then we will know that either the device is just not talking or
                # we have the wrong termination and timing
                # NOTE: The instrument could be in an error state from prior connections so
                # we will attempt connection up to 3 times
                for i in range(3):
                    try:
                        self._id = self._inst.query('*IDN?').replace('\n','')   #Strip any newline so we don't have to deal with it later
                        time.sleep(self._query_delay)
                        break
                    except Exception as e:
                        if i == 2:
                            raise e
            except:
                raise ConnectionError(f'{self._resource} did not open')
        else:
            raise LookupError

    @property
    def query_delay(self):
        return self._query_delay

    @query_delay.setter
    def query_delay(self, time_sec):
        self._query_delay = time_sec
        if self._inst is not None:
            self._inst.query_delay = self._query_delay

    @property
    def datastorage_path(self):
        return self._datastorage_path
    
    @datastorage_path.setter
    def datastorage_path(self,value):
        if not os.path.exists(value):
            os.mkdir(value) # Exception raised here if invalid for some reason
        print(f'[INFO] Data Storage Path for {self.id} changed to {value}')
        self._datastorage_path = value


    def close(self):
        if self._inst is not None:
            self._inst.close()

    def verbose_print(self, cmd_ret):
        if self.verbose:
            print(f'[INFO] {self.decoded_id["Model"]}-{self.decoded_id["SerialNumber"]} : {cmd_ret}')


    @property
    def touched(self):      # Indicates that this instrument was touched during script use
        return self._touched

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, val):
        if not isinstance(val, bool):
            raise TypeError('verbose must be bool')
        self._verbose = val

    # All of the 'read-only' properties
    @property
    def resource(self):
        """ returns the underlying visa resource string
        """
        return self._resource
    
    @property
    def inst(self):
        """ returns the underlying instrumentation resource
        """
        return self._inst
        
    @property
    def id(self):
        """ returns the underlying resource ID string
        """
        return self._id

    @property
    def decoded_id(self):
        """If Device has been identified then returns a dictionary with the following elements

        Manufacturer

        Model

        SerialNumber

        Firmware
        """
        d = {'Manufacturer' :'Unknown',
             'Model'        :'Unknown',
             'SerialNumber' :'Unknown',
             'Firmware'     :'Unknown'
             }
        if self._id is not None:
            x = self._id.split(',')
            l = len(x)
            d = {   'Manufacturer' :x[0] if l > 0 else "Unknown",
                    'Model'        :x[1] if l > 1 else "Unknown",
                    'SerialNumber' :x[2] if l > 2 else "Unknown",
                    'Firmware'     :x[3] if l > 3 else "Unknown"
                }

        return d

    @property
    def vid_pid(self):
        """ returns the vendor/product ID (and optional Serial Number) string used to construct
        """
        return self._vid_pid

    def isValid(self):
        """Returns True if the Device was connected at construction
        """
        return self._id is not None

    @property
    def valid(self):
        """ True when this Device instance connected at construction or after reset
        """
        return self.isValid()

    def query_raw(self, cmd):
        """ query helper shortcut that only executes when Device is ID'd

        :retval: None if the query was unsuccessful, otherwise returns result byte string

        NOTE: string is NOT stripped of newline, feeds or return
        """
        self._touched = True
        self.verbose_print(cmd)
        if self._id:
            try:
                self._inst.write(cmd)
                time.sleep(self._query_delay)
                ret = self._inst.read_raw()
                time.sleep(self._query_delay)
                self.verbose_print(ret) 
                return ret
            except visa.VisaIOError as e:
                print(f'[WARNING] : While attempting {cmd}...\nBackend Error {e.args[0]} issuing query {cmd}')
        
        return None
        
    def query(self, cmd):
        """ query helper shortcut that only executes when Device is ID'd

        :retval: None if the query was unsuccessful, otherwise returns result string

        NOTE: string is stripped of newline, feeds or return
        """
        self._touched = True
        self.verbose_print(cmd)
        if self._id:
            try:
                ret = self._inst.query(cmd)
                time.sleep(self._query_delay)
                self.verbose_print(ret) 
                return ret.replace('\n','')
            except visa.VisaIOError as e:
                print(f'[WARNING] : While attempting {cmd}...\nBackend Error {e.args[0]} issuing query {cmd}')
        
        return None

    def query_int(self, cmd):
        """ query helper that converts response to integer when integer is expected
        """
        return self._convert2int(self.query(cmd))

    def query_float(self, cmd):
        """ query helper that converts response to float when float is expected
        """
        return self._convert2float(self.query(cmd))

    def query_binary(self,cmd):
        return self._inst.query_binary_values(cmd, datatype='B')

    def command(self, cmd):
        """ command (write) helper shortcut that only executes when Device is ID'd

        :retval: None if unsuccessful in writing command, otherwise the number of byte written
        """
        self._touched = True
        self.verbose_print(cmd)
        if self._id:
            result = self._inst.write(cmd)
            time.sleep(self._query_delay)
            return result
        
        return None

    @property
    def simulated(self):
        if self._visabackend is not None:
            return 'yaml@sim' in self._visabackend
        else:
            return False

    def reset(self, timeout_sec = 10.0):
        """ Reset the Device and reconnect

        :timeout_sec: (Default = 10.0) Timeout when waiting for reconnect

        :retval: True if reconnect was successful
        """

        # Argument must be numeric
        if not isinstance(timeout_sec, (int, float)):
            raise ValueError('timeout_sec must be non-complex numeric')

        # NOTE: We don't use the command/query shortcut here because
        # we are manipulating the self._id as part of the validation sequence
        if self._id:
            self.verbose_print('*RST')
            self._inst.write('*RST')
            time.sleep(self._query_delay)

            if timeout_sec > 0:
                # A nonzero timeout means we want to re-ID the system
                self._id = None
            starttime_sec = time.time()
            while (time.time() - starttime_sec) < timeout_sec:
                try:
                    # Resource is assumed open already but we force re-ID
                    # If the backend does not contain a yaml mock then
                    if self._visabackend is None or 'yaml@sim' not in self._visabackend:
                        self._inst = self._rm.open_resource(self._resource)

                    # Attempt to query the ID to validate the connection
                    self.verbose_print('*OPC?')
                    opc_resp = self._inst.query('*OPC?').replace('\n','')
                    time.sleep(self._query_delay)

                    self.verbose_print('*IDN?')
                    id_resp = self._inst.query('*IDN?').replace('\n','')
                    time.sleep(self._query_delay)

                    self._id = id_resp
                    break
                except Exception as e:
                    # DEBUG: print(e)
                    pass

        return self.isValid()

    def _convert2int(self, x):
        """Internal function to safely convert SCPI return strings to integer or None
        """
        if (x is not None) and isinstance(x,str):
            try:
                x = int(x)
            except:
                x = None

        return x

    def _convert2float(self, x):
        """Internal function to safely convert SCPI return strings to float or None
        """
        if (x is not None) and isinstance(x,str):
            try:
                x = float(x)
            except:
                x = nan

        return x


    def wait_op_complete(self):
        return self.query('*OPC?')

    def clear_status(self):
        """ Clear status registers in the Device (but leaves enable registers alone)

        Minimum compliance with IEEE 488.2 and SCPI are the following registers:

        SESR, OPER, QUES and the Error/Event Queue

        NOTE: forces the device into OCIS and OQIS (see 4.1.3.3 and 4.1.3.4 of SCPI 1999) 
        without setting the No Operation Pending flag TRUE and without setting the OPC bit 
        of the SESR TRUE and without placing a “1” into the Output Queue.
        This means that clearing status immediate after attempting to start an operation
        means the operation may not appear as in progress.

        :retval: Returns True if Standard Event Status Register (SESR) is 0 noting that
        reading the register also clears it

        """
        self.command('*CLS')
        oper = self.query_int('*ESR?')

        return oper == 0

    @property
    def event_status_enable(self):
        """Returns the value of the enable register for the standard event status register (SESR) set or None
        """
        return self.query_int('*ESE?')
    
    @event_status_enable.setter
    def event_status_enable(self, value):
        """Property to set or get the the enable register for the standard event status register (SESR) set 
        """

        # Make sure the input is integer-like
        if isinstance(value, str):
            try:
                value = int(value)
            except:
                try:
                    value = int(value,16)
                except:
                    raise ValueError('input must be convertable to an integer')

        if isinstance(value, int):
            self.command(f'*ESE {value}')
        else:
            raise ValueError('input must be convertable to an integer')

    @property
    def event_status(self):
        """Queries and clears the standard event status register (SESR)

        :retval: Integer value if successful, None otherwise
        """
        return self.query_int('*ESR?')

    def _decode_event_status(self, x = None):
        """ Decodes or optionally queries and decodes the event status bits into a list of strings
        """
        decoder = {15: 'Reserved15',
                   14: 'Reserved14',
                   13: 'Reserved13',
                   12: 'Reserved12',
                   11: 'Reserved11',
                   10: 'Reserved10',
                    9: 'Reserved09',
                    8: 'Reserved08',
                    7: 'PowerOn',
                    6: 'UserRequest',
                    5: 'CommandError',
                    4: 'ExecutionError',
                    3: 'DeviceError',
                    2: 'QueryError',
                    1: 'RequestControl',
                    0: 'OperationComplete'
                   }
        
        if x is None:
            x = self.event_status

        if x is not None:
            result = []
            for bit in decoder:
                if x & (1 << bit):
                    result.append(decoder[bit])
        else:
            result = ['No Status']
        
        return result

    @property
    def decode_event_status(self):
        return self._decode_event_status()

    @property
    def operation_complete(self):
        """ Returns True if the current operation is complete, False otherwise

        NOTE: An invalid connection will return False (operation in progress)
        """
        return self.query_int('*OPC?') == 1

    @operation_complete.setter
    def operation_complete(self, value):
        """ Sets the Operation Complete bit in the Standard Event Status Register (SESR) 
        after the current operation is complete.

        :value: <don't care> just needed to signify a set vs get
        """
        self.command('*OPC')

    @property
    def status_request_enable(self):
        """Returns the value of the service request enable register or None
        """
        return self.query_int('*SRE?')
    
    @status_request_enable.setter
    def status_request_enable(self, value):
        """Property to set or get the service request enable register 
        """

        # Make sure the input is integer-like
        if isinstance(value, str):
            try:
                value = int(value)
            except:
                try:
                    value = int(value,16)
                except:
                    raise ValueError('input must be convertable to an integer')

        if isinstance(value, int):
            self.command(f'*SRE {value}')
        else:
            raise ValueError('input must be convertable to an integer')
    
    @property
    def status_byte(self):
        """Queries and clears the status byte register (SBR)

        :retval: Integer value if successful, None otherwise
        """
        return self.query_int('*STB?')

    @property
    def self_test(self):
        """Initiates a self test and queries the results

        :retval: integer result or None (if no connection)
        """
        return self.query_int('*TST?')

    @property
    def wait_for_operation(self):
        """Waits for current operation to complete. Subsequent command will only be carried out after current command completes

        NOTE: Often used in concatenated command inputs, but provided here for completeness
        """
        self.command('*WAI')

    def display_file(self,filename):
        ''' display the specified file ASSUMED to be at the datastorage_path

        Uses the system default for opening a file of the specified type
 
        '''
        filename = os.path.join(self.datastorage_path,filename)

        if os.path.exists(filename):            
            if platform.system() == 'Darwin':       # macOS
                subprocess.call(('open', filename))
            elif platform.system() == 'Windows':    # Windows
                os.startfile(filename)
            else:                                   # linux variants
                subprocess.call(('xdg-open', filename))
        else:
            print(f'[WARNING] Invalid Path or Filename: Cannot open {filename}')
