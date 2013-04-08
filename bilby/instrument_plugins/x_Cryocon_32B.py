# Cryocon_32B.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <mcschaafsma@gmail.com>, 2008
# Sam Gorman <samuel.gorman@student.unsw.edu.au>, 2013
# Sam Hile <samhile@gmail.com> 2013
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
import types
import visa
from time import sleep
import logging
import re

class x_Cryocon_32B(Instrument):
    '''
    This is the python driver for the Cryocon62

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Cryocon32B', address='<GPIB address>')

    TODO:
    1) Logging
    2) dataformats
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Cryocon32B, and comunicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('temperature', type=types.FloatType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2),  tags=['measure'])
        self.add_parameter('temp_setpoint', type=types.FloatType,
            channel_prefix='ch%d_',  tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, channels=(1,2))
        self.add_parameter('units', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('sensor_index', type=types.IntType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2),
            format_map = {
            1 : "X56242 - HeatExch",
            2 : "X56922 - SampleProbe",
            3 : "Empty 3",
            4 : "Empty 4"})
        self.add_parameter('vbias', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('channel_name', type=types.StringType,
            channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET, channels=(1,2))
        self.add_parameter('status', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)

            
        self.add_function('reset')
        self.add_function('loop_off')
        self.add_function('loop_on')
        
        if reset:
            self.reset()
        else:
            self.get_all()
        
    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')

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
        logging.info(__name__ + ' : reading all settings from instrument')
        self.get_ch1_temp_setpoint()
        self.get_ch1_temperature()
        self.get_ch1_units()
        self.get_ch1_sensor_index()
        self.get_ch1_vbias()
        self.get_ch1_channel_name()

        self.get_ch2_temp_setpoint()
        self.get_ch2_temperature()
        self.get_ch2_units()
        self.get_ch2_sensor_index()
        self.get_ch2_vbias()
        self.get_ch2_channel_name()
        
        self.get_status()
        

    def do_get_temperature(self, channel):
        '''
        Reads the temperature of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            temperature (float) : Temperature in Kelvin
        '''
        logging.debug(__name__ + ' : get temperature for channel %i' % channel)
        if (channel==1):
            value = self._visainstrument.ask('INPUT? A')
        elif (channel==2):
            value = self._visainstrument.ask('INPUT? B')
        else:
            return 'Channel does not exist'

        try:
            value = float(value)
        except ValueError:
            value = 0.0
        return value
        
    def do_get_temp_setpoint(self, channel):
        '''
        Reads the temperature set point of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            temperature (float) : Temperature setpoint in Kelvin
        '''
        
        logging.debug(__name__ + ' : get temperature of channel %i' % channel)
        str = self._visainstrument.ask('LOOP %i:SETPT?' % (3 - channel))
        #(3 - channel) is impleneted to change the LOOP channel from 1 to 2 and vice versa
        #since the loop 2 is set to channel A and loop 1 is channel B - Ask Giordy??
        
        try:
            #dissect with regex
            matchObj = re.search("(.+)([KCFS])",str) #extract value as string
            assert matchObj.group(2) == "K"
            value = float(matchObj.group(1))
        except ValueError:
            value = 0.0
        return value
    
    
    def do_set_temp_setpoint(self, channel, val):
        '''
        Sets the temperature set point of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel
            val (float) : Temperature setpoint in Kelvin

        Output:
            None
        '''

        logging.debug(__name__ + ' : set temperature of channel %i' % channel)
        self._visainstrument.write('LOOP %i:SETPT %e' % (3 - channel, val))
        #(3 - channel) is impleneted to change the LOOP channel from 1 to 2 and vice versa
        #since the loop 2 is channel A and loop 1 is channel B
    

    def do_get_units(self, channel):
        '''
        Reads the units of the designated channel from the device
        in which the temperature is measured.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            units (string) : units of temperature
        '''
        logging.debug(__name__ + ' : get units for channel %i' % channel)
        if (channel==1):
            return self._visainstrument.ask('INPUT A:UNITS?')
        elif (channel==2):
            return self._visainstrument.ask('INPUT B:UNITS?')
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_sensor_index(self, channel):
        '''
        Reads the user sensor index of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            index (int) : User Sensor index
        '''
        logging.debug(__name__ + ' : get units for channel %i' % channel)
        if (channel==1):
            return int(self._visainstrument.ask('INPUT A:USENIX?'))
        elif (channel==2):
            return int(self._visainstrument.ask('INPUT B:USENIX?'))
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_vbias(self, channel):
        '''
        Reads the bias of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            bias (string) : bias
        '''
        logging.debug(__name__ + ' : get units for channel %i' % channel)
        if (channel==1):
            return self._visainstrument.ask('INPUT A:VBIAS?')
        elif (channel==2):
            return self._visainstrument.ask('INPUT B:VBIAS?')
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_channel_name(self, channel):
        '''
        Reads the name of the designated channel from the device.

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            name (string) : Name of the device
        '''
        if (channel==1):
            return self._visainstrument.ask('INPUT A:NAME?')
        elif (channel==2):
            return self._visainstrument.ask('INPUT B:NAME?')
        else:
            raise ValueError('Channel %i does not exist' % channel)

    def do_get_status(self):
        '''
        Reads the status from the device for the specified channel

        Input:
            none

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : getting status')
        val = self._visainstrument.ask('CONTROL?')
        if (val=='ON'):
            return 'on'
        elif (val=='OFF'):
            return 'off'
        return 'error'
        
    def do_set_status(self, val):
        '''
        Sets the status of the specified channel

        Input:
            val (string)  : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status to %s' % val)
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('CONTROL %s' % val.upper())
        else:
            logging.warning(__name__ + " : state value supplied is not 'ON' or 'OFF' - no action taken")

    def loop_off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status('off')

    def loop_on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status('on')
