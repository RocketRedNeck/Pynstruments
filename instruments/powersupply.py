# Standard imports
from enum import Enum

# 3rd party imports

# local imports
from .deprecate import deprecated
from .scpi import Device

# Base class for all power supplies to help guide a common API
# Each brand will be different in syntax but the core functionality will be the same
# BUT in this case the variable power supply and the fixed power suppply may have some different functions
# At least at first, Fixed and variable supplies will have the same commands available

class PowerSupply(Device):
    NUM_CHANNELS = 0
    MAX_VOLTAGE = 0.0
    MIN_CURRENT = 0.0 # Some have a value for this, usually just handle silently
    MAX_CURRENT = 0.0
    SUPPORTS_CHANNEL_COUPLING = False

    def __init__(self,*args, **kwargs):
        super(PowerSupply, self).__init__(*args, **kwargs)
        self._coupling_mode = PowerSupply.CouplingMode.INDEPENDENT
        self._measure_delay = 0.0       # In addition to standard query_delay
        self._safety_voltage = 0.0
        self._last_voltage_setpoint = 0.0
        self._last_current_setpoint = 0.0

    def initialize(self):
        ''' unique initialization beyond simple Device.reset(), may include call to reset()
        '''      
        raise NotImplementedError

    @property
    def measure_delay(self):
        return self._measure_delay

    @measure_delay.setter
    def measure_delay(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError('value must be numeric')
        if value < 0.0:
            raise ValueError('value must be > 0')
        
        self._measure_delay = value

    @property
    def safety_voltage(self):
        return self._safety_voltage
    
    @safety_voltage.setter
    def safety_voltage(self, value):
        if value < 0 or value > self.MAX_VOLTAGE:
            raise ValueError(f'safety_voltage must be between 0 and MAX_VOLTAGE ({self.MAX_VOLTAGE}) for this supply')
        self._safety_voltage = value

    @deprecated('Use volt_setpoint instead')
    def voltset(self, channel, voltage = None):
        return self.volt_setpoint(channel = channel, voltage = voltage)

    def volt_setpoint(self, channel, voltage = None):
        ''' set or return the voltage setpoint
        '''
        raise NotImplementedError

    @property
    def last_voltage_setpoint(self):
        return self._last_voltage_setpoint

    def measure_voltage(self, channel):
        raise NotImplementedError

    def stepincrement(self, channel, increment):
        raise NotImplementedError

    @deprecated('Use volt_setpoint instead')
    def stepvolts(self, channel, direction):
        self.step_volts(channel = channel, direction = direction)

    @deprecated('Use volt_setpoint instead')
    def step_volts(self, channel, direction):
        raise NotImplementedError

    @deprecated('Use set_ovp instead')
    def setovp(self, channel, voltage):
        return self.set_ovp(channel, voltage)

    def set_ovp(self, channel, voltage):
        raise NotImplementedError
        
    @deprecated('Use current_setpoint instead')
    def ampset(self, channel, amps = None):
        return self.current_setpoint(channel = channel, amps = amps)

    def current_setpoint(self, amps, channel = None):
        raise NotImplementedError

    @property
    def last_current_setpoint(self):
        return self._last_current_setpoint
        
    def measure_current(self, channel, simulated_amps = None):
        raise NotImplementedError

    # Fixed only (we may not need this, since the current setting will never be exceeded
    @deprecated('Use set_ocp instead')
    def setocp(self, channel, current):
        self.set_ocp(channel, current)

    def set_ocp(self, channel, current):
        ''' Set overcurrent protection
        '''
        raise NotImplementedError

    def measure_power(self, channel):
        raise NotImplementedError


    class CouplingMode(Enum):
        ''' CouplingMode defines how the channels will operate when output() is called
        '''
        INDEPENDENT = 0     # Each channel is controlled independently
        SERIES      = 1     # Channels are switch on/off together in serial connection
        PARALLEL    = 2     # Channels are switch on/off together in parallel connection
        EXCLUSIVE   = 3     # Only one channel allowed to be on at a time, turning on one turns off the other

    @property
    def coupling_mode(self):
        return self._coupling_mode

    @coupling_mode.setter
    def coupling_mode(self, value):
        if not isinstance(value, PowerSupply.CouplingMode):
            raise TypeError('value must be a PowerSupply.CouplingMode')

        if not self.SUPPORTS_CHANNEL_COUPLING and \
            (value is PowerSupply.CouplingMode.SERIES or value is PowerSupply.CouplingMode.PARALLEL):

            print(f'[WARNING] {self.decoded_id["Model"]} : DOES NOT SUPPORT CouplingMode = {value} Programmatically')
        else:
            self._coupling_mode = value

        if self.verbose:
            print(f'[INFO] {self.decoded_id["Model"]} : CouplingMode = {self.coupling_mode}')
        
        # Give the derived class a chance to decide if any other actions are needed
        self._set_coupling_mode(value)

    def _set_coupling_mode(self, value):
        ''' underlying function to the property for changing coupling modes
        '''
        raise NotImplementedError

    class State(Enum):
        OFF = 0
        ON  = 1

    #Will enable or disable selected channels together, for now
    @deprecated('Use output instead')
    def outenable(self, state = None, channel = None):
        self.output(channel = channel, state = state)

    def output(self, channel = None, state = None):
        ''' Switches the power supply output on and off

        channel : None (default) will switch the channels together 
        where and integer channel number will only impact the specified channel

        state : either State.OFF or State.ON or None
        
        returns the current state of each channel if state = None

        '''
        raise NotImplementedError
