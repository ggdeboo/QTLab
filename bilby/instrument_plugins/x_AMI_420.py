# AMI_420.py class, to perform the communication between the Wrapper and the device
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
from time import time, sleep
import visa
import types
import logging

class x_AMI_420(Instrument):
    '''
    This is the python driver for the American Magnetics 420 Power Supply Programmer

    Usage:
    Initialize with
    <name> = instruments.create('name', 'AMI_420', address='GPIB::##')


    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Oxford Instruments IPS 120 Magnet Power Supply. Maximum

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB instrument address

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        #Add parameters
        self.add_parameter('state', type=types.IntType,
            flags=Instrument.FLAG_GET,
            format_map = {
            1 : "RAMPing to set point",
            2 : "HOLDing at setpoint",
            3 : "PAUSEd",
            4 : "Manually ramping UP",
            5 : "Manually ramping DOWN",
            6 : "ZEROing current",
            7 : "QUench detected",
            8 : "Heating PSwitch",
            9 : "At ZERO currrent"})
        self.add_parameter('field_setpoint', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=1.2, units='T', tags=['sweep'])
        self.add_parameter('field_rate', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=0.1, units='T/s')
        self.add_parameter('current_setpoint', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=50, units='A', tags=['sweep'])
        self.add_parameter('current_rate', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=0.5, units='A/s')
        self.add_parameter('coil_constant', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='T/A')
        self.add_parameter('magnet_current', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='A')
        self.add_parameter('magnet_field', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='T')
        self.add_parameter('magnet_voltage', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='V')
        self.add_parameter('supply_voltage', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='V')
        self.add_parameter('voltage_limit', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='V')
        self.add_parameter('current_limit', type=types.FloatType,
            flags=Instrument.FLAG_GET, units='A')


        # Add functions
        #self.add_function('get_all')
        self.add_function('reset')
        self.add_function('zero')
        self.add_function('ramp')
        self.add_function('pause')
        
        if reset:
            self.reset()
        else:
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
        self.get_state()
        self.get_field_setpoint()
        self.get_current_setpoint()
        self.get_field_rate()
        self.get_current_rate()
        self.get_coil_constant()
        self.get_magnet_field()
        self.get_magnet_current()
        self.get_magnet_voltage()
        self.get_supply_voltage()
        self.get_voltage_limit()
        self.get_current_limit()
        
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

#do_functions
    def do_get_state(self):
        '''
        Fetches the state of the power supply

        Input:
            None

        Output:
            state (int): as below
            1 : "RAMPing to set point",
            2 : "HOLDing at setpoint",
            3 : "PAUSEd",
            4 : "Manually ramping UP",
            5 : "Manually ramping DOWN",
            6 : "ZEROing current",
            7 : "QUench detected",
            8 : "Heating PSwitch",
            9 : "At ZERO currrent"
        '''
        logging.debug('Getting state')
        return self._visainstrument.ask('STATE?')
    
    def do_set_field_setpoint(self, Bset):
        '''
        Sets the mag field setpoint

        Input:
            Bset (float): the target field in Tesla

        Output:
            None
        '''
        logging.debug('Setting field setpoint')
        self._visainstrument.write('CONF:FIELD:PROG %e T' % Bset)
        return 
    
    def do_set_current_setpoint(self, Iset):
        '''
        Sets the current setpoint

        Input:
            Iset (float): the target current in Amps

        Output:
            None
        '''
        logging.debug('Setting current setpoint')
        self._visainstrument.write('CONF:CURR:PROG %e' % Iset)
        return 
        
    def do_set_field_rate(self, Brate):
        '''
        Sets the mag field ramp rate

        Input:
            Brate (float): the target ramp rate in Tesla/sec

        Output:
            None
        '''
        logging.debug('Setting field ramp')
        self._visainstrument.write('CONF:RAMP:RATE:FIELD %e T/s' % Brate)
        return 
    
    def do_set_current_rate(self, Irate):
        '''
        Sets the current ramp rate

        Input:
            Irate (float): the target rate in Amps/Sec

        Output:
            None
        '''
        logging.debug('Setting current ramp')
        self._visainstrument.write('CONF:RAMP:RATE:CURR %e A/s' % Irate)
        return 

    def do_get_field_setpoint(self):
        '''
        Fetches the mag field setpoint

        Input:
            None

        Output:
            field (float): the set field in Tesla (or kGauss if set wrong)
        '''
        logging.debug('Getting field setpoint')
        return self._visainstrument.ask('FIELD:PROG?')
    
    def do_get_current_setpoint(self):
        '''
        Fetches the current setpoint

        Input:
            None

        Output:
            current (float): the set current in Amps
        '''
        logging.debug('Getting current setpoint')
        return self._visainstrument.ask('CURR:PROG?')
        
    def do_get_field_rate(self):
        '''
        Fetches the field ramp rate

        Input:
            None

        Output:
            rate (float): the field ramping rate in Tesla/sec
        '''
        logging.debug('Getting field rate')
        return self._visainstrument.ask('RAMP:RATE:FIELD?')
    
    def do_get_current_rate(self):
        '''
        Fetches the current ramp rate

        Input:
            None

        Output:
            rate (float): the current ramping rate in Amps/sec
        '''
        logging.debug('Getting current rate')
        return self._visainstrument.ask('RAMP:RATE:CURR?')

    def do_get_coil_constant(self):
        '''
        Fetches the configured coil constant

        Input:
            None

        Output:
            CC (float): the ratio of Tesla/Amps set in the instrument
        '''
        logging.debug('Getting coil const')
        return self._visainstrument.ask('COIL?')
    
    def do_get_magnet_field(self):
        '''
        Fetches the instantaneous magnet field

        Input:
            None

        Output:
            field (float): the magnet filed in Tesla (or kG)
        '''
        logging.debug('Getting magnet field')
        return self._visainstrument.ask('FIELD:MAG?')
    
    def do_get_magnet_current(self):
        '''
        Fetches the instantaneous magnet current

        Input:
            None

        Output:
            current (float): the magnet current in Amps
        '''
        logging.debug('Getting magnet current')
        return self._visainstrument.ask('CURR:MAG?')
    
    def do_get_magnet_voltage(self):
        '''
        Fetches the instantaneous magnet voltage

        Input:
            None

        Output:
            volt (float): the magnet voltage in Volts
        '''
        logging.debug('Getting magnet voltage')
        return self._visainstrument.ask('VOLT:MAG?')
    
    def do_get_supply_voltage(self):
        '''
        Fetches the instantaneous supply voltage

        Input:
            None

        Output:
            volt (float): the supply voltage in Volts
        '''
        logging.debug('Getting supply voltage')
        return self._visainstrument.ask('VOLT:SUPP?')
    
    def do_get_voltage_limit(self):
        '''
        Fetches the (hard) ramping voltage limit

        Input:
            None

        Output:
            v_lim (float): the ramping voltage limit in Volts
        '''
        logging.debug('Getting ramping voltage limit')
        return self._visainstrument.ask('VOLT:LIM?')
    
    def do_get_current_limit(self):
        '''
        Fetches the current (hard) limit

        Input:
            None

        Output:
            i_lim (float): the limit current in Amps
        '''
        logging.debug('Getting current limit')
        return self._visainstrument.ask('CURR:LIM?')

    def zero(self):
        '''
        Set the state to Zeroing - the current will be ramped to zero at the set rate

        Input:
            None

        Output:
            None
        '''
        logging.info('Zeroing magnet')
        self._visainstrument.write('ZERO')
        
    def ramp(self):
        '''
        Sets the state to Ramping - the current will sweep to the setpoint at the set rate

        Input:
            None

        Output:
            None
        '''
        logging.info('Ramping magnet')
        self._visainstrument.write('RAMP')
    
    def pause(self):
        '''
        Sets the state to Paused - ramping is supended, all magnet values are read

        Input:
            None

        Output:
            None
        '''
        logging.info('Pausing magnet')
        self._visainstrument.write('PAUSE')
        self.get_all()