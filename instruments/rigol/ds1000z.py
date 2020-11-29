# Rigol MSO1000Z and DS1000Z scopes
# All have 4 analog channel scopes
# Some have 2 signal source channels
# Some have 16 digital channels
# TODO: add in modified classes and capabilities for signal source and digital channels
#       NOTE: the capability should be hinted in the base Oscilloscope class and parameters can tell scripts if capabilties exist

# Standard
from math import nan
import numpy as np
import os
import time

# 3rd party

# Local
from ..oscope import Oscilloscope

# These dictionaries conveniently convert between types, values, and strings
sourcedict = {  None        : None,
                "CHAN1"     : 1,
                "CHANnel1"  : 1,
                "CHAN2"     : 2,
                "CHANnel2"  : 2,
                "CHAN3"     : 3,
                "CHANnel3"  : 3,
                "CHAN4"     : 4,
                "CHANnel4"  : 4
            }
edgedict = {   None  : None,
               Oscilloscope.TriggerEdges.RISING : "POSitive",
               "POS"                            : Oscilloscope.TriggerEdges.RISING,
               "POSitive"                       : Oscilloscope.TriggerEdges.RISING,
               Oscilloscope.TriggerEdges.FALLING : "NEGative",
               "NEG"                            : Oscilloscope.TriggerEdges.FALLING,
               "NEGative"                       : Oscilloscope.TriggerEdges.FALLING,
               Oscilloscope.TriggerEdges.ANY    : "RFALl",
               "RFAL"                           : Oscilloscope.TriggerEdges.ANY,
               "RFALl"                          : Oscilloscope.TriggerEdges.ANY
            }
unitdict  = {   None                         : None,
                Oscilloscope.Units.VOLT      : "VOLT",
                "VOLT"                       : Oscilloscope.Units.VOLT,
                Oscilloscope.Units.WATT      : "WATT",
                "WATT"                       : Oscilloscope.Units.WATT,
                Oscilloscope.Units.AMP       : "AMP",
                "AMP"                        : Oscilloscope.Units.AMP,
                Oscilloscope.Units.UNKNOWN   : "UNK",
                "UNK"                        : Oscilloscope.Units.UNKNOWN
            }
sweepdict = {   None                                : None,
                Oscilloscope.TriggerSweeps.AUTO     : "AUTO",
                0                                   : Oscilloscope.TriggerSweeps.AUTO,
                "AUTO"                              : Oscilloscope.TriggerSweeps.AUTO,
                Oscilloscope.TriggerSweeps.NORMAL   : "NORM",
                1                                   : Oscilloscope.TriggerSweeps.NORMAL,
                "NORM"                              : Oscilloscope.TriggerSweeps.NORMAL,
                Oscilloscope.TriggerSweeps.SINGLE   : "SING",
                2                                   : Oscilloscope.TriggerSweeps.SINGLE,
                "SING"                              : Oscilloscope.TriggerSweeps.SINGLE
            }
displaydict = { None                           : None,
                Oscilloscope.DisplayState.OFF  : "OFF",
                0                              : Oscilloscope.DisplayState.OFF,
                "OFF"                          : Oscilloscope.DisplayState.OFF,
                Oscilloscope.DisplayState.ON   : "ON",
                1                              : Oscilloscope.DisplayState.ON,
                "ON"                           : Oscilloscope.DisplayState.ON
              }
measuredict = { Oscilloscope.Measurements.V_MAX           : "VMAX",
                Oscilloscope.Measurements.V_MIN           : "VMIN",
                Oscilloscope.Measurements.V_PEAK2PEAK     : "VPP",
                Oscilloscope.Measurements.V_TOP           : "VTOP",
                Oscilloscope.Measurements.V_UPPER         : "VUPper", 
                Oscilloscope.Measurements.V_MIDDLE        : "VMID",
                Oscilloscope.Measurements.V_LOWER         : "VLOWer",
                Oscilloscope.Measurements.V_BASE          : "VBASe",
                Oscilloscope.Measurements.V_AMPLITUDE     : "VAMP",
                Oscilloscope.Measurements.V_AVG           : "VAVG",
                Oscilloscope.Measurements.V_RMS           : "VRMS",
                Oscilloscope.Measurements.TIME_V_MAX      : "TVMAX",
                Oscilloscope.Measurements.TIME_V_MIN      : "TVMIN",
                Oscilloscope.Measurements.OVERSHOOT       : "OVERshoot",
                Oscilloscope.Measurements.PRESHOOT        : "PREshoot",
                Oscilloscope.Measurements.AREA            : "MARea",
                Oscilloscope.Measurements.PERIOD_AREA     : "MPARea",
                Oscilloscope.Measurements.PERIOD          : "PERiod",
                Oscilloscope.Measurements.FREQUENCY       : "FREQuency",
                Oscilloscope.Measurements.RISE_TIME       : "RTIMe",
                Oscilloscope.Measurements.FALL_TIME       : "FTIMe",
                Oscilloscope.Measurements.POSITIVE_WIDTH  : "PWIDth",
                Oscilloscope.Measurements.NEGATIVE_WIDTH  : "NWIDth",
                Oscilloscope.Measurements.POSITIVE_DUTY   : "PDUTy",
                Oscilloscope.Measurements.NEGATIVE_DUTY   : "NDUTy",
                Oscilloscope.Measurements.POSITIVE_SLEW   : "PSLEWrate",
                Oscilloscope.Measurements.NEGATIVE_SLEW   : "NSLEWrate",
                Oscilloscope.Measurements.VARIANCE        : "VARIance"
              }
