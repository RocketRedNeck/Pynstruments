# Tektronix MSO 4, 5, and 6 series scopes
# TODO: add in modified classes and capabilities for signal source and digital channels
#       NOTE: the capability should be hinted in the base Oscilloscope class and parameters can tell scripts if capabilties exist
# 
# See the following for examples:
#   https://forum.tek.com/viewtopic.php?f=580&t=133570

# Standard
from math import nan
import numpy as np
from struct import unpack
import os
import time

# 3rd party

# Local
from ..oscope import Oscilloscope

# NOTE: Read the section on Synchronization Methods (~page 1455), including example of a sequence a few pages in (1457)

# These dictionaries conveniently convert between types, values, and strings
sourcedict = {  None      : None,
                "CH1"     : 1,
                "CH2"     : 2,
                "CH3"     : 3,
                "CH4"     : 4,
                "CH5"     : 5,
                "CH6"     : 6,
                "CH7"     : 7,
                "CH8"     : 8
             }
edgedict = {   None  : None,
               Oscilloscope.TriggerEdges.RISING : "RISe",
               "RIS"                            : Oscilloscope.TriggerEdges.RISING,
               "RISe"                           : Oscilloscope.TriggerEdges.RISING,
               Oscilloscope.TriggerEdges.FALLING : "FALL",
               "FALL"                            : Oscilloscope.TriggerEdges.FALLING,
               Oscilloscope.TriggerEdges.ANY    : "EITher",
               "EIT"                            : Oscilloscope.TriggerEdges.ANY,
               "EITher"                         : Oscilloscope.TriggerEdges.ANY
            }
sweepdict = {   None                                : None,
                Oscilloscope.TriggerSweeps.AUTO     : "AUTO",
                "AUTO"                              : Oscilloscope.TriggerSweeps.AUTO,
                Oscilloscope.TriggerSweeps.NORMAL   : "NORMal",
                "NORM"                              : Oscilloscope.TriggerSweeps.NORMAL,
                "NORMal"                            : Oscilloscope.TriggerSweeps.NORMAL,
                Oscilloscope.TriggerSweeps.SINGLE   : "NORMal",
            }
displaydict = { None                           : None,
                Oscilloscope.DisplayState.OFF  : "OFF",
                0                              : Oscilloscope.DisplayState.OFF,
                "0"                            : Oscilloscope.DisplayState.OFF,
                "OFF"                          : Oscilloscope.DisplayState.OFF,
                Oscilloscope.DisplayState.ON   : "ON",
                1                              : Oscilloscope.DisplayState.ON,
                "1"                            : Oscilloscope.DisplayState.ON,
                "ON"                           : Oscilloscope.DisplayState.ON
              }
dataencdict = { None : None,                                  #ENCdg, BYT_Nr, unpack type, dtype
                Oscilloscope.DataEncoding.INT8              : ("RIBinary",  1, 'b', 'int8'),
                Oscilloscope.DataEncoding.INT16_LE          : ("SRIbinary", 2, 'h', 'int16'),
              }
measuredict = { Oscilloscope.Measurements.V_MAX           : "MAXimum",
                Oscilloscope.Measurements.V_MIN           : "MINImum",
                Oscilloscope.Measurements.V_PEAK2PEAK     : "PK2Pk",
                Oscilloscope.Measurements.V_TOP           : "TOP",
                Oscilloscope.Measurements.V_BASE          : "BASE",
                Oscilloscope.Measurements.V_AMPLITUDE     : "AMPLITUDE",
                Oscilloscope.Measurements.V_AVG           : "MEAN",
                Oscilloscope.Measurements.V_RMS           : "RMS",
                Oscilloscope.Measurements.OVERSHOOT       : "POVERSHOOT",
                Oscilloscope.Measurements.PRESHOOT        : "NOVershoot",
                Oscilloscope.Measurements.AREA            : "AREA",
                Oscilloscope.Measurements.PERIOD          : "PERIOD",
                Oscilloscope.Measurements.FREQUENCY       : "FREQuency",
                Oscilloscope.Measurements.RISE_TIME       : "RISETIME",
                Oscilloscope.Measurements.FALL_TIME       : "FALLTIME",
                Oscilloscope.Measurements.POSITIVE_WIDTH  : "PWIDth",
                Oscilloscope.Measurements.NEGATIVE_WIDTH  : "NWidth",
                Oscilloscope.Measurements.POSITIVE_DUTY   : "PDUTY",
                Oscilloscope.Measurements.NEGATIVE_DUTY   : "NDUTy",
                Oscilloscope.Measurements.POSITIVE_SLEW   : "RISESLEWRATE",
                Oscilloscope.Measurements.NEGATIVE_SLEW   : "FALLSLEWRATE"
              }
