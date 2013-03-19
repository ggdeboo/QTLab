# Yokogawa_7651.py class, to perform the communication between the Wrapper and the device
# Sam Hile <samhile@gmail.com>, 2013
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

class Yokogawa_7651(Instrument):
    '''
    This is the python driver for the Yokogawa 7651 DC voltage source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Yokogawa_7651', address='<GBIP address>, reset=<bool>')

    TODO:
    1) test properly
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initialzes the Yoko, and communicates with the wrapper

        Input:
            name (string)        : name of the instrument
            address (string)     : GPIB address (GPIB::nn)
            reset (bool)         : resets to default values, default=false
         Output:
            None
        '''
        logging.info('Initializing instrument Yoko')
        Instrument.__init__(self, name, tags=['physical'])
                
        # Set constants
        self._address = address
		self._visainstrument = visa.instrument(self._address)
        
        
        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_to_zero')
        self.add_function('off')
        self.add_function('on')

        # Add parameters
        # Implemented parameters        
        self.add_parameter('range', type=types.FloatType, 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=10e-3, maxval=10, units='V')
        self.add_parameter('voltage', type=types.FloatType, tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-12, maxval=12, units='V')
        self.add_parameter('current_limit', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
			minval=5, maxval=120, units='mA')
        self.add_parameter('status', type=types.StringType,
            flags=Instrument.FLAG_SET)


        if reset:
            self.reset()
        else:
            self.get_all()

			
    def __del__(self):
        '''
        Closes up the Yoko driver
		does nothing

        Input:
            None

        Output:
            None
        '''
        logging.info('Deleting Yoko instrument')

		
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
		self.set_to_zero()
        self._visainstrument.write('RC')
		self.on()
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
        self.get_voltage()
        self.get_range()
        self.get_limit()

    def do_get_voltage(self):
        '''
        Reads the voltage of the signal from the instrument

        Input:
            None

        Output:
            volt (float) : voltage in Volts
        '''
        logging.debug(__name__ + ' : get voltage')
        return float(self._visainstrument.ask('OD'))

    def do_set_voltage(self, volt):
        '''
        Set the output voltage for the instrument

        Input:
            volt (float) : voltage in Volts

        Output:
            None
        '''
        logging.debug(__name__ + ' : set voltage to %f' % amp)
        self._visainstrument.write('S%+E' % amp)
		self._visainstrument.write('E' % amp)
		

    def do_get_current_limit(self):
        '''
        Reads the current limit from the instrument

        Input:
            None

        Output:
            lim (float) : current limit (in mA)
        '''
        logging.debug(__name__ + ' : get limit')
		
		str1 = self._visainstrument.ask('OS')
		str2 = self._visainstrument.read()
		str3 = self._visainstrument.read()
		str4 = self._visainstrument.read()
		str5 = self._visainstrument.read()
		assert str5 == 'END\r\n'
		
		#dissect with regex
		matchObj = re.search("(LA)([1234567890.]+)",str4) #extract limit value as string
		lim = matchObj.group(2)
		
        return float(lim)

    def do_set_current_limit(self, lim):
        '''
        Set the current limit

        Input:
            lim (float) : power in mA

        Output:
            None
        '''
        logging.debug(__name__ + ' : set limit to %f' % lim)
        
		self._visainstrument.write('LA%f' % lim)

    def do_get_range(self):
        '''
        Reads the range from the instrument

        Input:
            None

        Output:
            range (float) : range (+/-) in Volts 
        '''
        logging.debug(__name__ + ' : get range')
		
		str1 = self._visainstrument.ask('OS')
		str2 = self._visainstrument.read()
		str3 = self._visainstrument.read()
		str4 = self._visainstrument.read()
		str5 = self._visainstrument.read()
		assert str5 == 'END\r\n'
		
		#dissect with regex
		matchObj = re.search("(R)([23456])",str2) #extract range value as int
		r = matchObj.group(2)
		range = 10**(r-4) #map setting to value in V
		if r == 6
			range = 30
		
        return float(range)

    def do_set_range(self, range):
        '''
        Set the range of the instrument, discrete powers of 10

        Input:
            range (float) : range (+/-) in Volts 

        Output:
            None
        '''
        logging.debug(__name__ + ' : set range to %f' % freq)
		
		r = math.ceil(math.log10(math.abs(range))) + 4 #map 10mV...10V onto R2...R5
		
        self._visainstrument.write('R%d' % r)


    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'on' or 'off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
			if status == 'ON'
				self._visainstrument.write('O1')
			else
				self._visainstrument.write('O0')
				
			self._visainstrument.write('E')
        else:
            raise ValueError('set_status(): can only set on or off')

    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status('off')

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status('on')

   def set_to_zero(self):
        '''
        Set output to 0.00000V

        Input:
            None

        Output:
            None
        '''
        self.set_voltage(0)
