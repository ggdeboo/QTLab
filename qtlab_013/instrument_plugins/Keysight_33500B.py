# Keysight_33520B.py class, to perform the communication between the Wrapper and the device
# Takashi Kobayashi <one-storn-s-o-r@mail.goo.ne.jp>, 2016
# Gabriele de Boo <ggdeboo@gmail.com>, 2016
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
#from time import sleep
from numpy import arange, float32
from math import log10
#from struct import *

#TODO
#1 put modes/shapes/status as parameter with list of options?
#   burst_state { on, off }
#   trigger_state { cont, external, gpib }
#   function_shape { see below }
#2 put above in get_all()

class Keysight_33500B(Instrument):
    '''
    This is the python driver for the Keysight 33500B series
    arbitrary waveform generator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keysight_33500B', address='<GPIB address>',
        reset=<bool>)
    '''
    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keysight_33500B, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB, TCPIP or USB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        logging.info('Initializing Keysight 33500B series AWG') 
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.term_chars = '\n'
        self._idn = self._visainstrument.ask('*IDN?')
        self._model =  self._idn.split(',')[1]
        self._channels = (1, 2)
        self._installed_options = self._visainstrument.ask('*OPT?').split(',')
        logging.info('The connected AWG is a {0}'.format(self._model))
        if 'MEM' in self._installed_options:
            logging.info('The extended memory option is installed')
            self._mem_size = 16e6
        else:
            self._mem_size = 1e6
            logging.debug('Extended memory option not installed')
        self._visainstrument.write('FORM:BORD SWAP') # correct byte order
        
        # Output
        self.add_parameter('output', 
            type=types.BooleanType, 
            flags=Instrument.FLAG_GETSET,
            channels=(1, 2), 
            channel_prefix='ch%i_',
            )
        self.add_parameter('sync_source', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            option_list=('CH1', 'CH2'))

        # General parameters
        self.add_parameter('frequency', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=1e-6, maxval=30e6, units='Hz')
        self.add_parameter('amplitude', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2),
            channel_prefix='ch%i_', 
            minval=1e-3, 
            maxval=5.0, 
            format='%.3f',
            units='Vpp')
        self.add_parameter('offset', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=-5.0, maxval=5.0, 
            format='%.3f',
            units='V')
        self.add_parameter('load',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            minval=1.0, maxval=10000,
            units='Ohm',
            )
        
        # Function parameter
        self.add_parameter('apply', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2),
            channel_prefix='ch%i_',
            )
        self.add_parameter('function', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            option_list=('SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 
                            'PRBS', 'NOIS', 'ARB', 'DC'))

        # Burst mode parameters
        self.add_parameter('burst_cycle', 
            type=types.IntType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=1, maxval=1e8, 
            units='#')
        self.add_parameter('burst_state', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            option_list=('ON', 'OFF'))
        self.add_parameter('burst_mode', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            option_list=('TRIG', 'GAT'))
        self.add_parameter('burst_gate_polarity', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            option_list=('NORM', 'INV'))
        self.add_parameter('burst_phase', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=-360.0, maxval=360.0, 
            units='degree')
        self.add_parameter('burst_period', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=1e-6, maxval=8e3, 
            units='second')

        # Pulse mode parameters
        self.add_parameter('pulse_dutycycle', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=0, maxval=100, 
            units='%')
        self.add_parameter('pulse_trans_leading', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=8.4e-9, maxval=1e-6, 
            units='second')
        self.add_parameter('pulse_trans_trailing', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=8.4e-9, maxval=1e-6, 
            units='second')
        self.add_parameter('pulse_width', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=16e-9, maxval=1e6, 
            units='second')
        

        # Trigger parameters
        self.add_parameter('continuous', 
            type=types.BooleanType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            )
        self.add_parameter('trigger_source', 
            type=types.StringType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            option_list=('IMM', 'EXT', 'TIM', 'BUS'))
        self.add_parameter('trigger_delay', 
            type=types.FloatType, 
            flags=Instrument.FLAG_GETSET, 
            channels=(1, 2), 
            channel_prefix='ch%i_',
            minval=0.0, maxval=1e3, 
            units='second')
        
        # memory
        self.add_parameter('free_volatile_memory',
            type=types.IntType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2), 
            channel_prefix='ch%i_',
            )

        # display
        self.add_parameter('display',
            type=types.BooleanType,
            flags=Instrument.FLAG_GET,
            )
        # arbitrary waveform system
        self.add_parameter('arbitrary_waveform',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            channels=(1, 2), 
            channel_prefix='ch%i_',
            )
        self.add_parameter('arbitrary_waveform_frequency',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            units='Hz',
            format='%.1f',
            )
        self.add_parameter('arbitrary_waveform_period',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            units='s',
            )
        self.add_parameter('arbitrary_waveform_points',
            type=types.IntType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            units='#',
            )
        self.add_parameter('arbitrary_waveform_samplerate',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            maxval=62500000,
            )
        self.add_parameter('arbitrary_waveform_filter',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            option_list=('NORMAL','STEP','OFF'),
            )
        self.add_parameter('arbitrary_waveform_peak_to_peak',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2),
            channel_prefix='ch%i_',
            units='V',
            format='%.3f',
            )
 
        self.add_function('imm_trigger')
        self.add_function('ext_trigger')
        self.add_function('bus_trigger')
        self.add_function('send_trigger1')
        self.add_function('send_trigger2')
        self.add_function('send_trigger')
        self.add_function('initiate')
        self.add_function('get_volatile_memory_catalog')
        self.add_function('synchronize_waveforms')

        self.add_function('reset')
        self.add_function('get_all')

        if reset:
            self.reset()
        else:
            self.get_all()

    def get_all(self):
        for channel in self._channels:
            self.get('ch{0}_frequency'.format(channel))
            self.get('ch{0}_amplitude'.format(channel))
            self.get('ch{0}_offset'.format(channel))
            self.get('ch{0}_load'.format(channel))
            self.get('ch{0}_function'.format(channel))
            self.get('ch{0}_burst_cycle'.format(channel))
            self.get('ch{0}_pulse_width'.format(channel))
            self.get('ch{0}_output'.format(channel))
            self.get('ch{0}_trigger_delay'.format(channel))
            self.get('ch{0}_trigger_source'.format(channel))
            self.get('ch{0}_continuous'.format(channel))
            self.get('ch{0}_arbitrary_waveform'.format(channel))
            self.get('ch{0}_arbitrary_waveform_frequency'.format(channel))
            self.get('ch{0}_arbitrary_waveform_period'.format(channel))
            self.get('ch{0}_arbitrary_waveform_points'.format(channel))
            self.get('ch{0}_arbitrary_waveform_samplerate'.format(channel))
            self.get('ch{0}_arbitrary_waveform_filter'.format(channel))
            self.get('ch{0}_arbitrary_waveform_peak_to_peak'.format(channel))
            self.get('ch{0}_free_volatile_memory'.format(channel))
        self.get_display()
        self.get_sync_source()

    def reset(self):
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        sleep(0.1)
        self.get_all()

    def get_error(self):
        logging.debug(__name__ + ' : Getting one error from error list')
        return self._visainstrument.ask('SYST:ERR?')        