mathopdict = {  None                                        : None,
                Oscilloscope.MathOperators.ADD              : "ADD",
                "ADD"                                       : Oscilloscope.MathOperators.ADD,
                Oscilloscope.MathOperators.SUBTRACT         : "SUBTract",
                "SUBT"                                      : Oscilloscope.MathOperators.SUBTRACT,
                Oscilloscope.MathOperators.MULTIPLY         : "MULTiply",
                "MULT"                                      : Oscilloscope.MathOperators.MULTIPLY,
                Oscilloscope.MathOperators.DIVIDE           : "DIVision",
                "DIV"                                       : Oscilloscope.MathOperators.DIVIDE,
                Oscilloscope.MathOperators.AND              : "AND",
                "AND"                                       : Oscilloscope.MathOperators.AND,
                Oscilloscope.MathOperators.OR               : "OR",
                "OR"                                        : Oscilloscope.MathOperators.OR,
                Oscilloscope.MathOperators.XOR              : "XOR",
                "XOR"                                       : Oscilloscope.MathOperators.XOR,
                Oscilloscope.MathOperators.NOT              : "NOT",
                "NOT"                                       : Oscilloscope.MathOperators.NOT,
                Oscilloscope.MathOperators.FFT              : "FFT",
                "FFT"                                       : Oscilloscope.MathOperators.FFT,
                Oscilloscope.MathOperators.INTEGRATE        : "INTG",
                "INTG"                                      : Oscilloscope.MathOperators.INTEGRATE,
                Oscilloscope.MathOperators.DIFFERNTIATE     : "DIFF",
                "DIFF"                                      : Oscilloscope.MathOperators.DIFFERNTIATE,
                Oscilloscope.MathOperators.SQRT             : "SQRT",
                "SQRT"                                      : Oscilloscope.MathOperators.SQRT,
                Oscilloscope.MathOperators.LOG10            : "LOG",
                "LOG"                                       : Oscilloscope.MathOperators.LOG10,
                Oscilloscope.MathOperators.LOGN             : "LN",
                "LN"                                        : Oscilloscope.MathOperators.LOGN,
                Oscilloscope.MathOperators.EXP              : "EXP",
                "EXP"                                       : Oscilloscope.MathOperators.EXP,
                Oscilloscope.MathOperators.ABS              : "ABS",
                "ABS"                                       : Oscilloscope.MathOperators.ABS                
             }
dataencdict = { None : None,
                Oscilloscope.DataEncoding.ASCII             : "ASCii",
                "ASC"                                       : Oscilloscope.DataEncoding.ASCII,
                Oscilloscope.DataEncoding.UINT8             : "BYTE",
                "BYTE"                                      : Oscilloscope.DataEncoding.UINT8
                # All other encoding is useless on this scope
              }
filetypedict = { None : None,
                 Oscilloscope.FileTypes.PNG                 : "PNG",
                 "PNG"                                      : Oscilloscope.FileTypes.PNG,
                 Oscilloscope.FileTypes.JPEG                : "JPEG",
                 "JPEG"                                     : Oscilloscope.FileTypes.JPEG,
                 "JPG"                                      : Oscilloscope.FileTypes.JPEG,
                 Oscilloscope.FileTypes.TIFF                : "TIFF",
                 "TIFF"                                     : Oscilloscope.FileTypes.TIFF,
                 "TIF"                                      : Oscilloscope.FileTypes.TIFF,
                 Oscilloscope.FileTypes.BMP                 : "BMP24",
                 "BMP"                                      : Oscilloscope.FileTypes.BMP
               }
