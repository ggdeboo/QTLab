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
from numpy import zeros, uint8, frombuffer
import struct

#tdiv_options = [200e-9, 500e-9]
#for i in range(-9,3):
#    for j in [1, 2, 5]:
#        tdiv_options.append(round(j*10**i,-i))
#tdiv_options.append(1000)

class WaveformReadout(object):
    '''A class to handle the readout of waveforms.'''
    def __init__(self):
        self.test = 'blaat'
        print 'Waveform readout initialized.'

    def get_waveform_length(self, raw_data):
        '''Extract the length of the waveform from the first 10 bytes.'''
        return int(raw_data[2:10])

    def get_proper_sampling_rate(self):
        '''Get the proper sampling rate.'''
        tdiv = self.get_timebase_scale()

    def convert_raw_waveform_to_int_array(self, raw_data):
#        wvf_length = self.get_waveform_length(raw_data)        
#        int_array = zeros((wvf_length),dtype=uint8)

#        for i in range(wvf_length):
#            int_array[-i] = struct.unpack('B', raw_data[10+i:11+i])[0]
        int_array = frombuffer(raw_data[10:], dtype=uint8)
        return int_array

    def get_raw_waveform_data(self, source, time_vector=False):
        '''Read out the waveform data'''
        trig_mode = self.get_trigger_mode()
        if trig_mode == 'edge':
            if not (self.get_edge_trigger_sweep() == 'SINGLE'):
                logging.info('If the sweep mode is not single, the number ' + 
                             'of points is limited to 600.')
                
        source_options = ('ch1','ch2','math','fft') 
        if source in source_options:
            if source == 'ch1':
                self._visainstrument.write(':WAV:DATA? CHAN1')
            if source == 'ch2':
                self._visainstrument.write(':WAV:DATA? CHAN2')
            if source == 'math':
                self._visainstrument.write(':WAV:DATA? MATH')
            if source == 'fft':
                self._visainstrument.write(':WAV:DATA? FFT')
            wvf_data = self._visainstrument.read_raw()
        else:
            print 'wrong source'
            return None

        if time_vector:
            pass            

        # struct.unpack('B', data)[0]
        return wvf_data

