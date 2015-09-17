# This Python file uses the following encoding: utf-8
# Keithley_2400.py driver for Keithley 2400 Source Meter
# Arjan Verduijn <a.verduijn@unsw.edu.au>
# Gabriele de Boo <g.deboo@student.unsw.edu.au>
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
from numpy import zeros, fromstring

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
        
        self.add_parameter('source_voltage',
            type=types.FloatType,
            tags=['sweep'],
            maxstep=0.020, stepdelay=100,
            flags=Instrument.FLAG_GETSET, minval=-210, maxval=210, units='V')
        self.add_parameter('source_voltage_range',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=-210, maxval=210, units='V')
        self.add_parameter('source_current',
            type=types.FloatType,
            tags=['sweep'],
            maxstep=1e-9, stepdelay=100,
            flags=Instrument.FLAG_GETSET, minval=-1, maxval=1, units='A')
        self.add_parameter('current_compliance',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=0, maxval=1.05, units='A')
        self.add_parameter('voltage_compliance',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=0, maxval=210, units='V')
        self.add_parameter('output_state',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('terminals',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=(
                'FRONT',
                'REAR'))
        self.add_parameter('4_wire_mode',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('source_function',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=(
                'voltage',
                'current',
                'memory'))
        self.add_parameter('measurement_function',
            type=types.StringType,
            flags=Instrument.FLAG_GET,
            option_list=(
                'voltage',
                'current',
                'resistance')
                )
        self.add_parameter('voltage_source_mode',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=(
                'fixed',
                'list',
                'sweep'))
        self.add_parameter('current_source_mode',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=(
                'fixed',
                'list',
                'sweep'))
        self.add_parameter('current_reading',
            type=types.FloatType,
            units='A',
            flags=Instrument.FLAG_GET)
        self.add_parameter('current_measurement_range',
            type=types.FloatType,
            units='A',
            flags=Instrument.FLAG_GET)			
        self.add_parameter('voltage_reading',
            type=types.FloatType,
            units='V',
            flags=Instrument.FLAG_GET) 
        self.add_parameter('voltage_measurement_range',
            type=types.FloatType,
            units='V',
            flags=Instrument.FLAG_GETSET,
            minval=-210, maxval=210)			

        self.add_parameter('display_top',
            type=types.StringType,
            flags=Instrument.FLAG_GET)          
        self.add_parameter('display_bottom',
            type=types.StringType,
            flags=Instrument.FLAG_GET)

        self.add_parameter('concurrent_measurements',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('concurrent_measurement_functions',
            type=types.StringType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('digits',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=4, maxval=7)
        self.add_parameter('integration_rate',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0.01, maxval=10,
            units='power line cycles')
        self.add_parameter('auto_zero',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('line_frequency',
            type=types.FloatType,
            flags=Instrument.FLAG_GET)

        # trigger parameters
        self.add_parameter('trigger_source',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list = ('immediate',
                            'tlink') 
            )
        self.add_parameter('arm_source',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list = ('immediate',
                            'bus',
                            'tlink',
                            'timer',
                            'manual',
                            'bus',
                            'nstest',
                            'pstest',
                            'bstest'),
            )
        self.add_parameter('arm_count',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=2500)

        # buffer
        self.add_parameter('buffer_size',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=2500)
			
        self.add_function('beep')

        if reset:
            if (self.get_output_state()):
                print 'Performing instrument reset, ramping voltage to zero...'
                self.get_source_voltage()
                self.set_source_voltage(0)
                self.reset()
            else:
                self.reset()
        
        self.get_all()

# --------------------------------------
#           functions
# --------------------------------------
    def get_all(self):
        self.get_source_voltage()
        self.get_source_voltage_range()
        self.get_current_compliance()
        self.get_voltage_compliance()        
        self.get_output_state()
        self.get_terminals()
        self.get_source_function()
        self.get_voltage_source_mode()
        self.get_current_source_mode()
        self.get_display_top()		
        self.get_display_bottom()	
        self.get_concurrent_measurements()	
        self.get_concurrent_measurement_functions()		
        self.get_voltage_measurement_range()
        self.get_current_measurement_range()
        self.get_4_wire_mode()
        self.get_digits()
        self.get_integration_rate()
        self.get_auto_zero()
        self.get_line_frequency()
        self.get_trigger_source()
        self.get_arm_source()
        self.get_arm_count()
    
    def reset(self):
        '''
        Resets instrument to default setting for GPIB operation, i.e. manual 
        trigger mode

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting instrument to default GPIB operation')
        self._visainstrument.write('*RST')

    def do_get_terminals(self):
        '''
        Get terminals that are used.

        Input:
            None
        Output:
            'FRONT'
            'REAR'
        '''
        logging.debug('Getting the terminal used by %s.' %self.get_name())
        reply = self._visainstrument.ask(':ROUT:TERM?')
        if reply == 'FRON': # The source meter responds with 'FRON'
            logging.info('The terminal used by %s is FRONT.' %(self.get_name())) 
            return 'FRONT'
        elif reply == 'REAR':
            logging.info('The terminal used by %s is %s.' %(self.get_name(),reply)) 
            return reply
        else:
            logging.warning('Received unexpected response from %s.' %self.get_name())
            raise Warning('Instrument %s responded with an unexpected response: %s.' %(self.get_name(),reply))

    def do_set_terminals(self, terminal):
        '''
        Set terminals to be used
        
        Input:
            'FRONT'
            'REAR'
        Output:
            None
        '''
        logging.debug('Setting the terminal used by %s.' %self.get_name())
        logging.info('Setting the terminal used by %s to %s.' %(self.get_name(), terminal))
        self._visainstrument.write(':ROUT:TERM %s' %terminal)

    def do_get_source_function(self):
        '''
        Get source function

        Input:
            None
        Output:
            'voltage'
            'current'
            'memory'
        '''
        logging.debug('Getting source function mode.')
        reply = self._visainstrument.ask(':SOUR:FUNC:MODE?')
        if reply == 'VOLT':
            logging.info('Source function of %s is voltage.' % self.get_name())
            return 'voltage'
        elif reply == 'CURR':
            logging.info('Source function of %s is current.' % self.get_name())
            return 'current'
        elif reply == 'MEM':
            logging.info('Source function of %s is memory.' % self.get_name())
            return 'memory'
        else:
            logging.warning('get_source_function: Received unexpected response from %s.' %self.get_name())
            raise Warning('Instrument %s responded with an unexpected response: %s.' %(self.get_name(),reply))

    def do_set_source_function(self, function):
        '''
        Set source function

        Input:
            'voltage'
            'current'
            'memory'
        Output:
            None
        '''
        logging.debug('Setting source function mode to %s.' %function)
        self._visainstrument.write(':SOUR:FUNC:MODE %s' %function)
        
    def do_get_measure_function(self):
        '''
        Get measurement function.

        Input:
            None
        Output:
            'voltage'
            'current'
            'resistance'
        '''
        logging.debug('Getting measurement function.')
        reply = self._visainstrument.ask(':SENS:FUNC:ON?')
        if 'VOLT' in reply:
            logging.info('Measurement function of %s is voltage.' % self.get_name())
            return 'voltage'
        
#            logging.info('Source function of %s is current.' % self.get_name())
#            return 'current'
#        elif reply == 'MEM':
#            logging.info('Source function of %s is memory.' % self.get_name())
#            return 'memory'
#        else:
#            logging.warning('get_source_function: Received unexpected response from %s.' %self.get_name())
#            raise Warning('Instrument %s responded with an unexpected response: %s.' %(self.get_name(),reply))
    
    def do_get_voltage_source_mode(self):
        '''
        Get voltage sourcing mode

        Input:
            None
        Output:
            'fixed'
            'list'
            'sweep'
        '''
        logging.debug('Getting voltage sourcing mode.')
        reply = self._visainstrument.ask('SOUR:VOLT:MODE?')
        if reply == 'FIX':
            logging.info('Voltage sourcing mode of %s is fixed.' % self.get_name())
            return 'fixed'
        elif reply == 'LIST':
            logging.info('Voltage sourcing mode of %s is list.' % self.get_name())
            return 'list'
        elif reply == 'SWE':
            logging.info('Voltage sourcing mode of %s is sweep.' % self.get_name())
            return 'sweep'
        else:
            logging.warning('get_source_function: Received unexpected response from %s.' %self.get_name())
            raise Warning('Instrument %s responded with an unexpected response: %s.' %(self.get_name(),reply))

    def do_set_voltage_source_mode(self, mode):
        '''
        Set voltage sourcing mode

        Input:
            'fixed'
            'list'
            'sweep'
        Output:
            None
        '''
        logging.debug('Setting voltage sourcing mdoe to %s.' %mode)
        self._visainstrument.write(':SOUR:VOLT:MODE %s' %mode)

    def do_get_current_source_mode(self):
        '''
        Get current sourcing mode

        Input:
            None
        Output:
            'fixed'
            'list'
            'sweep'
        '''
        logging.debug('Getting current sourcing mode.')
        reply = self._visainstrument.ask('SOUR:CURR:MODE?')
        if reply == 'FIX':
            logging.info('Current sourcing mode of %s is fixed.' % self.get_name())
            return 'fixed'
        elif reply == 'LIST':
            logging.info('Current sourcing mode of %s is list.' % self.get_name())
            return 'list'
        elif reply == 'SWE':
            logging.info('Current sourcing mode of %s is sweep.' % self.get_name())
            return 'sweep'
        else:
            logging.warning('get_source_function: Received unexpected response from %s.' %self.get_name())
            raise Warning('Instrument %s responded with an unexpected response: %s.' %(self.get_name(),reply))

    def do_set_current_source_mode(self, mode):
        '''
        Set current sourcing mode

        Input:
            'fixed'
            'list'
            'sweep'
        Output:
            None
        '''
        logging.debug('Setting current sourcing mdoe to %s.' %mode)
        self._visainstrument.write(':SOUR:CURR:MODE %s' %mode)

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

    def enable_measure_function(self, function):
        '''
        Enables measure function

        Input:
            1: voltage function
            2: current function
        Output:
            None
        '''
        flib = {
            1: '"VOLT"',
            2: '"CURR"'}
        logging.debug('Set measure function to' + flib[function])
        self._visainstrument.write(':SENS:FUNC ' + flib[function])
        self.get_concurrent_measurement_functions()
		
    def disable_measure_function(self, function):
        '''
        Disables measure function

        Input:
            1: voltage function
            2: current function
        Output:
            None
        '''
        flib = {
            1: '"VOLT"',
            2: '"CURR"'}
        logging.debug('Disable measure function of' + flib[function])
        self._visainstrument.write(':SENS:FUNC:OFF ' + flib[function])
        self.get_concurrent_measurement_functions()

    def do_set_current_compliance(self, compliance):
        '''
        Set current compliance in amps

        Input:
            compliance : compliance in amps
        Output:
            None
        '''
        logging.debug('Set current compliance to ' + str(compliance))
        self._visainstrument.write(':SENS:CURR:PROT:LEV '+ str(compliance))

    def do_get_current_compliance(self):
        '''
        Get current compliance in amps
        '''
        logging.debug('Get current compliance.')
        return self._visainstrument.ask(':SENS:CURR:PROT:LEV?')

    def do_set_voltage_compliance(self, compliance):
        '''
        Set voltage compliance in volts

        Input:
            compliance : compliance in volts
        Output:
            None
        '''
        logging.debug('Set voltage compliance to ' + str(compliance))
        self._visainstrument.write(':SENS:VOLT:PROT:LEV ' + str(compliance))

    def do_get_voltage_compliance(self):
        '''
        Get voltage compliance in volts
        '''
        logging.debug('Get voltage compliance.')
        return self._visainstrument.ask(':SENS:VOLT:PROT:LEV?')

    def do_get_source_voltage(self):
        '''
        Get the voltage for the voltage source mode.
        '''
        logging.debug('Get source voltage.')
        return float(self._visainstrument.ask(':SOUR:VOLT:LEV:AMPL?'))

    def do_set_source_voltage(self, V):
        '''
        Set the voltage for the voltage source mode.
        Input:
            Voltage in V
        Output:
            None
        '''
        logging.debug("Set source voltage of %s to %.3e V." %(self.get_name(), V))
        self._visainstrument.write(':SOUR:VOLT:LEV %e' % V)
        self._visainstrument.read() # to update the display
        
    def do_get_source_current(self):
        '''
        Get the current for the voltage source mode.
        '''
        logging.debug('Get source current.')
        return float(self._visainstrument.ask(':SOUR:CURR:LEV:AMPL?'))  

    def do_set_source_current(self, I):
        '''
        Set the current for the current source mode.
        Input:
            Current in A
        Output:
            None
        '''
        logging.debug("Set source current of %s to %.3e A." %(self.get_name(), I))
        self._visainstrument.write(':SOUR:CURR:LEV %e' % I)     
        self._visainstrument.read() # to update the display

    def do_get_source_voltage_range(self):
        '''
        Get the voltage range for the voltage source mode.
        '''
        logging.debug('Getting the source voltage range of %s.' % self.get_name())
        return self._visainstrument.ask(':SOUR:VOLT:RANG?')

    def do_set_source_voltage_range(self, voltage_range):
        '''
        Set the voltage range for the voltage source mode.
        '''
        logging.debug('Setting the source voltage range of %s to %f.' % (self.get_name(), voltage_range))
        if abs(self.get_source_voltage()) > abs(voltage_range):
            logging.warning('Can not change the voltage range because the source voltage is larger than the voltage range.')
            raise Warning('Source voltage is larger than the given voltage range. Change the source voltage first.')
        self._visainstrument.write(':SOUR:VOLT:RANG %f' %voltage_range)
        self.get_source_voltage_range() # Ask for the range that the source meter chose.
        
    def do_get_output_state(self):
        '''
        Get output status

        Instrument responds with 1 or 0
        Function returns True or False
        '''
        status = self._visainstrument.ask('OUTP:STAT?')
        logging.debug('Get output status: ' + status)
        return bool(int(status))

    def do_set_output_state(self, state):
        '''
        Set output status

        Input:
            On: True
            Off: False
        Output:
            None
        '''
        logging.info('Turn output ' + str(state))
        self._visainstrument.write(':OUTP ' + str(int(state)))

    def get_value(self, value):
        '''
        Measure one or more of the following from the  from buffer
        
        Input:
            None

        Output:
            voltage or current in volt or amps
        '''
        readmode = {
            1 : 'voltage',
            2 : 'current',
            3 : 'resistance',
            4 : 'timestamp',
            5 : 'statusword'}
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

    def do_get_current_reading(self):
        '''
        Get the latest current reading.
        '''
        logging.debug('Getting the current reading of %s.' % self.get_name())
        self._visainstrument.write(':SENS:FUNC "CURR"')
        self._visainstrument.write(':FORM:ELEM CURR')
        if self.get_output_state():
            return self._visainstrument.ask(':READ?')
        else:
            logging.warning('Trying to read current of %s while the output is off.' % self.get_name())
#            raise Warning('Trying to read current of %s while its output is off.' % self.get_name()) 
            return False
			
    def do_get_current_measurement_range(self):
        '''
        Get the current measurement range from the sense subsystem.
        '''
        logging.debug('Getting the current measurement range of %s.' % self.get_name())
        return self._visainstrument.ask(':SENS:CURR:RANG:UPP?')				
            
    def do_get_voltage_reading(self):
        '''
        Get the latest current reading.
        '''
        logging.debug('Getting the current reading of %s.' % self.get_name())
#        self._visainstrument.write(':SENS:FUNC "VOLT"')
        self.enable_measure_function(1)
        self._visainstrument.write(':FORM:ELEM VOLT')
        if self.get_output_state():
            return self._visainstrument.ask(':READ?')
        else:
            logging.warning('Trying to read voltage of %s while the output is off.' % self.get_name())
#            raise Warning('Trying to read current of %s while its output is off.' % self.get_name()) 
            return False            

    def do_get_voltage_measurement_range(self):
        '''
        Get the voltage measurement range from the sense subsystem.
        '''
        logging.debug('Getting the voltage measurement range of %s.' % self.get_name())
        return self._visainstrument.ask(':SENS:VOLT:RANG:UPP?')	

    def do_set_voltage_measurement_range(self, value):
        '''
        Set the voltage measurement by providing the expected reading in V. The
        instrument will adapt the range to accomodate this reading.
        One of the following ranges will be selected: 0.2, 2, 20, 210
        '''
        logging.debug('Setting the voltage measurment range with expected \
                        reading: %.1f' % value)
        self._visainstrument.write(':SENS:VOLT:RANG:UPP %.1f' % value)

    def do_get_display_top(self):
        '''
        Get the message displayed on the top of the display.
        '''
        return self._visainstrument.ask(':DISP:WINDow1:DATA?').replace('\x10','μ')        

    def do_get_display_bottom(self):
        '''
        Get the message displayed on the bottom of the display.
        '''
        return self._visainstrument.ask(':DISP:WINDow2:DATA?').replace('\x10','μ')    	

    def do_get_concurrent_measurements(self):
        answer = self._visainstrument.ask(':SENS:FUNC:CONC?')
        return bool(int(answer))
        
    def do_set_concurrent_measurements(self, enabled):
        '''Enable or disable measuring more than one function simultaneously. 
           
           When disabled, volts function is enabled.
        '''
        if enabled:
            self._visainstrument.write(':SENS:FUNC:CONC ON')
        else:
            self._visainstrument.write(':SENS:FUNC:CONC OFF')
		
    def do_get_concurrent_measurement_functions(self):
        return self._visainstrument.ask(':SENS:FUNC:ON?')

    def do_get_4_wire_mode(self):
        '''
        Get whether the instrument is in 4-wire mode.
        '''
        return bool(int(self._visainstrument.ask(':SYST:RSEN?')))

    def do_set_4_wire_mode(self, mode):
        '''
        Set whether the instrument is in 4-wire mode.
        '''
        if mode:
            self._visainstrument.write(':SYST:RSEN 1')
        else:
            self._visainstrument.write(':SYST:RSEN 0')

    def do_get_digits(self):
        '''
        Get the number of digits that the display is showing.
        '''
        logging.debug(__name__ + ' : Get the number of digits on the display')
        return int(self._visainstrument.ask('DISP:DIG?'))

    def do_set_digits(self, dig):
        '''
        Set the number of digits. Minimum value is 4, maximum = 7.
        '''
        logging.debug(__name__ + ' : Set the number of digits to %i.' % dig)
        self._visainstrument.write('DISP:DIG %i' % dig)

    def do_get_integration_rate(self):
        '''
        Get the integration rate of the instrument. This is defined in number 
        of power cycles with a minimum of 0.01 and a maximum of 10. 

        When auto-zero is enabled the A/D conversion takes three times as
        long. 

        On the instrument the following settings are available:
        FAST:        0.01 PLC, display resolution changed to 3.5 digits
        MED:         0.10 PLC, display resolution changed to 4.5 digits
        NORMAL:      1.00 PLC, display resolution changed to 5.5 digits
        HI ACCURACY: 10.00 PLC, display resolution changed to 6.5 digits
        OTHER:       any PLC value, display resolution is not changed
        '''
        logging.debug(__name__ + ' : Get the integration rate.')
        return float(self._visainstrument.ask(':SENS:VOLT:NPLC?') )

    def do_set_integration_rate(self, rate):
        '''
        Set the integration rate of the instrument. This is defined in number 
        of power cycles with a minimum of 0.01 and a maximum of 10. 

        When auto-zero is enabled the A/D conversion takes three times as
        long. 

        On the instrument the following settings are available:
        FAST:        0.01 PLC, display resolution changed to 3.5 digits
        MED:         0.10 PLC, display resolution changed to 4.5 digits
        NORMAL:      1.00 PLC, display resolution changed to 5.5 digits
        HI ACCURACY: 10.00 PLC, display resolution changed to 6.5 digits
        OTHER:       any PLC value, display resolution is not changed
        '''
        logging.debug(__name__ + ' : Set the integration rate to %.2f' % rate)
        self._visainstrument.write(':SENS:VOLT:NPLC %.2f' % rate)

    def do_get_auto_zero(self):
        '''
        Get whether the auto zero is enabled or not. With auto zero disabled 
        the analog to digital conversion is faster at the expense of long term 
        drift, see page A-7 of the manual.
        '''
        logging.debug(__name__ + ' : Get whether the auto zero is on or off.')
        answer = self._visainstrument.ask(':SYST:AZER:STAT?')
        if answer == '1':
            return True
        elif answer == '0':
            return False
        else:
            raise ValueError('Auto Zero state not specified: %s' % answer)

    def do_set_auto_zero(self, azero):
        '''
        Set whether the auto zero is enabled or not. With auto zero disabled 
        the analog to digital conversion is faster at the expense of long term 
        drift, see page A-7 of the manual.
        '''
        logging.debug(__name__ + ' : Set the auto zero to %s .' % azero)
        if azero:
            self._visainstrument.write(':SYST:AZER:STAT 1')
        else:
            self._visainstrument.write(':SYST:AZER:STAT 0')
    
    def do_get_line_frequency(self):
        '''
        Get the line frequency.
        '''
        logging.debug(__name__ + ' : Get the line frequency.')
        return float(self._visainstrument.ask(':SYST:LFR?'))  

    def beep(self, freq=500, length=1):
        '''
        Make a beep with specified frequency and length.
        '''
        logging.debug('Making a beep with %s.' %self.get_name())
        self._visainstrument.write('SYST:BEEP %f, %f' % (freq, length))

    def get_trace_buffer_contents(self):
        '''
        Get the contents of the buffer.

        Returns a numpy array
        '''
        n_readings = int(self._visainstrument.ask(':TRAC:POIN:ACT?'))
        logging.info('Number of stored readings in buffer: %i' % 
                        n_readings)
        trace = zeros(int(n_readings))
        if n_readings == 0:
            return trace
        else:
            self._visainstrument.timeout = 4
            trace_data = self._visainstrument.ask(':TRAC:DATA?')
        self._visainstrument.timeout = 1
        trace = fromstring(trace_data, sep=',')
        return trace

    def clear_trace_buffer(self):
        '''
        Clear the contents of the trace buffer.
        '''
        self._visainstrument.write(':TRAC:CLE')

    def trigger(self):
        '''
        Send a trigger command to the sourcemeter
        '''
        self._visainstrument.write('*TRG')

    def do_get_trigger_source(self):
        '''
        Get the source of the trigger.
        '''
        trigger_source = self._visainstrument.ask(':TRIG:SOUR?')
        if trigger_source == 'IMM':
            return 'immediate'
        elif trigger_source == 'TLIN':
            return 'tlink'
        elif trigger_source == 'BUS':
            return 'bus'
        else:
            logging.info('Trigger source query replied with: %s ' 
                            % trigger_source)

    def do_set_trigger_source(self, trigger_source):
        '''
        Set the source of the trigger.
        '''
        logging.info('Setting trigger source to %s'
            % trigger_source)
        if trigger_source == 'IMMEDIATE':
            self._visainstrument.write(':TRIG:SOUR IMM')
        elif trigger_source == 'TLINK':
            self._visainstrument.write(':TRIG:SOUR TLIN')

    def do_get_arm_source(self):
        '''
        Get the source of the arm subroutine
        '''
        arm_source = self._visainstrument.ask(':ARM:SOUR?')
        if arm_source == 'IMM':
            return 'immediate'
        elif arm_source == 'TLIN':
            return 'tlink'
        elif arm_source == 'TIM':
            return 'timer'
        elif arm_source == 'MAN':
            return 'manual'
        elif arm_source == 'BUS':
            return 'bus'
        elif arm_source == 'NST':
            return 'nstest'
        elif arm_source == 'PST':
            return 'pstest'
        elif arm_source == 'BST':
            return 'bstest'
        else:
            logging.error('Arm source query replied with: %s ' 
                            % arm_source)

    def do_set_arm_source(self, arm_source):
        '''
        '''
        if arm_source == 'IMMEDIATE':
            self._visainstrument.write(':ARM:SOUR IMM')
        elif arm_source == 'TLINK':
            self._visainstrument.write(':ARM:SOUR TLIN')
        elif arm_source == 'TIMER':
            self._visainstrument.write(':ARM:SOUR TIM')
        elif arm_source == 'MANUAL':
            self._visainstrument.write(':ARM:SOUR MAN')
        elif arm_source == 'BUS':
            self._visainstrument.write(':ARM:SOUR BUS')
        elif arm_source == 'NSTEST':
            self._visainstrument.write(':ARM:SOUR NST')
        elif arm_source == 'PSTEST':
            self._visainstrument.write(':ARM:SOUR PST')
        elif arm_source == 'BSTEST':
            self._visainstrument.write(':ARM:SOUR BST')

    def do_get_arm_count(self):
        '''
        '''
        arm_count = int(self._visainstrument.ask(':ARM:COUN?'))
        return arm_count

    def do_set_arm_count(self, arm_count):
        '''
        '''
        self._visainstrument.write(':ARM:COUN %i' % arm_count)

    def initiate(self):
        '''
        Send the initiate command
        '''
        self._visainstrument.write(':INIT')

    def abort(self):
        '''
        Reset the trigger system. Goes to idle state.
        '''
        self._visainstrument.write(':ABOR')

    def read_error_queue(self):
        '''
        '''
        return self._visainstrument.ask(':SYST:ERR?')

#    def store_buffer_readings(self, count):
#        '''
#        '''
#        self._visainstrument.write('TRAC:POIN %i' % count)

    def enable_buffer(self):
        '''
        '''
        self._visainstrument.write('TRAC:FEED:CONT NEXT')

    def disable_buffer(self):
        '''
        '''
        self._visainstrument.write('TRAC:FEED:CONT NEV')

    def do_get_buffer_size(self):
        '''
        '''
        buffer_size = int(self._visainstrument.ask('TRAC:POIN?'))
        return buffer_size

    def do_set_buffer_size(self, buffer_size):
        '''
        '''
        self._visainstrument.write('TRAC:POIN %i' % buffer_size)

    def set_format_elements(self, elements):
        '''
        '''
        element_string = ''
        for element in elements:
            element_string += element
        print(element_string)
        self._visainstrument.write(':FORM:ELEM %s' % element_string) 

    def clear_communication(self):
        '''
        '''
        self._visainstrument.clear()