mathopdict = {  None                                        : None,
                Oscilloscope.MathOperators.ADD              : "ADD",
                "ADD"                                       : Oscilloscope.MathOperators.ADD,
                Oscilloscope.MathOperators.SUBTRACT         : "SUBTract",
                "SUBT"                                      : Oscilloscope.MathOperators.SUBTRACT,
                Oscilloscope.MathOperators.MULTIPLY         : "MULTiply",
                "MULT"                                      : Oscilloscope.MathOperators.MULTIPLY,
                Oscilloscope.MathOperators.DIVIDE           : "DIVision",
                "DIV"                                       : Oscilloscope.MathOperators.DIVIDE               
             }
filetypedict = { None : None,
                 Oscilloscope.FileTypes.PNG                 : "PNG",
                 "PNG"                                      : Oscilloscope.FileTypes.PNG,
                 Oscilloscope.FileTypes.JPEG                : "JPEG",
                 "JPEG"                                     : Oscilloscope.FileTypes.JPEG,
                 "JPG"                                      : Oscilloscope.FileTypes.JPEG,
                 Oscilloscope.FileTypes.BMP                 : "BMP",
                 "BMP"                                      : Oscilloscope.FileTypes.BMP
               }
triggerdict = { None : None,
                "TRIGGER"                                   : Oscilloscope.TriggerStatus.TRIGGERED,
                "ARMED"                                     : Oscilloscope.TriggerStatus.WAITING,
                "READY"                                     : Oscilloscope.TriggerStatus.WAITING,
                "AUTO"                                      : Oscilloscope.TriggerStatus.AUTO,
                "SAVE"                                      : Oscilloscope.TriggerStatus.STOPPED
              }


