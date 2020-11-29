# Saleae Logic Analyzers
# Logic Pro 16 - Prefered
# Logic Pro 8
# Logic 8
# Logic 4

# Standard
import csv
import enum
import os
import platform
import sys
import time

# 3rd party
from matplotlib import pyplot as pl
import numpy as np

# Local
from instruments.saleae import saleae   # A non-SCPI compliant API
from instruments.analyzer import Analyzer

# Re-define the Analyzer base to be derived from the Saleae API
Base = Analyzer.create_type(saleae.Device)

class DigitalVoltageFlags(enum.IntEnum):
    '''Whether a given voltage is selected.'''
    NotSelected = 0
    Selected = 1

class ConnectedDevice():

    def __init__(self, type, name, id, index, active):
        self.type = type
        self.name = name
        self.id = int(id, 16)
        self.index = int(index)
        self.active = bool(active)

    def __str__(self):
        if self.active:
            return "<saleae.ConnectedDevice #{self.index} {self.type} {self.name} ({self.id:x}) **ACTIVE**>".format(self=self)
        else:
            return "<saleae.ConnectedDevice #{self.index} {self.type} {self.name} ({self.id:x})>".format(self=self)

    def __repr__(self):
        return str(self)

class Logic(Base):

    class PerformanceOption(enum.IntEnum):
        '''
        Additional control when performing mixed captures.

        For more see https://github.com/saleae/SaleaeSocketApi/blob/master/Doc/Logic%20Socket%20API%20Users%20Guide.md#set-performance-option
        '''
        OneHundredPercent = 100
        EightyPercent = 80
        SixtyPercent = 60
        FortyPercent = 40
        TwentyPercent = 20

    instance = False

    def __init__(self, la_type_str, *args, **kwargs):
        if Logic.instance:
            raise UserWarning('More than one instance of Logic(Saleae not allowed)')
        
        Logic.instance = True

        super(Logic, self).__init__(Base, *args, **kwargs)

        devices = self.get_connected_devices()

        for d in devices:
            if la_type_str in d.type:
                self.id = str(d)
                self.select_active_device(d.index)
                
        self.set_performance(self.PerformanceOption.OneHundredPercent)
                                                                            
        saleae.log.info("Set performance to full.")

        # Reset touched flag so we can detect use after construction
        self._touched = False

        # The following is a standalone default but can be overridden by property
        if 'win32' in sys.platform:
            self._datastorage_path = 'C:\\Users\\Public\\LogicAnalyzerData\\'
        else:
            self._datastorage_path = '/Users/Public/LogicAnalyzerData/'

        # Force the path to be created
        self.datastorage_path = self.datastorage_path

    # Implement the Logic functions using the Base API

    @property
    def datastorage_path(self):
        return self._datastorage_path
    
    @datastorage_path.setter
    def datastorage_path(self,value):
        if not os.path.exists(value):
            os.mkdir(value) # Exception raised here if invalid for some reason
        if value != self._datastorage_path:
            print(f'[INFO] Data Storage Path for {self.id} changed to {value}')        
        self._datastorage_path = value

    def get_all_sample_rates(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Get available sample rate combinations for the current performance level and channel combination.

        >>> s.get_all_sample_rates()
        [(12000000, 6000000), (12000000, 125000), (12000000, 5000), (12000000, 1000), (12000000, 100), (12000000, 10), (12000000, 0), (6000000, 0), (3000000, 0), (1000000, 0)]
        '''
        rates = self._cmd('GET_ALL_SAMPLE_RATES')
        self.sample_rates = []
        for line in rates.split('\n'):
            if len(line):
                digital, analog = list(map(int, map(str.strip, line.split(','))))
                self.sample_rates.append((digital, analog))
        return self.sample_rates

    def get_bandwidth(self, sample_rate, device = None, channels = None):
        '''Compute USB bandwidth for a given configuration.

        Must supply sample_rate because Saleae API has no get_sample_rate method.

        >>> s.get_bandwidth(s.get_all_sample_rates()[0])
        96000000
        '''
        # From https://github.com/ppannuto/python-saleae/issues/8
        # Bandwidth (bits per second) =
        #   (digital_sample_rate * digital_channel_count) +
        #   (analog_sample_rate * analog_channel_count * ADC_WIDTH)
        #
        # ADC width = 12 bits for Logic 8, Pro 8 and Pro 16.
        # ADC width = 8 bits for logic 4.
        
        if device is None:
            device = self.get_active_device()
        if channels is None:
            digital_channels, analog_channels = self.get_active_channels()
        else:
            digital_channels, analog_channels = channels

        return sample_rate[0] * len(digital_channels) +\
               sample_rate[1] * len(analog_channels) * self.ADC_WIDTH

    def get_performance(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Get performance value. Performance controls USB traffic and quality.

        :returns: A ``saleae.PerformanceOption``

        >>> s.get_performance() #doctest:+SKIP
        <PerformanceOption.Full: 100>
        '''
        try:
            return PerformanceOption(int(self._cmd("GET_PERFORMANCE")))
        except self.CommandNAKedError:
            saleae.log.info("get_performance is only supported when a physical Saleae device is attached if")
            saleae.log.info("                you are testing / do not have a Saleae attached this will fail.")

    def set_performance(self, performance):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set performance value. Performance controls USB traffic and quality.

        :param performance: must be of type saleae.PerformanceOption

        **Note: This will change the sample rate.**

        #>>> s.set_performance(saleae.PerformanceOption.Full)
        '''
        performance = performance
        try:
            self._cmd('SET_PERFORMANCE, {}'.format(performance.value))
        except self.CommandNAKedError:
            saleae.log.info("set_performance is only supported when a physical Saleae device is attached if")
            saleae.log.info("                you are testing / do not have a Saleae attached this will fail.")
 
    def get_capture_pretrigger_buffer_size(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''The number of samples saleae records before the trigger.

        :returns: An integer number descripting the pretrigger buffer size

        >>> s.get_capture_pretrigger_buffer_size() #doctest:+ELLIPSIS
        1...
        '''
        return int(self._cmd('GET_CAPTURE_PRETRIGGER_BUFFER_SIZE'))

    def get_connected_devices(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Get a list of attached Saleae devices.

        Note, this will never be an empty list. If no actual Saleae devices are
        connected, then Logic will return the four fake devices shown in the
        example.

        :returns: A list of ``saleae.ConnectedDevice`` objects

        >>> s.get_connected_devices() #doctest:+ELLIPSIS
        [<saleae.ConnectedDevice #1 LOGIC_4_DEVICE Logic 4 (...) **ACTIVE**>, <saleae.ConnectedDevice #2 LOGIC_8_DEVICE Logic 8 (...)>, <saleae.ConnectedDevice #3 LOGIC_PRO_8_DEVICE Logic Pro 8 (...)>, <saleae.ConnectedDevice #4 LOGIC_PRO_16_DEVICE Logic Pro 16 (...)>]
        '''
        devices = self._cmd('GET_CONNECTED_DEVICES')
        # command response is sometimes not the expected one : a non-empty string starting with a digit (index)
        while ('' == devices or not devices[0].isdigit()):
            time.sleep(0.1)
            devices = self._cmd('GET_CONNECTED_DEVICES')

        self.connected_devices = []
        for dev in devices.split('\n')[:-1]:
            active = False
            try:
                index, name, type, id, active = list(map(str.strip, dev.split(',')))
            except ValueError:
                index, name, type, id = list(map(str.strip, dev.split(',')))
            self.connected_devices.append(ConnectedDevice(type, name, id, index, active))
        return self.connected_devices

    @property
    def simulated(self):
        return self.connected_devices is not None and len(self.connected_devices) > 1


    def get_active_device(self):
        '''Get the current active Saleae device.

        :returns: A ``saleae.ConnectedDevice`` object for the active Saleae

        >>> s.get_active_device() #doctest:+ELLIPSIS
        <saleae.ConnectedDevice #1 LOGIC_4_DEVICE Logic 4 (...) **ACTIVE**>
        '''
        self.get_connected_devices()
        for dev in self.connected_devices:
            if dev.active:
                return dev
        raise NotImplementedError("No active device?")

    def select_active_device(self, device_index):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''
        >>> s.select_active_device(2)
        >>> s.get_active_device() #doctest:+ELLIPSIS
        <saleae.ConnectedDevice #2 LOGIC_8_DEVICE Logic 8 (...) **ACTIVE**>
        >>> s.select_active_device(1)
        '''
        if self.connected_devices is None:
            self.get_connected_devices()
        for dev in self.connected_devices:
            if dev.index == device_index:
                self._cmd('SELECT_ACTIVE_DEVICE, {}'.format(device_index))
                break
        else:
            raise NotImplementedError("Device index not in connected_devices")

    def get_digital_voltage_options(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Get a list of available digital I/O voltage thresholds for the device and the currently active selection.

        This feature is only supported on the original Logic 16, Logic Pro 8,
        and Logic Pro 16.

        >>> s.get_digital_voltage_options() #doctest:+SKIP
        [(0, '1.2 Volts', <DigitalVoltageFlags.Selected: 1>), (1, '1.8 Volts', <DigitalVoltageFlags.NotSelected: 0>), (2, '3.3+ Volts', <DigitalVoltageFlags.NotSelected: 0>)]
        '''
        voltages = self._cmd('GET_DIGITAL_VOLTAGE_OPTIONS')
        self.digital_voltages = []
        for line in voltages.split('\n'):
            if len(line):
                l = line.split(',')
                self.digital_voltages.append((int(l[0]), l[1].strip(), DigitalVoltageFlags.Selected if l[2].strip() == "SELECTED" else DigitalVoltageFlags.NotSelected))
        return self.digital_voltages

    def set_digital_voltage_option(self, index):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set active digital I/O voltage threshold for the device.

        This feature is only supported on the original Logic 16, Logic Pro 8,
        and Logic Pro 16.

        :param index: digital I/O voltage threshold index from the getter function.
        :raises ImpossibleSettings: raised if out of range index is requested
        >>> s.set_digital_voltage_option(0) #doctest:+SKIP
        '''

        self.get_digital_voltage_options()
        for option_index in [option[0] for option in self.digital_voltages]:
            if option_index == index:
                self._cmd('SET_DIGITAL_VOLTAGE_OPTION, {:d}'.format(int(index)))
                return

        raise self.ImpossibleSettings("Digital I/O voltage threshold index out of range")

    def get_active_channels(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Get the active digital and analog channels.

        :returns: A 2-tuple of lists of integers, the active digital and analog channels respectively

        >>> s.get_active_channels()
        ([0, 1, 2, 3], [0])
        '''

        channels = self._cmd('GET_ACTIVE_CHANNELS')
        # Work around possible bug in Logic8
        # https://github.com/ppannuto/python-saleae/pull/19
        while not channels.startswith('digital_channels'):
            time.sleep(0.1)
            channels = self._cmd('GET_ACTIVE_CHANNELS')
        msg = list(map(str.strip, channels.split(',')))
        assert msg.pop(0) == 'digital_channels'
        i = msg.index('analog_channels')
        digital = list(map(int, msg[:i]))
        analog = list(map(int, msg[i+1:]))

        return digital, analog

    def set_active_channels(self, digital=None, analog=None):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set the active digital and analog channels.

        *Note: This feature is only supported on Logic 16, Logic 8(2nd gen),
        Logic Pro 8, and Logic Pro 16*

        :raises ImpossibleSettings: if used with a Logic 4 device
        :raises ImpossibleSettings: if no active channels are given

        >>> s.set_active_channels([0,1,2,3], [0]) #doctest:+SKIP
        '''
        digital_no = 0 if digital is None else len(digital)
        analog_no = 0 if analog is None else len(analog)
        if digital_no <= 0 and analog_no <= 0:
            raise self.ImpossibleSettings('Logic requires at least one activate channel (digital or analog) and none are given')

        self._build('SET_ACTIVE_CHANNELS')
        if digital_no > 0:
            self._build('digital_channels')
            self._build(['{0:d}'.format(ch) for ch in digital])
        if analog_no > 0:
            self._build('analog_channels')
            self._build(['{0:d}'.format(ch) for ch in analog])
        self._finish()

    def activate_all_channels(self):
        ''' activates all DIGITAL channels

        While some logic analyzers can record analog data that is not their intended function
        
        Use an oscilloscope, instead. However, if you must use analog records with this device
        then use the set_active_channels() function, which allows you to partition the channel
        allocation
        '''
        self.set_active_channels(digital=list(range(0,self.NUM_CHANNELS)),analog=[])

    def reset_active_channels(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set all channels to active.

        >>> s.reset_active_channels()
        '''
        self._cmd('RESET_ACTIVE_CHANNELS')

    def set_capture_pretrigger_buffer_size(self, size, round=True):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set the number of samples saleae records before the trigger.

        >>> s.set_capture_pretrigger_buffer_size(1e6)
        '''
        valid_sizes = (1000000, 10000000, 100000000, 1000000000)
        if round:
            size = self._round_up_or_max(size, valid_sizes)
        elif size not in valid_sizes:
            raise NotImplementedError("Invalid size")
        self._cmd('SET_CAPTURE_PRETRIGGER_BUFFER_SIZE, {}'.format(size))

    def set_trigger_one_channel(self, digital_channel, trigger):
        '''Convenience method to set one trigger.

        :param channel: Integer specifying channel
        :param trigger: saleae.Trigger indicating trigger type
        :raises ImpossibleSettings: rasied if channel is not active
        '''
        digital, analog = self.get_active_channels()

        to_set = [self.Trigger.NoTrigger for x in range(len(digital))]
        trigger = self.Trigger(trigger)
        try:
            to_set[digital.index(digital_channel)] = trigger
        except ValueError:
            raise self.ImpossibleSettings("Cannot set trigger on inactive channel")
        self._set_triggers_for_all_channels(to_set)

    def set_triggers_for_all_channels(self, channels):
        '''Set the trigger conditions for all active digital channels.

        :param channels: An array of saleae.Trigger for each channel
        :raises ImpossibleSettings: rasied if configuration is not provided for all channels

        *Note: Calls to this function must always set all active digital
        channels. The Saleae protocol does not currently expose a method to read
        current triggers.*'''

        digital, analog = self.get_active_channels()
        if len(channels) != len(digital):
            raise self.ImpossibleSettings("Trigger settings must set all active digital channels")

        self._set_triggers_for_all_channels(channels)
        
    def set_num_samples(self, samples):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set the capture duration to a specific number of samples.

        :param samples: Number of samples to capture, will be coerced to ``int``

        *From Saleae documentation*
          Note: USB transfer chunks are about 33ms of data so the number of
          samples you actually get are in steps of 33ms.

        >>> s.set_num_samples(1e6)
        '''
        self._cmd('SET_NUM_SAMPLES, {:d}'.format(int(samples)))

    def get_num_samples(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Get the capture duration in samples.

        *From Saleae documentation*
          Note: USB transfer chunks are about 33ms of data so the number of
          samples you actually get are in steps of 33ms.

        >>> s.get_num_samples()
        '''
        return self._cmd('GET_NUM_SAMPLES')

    def set_capture_seconds(self, seconds):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set the capture duration to a length of time.

        :param seconds: Capture length. Partial seconds (floats) are fine.

        >>> s.set_capture_seconds(1)
        '''
        self._cmd('SET_CAPTURE_SECONDS, {}'.format(float(seconds)))

    def set_sample_rate(self, sample_rate_tuple):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Set the sample rate. Note the caveats. Consider ``set_sample_rate_by_minimum``.

        Due to saleae software limitations, only sample rates exposed in the
        Logic software can be used. Use the ``get_all_sample_rates`` method to
        get all of the valid sample rates. The list of valid sample rates
        changes based on the number and type of active channels, so set up all
        channel configuration before attempting to set the sample rate.

        :param sample_rate_tuple: A sample rate as returned from ``get_all_sample_rates``

        >>> s.set_sample_rate(s.get_all_sample_rates()[0])
        '''

        self.get_all_sample_rates()
        if sample_rate_tuple not in self.sample_rates:
            raise NotImplementedError("Unsupported sample rate")

        self._cmd('SET_SAMPLE_RATE, {}, {}'.format(*sample_rate_tuple))

    def set_sample_rate_by_minimum(self, digital_minimum=0, analog_minimum=0):
        '''Set to a valid sample rate given current configuration and a target.

        Because the avaiable sample rates are not known until runtime after all
        other configuration, this helper method takes a minimum digital and/or
        analog sampling rate and will choose the minimum sampling rate available
        at runtime. Setting digital or analog to 0 will disable the respective
        sampling method.

        :param digital_minimum: Minimum digital sampling rate in samples/sec or 0 for don't care
        :param analog_minimum: Minimum analog sampling rate in samples/sec or 0 for don't care
        :returns (digital_rate, analog_rate): the sample rate that was set
        :raises ImpossibleSettings: rasied if sample rate cannot be met

        >>> s.set_sample_rate_by_minimum(1e6, 1)
        (12000000, 10)
        '''

        if digital_minimum == analog_minimum == 0:
            raise self.ImpossibleSettings("One of digital or analog minimum must be nonzero")

        self.get_all_sample_rates()

        # Sample rates may be unordered, iterate all tracking the best
        best_rate = None
        best_bandwidth = None
        for rate in self.sample_rates:
            if digital_minimum != 0 and digital_minimum <= rate[0]:
                if (analog_minimum == 0) or (analog_minimum != 0 and analog_minimum <= rate[1]):
                    if best_rate is None:
                        best_rate = rate
                        best_bandwidth = self.get_bandwidth(sample_rate=rate)
                    else:
                        new_bandwidth = self.get_bandwidth(sample_rate=rate)
                        if new_bandwidth < best_bandwidth:
                            best_rate = rate
                            best_bandwidth = new_bandwidth
            elif analog_minimum != 0 and analog_minimum <= rate[1]:
                if best_rate is None:
                    best_rate = rate
                    best_bandwidth = self.get_bandwidth(sample_rate=rate)
                else:
                    new_bandwidth = self.get_bandwidth(sample_rate=rate)
                    if new_bandwidth < best_bandwidth:
                        best_rate = rate
                        best_bandwidth = new_bandwidth

        if best_rate is None:
            raise self.ImpossibleSettings("No sample rate for configuration. Try lowering rate or disabling channels (especially analog channels)")

        self.set_sample_rate(best_rate)
        return best_rate

    def capture_start(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Start a new capture and immediately return.'''
        self._cmd('CAPTURE', False)

    def capture_start_and_wait_until_finished(self):
        '''Convenience method that blocks until capture is complete.

        >>> s.set_capture_seconds(.5)
        >>> s.capture_start_and_wait_until_finished()
        >>> s.is_processing_complete()
        True
        '''
        self.capture_start()
        while not self.is_processing_complete():
            time.sleep(0.1)

    def is_processing_complete(self, timeout = 0.0):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        starttime = time.perf_counter()
        done = False
        resp = None
        while not done:
            resp = self._cmd('IS_PROCESSING_COMPLETE', expect_nak=True)
            if timeout > 0.0:
                time.sleep(0.100)   # Aproximate 10 Hz polling
            if time.perf_counter() - starttime > timeout:
                done = True

        return False if resp is None else resp.strip().upper() == 'TRUE'

    def capture_stop(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Stop a capture and return whether any data was captured.

        :returns: True if any data collected, False otherwise

        >>> s.set_capture_seconds(5)
        >>> s.capture_start()
        >>> time.sleep(1)
        >>> s.capture_stop()
        True
        '''
    # This seems to cause trouble if processing is not running.  Adding a test.
        if not(self.is_processing_complete()):
            try:
                self._cmd('STOP_CAPTURE')
                return True
            except self.CommandNAKedError:
                return False
        else:
            return True

    def capture_to_file(self, filename):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        if os.path.splitext(filename)[1] == '':
            filename += '.logicdata'

        file_path_on_target_machine = os.path.join(self.datastorage_path, filename)

        # Fix windows path if needed
        file_path_on_target_machine.replace('\\', '/')
        self._cmd('CAPTURE_TO_FILE, ' + os.path.abspath(file_path_on_target_machine))

    def save_to_file(self, filename, timeout = 5.0):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        if self.is_processing_complete(timeout):

            file_path_on_target_machine = os.path.join(self.datastorage_path, filename)

            # Fix windows path if needed
            file_path_on_target_machine.replace('\\', '/')
            self._cmd('SAVE_TO_FILE, ' + os.path.abspath(file_path_on_target_machine))
        else:
            print(f'[WARNING] Unable to Save Data: Processing was not completed')


    def load_from_file(self, filename):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent

        file_path_on_target_machine = os.path.join(self.datastorage_path, filename)

        # Fix windows path if needed
        file_path_on_target_machine.replace('\\', '/')
        self._cmd('LOAD_FROM_FILE, ' + os.path.abspath(file_path_on_target_machine))

    def export_data(self, filename, digital_channels=None, analog_channels=None, time_span=None, format='csv', timeout=5.0, **export_args):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Export command:
            EXPORT_DATA2,
            <filename>,
            [ALL_CHANNELS|SPECIFIC_CHANNELS, [DIGITAL_ONLY|ANALOG_ONLY|ANALOG_AND_DIGITAL], <channel index> [ANALOG|DIGITAL], ..., <channel index> [ANALOG|DIGITAL]],
            [ALL_TIME|TIME_SPAN, <(double)start>, <(double)end>],
            [BINARY, <binary settings>|CSV, <csv settings>|VCD|MATLAB, <matlab settings>]

        >>> s.export_data2('/tmp/test.csv')
        '''

        file_path_on_target_machine = os.path.join(self.datastorage_path, filename)
        print(f'[INFO] Exporting to {file_path_on_target_machine}.{format}')

        if self.is_processing_complete(timeout):

            # NOTE: Note to Saleae, Logic should resolve relative paths, I do not see reasons not to do this ...
            if file_path_on_target_machine[0] in ('~', '.'):
                raise ValueError('File path must be absolute')
            # Fix windows path if needed
            file_path_on_target_machine.replace('\\', '/')

            #Get active channels
            digital_active, analog_active = self.get_active_channels()

            self._build('EXPORT_DATA2')
            self._build(os.path.abspath(file_path_on_target_machine))

            # Channel selection
            is_analog = False
            if (digital_channels is None) and (analog_channels is None):
                self._build('ALL_CHANNELS')
                is_analog = len(self.get_active_channels()[1]) > 0
            else:
                self._build('SPECIFIC_CHANNELS')
                # Check for mixed mode
                # NOTE: This feels redundant, we can see if digital only, analog
                # only or mixed from parsing the channels right?!  especially given
                # the fact that only ANALOG_AND_DIGITAL is printed and never
                # DIGITAL_ONLY or ANALOG_ONLY (according to Saleae C#
                # implementation)
                if len(digital_active) and len(analog_active):
                    if digital_channels is not None and len(digital_channels) and analog_channels is not None and len(analog_channels):
                        self._build('ANALOG_AND_DIGITAL')
                    elif digital_channels is not None and len(digital_channels):
                        self._build('DIGITAL_ONLY')
                    elif analog_channels is not None and len(analog_channels):
                        self._build('ANALOG_ONLY')

                # Add in the channels
                if digital_channels is not None and len(digital_channels):
                    self._build(['{0:d} DIGITAL'.format(ch) for ch in digital_channels])
                if analog_channels is not None and len(analog_channels):
                    self._build(['{0:d} ANALOG'.format(ch) for ch in analog_channels])
                    is_analog = True

            # Time selection
            if time_span is None:
                self._build('ALL_TIME')
            elif len(time_span) == 2:
                self._build(['TIME_SPAN', '{0:f}'.format(time_span[0]), '{0:f}'.format(time_span[1])])
            else:
                raise self.ImpossibleSettings('Unsupported time span')

            # Find exporter
            export_name = '_export_data2_{0:s}_{1:s}'.format('analog' if is_analog else 'digital', format.lower())
            if not hasattr(self, export_name):
                raise NotImplementedError('Unsupported export format given ({0:s})'.format(export_name))

            # Let specific export function handle arguments
            self._build(format.upper())
            getattr(self, export_name)(**export_args)

            self._finish()
            time.sleep(0.5) # HACK: Delete me when Logic (saleae) race conditions are fixed
        else:
            print(f'[WARNING] Unable to Export Data: Processing was not completed')


    def data(self, filename, plotit = True, displayit = False):
        ''' Read filename from datastorage_path and return time and data as arrays for processing
        as digital data.

        Optional arguments to plot and display the data is provided.
        HOWEVER, if the data contains analog information the plotit should be set to False since
        the plotting algorithm, herein, assumes digital data

        Returns:

        t : time values corresponding to each transition point in the data

        data : a list of numpy arrays for each channel recorded.

        NOTE: The data is extracted from an assumed CSV file exported via export_data. The assumed format
        is a time column and a hex numeric for which the least signficant bit is the lowest numbered
        active channel at the time of the recording. This means the caller needs to be aware of which
        channels were recorded.

        NOTE: It is HIGHLY RECOMMENDED to simply make all channels active, record them all and not need
        to worry about which channel number is which bit when few than max channels
        '''
        if '\\' in filename or '/' in filename:
            raise ValueError(f'{filename} must not have path in it (use datastorage_path property)')

        if '.csv' not in filename:
            filename += '.csv'

        filepath = os.path.join(self.datastorage_path,filename)

        t = np.array([])
        data = self.NUM_CHANNELS*[np.array([], dtype='bool')]
        with open(filepath, newline = '') as f:
            reader = csv.reader(f)
            for rowdata in reader:
                if 'Time' in rowdata[0] or 'Data' in rowdata[1]:
                    pass
                else:
                    t = np.append(t, float(rowdata[0]))
                    x = int(rowdata[1], self.NUM_CHANNELS)
                    for channel in range(self.NUM_CHANNELS):
                        data[channel] = np.append(data[channel], ((x >> channel) & 1) == True)
        
        # Verify that t is always increasing
        dt = np.diff(t)
        index_dt_wrong = np.where(dt <= 0)[0]
        if len(index_dt_wrong) > 0:
            raise ValueError(f't must be always increasing: invalid value found near index {index_dt_wrong + 1}')

        if len(t) > 0 and plotit:
            fig,ax = pl.subplots()
            index = 0
            for d in data:
                pl.step(t,d + index, where='post')
                index += 2
            
            # Create labels that are active channels for aligning to bottom
            # edge of each logic range (typically 0..1 offset by 2x the index)
            pl.yticks(list(range(0,self.NUM_CHANNELS*2 - 1, 2)))
            labels = list(range(0,self.NUM_CHANNELS))
            ax.set_yticklabels(labels)
            
            pl.title(filename)
            pl.xlabel('Time (seconds)')
            pl.ylabel('Active Channel Index')

            figfilepath = filepath.replace('.csv','.png')
            print(f'[INFO] Figure saved to {figfilepath}')
            pl.savefig(figfilepath)

            if displayit:
                if os.path.exists(figfilepath):            
                    if platform.system() == 'Darwin':       # macOS
                        subprocess.call(('open', figfilepath))
                    elif platform.system() == 'Windows':    # Windows
                        os.startfile(figfilepath)
                    else:                                   # linux variants
                        subprocess.call(('xdg-open', figfilepath))
                else:
                    print(f'[WARNING] Invalid Path or Filename: Cannot open {figfilepath}')


        return t, data

    def simulate_data(self,filename,t,data):
        ''' creates a user-defined data file that can be recalled using the data() function for plotting
        and analysis. The primary use case is to create data sets that can be used to test analysis logic
        '''
        if self.simulated:
            if '\\' in filename or '/' in filename:
                raise ValueError(f'{filename} must not have path in it (use datastorage_path property)')

            filename += '_simulated'

            if '.csv' not in filename:
                filename += '.csv'

            filepath = os.path.join(self.datastorage_path,filename)

            # Check for data sizing validity
            if len(data) != self.NUM_CHANNELS:
                raise ValueError(f'data of length {len(data)} does not match number of channels {self.NUM_CHANNELS}')

            channel = 0
            for d in data:
                if len(t) != len(d):
                    raise ValueError(f'channel {channel} data length {len(d)} does not match t length {len(t)}')
                channel += 1

            # Verify that t is always increasing
            dt = np.diff(t)
            index_dt_wrong = np.where(dt <= 0)[0]
            if len(index_dt_wrong) > 0:
                raise ValueError(f't must be always increasing: invalid value found near index {index_dt_wrong + 1}')
            
            with open(filepath, mode='w', newline = '') as f:
                writer = csv.writer(f)
                writer.writerow(['Time (s)'] + ['Data (hex)'])
                
                # Assemble hex data for each row
                index = 0
                for trow in t:
                    combined_data = 0
                    channel = 0
                    for d in data:
                        combined_data |= ((d[index] & 1) << channel)
                        channel += 1
                    
                    index += 1

                    writer.writerow([trow] + [hex(combined_data)[2:]])           
        else:
            print('[WARNING] simulate_data called while not simulating Logic Analyzer. No data written')


    def get_analyzers(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Return a list of analyzers currently in use, with indexes.'''
        reply = self._cmd('GET_ANALYZERS')
        self.analyzers = []
        for line in reply.split('\n'):
            if len(line):
                analyzer_name = line.split(',')[0]
                analyzer_index = int(line.split(',')[1])
                self.analyzers.append((analyzer_name, analyzer_index))
        return self.analyzers

    def export_analyzer(self, analyzer_index, save_path, wait_for_processing=True, data_response=False):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''Export analyzer index N and save to absolute path save_path. The analyzer must be finished processing'''
        if wait_for_processing:
            while not self.is_analyzer_complete(analyzer_index):
                time.sleep(0.1)
        self._build('EXPORT_ANALYZER')
        self._build(str(analyzer_index))
        self._build(os.path.abspath(save_path))
        if data_response:
            self._build('data_response')  # any old extra parameter can be used
        resp = self._finish()
        return resp if data_response else None

    def is_analyzer_complete(self, analyzer_index):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        '''check to see if analyzer with index N has finished processing.'''
        self._build('IS_ANALYZER_COMPLETE')
        self._build(str(analyzer_index))
        resp = self._finish()
        return resp.strip().upper() == 'TRUE'

    def close(self):
    #TODO These functions should call functions in saleae that interface with the hardware, to allow changes to the interface
    #to be transparent
        self._cmd('CLOSE_ALL_TABS')

    def find(self, channel_data, value):
        ''' Convenience function for decoding the t,data output from the data() function

        Returns the indices where the data is the value

        USAGE:  indices = logic_analyzer.find(data[SOME_CHANNEL], value)

        Where value is 0 or 1
        '''
        if value != 0 and value != 1:
            raise ValueError('value must be 0 or 1')

        # NOTE: the np.where() function returns a tuple, the first element of which is the index array
        return np.where(channel_data == value)[0]

    def boolean(self, channel_data):
        ''' Convert channel data into Boolean value for easier logic checks in some cases
        '''
        retval = np.array(len(channel_data)*[False])
        index = np.where(channel_data == 1)[0]
        if len(index):
            retval[index] = True

        return retval

    def find_first(self, channel_data, value):
        ''' Convenience function for decoding the t,data output from the data() function

        Returns the index of the first occurence of value

        USAGE:  index_first = logic_analyzer.find_first(data[SOME_CHANNEL], value)

        Where value is 0 or 1
        '''
        if value != 0 and value != 1:
            raise ValueError('value must be 0 or 1')

        # NOTE: the np.where() function returns a tuple, the first element of which is the index array
        return np.where(channel_data == value)[0][0]

    def find_last(self, channel_data, value):
        ''' Convenience function for decoding the t,data output from the data() function

        Returns the index of the last occurence of value
    
        NOTE: The index returned is actualy +1 from the last actual value match because the
        data is assumed to be stored on-change-only meaning that the "last" value is epsilon
        before the index returned here. It is accurate to within the sample rate of the device.

        USAGE:  index_last = logic_analyzer.find_last(data[SOME_CHANNEL], value)

        Where value is 0 or 1
        '''
        if value != 0 and value != 1:
            raise ValueError('value must be 0 or 1')

        # NOTE: the np.where() function returns a tuple, the first element of which is the index array
        # NOTE: The data is assumed to store transitions, only, so the last occurence is actually +1
        # where the transition is noted
        index_last = np.where(channel_data == value)[0][-1] + 1
        if index_last >= len(channel_data):
            index_last = 0    # Rolloever
            print(f'[WARNING] find_last index overruns channel_data: returning 0')
        return index_last

    def find_transitions(self, channel_data):
        ''' Convenience function for decoding the t,data output from the data() function

        Returns the indices of every transition in the data
    
        NOTE: The indices returned are actualy +1 from the last actual value match because the
        data is assumed to be stored on-change-only meaning that the "last" value is epsilon
        before the index returned here. It is accurate to within the sample rate of the device.

        USAGE:  transition_indices = logic_analyzer.find_transitions(data[SOME_CHANNEL])
        '''
        datadiff = np.diff(channel_data)
        index_trans = np.where(datadiff != 0)[0] + 1

        # NOTE: No worry about index out of bounds since diff is always -1 in length
        return index_trans            

    def isBounced(self, channel_data):
        return self.is_bounced(channel_data)

    def is_bounced(self, channel_data):
        ''' Convenience function for decoding the t,data output from the data() function

        Returns true if the number of transition in the channel data is > 2
    
        USAGE:  result = logic_analyzer.isBounced(data[SOME_CHANNEL])
        '''
        return len(self.find_transitions(channel_data)) > 2

class Logic4(Logic):
    USB_PID = '1003'
    ADC_WIDTH=8
    NUM_CHANNELS=4

    def __init__(self,*args, **kwargs):
        super(Logic8, self).__init__("LOGIC_4_DEVICE", *args, **kwargs)

class Logic8(Logic):
    USB_PID = '1004'
    ADC_WIDTH=12
    NUM_CHANNELS=8

    def __init__(self,*args, **kwargs):
        super(Logic8, self).__init__("LOGIC_8_DEVICE", *args, **kwargs)

class LogicPro8(Logic):
    USB_PID = '1005'
    ADC_WIDTH=12
    NUM_CHANNELS=8

    def __init__(self,*args, **kwargs):
        super(LogicPro8, self).__init__("LOGIC_PRO_8_DEVICE", *args, **kwargs)

class LogicPro16(Logic):
    USB_PID = '1006'
    ADC_WIDTH=12
    NUM_CHANNELS=16
    
    def __init__(self,*args, **kwargs):
        super(LogicPro16, self).__init__("LOGIC_PRO_16_DEVICE", *args, **kwargs)
