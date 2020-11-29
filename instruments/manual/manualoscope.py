# Standard
from enum import Enum
import time

# 3rd party

# Local
from instruments.manual import manual


class Oscilloscope(manual.Device):
    USB_PID = '0000'

    NUM_ANA_CHAN = 8
    NUM_DIG_CHAN = 0
    NUM_SIG_CHAN = 0
    MAX_DATA_POINTS = 0

    def __init__(self,*args, **kwargs):
        super(Oscilloscope, self).__init__('OSCILLOSCOPE')

    class DisplayState(Enum):
        OFF   = 0
        ON    = 1

    def display(self, channel, state = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if state is not None and not isinstance(state, self.DisplayState):
            raise TypeError('state must be a DisplayState')

        if state is None:
            return self.menu(enum = self.DisplayState, prefix = f'Channel {channel}')
        else:
            self.command(f'SET Channel {channel} to {state}')        

    class Units(Enum):
        UNKNOWN = 0
        VOLT    = 1
        WATT    = 2
        AMP     = 3


    def units(self, channel, unit = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if unit is not None and not isinstance(unit, self.Units):
            raise TypeError('unit must be a Units')

        if unit is None:
            return menu(enum = self.Units, prefix = f'Channel {channel}')
        else:
            self.command(f'SET Channel {channel} to {unit}') 

    def hscale(self, hdiv_sec = None):
        if hdiv_sec is not None:
            if not isinstance(hdiv_sec, (int, float)):
                raise TypeError('hdiv_sec must be numeric value')

            self.command(f'SET Horizontal Scale to {hdiv_sec} sec/div') 
        else:
            return self.query_float('ENTER Horizontal Scale (sec/div)')

    def hpos(self, offset_sec = None):
        """ Align trigger on display (> 0 is right of center, < 0 is left of center)
        """
        if offset_sec is not None:
            if not isinstance(offset_sec, (int, float)):
                raise TypeError('delay_sec must be numeric value')

            self.command(f'SET Horizontal Offset of Trigger {-offset_sec} sec {"LEFT" if offset_sec < 0 else "RIGHT"} of center')
        else:
            return self.query_float('ENTER Current Horizontal Offset of Trigger (seconds)')

    def probescale(self, channel, nx = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
        
        if nx is not None:
            if not isinstance(nx, (int, float)):
                raise TypeError('nx must be numeric scale for probe: e.g, 0.1, 1, 10, etc')

            self.command(f'SET Channel {channel} Probe Scale to {nx}x')
        else:
            return self.query_float(f'ENTER Current Channel {channel} Probe Scale')

    def vscale(self, channel, vdiv = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if vdiv is not None:
            if not isinstance(vdiv, (int, float)):
                raise TypeError('vdiv must be numeric value')

            self.command(f'SET Channel {channel} Vertical Scale to {vdiv} /div')
        else:
            return self.query_float(f'ENTER Channel {channel} Veritical Scale (per div)')

    def trigger_status(self):
        return self.query('ENTER Current Trigger Status (e.g., ARMED, TRIGGERED, etc)')

    def trigger_holdoff(self, time_sec = None):
        if not isinstance(time_sec, (int, float)):
            raise TypeError('time_sec must be numeric value')

        if time_sec is None:
            return self.query_float('ENTER Current Trigger Holdoff (seconds)')
        else:
            self.command(f'SET Trigger Holdoff to {time_sec}')

    def trigger_off(self, channel):
        self.command(f'Turn OFF Trigger on Channel {channel}')

    class TriggerEdges(Enum):
        RISING  = 1
        FALLING = 2
        ANY     = 3

    def trigger_edge(self, channel, edgetype = None, level = 0):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if edgetype is not None and not isinstance(edgetype, self.TriggerEdges):
            raise TypeError('edgetype must be a TriggerEdges')

        if not isinstance(level, (int, float)):
            raise TypeError('level must be numeric value')

        if edgetype is None:
            channel = self.query_int('ENTER Current Trigger Source Channel')
            edgetype = self.menu(self.TriggerEdges,prefix='Trigger Slope')
            level = self.query_float('ENTER Current Trigger Level')

            return channel, edgetype, level
        else:
            self.command(f'SET Trigger Mode to EDGE')
            self.command(f'SET Trigger Source to Channel {channel}')
            self.command(f'SET Trigger Slope to {edgetype}')
            self.command(f'SET Trigger Level to {level}')

    class TriggerPulses(Enum):
        POSITIVE_GT       = 1
        POSITIVE_LT       = 2
        POSITIVE_BETWEEN  = 3
        NEGATIVE_GT       = 4
        NEGATIVE_LT       = 5
        NEGATIVE_BETWEEN  = 6

    def trigger_pulse(self, channel, pulsetype = None, level = 0, width = (0,0)):
        raise NotImplementedError

    class TriggerSlopes(Enum):
        POSITIVE_GT       = 1
        POSITIVE_LT       = 2
        POSITIVE_BETWEEN  = 3
        NEGATIVE_GT       = 4
        NEGATIVE_LT       = 5
        NEGATIVE_BETWEEN  = 6

    def trigger_slope(self, channel, slopetype = None, time = (0,0), level = (0,0)):
        raise NotImplementedError

    class TriggerRunts(Enum):
        NONE            = 1
        POSITIVE_GT     = 2,
        POSITIVE_LT     = 3,
        NEGATIVE_GT     = 4,
        NEGATIVE_LT     = 5

    def trigger_runt(self, channel, slopetype = None, wdith = (0,0), level = (0,0)):
        raise NotImplementedError
    
    class TriggerSweeps(Enum):
        AUTO   = 1  # Always display regardless of trigger
        NORMAL = 2  # Display on trigger, hold display, repeat at each trigger
        SINGLE = 3  # Wait for trigger, display and stop

    def sweep(self, trigsweep = None):
        if trigsweep is not None and not isinstance(trigsweep, self.TriggerSweeps):
            raise TypeError('trigsweep must be TriggerSweeps')
        
        if trigsweep is None:
            return self.menu(self.TriggerSweeps)
        else:
            self.command(f'SET Trigger Sweep to {trigsweep}')

    def run(self, trigsweep = TriggerSweeps.AUTO):
        self.command('PRESS RUN')
        self.sweep(trigsweep)

    def stop(self):
        self.command('PRESS STOP')

    class Measurements(Enum):
        V_MAX           =  0
        V_MIN           =  1
        V_PEAK2PEAK     =  2
        V_TOP           =  3
        V_UPPER         =  4    # 90% typical
        V_MIDDLE        =  5    # 50% typical
        V_LOWER         =  6    # 10% typical
        V_BASE          =  7
        V_AMPLITUDE     =  8
        V_AVG           =  9
        V_RMS           = 10
        TIME_V_MAX      = 11
        TIME_V_MIN      = 12
        OVERSHOOT       = 13
        PRESHOOT        = 14
        AREA            = 15
        PERIOD_AREA     = 16
        PERIOD          = 17
        FREQUENCY       = 18
        RISE_TIME       = 19
        FALL_TIME       = 20
        POSITIVE_WIDTH  = 21    # Rise to fall
        NEGATIVE_WIDTH  = 22    # Fall to rise
        POSITIVE_DUTY   = 23
        NEGATIVE_DUTY   = 24
        POSITIVE_SLEW   = 25
        NEGATIVE_SLEW   = 26
        VARIANCE        = 27

    class MathOperators(Enum):
        ADD             = 0
        SUBTRACT        = 1
        MULTIPLY        = 2
        DIVIDE          = 3
        AND             = 4
        OR              = 5
        XOR             = 6
        NOT             = 7
        FFT             = 8
        INTEGRATE       = 9
        DIFFERNTIATE    = 10
        SQRT            = 11
        LOG10           = 12
        LOGN            = 13
        EXP             = 14
        ABS             = 15

    def measure(self, channel, measuretype = None, n = 1, delay_sec = 0.5, timeout_sec = 0.0, threshold = 1.0e37, mathop = MathOperators.SUBTRACT):
        math_meas = False # No math until we know if there is more than one channel requested

        if not isinstance(channel, (int, tuple, list)):
            raise TypeError('channel must an integer type, or a list or tuple of int types')
        elif isinstance(channel, (tuple, list)):
            if len(channel) > 2:
                raise ValueError('only 1 or 2 channels can be used for measurement')
            elif len(channel) == 2:
                math_meas = True
            else:
                channel = channel[0]

        if measuretype is not None:
            if isinstance(measuretype, (tuple, list)):
                for m in measuretype:
                    if not m in self.Measurements:
                        raise ValueError('measuretype must contain values in Measurements enum')
            elif measuretype in self.Measurements:
                # Make the single value iterable
                measuretype = [measuretype]
            else:
                raise TypeError('measuretype must be a value or tuple of Measurements enum')
        else:
            # Default to all that this class currently provides
            measuretype = []
            for m in self.Measurements:
                measuretype.append(m)

        if not isinstance(n, int):
            raise TypeError('n must an integer type')

        if n < 1:
            # measuretype must be a singular measurement to poll
            if isinstance(measuretype, self.Measurements):
                raise ValueError('measuretype must be singular value for polling')
            elif len(measuretype) > 1:
                raise ValueError('measuretype must be singular value for polling')

        if not isinstance(timeout_sec, (int, float)):
            raise TypeError('timeout_sec must be numeric')

        if timeout_sec < 0.0 or timeout_sec == float('inf') or timeout_sec == float('nan'):
            print(f'[WARNING] measure timeout_sec forced to 0.0: was {timeout_sec}')
            timeout_sec = 0.0

        if not isinstance(delay_sec, (int, float)):
            raise TypeError('delay_sec must numeric type')

        if delay_sec < 0:
            delay_sec = 0
            print(f'[WARNING] : delay_sec = {delay_sec} ignored while in measure_frequency_hz')


        if math_meas:
            self.command(f'ENALE Basic MATH Features') # Keeping it simple, only one math
            
            self.command(f'SET Math Source 1 to Channel {channel[0]}')
            self.command(f'SET Math Source 2 to Channel {channel[1]}')
            self.command(f'SET Math Operation to {mathop}')
            self.command(f'SET Math Display to ON')

            # Scale and position the math waveform so it can be seen
            # In add/subtract we assume that scale can add
            # In multiply/divide we assume that scale can product
            s0 = self.vscale(channel = channel[0])
            s1 = self.vscale(channel = channel[1])
            if (mathop == Oscilloscope.MathOperators.MULTIPLY) or (mathop == Oscilloscope.MathOperators.DIVIDE):
                scale = s0 * s1
            else:
                scale = s0 + s1
            self.command(f'SET Math Display Vertical Scale to {scale} /dev')
            self.command('SET Math Display Vertical Offset to 0')

            self.command('SET Measurement Source to MATH')

        else:
            self.command(f'SET Measurement Source to Channel {channel}')

        result = {}
        for m in measuretype:
            result.update({m : []})

        if n > 0:
            for i in range(n):
                for m in measuretype:
                    self.command(f'SET Measurement Type to {m} (for automatic measurement)')
                    value = self.query_float(f'ENTER Measured Value {m}')
                    if len(measuretype) > 1:
                        print('.',end='')
                    if value is not None and abs(value) > threshold:
                        value = None
                    result[m].append(value)
                if len(measuretype) > 1:
                    print('')
        else:
            starttime_sec = time.time()
            nexttime_sec = starttime_sec + 1.0
            m = measuretype[0]
            while (time.time() - starttime_sec) <= timeout_sec:
                self.command(f'SET Measurement Type to {m} (for automatic measurement)')
                value = self.query_float(f'ENTER Measured Value {m}')
                if time.time() >= nexttime_sec:
                    nexttime_sec += 1.0
                    print('.',end='')
                if value is not None:
                    if abs(value) < threshold:
                        result[m].append(value)
                        break
            if timeout_sec >= 1.0:
                print('')

        # Remove the detritus from the display
        self.command('CLEAR Measurements from Display')

        return result

    class DataEncoding(Enum):
        """ Common formats
        """
        ASCII       = 0
        INT8        = 1
        INT16_BE    = 2
        INT16_LE    = 3
        UINT8       = 4
        UINT16_BE   = 5
        UINT16_LE   = 6
        FLOAT32_BE  = 7
        FLOAT32_LE  = 8

    def data(self, channel, startstop = (1, 10000), encoding = DataEncoding.ASCII):
        v = self.verbose
        self.verbose = False

        if not isinstance(channel, int):
            if not isinstance(channel, str) or 'MATH' != channel:
                raise TypeError('channel must an integer type or the string "MATH"')

        if startstop is not None:
            if not isinstance(startstop, (tuple, list)) or len(startstop) != 2:
                raise TypeError('startstop must be a tuple or list of 2 integers')
            
            start = startstop[0]
            stop = startstop[1]
            if not isinstance(start, int) or not isinstance(stop, int):
                raise TypeError('startstop must be a tuple or list of 2 integers')
            
            if stop < start: # Swap fast
                print('[WARNING] startstop swapped for order')
                stop  ^= start
                start ^= stop
                stop  ^= start
 
        if not isinstance(encoding, self.DataEncoding):
            raise TypeError('encoding must be a DataCoding(Enum) value')

        self.command(f'DATA CAPTURE Channel {channel} : NOT supported in Manual operations')

        result = None
        t = None
        preamble = None

        self.verbose = v

        return result, t, preamble

    def sample_rate(self):
        """ Return current sample rate in Sa/s
        """
        return self.query_float('ENTER Current Sample Rate (Sa/s)')

    class FileTypes(Enum):
        PNG     = 0
        JPEG    = 1
        TIFF    = 2
        BMP     = 3
        
    def screen_capture(self, filename):
        """ Capture scope screen and save as filename. File type determines format as supported by derived class
        """
        self.command(f'CAPTURE SCREEN as {filename}')
        return None
