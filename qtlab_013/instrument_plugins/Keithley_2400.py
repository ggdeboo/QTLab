# Keithley_2400.py driver for Keithley 2400 Source Meter
# Arjan Verduijn <a.verduijn@unsw.edu.au>
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
import qt
from time import sleep

class Keithley_2400(Instrument):
    '''
    This is the driver for the Keithley 2400 Source Meter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2400',
        address='<GBIP address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=True):
        '''
        Initializes the Keithley_2400, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Keithley_2400')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants and set up visa instrument
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.clear()
        self._visainstrument.delay = 20e-3
        self._visainstrument.timeout = 1
        
        self._voltage_step = 50e-3
        self._voltage_step_time = 100e-3
        
        
        if reset:
            if (self.get_output() == 1):
                print 'Performing instrument reset, ramping voltage to zero...'
                self.set_voltage(0)
                self.reset()
            elif (self.get_output() == 2):
                self.reset()
            else:
                print 'Warning: Instrument reset could not be performed!'

# --------------------------------------
#           functions
# --------------------------------------

    def reset(self):
        '''
        Resets instrument to default setting for GPIB operation, i.e. manual trigger mode

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting instrument to default GPIB operation')
        self._visainstrument.write('*RST')

    def set_voltage_ramp(self, voltage_step, voltage_step_time):
        '''
        Set voltage ramp settings, default values set in "__init__"

        Input:
            voltage step and voltage step time
        Output:
            none
        '''
        self._voltage_step = voltage_step
        self._voltage_step_time = voltage_step_time
        
    def set_voltage(self, voltage):
        '''
        Ramps voltage to desired value

        Input:
            Ramp voltage in Volts to a specified value according to ramp settings in __init__

        Output:
            Actual voltage after ramp is performed
        '''
        start_voltage = self.get_value(1)
        
        step = self._voltage_step * cmp(voltage, start_voltage)
        step_time = self._voltage_step_time
        voltage_ramp = []
        if not(step == 0):
            Nramp = int(abs((start_voltage - voltage) / step))
            voltage_ramp = [x * step + start_voltage for x in range(Nramp + 1)]
            voltage_ramp.append(voltage)
        else:
            voltage_ramp = [start_voltage, voltage]
        
        self.set_source_mode(1, 1)
        for v in voltage_ramp:
            self.set_source_amplitude(1, v)
            qt.msleep(step_time)
            self.get_value(2)
        return self.get_value(1)

    def set_terminals(self, terminal):
        '''
        Set terminals to be used
        
        Input:
            1: Use front terminals
            2: Rear terminals
        Output:
            None
        '''
        termlib = {
            1: 'FRONT',
            2: 'REAR'}
        logging.debug('Setting instrument to use ' + termlib[terminal] + ' terminals')
        self._visainstrument.write(':ROUT:TERM ' + termlib[terminal])

    def set_source_function(self, function):
        '''
        Set sourcing function

        Input:
            1: voltage mode
            2: current mode
        Output:
            None
        '''
        flib = {
            1: 'VOLT',
            2: 'CURR'}
        logging.debug('Set sourcing function to' + flib[function])
        self._visainstrument.write(':SOUR:FUNC ' + flib[function])
    
    def set_source_mode(self, function, mode):
        '''
        Set sourcing mode

        Input:
            1: fixed
            2: list
            3: sweep
        Output:
            None
        '''
        flib = {
            1: 'VOLT',
            2: 'CURR'}
        source = {
            1: 'FIX',
            2: 'LIST',
            3: 'SWE'}
        logging.debug('Set ' + flib[function] + ' sourcing to' + source[mode])
        self._visainstrument.write(':SOUR:' + flib[function] + ':MODE ' + source[mode])

    def set_measure_range(self, function, range):
        '''
        Set measurement range in volts or amps

        Input:
            1     : voltage mode
            2     : current mode
            range : range in volts or amps
        Output:
            None
        '''
        flib = {
            1: 'VOLT',
            2: 'CURR'}
        logging.debug('Select measurement range: ' + str(range) + flib[function])
        self._visainstrument.write(':SOUR:' + flib[function] +':RANG ' + str(range))

    def set_source_amplitude(self, function, amplitude):
        '''
        Set source amplitude in volts or amps
        
        Input:
            1           : voltage mode
            2           : current mode
            amplitude   : range in volts or amps
        Output:
            None
        '''
        flib = {
            1: 'VOLT',
            2: 'CURR'}
        logging.debug('Set source amplitude to ' + str(amplitude))
        self._visainstrument.write(':SOUR:' + flib[function] + ':LEV ' + str(amplitude))

    def set_measure_function(self, function):
        '''
        Set measure function

        Input:
            1: voltage function
            2: current function
        Output:
            None
        '''
        flib = {
            1: 'VOLT',
            2: 'CURR'}
        logging.debug('Set measure function to' + flib[function])
        self._visainstrument.write(':SENS:FUNC ' + flib[function])

    def set_compliance(self, function, compliance):
        '''
        Set compliance value in volts or amps

        Input:
            1          : voltage compliance
            2          : current compliance
            compliance : compliance in volts or amps
        Output:
            None
        '''
        flib = {
            1: 'VOLT',
            2: 'CURR'}
        logging.debug('Set compliance to ' + str(compliance) + ' ' + flib[function])
        self._visainstrument.write(':SENS:' + flib[function] + ':PROT ' + str(compliance))

    def set_output(self, setting):
        '''
        Turn ouput on or off

        Input:
            1: 'ON'
            2: 'OFF'
        Output:
            None
        '''
        mode = {
            1: 'ON',
            2: 'OFF'}
        logging.debug('Turn output ' + mode[setting])
        self._visainstrument.write(':OUTP ' + mode[setting])

    def get_output(self):
        '''
        Get ouput status

        Input:
            None
        Output:
            1: 'ON'
            2: 'OFF'
        '''
        mode = {
            1: 'ON',
            2: 'OFF'}
        status = 2 - int(float(self._visainstrument.ask('OUTP:STAT?')))
        logging.debug('Get output status:' + mode[status])
        return status
        
    def get_value(self, value):
        '''
        Measure one or more of the following from the  from buffer
        
        Input:
            None

        Output:
            voltage or current in volt or amps
        '''
        readmode = {
            1 :	'voltage',
            2 :	'current',
            3 :	'resistance',
            4 :	'timestamp',
            5 :	'statusword'}
        data = self._visainstrument.ask(':READ?').split(',')
        logging.debug(__name__ + ' : Read output values from instrument')
        if type(value) == int:
            if data[value-1][-4:] == 'E+37':
                print 'warning: cannot read ' + readmode[value] + ', parameter not available...'
                return 'NA'
            elif value <= 3:
                return float(data[value-1])
            else:
                return int(float(data[value-1]))
        else:
            result = []
            for v in value:
                if data[v-1][-4:] == 'E+37':
                    result.append('NA')
                    print 'warning: cannot read ' + readmode[v] + ', parameter not available...'
                elif v <= 3:
                    result.append(float(data[v-1]))
                else:
                    result.append(int(float(data[v-1])))
            return result
