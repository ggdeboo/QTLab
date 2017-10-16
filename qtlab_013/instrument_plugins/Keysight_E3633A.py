# Keysight_E3633A.py driver for Keysight E3633A power supply
#
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
import qt

class Keysight_E3633A(Instrument):
    '''
    This is the driver for the Keysight E3633A power supply

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keysight_E3633A',
        address='<GBIP address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley E3633A power supply

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Keysight E3633A on {0}'.format(
            address))
        Instrument.__init__(self, name, tags=['physical', 'measure'])

        # Add some global constants
        self._address = address
        RM = visa.ResourceManager()
        self._visainstrument = RM.open_resource(self._address)
        self._visainstrument.read_termination = '\n'

        # Add parameters to wrapper
        self.add_parameter('voltage',
            flags=Instrument.FLAG_GETSET,
            units='V', minval=0.0, maxval=8.0, type=types.FloatType, 
            )
        self.add_parameter('voltage_reading',
            flags=Instrument.FLAG_GET,
            units='V', type=types.FloatType, 
            )
        self.add_parameter('current',
            flags=Instrument.FLAG_GETSET,
            units='A', minval=0.0, maxval=22.0, type=types.FloatType, 
            )
        self.add_parameter('current_reading',
            flags=Instrument.FLAG_GET,
            units='A', type=types.FloatType, 
            )
        self.add_parameter('active',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
#        self.add_parameter('remote_status',
#            flags=Instrument.FLAG_GETSET,
#            type=types.BooleanType)
        # Add functions to wrapper


        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_remote')
        self.add_function('ramp_current')


        if reset:
            self.reset()
        else:
            self.get_all()

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
        self.get_active()
        self.get_voltage()
        self.get_current()
        self.get_voltage_reading()
        self.get_current_reading()        

    def do_get_voltage(self):
        '''
        Get voltage for a specified channel
            in: ch - channel number
            out: voltage [Volts]
        '''
        logging.debug('Getting voltage from instrument')
        response = self._visainstrument.query('APPL?').strip('"')
        voltage = float(response.split(',')[0])
        return voltage

    def do_get_voltage_reading(self):
        '''
        Get voltage reading
            in:
            out: voltage [Volts]
        '''
        logging.debug(__name__ + ': Getting measured voltage from instrument')
        response = self._visainstrument.query('MEAS:VOLT?')
        return float(response)

    def do_set_voltage(self,v):
        '''
        Get voltage for a specified channel
            in: ch - channel number
                v - voltage [Volts]
            out: none
        '''
        logging.debug('Sending voltage to instrument')
        self._visainstrument.write('VOLT {0:.3f}'.format(v))
        return

    def do_get_current(self):
        '''
        Get current for a specified 
            in: 
            out: current [A]
        '''
        logging.debug(__name__ + ': Getting current from instrument')
        response = self._visainstrument.query('APPL?').strip('"')
        voltage = float(response.split(',')[1])
        return voltage

    def do_set_current(self, I):
        '''
        Set current for a specified channel
            in: ch - channel number
            out: current [A]
        '''
        logging.debug(__name__ + ': Setting current to %.3f' % I)
        self._visainstrument.write('CURR {0:.3f}'.format(I))

        return

    def do_get_current_reading(self):
        '''
        Get current reading for a specified 
            in: 
            out: 
        '''
        logging.debug(__name__ + ': Getting current from instrument')
        response = self._visainstrument.query('MEAS:CURR?')
        return float(response)
        
    def do_get_active(self):
        '''
        Get whether the output is on or off
            in:
            out: active_status [Boolean]
        '''
        logging.debug('Getting active status from instrument')
        response = self._visainstrument.query('OUTPUT:STATE?')
        if response == '1':
            return True
        elif response =='0':
            return False
        else:
            logging.warning('{0}: responded with unexpected answer: {1}'.format(
                __name__, response))

    def do_set_active(self,a):
        '''
        Get voltage for a specified channel
            in:
                a - active_status [Boolean]
            out: none
        '''
        logging.debug('Sending active status to instrument')
        if a == False :
            self._visainstrument.write('OUTP OFF')
            return True
        elif a == True :
            self._visainstrument.write('OUTP ON')
            return True

    def ramp_current(self,I):
        '''
        Ramp to set current
        '''
        logging.debug(__name__+ 'Ramping current to %.3f' % I)
        rate = 0.01 #A/20ms
        I_init = self.do_get_current_reading()
        if I_init < I:
            I_set = I_init+rate
            while I-I_set > 0.1:  
                self._visainstrument.write('CURR %.3f' % (I_set))
                qt.msleep(0.02)
                I_set += rate
            self._visainstrument.write('CURR %.3f' % I)
            qt.msleep(0.02)
            return True

        else:
            I_set = I_init-rate
            while I_set-I > 0.1:  
                self._visainstrument.write('CURR %.3f' % (I_set))
                qt.msleep(0.02)
                I_set -= rate
            self._visainstrument.write('CURR %.3f' % I)
            qt.msleep(0.02)
            return True

    def zero(self):
        '''
        Ramp voltage and current to zero and turn off output
        '''
        self.ramp_current(0.0)
        self.do_set_voltage(0.0)
        self.do_set_active(False)
        return True

    def set_remote(self):
        self._visainstrument.write('SYST:REM')
