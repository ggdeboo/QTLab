# HP_8130A.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Sam Hile <samhile@gmail.com>, 2011
# Takashi Kobayashi, 2014
# Gabriele de Boo <ggdeboo@gmail.com>, 2015
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

class HP_8130A(Instrument):
    '''
    This is the driver for the HP 8130A 1 channel Pulse Generator
    NOTE: this driver does NOT check for errors such as <width> being 
    greater than <period> or <low> being greater than <high>

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_8131A', 
                                address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_8131A, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument HP_8130A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.clear()
        self._visainstrument.timeout = 1
        self._idn = self._visainstrument.ask('*IDN?')
        if not self._idn.startswith('HEWLETT-PACKARD,8130A'):
            logging.error('The connected instrument is not a HP8130A pulser.')
            
        # Implemented parameters        
        self.add_parameter('period', 
                            type=types.FloatType, tags=['sweep'],
                            flags=Instrument.FLAG_GETSET,
                            minval=3.33e-9, maxval=99.9e-3, 
                            units='s')
##        self.add_parameter('dutycycle', type=types.IntType,
##            flags=Instrument.FLAG_GETSET,minval=1, maxval=99, units='percent')
        self.add_parameter('width', 
                            type=types.FloatType, 
                            tags=['sweep'],
                            flags=Instrument.FLAG_GETSET,
                            minval=1.0e-9, maxval=99.9e-3, 
                            units='s')
        self.add_parameter('delay', 
                            type=types.FloatType, 
                            tags=['sweep'],
                            flags=Instrument.FLAG_GETSET,
                            minval=0.0e-9, maxval=99.9e-3, 
                            units='s')
        self.add_parameter('high', 
                            type=types.FloatType, 
                            tags=['sweep'],
                            flags=Instrument.FLAG_GETSET,
                            minval=-4.90, maxval=5.0, 
                            units='V')
        self.add_parameter('low', 
                            type=types.FloatType, 
                            tags=['sweep'],
                            flags=Instrument.FLAG_GETSET,
                            minval=-5.0, maxval=4.90, 
                            units='V') 
        self.add_parameter('status', 
                            type=types.StringType,
                            flags=Instrument.FLAG_GETSET,
                            format_map={True:   'on',
                                        False:  'off'})
        self.add_parameter('inverted_output_status',
                            type=types.BooleanType,
                            flags=Instrument.FLAG_GETSET,
                            format_map={True:   'on',
                                        False:  'off'})
        self.add_parameter('double_pulse_mode',
                            type=types.BooleanType,
                            flags=Instrument.FLAG_GET,
                            format_map={True:   'on',
                                        False:  'off'})
        self.add_parameter('double_pulse_timing',
                            type=types.FloatType,
                            flags=Instrument.FLAG_GET,
                            units='s')
        self.add_parameter('external_input_trigger_threshold',
                            type=types.FloatType,
                            flags=Instrument.FLAG_GET,
                            minval=-5.0, maxval=5.0,
                            units='V')
        self.add_parameter('trigger_operating_mode',
                            type=types.StringType,
                            flags=Instrument.FLAG_GET,
                            option_list = ['AUTO',
                                        'TRIGGER',
                                        'BURST',
                                        'EWIDTH',
                                        'GATE'])
        self.add_parameter('pulse_duty_cycle',
                            type=types.FloatType,
                            flags=Instrument.FLAG_GET,
                            minval=0, maxval=100,
                            units='%')
        self.add_parameter('pulse_duty_cycle_mode',
                            type=types.BooleanType,
                            flags=Instrument.FLAG_GET,
                            format_map={True:   'on',
                                        False:  'off'})

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_mode_continuous')
        self.add_function('set_mode_trigger')
        self.add_function('set_mode_burst')
        self.add_function('send_trigger')
        self.add_function('off')
        self.add_function('on')

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

        self.get_period()
        self.get_width()
        self.get_delay()
        self.get_low()
        self.get_high()
        self.get_status()
        self.get_inverted_output_status()
        self.get_double_pulse_mode()
        self.get_double_pulse_timing()
        self.get_external_input_trigger_threshold()
        self.get_trigger_operating_mode()
        self.get_pulse_duty_cycle()
        self.get_pulse_duty_cycle_mode()

    def send_trigger(self):
        self._visainstrument.write('*TRG')

    # communication with device
    def do_get_width(self):
        '''
        Reads the pulse width from the device

        Input:
            None
        Output:
            width (float) : width in seconds
        '''
        logging.debug(__name__ + ' : get width')
        return float(self._visainstrument.ask('PULS:TIM:WIDT?'))
    
    def do_get_period(self):
        '''
        Reads the period of the instrument

        Input:
            None

        Output:
            period (float) : period in seconds
        '''
        logging.debug(__name__ + ' : get period')
        return float(self._visainstrument.ask("PULS:TIM:PER?"))

    def do_set_period(self, val):
        '''
        Sets the period of the instrument

        Input:
            val (float)   : period in seconds

        Output:
            None
        '''
        logging.debug(__name__ + ' : set period to %f' % val)
        self._visainstrument.write("PULS:TIM:PER " + str(val))
        self.error_check_timing()

##    def do_get_dutycycle(self):
##        '''
##        Reads the duty cycle
##
##        Input:
##            None
##        Output:
##            dcycle (int) : duty cycle in percent
##        '''
##        logging.debug(__name__ + ' : get duty cycle')
##        return int(self._visainstrument.ask('PULS:TIM:DCYC?'))
##
##    def do_set_dutycycle(self, val):
##        '''
##        Sets the duty cycle
##
##        Input:
##            val (int)   : duty cycle in percent
##        Output:
##            None
##        '''
##        logging.debug(__name__ + ' : set duty cycle to %f' % , val)
##        self._visainstrument.write('PULS:TIM:DCYC ' + str(val))

    def do_set_width(self, val):
        '''
        Sets the width of the pulse

        Input:
            val (float)   : width in seconds
        Output:
            None
        '''
        logging.debug(__name__ + ' : set width bto %f' % val)
        self._visainstrument.write('PULS:TIM:WIDT ' + str(val))
        self.error_check_timing()

    def do_get_delay(self):
        '''
        Reads the pulse delay from the device

        Input:
            None
        Output:
            delay (float) : delay in seconds
        '''
        logging.debug(__name__ + ' : get delay')
        return float(self._visainstrument.ask('PULS:TIM:DEL?'))

    def do_set_delay(self, val):
        '''
        Sets the delay of the pulse

        Input:
            val (float)   : delay in seconds
        Output:
            None
        '''
        logging.debug(__name__ + ' : set delay for to %f' % val)
        self._visainstrument.write('PULS:TIM:DEL ' + str(val))
        self.error_check_timing()

    def do_get_high(self):
        '''
        Reads the upper value from the device

        Input:
            None
        Output:
            val (float) : upper bound in Volts
        '''
        logging.debug(__name__ + ' : get high')
        return float(self._visainstrument.ask('PULS:LEV:HIGH?'))

    def do_set_high(self, val):
        '''
        Sets the upper value

        Input:
            val (float)   : high bound in Volts
        Output:
            None
        '''
        logging.debug(__name__ + ' : set high to %f' % val)
        self._visainstrument.write('PULS:LEV:HIGH ' + str(val))
        self.error_check_high(val)

    def do_get_low(self):
        '''
        Reads the lower value from the device for the specified channel

        Input:
            None
        Output:
            val (float) : lower bound in Volts
        '''
        logging.debug(__name__ + ' : get low')
        return float(self._visainstrument.ask('PULS:LEV:LOW?'))

    def do_set_low(self, val):
        '''
        Sets the lower value

        Input:
            val (float)   : lower bound in Volts
        Output:
            None
        '''
        logging.debug(__name__ + ' : set low to %f' % val)
        self._visainstrument.write('PULS:LEV:LOW ' + str(val))
        self.error_check_low(val)

    def do_get_status(self):
        '''
        Reads the status from the device

        Input:
            None
        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : getting status')
        val = self._visainstrument.ask('OUTP:PULS:STAT?')
        if (val=='ON'):
            return 'on'
        elif (val=='OFF'):
            return 'off'
        return 'error'

    def do_set_status(self, val):
        '''
        Sets the status

        Input:
            val (string)  : 'on' or 'off'
        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status to %s' % val)
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
            self._visainstrument.write('OUTP:PULSE:STAT ' + val)
        else:
            logging.error('Tried to set status to "' + str(val) +
                            '" (value must be "on"/"off")')

    def do_get_inverted_output_status(self):
        '''Get whether the inverted output is on or off.'''
        logging.debug(__name__ + ' : getting the status of the inverted ' +
                                 'output')
        response = self._visainstrument.ask('OUTP:PULS:CST?')        
        if response == 'ON':
            return True
        elif response == 'OFF':
            return False
        else:
            logging.warning('get_inverted_output_status : wrong response : %s'
                            % response)

    def do_set_inverted_output_status(self, status):
        '''Set the inverted output on or off.'''
        logging.debug(__name__ + ' : setting the status of the inverted ' +
                                 'output to %s' % status)
        if status:
            self._visainstrument.write('OUTP:PULS:CST ON')
        else:
            self._visainstrument.write('OUTP:PULS:CST OFF')

    def set_mode_continuous(self):
        '''
        Sets the instrument in 'auto' mode

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting instrument to continuous mode')
        self._visainstrument.write('INP:TRIG:MODE AUTO')

    def set_mode_trigger(self):
        self._visainstrument.write('INP:TRIG:MODE TRIG')

    def set_mode_burst(self):
        self._visainstrument.write('INP:TRIG:MODE BURS')

    def do_get_double_pulse_mode(self):
        '''Get whether the instrument is in double pulse mode'''
        logging.debug(__name__ + ' : getting double pulse mode')
        response = self._visainstrument.ask(':PULS:TIM:DOUB:MODE?')
        if response == 'ON':
            return True
        elif response == 'OFF':
            return False
        else:
            logging.warning('get_double_pulse_mode : wrong response : %s'
                            % response)

    def do_get_double_pulse_timing(self):
        '''Get the delay for the double pulse in double pulse mode'''
        logging.debug(__name__ + ' : getting double pulse timing')
        response = self._visainstrument.ask(':PULS:TIM:DOUB?')
        return float(response)        

    def do_get_external_input_trigger_threshold(self):
        '''Get the threshold for the external input trigger'''
        logging.debug(__name__ + ' : getting ext input trigger threshold')
        response = self._visainstrument.ask(':INP:TRIG:THR?')
        return float(response)

    def do_get_trigger_operating_mode(self):
        '''Get whether the pulser is in trigger operating mode'''
        logging.debug(__name__ + ' : getting the trigger operating mode')
        return self._visainstrument.ask(':INP:TRIG:MODE?')

    def do_get_pulse_duty_cycle(self):
        '''Get the duty cycle of the pulse'''
        logging.debug(__name__ + ' : getting the duty cycle of the pulse')
        return float(self._visainstrument.ask(':PULS:TIM:DCYC?'))

    def do_get_pulse_duty_cycle_mode(self):
        '''Get whether the pulser is in duty cycle mode'''
        logging.debug(__name__ + ' : getting duty cycle mode of the pulse')
        response = self._visainstrument.ask(':PULS:TIM:DCYC:MODE?')
        if response == 'ON':
            return True
        elif response == 'OFF':
            return False
        else:
            logging.warning('get_pulse_duty_cycle_mode : wrong response : %s'
                            % response)

    # shortcuts
    def off(self):
        '''
        Set status to 'off'

        Input:
            None
        Output:
            None
        '''
        self.set_status('OFF')

    def on(self):
        '''
        Set status to 'on'

        Input:
            None
        Output:
            None
        '''
        self.set_status('ON')
        self.error_check_timing()

    def error_check_timing(self):
        '''
        Ask the instrument if there are device dependant errors, send to 
        logging.warning
        
        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : checking instrument for errors')
        errval = self._visainstrument.ask('SYST:DERR? STR')
        if errval != "0,<No Error>":
            logging.warning(__name__ + ' : Device Error - ' + errval)


    def error_check_low(self, val):
        '''
        Compare intended value with real value, send discrepancy to 
        logging.warning
        
        Input:
            Low (float) : low level intended to be set

        Output:
            None
        '''
        logging.debug(__name__ + ' : checking for ignored input')
        errval = self._visainstrument.ask('SYST:DERR? STR')
        if val != self.do_get_low():
            logging.warning(__name__ + ' : Command Ignored - tried to set ' +
                                        'low > high or amplitude > 5')

    def error_check_high(self, val):
        '''
        Compare intended value with real value, send discrepancy to 
        logging.warning
        
        Input:
            Low (float) : low level intended to be set

        Output:
            None
        '''
        logging.debug(__name__ + ' : checking for ignored input')
        if val != self.do_get_high():
            logging.warning(__name__ + ' : Command Ignored - tried to set ' + 
                                        'high < low or amplitude > 5')
        
