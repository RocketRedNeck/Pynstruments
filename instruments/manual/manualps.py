# Standard
from enum import Enum

# 3rd party

# Local
from instruments.manual import manual

class PowerSupply(manual.Device):
    USB_PID = '0000'

    def __init__(self,*args, **kwargs):
        super(PowerSupply,self).__init__('POWER SUPPLY')

    def voltset(self, channel, voltage):
        self.command(f'SET Channel {channel} Voltage to {voltage} Volts.')
        self.voltage = voltage

    def stepincrement(self, channel, increment):
        self.command(f'SET Channel {channel} Voltage INCREMENT to {increment} Volts.')
        self.increment = increment

    def stepvolts(self, channel, direction):
        if (direction != 'UP') and (direction != 'DOWN'):
            raise ValueError (f'{self.id} : direction must be "UP or "DOWN"')

        self.command(f'STEP Channel {channel} Voltage {direction} by {self.increment} Volts.')
        if 'UP' in direction:
            self.voltage += self.increment
        else:
            self.voltage -= self.increment

    def setovp(self, channel, voltage):
        self.command(f'SET Channel {channel} OVER VOLT PROTECTION to {voltage} Volts.')
        
    def ampset(self, channel, amps):
        self.command(f'SET Channel {channel} current to {amps} Amp.')

    # Fixed only (we may not need this, since the current setting will never be exceeded
    def setocp(self, channel, current):
        self.command(f'SET Channel {channel} OVER CURRENT PROTECTION to {current} Amp.')

    class State(Enum):
        OFF = 0
        ON  = 1

    #Will enable or disable selected channels together, for now
    def outenable(self, state = State.OFF):
        self.command(f'SET Output to {state}.')

    # Override default close
    def close(self):
        self.outenable(self.State.OFF)
