# Rohde & Schwarz Adjustable Power Supply

# Standard
import numpy as np
import time

# 3rd party

# Local
from ..powersupply import PowerSupply
from ..deprecate import deprecated
from ..freeze_it import freeze_it

coupledict = {  PowerSupply.CouplingMode.INDEPENDENT    : 0,
                PowerSupply.CouplingMode.SERIES         : 1,
                PowerSupply.CouplingMode.PARALLEL       : 2,
                PowerSupply.CouplingMode.EXCLUSIVE      : 0
             }

@freeze_it
class SPD3303X(PowerSupply):
    USB_PID = '7540'
    NUM_CHANNELS = 2
    MEASURE_DELAY = 0.2
    MAX_VOLTAGE = 32.0
    MAX_CURRENT = 3.2
    SUPPORTS_CHANNEL_COUPLING = True

    def __init__(self,*args, **kwargs):
        super(SPD3303X, self).__init__(*args, **kwargs)

        # This instrument is missing some query forms
        # so we have to retain information in the class
        self.state = self.NUM_CHANNELS*[self.State.OFF]
        self.step = 0.0

    def _set_coupling_mode(self, value):
        ''' underlying function to the property for changing coupling modes

        This function should not be called b the user directly since it would
        cause an internal mismatch of the coupling_mode internals
        '''
        self.command(f'OUTPut:TRACK {coupledict[value]}')

    def initialize(self):
        """ unique initialization beyond simple Device.reset(), may include call to reset()
        """

        # NOTE: This device does not support reset

        self.coupling_mode = self.CouplingMode.INDEPENDENT
        self.output(state = self.State.OFF)

        for i in range(self.NUM_CHANNELS):
            self.volt_setpoint(i+1,0.0)
            self.current_setpoint(i+1,0.0)

    def close(self):
        self.initialize()
        PowerSupply.close(self)
        
    def volt_setpoint(self, channel, voltage = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        if voltage is None:
            return self.query_float(f'CH{channel}:VOLTage?')

        if not isinstance(voltage, (int, float)):
            raise TypeError('voltage must be numeric value')

        if (voltage < 0) or (voltage > self.safety_voltage):
            raise ValueError(f'voltage out of range: must be between 0 and safety_voltage {self.safety_voltage}')

        self.command(f'CH{channel}:VOLTage {voltage}')      # Sets the voltage
        self._last_voltage_setpoint = voltage

        return self.last_voltage_setpoint

    def measure_voltage(self, channel):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')
        
        # Always delay measurement to ensure accuracy
        time.sleep(self.MEASURE_DELAY)
        return self.query_float(f'MEASure:VOLTage? CH{channel}')


    def step_increment(self, channel, increment = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        self.command(f'INSTrument CH{channel}')   # Selects the channel

        if increment is None:
            return self.step

        if not isinstance(increment, (int, float)):
            raise TypeError('increment must be numeric value')

        # Arbitrary range for us right now
        if (increment < 0.001) or (increment > 5):
            raise ValueError('increment out of range')

        self.step = increment

    def step_volts(self, channel, direction):
        
        if (direction != 'UP') and (direction != 'DOWN'):
            raise ValueError ('direction out of range')

        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        # Query then set
        step = self.step if direction=='UP' else -self.step
        self.voltset(channel, self.voltset(channel) + step)
 
    def set_ovp(self, channel, voltage):
        raise NotImplementedError
        
    def current_setpoint(self, channel, amps = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        if amps is None:
            return self.query_float(f'CH{channel}:CURRent?')

        if not isinstance(amps, (int, float)):
            raise TypeError('voltage must be numeric value')

        if (amps < 0.00) or (amps > self.MAX_CURRENT):
            raise ValueError(f'amps out of range: must be 0.0 through {self.MAX_CURRENT}')

        self.command(f'CH{channel}:CURRent {amps}')      # Sets the amperage
        self._last_current_setpoint

        return self.last_current_setpoint
        
    def measure_current(self, channel, simulated_amps = None):
        if simulated_amps is not None:
            if self.simulated:
                if not isinstance(simulated_amps, (int, float)):
                    raise TypeError('simulated_amps must be numeric value')
                self.command(f'MEASure:CURRent! {simulated_amps:.2f}')
            else:
                print('[WARNING] attempt to set simulated current measurement in non-simulated state')
        else:
            if not isinstance(channel, int):
                raise TypeError('channel must an integer type')
                
            if channel not in range(1,self.NUM_CHANNELS+1):
                raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')
            
            # Always delay measurement to ensure accuracy
            time.sleep(self.MEASURE_DELAY)
            return self.query_float(f'MEASure:CURRent? CH{channel}')

    # Fixed only (we may not need this, since the current setting will never be exceeded
    def set_ocp(self, channel, current):
        raise NotImplementedError

    def measure_power(self, channel):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        time.sleep(self.MEASURE_DELAY)
        return self.query_float(f'MEASure:POWEr? CH{channel}')
    
    def output(self, channel = None, state = None):
        if channel is None:
            channel = list(range(1, self.NUM_CHANNELS+1))
        
        if not isinstance(channel, (list,tuple)):
            if not isinstance(channel, int):
                raise TypeError('channel must an integer type or a list/tuple of integer type')
            else:
                channel = [channel]
        
        for c in channel:
            if not isinstance(c, int):
                raise TypeError('channel must an integer type')
            
            if c not in range(1,self.NUM_CHANNELS+1):
                raise ValueError (f'channel {c} out of range: must be 1 through {self.NUM_CHANNELS}')

        if state is None:
            return self.state

        if not isinstance(state, (list,tuple)):
            if not isinstance(state, PowerSupply.State):
                raise TypeError('state must be type PowerSupply.State containing ON/OFF values')
            else:
                state = [state]

        # Arbitrate state based on coupling mode
        if len(state) > 1 and len(state) != len(channel):
            raise ValueError('Number of states must be 1 or same length as channel')
        
        state = len(channel)*state

        # Sort the state and channel information by channel to ensure the order
        # not ambiguous
        idx = list(np.argsort(channel))
        channel = [channel[i] for i in idx]
        state = [state[i] for i in idx]

        if self.coupling_mode is self.CouplingMode.SERIES or self.coupling_mode is self.CouplingMode.PARALLEL:
            # All states must be the same
            if not (state[1:] == state[:-1]):
                raise ValueError('states for SERIES or PARALLEL coupling must be same for all channels (pass single not list/tuple)')
        
        if self.coupling_mode is self.CouplingMode.EXCLUSIVE:
            # Only one channel can be ON at a time
            # Make sure only one channel was passed in
            if len(channel) > 1:
                raise ValueError('only one channel should be passed in EXCLUSIVE coupling')

            # if the state being command is ON then we can do something, otherwise just move on
            # since commanding OFF in an exclusive state does not mean anything to the other
            # channel states

            if state[0] is self.State.ON:
                # If the current channel is commanded on, make sure the others are commanded off, first
                for c in range(1, self.NUM_CHANNELS+1):
                    if c != channel[0]:
                        self.command(f'OUTPut CH{c},OFF')
                        self.state[c-1] = self.State.OFF

        # Retain state since this device does not have a query form
        i = 0
        for c in channel:
            self.state[c-1] = state[i]
            if c == 1 or (c > 1 and not (self.coupling_mode is self.CouplingMode.SERIES or self.coupling_mode is self.CouplingMode.PARALLEL)):
                # Use only channel 1 in series and parallel modes
                self.command(f'OUTPut CH{c},{"ON" if self.state[c-1]==self.State.ON else "OFF"}')
            i += 1
