# Keithley_2230.py driver for Keithley 2230 power supply
#
# Sam Hile <samhile@gmail.com>
# Daniel Widmann <>
# Gabriele de Boo <ggdeboo@gmail.com>
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
import re

import qt

def bool_to_str(val):
    '''
    Function to convert boolean to 'ON' or 'OFF'
    '''
    if val == True:
        return "ON"
    else:
        return "OFF"

class Keithley_2230(Instrument):
    '''
    This is the driver for the Keithley 2230 Multimeter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2230',
        address='<GBIP address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley_2230, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Keithley_2230')
        Instrument.__init__(self, name, tags=['physical', 'measure'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Add parameters to wrapper
        self.add_parameter('voltage',
            flags=Instrument.FLAG_GETSET,
            units='V', minval=0, maxval=30, type=types.FloatType, 
            channels=(1,2,3))
        self.add_parameter('voltage_reading',
            flags=Instrument.FLAG_GET,
            units='V', minval=0, maxval=30, type=types.FloatType, 
            channels=(1,2,3))
        self.add_parameter('current',
            flags=Instrument.FLAG_GETSET,
            units='A', minval=0, maxval=5, type=types.FloatType, 
            channels=(1,2,3))
        self.add_parameter('current_reading',
            flags=Instrument.FLAG_GET,
            units='A', minval=0, maxval=5, type=types.FloatType, 
            channels=(1,2,3))
        self.add_parameter('active',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType, channels=(1,2,3))
#        self.add_parameter('remote_status',
#            flags=Instrument.FLAG_GETSET,
#            type=types.BooleanType)
        # Add functions to wrapper

        self.set_parameter_bounds('voltage3', 0, 6)
        self.set_parameter_bounds('current1', 0, 1.5)
        self.set_parameter_bounds('current2', 0, 1.5)

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_remote')



        if reset:
            self.reset()
        else:
            pass#self.get_all()


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
        self.get_all()



    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.info('Get all relevant data from device')
        self.get_active1()
        self.get_active2()
        self.get_active3()
        self.get_voltage1()
        self.get_voltage2()
        self.get_voltage3()
        self.get_voltage_reading1()
        self.get_voltage_reading2()
        self.get_voltage_reading3()
        self.get_current_reading1()        
        self.get_current_reading2()        
        self.get_current_reading3()        


########


    def do_get_voltage(self,channel):
        '''
        Get voltage for a specified channel
            in: ch - channel number
            out: voltage [Volts]
        '''
        logging.debug('Getting voltage from instrument')
        self._visainstrument.write('INST:SEL CH%d' % channel)
        return self._visainstrument.ask('SOUR:VOLTAGE?')

    def do_get_voltage_reading(self,channel):
        '''
        Get voltage for a specified channel
            in: ch - channel number
            out: voltage [Volts]
        '''
        logging.debug('Getting voltage from instrument')
        return self._visainstrument.ask('MEAS:VOLT? CH%d' % channel)

    def do_set_voltage(self,v,channel):
        '''
        Get voltage for a specified channel
            in: ch - channel number
                v - voltage [Volts]
            out: none
        '''
        logging.debug('Sending voltage to instrument')
        self._visainstrument.write('INST:SEL CH%d' % channel)
        self._visainstrument.write('SOUR:VOLT %.3fV' % v)
#        self._visainstrument.write('SOUR:APP CH%d,%fV' % (channel,v))
        return

    def do_get_current(self, channel):
        '''
        Get current for a specified channel
            in: ch - channel number
            out: current [A]
        '''
        logging.debug(__name__ + ': Getting current from instrument')
        self._visainstrument.write('INST:SEL CH%d' % channel)
        return self._visainstrument.ask('SOUR:CURR?')

    def do_set_current(self, I, channel):
        '''
        Set current for a specified channel
            in: ch - channel number
            out: current [A]
        '''
        logging.debug(__name__ + ': Setting current to %.3f' % I)
        self._visainstrument.write('INST:SEL CH%d' % channel)
        self._visainstrument.write('SOUR:CURR %.3fA' % I)
        return

    def do_get_current_reading(self, channel):
        '''
        Get current reading for a specified channel
            in: ch - channel number
            out: 
        '''
        logging.debug(__name__ + ': Getting current from instrument')
        return self._visainstrument.ask('MEAS:CURR? CH%d' % channel)
        
    def do_get_active(self,channel):
        '''
        Get voltage for a specified channel
            in: ch - channel number
            out: active_status [Boolean]
        '''
        logging.debug('Getting active status from instrument')
        self._visainstrument.write('INST:SEL CH%d' % channel)
        answer = self._visainstrument.ask('CHAN:OUTP?')
        if answer == '1':
            return True
        elif answer =='0':
            return False
        else:
            logging.warning(__name__ + ': responded with unexpected answer: %s' % answer)

    def do_set_active(self,a,channel):
        '''
        Get voltage for a specified channel
            in: ch - channel number
                a - active_status [Boolean]
            out: none
        '''
        logging.debug('Sending active status to instrument')
        self._visainstrument.write('INST:SEL CH%d' % channel)
        self._visainstrument.write('CHAN:OUTP %s' % bool_to_str(a))
        return

    def set_remote(self):
        self._visainstrument.write('SYST:REM')



