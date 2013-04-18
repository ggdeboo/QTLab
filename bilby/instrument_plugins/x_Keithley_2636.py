# Keithley_2636.py class, to perform the communication between the Wrapper and the device
# Sam Gorman <samuel.gorman@student.unsw.edu.au>, 2013
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
import numpy
import math
import re


class x_Keithley_2636(Instrument):
    '''
    This is the python driver for the Keithley 2636 System SourceMeter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'x_Keithley_2636', address='<GBIP address>, reset=<bool>')

    TODO:
    1) All
    '''


    def __init__(self, name, address, reset=False):
        '''
        Initialzes the Yoko, and communicates with the wrapper

        Input:
            name (string)        : name of the instrument
            address (string)     : GPIB address (GPIB::nn)
         Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument Yoko')
        Instrument.__init__(self, name, tags=['physical'])

        # Set constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)


        # Add parameters
        # Implemented parameters        
        self.add_parameter('current', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='A', channels=(1, 2), tags=['sweep', 'measure'])
        self.add_parameter('voltage', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='V', channels=(1, 2), tags=['sweep', 'measure'])
        self.add_parameter('limit', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='AU', channels=(1, 2))
        self.add_parameter('output_mode', type=types.IntType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,            
            channels=(1, 2), 
            format_map = {
            0 : "DCAMPS",
            1 : "DCVOLTS"})
        # self.add_parameter('line_freq', type=types.IntType, 
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # units='Hz')
        # self.add_parameter('range', type=types.FloatType, 
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # units='AU', channels=(1, 2))
        # self.add_parameter('source_autorange', type=types.BooleanType, 
            # flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            # channels=(1, 2))
        # self.add_parameter('status', type=types.FloatType, 
            # flags=Instrument.FLAG_GET)


        self.add_function('reset')
        # self.add_function('get_all')

        # self.add_function('off')
        # self.add_function('on')

        # if reset:
            # self.reset()
        # else:
            # self.get_all()


    def reset(self):
        '''
        Resets the instrument to default values (unsafe for device)
        0V, voltage output, limit 120mA, range 10mV, output on, 

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visaintrsument.write(reset())
        #self.get_all()

    # def get_all(self):
        # '''
        # Reads all implemented parameters from the instrument,
        # and updates the wrapper.

        # Input:
            # None

        # Output:
            # None
        # '''
        # logging.info(__name__ + ' : get all')

        # self.get_ch1_mode()
        # self.get_ch1_current()
        # self.get_ch1_voltage()
        # self.get_ch1_limit()
        # self.get_ch1_range()

        # self.get_ch2_mode()
        # self.get_ch2_current()
        # self.get_ch2_voltage()
        # self.get_ch2_limit()
        # self.get_ch2_range()

        # self.get_line_freq
        # self.get_status


    # communication with device


    def do_get_output_mode(self, channel):
        '''
        Gets the mode from channel A (1) or B (2) and updates the wrapper

        Input:
            Channel (int) = 1 (A) or 2 (B)

        Output:
            Mode of the channel (int) ((0) DCAMPS or (1) DCVOLTS)
        '''

        logging.debug(__name__ + ' :Getting functional mode value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            return mode
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            return mode
        else:
            raise ValueError('Invalid channel')

# figure out what is going on here val and channel are switched?
    def do_set_output_mode(self, val, channel):
        '''
        Sets the mode from channel A (1) or B (2) and updates the wrapper

        Input:
            Channel (int) = 1 (A) or 2 (B)
            val = (0) DCAMPS or (1) DCVOLTS

        Output:
            None
        '''

        logging.debug(__name__ + ' :Setting functional mode value of channel %i' % channel)
        if channel == 1:
            self._visainstrument.write('smua.source.func=%i' % val)
        elif channel == 2:
            self._visainstrument.write('smub.source.func=%i' % val)
        else:
            raise ValueError('Invalid channel')


    def do_get_current(self, channel):
        '''
        Get the current from channel A or channel B

        Input:
            Channel (int) = 1 (A) or 2 (B)
            output_mode = (0) DCAMPS or (1) DCVOLTS

        Output:
            Current of the channel A or B
        '''

        logging.debug(__name__ + ' :Getting current value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            if mode == 0:
                current = float(self._visainstrument.ask('print(smua.source.leveli)'))
                return current
            elif mode == 1:
                current = float(self._visainstrument.ask('print(smua.measure.i())'))
                return current
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            if mode == 0:
                current = float(self._visainstrument.ask('print(smub.source.leveli)'))
                return current
            elif mode == 1:
                current = float(self._visainstrument.ask('print(smub.measure.i())'))
                return current
        else:
            raise ValueError('Invalid channel')


    def do_set_current(self, val, channel):
        '''
        set the current from channel A or channel B

        Input:
            Channel (int) = 1 (A) or 2 (B)
            output_mode = (0) DCAMPS or (1) DCVOLTS 

        Output:
            Current of the channel A or B # CHNAGE THIS
        '''

        logging.debug(__name__ + ' :Setting current value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.source.leveli=%e' % val)
            else:
                raise ValueError('Cannot set current. Change to DCAMPS to set current')
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            if mode == 0:
                self._visainstrument.write('smub.source.leveli=%e' % val)
            else:
                raise ValueError('Cannot set current. Change to DCAMPS to set current')
        else:
            raise ValueError('Invalid channel')


    def do_get_voltage(self, channel):
        '''
        Get the current from channel A or channel B

        Input:
            Channel (int) = 1 (A) or 2 (B)

        Output:
            Voltage of the channel A or B
        '''

        logging.debug(__name__ + ' :Getting voltage value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            if mode == 0:
                voltage = self._visainstrument.ask('print(smua.measure.v())')
                return voltage
            elif mode == 1:
                voltage = self._visainstrument.ask('print(smua.source.levelv)')
                return voltage
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            if mode == 0:
                voltage = self._visainstrument.ask('print(smub.measure.v())')
                return voltage
            elif mode == 1:
                voltage = self._visainstrument.ask('print(smub.source.levelv)')
                return voltage
        else:
            raise ValueError('Invalid channel')


    def do_set_voltage(self, val, channel):        
        '''
        set the current from channel A or channel B

        Input:
            Channel (int) = 1 (A) or 2 (B)
            val (float) = Voltage that is to be set

        Output:
            None
        '''

        logging.debug(__name__ + ' :Setting voltage value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            if mode == 1:
                self._visainstrument.write('smua.source.levelv=%e' % val)
            else:
                raise ValueError('Cannot set voltage. Change to DCVOLTS to set voltage')
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            if mode == 1:
                self._visainstrument.write('smub.source.levelv=%e' % val)
            else:
                raise ValueError('Cannot set voltage. Change to DCVOLTS to set voltage')
        else:
            raise ValueError('Invalid channel')

    def do_get_limit(self, channel):
        '''
        Get the limit that has been set from either channel A or Channel B
        
        Input:
           Channel (int) = 1 (A) or 2 (B)
           
        Output:
           Limit of the voltage (DCAMPS) or current (DCVOLTS) for channel A or channel B
        '''

        logging.debug(__name__ + ' :Getting the limit value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            if mode == 0:
                limit = float(self._visainstrument.ask('print(smua.source.limitv)'))
                return limit
            elif mode == 1:
                limit = float(self._visainstrument.ask('print(smua.source.limiti)'))
                return limit
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            if mode == 0:
                limit = float(self._visainstrument.ask('print(smub.source.limitv)'))
                return limit
            elif mode == 1:
                limit = float(self._visainstrument.ask('print(smub.source.limiti)'))
                return limit
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')


    def do_set_limit(self, val, channel):
        '''
        Set the limit that has been set from either channel A or Channel B
        
        Input:
           Channel (int) = 1 (A) or 2 (B)
           val (float) = Value to which the limit will be set
           
        Output:
           None
        '''

        logging.debug(__name__ + ' :Setting the limit value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.ask('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.source.limitv=%e' % val)
            elif mode == 1:
                self._visainstrument.write('smua.source.limiti=%e' % val)
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.ask('print(smub.source.func)')))
            if mode == 0:
                self._visainstrument.write('smub.source.limitv=%e' % val)
            elif mode == 1:
                self._visainstrument.write('smub.source.limiti=%e' % val)
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channe;')
