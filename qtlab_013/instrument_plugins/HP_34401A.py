#  -*- coding: utf-8 -*-
# HP_34401A.py driver for HP 34401A 6½ digit Digital Multimeter
# Thomas Watson <tfwatson15@gmail.com>
# Gabriele de Boo <ggdeboo@gmail.com>
# Based on the Keithley_2001.py driver. 

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

function_unit = { 'VOLT'    : 'V',
                  'CURR'    : 'A',
                  'RES'     : 'Ohm',
                  'FRES'    : 'Ohm',
                }

def bool_to_str(val):
    '''
    Function to convert boolean to 'ON' or 'OFF'
    '''
    if val == True:
        return "ON"
    else:
        return "OFF"

class HP_34401A(Instrument):
    '''
    This is the driver for the HP 34401A 6½ digit Multimeter
    #still needs a bit of debugging

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_34401A',
        address='<GBIP address>',
        reset=<bool>,
        change_display=<bool>,
        change_autozero=<bool>)
    '''

    def __init__(self, name, address, reset=False,
        change_display=False, change_autozero=False):
        '''
        Initializes the HP_34401A, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
            change_display (bool)   : If True (default), automatically turn off
                                        display during measurements.
            change_autozero (bool)  : If True (default), automatically turn off
                                        autozero during measurements.
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument HP_34401A')
        Instrument.__init__(self, name, tags=['physical', 'measure'])

        # Add some global constants
        self.__name__ = name
        self._address = address

        rm = visa.ResourceManager()
        self._visainstrument = rm.open_resource(self._address)
        self._visainstrument.timeout = 500 
        if self._visainstrument.interface_type == 4: # serial?
            self._visainstrument.read_termination = '\r\n'
            self._visainstrument.write('SYST:REMOTE')
        self._modes = ['VOLT', 
                       'VOLT:AC', 
                       'CURR',
                       'CURR:AC',
                       'RES',
                       'FRES', 
                       'FREQ',
                       'PER',
                       'CONT',
                       'DIOD',
                      ]
        self._change_display = change_display
        self._change_autozero = change_autozero

        self._trigger_count = 0
        self._triggers_sent = 0
        self._wait_for_trigger = False

        # Add parameters to wrapper
        self.add_parameter('range',
            flags=Instrument.FLAG_GETSET,
            units='', minval=0.01, maxval=100, type=types.FloatType)

        # trigger section
        self.add_parameter('trigger_count',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.IntType)
        self.add_parameter('trigger_delay',
            flags=Instrument.FLAG_GETSET,
            units='s', minval=0, maxval=3600, type=types.FloatType)
        self.add_parameter('trigger_source',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            format_map = { 'BUS' : 'bus',
                           'IMM' : 'immediate',
                           'EXT' : 'external'}
            )
        self.add_parameter('sample_count',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.IntType,
            minval=1, maxval=50000)
    
        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            format_map = { 
                            'VOLT'   : 'voltage DC',
                            'VOLT:AC'   : 'voltage AC',
                            'CURR'   : 'current DC',
                            'CURR:AC'   : 'current AC',
                            'RES'       : 'resistance',
                            'FRES'      : 'resistance 4 wire mode',
                            'FREQ'      : 'frequency',
                            'PER'       : 'period',
                            'CONT'      : 'continuity',
                            'DIOD'      : 'diode'
                        }
            )
        self.add_parameter('resolution',
            flags=Instrument.FLAG_GETSET,
            units='', minval = 3e-7, maxval=1e-4, type=types.FloatType)                  
        self.add_parameter('readval', flags=Instrument.FLAG_GET,
            units='AU',
            type=types.FloatType,
            tags=['measure'])
        self.add_parameter('nplc',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.FloatType, minval=0.02, maxval=100)
        self.add_parameter('display', flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('autozero', flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('autorange',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('last_error_message',
                type=types.StringType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('terminals',
            type=types.StringType,
            flags=Instrument.FLAG_GET,
            option_list=(
                'FRONT',
                'REAR'))

        # Add functions to wrapper
        self.add_function('set_mode_volt_ac')
        self.add_function('set_mode_volt_dc')
        self.add_function('set_mode_curr_ac')
        self.add_function('set_mode_curr_dc')
        self.add_function('set_mode_res')
        self.add_function('set_mode_fres')
        self.add_function('set_mode_freq')
        self.add_function('set_range_auto')
        self.add_function('reset')
        self.add_function('get_all')

        self.add_function('read')

        self.add_function('send_init')
        self.add_function('send_trigger')
        self.add_function('fetch')

        # Connect to measurement flow to detect start and stop of measurement
        #qt.flow.connect('measurement-start', self._measurement_start_cb)
        #qt.flow.connect('measurement-end', self._measurement_end_cb)

        if reset:
            self.reset()
        else:
            pass
            #self.get_all()
            #self.set_defaults()

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

    def set_defaults(self):
        '''
        Set to driver defaults:
        Output=data only
        Mode=Volt:DC
        Range=10 V
        Resolution 1e-5

        '''

        self.set_mode_volt_dc()
        self.set_range(10)
        self.set_resolution(1e-5)

    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.info('Get all relevant data from device')
        self.get_mode()
        self.get_range()
        self.get_trigger_count()
        self.get_sample_count()
        self.get_trigger_delay()
        self.get_trigger_source()
        self.get_nplc()
        self.get_display()
        self.get_autozero()
        self.get_autorange()
        self.get_terminals()
        self.get_last_error_message()

    def set_to_remote(self):
        '''
        Set the instrument to remote mode for RS-232 operation
        '''        
        if self._visainstrument.interface_type == 4: # serial?
            self._visainstrument.write('SYST:REM')
        else:
            logging.error('This function only applies to RS-232 operation.')

    def read(self): 
        '''
        Old function for read-out, links to get_readval()
        '''
        logging.debug('Link to get_readval()')
        return self.get_readval()

    def send_init(self):
        '''
        Send init to HP, use when triggering is not continous.
        '''
        self._visainstrument.write('INIT')
        self._wait_for_trigger = True
        self._triggers_sent = 0
        qt.msleep(0.020) # instrument needs 20 ms to set up

    def send_trigger(self):
        '''Send a trigger to the multimeter
        '''
        self._visainstrument.write('*TRG')
        self._triggers_sent += 1

    def fetch(self):
        '''Transfer readings stored in the multimeter's internal memory
        
        Use send_trigger() to trigger the device.
        Note that Readval is not updated since this triggers itself.
        '''
        if self._triggers_sent > 0:
            reply = self._visainstrument.query('FETCH?')
            if self._triggers_sent >= self._trigger_count:
                self._wait_for_trigger = False
        else:
            data_points = int(self._visainstrument.query('DATA:POIN?'))
            if data_points == 0:
                # No triggers have been sent and there is no data in the buffer
                logging.warning('No triggers have been sent yet and buffer' + 
                                ' is empty.')
            else:
                # No triggers have been sent, but the buffer is not empty
                reply = self._visainstrument.query('FETCH?')
        return float(reply[0:15])

    def set_mode_volt_ac(self): 
        '''
        Set mode to AC Voltage

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to AC Voltage')
        self.set_mode('VOLT:AC')

    def set_mode_volt_dc(self): 
        '''
        Set mode to DC Voltage

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to DC Voltage')
        self.set_mode('VOLT')

    def set_mode_curr_ac(self): 
        '''
        Set mode to AC Current

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to AC Current')
        self.set_mode('CURR:AC')

    def set_mode_curr_dc(self): 
        '''
        Set mode to DC Current

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to DC Current')
        self.set_mode('CURR')

    def set_mode_res(self):
        '''
        Set mode to Resistance

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to Resistance')
        self.set_mode('RES')

    def set_mode_fres(self):    
        '''
        Set mode to 'four wire Resistance'

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to "four wire resistance"')
        self.set_mode('FRES')


    def set_mode_freq(self):    
        '''
        Set mode to Frequency

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to Frequency')
        self.set_mode('FREQ')

    def set_range_auto(self, mode=None):
        '''
        Old function to set autorange, links to set_autorange()
        '''
        logging.debug('Redirect to set_autorange')
        self.set_autorange(True)