# Output
        
    def do_set_output(self, state, channel):
        logging.debug(__name__ + ' : Set output state')
        self._visainstrument.write('OUTP{0} {1:d}'.format(channel, state))
        
    def do_get_output(self, channel):
        logging.debug(__name__ + ' : Get output state')
        output_status = self._visainstrument.ask('OUTP%s?' % channel)
        return bool(int(output_status))
    
    def do_set_sync_source(self, source):
        logging.debug(__name__ + ' : Set output state')
        self._visainstrument.write('OUTP:SYNC:SOUR %s' % source)
        
    def do_get_sync_source(self):
        logging.debug(__name__ + ' : Get output state')
        return self._visainstrument.ask('OUTP:SYNC:SOUR?')
    
        
# Trigger

    def do_set_continuous(self, mode, channel):
        logging.debug(__name__ + ' : Set continuous mode')
        self._visainstrument.write('INIT{0}:CONT {1:d}'.format(channel, mode))
        
    def do_get_continuous(self, channel):
        logging.debug(__name__ + ' : Get continuous mode')
        cnts = self._visainstrument.ask('INIT%s:CONT?' % channel)
        return bool(int(cnts))
        
    def do_set_trigger_delay(self, delay, channel):
        logging.debug(__name__ + ' : Set trigger delay')
        self._visainstrument.write('TRIG%s:DEL %s' % (channel, delay))
        
    def do_get_trigger_delay(self, channel):
        logging.debug(__name__ + ' : Get trigger delay')
        return self._visainstrument.ask('TRIG%s:DEL?' % channel)
        
    def do_set_trigger_source(self, source, channel):
        logging.debug(__name__ + ' : Setting trigger source')
        self._visainstrument.write('TRIG%s:SOUR %s' % (channel, source))
        
    def do_get_trigger_source(self, channel):
        logging.debug(__name__ + ' : Getting trigger source')
        return self._visainstrument.ask('TRIG%s:SOUR?' % channel)

    def imm_trigger(self, channel):
        logging.debug(__name__ + ' : Set trigger to immediate')
        self._visainstrument.write('TRIG%s:SOUR IMM' % channel)

    def ext_trigger(self, channel):
        logging.debug(__name__ + ' : Set trigger to external')
        self._visainstrument.write('TRIG%s:SOUR EXT' % channel)
        
    def bus_trigger(self, channel):
        logging.debug(__name__ + ' : Set trigger to gpib')
        self._visainstrument.write('TRIG%s:SOUR BUS' % channel)

    
    def send_trigger1(self):
        logging.debug(__name__ + ' : Sending Trigger')
        self._visainstrument.write('TRIG1')

    def send_trigger2(self):
        logging.debug(__name__ + ' : Sending Trigger')
        self._visainstrument.write('TRIG2')

    def send_trigger(self):
        logging.debug(__name__ + ' : Sending Trigger')
        self._visainstrument.write('*TRG')
    
        
    def initiate(self, channel):
        logging.debug(__name__ + ' : Initiate')
        self._visainstrument.write('INIT%s' % channel)

