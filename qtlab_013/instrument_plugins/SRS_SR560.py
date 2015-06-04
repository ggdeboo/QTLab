#  -*- coding: utf-8 -*-
# SRS_SR560 driver for SR560 low-noise preamplifier 
# Gabriele de Boo <ggdeboo@gmail.com>

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
import qt

class SRS_SR560(Instrument):
    ''' This is the driver for the SRS SR560
    
    The SR560 amplifier can be controlled with the serial port. It only 
    listens to command so the wrapper doesn't know what the status of the 
    instrument is unless it is reset.

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'SRS_SR560',
        address='<serial port address>',
        reset=<bool>,
        change_display=<bool>,
        change_autozero=<bool>)
    '''

    def __init__(self, name, address, reset=True):
        '''
        Initializes the SRS_SR560, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : serial port address
            reset (bool)            : resets to default values
            change_display (bool)   : If True (default), automatically turn off
                                        display during measurements.
            change_autozero (bool)  : If True (default), automatically turn off
                                        autozero during measurements.
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument SRS_SR560')
        Instrument.__init__(self, name, tags=['physical', 'measure'])

        # Add some global constants
        self.__name__ = name
        self._address = address
        self._visainstrument = visa.SerialInstrument(self._address)
        self._visainstrument.baud_rate = 9600
        self._visainstrument.stop_bits = 2
        self._visainstrument.term_chars = '\r\n'
        self._visainstrument.write('LALL') # Listen all

        self.add_parameter('gain',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.IntType,
            option_list=(1,2,5,10,20,50,100,200,500,1000,2000,5000,10000,20000,
                        50000))
        self.add_parameter('input_coupling',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.StringType,
            option_list=('ground','DC','AC'))
        self.add_parameter('dynamic_reserve',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.StringType,
            format_map = { 0 : 'low noise',
                           1 : 'high DR',
                           2 : 'calibration gains'}) 
        self.add_parameter('filter_mode',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.StringType,
            option_list = ('bypass',
                        '6 dB low pass',
                        '12 dB low pass',
                        '6 dB high pass',
                        '12 dB high pass',
                        'bandpass'))
        self.add_parameter('highpass_frequency',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.FloatType,
            option_list = ( 0.03,
                            .1,
                            .3,
                            1.,
                            3.,
                            10.,
                            30.,
                            100.,
                            300.,
                            1000.,
                            3000.,
                            10000.))
        self.add_parameter('signal_invert',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.BooleanType)
        self.add_parameter('lowpass_frequency',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.FloatType,
            option_list = ( 3e-2, 1e-1, 3e-1, 1e0, 3e0, 1e1, 3e1, 1e2, 
                            3e2, 1e3, 3e3, 1e4, 3e4, 1e5, 300e3, 1e6))
        self.add_parameter('input_source',
            flags=Instrument.FLAG_SOFTGET|Instrument.FLAG_SET,
            type=types.StringType,
            option_list = ('A', 'A-B', 'B'))
        
        self.add_function('reset')

        if reset:
            self.reset()
        else:
            pass

# --------------------------------------
#           functions
# --------------------------------------

    def reset(self):
        '''
        Resets instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting instrument')
        self._visainstrument.write('*RST')

        # reset defaults
        self.set_parameter_options('gain',value=10)
        self.set_parameter_options('input_coupling',value='DC')
        self.set_parameter_options('dynamic_reserve',value='low noise')
        self.set_parameter_options('filter_mode',value='bypass')
        self.set_parameter_options('signal_invert',value=False)
        self.set_parameter_options('input_source',value='A')

    def do_set_gain(self, gain_value):
        '''Set the gain of the amplifier'''
        gain_dict = {1     : 0,
                     2     : 1,
                     5     : 2,
                     10    : 3,
                     20    : 4,
                     50    : 5,
                     100   : 6,
                     200   : 7,
                     500   : 8,
                     1000  : 9,
                     2000  : 10,
                     5000  : 11,
                     10000 : 12,
                     20000 : 13,
                     50000 : 14}
        self._visainstrument.write('GAIN %i' % gain_dict.get(gain_value))

    def do_set_input_coupling(self, coupling):
        '''Set the input coupling of the amplifier'''
        coupling_dict = { 'GROUND' : 0,
                            'DC' : 1,
                            'AC' : 2} 
        self._visainstrument.write('CPLG %i' % coupling_dict.get(coupling))

    def do_set_dynamic_reserve(self, dr):
        self._visainstrument.write('DYNR %i' % int(dr))

    def do_set_filter_mode(self, mode):
        filter_mode_dict = {'BYPASS' : 0,
                        '6 DB LOW PASS'     : 1,
                        '12 DB LOW PASS'    : 2,
                        '6 DB HIGH PASS'    : 3,
                        '12 DB HIGH PASS'   : 4,
                        'BANDPASS'          : 5}
        self._visainstrument.write('FLTM %i' % filter_mode_dict.get(mode))

    def do_set_highpass_frequency(self, hp):
        if self.get_filter_mode() == 'BYPASS':
            logging.warning('Can not set filter frequency while filter mode ' 
                            + 'is bypass')
            return False
        if hp == 0.03:
            command_i = 0
        elif hp == 0.1:
            command_i = 1
        elif hp == 0.3:
            command_i = 2
        elif hp == 1.0:
            command_i = 3
        elif hp == 3.0:
            command_i = 4
        elif hp == 10.0:
            command_i = 5
        elif hp == 30.0:
            command_i = 6
        elif hp == 100.0:
            command_i = 7
        elif hp == 300.0:
            command_i = 8
        elif hp == 1000.0:
            command_i = 9
        elif hp == 3000.0:
            command_i = 10
        elif hp == 10000.0:
            command_i = 11
        self._visainstrument.write('HFRQ %i' % command_i)

    def do_set_signal_invert(self, invert):
        self._visainstrument.write('INVT %i' % invert)

    def do_set_lowpass_frequency(self, lp_freq):
        freq_list = [3e-2, 1e-1, 3e-1, 1e0, 3e0, 1e1, 3e1, 1e2, 
                            3e2, 1e3, 3e3, 1e4, 3e4, 1e5, 300e3, 1e6]
        for idx, freq in enumerate(freq_list):
            if lp_freq == freq:
                break
        self._visainstrument.write('LFRQ %i' % idx)

    def do_set_input_source(self, source):
        if source == 'A':
            self._visainstrument.write('SRCE 0')
        elif source == 'A-B':
            self._visainstrument.write('SRCE 1')
        elif source == 'B':
            self._visainstrument.write('SRCE 2')