# --------------------------------------
#           parameters
# --------------------------------------

    def do_get_readval(self, ignore_error=False):
        '''
        Aborts current trigger and sends a new trigger
        to the device and reads float value.

        Input:
            ignore_error (boolean): Ignore trigger errors, default is 'False'

        Output:
            value(float) : current value on input
        '''

        logging.debug('Read current value')
        text = self._visainstrument.query('READ?')
        self._trigger_count = 0
        text = re.sub('N.*','',text)
            
        return float(text)


    def do_set_range(self, val, mode=None):
        '''
        Set range to the specified value for the
        designated mode. If mode=None, the current mode is assumed

        Input:
            val (float)   : Range in specified units
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            None
        '''
        
        logging.debug('Set range to %s' % val)
        self._set_func_par_value(mode, 'RANG', val)

    def do_get_range(self, mode=None):
        '''
        Get range for the specified mode.
        If mode=None, the current mode is assumed.

        Input:
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            range (float) : Range in the specified units
        '''
        logging.debug('Get range')
        return float(self._get_func_par(mode, 'RANG'))

    def do_set_nplc(self, val, mode=None, unit='APER'):
        '''
        Set integration time to the specified value in Number of Powerline Cycles.
        To set the integrationtime in seconds, use set_integrationtime().
        Note that this will automatically update integrationtime as well.
        If mode=None the current mode is assumed

        Input:
            val (float)   : Integration time in nplc.
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        mode = self.get_mode(query=False)
        if mode in ('VOLT',  'CURR', 'RES', 'FRES'):
            logging.debug('Set integration time to %s PLC' % val)
            self._set_func_par_value(mode, 'NPLC', val)
        else:
            logging.info('Cant set NPLC in this mode')     
        
    def do_get_nplc(self, mode=None, unit='APER'):
        '''
        Get integration time in Number of PowerLine Cycles.
        To get the integrationtime in seconds, use get_integrationtime().
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to get property of. Choose from self._modes.

        Output:
            time (float) : Integration time in PLCs
        '''
        mode = self.get_mode(query=False)
        if mode in ('VOLT',  'CURR', 'RES', 'FRES'):
            logging.debug('Read integration time in PLCs')
            return float(self._get_func_par(mode, 'NPLC'))            
        else:
            return float(0)

    def do_set_resolution(self, val, mode = None):
        '''
        Set resolution.
        If mode=None the current mode is assumed

        Input:
            val (float)   : Resolution.
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        mode = self.get_mode(query=False)
        if mode in ('VOLT' ,'VOLT:AC','CURR:AC', 'CURR', 'RES', 'FRES'):
            logging.debug('Set resolution to %s' % val)
            self._set_func_par_value(mode, 'RES', val)
        else:
            logging.info('Cant set resolution in this mode') 
        

    def do_get_resolution(self, mode = None):
        '''
        Get resolution
        
        Input:
        mode (string) : mode to get property of. Choose from self._modes.

        Output:
            resolution (float) :
        '''

        mode = self.get_mode(query=False)
        if mode in ('VOLT' ,'VOLT:AC','CURR:AC', 'CURR', 'RES', 'FRES'):
            logging.debug('Get resolution')
            return float(self._get_func_par(mode, 'RES'))
        else:
            return float(0)
        

    def do_set_trigger_count(self, val):
        '''
        Set trigger count
        if val>9999 count is set to INF

        Input:
            val (int) : trigger count

        Output:
            None
        '''
        logging.debug('Set trigger count to %s' % val)
        self._trigger_count = val
        if val > 9999:
            self._visainstrument.write('TRIG:COUNT INF')
        else:
            self._visainstrument.write('TRIG:COUNT %i' % val)

    def do_get_trigger_count(self):
        '''
        Get trigger count

        Input:
            None

        Output:
            count (int) : Trigger count
        '''
        logging.debug('Read trigger count from instrument')
        ans = self._visainstrument.query('TRIG:COUN?')
        try:
            ret = int(float(ans))
        except:
            ret = 0
        self._trigger_count = ret
        return ret

    def do_get_sample_count(self):
        '''Get the samples taken per trigger

        Input:
            None
    
        Output:
            sample_count (int) : sample count
        '''
        logging.debug(self.__name__ + 'Read the sample count from instrument')
        ans = self._visainstrument.query('SAMP:COUN?')
        return int(ans)

    def do_set_sample_count(self, val):
        logging.debug(self.__name__ + 'Setting sample count to %i' % val)
        self._visainstrument.write('SAMP:COUNT %i' % val)

    def do_set_trigger_delay(self, val):
        '''
        Set trigger delay to the specified value

        Input:
            val (float) : Trigger delay in seconds

        Output:
            None
        '''
        logging.debug('Set trigger delay to %s' % val)
        self._set_func_par_value('TRIG', 'DEL', val)

    def do_get_trigger_delay(self):
        '''
        Read trigger delay from instrument

        Input:
            None

        Output:
            delay (float) : Delay in seconds
        '''
        logging.debug('Get trigger delay')
        return float(self._get_func_par('TRIG', 'DEL'))

    def do_set_trigger_source(self, val):
        '''
        Set trigger source

        Input:
            val (string) : Trigger source

        Output:
            None
        '''
        logging.debug('Set Trigger source to %s' % val)
        self._set_func_par_value('TRIG', 'SOUR', val)

    def do_get_trigger_source(self):
        '''
        Read trigger source from instrument

        Input:
            None

        Output:
            source (string) : The trigger source
        '''
        logging.debug('Getting trigger source')
        return self._get_func_par('TRIG', 'SOUR')

    def do_set_mode(self, mode): 
        '''
        Set the mode to the specified value

        Input:
            mode (string) : mode to be set. Choose from self._modes

        Output:
            None
        '''
        logging.debug('Set mode to %s', mode)
        if mode in self._modes:
            string = 'SENS:FUNC "%s"' % mode
            self._visainstrument.write(string)

            if mode.startswith('VOLT'):
                self._change_units('V') 
            elif mode.startswith('CURR'):
                self._change_units('A')
            elif mode.startswith('RES'):
                self._change_units('Ohm')
            elif mode.startswith('FRES'):
                self._change_units('Ohm')
            elif mode.startswith('FREQ'):
                self._change_units('Hz')

        else:
            logging.error('invalid mode %s' % mode)

        # Get all values again because some paramaters depend on mode
        # self.get_all()

    def do_get_mode(self):

        '''
        Read the mode from the device

        Input:
            None

        Output:
            mode (string) : Current mode
        '''
        string = 'SENS:FUNC?'
        logging.debug('Getting mode')
        ans = self._visainstrument.query(string)
        return ans.strip('"')

    def do_get_display(self):
        '''
        Read the status of diplay

        Input:
            None

        Output:
            True = On
            False= Off
        '''
        logging.debug('Reading the status of the display from instrument')
        reply = self._visainstrument.query('DISP?')
        return bool(int(reply))

    def do_set_display(self, val):
        '''
        Switch the diplay on or off.

        Input:
            val (boolean) : True for display on and False for display off

        Output

        '''
        logging.debug('Set display to %s' % val)
        val = bool_to_str(val)
        self._visainstrument.write('DISP %s' % val)
        #return self._set_func_par_value('DISP',val)

    def do_get_autozero(self):
        '''
        Read the staturs of the autozero function

        Input:
            None

        Output:
            reply (boolean) : Autozero status.
        '''
        logging.debug('Reading autozero status from instrument')
        reply = self._visainstrument.query(':ZERO:AUTO?')
        return bool(int(reply))

    def do_set_autozero(self, val):
        '''
        Switch the autozero on or off.
        For front panel operation the autozero is set indirectly when you set
        the resolution:
            Resolution Choices      Integration Time    Autozero
            Fast 4 Digit            0.02 PLC            Off
          * Slow 4 Digit            1 PLC               On
            Fast 5 Digit            0.2 PLC             Off
          * Slow 5 Digit (default)  10 PLC              On
          * Fast 6 Digit            10 PLC              On
            Slow 6 Digit            100 PLC             On
        * These setings configure the multimeter just as if you had
          pressed the corresponding "DIGITS" keys from the front panel

        Input:
            val (boolean) : True for autozero on and False for autozero off

        Output

        '''
        logging.debug('Set autozero to %s' % val)
        val = bool_to_str(val)
        return self._visainstrument.write('SENS:ZERO:AUTO %s' % val)

    def do_set_autorange(self, val, mode=None): 
        '''
        Switch autorange on or off.
        If mode=None the current mode is assumed

        Input:
            val (boolean)
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        logging.debug('Set autorange to %s ' % val)
        val = bool_to_str(val)
        self._set_func_par_value(mode, 'RANG:AUTO', val)

    def do_get_autorange(self, mode=None):
        '''
        Get status of averaging.
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            result (boolean)
        '''
        logging.debug('Get autorange')
        reply = self._get_func_par(mode, 'RANG:AUTO')
        return bool(int(reply))

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
        reply = self._visainstrument.query(':ROUT:TERM?')
        if reply == 'FRON': # The source meter responds with 'FRON'
            logging.info('The terminal used by %s is FRONT.' %
                            (self.get_name())) 
            return 'FRONT'
        elif reply == 'REAR':
            logging.info('The terminal used by %s is %s.' %
                            (self.get_name(),reply)) 
            return reply
        else:
            logging.warning('Received unexpected response from %s.' %
                            self.get_name())
            raise Warning('Instrument %s responded with an unexpected ' + 
                            'response: %s.' %(self.get_name(),reply))

# --------------------------------------
#           Internal Routines
# --------------------------------------

    def _change_units(self, unit):
        self.set_parameter_options('readval', units=unit)
        
    def _determine_mode(self, mode):
        '''
        Return the mode string to use.
        If mode is None it will return the currently selected mode.
        '''
        logging.debug('Determine mode with mode=%s' % mode)
        if mode is None:
            mode = self.get_mode(query=False)
        if mode not in self._modes and mode not in ('INIT', 'TRIG', 'SYST', 'DISP'):
            logging.warning('Invalid mode %s, assuming current' % mode)
            mode = self.get_mode(query=False)   
        if mode == 'CONT':
            logging.warning('Multimeter is in continuity mode.')
        if mode == 'DIOD':
            logging.warning('Multimeter is in diode mode.')
        return mode

    def _set_func_par_value(self, mode, par, val):
        '''
        For internal use only!!
        Changes the value of the parameter for the function specified

        Input:
            mode (string) : The mode to use
            par (string)  : Parameter
            val (depends) : Value

        Output:
            None
        '''
        mode = self._determine_mode(mode)
        string = ':%s:%s %s' % (mode, par, val)
        logging.debug('Set instrument to %s' % string)
        self._visainstrument.write(string)

    def _get_func_par(self, mode, par):
        '''
        For internal use only!!
        Reads the value of the parameter for the function specified
        from the instrument

        Input:
            func (string) : The mode to use
            par (string)  : Parameter
:
        Output:
            val (string) :
        '''
        mode = self._determine_mode(mode)
        string = ':%s:%s?' % (mode, par)
        ans = self._visainstrument.query(string)
        logging.debug('query instrument for %s (result %s)' % \
            (string, ans))
        return ans

    def _measurement_start_cb(self, sender):
        '''
        Things to do at starting of measurement
        '''
        if self._change_display:
            self.set_display(False)
            #Switch off display to get stable timing
        if self._change_autozero:
            self.set_autozero(False)
            #Switch off autozero to speed up measurement

    def _measurement_end_cb(self, sender):
        '''
        Things to do after the measurement
        '''
        if self._change_display:
            self.set_display(True)
        if self._change_autozero:
            self.set_autozero(True)

    def do_get_last_error_message(self):
        '''
        Read out the last error message from the instrument.
        '''
        message = self._visainstrument.query('SYST:ERR?')
        return message

