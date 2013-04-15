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
            units='A', channels=(1, 2), tags=['sweep'])
        self.add_parameter('voltage', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='V', channels=(1, 2), tags=['sweep'])
        self.add_parameter('limit', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='AU', channels=(1, 2))
        self.add_parameter('mode', type=types.IntType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2),
            format_map = {
            0 : "DC Voltage",
            1 : "DC Current"})
        self.add_parameter('line_freq', type=types.IntType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='Hz')
        self.add_parameter('range', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='AU', channels=(1, 2))
        self.add_parameter('autorange', type=types.BooelanType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2))
        self.add_parameter('status', type=types.FloatType, 
            flags=Instrument.FLAG_GET)


        self.add_function('reset')
        self.add_function('get_all')

        self.add_function('off')
        self.add_function('on')
        
        if reset:
            self.reset()
        else:
            self.get_all()


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
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        
        self.get_ch1_current()
        self.get_ch1_voltage()
        self.get_ch1_limit()
        self.get_ch1_range()
        self.get_ch1_mode()

        self.get_ch2_current()
        self.get_ch2_voltage()
        self.get_ch2_limit()
        self.get_ch2_range()
        self.get_ch2_mode()
        
        self.get_line_freq
        self.get_status
        

    # communication with device
    
    
    def do_get_mode(self, channel):
        '''
        Gets the mode from channel A (1) or B (2) and updates the wrapper
        
        Input:
            Channel (int) = 1 (A) or 2 (B)
             
        Output:
            Mode of the channel (int) ((0) DCVOLTS or (1) DCAMPS)
        '''
        
        logging.debug(__name__ + ' :Getting functional mode value of channel %i' % channel)
        if channel == 1:
            mode = self._visainstrument.ask('print(smua.source.func)')
                if mode == smua.OUTPUT_DCVOLTS:
                    return 0
                elif mode == smua.OUTPUT_DCAMPS:
                    return 1
                else:
                    raise ValueError('Invalid function mode - Select DCVOLTS (0) or DCAMPS (1)')
        elif channel == 2:
            mode = self._visainstrument.ask('print(smub.source.func)')
                if mode == smub.OUTPUT_DCVOLTS:
                    return 0
                elif mode == smub.OUTPUT_DCAMPS:
                    return 1
                else:
                    raise ValueError('Invalid function mode - Select DCVOLTS (0) or DCAMPS (1)')
        else:
            raise ValueError('Invalid channel')
            

    def do_set_mode(self, channel, val):
                '''
        Sets the mode from channel A (1) or B (2) and updates the wrapper
        
        Input:
            Channel (int) = 1 (A) or 2 (B)
            val = (0) DCVOLTS or (1) DCAMPS
             
        Output:
            None
        '''
        logging.debug(__name__ + ' :Setting functional mode value of channel %i' % channel)
        if channel == 1:
            if val == 0:
                self._visainstrument.write('smua.source.func=smua.OUTPUT_DCVOLTS')
            elif val == 1:
                self._visainstrument.write('smua.source.func=smua.OUTPUT_DCAMPS')
            else:
                raise ValueError('Invalid function mode - Select DCVOLTS (0) or DCAMPS (1)')
        elif channel == 2:
            if val == 0:
                self._visainstrument.write('smub.source.func=smub.OUTPUT_DCVOLTS')
            elif val == 1:
                self._visainstrument.write('smub.source.func=smub.OUTPUT_DCAMPS')
            else:
                raise ValueError('Invalid function mode - Select DCVOLTS (0) or DCAMPS (1)')
        else:
            raise ValueError('Invalid channel')
            
    
    def do_get_current(self, channel, mode):
        '''
        Gets the current from channel A (1) or B (2) and updates the wrapper
        
        Input:
            Channel (int) = 1 (A) or 2 (B)
            mode (int) = Mode of the channel
             
        Output:
            Current value of the channel (float)
        '''
        
        logging.debug(__name__ + ' :Getting current value of channel %i' % channel)
        if channel == 1:
            return float(self._visainstrumnet.ask('print(smua.measure.i())'))
        elif channel == 2:
            return float(self._visainstrumnet.ask('print(smub.measure.i())'))
        else:
            raise ValueError('Invalid Channel')
            
    
    def do_set_current(self, channel, mode, val):
        '''
        Sets the current from channel A (1) or B (2) and updates the wrapper
        
        Input:
            Channel (int) = 1 (A) or 2 (B)
            mode (int) = Mode of the channel
            val (float) = The current to be set
             
        Output:
            None
        '''
    
        logging.debug(__name__ + ' :Setting current value of channel %i' % channel)
        if channel == 1:
            self._visainstrumnet.write('smua.source.leveli=%i' % val)
        elif channel == 2:
            self._visainstrument.write('smub.source.leveli=%i' % val)
        else:
            raise ValueError('Invalid channel')
            
            
    def do_get_voltage(self, channel, mode):
        '''
        Gets the voltage from channel A (1) or B (2) and updates the wrapper
        
        Input:
            Channel (int) = 1 (A) or 2 (B)
            mode (int) = Mode of the channel
             
        Output:
            Voltage value of the channel
        '''
        
        logging.debug(__name__ + ' :Getting voltage value of channel %i' % channel)
        if channel == 1:
            return float(self._visainstrumnet.ask('print(smua.measure.v())'))
        elif channel == 2:
            return float(self._visainstrumnet.ask('print(smub.measure.v())'))
        else:
            raise ValueError('Invalid Channel')
            
    
    def do_set_voltage(self, channel, mode, val):
        '''
        Sets the voltage from channel A (1) or B (2) and updates the wrapper
        
        Input:
            Channel (int) = 1 (A) or 2 (B)
            mode (int) = Mode of the channel
            val (float) = Voltage to be set.
             
        Output:
            None
        '''
    
        logging.debug(__name__ + ' :Setting current value of channel %i' % channel)
        if channel == 1:
            self._visainstrumnet.write('smua.source.levelv=%i' % val)
        elif channel == 2:
            self._visainstrument.write('smub.source.levelv=%i' % val)
        else:
            raise ValueError('Invalid channel')
            

    def do_get_autorange(self, channel, mode):
        '''
        Get status of autorange (ON or OFF).
        returns the value of the autorange value for the source mode

        Input:
            channel (int) = 1 (A) or 2 (B)
            mode (int) = Mode of the channel

        Output:
            result (boolean)
        '''
        if channel == 0 and mode == 0:
            auto = self._visainstrument.ask('print(smua.source.autorangev)')
            if auto == smua.AUTORANGE_OFF:
                return False
            if auto == smua.AUTORANGE_ON:
                return True
            else:
                raise ValueError('Invalid autorange setting')
        elif channel == 0 and mode == 1:
            auto = self._visainstrument.ask('print(smua.source.autorangei)')
            if auto == smua.AUTORANGE_OFF:
                return False
            if auto == smua.AUTORANGE_ON:
                return True
            else:
                raise ValueError('Invalid autorange setting')
        elif channel == 1 and mode == 0:
            auto = self._visainstrument.ask('print(smub.source.autorangev)')
            if auto == smua.AUTORANGE_OFF:
                return False
            if auto == smua.AUTORANGE_ON:
                return True
            else:
                raise ValueError('Invalid autorange setting')
        elif channel == 1 and mode == 1:
            auto = self._visainstrument.ask('print(smub.source.autorangei)')
            if auto == smua.AUTORANGE_OFF:
                return False
            if auto == smua.AUTORANGE_ON:
                return True
            else:
                raise ValueError('Invalid autorange setting')
        else:
            raise ValueError('Invalid mode and/or channel')
        
    
    def do_set_autorange(self, channel, mode, val):
        '''
        Switch autorange on or off.
        If mode=None the current mode is assumed

        Input:
            val (boolean)
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        logging.debug('Set autorange to %s ' % val)
        val = bool_to_str(val)
        self._set_func_par_value(mode, 'RANG:AUTO', val)
    

    
        
    