# Standard imports
from enum import Enum
import time

# 3rd party imports

# local imports
from .scpi import Device

# Base class for all oscopes to help guide a common API
# Each brand will be different in syntax but the core functionality will be the same
class Oscilloscope(Device):
    NUM_ANA_CHAN = 0
    NUM_DIG_CHAN = 0
    NUM_SIG_CHAN = 0
    MAX_DATA_POINTS = 0

    def __init__(self,*args, **kwargs):
        super(Oscilloscope, self).__init__(*args, **kwargs)

    class DisplayState(Enum):
        QUERY = 0
        OFF   = 1
        ON    = 2

    def display(self, channel, state = DisplayState.QUERY):
        raise NotImplementedError

    class Units(Enum):
        UNKNOWN = 0
        QUERY   = 1
        VOLT    = 2
        WATT    = 3
        AMP     = 4


    def units(self, channel, unit = Units.QUERY):
        ''' Set the veritical units of the specified channel when supported

        If not supported this functions should just silently return
        '''
        raise NotImplementedError

    def horizontal_scale(self, hdiv_sec = None):
        raise NotImplementedError

    def horizontal_position(self, offset_sec = None):
        """ Align trigger on display (> 0 is right of center, < 0 is left of center)
        """
        raise NotImplementedError

    def probe_scale(self, channel, nx = None):
        raise NotImplementedError

    def vertical_scale(self, channel, vdiv = None):
        raise NotImplementedError

    def vertical_position(self, channel, offset = None):
        raise NotImplementedError

    class TriggerStatus(Enum):
        TRIGGERED   = 0  # Trigger occured or is occuring
        WAITING     = 1  # Waiting for trigger
        AUTO        = 3  # Always acquiring data even without trigger
        STOPPED     = 4  # Not acquiring data (trigger in single mode will end here)

    def trigger_status(self):
        raise NotImplementedError

    def wait_for_trigger_status(self, trigger_status, timeout_sec):
        if not isinstance(trigger_status, Oscilloscope.TriggerStatus):
            if not isinstance(trigger_status, (list, tuple)):
                raise TypeError("trigger_status must be an Oscilloscope.TriggerStatus or list or tuple of same")
            else:
                for t in trigger_status:
                    if not isinstance(t,Oscilloscope.TriggerStatus):
                        raise TypeError("trigger_status list or tuple must only contain Oscilloscope.TriggerStatus")
        else:
            trigger_status = [trigger_status]
        
        if not isinstance(timeout_sec, (float, int)):
            raise TypeError("timeout_sec must be numeric")

        verbose = self.verbose
        self.verbose = False

        done = False
        start  = time.perf_counter()
        while (time.perf_counter() - start < timeout_sec) and not done:
            for t in trigger_status:
                if self.trigger_status() is t:
                    done = True
                    break

        self.verbose = verbose
        return self.trigger_status()

    def trigger_holdoff(self, time_sec = None):
        ''' seconds between re-arming the trigger
        '''
        raise NotImplementedError

    def trigger_off(self, channel):
        raise NotImplementedError

    class TriggerEdges(Enum):
        QUERY = 0
        RISING  = 1
        FALLING = 2
        ANY     = 3

    def trigger_edge(self, channel, edgetype = TriggerEdges.QUERY, level = 0):
        raise NotImplementedError

    class TriggerPulses(Enum):
        QUERY             = 0
        POSITIVE_GT       = 1
        POSITIVE_LT       = 2
        POSITIVE_BETWEEN  = 3
        NEGATIVE_GT       = 4
        NEGATIVE_LT       = 5
        NEGATIVE_BETWEEN  = 6

    def trigger_pulse(self, channel, pulsetype = TriggerPulses.QUERY, level = 0, width = (0,0)):
        raise NotImplementedError

    class TriggerSlopes(Enum):
        QUERY             = 0
        POSITIVE_GT       = 1
        POSITIVE_LT       = 2
        POSITIVE_BETWEEN  = 3
        NEGATIVE_GT       = 4
        NEGATIVE_LT       = 5
        NEGATIVE_BETWEEN  = 6

    def trigger_slope(self, channel, slopetype = TriggerSlopes.QUERY, time = (0,0), level = (0,0)):
        raise NotImplementedError

    class TriggerRunts(Enum):
        QUERY           = 0
        NONE            = 1
        POSITIVE_GT     = 2,
        POSITIVE_LT     = 3,
        NEGATIVE_GT     = 4,
        NEGATIVE_LT     = 5

    def trigger_runt(self, channel, slopetype = TriggerRunts.QUERY, wdith = (0,0), level = (0,0)):
        raise NotImplementedError
    
    class TriggerSweeps(Enum):
        QUERY  = 0
        AUTO   = 1  # Always display regardless of trigger
        NORMAL = 2  # Display on trigger, hold display, repeat at each trigger
        SINGLE = 3  # Wait for trigger, display and stop

    def sweep(self, trigsweep = TriggerSweeps.QUERY):
        raise NotImplementedError

    def run(self, trigsweep = TriggerSweeps.AUTO):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

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

    def measure(self, channel, measuretype = None, n = 1, delay_sec = 0.5, timeout_sec = 0.0, threshold = float('inf'), mathop = MathOperators.SUBTRACT):
        """Single source measurements as defined by Measurements(Enum)

        :channel: either single integer or a tuple or list of 2 integers
        When 2 integers are supplied the measurement source is defined by the scope's math functions using the mathop

        :measuretype: either None (all), a value from Measurements(Enum), or tuple or list of values

        :n: number of measurements of measuretype to read, nominally > 0, but if <= 0 will poll until timeout 

        :delay_sec: delay between selection of measurement source and start of measurements
        sometimes needed to ensure measurement stability

        :timeout_sec: timeout when polling for a value within +/- threshold

        :threshold: used during polling to reject values deemed invalid by the scope

        :return: a dictionary of measured values in lists
        """
        raise NotImplementedError

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
        # Select a data source
        # Select encoding (e.g., ascii or binary various forms, etc)
        # Select number of bytes per data point (if applicable)
        # Select the start/stop points in the data to transfer
        # Get preamble information if applicable
        # Transfer the data

        raise NotImplementedError

    def sample_rate(self):
        """ Return current sample rate in Sa/s
        """
        raise NotImplementedError

    class FileTypes(Enum):
        PNG     = 0
        JPEG    = 1
        TIFF    = 2
        BMP     = 3
        
    def screen_capture(self, filename):
        """ Capture scope screen and save as filename. File type determines format as supported by derived class
        """
        raise NotImplementedError
