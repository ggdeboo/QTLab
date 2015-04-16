# Rigol_DS1000E class, to perform the communication between the Wrapper and the device
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
import numpy as np #added later..!
import struct
#from numpy import linspace

#tdiv_options = [200e-9, 500e-9]
#for i in range(-9,3):
#    for j in [1, 2, 5]:
#        tdiv_options.append(round(j*10**i,-i))
#tdiv_options.append(1000)

class Rigol_DS1000E(Instrument):
    '''
    This is the python driver for the Rigol DS1000E series oscilloscopes
   
    The two models in DS1000E series are:
        DS1102E 100 MHz
        DS1052E  50 MHz

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Rigol_DS1000E', address='<VICP address>')
    <VICP address> = VICP::<ip-address>
    '''

    def __init__(self, name, address):
        '''
        Initializes the Rigol DS1000E.

        Input:
            name (string)    : name of the instrument
            address (string) : VICP address

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])
        logging.debug(__name__ + ' : Initializing instrument')
        
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._idn = self._visainstrument.ask('*IDN?')
        self._model = self._idn.lstrip('Rigol Technologies,')[:7]

        #self._visainstrument.delay = 20e-3

        self.add_parameter('trigger_slope',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('POSITIVE','NEGATIVE'))
        self.add_parameter('acquire_type',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('NORMAL','AVERAGE','PEAKDETECT'))
        self.add_parameter('acquire_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('REAL_TIME','EQUAL_TIME'),
            format_map={'REAL_TIME'  : 'real time',
                        'EQUAL_TIME' : 'equal time'
                        })
        self.add_parameter('acquire_averages',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            option_list=(2, 4, 8, 16, 32, 64, 128, 256))
        self.add_parameter('sampling_rate',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            units='S/s')
#        self.add_parameter('memory_depth',
#            flags=Instrument.FLAG_GET,
#            type=types.StringType,
#            option_list=('LONG','NORMAL'))
        self.add_parameter('timebase_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            format_map={'MAIN'    : 'main timebase',
                        'DELAYED' : 'delayed scan'})
        self.add_parameter('timebase_format',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('XY', 'YT', 'SCAN')) 
        self.add_parameter('trigger_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('EDGE',
                        'PULSE',
                        'VIDEO',
                        'SLOPE',
                        'PATTERN',
                        'DURATION',
                        'ALTERNATION'))
        self.add_parameter('trigger_source',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            channels=('EDGE','PULSE','SLOPE','VIDEO'),
            channel_prefix='mode_%s_',
            format_map={'CHAN1'  : 'channel 1',
                       'CHAN2'  : 'channel 2',
                       'EXT'    : 'external trigger channel',
                       'ACLINE' : 'mains supply'}
            )

        
#        for ch_in in self._input_channels:
#            self.add_parameter('enhanced_resolution_bits_'+ch_in,
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                minval=0, maxval=3,
#                get_func=self.do_get_enhanced_resolution,
#                channel=ch_in)
#            self.add_parameter(ch_in+'_vdiv',
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                get_func=self.do_get_vdiv,
#                channel=ch_in,
#                units='V')
#            self.add_parameter(ch_in+'_tdiv',
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                get_func=self.do_get_tdiv,
#                channel=ch_in,
#                units='s')
#            self.add_parameter(ch_in+'_vertical_offset',
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                get_func=self.do_get_voffset,
#                channel=ch_in,
#                units='V'
#                )        
#            self.add_parameter(ch_in+'_trace_on_display',
#                flags=Instrument.FLAG_GET,
#                type=types.BooleanType,
#                get_func=self.do_get_trace_on_display,
#                channel=ch_in,
#                )
#            self.add_parameter(ch_in+'_coupling',
#                flags=Instrument.FLAG_GET,
#                type=types.StringType,
#                get_func=self.do_get_coupling,
#                channel=ch_in,
#                )
#        self.add_parameter('tdiv',
#            flags=Instrument.FLAG_GETSET,
#            type=types.FloatType,
#            units='s',option_list=tdiv_options)
#        self.add_parameter('max_memsize',
#            flags=Instrument.FLAG_GETSET,
#            type=types.IntType,
#            units='S',option_list=(10000000,5000000,2500000,1000000,500000,100000,10000,1000,500))
#        self.add_parameter('samplerate',
#            flags=Instrument.FLAG_GET,
#            type=types.IntType,
#            units='S/s',option_list=(),minval=500,maxval=5e9)
#        self.add_parameter('trigger_source',
#            flags=Instrument.FLAG_GET,
#            type=types.StringType)
#        self.add_parameter('trigger_type',
#            flags=Instrument.FLAG_GET,
#            type=types.StringType,)
        
#        self.add_function('arm_acquisition')
#        self.add_function('get_all')
#        self.add_function('stop_acquisition')
#        self.add_function('get_esr')
#        self.add_function('get_stb')
#        self.add_function('trigger')
        self.get_all()
        print 'Rigol %s has been initialized.' % self._model


        # Make Load/Delete Waveform functions for each channel


    # Functions

    def get_all(self):
        logging.debug(__name__ + ' : Get all.')
        self.get_trigger_slope()
        self.get_acquire_type()
        self.get_acquire_mode()
        self.get_acquire_averages()
#        self.get_memory_depth()
        self.get_timebase_mode()
        self.get_timebase_format()
        self.get_trigger_mode()
#        self.get_trigger_source()

#        for ch_in in self._input_channels:
#            logging.info(__name__ + ' : Get '+ch_in)
#            self.get(ch_in+'_vdiv')
#            self.get(ch_in+'_tdiv')
#            self.get(ch_in+'_vertical_offset')
#            self.get(ch_in+'_trace_on_display')
#            self.get(ch_in+'_coupling')
#	    self.get(ch_in+'_eres_bits')
#	    self.get(ch_in+'_eres_bandwidth')
#        self.get('tdiv')
#        self.get('max_memsize')
#        self.get('samplerate')
#	self.get_trigger_source()
#	self.get_trigger_type()
#            self.get_enhanced_resolution(ch_in)

    def do_get_trigger_slope(self):
        '''
        Get the trigger slope.

        Output:
            POSITIVE
            NEGATIVE
        '''
        logging.debug(__name__ + ' : Get the trigger edge slope.')
        response = self._visainstrument.ask(':TRIG:EDGE:SLOP?')
        options = self.get_parameter_options('trigger_slope')['option_list']
        if response in options:
             return response
        else:
            logging.warning(self.__name__ + 
                            'Unexpected response: %s.' % response)

    def do_set_trigger_slope(self,slope):
        '''
        Set the trigger slope.

        Input:
            POSITIVE
            NEGATIVE
        Output:
            None
        '''
        logging.debug(__name__ + ' : Set the trigger edge slope to %s.'
                      % slope)
        self._visainstrument.write(':TRIG:EDGE:SLOP %s' % slope)

    def do_get_acquire_type(self):
        '''
        Get the acquisition type.

        Output:
            NORMAL
            AVERAGE
            PEAKDETECT
        '''
        logging.debug(__name__ + ' : Get the acquire type.')
        response = self._visainstrument.ask(':ACQ:TYPE?')
        options = self.get_parameter_options('acquire_type')['option_list']
        if response in options:
            return response
        else:
            logging.warning(self.__name__ + 
                            'Unexpected response: %s.' % response)

    def do_set_acquire_type(self,acq_type):
        '''
        Set the acquisition type.

        Input:
            NORMAL
            AVERAGE
            PEAKDETECT
        Output:
            None
        '''
        logging.debug(__name__ + ' : Set the acquisition type to %s.'
                      % acq_type)
        self._visainstrument.write(':ACQ:TYPE %s' % acq_type)


    def do_get_acquire_mode(self):
        '''
        Get the acquisition mode.

        Output:
            REAL_TIME
            EQUAL_TIME
        '''
        logging.debug(__name__ + ' : Get the acquire mode.')
        response = self._visainstrument.ask(':ACQ:MODE?')
        options = self.get_parameter_options('acquire_mode')['option_list']
        if response in options:
            return response
        else:
            logging.warning(self.__name__ + 
                            'Unexpected response: %s.' % response)

    def do_set_acquire_mode(self,acq_mode):
        '''
        Set the acquisition mode.

        Input:
            REAL_TIME
            EQUAL_TIME
        Output:
            None
        '''
        logging.debug(__name__ + ' : Set the acquisition mode to %s.'
                      % acq_mode)
        if acq_mode == 'REAL_TIME':
            self._visainstrument.write(':ACQ:MODE RTIM')
        else:
            self._visainstrument.write(':ACQ:MODE ETIM')

    def do_get_acquire_averages(self):
        '''
        Get the number of acquired averages in average mode.
        '''
        logging.debug(__name__ + ' : Get the acquisition averages.')
        response = self._visainstrument.ask(':ACQ:AVER?')
        return int(response)

    def do_set_acquire_averages(self, acq_number):
        '''Set the number of acquired averages in average mode.'''
        logging.debug(__name__ + ' : Set the acquisition averaging to %i'
                      % acq_number)
        self._visainstrument.write(':ACQ:AVER %i' % acq_number)

    def do_get_sampling_rate(self):
        '''Get the sampling rate.'''
        logging.debug(__name__ + ' : Get the sampling rate.')
        response = self._visainstrument.ask(':ACQ:SAMP?')
        return int(float(response))

    def do_get_timebase_mode(self):
        '''Get the timebase mode.'''
        logging.debug(__name__ + ' : Get the timebase mode.')
        response = self._visainstrument.ask(':TIM:MODE?')
        return response

    def do_set_timebase_mode(self, tmb_mode):
        '''Set the timebase mode.'''
        logging.debug(__name__ + ' : Set the timebase mode to %s' % tmb_mode)
        self._visainstrument.write(':TIM:MODE %s' % tmb_mode)

    def do_get_timebase_format(self):
        '''Get the timebase format.'''
        logging.debug(__name__ + ' : Get the timebase format.')
        response = self._visainstrument.ask(':TIM:FORM?')
        return response.replace('-','')

    def do_set_timebase_format(self, tmb_format):
        '''Set the timebase format.'''
        logging.debug(__name__ + ' : Set the timebase format to %s.'
                      % tmb_format)
        self._visainstrument.write(':TIM:FORM %s' %tmb_format)

    def do_get_trigger_mode(self):
        '''Get the trigger mode.'''
        logging.debug(__name__ + ' : Get the trigger mode.')
        response = self._visainstrument.ask(':TRIG:MODE?')
        return response

    def do_set_trigger_mode(self, trg_mode):
        '''Set the trigger mode.'''
        logging.debug(__name__ + ' : Set the trigger mode to %s.' % trg_mode)
        self._visainstrument.write(':TRIG:MODE %s' % trg_mode)

    def do_get_trigger_source(self, channel):
        '''Get the trigger source.'''
        logging.debug(__name__ + ' : Get the trigger source for mode %s.' %
                        channel)
        trg_mode = channel
        response = self._visainstrument.ask(':TRIG:%s:SOUR?' % trg_mode)
        if response == 'CH1':
            return 'CHAN1'
        if response == 'CH2':
            return 'CHAN2'
        if response == 'EXT':
            return 'EXT'
        if response == 'ACLINE':
            return 'ACLINE'

    def do_set_trigger_source(self, trg_source, channel):
        '''
        Set the trigger source.
        The allowed setting depends on the trigger mode.
        EDGE  mode: CHAN<n>, EXT, ACLINE
        PULSE mode: CHAN<n>, EXT
        SLOPE mode: CHAN<n>, EXT
        VIDEO mode: CHAN<n>, EXT
        '''
        logging.debug(__name__ + ' : Set the trigger source to %s.' 
                        % trg_source)
        trg_mode = channel
        if (trg_source == 'ACLINE' and 
            not (trg_mode == 'EDGE')):
            logging.warning('Can not set trigger source to AC line when' +
                             ' the trigger mode is not EDGE.')
        else:
            self._visainstrument.write(':TRIG:%s:SOUR %s' % 
                                        (trg_mode, trg_source))
                        
#    def do_get_memory_depth(self):
#        '''Get the memory depth.'''
#        logging.debug(__name__ + ' : Get the memory depth.')
#        response = self._visainstrument.ask(':ACQ:MEMD?')
#        return response

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

#    def trigger(self):
#        self._visainstrument.write('*TRG')


