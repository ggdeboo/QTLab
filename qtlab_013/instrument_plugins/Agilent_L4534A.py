#  -*- coding: utf-8 -*-
# Agilent_L4534A class, to perform the communication between the Wrapper and the device
# Gabriele de Boo <ggdeboo@gmail.com>, 2015
# Chunming Yin <c.yin@unsw.edu.au>, 2017
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
import visa
import types
import logging
import socket
from numpy import zeros, uint8, frombuffer, float32, mean, arange
import struct
from time import time, sleep

class Agilent_L4534A(Instrument):
    '''
    This is the python driver for the Agilent L4534A 20 MSa/s Digitizer
   
    '''
    def __init__(self, name, address):
        '''
        Initializes the Agilent L4534A Digitizer.

        Input:
            name (string)    : name of the instrument
            address (string) : VICP address

        Output:
            Non
        '''
        Instrument.__init__(self, name, tags=['physical'])
        logging.debug(__name__ + ' : Initializing instrument')
        
        self._address = address
        rm = visa.ResourceManager()
        self._visainstrument = rm.open_resource(self._address)
        self._visainstrument.write_termination = '\n'
        #self._visainstrument.read_termination = '\n'
        self._idn = self._visainstrument.query('*IDN?')
        self._model = self._idn.split(',')[1]
        self._serialnumber = self._idn.split(',')[2]

        # timebase
        self.add_parameter('reference_oscillator',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            format_map={'INT'   :   'internal',
                        'EXT'   :   'external',
                        }
            )

        # trigger
        self.add_parameter('trigger_source',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            format_map={'IMM'   : 'immediate',
                        'SOFT'  : 'software',
                        'EXT'   : 'external',
                        'CHAN'  : 'channel',
                        'OR'    : 'or'}
            )
        self.add_parameter('arm_source',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            format_map={'IMM'   : 'immediate',
                        'SOFT'  : 'software',
                        'EXT'   : 'external',
                        'TIM'   : 'timer',
                        }
            )
        self.add_parameter('triggers_per_arm',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            )
        self.add_parameter('records_per_acquisition',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
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
            channels=(1,2,3,4),
            channel_prefix='ch%i_',
            units='V',
            option_list=(.25, .5, 1.0, 2.0, 4.0, 8.0, 
                            16.0, 32.0, 128.0, 256.0),
            )
        self.add_parameter('filter',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            channels=(1,2,3,4),
            channel_prefix='ch%i_',
            option_list=('LP_200_kHz',  'LP_2_MHz', 'LP_20_MHz')
            )
        self.add_parameter('channel_trigger',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            channels=(1,2,3,4),
            channel_prefix='ch%i_',
            format_map={'EDGE'   : 'edge',
                        'WIND'  : 'window',
                        'OFF'   : 'off',
                        }
            )
        self.add_parameter('edge_trigger_level',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            channels=(1,2,3,4),
            channel_prefix='ch%i_',
            units='V',
            )
        self.add_parameter('edge_trigger_slope',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            channels=(1,2,3,4),
            channel_prefix='ch%i_',
            format_map={'POS'   : 'positive',
                        'NEG'   : 'negative',
                        }
            )
            
        self.add_parameter('sample_rate',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            option_list=(1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000,
                        500000, 1000000, 2000000, 5000000, 10000000, 20000000),
            units='Sa/s',
            )
        self.add_parameter('samples_per_record',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            minval=1,
            maxval=134205440, # extended memory option
            )
        self.add_parameter('pre_trigger_samples',
            flags=Instrument.FLAG_GETSET,  
            type=types.IntType,
            minval=0)
        self.add_parameter('trigger_delay',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=0.0, maxval=3600.0,
            units='s',
            )
        self.add_function('fetch_data')
        self.add_function('fetch_records')
        self.add_function('start_acquisition')
        self.add_function('start_acquisition_wait')
        self.add_function('acquisition_status')
        self.add_function('reset')
        self.add_function('get_error_message')
        self.add_function('abort')
        self.add_function('completion_status')
        self.add_function('send_trigger')
        self.add_function('protection_off_all')
        self.add_function('channel_trigger_off_all')
        self.get_all()
        print('Agilent %s with serial number %s has been initialized.' 
                % (self._model, self._serialnumber))

    # Functions

    def get_all(self):
        logging.debug(__name__ + ' : Get all.')
        self.get_reference_oscillator()
        self.get_trigger_source()
        self.get_arm_source()
        self.get_triggers_per_arm()
        self.get_records_per_acquisition()
        self.get_sample_rate()
        self.get_samples_per_record()
        self.get_pre_trigger_samples()
        self.get_trigger_delay()

        for channel in range(1,5):
            self.get('ch%i_coupling' % channel)
            self.get('ch%i_range' % channel)
            self.get('ch%i_filter' % channel)
            self.get('ch%i_channel_trigger' % channel)
            self.get('ch%i_edge_trigger_level' % channel)
            self.get('ch%i_edge_trigger_slope' % channel)
            

    def do_get_reference_oscillator(self):
        '''Query whether the internal or external oscillator is used'''
        response = self._visainstrument.query('CONF:ROSC?')
        return response

    def do_get_sample_rate(self):
        '''Get the sample rate'''
        logging.debug(__name__ + ' : Getting the sample rate')
        response = self._visainstrument.query('CONF:ACQ:SRAT?')
        return int(response)

    def do_set_sample_rate(self, sample_rate):
        '''Get the sample rate'''
        logging.debug(__name__ + ' : Setting the sample rate')
        self._visainstrument.write('CONF:ACQ:SRAT %.1e' % sample_rate)

    def do_get_samples_per_record(self):
        '''Get the number of samples per record'''
        logging.debug(__name__ + ' : Getting the samples per record')
        response = self._visainstrument.query('CONF:ACQ:SCO?')
        return int(response)

    def do_set_samples_per_record(self, samples):
        '''Set the number of samples per record'''
        logging.debug(__name__ + ' : Setting the number of samples per ' +
                        'to %i.' % samples)
        self._visainstrument.write('CONF:ACQ:SCO %i' % samples) 

    def do_get_pre_trigger_samples(self):
        '''Get the number of pre-trigger samples per record'''
        response = self._visainstrument.query('CONF:ACQ:SPR?')
        return int(response)
        self.add_function('send_trigger')
    def do_set_pre_trigger_samples(self, pre_samples=0):
        '''Get the number of pre-trigger samples per record'''
        self._visainstrument.write('CONF:ACQ:SPR %i' % pre_samples)

    def do_get_trigger_delay(self):
        '''
            Get the time following a trigger event before the trigger sample
            is acquired.
        '''
        response = self._visainstrument.query('CONF:ACQ:TDEL?')
        return float(response)

    def do_set_trigger_delay(self, delay):
        '''
            Set the time following a trigger event before the trigger sample
            is acquired.
        '''
        self._visainstrument.write('CONF:ACQ:TDEL %e' % delay)

    def do_get_trigger_source(self):
        '''Get the trigger source.'''
        logging.debug(__name__ + ' : Get the trigger source')
        response = self._visainstrument.query('CONF:TRIG:SOUR?')
        return response

    def do_get_arm_source(self):
        '''Get the arm source.'''
        logging.debug(__name__ + ' : Get the arm source')
        response = self._visainstrument.query('CONF:ARM:SOUR?')
        return response.split(',')[0]

    def do_set_arm_source(self, source):
        '''Set the arm source.'''
        self._visainstrument.write('CONF:ARM:SOUR %s' % source)

    def do_get_triggers_per_arm(self):
        '''Get the number of triggers per arm. Default 1024'''
        logging.debug(__name__ + ' : Get the triggers per arm.')
        response = self._visainstrument.query('CONF:ARM:SOUR?')
        return response.split(',')[1]

    def do_get_records_per_acquisition(self):
        '''Get the number of records per acquisition.
            An acquisition is started after the INITiate command.
            Each record requires a trigger. 

            Default value: 1
        '''
        logging.debug(__name__ + ' : Get the number of records per aqcuisition.')
        response = self._visainstrument.query('CONF:ACQ:REC?')
        return response
    
    def do_set_records_per_acquisition(self, num_records):
        '''Set the number of records per acquisition.
            An acquisition is started after the INITiate command.
            Each record requires a trigger. 

            Default value: 1
        '''
        logging.debug(__name__ + ' : Set the number of records per aqcuisition.')
        response = self._visainstrument.write('CONF:ACQ:REC %i' % num_records)
        return response
    
    def do_set_trigger_source(self, trg_source):
        '''
        Set the trigger source.
            IMM     : immediate
            SOFT    : software
            EXT     : external
            CHAN    : channel
            OR      : or
        '''
        logging.debug(__name__ + ' : Set the trigger source to %s.' 
                        % trg_source)
        self._visainstrument.write('CONF:TRIG:SOUR %s' % trg_source)

    def do_get_coupling(self, channel):
        '''Get the coupling of an digitizer channel.'''
        logging.debug(__name__ +
            ' : Get the coupling of digitizer channel %i' % channel)
        response = self._visainstrument.query('CONF:CHAN:COUP? (@%s)' % channel)
        return response

    def do_set_coupling(self, coupling, channel):
        '''Set the coupling of an digitizer channel.'''
        logging.debug(__name__ +
            ' : Set the coupling of digitizer channel %i to %s' 
            % (channel, coupling))
        self._visainstrument.write('CONF:CHAN:COUP (@%s), %s' % 
                                    (channel, coupling))

    def do_get_range(self, channel):
        '''Get the range of the digitizer channel.'''
        logging.debug(__name__ +
            ' : Get the range of digitizer channel %i' % channel)
        response = self._visainstrument.query('CONF:CHAN:RANG? (@%i)' % channel)
        # The scale determines the bounds for several other parameters.
        return float(response)
        self.add_function('send_trigger')
    def do_set_range(self, channel_range, channel):
        '''Set the range of the digitizer channel.'''
        logging.debug(__name__ +
            ' : Set the range of the digitizer channel %i' % channel)
        self._visainstrument.write('CONF:CHAN:RANG (@%i), %.1f' 
                                % (channel, channel_range))

    def do_get_filter(self, channel):
        logging.debug(__name__ +
            ' : Get the filter on channel %i' % channel)
        response = self._visainstrument.query('CONF:CHAN:FILT? (@%i)' % channel)
        return response

    def do_set_filter(self, filter_type, channel):
        '''Set the filter of the digitizer channel.
            LP_200_KHZ
            LP_2_MHZ
            LP_20_MHZ'''
        logging.debug(__name__ +
            ' : Set the filter type on channel %i to %s' % (channel, filter_type))
        self._visainstrument.write('CONF:CHAN:FILT (@%i), %s' 
            % (channel, filter_type))

    def do_get_channel_trigger(self, channel):
        '''
        Get the channel trigger configuration for the channel trigger mode
        '''
        response = self._visainstrument.query('CONF:TRIG:SOUR:CHAN? (@%i)' %
                                            channel)
        return response

    def do_get_edge_trigger_level(self, channel):
        '''
        Get the level for the edge trigger mode on the specified channel
        '''
        response = self._visainstrument.query('CONF:TRIG:SOUR:CHAN:EDGE? (@%i)' 
                                            % channel)
        return float(response.split(',')[0])

    def set_channel_edge_trigger(self, channel, edge_level, edge_slope = 'POS',
        edge_hysteresis = 2.0 ):
        '''
        set the trigger level of channel x to edge_level, triggering slope to 
        edge_slope, and with edge_hysteresis.
        channel = 1|2|3|4
        edge_level = float (V)
        'EDGE'   : 'edge'
        'WIND'  : 'window',
        'OFF'   : 'off',
        [edge_slope = 'POS'|'NEG', default = 'POS']
        [edge_hysteresis = 0.0-100.0, default = 2.0]
        '''
        logging.debug(__name__+
            ' : Set the channel edge_trigger_level on channel %i to %.f'
            % (channel, edge_level))
        self._visainstrument.write(
            'CONF:TRIG:SOUR:CHAN:EDGE (@%i), %f, %s, %f ' 
            % (channel, edge_level, edge_slope, edge_hysteresis))
    def channel_trigger_off_all(self):
        '''
        turn off channel trigger for all channels.
        '''
        self._visainstrument.write('CONF:TRIG:SOUR:CHAN:OFF (@1:4)')
    def do_get_edge_trigger_slope(self, channel):
        '''
        Get the slope for the edge trigger mode on the specified channel
        '''
        response = self._visainstrument.query('CONF:TRIG:SOUR:CHAN:EDGE? (@%i)' 
                                            % channel)
        return response.split(',')[1]


    def fetch_data(self, channel, average=False, raw=False):
        '''Fetch the data from the specified channel
           returns a numpy Float32 array
        '''
        # check whether data is available
        if self._visainstrument.query('STAT:OPER:COND? MTHR').split('\n')[0] == u'+1':
            preamble = self._visainstrument.query('FETC:WAV:ACQ:PRE?').split(',')
            n_samples = int(preamble[1])
            data_array = zeros(n_samples, dtype=float32)
            dig_range = self.get('ch%i_range' % channel)
            self._visainstrument.write('FETC:WAV:ADC? (@{0})'.format(channel))
            sleep(2)
            data = self._visainstrument.read_raw()[:-1]
            # ADC16 format from the digitizer, to convert use struct.unpack
            if data.startswith('#'):
                header_length = int(data[1])
                data_array[:] =  struct.unpack('>%ih' % n_samples, 
                                    data[2+header_length:-1])
                if average:
                    return mean(dig_range * data_array / 32767.0)
                else:
                    return (dig_range * data_array / 32767.0)
            else:
                logging.warning('wrong response to FETC:WAV:ADC? (@%i)' %
                                channel)
        else:
            # TODO build check whether acquisition is in process
            logging.warning('No data available on digitizer, ' + 
                            'did the acquisition start?')

    def fetch_records(self, channel, records_tofetch, record_start = 1, average=False):
        '''Function added by Chunming in 2016 to read mutiple records from the digitizer.
           Fetch records_tofetch records of data from the specified channel
           returns a numpy Float32 2D array
        '''
        # check whether data is available
        if self._visainstrument.query('STAT:OPER:COND? MTHR').split('\n')[0] == u'+1':
            pre_trig_length = self.get_pre_trigger_samples()
            preamble = self._visainstrument.query('FETC:WAV:ACQ:PRE?').split(',')
            number_records = int(preamble[0])
            record_end = records_tofetch + record_start -1
            if record_end > number_records:
                logging.warning('Number of records to fetch exceed the total length of records.')
                return'ERROR! Number of records to fetch exceed the total length of records.'
            n_samples = int(preamble[1])
            dig_range = self.get('ch%i_range' % channel)
            #data = self._visainstrument.query_binary_values('FETC:WAV:ADC? (@{0}),-{1},{2},(@{3}:{4})'.format(channel,pre_trig_length,n_samples,record_start,record_end),datatype='d')
            self._visainstrument.write('FETC:WAV:ADC? (@{0}),-{1},{2},(@{3}:{4})'.format(channel,pre_trig_length,n_samples,record_start,record_end))
            sleep(2)
            data = self._visainstrument.read_raw()[:-1]
            # ADC16 format from the digitizer, to convert use struct.unpack
            if data.startswith('#'):
                header_length = int(data[1])
                dat_tmp = zeros(records_tofetch*n_samples,dtype=float32)
                dat_tmp[:] =  struct.unpack('>%ih' % (records_tofetch*n_samples), data[2+header_length:])
                dat_raw = dig_range*dat_tmp/32767.0
                if average:
                    data_array = zeros(records_tofetch, dtype=float32)
                    for idx in arange(records_tofetch):
                        data_array[idx] = mean(dat_raw[idx*n_samples:(idx+1)*n_samples])
                else:
                    data_array = zeros((records_tofetch, n_samples), dtype=float32)
                    for idx in arange(records_tofetch):
                        data_array[idx,:] = dat_raw[idx*n_samples:(idx+1)*n_samples]
                return data_array
            else:
                logging.warning('wrong response to FETC:WAV:ADC? (@%i)' %
                                channel)
        else:
            # TODO build check whether acquisition is in process
            logging.warning('No data available on digitizer, ' + 
                            'did the acquisition start?')

    def start_acquisition(self):
        self._visainstrument.write('INIT')

    def start_acquisition_wait(self, wait_time = 10):
        self._visainstrument.write('INIT')
        start_time = time()
        while time()- start_time < wait_time and self._visainstrument.query('STAT:OPER:COND? MTHR') != u'+1':
            sleep(0.01)

    def acquisition_status(self):
        status = self._visainstrument.query('STAT:OPER:COND? MTHR')
        if status.split('\n')[0] == u'+1':
            return True
        else:
            return False

    def completion_status(self):
        '''
        Acquisition completion status.

        Input:
            None

        Output:
            NOIN - not initialised.
            RUN - The digitizer is still running (either sampling or writing records to sample memory).
            NORM - The digitizer completed its last configured and triggered sample, and completed writing records to sample memory.
            ABOR - The digitizer aborted sampling.
        '''
        return self._visainstrument.query('FETC:WAV:ACQ:PRE?').split(',')[3]

    def get_acquisition_overview(self):
        return self._visainstrument.query('FETC:WAV:ACQ:PRE?')

    def get_last_record_completed(self):
        last_record = self.get_acquisition_overview().split(',')[0]
        return int(last_record)

    def get_total_record_completed(self):
        last_record = self.get_acquisition_overview().split(',')[1]
        return int(last_record)

    def send_trigger(self):
        '''
        Send a software trigger.
        '''
        self._visainstrument.write('*TRG')

    def protection_off_all(self):
        '''
        Turn off protection relay for all channels.
        '''
        self._visainstrument.write('CHAN:ATTR:PROT (@1:4),OFF')

    def abort(self):
        '''
        Abort the current acquisition.

        Input:
            None

        Output:
            None
        '''
        self._visainstrument.write('ABOR')

    def reset(self):
        '''
        Resets the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting Instrument')
        self._visainstrument.write('*RST')
        self._visainstrument.clear()

    def get_error_message(self):
        return self._visainstrument.query('SYST:ERR?')

