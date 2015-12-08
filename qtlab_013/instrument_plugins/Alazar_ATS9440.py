#  -*- coding: utf-8 -*-
# Alazar_ATS9440 class
# Gabriele de Boo <ggdeboo@gmail.com>, 2015
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
from lib.dll_support import alazar
import types
import logging
import socket
from numpy import zeros, uint8, frombuffer, float32
import struct
import sys

class Alazar_ATS9440(Instrument):
    '''
    This is the python driver for the Alazar ATS9440 125 MSa/s Digitizer
   
    '''
    def __init__(self, name):
        '''
        Initializes the Alazar ATS9440 Digitizer.

        Input:
            name (string)    : name of the instrument

        Output:
            Non
        '''
        Instrument.__init__(self, name, tags=['physical'])
        logging.debug(__name__ + ' : Initializing instrument')
        
        self._handle = alazar.get_boardID()
        self._memsize, self._bitdepth = alazar.get_channel_info(self._handle)

        # timebase
        self.add_parameter('clock_source',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list = ('internal',
                           'external fast',
                           'external slow',
                           'external 10MHz'),
            )
        self.add_parameter('sample_rate',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            option_list = (1000, 2000, 5000, 10000, 20000, 50000, 100000,
                            200000, 500000, 1000000, 2000000, 5000000,
                            10000, 20000000, 50000000,
                            100000000, 125000000 ),
            units='Sa/s')

        # trigger
        self.add_parameter('trigger_source1',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list = ('A', 'B', 'C', 'D', 'external', 'disable'), 
            )
        self.add_parameter('trigger_source2',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list = ('A', 'B', 'C', 'D', 'external', 'disable'), 
            )
        self.add_parameter('trigger_timeout',
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
            type=types.FloatType,
            minval=0.0,
            units='s',
            )
        self.add_parameter('trigger_delay',
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
            type=types.FloatType,
            minval=0.0,
            units='s',
            )

        self.add_parameter('records_per_acquisition',
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
            type=types.IntType,
            )
        self.add_parameter('samples_per_record',
            flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
            type=types.IntType,
            minval=1,
            maxval=134205440, # extended memory option
            )
        self.add_parameter('pre_trigger_samples',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            minval=0,
            ) 

        # channel parameters
        self.add_parameter('coupling',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            channels=(1,4),
            channel_prefix='ch%i_',
            option_list=('AC','DC'))
        self.add_parameter('range',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=(1,4),
            channel_prefix='ch%i_',
            units='V',
            option_list=(.1, .2, .4, 1.0, 2.0, 4.0) ,
            )

#        self.add_parameter('pre_trigger_samples',
#            flags=Instrument.FLAG_GET,  
#            type=types.IntType,
#            minval=0)

        # measure parameters
#        self.add_function(set_defaults)

        self._trigger_source1 = 'disable'
        self._trigger_source2 = 'disable'
        self._ch_coupling = ['DC'] * 4
        self._ch_range = [4.] * 4
        self._sample_rate = 125000000
        self._clock_source = 'internal'
        self._pre_trigger_samples = 0
        self.set_defaults()

        self.get_all()

    # Functions

    def get_all(self):
        logging.debug(__name__ + ' : Get all.')

    def set_defaults(self):
