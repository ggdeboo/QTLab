#  -*- coding: utf-8 -*-
# Agilent_L4534A class, to perform the communication between the Wrapper and the device
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
import visa
import types
import logging
import socket
from numpy import zeros, uint8, frombuffer, float32
import struct

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
        self._visainstrument = visa.instrument(self._address)
        self._idn = self._visainstrument.ask('*IDN?')
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
            flags=Instrument.FLAG_GET,
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
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            channels=(1,2,3,4),
            channel_prefix='ch%i_')
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
            flags=Instrument.FLAG_GET,  
            type=types.IntType,
            minval=0)
        self.add_parameter('trigger_delay',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=0.0, maxval=3600.0,
            units='s',
            )

        # measure parameters

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
        response = self._visainstrument.ask('CONF:ROSC?')
        return response

    def do_get_sample_rate(self):
        '''Get the sample rate'''
        logging.debug(__name__ + ' : Getting the sample rate')
        response = self._visainstrument.ask('CONF:ACQ:SRAT?')
        return int(response)

    def do_set_sample_rate(self, sample_rate):
        '''Get the sample rate'''
        logging.debug(__name__ + ' : Setting the sample rate')
        self._visainstrument.write('CONF:ACQ:SRAT %.1e' % sample_rate)

    def do_get_samples_per_record(self):
        '''Get the number of samples per record'''
        logging.debug(__name__ + ' : Getting the samples per record')
        response = self._visainstrument.ask('CONF:ACQ:SCO?')
        return int(response)

    def do_set_samples_per_record(self, samples):
        '''Set the number of samples per record'''
        logging.debug(__name__ + ' : Setting the number of samples per ' +
                        'to %i.' % samples)
        self._visainstrument.write('CONF:ACQ:SCO %i' % samples) 

    def do_get_pre_trigger_samples(self):
        '''Get the number of pre-trigger samples per record'''
        response = self._visainstrument.ask('CONF:ACQ:SPR?')
        return int(response)

    def do_get_trigger_delay(self):
        '''
            Get the time following a trigger event before the trigger sample
            is acquired.
        '''
        response = self._visainstrument.ask('CONF:ACQ:TDEL?')
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
        response = self._visainstrument.ask('CONF:TRIG:SOUR?')
        return response

    def do_get_arm_source(self):
        '''Get the arm source.'''
        logging.debug(__name__ + ' : Get the arm source')
        response = self._visainstrument.ask('CONF:ARM:SOUR?')
        return response.split(',')[0]

    def do_set_arm_source(self, source):
        '''Set the arm source.'''
        self._visainstrument.write('CONF:ARM:SOUR %s' % source)

    def do_get_triggers_per_arm(self):
        '''Get the number of triggers per arm. Default 1024'''
        logging.debug(__name__ + ' : Get the triggers per arm.')
        response = self._visainstrument.ask('CONF:ARM:SOUR?')
        return response.split(',')[1]

    def do_get_records_per_acquisition(self):
        '''Get the number of records per acquisition.
            An acquisition is started after the INITiate command.
            Each record requires a trigger. 

            Default value: 1
        '''
        logging.debug(__name__ + ' : Get the number of records per aqcuisition.')
        response = self._visainstrument.ask('CONF:ACQ:REC?')
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
        response = self._visainstrument.ask('CONF:CHAN:COUP? (@%s)' % channel)
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
        response = self._visainstrument.ask('CONF:CHAN:RANG? (@%i)' % channel)
        # The scale determines the bounds for several other parameters.
        return float(response)

    def do_set_range(self, channel_range, channel):
        '''Set the range of the digitizer channel.'''
        logging.debug(__name__ +
            ' : Set the range of the digitizer channel %i' % channel)
        self._visainstrument.write('CONF:CHAN:RANG (@%i), %.1f' 
                                % (channel, channel_range))

    def do_get_filter(self, channel):
        '''Get the filter of the digitizer channel.
            LP_200_KHZ
            LP_2_MHZ
            LP_20_MHZ'''
        logging.debug(__name__ +
            ' : Get the filter on channel %i' % channel)
        response = self._visainstrument.ask('CONF:CHAN:FILT? (@%i)' % channel)
        return response

    def do_get_channel_trigger(self, channel):
        '''
        Get the channel trigger configuration for the channel trigger mode
        '''
        response = self._visainstrument.ask('CONF:TRIG:SOUR:CHAN? (@%i)' %
                                            channel)
        return response

    def do_get_edge_trigger_level(self, channel):
        '''
        Get the level for the edge trigger mode on the specified channel
        '''
        response = self._visainstrument.ask('CONF:TRIG:SOUR:CHAN:EDGE? (@%i)' 
                                            % channel)
        return float(response.split(',')[0])

    def do_get_edge_trigger_slope(self, channel):
        '''
        Get the slope for the edge trigger mode on the specified channel
        '''
        response = self._visainstrument.ask('CONF:TRIG:SOUR:CHAN:EDGE? (@%i)' 
                                            % channel)
        return response.split(',')[1]

    def fetch_data(self, channel, raw=False):
        '''Fetch the data from the specified channel
           returns a numpy Float32 array
        '''
        # check whether data is available
        if self._visainstrument.ask('STAT:OPER:COND? MTHR') == '+1':
            preamble = self._visainstrument.ask('FETC:WAV:ACQ:PRE?').split(',')
            n_samples = int(preamble[1])
            data_array = zeros(n_samples, dtype=float32)
            dig_range = self.get('ch%i_range' % channel)
            data = self._visainstrument.ask('FETC:WAV:ADC? (@%i)' % channel)
            # ADC16 format from the digitizer, to convert use struct.unpack
            if data.startswith('#'):
                header_length = int(data[1])
                data_array[:] =  struct.unpack('>%ih' % n_samples, 
                                    data[2+header_length:])
                return (dig_range * data_array / 32767.0)
            else:
                logging.warning('wrong response to FETC:WAV:ADC? (@%i)' %
                                channel)
        else:
            # TODO build check whether acquisition is in process
            logging.warning('No data available on digitizer, ' + 
                            'did the acquisition start?')

    def start_acquisition(self):
        self._visainstrument.write('INIT')

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
        return self._visainstrument.ask('SYST:ERR?')

