# Keithley_2602.py class, to perform the communication between the Wrapper and the device
# Sam Gorman <samuel.gorman@student.unsw.edu.au>, 2013
# Gabriele de Boo <g.deboo@student.unsw.edu.au>, 2016
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


class Keithley_2602(Instrument):
    '''
    This is the python driver for the Keithley 2602 System SourceMeter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2602', 
                address='<GBIP address>, reset=<bool>')

    TODO:
        1) Implement different measuring functions. This means irrespective 
           of the source func you are able to measure current, voltage, 
            resistance or power. This is achieved by using the 
            display.smuX.measure.func command (Details on P312 of manual). 
            However, this involves altering the rest of the commands in order 
            to incorporate the new features.
    '''


    def __init__(self, name, address, reset=False, step=10e-3, delay=10, 
                    upperlim=12, lowerlim=-12):
        '''
        Initialzes the source meter, and communicates with the wrapper

        Input:
            name (string)        : name of the instrument
            address (string)     : VISA address (GPIB::nn)
         Output:
            None
            
        '''
        logging.info(__name__ + ' : Initializing instrument Yoko')
        Instrument.__init__(self, name, tags=['physical'])

        # Set constants
        self._address = address
        rm = visa.ResourceManager()
        self._visainstrument = rm.open_resource(self._address)
        self._visainstrument.read_termination = '\n'
        if self._visainstrument.interface_type == 4:
            logging.info('Serial communication')
            self._visainstrument.baud_rate = 115200
            self._visainstrument.clear()
        idn_string = ''
        while not idn_string.startswith('Keithley'):        
            idn_string = self._visainstrument.query('*IDN?')
        print(idn_string)

        # Add parameters
        # Implemented parameters        
        self.add_parameter('current', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='A', channels=(1, 2), tags=['sweep', 'measure'],
            maxstep=0.1, stepdelay=100)
        self.add_parameter('voltage', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='V', channels=(1, 2), tags=['sweep', 'measure'], 
            minval=lowerlim, maxval=upperlim, maxstep=step, stepdelay=delay)
        self.add_parameter('limit', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='AU', channels=(1, 2))
        self.add_parameter('output_mode', type=types.IntType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2),
            format_map = {
            0 : "DCAMPS",
            1 : "DCVOLTS"})
        self.add_parameter('output_status', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2),
            format_map = {
            0 : False,
            1 : True})
        self.add_parameter('line_freq', type=types.IntType, 
            flags=Instrument.FLAG_GET, units='Hz')
        self.add_parameter('source_range', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='AU', channels=(1, 2))
        self.add_parameter('measure_range', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units='AU', channels=(1, 2))
        self.add_parameter('source_autorange', type=types.IntType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2),
            format_map = {
            0 : "OFF",
            1 : "ON"})
            
        self.add_parameter('nplc', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=0.001, maxval = 25)
            
        self.add_parameter('measure_autorange', type=types.IntType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2),
            format_map = {
            0 : "OFF",
            1 : "ON"})

        self.add_parameter('sense_mode', type=types.IntType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2),
            format_map = {
                0    : 'local',
                1    : 'remote'
                })
        self.add_parameter('in_compliance', type=types.BooleanType,
            flags=Instrument.FLAG_GET,
            channels=(1, 2),
            )

        self._visainstrument.write('beeper.enable=0')
        self.add_function('reset')      
        
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

    def get_all(self):
        '''
        Get all parameters from instrument
        '''
        for channel in [1, 2]:
            self.get('output_mode{0}'.format(channel))
            self.get('output_status{0}'.format(channel))
            self.get('source_range{0}'.format(channel))
            self.get('nplc{0}'.format(channel))
            self.get('sense_mode{0}'.format(channel))
            self.get('in_compliance{0}'.format(channel))

    # communication with device

    def do_get_output_mode(self, channel):
        '''
        Gets the mode from channel A (1) or B (2) and updates the wrapper

        Input:
            Channel (int) = 1 (A) or 2 (B)

        Output:
            Mode of the channel (int) ((0) DCAMPS or (1) DCVOLTS)
        '''

        logging.debug(__name__ + 
            ' :Getting functional mode value of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            return mode
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
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

        logging.debug(__name__ + 
            ' :Setting functional mode value of channel %i' % channel)
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
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                current = float(self._visainstrument.query('print(smua.source.leveli)'))
                return current
            elif mode == 1:
                current = float(self._visainstrument.query('print(smua.measure.i())'))
                return current
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                current = float(self._visainstrument.query('print(smub.source.leveli)'))
                return current
            elif mode == 1:
                current = float(self._visainstrument.query('print(smub.measure.i())'))
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
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.source.leveli=%e' % val)
            else:
                raise ValueError('Cannot set current. Change to DCAMPS to set current')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
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
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                voltage = self._visainstrument.query('print(smua.measure.v())')
                return voltage
            elif mode == 1:
                voltage = self._visainstrument.query('print(smua.source.levelv)')
                return voltage
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                voltage = self._visainstrument.query('print(smub.measure.v())')
                return voltage
            elif mode == 1:
                voltage = self._visainstrument.query('print(smub.source.levelv)')
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
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 1:
                self._visainstrument.write('smua.source.levelv=%e' % val)
            else:
                raise ValueError('Cannot set voltage. Change to DCVOLTS to set voltage')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
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
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 1:
                limit = float(self._visainstrument.query('print(smua.source.limiti)'))
                return limit
            elif mode == 0:
                limit = float(self._visainstrument.query('print(smua.source.limitv)'))
                return limit
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 1:
                limit = float(self._visainstrument.query('print(smub.source.limiti)'))
                return limit
            elif mode == 0:
                limit = float(self._visainstrument.query('print(smub.source.limitv)'))
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
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 1:
                self._visainstrument.write('smua.source.limiti=%e' % val)
            elif mode == 0:
                self._visainstrument.write('smua.source.limitv=%e' % val)
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 1:
                self._visainstrument.write('smub.source.limiti=%e' % val)
            elif mode == 0:
                self._visainstrument.write('smub.source.limitv=%e' % val)
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')
    
    def do_set_nplc(self, nplc, channel):
        # Set speed (nplc = 0.001 to 25)
        if channel == 1:        
            self._visainstrument.write('smua.measure.nplc=%e' % nplc)
        elif channel == 2:
            self._visainstrument.write('smub.measure.nplc=%e' % nplc)
        else:
            raise ValueError('Invalid channel')
    
    def do_get_nplc(self, channel):
        # Set speed (nplc = 0.001 to 25)
        if channel == 1:        
            return float(self._visainstrument.query('print(smua.measure.nplc)'))
        elif channel == 2:
            return float(self._visainstrument.query('print(smub.measure.nplc)'))
        else:
            raise ValueError('Invalid channel')    

    def do_get_output_status(self, channel):
        '''
        Gets the status of the output voltage or current (either ON or OFF)
        
        Input:
            Channel (int) = (1) A or (2) B
            
        Output:
            status (int) = OFF (0) or ON (0)
        '''

        logging.debug(__name__ + ' :Getting the output status of channel %i' % channel)
        if channel == 1:
            status = int(float(self._visainstrument.query('print(smua.source.output)')))
            return bool(status)
        elif channel == 2:
            status = int(float(self._visainstrument.query('print(smub.source.output)')))
            return bool(status)
        else:
            raise ValueError('Invalid channel')

    def do_set_output_status(self, val, channel):
        '''
        Sets the status of the output voltage or current (either ON or OFF)
        
        Input:
            Channel (int) = (1) A or (2) B
            val (int) = OFF (0) or ON (0)
            
        Output:
            None
        '''

        logging.debug(__name__ + ' :Setting the output status of channel %i' % channel)
        if channel == 1:
            self._visainstrument.write('smua.source.output=%i' % val)
        elif channel == 2:
            self._visainstrument.write('smub.source.output=%i' % val)
        else:
            raise ValueError('Invalid channel')
            
    
    def do_get_source_autorange(self, channel):
        '''
        Gets the status of the autorange function

        Input:
            Channel (int) = (1) A or (2) B

        Output:
            autorange (int) = OFF (0) or ON (1)
        '''

        logging.debug(__name__ + ' :Getting the source autorange status of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                autorange = int(float(self._visainstrument.query('print(smua.source.autorangei)')))
                return autorange
            elif mode == 1:
                autorange = int(float(self._visainstrument.query('print(smua.source.autorangev)')))
                return autorange
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                autorange = int(float(self._visainstrument.query('print(smub.source.autorangei)')))
                return autorange
            elif mode == 1:
                autorange = int(float(self._visainstrument.query('print(smub.source.autorangev)')))
                return autorange
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')


    def do_set_source_autorange(self, val, channel):
        '''
        Sets the status of the autorange function

        Input:
            Channel (int) = (1) A or (2) B
            val (int) = OFF (0) or ON (1)
            
        Output:
            None
        '''

        logging.debug(__name__ + ' :Setting the source autorange status of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.source.autorangei=%i' % val)
            elif mode == 1:
                self._visainstrument.write('smua.source.autorangev=%i' % val)
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                self._visainstrument.write('smub.source.autorangei=%i' % val)
            elif mode == 1:
                self._visainstrument.write('smub.source.autorangev=%i' % val)
            else:
                raise ValueError('Invalid mode')
        else:
             raise ValueError('Invalid channel')


    def do_get_source_range(self, channel):
        '''
        Gets the output source range of the Source Meter

        Input:
            channel (int) = Channel (int) = (1) A or (2) B

        Output:
            Range (float) = Value of the range the source is set to
        '''

        logging.debug(__name__ + ' :Getting the range of the source of SourceMeter')
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                range = float(self._visainstrument.query('print(smua.source.rangei)'))
                return range
            elif mode == 1:
                range = float(self._visainstrument.query('print(smua.source.rangev)'))
                return range
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                range = float(self._visainstrument.query('print(smub.source.rangei)'))
                return range
            elif mode == 1:
                range = float(self._visainstrument.query('print(smub.source.rangev)'))
                return range
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')


    def do_set_source_range(self, val, channel):
        '''
        Sets the output source range of the Source Meter

        Input:
            channel (int) = Channel (int) = (1) A or (2) B
            val (float) = Value of which the range is to be set

        Output:
            None
        '''
        logging.debug(__name__ + ' :Setting the range of the source of SourceMeter')
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.source.rangei=%e' % val)
            elif mode == 1:
                self._visainstrument.write('smua.source.rangev=%e' % val)
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                self._visainstrument.write('smub.source.rangei=%e' % val)
            elif mode == 1:
                self._visainstrument.write('smub.source.rangev=%e' % val)
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')


    def do_get_measure_autorange(self, channel):
        '''
        Gets the status of the measure autorange function

        Input:
            Channel (int) = (1) A or (2) B

        Output:
            autorange (int) = OFF (0) or ON (1)
        '''

        logging.debug(__name__ + ' :Getting the measure autorange status of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                autorange = int(float(self._visainstrument.query(
                    'print(smua.measure.autorangev)')))
                return autorange
            elif mode == 1:
                autorange = int(float(self._visainstrument.query(
                    'print(smua.measure.autorangei)')))
                return autorange
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query(
                'print(smub.source.func)')))
            if mode == 0:
                autorange = int(float(self._visainstrument.query(
                    'print(smub.measure.autorangev)')))
                return autorange
            elif mode == 1:
                autorange = int(float(self._visainstrument.query(
                    'print(smub.measure.autorangei)')))
                return autorange
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')


    def do_set_measure_autorange(self, val, channel):
        '''
        Sets the status of the measure autorange function

        Input:
            Channel (int) = (1) A or (2) B
            val (int) = OFF (0) or ON (1)
            
        Output:
            None
        '''

        logging.debug(__name__ + ' :Setting the measure autorange status of channel %i' % channel)
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.measure.autorangev=%i' % val)
            elif mode == 1:
                self._visainstrument.write('smua.measure.autorangei=%i' % val)
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                self._visainstrument.write('smub.measure.autorangev=%i' % val)
            elif mode == 1:
                self._visainstrument.write('smub.measure.autorangei=%i' % val)
            else:
                raise ValueError('Invalid mode')
        else:
             raise ValueError('Invalid channel')

    def do_get_measure_range(self, channel):
        '''
        Gets the measure range of the Source Meter

        Input:
            channel (int) = Channel (int) = (1) A or (2) B

        Output:
            Range (float) = Value of the range the source is set to
        '''

        logging.debug(__name__ + ' :Getting the measure range of SourceMeter')
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                range = float(self._visainstrument.query('print(smua.measure.rangev)'))
                return range
            elif mode == 1:
                range = float(self._visainstrument.query('print(smua.measure.rangei)'))
                return range
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                range = float(self._visainstrument.query('print(smub.measure.rangev)'))
                return range
            elif mode == 1:
                range = float(self._visainstrument.query('print(smub.measure.rangei)'))
                return range
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')


    def do_set_measure_range(self, val, channel):
        '''
        Sets the measure range of the Source Meter

        Input:
            channel (int) = Channel (int) = (1) A or (2) B
            val (float) = Value of which the range is to be set

        Output:
            None
        '''
        logging.debug(__name__ + ' :Setting the measure range of SourceMeter')
        if channel == 1:
            mode = int(float(self._visainstrument.query('print(smua.source.func)')))
            if mode == 0:
                self._visainstrument.write('smua.measure.rangev=%e' % val)
            elif mode == 1:
                self._visainstrument.write('smua.measure.rangei=%e' % val)
            else:
                raise ValueError('Invalid mode')
        elif channel == 2:
            mode = int(float(self._visainstrument.query('print(smub.source.func)')))
            if mode == 0:
                self._visainstrument.write('smub.measure.rangev=%e' % val)
            elif mode == 1:
                self._visainstrument.write('smub.measure.rangei=%e' % val)
            else:
                raise ValueError('Invalid mode')
        else:
            raise ValueError('Invalid channel')

    def do_get_sense_mode(self, channel):
        '''
        Get the sense mode.

        Input:
            None
        
        Output:
            local
            remote
        '''
        logging.debug(__name__ + ' : Getting the sense mode')
        if channel == 1:
            chan_string = 'a'
        elif channel == 2:
            chan_string = 'b'
        else:
            raise ValueError('Invalid channel')
        
        reply = self._visainstrument.query(
            'print(smu{0}.sense)'.format(chan_string))
        return int(float(reply))

    def do_get_in_compliance(self, channel):
        '''
        Get whether the channel is in compliance
        '''
        if channel == 1:
            chan_string = 'a'
        elif channel == 2:
            chan_string = 'b'
        else:
            raise ValueError('Invalid channel')
        reply = self._visainstrument.query(
            'print(smu{0}.source.compliance)'.format(chan_string))
        if reply == 'true':
            return True
        elif reply == 'false':
            return False
        else:
            logging.warning('incorrect response to compliance query')
        
    def do_get_line_freq(self):
        '''
        Gets the line freqency of the Source Meter
        
        Input:
            None
        
        Output:
            Line freq (int) = 50 or 60 Hz
        '''
        
        logging.debug(__name__ + ' :Getting the line frequency of SourceMeter')
        frequency = int(float(self._visainstrument.query('print(localnode.linefreq)')))
        return frequency
        if frequency != 50 | frequency != 60:
            raise ValueError('Line frequency not configured')