# Burst

    def do_set_burst_cycle(self, cycle, channel):
        logging.debug(__name__ + ' : Setting burst cycle')
        self._visainstrument.write('SOUR%s:BURS:NCYC %d' % (channel, cycle))

    def do_get_burst_cycle(self, channel):
        logging.debug(__name__ + ' : Getting burst cycle')
        return float(self._visainstrument.ask('SOUR%s:BURS:NCYC?' % channel))

    def do_set_burst_state(self, stat, channel):
        '''
        stat: { ON OFF }
        '''
        logging.debug(__name__ + ' : Setting burst state')
        self._visainstrument.write('SOUR%s:BURS:STAT %s' % (channel, stat))

    def do_get_burst_state(self, channel):
        '''
        stat: { ON OFF }
        '''
        logging.debug(__name__ + ' : Getting burst state')
        return self._visainstrument.ask('SOUR%s:BURS:STAT?' % channel)

    def do_set_burst_mode(self, mode, channel):
        '''
        mode: { TRIG GAT }
        '''
        logging.debug(__name__ + ' : Setting burst gate mode')
        self._visainstrument.write('SOUR%s:BURS:MODE %s' % (channel, source))

    def do_get_burst_mode(self, channel):
        '''
        mode: { TRIG GAT }
        '''
        logging.debug(__name__ + ' : Getting burst gate mode')
        return self._visainstrument.ask('SOUR%s:BURS:MODE?' % channel)

    def do_set_burst_gate_polarity(self, pol, channel):
        '''
        pol: { NORM INV }
        '''
        logging.debug(__name__ + ' : Setting burst gate polarity')
        self._visainstrument.write('SOUR%s:BURS:GATE:POL %s' % (channel, pol))

    def do_get_burst_gate_polarity(self):
        '''
        pol: { NORM INV }
        '''
        logging.debug(__name__ + ' : Getting burst gate polarity')
        return self._visainstrument.ask('SOUR%s:BURS:GATE:POL?' % channel)

    def do_set_burst_phase(self, ph, channel):
        '''
        Phase: { -360 to 360 }
        '''
        logging.debug(__name__ + ' : Setting burst phase')
        self._visainstrument.write('SOUR%s:BURS:PHAS %s' % (channel, ph))

    def do_get_burst_phase(self, channel):
        '''
        Phase: { -360 to 360 }
        '''
        logging.debug(__name__ + ' : Getting burst phase')
        return self._visainstrument.ask('SOUR%s:BURS:PHAS?' % channel)
        
    def do_set_burst_period(self, period, channel):
        '''
        Period: { 1e-6 to 8e3 }
        '''
        logging.debug(__name__ + ' : Setting burst period')
        self._visainstrument.write('SOUR%s:BURS:INT:PER %s' % (period, channel))

    def do_get_burst_period(self, channel):
        '''
        Period: { 1e-6 to 8e3 }
        '''
        logging.debug(__name__ + ' : Getting burst period')
        return self._visainstrument.ask('SOUR%s:BURS:INT:PER?' % channel)