class Rigol_DS1000E(Instrument, WaveformReadout):
    '''
    This is the python driver for the Rigol DS1000E series oscilloscopes
   
    The two models in DS1000E series are:
        DS1102E 100 MHz
        DS1052E  50 MHz

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
        self._model = self._idn.split(',')[1]
        self._serialnumber = self._idn.split(',')[2]

        self._timebase_options = [2e-9,5e-9]
        for j in range(-8,2):
            for i in [1, 2, 5]:
                self._timebase_options.append(i*10**j)

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
        self.add_parameter('memory_depth_setting',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('LONG','NORMAL'))
        # timebase
        self.add_parameter('timebase_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            format_map={'MAIN'    : 'main timebase',
                        'DELAYED' : 'delayed scan'})
        self.add_parameter('timebase_format',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('XY', 'YT', 'SCAN')) 
        self.add_parameter('timebase_scale',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            units='s/div',
            option_list=self._timebase_options)
            

        # trigger
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
            channels=('edge','pulse','slope','video'),
            channel_prefix='%s_mode_',
            format_map={'CHAN1'  : 'channel 1',
                       'CHAN2'  : 'channel 2',
                       'EXT'    : 'external trigger channel',
                       'ACLINE' : 'mains supply'}
            )
        self.add_parameter('trigger_level',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=('edge',),
            channel_prefix='%s_mode_',
            units='V'
            )
        self.add_parameter('trigger_sensitivity',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            minval=0.1, maxval=1.0,
            channels=('pulse','video'),
            channel_prefix='%s_mode_',
            units='divisions')
        self.add_parameter('trigger_sweep',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            channels=('edge','pulse','slope','pattern','duration'),
            channel_prefix='%s_mode_',
            option_list=('AUTO','NORMAL','SINGLE'))
        self.add_parameter('trigger_coupling',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            channels=('edge','pulse','slope'),
            channel_prefix='%s_mode_',
            option_list=('DC','AC','HF','LF'))
        self.add_parameter('trigger_holdoff',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='s')
        self.add_parameter('trigger_status',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            option_list=('run','stop','t`d','wait','auto'))
        self.add_parameter('edge_mode_trigger_slope',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            option_list=('positive','negative'))

        # channel parameters
        self.add_parameter('bandwidth_limit',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType,
            channels=(1,2),
            channel_prefix='ch%i_')
        self.add_parameter('coupling',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            channels=(1,2),
            channel_prefix='ch%i_',
            option_list=('AC','DC','GND'))
        self.add_parameter('display',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType,
            channels=(1,2),
            channel_prefix='ch%i_')
        self.add_parameter('invert',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType,
            channels=(1,2),
            channel_prefix='ch%i_')
        self.add_parameter('offset',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=(1,2),
            channel_prefix='ch%i_',
            minval=-40,maxval=40,
            units='V')
        self.add_parameter('probe',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            channels=(1,2),
            channel_prefix='ch%i_',
            option_list=(1,5,10,50,100,500,1000),
            units='X')
        self.add_parameter('scale',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            channels=(1,2),
            channel_prefix='ch%i_',
            units='V')
        self.add_parameter('filter',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType,
            channels=(1,2),
            channel_prefix='ch%i_')
        self.add_parameter('memory_depth',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            channels=(1,2),
            channel_prefix='ch%i_',
            minval=512, maxval=1048576)
        self.add_parameter('vernier',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType,
            channels=(1,2),
            channel_prefix='ch%i_')

        # math parameters
        self.add_parameter('math_display',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType,
            format_map={ True : 'on',
                         False: 'off'})
        self.add_parameter('FFT_display',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType,
            format_map={ True : 'on',
                         False: 'off'})
            
        # measure parameters
        self.add_parameter('counter_value',
            flags=Instrument.FLAG_GET,
            type=types.IntType)
        self.add_parameter('counter_enabled',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType)

        self.add_parameter('waveform_points_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('NORMAL','MAXIMUM','RAW'))
            
        self.add_function('run')
        self.add_function('trigger')
        self.add_function('get_waveform_data')
        self.add_function('weird_test')
        self.get_all()
        WaveformReadout.__init__(self)
        print('Rigol %s with serial number %s has been initialized.' 
                % (self._model, self._serialnumber))


        # Make Load/Delete Waveform functions for each channel


    # Functions

    def get_all(self):
        logging.debug(__name__ + ' : Get all.')
        self.get_trigger_slope()
        self.get_acquire_type()
        self.get_acquire_mode()
        self.get_acquire_averages()
        self.get_memory_depth_setting()
        self.get_timebase_mode()
        self.get_timebase_format()
        self.get_timebase_scale()

        self.get_trigger_mode()
        self.get_trigger_holdoff()
        self.get_trigger_status()
        self.get_edge_mode_trigger_coupling()
        self.get_edge_mode_trigger_level()
        self.get_edge_mode_trigger_slope()
        self.get_edge_mode_trigger_sweep()
        self.get_edge_mode_trigger_source()
        self.get_pulse_mode_trigger_sensitivity()
        self.get_video_mode_trigger_sensitivity()
        self.get_sampling_rate()
        self.get_ch1_bandwidth_limit()
        self.get_ch2_bandwidth_limit()
        self.get_ch1_coupling()
        self.get_ch2_coupling()
        self.get_ch1_display()
        self.get_ch2_display()
        self.get_ch1_invert()
        self.get_ch2_invert()
        self.get_ch1_offset()
        self.get_ch2_offset()
        self.get_ch1_probe()
        self.get_ch2_probe()
        self.get_ch1_scale()
        self.get_ch2_scale()
        self.get_ch1_filter()
        self.get_ch2_filter()
        self.get_ch1_memory_depth()
        self.get_ch2_memory_depth()
        self.get_ch1_vernier()
        self.get_ch2_vernier()
        self.get_math_display()
        self.get_FFT_display()

        self.get_counter_value()

        self.get_counter_enabled()
        self.get_waveform_points_mode()

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
#        logging.warning('It is unclear what this sampling rate value represents.')
        tdiv = self.get_timebase_scale()
        correct_samplerate = {  5e-9 : 1e9,
                               10e-9 : 1e9,
                               20e-9 : 1e9,
                               50e-9 : 1e9,
                              100e-9 : 500e6,
                              200e-9 : 250e6}
        if tdiv < 500e-9:
            # response from scope doesn't seem to be correct for a small
            # timebase
            return int(correct_samplerate[tdiv])
            
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

    def do_get_timebase_scale(self):
        '''Get the timebase scale in s.'''
        logging.debug(__name__ + ' : Get the timebase scale.')
        response = self._visainstrument.ask(':TIM:SCAL?')
        return float(response)

    def do_set_timebase_scale(self, scale):
        '''Set the timebase scale in s.'''
        logging.debug(__name__ + ' : Set the timebase scale to %f.' % scale)
        self._visainstrument.write(':TIM:SCAL %.9f' % scale)

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
        trg_mode = channel.upper()
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

    def do_get_trigger_level(self, channel):
        '''Get the trigger level.'''
        logging.debug(__name__ + ' : Get the trigger level for the %s mode.'
                        % channel)
        response = self._visainstrument.ask(':TRIG:%s:LEV?' % channel)
        return float(response)

    def do_set_trigger_level(self, level, channel):
        '''Set the trigger level.'''
        logging.debug(__name__ + ' : Set the trigger level to %f.' % level)
        self._visainstrument.write(':TRIG:%s:LEV %f' % (channel, level))

    def do_get_trigger_sensitivity(self, channel):
        '''Get the trigger sensitivity for the pulse and video mode.'''
        logging.debug(__name__ + 
                ' : Get the trigger sensitivity for the %s mode.' % channel)
        response = self._visainstrument.ask(':TRIG:%s:SENS?' % channel)
        return response

    def do_set_trigger_sensitivity(self, sens, channel):
        '''Set the trigger sensitivity for the pulse and video mode.'''
        logging.debug(__name__ + 
            ' : Set the trigger sensitivity for the %s mode to %s.' 
            % (channel, sens))
        self._visainstrument.write(':TRIG:%s:SENS %.1f' % (channel, sens))

    def do_get_trigger_sweep(self, channel):
        '''Get the trigger sweep setting.'''
        logging.debug(__name__ + 
                ' : Get the trigger sweep setting for the %s mode' % channel)
        response = self._visainstrument.ask(':TRIG:%s:SWE?' % channel)
        return response

    def do_set_trigger_sweep(self, swp_mode, channel):
        logging.debug(__name__ + 
                ' : Set the trigger sweep setting for the %s mode' % channel)
        self._visainstrument.write(':TRIG:%s:SWE %s' % (channel, swp_mode))

    def do_get_trigger_coupling(self, channel):
        '''Get the trigger coupling.'''
        logging.debug(__name__ +
            ' : Get the trigger coupling setting for the %s mode' % channel)
        response = self._visainstrument.ask(':TRIG:%s:COUP?' % channel)
        return response

    def do_get_trigger_holdoff(self):
        '''Get the trigger holdoff.'''
        logging.debug(__name__ + ' : Get the trigger holdoff time.')
        response = self._visainstrument.ask(':TRIG:HOLD?')
        return float(response)

    def do_get_trigger_status(self):
        '''Get the trigger status.'''
        logging.debug(__name__ + ' : Get the trigger status.')
        response = self._visainstrument.ask(':TRIG:STAT?')
        return response.lower()

    def do_get_edge_mode_trigger_slope(self):
        '''Get the slope of the edge mode trigger.'''
        logging.debug(__name__ + ' : Get the slope of the edge mode trigger.')
        response = self._visainstrument.ask(':TRIG:EDGE:SLOP?')
        return response.lower()

    def do_get_bandwidth_limit(self, channel):
        '''Get the bandwidth limit of an oscilloscope channel.'''
        logging.debug(__name__ + 
            ' : Get the bandwidth limit of oscilloscope channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:BWL?' % channel)
        if response == 'ON':
            return True
        else:
            return False

    def do_get_coupling(self, channel):
        '''Get the coupling of an oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Get the coupling of oscilloscope channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:COUP?' % channel)
        return response

    def do_set_coupling(self, coupling, channel):
        '''Set the coupling of an oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Set the coupling of oscilloscope channel %i to %s' 
            % (channel, coupling))
        self._visainstrument.write(':CHAN%i:COUP %s' % (channel, coupling))

    def do_get_display(self, channel):
        '''Get the On/Off state of an oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Get the On/Off state of oscilloscope channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:DISP?' % channel)
        if response == '1':
            return True
        else:
            return False

    def do_set_display(self, status, channel):
        '''Set whether the oscilloscope channel is on or off.'''
        logging.debug(__name__ + 
            ' : Set the On/Off state of oscilloscope channel %i to %s' 
            % (channel, status))
        if status:
            self._visainstrument.write(':CHAN%i:DISP 1' % channel)
        else:
            self._visainstrument.write(':CHAN%i:DISP 0' % channel)

    def do_get_invert(self, channel):
        '''Get whether the oscilloscope channel is inverted.'''
        logging.debug(__name__ + 
            ' : Get whether oscilloscope channel %i is inverted' % channel)
        response = self._visainstrument.ask(':CHAN%i:INV?' % channel)
        if response == 'ON':
            return True
        else:
            return False

    def do_get_offset(self, channel):
        '''Get the offset of the oscilloscope channel.'''
        logging.debug(__name__ + 
            ' : Get the offset of oscilloscope channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:OFFS?' % channel)
        return float(response)

    def do_set_offset(self, offset, channel):
        '''Set the offset of the oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Set the offset of oscilloscope channel %i to %f' 
            % (channel, offset))
        self._visainstrument.write(':CHAN%i:OFFS %.3f' % (channel, offset))

    def do_get_probe(self, channel):
        '''Get the probe attenuation factor of the oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Get the probe attenuation factor of oscilloscope channel %i' 
            % channel)
        response = self._visainstrument.ask(':CHAN%i:PROB?' % channel)
        prb_att = int(float(response))
        # The probe setting determines the range of the scale parameter.
        unity_scale_range = [0.002, 10.0]
        self.set_parameter_bounds('ch%i_scale'%channel,
                                prb_att*unity_scale_range[0],
                                prb_att*unity_scale_range[1])
        return prb_att

    def do_set_probe(self, prb_att, channel):
        '''Set the probe attenuation factor of the oscilloscope channel.'''
        logging.debug(__name__ + 
            ' : Set the probe attenuation factor of oscilloscope channel %i'
            % channel)
        # The probe setting determines the range of the scale parameter.
        unity_scale_range = [0.002, 10.0]
        self.set_parameter_bounds('ch%i_scale'%channel,
                                prb_att*unity_scale_range[0],
                                prb_att*unity_scale_range[1])
        self._visainstrument.write(':CHAN%i:PROB %i' % (channel, prb_att))

    def do_get_scale(self, channel):
        '''Get the scale of the oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Get the scale of oscilloscope channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:SCAL?' % channel)
        scale = float(response)
        # The scale determines the bounds for several other parameters.
        if self.get_edge_mode_trigger_source() == ('CHAN %i' % channel):
            self.set_parameter_bounds('edge_mode_trigger_level',
                                        -6*scale,6*scale)
        if scale < 0.250:
            self.set_parameter_bounds('ch%i_offset'%channel,-2,+2)
        else:
            self.set_parameter_bounds('ch%i_offset'%channel,-40,+40)
        return scale

    def do_set_scale(self, scale, channel):
        '''Set the scale of the oscilloscope channel.'''
        logging.debug(__name__ +
            ' : Set the scale of the oscilloscope channel %i' % channel)
        # The scale determines the bounds for several other parameters.
        if self.get_edge_mode_trigger_source() == ('CHAN %i' % channel):
            self.set_parameter_bounds('edge_mode_trigger_level',
                                        -6*scale,6*scale)
        if scale < 0.250:
            self.set_parameter_bounds('ch%i_offset'%channel,-2,+2)
        else:
            self.set_parameter_bounds('ch%i_offset'%channel,-40,+40)
        self._visainstrument.write(':CHAN%i:SCAL %.3f' 
                                % (channel, scale))

    def do_get_filter(self, channel):
        '''Get whether the filter of the oscilloscope channel is on or off.'''
        logging.debug(__name__ +
            ' : Get whether the filter is on or off on channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:FILT?' % channel)
        if response == 'ON':
            return True
        else:
            return False

    def do_get_memory_depth_setting(self):
        '''Get the memory depth setting of the oscillosocpe.'''
        logging.debug(__name__ +
            ' : Get the memory depth of the oscilloscope.')
        response = self._visainstrument.ask(':ACQuire:MEMDepth?')
        return response

    def do_set_memory_depth_setting(self, setting):
        '''Set the memory depth setting of the oscilloscope.'''
        logging.debug(__name__ +
            ' : Set the memory depth of the oscilloscope to %s.' % setting)
        self._visainstrument.write(':ACQuire:MEMDepth %s' % setting)

    def do_get_memory_depth(self, channel):
        '''Get the memory depth of the oscilloscope channel.'''
        logging.debug(__name__ + 
            ' : Get the memory depth of oscilloscope channel %i' % channel)
        response = self._visainstrument.ask(':CHAN%i:MEMoryDepth?' % channel)
        return int(response)

    def do_get_vernier(self, channel):
        '''Get the vernier of the oscilloscope channel.'''
        logging.debug(__name__ + 
        ' : Get whether the vernier is on or off on oscilloscope channel %i'
        % channel)
        response = self._visainstrument.ask(':CHAN%i:VERN?' % channel)
        if response == 'ON':
            return True
        else:
            return False

    def do_get_counter_value(self):
        '''Get the counter value of the oscilloscope.'''
        logging.debug(__name__ + ' : Get the counter value')
        response = self._visainstrument.ask(':COUNter:VALue?')
        if response == '-inf':
            return 0
        else:
            return int(float(response))

    def do_get_counter_enabled(self):
        '''Get whether the counter is on or off.'''
        logging.debug(__name__ + ' : Get whether the counter is enabled.')
        response = self._visainstrument.ask(':COUN:ENAB?')
        if response == 'ON':
            return True
        else:
            return False

    def do_get_math_display(self):
        '''Get whether the math operation is enabled.'''
        logging.debug(__name__ + 
                        ' : Get whether the math operation is enabled.')
        response = self._visainstrument.ask(':MATH:DISPlay?')
        if response == 'ON':
            return True
        else:
            return False

    def do_set_math_display(self, math_status):
        '''Set whether the math operation is enabled.'''
        logging.debug(__name__ + 
                    ' : Set the math operation status to %s.' % math_status)
        if math_status:
            self._visainstrument.write(':MATH:DISP ON')
        else:
            self._visainstrument.write(':MATH:DISP OFF')

    def do_get_FFT_display(self):
        '''Get whether the FFT operation is enabled.'''
        logging.debug(__name__ + 
                        ' : Get whether the FFT operation is enabled.')
        response = self._visainstrument.ask(':FFT:DISPlay?')
        if response == 'ON':
            return True
        else:
            return False

    def do_set_FFT_display(self, fft_status):
        '''Set whether the FFT operation is enabled.'''
        logging.debug(__name__ + 
                    ' : Set the FFT operation status to %s.' % fft_status)
        if fft_status:
            self._visainstrument.write(':FFT:DISP ON')
        else:
            self._visainstrument.write(':FFT:DISP OFF')
                        
#    def do_get_memory_depth(self):
#        '''Get the memory depth.'''
#        logging.debug(__name__ + ' : Get the memory depth.')
#        response = self._visainstrument.ask(':ACQ:MEMD?')
#        return response

    def do_get_waveform_points_mode(self):
        '''Get the points mode for obtaining a waveform.'''
        response = self._visainstrument.ask(':WAV:POINTS:MODE?')
        return response

    def do_set_waveform_points_mode(self, points_mode):
        self._visainstrument.write(':WAV:POIN:MODE %s' % points_mode)

    def get_waveform_data(self, source):
        '''Read out the waveform data'''
        self.set_waveform_points_mode('raw')
        # If the points mode is set to normal, the oscilloscope will pad the 
        # data points with sin(x)/x interpolation to get to 600 points in the
        # time span of 12div*timebase.
        # I don't know why you would want this, so by default the read out is
        # in raw mode.
        # The length of the output depends on whether one or two channels are
        # being used and whether the long memory option is enabled.
        data = []
        while len(data) < 611:
            data = self.get_raw_waveform_data(source)
        return self.convert_raw_waveform_to_int_array(data)
        
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

    def run(self):
        self._visainstrument.write(':RUN')

    def trigger(self):
        self._visainstrument.write(':FORC')

    def weird_test(self):
        print self.test
