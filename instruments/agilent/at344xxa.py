# Agilent Technologies

# Standard

# 3rd party

# Local
from ..multimeter import MultiMeter

voltage_valid_range = {0.2, 1.0, 10.0, 100.0, 1000.0, "AUTO", "MIN", "MAX", "DEFAULT"}
current_valid_range = {0.0001, 0.001, 0.01, 0.1, 1.0, 3.0, 10.0, "AUTO", "MIN", "MAX", "DEFAULT"}
resistance_valid_range = {100, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000, "AUTO", "MIN", "MAX", "DEFAULT"}  
freq_per_enums = {"MIN", "MAX", "DEF"}

# For interpretation of CONFigure? responses which always return the short form
modedict = {None : None,
           "VOLT" : MultiMeter.Mode.DC_VOLT,
           "VOLT:DC" : MultiMeter.Mode.DC_VOLT,
           "VOLT:AC" : MultiMeter.Mode.AC_VOLT,
           "CURR"    : MultiMeter.Mode.DC_AMP,
           "CURR:DC" : MultiMeter.Mode.DC_AMP,
           "CURR:AC" : MultiMeter.Mode.AC_AMP,
           "RES"     : MultiMeter.Mode.RESISTANCE,
           "FRES"    : MultiMeter.Mode.RESISTANCE,  # Don't really support 4-wire resistance
           "FREQ"    : MultiMeter.Mode.FREQUENCY,
           "PER"     : MultiMeter.Mode.PERIOD
           }

class AT344XXA(MultiMeter):
    USB_PID = '0000'

    def __init__(self,*args, **kwargs):
        super(AT344XXA, self).__init__(*args, **kwargs)

    def set_mode_range(self, range, mode):

        if not isinstance(mode, self.Mode):
            raise ValueError('mode out of range')
            
        if self.Mode.DC_VOLT == mode:
            if (range in voltage_valid_range):
                self.command(f'CONFigure:VOLTage:DC {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('volts range out of range')


        elif self.Mode.AC_VOLT == mode:
            if (range in voltage_valid_range):
                self.command(f'CONFigure:VOLTage:AC {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('volts range out of range')

        elif self.Mode.DC_AMP == mode:
            if (range in current_valid_range):
                self.command(f'CONFigure:CURRent:DC {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('current range out of range')

        elif self.Mode.AC_AMP == mode:
            if (range in current_valid_range):
                self.command(f'CONFigure:CURRent:AC {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('current range out of range')
                
        elif self.Mode.RESISTANCE == mode:
            if (range in resistance_valid_range):
                self.command(f'CONFigure:RESistance {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('resistance range out of range')

        elif self.Mode.FREQUENCY == mode:
            if (range in freq_per_enums) or ((int(range) >= 3 ) and (int(range) <=  300000)):
                self.command(f'CONFigure:FREquency {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('frequency range out of range')
                     
        elif self.Mode.PERIOD == mode:
            if (range in freq_per_enums) or ((float(range) >= 0.00000333) and (float(range) <= 0.33333)):
                self.command(f'CONFigure:PERiod {range}')
                self.command('TRIGger:SOURce:IMMediate')
            else:
                raise ValueError('period range out of range')

    def get_mode_range(self):
        # This device returns mode, range, and resolution in a single response that needs to be parsed
        # Resolution is usually fixed by this device model so is generally ignored even on command option
        str = self.query('CONFigure?')
        vals = str.split(' ')
        ret_mode = modedict[vals[0].replace('"','')]

        ret_range = vals[1].split(',')[0]
        try:
            ret_range = float(ret_range)
        except ValueError:
            # A nonnumeric string like "AUTO", "MIN", "MAX", or "DEFAULT" was returned
            pass

        return ret_mode, ret_range

    def read(self):
        return self.query_float('READ?')

#Next one is for using pyvisasim for test    
    def setcurrent(self, current):
        self.query(f'READ! {current}')