class MSO456(Oscilloscope):
    USB_PID = '0522'
    NUM_ANA_CHAN = 4    # Minimum, and in derived versions can be 6 or 8
    NUM_DIG_CHAN = NUM_ANA_CHAN * 8    # Create derived class to add specializations
    NUM_SIG_CHAN = 0    # Create derived class to add specialization
    MAX_DATA_POINTS = 0 # TODO
    MAX_DATA_BATCH  = 10000 # TODO

    def __init__(self,*args, **kwargs):
        super(MSO456, self).__init__(*args, **kwargs)

        self.query_delay = 0.0

        # Tek embeds some characters that do not decode using
        # the default ASCII codec
        self._inst.encoding = 'utf-8'

    # Override reset to ensure that headers are disabled and codec is enforced
    def reset(self, timeout_sec = 10.0):
        super(MSO456, self).reset(timeout_sec)
        
        # Reinforce the codec we need
        self._inst.encoding = 'utf-8'

        # Disable headers in responses
        self.command(f':HEADer 0')

    def display(self, channel, state = Oscilloscope.DisplayState.QUERY):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if not isinstance(state, self.DisplayState):
            raise TypeError('state must be a DisplayState')

        if Oscilloscope.DisplayState.QUERY == state:
            return displaydict[self.query(f':DISplay:WAVEView1:CH{channel}:STATE?')]
        else:
            self.command(f':DISplay:WAVEView1:CH{channel}:STATE {"ON" if state == self.DisplayState.ON else "OFF"}')

    def units(self, channel, unit = Oscilloscope.Units.QUERY):
        pass

    def horizontal_scale(self, hdiv_sec = None):
        if hdiv_sec is not None:
            if not isinstance(hdiv_sec, (int, float)):
                raise TypeError('hdiv_sec must be numeric value')

            self.command(f':HORizontal:MODE:SCAle {hdiv_sec}')
        else:
            return self.query_float(':HORizontal:MODE:SCAle?')

    def horizontal_position(self, offset_sec = None):
        if offset_sec is not None:
            if not isinstance(offset_sec, (int, float)):
                raise TypeError('delay_sec must be numeric value')

            # Tek has two ways to control horizontal position
            #  1. A percent 0-left 100-right
            #  2. A delay time, < 0 for right > 0 for left
            # our interface is > 0 for right, so invert
            self.command(f':HORizontal:DELay:MODe ON')
            self.command(f':HORizontal:DELay:TIMe {-offset_sec}')
        else:
            return self.query_float(':HORizontal:DELay:TIMe?')

    def probe_scale(self, channel, nx = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')
        
        if nx is not None:
            if not isinstance(nx, (int, float)):
                raise TypeError('nx must be numeric scale for probe: e.g, 0.1, 1, 10, etc')

            self.command(f':CH{channel}:PROBe:SET "ATTENUATION {nx}X"')
        else:
            # nx is None right now, a good default for return
            qstr = self.query(f':CH{channel}:PROBe:SET?')
            if qstr is not None:
                nxstr = qstr.split(' ')
                if len(nxstr) == 2:
                    nxstr = nxstr[1].replace('X','')
                    nx = int(nxstr)

            return nx

    def vertical_scale(self, channel, vdiv = None):
        if not isinstance(channel, int):
            raise TypeError('channel must an integer type')

        if vdiv is not None:
            if not isinstance(vdiv, (int, float)):
                raise TypeError('vdiv must be numeric value')

            self.command(f':CH{channel}:SCALe {vdiv}')   # NOTE: is Volts only on Tek?
        else:
            return self.query_float(f':CH{channel}:SCALe?')

    def trigger_status(self):
        stat = triggerdict[self.query(':TRIGger:STATE?')]
        if self.verbose:
            print(f'[INFO] Trigger Status is {stat}')

        return stat


    def trigger_holdoff(self, time_sec = None):
        if not isinstance(time_sec, (int, float)):
            raise TypeError('time_sec must be numeric value')

        if time_sec is None:
            return self.query_float(':TRIGger:A:HOLDoff:TIMe?')
        else:
            if time_sec == 0.0:
                time_sec = 16.0e-9 # Minimum allowed

            self.command(f':TRIGger:A:HOLDoff:BY TIMe')
            self.command(f':TRIGger:HOLDoff:TIMe {time_sec}')

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
            channel = sourcedict[self.query(':TRIGger:A:EDGe:SOURce?')]
            edgetype = edgedict[self.query(':TRIGger:A:EDGe:SLOPe?')]
            level = self.query_float(f':TRIGger:A:LOWerthreshold:CH{channel}?')

            return channel, edgetype, level
        else:
            self.command(f':TRIGger:A:LOWerthreshold:CH{channel} 0.0')    # Start with zero before changing mode
            self.command(f':TRIGger:A:TYPe EDGE')
            self.command(f':TRIGger:A:EDGe:SOURce CH{channel}')
            self.command(f':TRIGger:EDGe:SLOPe {edgedict[edgetype]}')
            self.command(f':TRIGger:A:LOWerthreshold:CH{channel} {level}')

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
            return sweepdict[self.query(':TRIGger:A:MODe?')]
        else:
            self.command(f':TRIGger:A:MODe {sweepdict[trigsweep]}')

    def run(self, trigsweep = Oscilloscope.TriggerSweeps.AUTO):
        self.command(":ACQuire:STATE RUN")
        self.wait_op_complete()
        self.sweep(trigsweep)
        self.wait_op_complete()

    def stop(self):
        self.command(":ACQuire:STATE STOP")

    def measure(self, channel, measuretype = None, n = 1, delay_sec = 0.5, timeout_sec = 0.0, threshold = 1.0e37, mathop = Oscilloscope.MathOperators.SUBTRACT):
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
                if m in measuredict:
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
            self.command(f':MATH:MATH1:TYPe BASic') # Keeping it simple, only one math
            
            self.command(f':MATH:MATH1:SOURCE1 CH{channel[0]}')
            self.command(f':MATH:MATH1:SOURCE2 CH{channel[1]}')
            self.command(f':MATH:MATH1:FUNCtion {mathopdict[mathop]}')
            self.command(f':DISplay:SELect:MATH MATH1')
            self.command(f':DISplay:GLOBal:MATH1:STATE ON')

            # Scale and position the math waveform so it can be seen
            # In add/subtract we assume that scale can add
            # In multiply/divide we assume that scale can product
            s0 = self.vertical_scale(channel = channel[0])
            s1 = self.vertical_scale(channel = channel[1])
            op = mathopdict[mathop]
            if (op == Oscilloscope.MathOperators.MULTIPLY) or (op == Oscilloscope.MathOperators.DIVIDE):
                scale = s0 * s1
            else:
                scale = s0 + s1
            self.command(f'DISplay:WAVEView1:MATH:MATH1:VERTical:SCAle {scale}')
            self.command(':DISplay:WAVEView1:MATH:MATH1:VERTical:POSition 0.0')

            self.wait_op_complete()

            self.command(f':MEASUrement:IMMed:SOURce MATH1')
        else:
            self.wait_op_complete()
            self.command(f':DISplay:GLOBal:MATH1:STATE OFF')
            self.command(f':MEASUrement:IMMed:SOURce CH{channel}')


        # # Force threshold to be standard 10/50/90 %
        # self.command(':MEASure:SETup:MIN 10')
        # self.command(':MEASure:SETup:MID 50')
        # self.command(':MEASure:SETup:MAX 90')
        # time.sleep(delay_sec)

        result = {}
        for m in measuretype:
            result.update({m : []})

        if n > 0:
            for i in range(n):
                for m in measuretype:
                    self.command(f':MEASUrement:IMMed:TYPE {measuredict[m]}')
                    value = self.query_float(f':MEASUrement:IMMed:VALue?')
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
                self.command(f':MEASUrement:IMMed:TYPE {measuredict[m]}')
                value = self.query_float(f':MEASUrement:IMMed:VALue?')
                if time.time() >= nexttime_sec:
                    nexttime_sec += 1.0
                    print('.',end='')
                if value is not None:
                    if abs(value) < threshold:
                        result[m].append(value)
                        break
            if timeout_sec >= 1.0:
                print('')
            if len(result[m]) == 0:
                result[m].append(nan)

        # Remove the detritus from the display
        self.command(':MEASure:CLEar ALL')

        return result

    def data(self, channel, startstop = (1,1250000), encoding = Oscilloscope.DataEncoding.INT16_LE):
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
            stop = MSO456.MAX_DATA_BATCH

        if not isinstance(encoding, self.DataEncoding):
            raise TypeError('encoding must be a DataCoding(Enum) value')
        elif not encoding in dataencdict:
            raise ValueError('Unsupported Encoding for this oscilloscope')

        # Select a data source
        if isinstance(channel,int):
            self.command(f':DATa:SOUrce CH{channel}')
            self.query(':DATa:SOUrce?')
        else:
            self.command(':DATa:SOUrce MATH1') # Default to a simple 1 math concept TODO more?

        # Select encoding (e.g., ascii or binary various forms, etc)
        # Select number of bytes per data point (if applicable)
        # NOTE: the tuple order is ENCdg, BYT_Nr, BYT_Or, BN_Fmt

        self.command(f':DATa:ENCdg {dataencdict[encoding][0]}')
        self.query(':DATa:ENCdg?')
        self.command(f':WFMOutpre:BYT_Nr {dataencdict[encoding][1]}')
        self.query(':WFMOutpre:ENCdg?')
        self.query(':WFMOutpre:BYT_Nr?')
        self.query(':WFMOutpre:BN_Fmt?')
        self.query(':WFMOutpre:BYT_Or?')

        # Get preamble information if applicable
        # Tek encodes characters in a way that crashes the default query
        # So manually write/read_raw and use a decode that works
        preamble = self.query(':WFMOutpre?')

        # Decode the preamble into essential information about the sample
        if preamble is not None:
            x = preamble.split(';')
            preamble = {    'format' : x[0:6],
                            'type'   : x[6],
                            'points' : int(x[7]),
                            'count'  : None,
                            'xincr'  : float(x[11]),
                            'xorig'  : float(x[12]),
                            'xref'   : float(x[13]),
                            'yincr'  : float(x[15]),
                            'ymult'  : float(x[15]),
                            'yorig'  : float(x[17]),
                            'yref'   : float(x[16]),
                            'yoff'   : float(x[16])
                       }
        if self.verbose:
            for key in preamble:
                print(key, preamble[key])

        # Right now it looks like ths scope does not require batch processing
        # to retrieve all the points
        if startstop is None:
            # process until all of the points are read
            points = preamble['points'] # TODO: Error handle None
        else:
            points = stop - start + 1

        translator = {  Oscilloscope.DataEncoding.INT8     : ('b', 1, 'int8'),
                        Oscilloscope.DataEncoding.INT16_LE : ('h', 2, 'int16')
                        }

        result = np.array([],dtype=dataencdict[encoding][3])

        while points > 0:
            print('.',end='')
            self.command(f':DATa:START {start}')
            self.command(f':DATa:STOP {stop}')

            # Transfer the data
            t = dataencdict[encoding]
            _result = self.query_raw(':CURVe?')
            if _result is not None:
                # Parse the data
                # Header is #Nxxxx.n
                #   # is starting delimiter
                #   N is number of digits following (1 .. 9)
                #   xxx...n is the N digits representing the number of bytes or sample point depending on mode
                headerlen = 2 + int(_result[1:2].decode('ascii'))
                header = _result[:headerlen]
                _result = _result[headerlen:]

            if _result is not None:
                points -= len(_result)
                ustr = f'{len(_result) // t[1]}{t[2]}'
                _result = np.array(unpack(ustr, _result[:t[1]*(len(_result)//t[1])]),dtype=t[3])
                _result = (_result - preamble['yoff']) * preamble['ymult'] + preamble['yorig']
                result = np.append(result, _result)

                if len(_result) > 1200:
                    start = start + len(_result)
                    stop = start + min(points,MSO456.MAX_DATA_BATCH) - 1
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
        """ Return current sample rate in Sa/s
        """
        raise NotImplementedError

    def screen_capture(self, filename):
        if not self.simulated:
            # Break the filename down to get type
            ext = os.path.splitext(filename)[1][1:].upper()
            if ext in filetypedict:
                enum = filetypedict[ext]
                filetypestring = filetypedict[enum]

                self.command('FILESystem:CWD "C:/Users/Public"')

                # Save the file on the scope's hard drive
                self.command(f':SAVe:IMAGe "Temp.{ext}"')
                self.wait_op_complete()

                # Read the image file from the scope's hard drive
                v = self.verbose
                self.verbose = False
                buf = self.query_raw(f'FILESystem:READFile "Temp.{ext}"')
                self.verbose = v

                filename = os.path.join(self.datastorage_path,filename)
                
                with open(filename, 'wb') as f:
                    f.write(bytearray(buf))

                # Delete the image file from the scope's hard drive.
                self.command(f'FILESystem:DELEte "Temp.{ext}"')

                return buf is not None
                        
            else:
                raise TypeError(f'Unsupported file type: {ext}')
        else:
            print('[WARNING] Screen Capture not supported in Simulation')
            return False            

class MSO58(MSO456):
    NUM_ANA_CHAN = 8    # For this specific model
    NUM_DIG_CHAN = NUM_ANA_CHAN * 8    # Create derived class to add specializations
    NUM_SIG_CHAN = 0    # Create derived class to add specialization
    MAX_DATA_POINTS = 0 # TODO

    def __init__(self,*args, **kwargs):
        super(MSO58, self).__init__(*args, **kwargs)
 