# Function

    def do_set_apply(self, cmd, channel):
        '''
        shape : { 'SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'NOIS', 
                    'ARB', 'DC' }
        '''
        logging.debug(__name__ + ' : Setting waveform parameters')
        self._visainstrument.write('SOUR%s:APPL %s' % (channel, cmd))

    def do_get_apply(self, channel):
        logging.debug(__name__ + ' : Getting waveform parameters')
        return self._visainstrument.ask('SOUR%s:APPL?' % channel)
        
    def do_set_function(self, shape, channel):
        '''
        shape : { 'SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'NOIS', 'ARB', 'DC' }
        '''
        logging.debug(__name__ + ' : Setting function')
        self._visainstrument.write('SOUR%s:FUNC:SHAP %s' % (channel, shape))

    def do_get_function(self, channel):
        '''Get the function for a particular channel'''
        logging.debug(__name__ + ' : Getting function')
        return self._visainstrument.ask('SOUR%s:FUNC:SHAP?' % channel)

# Pulse

    def do_set_pulse_dutycycle(self, dcyc, channel):
        logging.debug(__name__ + ' : Setting pulse duty cycle')
        self._visainstrument.write('SOUR%s:FUNC:PULS:DCYC %s' % (channel, dcyc))
    
    def do_get_pulse_dutycycle(self, channel):
        logging.debug(__name__ + ' : Getting pulse duty cycle')
        return self._visainstrument.ask('SOUR%s:FUNC:PULS:DCYC?' % channel)
        
    def do_set_pulse_trans_leading(self, t1, channel):
        logging.debug(__name__ + ' : Setting pulse duty cycle')
        self._visainstrument.write('SOUR%s:FUNC:PULS:LEAD %s' % (channel, t1))
    
    def do_get_pulse_trans_leading(self, channel):
        logging.debug(__name__ + ' : Getting pulse duty cycle')
        return self._visainstrument.ask('SOUR%s:FUNC:PULS:LEAD?' % channel)
        
    def do_set_pulse_trans_trailing(self, t2, channel):
        logging.debug(__name__ + ' : Setting pulse transition trailing')
        self._visainstrument.write('SOUR%s:FUNC:PULS:TRA %s' % (channel, t2))
    
    def do_get_pulse_trans_trailing(self, channel):
        logging.debug(__name__ + ' : Getting pulse transition trailing')
        return self._visainstrument.ask('SOUR%s:FUNC:PULS:TRA?' % channel)
        
    def do_set_pulse_width(self, width, channel):
        logging.debug(__name__ + ' : Setting pulse width')
        self._visainstrument.write('SOUR%s:FUNC:PULS:WIDT %s' % (channel, width))
    
    def do_get_pulse_width(self, channel):
        logging.debug(__name__ + ' : Getting pulse width')
        return self._visainstrument.ask('SOUR%s:FUNC:PULS:WIDT?' % channel)
    
