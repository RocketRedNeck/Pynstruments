# Base class for all Analyzers to help guide a common API
# Each brand will be different in syntax but the core functionality will be the same

import enum
import os

class Analyzer:     # This class provides the suggested API for all logic analyzers

    @staticmethod
    def create_type(interface_type):
        ''' type factory - since the classes derived from Analyzer need a backend API
        this factory allows the API to be injected as the base class for the Analyzer
        class, thus passing the API to the derived classes while also making the
        suggest Analyzer API the suggested interface design in the correct order

        This creates:
            class Analyzer(interface_type)

            where interface_type is a backend API class (e.g., scpi.Device or saleae.Device)

        The derived class must be defined as follows:

            from instruments import Analyzer

            Base = Analyzer.create_type(interface_type)

            class DerivedAnalyzer(Base)
        '''
        # Re-define the Analyzer to be derived from the Saleae API
        return type('Analyzer', (interface_type,), dict(Analyzer.__dict__)) 

    def __init__(self, basetype, *args, **kwargs):
        '''
        : basetype : is the results of calling Base = Analyzer.create_type(interface_type)
                     The derived class is defined as class DerivedAnalyzer(Base)
        '''
        super(basetype, self).__init__( *args, **kwargs)

        self._datastorage_path = '.' # Common default for all analyzers
        
    @property
    def datastorage_path(self):
        return self._datastorage_path
    
    @datastorage_path.setter
    def datastorage_path(self,value):
        if not os.path.exists(value):
            os.mkdir(value) # Exception raised here if invalid for some reason
        
        self._datastorage_path = value

    # TODO: Fill in common API for all logic anlyzers
    class Trigger(enum.IntEnum):
        '''Trigger types to start sampling.'''
        # Python convention is to start enums at 1 for truth checks, but it
        # seems reasonable that no trigger should compare as false
        NoTrigger = 0
        High = 1
        Low = 2
        Posedge = 3
        Negedge = 4

    def get_active_channels(self):
        '''Get the active digital and analog channels.

        :returns: A 2-tuple of lists of integers, the active digital and analog channels respectively

        >>> s.get_active_channels()
        ([0, 1, 2, 3], [0])
        '''
        raise NotImplementedError

    def set_active_channels(self, digital=None, analog=None):
        '''Set the active digital and analog channels.

        :raises ImpossibleSettings: if no active channels are given

        >>> s.set_active_channels([0,1,2,3], [0]) #doctest:+SKIP
        '''
        raise NotImplementedError

    def reset_active_channels(self):
        '''Set all channels to active.

        >>> s.reset_active_channels()
        '''
        raise NotImplementedError

    def set_triggers_for_all_channels(self, channels):
        '''Set the trigger conditions for all active digital channels.

        :param channels: An array of Trigger for each channel
        :raises ImpossibleSettings: rasied if configuration is not provided for all channels

        *Note: Calls to this function must always set all active digital
        channels. The Saleae protocol does not currently expose a method to read
        current triggers.*'''

        raise NotImplementedError

    def set_trigger_one_channel(self, digital_channel, trigger):
        '''Convenience method to set one trigger.

        :param channel: Integer specifying channel
        :param trigger: Trigger indicating trigger type
        :raises ImpossibleSettings: rasied if channel is not active
        '''
        raise NotImplementedError

    def set_num_samples(self, samples):
        '''Set the capture duration to a specific number of samples.

        :param samples: Number of samples to capture, will be coerced to ``int``

        *From Saleae documentation*
          Note: USB transfer chunks are about 33ms of data so the number of
          samples you actually get are in steps of 33ms.

        >>> s.set_num_samples(1e6)
        '''
        raise NotImplementedError

    def get_num_samples(self):
        '''Get the capture duration in samples.

        *From Saleae documentation*
          Note: USB transfer chunks are about 33ms of data so the number of
          samples you actually get are in steps of 33ms.

        >>> s.get_num_samples()
        '''
        raise NotImplementedError

    def set_capture_seconds(self, seconds):
        '''Set the capture duration to a length of time.

        :param seconds: Capture length. Partial seconds (floats) are fine.

        >>> s.set_capture_seconds(1)
        '''
        raise NotImplementedError

    def set_sample_rate(self, sample_rate_tuple):
        '''Set the sample rate. Note the caveats. Consider ``set_sample_rate_by_minimum``.

        Due to saleae software limitations, only sample rates exposed in the
        Logic software can be used. Use the ``get_all_sample_rates`` method to
        get all of the valid sample rates. The list of valid sample rates
        changes based on the number and type of active channels, so set up all
        channel configuration before attempting to set the sample rate.

        :param sample_rate_tuple: A sample rate as returned from ``get_all_sample_rates``

        >>> s.set_sample_rate(s.get_all_sample_rates()[0])
        '''
        raise NotImplementedError

    def set_capture_pretrigger_buffer_size(self, size, round=True):
        '''Set the number of samples saleae records before the trigger.

        >>> s.set_capture_pretrigger_buffer_size(1e6)
        '''
        raise NotImplementedError

    def capture_start(self):
        '''Start a new capture and immediately return.'''
        raise NotImplementedError

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

        raise NotImplementedError

    def save_to_file(self, file_path_on_target_machine):
        raise NotImplementedError

    def load_from_file(self, file_path_on_target_machine):
        raise NotImplementedError

    def is_processing_complete(self):
        resp = self._cmd('IS_PROCESSING_COMPLETE', expect_nak=True)
        if resp is None:
            return False
        return resp.strip().upper() == 'TRUE'

        raise NotImplementedError

    def capture_stop(self):
        '''Stop a capture and return whether any data was captured.

        :returns: True if any data collected, False otherwise

        >>> s.set_capture_seconds(5)
        >>> s.capture_start()
        >>> time.sleep(1)
        >>> s.capture_stop()
        True
        '''
        raise NotImplementedError

    def export_data(self, *args, **kargs):
        raise NotImplementedError

    def capture_to_file(self, file_path_on_target_machine):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
