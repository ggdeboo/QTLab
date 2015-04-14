# OxfordInstruments_ITC503.py class, to perform the communication between the Wrapper and the device
# Arjan Verudijn, 2011
# Gabriele de Boo, 2015 <ggdeboo@gmail.com>
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
import qt

class OxfordInstruments_ITC503(Instrument):
    '''
    This is the python driver for the Oxford Instruments ITC503 temperature
    controller

    Usage:
    Initialize with
    <name> = instruments.create('name', 'OxfordInstruments_ITC503', 
             address='<Instrument address>')
    '''
    
    def __init__(self, name, address):
        '''
        Initializes the Oxford Instruments ITC503 temperature controller.

        Input:
            name (string)    : name of the instrument
            address (string) : instrument GPIB address, form: 'GPIB::nn'

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.timeout = 1
        self._visainstrument.delay = 20e-3
        self._visainstrument.term_chars = visa.CR
        self._visainstrument.clear()

#        self._gasflow_low = 5
#        self._gasflow_high = 10
        
        #Add parameters
        self.add_parameter('temperature', type=types.FloatType,
            channels=(1, 2, 3), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GET)
        self.add_parameter('heater_voltage', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('proportional_term', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=999)
        self.add_parameter('integral_term', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=140)
        self.add_parameter('derivative_term', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=273)
        self.add_parameter('gas_flow', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0.0, maxval=99.9)
        self.add_parameter('heater_control', type=types.IntType,
            flags=Instrument.FLAG_SET, minval=1, maxval=3)
        self.add_parameter('maximum_heater_voltage', type=types.FloatType,
            flags=Instrument.FLAG_SET, minval=0, maxval=40)
        self.add_parameter('heater_manual', type=types.FloatType,
            flags=Instrument.FLAG_SET, minval=0, maxval=99.9)
        self.add_parameter('setpoint_temperature', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=99.9)
        self.add_parameter('remote_status', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked"})
        self.add_parameter('pid_control', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Heater manual, gas manual",
            1 : "Heater auto, gas manual",
            2 : "Heater manual, gas auto",
            3 : "Heater auto, gas auto"})
        self.add_parameter('front_panel_display', type=types.IntType,
            flags=Instrument.FLAG_SET,
            format_map = {
            0 : "Set temperature",
            1 : "Sensor 1 temperature",
            2 : "Sensor 2 temperature",
            3 : "Sensor 3 temperature",
            4 : "Temperature error (+ve when set > measured)",
            5 : "Heater o/p (as Volts, approx.)",
            6 : "Heater o/p (as % of current limit)",
            7 : "Gas flow o/p (arbitrary units)",
            8 : "Proportinal band",
            9 : "Integral action time",
            10 : "Derivative action time",
            11 : "Channel 1 freq/4",
            12 : "Channel 2 freq/4",
            13 : "Channel 3 freq/4"})        
        self.add_parameter('auto_pid_status', type=types.IntType,
            flags=Instrument.FLAG_GET,
            format_map = {
            0 : "Auto-PID disabled",
            1 : "Auto-PID enabled",})

        # Add functions
        self.add_function('get_all')
        #self.add_function('set_temperature')
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
        # Functions
        self.get_ch1_temperature()
        self.get_ch2_temperature()
        self.get_ch3_temperature()
        self.get_heater_voltage()
        self.get_proportional_term()
        self.get_integral_term()
        self.get_derivative_term()
        self.get_gas_flow()
        self.get_setpoint_temperature()
        self.get_remote_status()
        self.get_pid_control()
        self.get_auto_pid_status()

    def set_temperature(self, channel, temperature, margin=0.01, 
                        stabilization_time=120):
        '''
        Sets the temperature and waits for stablization, default criteria 
        are 120 seconds within 0.01 Kelvin from the setpoint.

        Input:
            ...
        Output:
            ...
        '''
        #gasflow_low = self._gasflow_low
        #gasflow_high = self._gasflow_high
        _get_temperature = eval('self.get_ch%s_temperature' % channel)
        
        self.set_remote_status(3)
        self.set_setpoint_temperature(temperature)
        self.set_heater_control(channel)
        self.set_pid_control(1)
        count = 0
        print ('Waiting until set temperature (%s K) is reached and system '
                'is stable...' % temperature)

        while (count <= stabilization_time) and (count <= 1200):
            abs_error = abs(_get_temperature() - temperature)
            qt.msleep(1)
            if (abs_error < margin):
                count = count + 1
            else:
                count = 0

        actual_temperature = _get_temperature()
        if count >= 1200:
            print ('Warning: temperature seems to be not very stable. '
                   ' Temperature: ' + str(actual_temperature))
            return False
        else:
            print ('Set temperature reached: ' 
                  + str(actual_temperature) + ' Kelvin')
            return True
        
    def _execute(self, message):
        '''
        Write a command to the device

        Input:
            message (str) : write command for the device

        Output:
            None
        '''
        logging.info(__name__ + 
                 ' : Send the following command to the device: %s' % message)
        result = self._visainstrument.ask(message)  
        if result.find('?') >= 0:
            print "Error: Command %s not recognized" % message
        else:
            return result

    def identify(self):
        '''
        Identify the device

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Identify the device')
        return self._execute('V')

    def remote(self):
        '''
        Set control to remote & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to remote & locked')
        self.set_remote_status(3)

    def local(self):
        '''
        Set control to local & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to local & locked')
        self.set_remote_status(0)

    def clear(self):
        '''
        Clear communication buffer
        
        Input:
            None
        Ouput:
            None
        '''
        logging.info(__name__ + 
                        ' : Clear visa instrument communication buffer.')
        self._visainstrument.clear()

    def do_set_remote_status(self, mode):
        '''
        Set remote control status.

        Input:
            mode(int) :
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",

        Output:
            None
        '''
        status = {
        0 : "Local and locked",
        1 : "Remote and locked",
        2 : "Local and unlocked",
        3 : "Remote and unlocked"
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting remote control status to %s' 
                         % status.get(mode,"Unknown"))
            self._execute('C%s' % mode)
        else:
            print 'Invalid mode inserted: %s' % mode
            
    def do_get_remote_status(self):
        '''
        Get remote control status

        Input:
            None

        Output:
            result(str) :
            "Local & locked",
            "Remote & locked",
            "Local & unlocked",
            "Remote & unlocked"
        '''
        logging.info(__name__ + ' : Get remote control status')
        result = self._execute('X')
        return int(result[5])

    def do_set_heater_control(self, channel):
        '''
        Set heater control to one of the channels

        Input:
            none
        Output:
            none
        '''
        logging.info(__name__ + ' : Setting heater control sensor')
        self._visainstrument.ask('H%s' %channel)

    def do_get_auto_pid_status(self):
        '''
        Get the Auto-PID status

        Input:
            None

        Output:
            result (str) :
                "Auto-PID disabled",
                "Auto-PID enabled"
        '''
        logging.info(__name__ + 
            ' : Getting Auto-PID status: %s' % int(self._execute('X')[12]))
        return int(self._execute('X')[12])

    def do_get_temperature(self, channel):
        '''
        Demand output current of device

        Input:
            None

        Output:
            result (float) : output current in Amp
        '''
        logging.info(__name__ + 
                        ' : Read temperature from channel' + str(channel))
        result = self._execute('R' + str(channel))
        return float(result.replace('R',''))

    def do_get_heater_voltage(self):
        '''
        Get voltage on heater

        Input:
            None
        Output:
            Voltage on heater
        '''
        logging.info(__name__ + ' : Getting voltage from heater')
        result = self._execute('R6')
        return float(result.replace('R',''))
    
    def do_set_pid_control(self, mode):
        '''
        Set PID control status.

        Input:
            mode(int) :
            0: "Heater manual, gas manual",
            1: "Heater auto, gas manual",
            2: "Heater manual, gas auto",
            3: "Heater auto, gas auto".

        Output:
            None
        '''
        status = {
            0 : "Heater manual, gas manual",
            1 : "Heater auto, gas manual",
            2 : "Heater manual, gas auto",
            3 : "Heater auto, gas auto"}
        if status.__contains__(mode):
            logging.info(__name__ + 
        ' : Setting PID control to sensor %s' % status.get(mode,"Unknown"))
            self._execute('A%s' % mode)
        else:
            print 'Invalid mode inserted: %s' % mode
            
    def do_get_pid_control(self):
        '''
        Get PID control status.
        Input:
            none
        Output:
            mode(int) :
            0: "Heater manual, gas manual",
            1: "Heater auto, gas manual",
            2: "Heater manual, gas auto",
            3: "Heater auto, gas auto".

        Output:
            None
        '''
        status = {
            0 : "Heater manual, gas manual",
            1 : "Heater auto, gas manual",
            2 : "Heater manual, gas auto",
            3 : "Heater auto, gas auto"}
        logging.info(__name__ + ' : Get PID control status')
        return int(self._execute('X')[3])

    def do_set_proportional_term(self, value):
        '''
        Set proportional term of PID controller

        Input:
            Value in Kelvin

        Output:
            none
        '''
        logging.info(__name__ + 
            ' : Set proportional term of PID controller to ' + str(value))
        self._visainstrument.write('P' + str(value))

    def do_get_proportional_term(self):
        '''
        Get proportional term of PID controller

        Input:
            none

        Output:
            Value in Kelvin
        '''
        result = self._execute('R8')
        logging.info(__name__ + 
                     ' : Get proportional term of PID controller: ' 
                     + str(result.replace('R','')))
        return float(result.replace('R',''))

    def do_set_integral_term(self, value):
        '''
        Set integral action time of PID controller

        Input:
            Value in minutes

        Output:
            result (float) : value in minutes
        '''
        logging.info(__name__ + 
                     ' : Set integral action time of PID controller to ' 
                     + str(value))
        self._visainstrument.write('I' + str(value))

    def do_get_integral_term(self):
        '''
        Get integral action time of PID controller

        Input:
            none

        Output:
            Value in minutes
        '''
        result = self._execute('R9')
        logging.info(__name__ + 
                     ' : Get integral action time of PID controller: ' 
                     + str(result.replace('R','')))
        return float(result.replace('R',''))
    
    def do_set_derivative_term(self, value):
        '''
        Set derivative action time of PID controller

        Input:
            Value in minutes

        Output:
            result (float) : value in minutes
        '''
        logging.info(__name__ + 
                     ' : Set derivative action time of PID controller to ' 
                     + str(value))
        self._visainstrument.write('D' + str(value))

    def do_get_derivative_term(self):
        '''
        Get derivative action time of PID controller

        Input:
            none

        Output:
            Value in minutes
        '''
        result = self._execute('R10')
        logging.info(__name__ + 
                     ' : Get derivative action time of PID controller: ' 
                     + str(result.replace('R','')))
        return float(result.replace('R',''))
    
    def do_set_gas_flow(self, value):
        '''
        Set the gas flow with the needle valve

        Input:
            value in percent (between 0 and 100)

        Output:
            none
        '''
        logging.info(__name__ + ' : Set gas flow to ' + str(value))
        self._visainstrument.ask('G%s' % value)

    def do_get_gas_flow(self):
        '''
        Set the gas flow with the needle valve

        Input:
            none

        Output:
            Value in in percent
        '''
        result = self._execute('R7')
        logging.info(__name__ + 
                     ' : Get gas flow setting: ' 
                     + str(result.replace('R','')))
        return float(result.replace('R',''))

    def do_set_front_panel_display(self, display):
        '''
        Set front panel display to show one of the internal parameters.
        
        Input:
            mode(int)
            0 : "Set temperature",
            1 : "Sensor 1 temperature",
            2 : "Sensor 2 temperature",
            3 : "Sensor 3 temperature",
            4 : "Temperature error (+ve when set > measured)",
            5 : "Heater o/p (as Volts, approx.)",
            6 : "Heater o/p (as % of current limit)",
            7 : "Gas flow o/p (arbitrary units)",
            8 : "Proportinal band",
            9 : "Integral action time",
            10 : "Derivative action time",
            11 : "Channel 1 freq/4",
            12 : "Channel 2 freq/4",
            13 : "Channel 3 freq/4"
            
        Output
            none
        '''
        parameter = {
            0 : "Set temperature",
            1 : "Sensor 1 temperature",
            2 : "Sensor 2 temperature",
            3 : "Sensor 3 temperature",
            4 : "Temperature error (+ve when set > measured)",
            5 : "Heater o/p (as Volts, approx.)",
            6 : "Heater o/p (as % of current limit)",
            7 : "Gas flow o/p (arbitrary units)",
            8 : "Proportinal band",
            9 : "Integral action time",
            10 : "Derivative action time",
            11 : "Channel 1 freq/4",
            12 : "Channel 2 freq/4",
            13 : "Channel 3 freq/4"
            }
        if parameter.__contains__(display):
            logging.info(__name__ + 
            ' : Setting display to show %s' 
            % parameter.get(display,"Unknown"))
            self._visainstrument.write('F%s' % display)
        else:
            print 'Invalid mode inserted: %s' % display
            
    def do_set_setpoint_temperature(self, value):
        '''
        Set temperature setpoint (target temperature)
        Input:
            temperature (float) : target temperature in Kelvin

        Output:
            None
        '''
        logging.info(__name__ + ' : Setting target temperature to %s' % value)
        self._execute('T%s' % value)

    def do_get_setpoint_temperature(self):
        '''
        Get current temperature setpoint
        Input:
            none
        Output:
            temperature setpoint (target) in Kelvin
        '''
        result = self._execute('R0')
        logging.info(__name__ + 
                     ' : Getting current target temperature to %s' 
                     % result.replace('R',''))
        return float(result.replace('R',''))
        
    def do_set_maximum_heater_voltage(self, voltage):
        '''
        Set maximum heater voltage

        Input:
            Heater voltage in Volts

        Output:
            none
        '''
        logging.info(__name__ + 
                     ' : Setting maximum heater voltage to: %s' % voltage)
        self._visainstrument.write('M%s' % voltage)

    def do_set_heater_manual(self, voltage):
        '''
        Set heater control in manual mode and set heater voltage to 
        specified value.

        Input:
            Heater voltage in Volts

        Output:
            none
        '''
        logging.info(__name__ + ' : Setting heater voltage to: %s ,' % voltage,
                     'and switch to manual control')
        self._execute('O%s' % voltage)