# Parameters

    def do_set_frequency(self, freq, channel):
        logging.debug(__name__ + ' : Setting frequency')
        self._visainstrument.write('SOUR%s:FREQ %f' % (channel, freq))

    def do_get_frequency(self, channel):
        logging.debug(__name__ + ' : Getting frequency')
        return self._visainstrument.ask('SOUR%s:FREQ?' % channel)

    def do_set_amplitude(self, amp, channel):
        logging.debug(__name__ + ' : Setting amplitude')
        self._visainstrument.write('SOUR%s:VOLT %f' % (channel, amp))

    def do_get_amplitude(self, channel):
        logging.debug(__name__ + ' : Getting amplitude')
        return self._visainstrument.ask('SOUR%s:VOLT?' % channel)

    def do_set_offset(self, offset, channel):
        logging.debug(__name__ + ' : Setting offset')
        self._visainstrument.write('SOUR%s:VOLT:OFFS %f' % (channel, offset))

    def do_get_offset(self, channel):
        logging.debug(__name__ + ' : Getting offset')
        return self._visainstrument.ask('SOUR%s:VOLT:OFFS?' % channel)

    def do_get_load(self, channel):
        load = self._visainstrument.ask( 'OUTP{0}:LOAD?'.format(channel))
        return float(load)

    def do_set_load(self, load, channel):
        self._visainstrument.write('OUTP{0}:LOAD {1:.1f}'.format(channel, load)) 

    def do_get_free_volatile_memory(self, channel):
        logging.debug(__name__ + ' : Getting free volatile memory')
        return int(self._visainstrument.ask(
                    'SOUR{0}:DATA:VOL:FREE?'.format(channel)))

    def get_volatile_memory_catalog(self, channel):
        logging.debug(__name__ + ' : Getting volatile memory catalog')
        catalog = self._visainstrument.ask(
            'SOUR{0}:DATA:VOL:CAT?'.format(channel))
        return catalog.replace('"','').split(',')

    def do_get_display(self):
        '''Get whether the display is on or off'''
        logging.debug(__name__ + ' : Getting display status')
        display_status = self._visainstrument.ask('DISP?')
        return bool(display_status)        

    def do_get_arbitrary_waveform(self, channel):
        '''Get which waveform is selected'''
        logging.debug(__name__ + ' : Getting the waveform')
        return self._visainstrument.ask('SOUR{0}:FUNC:ARB?'.format(channel)).strip('"')

    def do_set_arbitrary_waveform(self, waveform, channel):
        '''Select the waveform'''
        self._visainstrument.write(
            'SOUR{0}:FUNC:ARB "{1}"'.format(channel, waveform))

    def do_get_arbitrary_waveform_frequency(self, channel):
        '''Get the frequency of the arbitrary waveform'''
        freq = self._visainstrument.ask('SOUR{0}:FUNC:ARB:FREQ?'.format(channel))
        return float(freq)

    def do_get_arbitrary_waveform_period(self, channel):
        '''Get the period of the arbitrary waveform'''
        period = self._visainstrument.ask('SOUR{0}:FUNC:ARB:PER?'.format(channel))
        return float(period)

    def do_get_arbitrary_waveform_points(self, channel):
        '''Get the number of points of the selected arbitrary waveform'''
        points = self._visainstrument.ask(
            'SOUR{0}:FUNC:ARB:POIN?'.format(channel))
        return(int(points))

    def do_get_arbitrary_waveform_samplerate(self, channel):
        '''Get the sample rate for the selected arbitrary waveform'''
        sample_rate = self._visainstrument.ask(
            'SOUR{0}:FUNC:ARB:SRAT?'.format(channel))
        return int(float(sample_rate))

    def do_set_arbitrary_waveform_samplerate(self, samplerate, channel):
        '''Set the sample rate for the selected arbitrary waveform'''
        self._visainstrument.write(
                'SOUR{0}:FUNC:ARB:SRAT {1:.12e}'.format(channel, samplerate))

    def do_get_arbitrary_waveform_filter(self, channel):
        '''Get the filter setting for the arbitrary waveform

            Options:
                NORMAL: flattest frequency response
                STEP:   smoothing, minimizing preshoot and overshoot
                OFF:    step from point to point at the sample rate (no smoothing)
        '''
        filter = self._visainstrument.ask(
            'SOUR{0}:FUNC:ARB:FILT?'.format(channel))
        return filter.upper()

    def do_set_arbitrary_waveform_filter(self, filter, channel):
        '''Set the filter setting for the arbitrary waveform

            Options:
                NORMAL: flattest frequency response
                STEP:   smoothing, minimizing preshoot and overshoot
                OFF:    step from point to point at the sample rate (no smoothing)
        '''
        self._visainstrument.write(
            'SOUR{0}:FUNC:ARB:FILT {1}'.format(channel, filter.upper()))

    def do_get_arbitrary_waveform_peak_to_peak(self, channel):
        ptp = self._visainstrument.ask(
            'SOUR{0}:FUNC:ARB:PTP?'.format(channel))
        return float(ptp)

    def write_arbitrary_waveform(self, waveform, name, channel):
        '''Takes a 1d numpy array and writes it to the volatile memory of the 
            waveform generator'''
        src = 'SOUR{0}:'.format(channel)
        if name.upper() in self.get_volatile_memory_catalog(channel): 
            self._visainstrument.write(src + 'DATA:VOL:CLE')

        header_length = 6
        if len(name) > 12:
            raise ValueError('Waveform name can not be longer than 12 characters')
        if len(waveform) < 8:
            raise ValueError('Waveform length has to be larger than 8')

        if waveform.dtype == 'float64':
