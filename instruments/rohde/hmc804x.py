# Rohde & Schwarz Adjustable Power Supply

# Standard
import math
import numpy as np
import time

# 3rd party

# Local
from ..powersupply import PowerSupply

outputdict = { None                     : None,
               "OFF"                    : PowerSupply.State.OFF,
               "0"                      : PowerSupply.State.OFF,
               PowerSupply.State.OFF    : "OFF",
               "ON"                     : PowerSupply.State.ON,
               "1"                      : PowerSupply.State.ON,
               PowerSupply.State.ON     : "ON"}

class HMC804X(PowerSupply):
    USB_PID = '0002'     # Fake ID for mocking, see derived classes for real IDs
    NUM_CHANNELS = 1     # Assume minimum channels generically
    MAX_VOLTAGE = 32.05
    MIN_CURRENT = 0.005  # Unique to this device, will be silent about it
    MAX_CURRENT = 3.0    # Assume minimum current generically

    def __init__(self,*args, **kwargs):
        super(HMC804X, self).__init__(*args, **kwargs)

        self.measure_delay = 0.25    # Emprically found, can be adjusted later as needed
        self.state = self.NUM_CHANNELS*[self.State.OFF] # Used for debug and other validation even with device query form

    def _set_coupling_mode(self, value):
        ''' underlying function to the property for changing coupling modes

        This function should not be called b the user directly since it would
        cause an internal mismatch of the coupling_mode internals
        '''

        # NOTE: This power supply does not provide anything other than independent channels
        # Serial and Parallel modes will result no change to the coupling mode
        # We have a couple of options
        #   1) move on since the warning was issued by the base class
        #   2) consider raising an exception

        # For now we choose option 1 and can consider a switcable exception state
        # using the following commented out code
        # if value is not self.coupling_mode:
        #     raise ValueError('This power supply does not support SERIES or PARALLEL coupling (use a different power supply')

    def initialize(self):
        """ unique initialization beyond simple Device.reset(), may include call to reset()
        """        
        self.reset(timeout_sec = 0.0)   # Don't wait i.e., don't attempt re-id

        self.coupling_mode = self.CouplingMode.INDEPENDENT
        self.output(state = self.State.OFF)

        for i in range(self.NUM_CHANNELS):
            self.volt_setpoint(i+1,0.0)
            self.current_setpoint(i+1,0.0)
        
    def volt_setpoint(self, channel, voltage = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        self.command(f'INSTrument OUT{channel}')   # Selects the channel

        if voltage == None:
            return self.query_float(f'VOLTage?')

        if not isinstance(voltage, (int, float)):
            raise TypeError('voltage must be numeric value')

        if (voltage < 0) or (voltage > self.safety_voltage):
            raise ValueError(f'voltage out of range: must be between 0 and safety_voltage {self.safety_voltage}')

        self.command(f'VOLTage {voltage}')      # Sets the voltage
        self._last_voltage_setpoint = voltage

        # Check current setpoint and note any device changes
        current_setpoint = self.current_setpoint(channel = channel)
        if self.last_current_setpoint > current_setpoint:
            self._last_current_setpoint = current_setpoint
            print(f'[WARNING] Current setpoint was automatically adjusted to {current_setpoint} A by device')

        return self.last_voltage_setpoint

    def measure_voltage(self, channel):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')
        
        # Always delay measurement transaction by an additional amount to give device time to settle
        # This can be reduced or in combination with the standard query delay
        time.sleep(self.measure_delay)
        self.command(f'INSTrument OUT{channel}')   # Selects the channel
        v = self.query_float(f'MEASure:VOLTage?')   # Check for NaN (which means disabled on this PS) 
        return 0.0 if math.isnan(v) else v

    def step_increment(self, channel, increment : None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        self.command(f'INSTrument OUT{channel}')   # Selects the channel

        if increment == None:
            return self.query(f'VOLTage:STEP?')

        if not isinstance(increment, (int, float)):
            raise TypeError('increment must be numeric value')

        if (increment < 0.001) or (increment > 5):
            raise ValueError('increment out of range')

        self.command(f'VOLTage:STEP {increment}')      # Sets the increment

    def step_volts(self, channel, direction):
        
        if (direction != 'UP') and (direction != 'DOWN'):
            raise ValueError ('direction out of range')

        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        self.command(f'INSTrument OUT{channel}')
        self.command(f'VOLTage {direction}')
 
    def set_ovp(self, channel, voltage):
        raise NotImplementedError
        
    def current_setpoint(self, channel, amps = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')

        self.command(f'INSTrument OUT{channel}')   # Selects the channel

        if amps == None:
            return self.query_float(f'CURRent?')

        if not isinstance(amps, (int, float)):
            raise TypeError('current must be numeric value')

        if (amps < 0.00) or (amps > self.MAX_CURRENT):
            raise ValueError(f'amps out of range: must be 0.0 through {self.MAX_CURRENT}')

        if amps < self.MIN_CURRENT:
            amps = self.MIN_CURRENT

        self.command(f'CURRent {amps}')      # Sets the amperage
        self._last_current_setpoint = amps

        current_setpoint = self.query_float(f'CURRent?')
        if self._last_current_setpoint > current_setpoint:
            self._last_current_setpoint = current_setpoint
            print(f'[WARNING] Current setpoint was automatically adjusted to {current_setpoint} A by device')

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
            
            # Always delay measurement transaction by an additional amount to give device time to settle
            # This can be reduced or in combination with the standard query delay
            time.sleep(self.measure_delay)
            self.command(f'INSTrument OUT{channel}')   # Selects the channel
            v = self.query_float(f'MEASure:CURRent?')   # Check for NaN (which means disabled on this PS) 
            return 0.0 if math.isnan(v) else v
    
    # Fixed only (we may not need this, since the current setting will never be exceeded
    def set_ocp(self, channel, current):
        raise NotImplementedError

    def measure_power(self, channel):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
            
        if channel not in range(1,self.NUM_CHANNELS+1):
            raise ValueError (f'channel {channel} out of range: must be 1 through {self.NUM_CHANNELS}')
        
        # Always delay measurement transaction by an additional amount to give device time to settle
        # This can be reduced or in combination with the standard query delay
        time.sleep(self.measure_delay)
        self.command(f'INSTrument OUT{channel}')   # Selects the channel
        v = self.query_float(f'MEASure:POWer?')   # Check for NaN (which means disabled on this PS) 
        return 0.0 if math.isnan(v) else v

    def output(self, channel = None, state = None):
        # NOTE: the internal self.state keeps track of the activations not the actual output
        # state; even through the device supports a direct query of the states (channel and general)
        # we retain this soft state for debug purposes

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
            # This device has a query for state but includes dual states in interface (activation and general output)
            # I.e., a channel can be active, but if general output is off then the state here is OFF
            # And a deactivated channel with general output ON is also OFF
            general_state = outputdict(self.query(f'OUTput:General?'))
            for c in range(1, self.NUM_CHANNELS+1):
                # Use this opportunity to refresh the internal state
                self.command(f'INSTrument OUT{c}')
                self.state[c-1] = outputdict(self.query(f'OUTPut:SELect?'))

            # If the general state and the individual channels disagree then issue a warning to be investigated later
            # This could occur if a user touches the buttons manually while scripts are running
            if (self.state[0] is PowerSupply.State.OFF) and (self.state[1:] == self.state[:-1]):  # all channels off
                if general_state is PowerSupply.State.ON:
                    print('[WARNING] General State is ON but all channels appear deactivated (suspect buttons have been manually changed)')
            elif general_state is PowerSupply.State.OFF: # Some channel on
                    print('[WARNING] General State is OFF but some channels are Active (suspect buttons have been manually changed)')

            # Regardless, return the current state based on activations
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


        # Arbitrate the exclusive mode first
        if self.coupling_mode is self.CouplingMode.EXCLUSIVE:
            # Only one channel can be ON at a time
            # Make sure only one channel was passed in
            if len(channel) > 1:
                raise ValueError('only one channel should be passed in EXCLUSIVE coupling')

            # if the state being command is ON then we can do something, otherwise just move on
            # since commanding OFF in an exclusive state does not mean anything to the other
            # channel states

            if state[0] is self.State.ON:
                # If the current channel is commanded on, make sure the others are deactivated first
                for c in range(1, self.NUM_CHANNELS+1):
                    if c != channel[0]:
                        self.command(f'INSTrument OUT{c}')
                        self.command(f'OUTPut:CHANnel OFF')
                        self.state[c-1] = self.State.OFF

        # Activate or deactivate as needed (NOTE: the GENeral output will turn power on or off
        # based on activation)
        # Retain state (mainly for debug purposes since this device has a state query form)
        i = 0
        for c in channel:
            self.state[c-1] = state[i]
            self.command(f'INSTrument OUT{c}')
            self.command(f'OUTPut:CHANnel {"ON" if self.state[c-1]==self.State.ON else "OFF"}')
            i += 1

        # If all of the selected states are off then disable the general output
        # Otherwise, switch the channels on (potentially at the same time if both are active)
        if (self.state[0] is PowerSupply.State.OFF) and (self.state[1:] == self.state[:-1]):
            # Everything is OFF, just turn off the general output too
            self.command('OUTPut:MASTer:STATe OFF')
        else:
            # At least one channel is active, enable the output
            self.command('OUTPut:MASTer:STATe ON')   

class HMC8041(HMC804X):
    USB_PID = '0002'        # Mock until real ID is found
    NUM_CHANNELS = 1
    MAX_CURRENT = 10.0

    def __init__(self,*args, **kwargs):
        super(HMC8041, self).__init__(*args, **kwargs)

class HMC8042(HMC804X):
    USB_PID = '0135'
    NUM_CHANNELS = 2
    MAX_CURRENT = 5.0

    def __init__(self,*args, **kwargs):
        super(HMC8042, self).__init__(*args, **kwargs)

class HMC8043(HMC804X):
    USB_PID = '0002'        # Mock until real ID is found  
    NUM_CHANNELS = 3
    MAX_CURRENT = 3.0

    def __init__(self,*args, **kwargs):
        super(HMC8043, self).__init__(*args, **kwargs)
