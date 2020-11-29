# Standard
from enum import Enum
import sys

# 3rd party

# Local
from ..getch import pause  # 3rd patry direct copy but in local path

BELL = chr(7)

class Device:
    USB_PID = '0000'

    def __init__(self,name):
        self._id = f'MANUAL {name}'
        self._resource = self.id
        self._inst = None
        self._vid_pid = None
        self._verbose = False
        self.emphasis = '!!'
        self.deemphasis = '!!'

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
        d = {'Manufacturer' :self.query('ENTER Manufacturer'),
             'Model'        :self.query('ENTER Model'),
             'SerialNumber' :self.query('ENTER Serial Number'),
             'Firmware'     :self.query('ENTER Firmware Version')
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

    def menu(self, enum, prefix = None):
        ''' displays an enumeration type as a menu for selection
            user enters value from list to be returned to caller
        '''
        selection = None
        if prefix is None:
            prefix = self.id
        else:
            prefix = f'{self.id} {prefix}'

        if issubclass(enum,Enum):
            values = set(e.value for e in enum)
            while True:
                print('\n')
                for e in enum:
                    print(f'{e.value} : {e}')
                try:
                    x = int(input(f'{prefix} : ENTER {enum.__name__}: '))
                    if x in values:
                        selection = enum(x)
                        if self.verbose:
                            print(f'{prefix} : SELECTED {selection}')
                        break
                except KeyboardInterrupt:
                    print('CTRL-C PRESSED: Exiting...')
                    raise KeyboardInterrupt
                except:
                    print(f'{self.emphasis} Value must be integer {self.deemphasis} {BELL}')
        else:
            raise ValueError('input must be an Enum type')

        return selection

    def query(self, prompt, res_type = str):
        retval = None
        try:
            print('\n')
            retval = input(f'{self.id} : {prompt} ({res_type.__name__}): ')
            if "" is retval:
                retval = None
            if self.verbose:
                print(f'{self.id} : ENTERED : {retval}')
        except KeyboardInterrupt:
            print('CTRL-C PRESSED: Exiting...')
            raise KeyboardInterrupt

        return retval
    
    def query_float(self, prompt):
        value = None
        while True:
            try:
                value = float(self.query(prompt,float))
                break
            except KeyboardInterrupt:
                print('CTRL-C PRESSED: Exiting...')
                raise KeyboardInterrupt
            except Exception as e:
                print(f'{self.emphasis} Value must be numeric {self.deemphasis} {BELL}')
        return value

    def query_int(self, prompt):
        value = None
        while True:
            try:
                value = int(self.query(prompt,int))
                break
            except KeyboardInterrupt:
                print('CTRL-C PRESSED: Exiting...')
                raise KeyboardInterrupt
            except Exception as e:
                print(f'{self.emphasis} Value must be integer {self.deemphasis} {BELL}')
        return value

    def command(self, prompt):
        print('\n')
        if ord(pause(f'{self.id} : {prompt}')) == 3:
            print('CTRL-C PRESSED: Exiting...')
            raise KeyboardInterrupt

    def wait_op_complete(self):
        print(f'{self.id} : WAIT OP COMPLETE HERE')

    def reset(self):
        self.command('RESET the instrument.')

    def initialize(self):
        ''' unique initialization beyond simple Device.reset(), may include call to reset()
        '''
        self.reset()

    def close(self):
        ''' formal close interface to satisfy factory. Derived updates as needed

        Implementations can include disabling, stopping, or turning off the Device
        '''
        self.command('CLOSE (disable, stop, or turn off) the instrument as needed.')