#            if len(waveform) > 65536:
#                raise ValueError('Waveform length can not be longer than ' + 
#                                '65,536 when using floating point numbers.')
            if waveform.min() < -1.0:
                raise ValueError('Waveform values can not be smaller than -1.0')
            if waveform.max() > 1.0:
                raise ValueError('Waveform values can not be larger than 1.0')
            # make a concatenated string of values
#            value_string = ', '.join(['%.5f' % num for num in waveform])
            value_string = ('#4{0:d}'.format(len(waveform)*4) + 
                                float32(waveform).tostring().encode('hex'))
            message = src + 'DATA:ARB {0:s}, {1:s}'.format(name, value_string)
            print message
            self._visainstrument.write(message)

        elif waveform.dtype == 'int16':
            # make a binary block
            #value_string = ', '.join(['%i' % num for num in waveform])
            value_string = ('#{0:d}{1:06d}'.format(header_length, len(waveform)*2) + 
                                waveform.tostring())
            message = src + 'DATA:ARB:DAC {0}, {1}'.format(name, value_string)
            self._visainstrument.write_raw(message + '\n')
        elif waveform.dtype == 'float32':
            if waveform.min() < -1.0:
                raise ValueError('Waveform values can not be smaller than -1.0')
            if waveform.max() > 1.0:
                raise ValueError('Waveform values can not be larger than 1.0')
            value_string = ('#{0:d}{1:06d}'.format(header_length, len(waveform)*4) +
                                waveform.tostring())
            message = src + 'DATA:ARB {0}, {1}'.format(name, value_string)
#            print message
            self._visainstrument.write_raw(message + '\n')

        self.get('ch{0}_free_volatile_memory'.format(channel))

    def synchronize_waveforms(self):
        self._visainstrument.write('FUNC:ARB:SYNC')
            