#        self.set_clock_source('internal')
        self.set_sample_rate(125000000)
        self.set_trigger_source1('disable')
        self.set_trigger_source2('disable')
        self.set_trigger_timeout(1e-5)
        self.set_trigger_delay(0.0)
        self.set_records_per_acquisition(1)
        self.set_samples_per_record(1024)
        for channel in range(1,5):
            self.set('ch%i_coupling' % channel, 'DC')
            self.set('ch%i_range' % channel, 4.0)

    def do_set_clock_source(self, clock_source):
        self._clock_source = clock_source
        sample_rate = self.get_sample_rate()
        alazar.set_clock_source(self._handle,
                                sample_rate,
                                clock_source)

    def do_get_clock_source(self):
        return self._clock_source

    def do_set_sample_rate(self, sample_rate):
        '''Get the sample rate'''
        logging.debug(__name__ + ' : Setting the sample rate')
        self._sample_rate = sample_rate
        clock_source = self.get_clock_source()
        alazar.set_clock(self._handle,
                         sample_rate,
                         clock_source)

    def do_get_sample_rate(self):
        return self._sample_rate

    def do_set_samples_per_record(self, samples):
        '''Set the number of samples per record'''
        logging.debug(__name__ + ' : Setting the number of samples per ' +
                        'to %i.' % samples)
        if samples < self.get_pre_trigger_samples():
            raise ValueError('Number of samples has to be bigger than number' +
                            ' of pre trigger samples')
        status, real_pre, real_post = alazar.set_record_size(self._handle, 
                               self.get_pre_trigger_samples(),
                               samples - self.get_pre_trigger_samples())
        self._real_pre_trig_samples = real_pre
        print('Real pre is %i ' % real_pre)
        self._real_post_trig_samples = real_post
        print('Real post is %i ' % real_post)

    def do_get_pre_trigger_samples(self):
        return self._pre_trigger_samples
     
    def do_set_pre_trigger_samples(self, pre_trigger_samples):
        self._pre_trigger_samples = pre_trigger_samples

    def do_set_records_per_acquisition(self, records):
        alazar.set_records_per_capture(self._handle, records)

    def do_set_trigger_delay(self, delay):
        '''
            Set the time following a trigger event before the trigger sample
            is acquired.
        '''
        alazar.set_trigger_delay(self._handle, 
                                 self.get_sample_rate(),
                                 delay)

    def do_set_trigger_timeout(self, timeout):
        '''Set the trigger timeout'''
        alazar.set_trigger_timeout(self._handle, timeout)

    def do_set_trigger_source1(self, trg_source1):
        '''
        Set the trigger source.
        '''
        logging.debug(__name__ + ' : Set the trigger source to %s.' 
                        % trg_source1)
        self._trigger_source1 = trg_source1
        trg_source2 = self.get_trigger_source2()
        alazar.set_trigger(self._handle,
                           source1=trg_source1, 
                           source2=trg_source2)

    def do_set_trigger_source2(self, trg_source2):
        '''
        Set the trigger source.
        '''
        logging.debug(__name__ + ' : Set the trigger source to %s.' 
                        % trg_source2)
        self._trigger_source2 = trg_source2
        trg_source1 = self.get_trigger_source1()
        alazar.set_trigger(self._handle,
                           source1=trg_source1, 
                           source2=trg_source2)

    def do_get_trigger_source1(self):
        return self._trigger_source1

    def do_get_trigger_source2(self):
        return self._trigger_source2

    def do_set_coupling(self, coupling, channel):
        '''Set the coupling of an digitizer channel.'''
        logging.debug(__name__ +
            ' : Set the coupling of digitizer channel %i to %s' 
            % (channel, coupling))
        channel_range = self.get('ch%i_range' % channel)
        alazar.set_input_channel_parameters(self._handle,
                                    self._channel_number_to_letter(channel),
                                    coupling,
                                    channel_range)

    def do_get_coupling(self, channel):
        return self._ch_coupling[channel-1]

    def do_set_range(self, channel_range, channel):
        '''Set the range of the digitizer channel.'''
        logging.debug(__name__ +
            ' : Set the range of the digitizer channel %i' % channel)
        self._ch_range[channel-1] = channel_range
        coupling = self.get('ch%i_coupling' % channel)
        alazar.set_input_channel_parameters(self._handle,
                                    self._channel_number_to_letter(channel),
                                    coupling,
                                    channel_range)

    def do_get_range(self, channel):
        return self._ch_range[channel-1]

    def fetch_data(self, channel, raw=False):
        '''Fetch the data from the specified channel
           returns a numpy Float32 array
        '''
        if alazar.is_busy(self._handle):
            while alazar.is_busy(self._handle):
                sys.stdout.write('\rWaiting for digitizer...')
                qt.msleep(0.1)
            sys.stdout.write('\rAcquisition finished.\n')

        offset = - self.get_pre_trigger_samples()
        print('offset is %i ' % offset)
        real_total_samples = self.get_samples_per_record()  

        data = alazar.read(self._handle, 
                           self._channel_number_to_letter(channel),
                           0,
                           real_total_samples,
                           offset, 
                            )
        input_range = self.get('ch%i_range' % channel)
        
        if raw:
            return data
        else:
#            output_data = zeros(data.shape, dtype=float32)
#            for idx in range(len(data)):
#                output_data[idx] = (data[idx] - 2**15) * input_range
#            return output_data
            return (float32(data) - 2**15)/2**16 * input_range

    def start_acquisition(self):
        alazar.start_capture(self._handle)

    def _channel_number_to_letter(self, ch_number):
        if ch_number == 1:
            return 'A'
        if ch_number == 2:
            return 'B'
        if ch_number == 3:
            return 'C'
        if ch_number == 4:
            return 'D'