triggerdict = { None : None,
                "TD"                                        : Oscilloscope.TriggerStatus.TRIGGERED,
                "WAIT"                                      : Oscilloscope.TriggerStatus.WAITING,
                "AUTO"                                      : Oscilloscope.TriggerStatus.AUTO,
                "RUN"                                       : Oscilloscope.TriggerStatus.AUTO,
                "STOP"                                      : Oscilloscope.TriggerStatus.STOPPED,
              }

class DS1000Z(Oscilloscope):
    USB_PID = '04ce'
    NUM_ANA_CHAN = 4
    NUM_DIG_CHAN = 0    # Create derived class to add specializations
    NUM_SIG_CHAN = 0    # Create derived class to add specialization
    MAX_DATA_POINTS = 12000000
    MAX_DATA_BATCH  = 250000

    def __init__(self,*args, **kwargs):
        super(DS1000Z, self).__init__(*args, **kwargs)

    def display(self, channel, state = Oscilloscope.DisplayState.QUERY):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if not isinstance(state, self.DisplayState):
            raise TypeError('state must be a DisplayState')

        if Oscilloscope.DisplayState.QUERY == state:
            return displaydict[self.query_int(f':CHANnel{channel}:DISPlay?')]
        else:
            self.command(f':CHANnel{channel}:DISPlay {"ON" if state == self.DisplayState.ON else "OFF"}')

    def units(self, channel, unit = Oscilloscope.Units.QUERY):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if not isinstance(unit, self.Units):
            raise TypeError('unit must be a Units')

        if Oscilloscope.Units.QUERY == unit:
            return unitdict[self.query(f':CHANnel{channel}:UNITs?')]
        else:
            self.command(f':CHANnel{channel}:UNITs {unitdict[unit]}')

    def horizontal_scale(self, hdiv_sec = None):
        if hdiv_sec is not None:
            if not isinstance(hdiv_sec, (int, float)):
                raise TypeError('hdiv_sec must be numeric value')

            self.command(f':TIMebase:MAIN:SCALe {hdiv_sec}')
        else:
            return self.query_float(':TIMebase:MAIN:SCALe?')

    def horizontal_position(self, offset_sec = None):
        if offset_sec is not None:
            if not isinstance(offset_sec, (int, float)):
                raise TypeError('offset_sec must be numeric value')

            # Rigol uses < 0 for right of center and our interface is > 0 for right, so invert
            self.command(f':TIMebase:MAIN:OFFSet {-offset_sec}')
        else:
            return self.query_float(':TIMebase:MAIN:OFFSet?')

    def vertical_position(self, channel, offset = None):
        if offset is not None:
            if not isinstance(offset, (int, float)):
                raise TypeError('offset must be numeric value')

            # Rigol uses < 0 for right of center and our interface is > 0 for right, so invert
            self.command(f':CHANnel{channel}:OFFSet {-offset}')
        else:
            return self.query_float(':CHANnel{channel}:OFFSet?')

    def probe_scale(self, channel, nx = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
        
        if nx is not None:
            if not isinstance(nx, (int, float)):
                raise TypeError('nx must be numeric scale for probe: e.g, 0.1, 1, 10, etc')

            self.command(f':CHANnel{channel}:PROBe {nx}')
        else:
            return self.query_float(f':CHANnel{channel}:PROBe?')

    def vertical_scale(self, channel, vdiv = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if vdiv is not None:
            if not isinstance(vdiv, (int, float)):
                raise TypeError('vdiv must be numeric value')

            self.command(f':CHANnel{channel}:SCALe {vdiv}')   # NOTE: van be Volts, Watts, Amps, etc. 10 mV/div is lowest for a 10x probe on this scope)
        else:
            return self.query_float(f':CHANnel{channel}:SCALe?')

    def trigger_status(self):
        stat = triggerdict[self.query(':TRIGger:STATus?')]
        if self.verbose:
            print(f'[INFO] Trigger Status is {stat}')

        return stat

    def trigger_holdoff(self, time_sec = None):
        ''' seconds between re-arming the trigger
        '''
        if not isinstance(time_sec, (int, float)):
            raise TypeError('time_sec must be numeric value')

        if time_sec is None:
            return self.query_float(':TRIGger:HOLDoff?')
        else:
            if time_sec == 0.0:
                time_sec = 16.0e-9 # Minimum allowed

            self.command(f':TRIGger:HOLDoff {time_sec}')

    def trigger_off(self, channel):
        # Easiest is to set the mode to trigger on rising edge with level = 0
        self.trigger_edge(channel, edgetype = self.TriggerEdges.RISING, level = 0.0)

    def trigger_edge(self, channel, edgetype = Oscilloscope.TriggerEdges.QUERY, level = 0):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if not isinstance(edgetype, self.TriggerEdges):
            raise TypeError('edgetype must be a TriggerEdges')

        if not isinstance(level, (int, float)):
            raise TypeError('level must be numeric value')

        if self.TriggerEdges.QUERY == edgetype:
            channel = sourcedict[self.query(':TRIGger:EDGe:SOURce?')]
            edgetype = edgedict[self.query(':TRIGger:EDGe:SLOPe?')]
            level = self.query_float(':TRIGger:EDGe:LEVel?')

            return channel, edgetype, level
        else:
            self.command(f':TRIGger:EDGe:LEVel 0.0')    # Start with zero before changing mode
            self.command(f':TRIGger:MODE EDGE')
            self.command(f':TRIGger:EDGe:SOURce CHANnel{channel}')
            self.command(f':TRIGger:EDGe:SLOPe {edgedict[edgetype]}')
            self.command(f':TRIGger:EDGe:LEVel {level}')

    def trigger_pulse(self, channel, pulsetype = Oscilloscope.TriggerPulses.QUERY, level = 0, width = (0,0)):
        raise NotImplementedError

    def trigger_slope(self, channel, slopetype = Oscilloscope.TriggerSlopes.QUERY, time = (0,0), level = (0,0)):
        raise NotImplementedError

    def trigger_runt(self, channel, slopetype = Oscilloscope.TriggerRunts.QUERY, wdith = (0,0), level = (0,0)):
        raise NotImplementedError

    def sweep(self, trigsweep = Oscilloscope.TriggerSweeps.QUERY):
        if not isinstance(trigsweep, self.TriggerSweeps):
            raise TypeError('trigsweep must be TriggerSweeps')
        
        if Oscilloscope.TriggerSweeps.QUERY == trigsweep:
            return sweepdict[self.query(':TRIGger:SWEep?')]
        else:
            self.command(f':TRIGger:SWEep {sweepdict[trigsweep]}')

    def run(self, trigsweep = Oscilloscope.TriggerSweeps.AUTO):
        # Rigol will default to auto when transitioning from stop to run
        # This means that run must be commanded before the sweep mode is selected
        self.command(":RUN")
        self.sweep(trigsweep)

    def stop(self):
        self.command(":STOP")

    # Rigol needs at least 1 second to stabilize after source change
    def measure(self, channel, measuretype = None, n = 1, delay_sec = 1.0, timeout_sec = 0.0, threshold = 1.0e37, mathop = Oscilloscope.MathOperators.SUBTRACT):
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
            measuretype = self.Measurements

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

        # Rigol uses this source as the default when omitting the sources from the measure item command
        if math_meas:
            self.command(f':MATH:SOURce1 CHANnel{channel[0]}')
            self.command(f':MATH:SOURce2 CHANnel{channel[1]}')
            self.command(f':MATH:LSOUrce1 CHANnel{channel[0]}')
            self.command(f':MATH:LSOUrce2 CHANnel{channel[1]}')
            self.command(f':MATH:DISPlay ON')
            self.command(f':MATH:OPERator {mathopdict[mathop]}')

            self.command(f':MEASure:SOURce MATH')
        else:
            self.command(f':MEASure:SOURce CHANnel{channel}')

        # Force threshold to be standard 10/50/90 %
        self.command(':MEASure:SETup:MIN 10')
        self.command(':MEASure:SETup:MID 50')
        self.command(':MEASure:SETup:MAX 90')
        time.sleep(delay_sec)

        result = {}
        for m in measuretype:
            result.update({m : []})

        if n > 0:
            for i in range(n):
                for m in measuretype:
                    value = self.query_float(f':MEASure:ITEM? {measuredict[m]}')
                    if len(measuretype) > 1:
                        print('.',end='')
                    if value is not None and abs(value) > threshold:
                        value = nan
                    result[m].append(value)
                if len(measuretype) > 1:
                    print('')
        else:
            starttime_sec = time.time()
            nexttime_sec = starttime_sec + 1.0
            m = measuretype[0]
            while (time.time() - starttime_sec) <= timeout_sec:
                value = self.query_float(f':MEASure:ITEM? {measuredict[m]}')
                if time.time() >= nexttime_sec:
                    nexttime_sec += 1.0
                    print('.',end='')
                if value is not None:
                    if abs(value) < threshold:
                        break
            if timeout_sec >= 1.0:
                print('')
            if len(result[m]) == 0:
                result[m].append(nan)

        # Remove the detritus from the display
        self.command(':MEASure:CLEar ALL')

        return result

    # Rigol has a 1200 point limit in normal waveform mode
    def data(self, channel, startstop = None, encoding = Oscilloscope.DataEncoding.ASCII):
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
        else:
            # Setup to batch read to the end of memory
            start = 1
            stop = DS1000Z.MAX_DATA_BATCH

        if not isinstance(encoding, self.DataEncoding):
            raise TypeError('encoding must be a DataCoding(Enum) value')
        elif not encoding in dataencdict:
            raise ValueError('Unsupported Encoding for this oscilloscope')

        # Select a data source
        if isinstance(channel,int):
            self.command(f':WAVeform:SOURce CHANnel{channel}')
            if v:
                print(f'[INFO] Reading Channel {channel} Data')

        else:
            self.command(':WAVeform:SOURce MATH')
            if v:
                print(f'[INFO] Reading MATH Data')

        # Select encoding (e.g., ascii or binary various forms, etc)
        # Select number of bytes per data point (if applicable)
        self.command(f':WAVeform:FORMat {dataencdict[encoding]}')

        # Select the start/stop points in the data to transfer
        if isinstance(channel,str):
            self.command(':WAVeform:MODE NORMal')
        else:
            self.command(':WAVeform:MODE MAXimum')

        if (stop-start) > 1200 and isinstance(channel,str):
            print("[WARNING] MATH source on this scope only supports 1200 data points")
            start = 1
            stop = 1200
            startstop = (start, stop) # Used as a flag to cancel the "all points" state

        # Get preamble information if applicable
        preamble = self.query(':WAVeform:PREamble?')

        # Decode the preamble into essential information about the sample
        if preamble is not None:
            x = preamble.split(',')
            preamble = {    'format' : x[0],
                            'type'   : x[1],
                            'points' : int(x[2]),
                            'count'  : int(x[3]),
                            'xincr'  : float(x[4]),
                            'xorig'  : float(x[5]),
                            'xref'   : int(x[6]),
                            'yincr'  : float(x[7]),
                            'yorig'  : float(x[8]),
                            'yref'   : int(x[9])
                       }

        if startstop is None:
            # batch process until all of the points are read
            points = float(preamble['points']) # TODO: Error handle None
        else:
            points = stop - start + 1

        if self.DataEncoding.ASCII == encoding:
            result = np.array([],dtype=np.float32)
        else:
            result = np.array([], dtype=np.uint8)

        while points > 0:
            print('.',end='')
            self.command(f':WAVeform:STARt {start}')
            self.command(f':WAVeform:STOP {stop}')

            # Transfer the data
            if self.DataEncoding.ASCII == encoding:
                _result = self.query(':WAVeform:DATA?')
                if _result is not None:
                    # Parse the data
                    # Header is #Nxxx...n
                    #   # is starting delimiter
                    #   N is number of digits following (1 .. 9)
                    #   xxx...n is the N digits representing the number of bytes or sample point depending on mode
                    if _result[0] == '#':
                        N = int(_result[1])
                        count = int(_result[2:N+2])
                        _result = _result[N+2:]

                    _result = _result.replace('\n','')
                    _result = _result.split(',')
                    _result = np.array(_result, dtype=np.float32)

            else:
                _result = self.query_binary(':WAVeform:DATA?')
                _result = np.array(_result, dtype=np.uint8)

            if _result is not None:
                points -= len(_result)
                result = np.append(result, _result)

                if len(_result) > 1200:
                    start = start + len(_result)
                    stop = start + min(points,DS1000Z.MAX_DATA_BATCH) - 1
                else:
                    break
            else:
                break

        print('')
        self.verbose = v

        if len(result) != 0:
            t = np.arange(0, preamble['xincr'] * len(result), preamble['xincr'])
        else:
            t = np.array([])

        return result, t, preamble

    def sample_rate(self):
        return self.query_float(':ACQuire:SRATe?')

    def screen_capture(self, filename):
        if not self.simulated:
            # Break the filename down to get type
            ext = os.path.splitext(filename)[1][1:].upper()
            if ext in filetypedict:
                enum = filetypedict[ext]
                filetypestring = filetypedict[enum]
                buf = self.query_binary(f':DISP:DATA? ON,0,{filetypestring}')

                filename = os.path.join(self.datastorage_path,filename)

                with open(filename, 'wb') as f:
                    f.write(bytearray(buf))

                return buf is not None
            else:
                raise TypeError(f'Unsupported file type: {ext}')
        else:
            print('[WARNING] Screen Capture not supported in Simulation')
            return False
