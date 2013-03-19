# HP_8131A.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Sam Hile <samhile@gmail.com>, 2011
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

class HP_8131A(Instrument):
    '''
    This is the driver for the HP 8131A 2 channel Pulse Generator
    (modification may be required for the single channel version)
    NOTE: this driver does now check for errors such as <width> being greater than <period>
          or <low> being greater than <high>

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_8131A', address='<GBIP address>, reset=<bool>')

    TODO: allow initialisation with 1 or 2 channels    
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_8131A, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument HP_8131A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Implemented parameters        
        self.add_parameter('period', type=types.FloatType, tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=3.33e-9, maxval=99.9e-3, units='sec')
##        self.add_parameter('dutycycle', type=types.IntType,
##            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
##            channels=(1, 2), minval=1, maxval=99, units='percent',channel_prefix='ch%d_')
        self.add_parameter('width', type=types.FloatType, tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=1.0e-9, maxval=99.9e-6, units='sec',channel_prefix='ch%d_')
        self.add_parameter('delay', type=types.FloatType, tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=0.0e-9, maxval=99.9e-3, units='sec',channel_prefix='ch%d_')
        self.add_parameter('high', type=types.FloatType, tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=-4.90, maxval=5.0, units='Volts',channel_prefix='ch%d_')
        self.add_parameter('low', type=types.FloatType, tags=['sweep'],
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, 2), minval=-5.0, maxval=4.90, units='Volts',channel_prefix='ch%d_')
        self.add_parameter('status', type=types.StringType, channels=(1, 2),
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,channel_prefix='ch%d_')

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('set_mode_continuous')
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
        #self._visainstrument.write('*RST')

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

        self.get('period')
        for i in range(1,3): #range requires (1,3) to iterate over 1 and 2
##            self.get('ch%d_dutycycle' % i)
            self.get('ch%d_width' % i)
            self.get('ch%d_delay' % i)
            self.get('ch%d_low' % i)
            self.get('ch%d_high' % i)
            self.get('ch%d_status' % i)


    # communication with device
    def do_get_period(self):
        '''
        Reads the period of the instrument (common to both channels)

        Input:
            None

        Output:
            period (float) : period in seconds
        '''
        logging.debug(__name__ + ' : get period for both channels')
        return 666#float(self._visainstrument.ask("PULS:TIM:PER?"))

    def do_set_period(self, val):
        '''
        Sets the period of the instrument (common to both channels)

        Input:
            val (float)   : period in seconds

        Output:
            None
        '''
        logging.debug(__name__ + ' : set period for both channels to %f' % val)
        #self._visainstrument.write("PULS:TIM:PER " + str(val))
        self.error_check_timing()

##    def do_get_dutycycle(self, channel=1):
##        '''
##        Reads the duty cycle from the specified channel
##
##        Input:
##            channel (int) : 1 or 2, the number of the designated channel (default 1)
##
##        Output:
##            dcycle (int) : duty cycle in percent
##        '''
##        logging.debug(__name__ + ' : get duty cycle for channel %d' % channel)
##        return int(self._visainstrument.ask('PULS' + str(channel) + ":TIM:DCYC?"))
##
##    def do_set_dutycycle(self, val, channel=1):
##        '''
##        Sets the duty cycle of the specified channel
##
##        Input:
##            val (int)   : duty cycle in percent
##            channel (int) : 1 or 2, the number of the designated channel (default 1)
##
##        Output:
##            None
##        '''
##        logging.debug(__name__ + ' : set duty cycle for channel %d to %f' % (channel, val))
##        self._visainstrument.write('PULS' + str(channel) + ":TIM:DCYC " + str(val))

    def do_get_width(self, channel=1):
        '''
        Reads the pulse width from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            width (float) : width in seconds
        '''
        logging.debug(__name__ + ' : get width for channel %d' % channel)
        return 666#float(self._visainstrument.ask('PULS' + str(channel) + ":TIM:WIDT?"))

    def do_set_width(self, val, channel=1):
        '''
        Sets the width of the pulse of the specified channel

        Input:
            val (float)   : width in seconds
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set width for channel %d to %f' % (channel, val))
        #self._visainstrument.write('PULS' + str(channel) + ":TIM:WIDT " + str(val))
        self.error_check_timing()

    def do_get_delay(self, channel=1):
        '''
        Reads the pulse delay from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            delay (float) : delay in seconds
        '''
        logging.debug(__name__ + ' : get delay for channel %d' % channel)
        return 666#float(self._visainstrument.ask('PULS' + str(channel) + ":TIM:DEL?"))

    def do_set_delay(self, val, channel=1):
        '''
        Sets the delay of the pulse of the specified channel

        Input:
            val (float)   : delay in seconds
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set delay for channel %d to %f' % (channel, val))
        #self._visainstrument.write('PULS' + str(channel) + ":TIM:DEL " + str(val))
        self.error_check_timing()

    def do_get_high(self, channel=1):
        '''
        Reads the upper value from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            val (float) : upper bound in Volts
        '''
        logging.debug(__name__ + ' : get high for channel %d' % channel)
        return 666#float(self._visainstrument.ask('PULS' + str(channel) + ":LEV:HIGH?"))

    def do_set_high(self, val, channel=1):
        '''
        Sets the upper value of the specified channel

        Input:
            val (float)   : high bound in Volts
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set high for channel %d to %f' % (channel, val))
        #self._visainstrument.write('PULS' + str(channel) + ":LEV:HIGH " + str(val))
        self.error_check_high(val, channel)

    def do_get_low(self, channel=1):
        '''
        Reads the lower value from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            val (float) : lower bound in Volts
        '''
        logging.debug(__name__ + ' : get low for channel %d' % channel)
        return 666#float(self._visainstrument.ask('PULS' + str(channel) + ":LEV:LOW?"))

    def do_set_low(self, val, channel=1):
        '''
        Sets the lower value of the specified channel

        Input:
            val (float)   : lower bound in Volts
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            None
        '''
        logging.debug(__name__ + ' : set low for channel %d to %f' % (channel, val))
        #self._visainstrument.write('PULS' + str(channel) + ":LEV:LOW " + str(val))
        self.error_check_low(val, channel)

    def do_get_status(self, channel=1):
        '''
        Reads the status from the device for the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            status (string) : 'on' or 'off'
        '''
        logging.debug(__name__ + ' : getting status for channel %d' % channel)
        val = 'ON'#self._visainstrument.ask('OUTP' + str(channel) + ':PULS:STAT?')
        if (val=='ON'):
            return 'on'
        elif (val=='OFF'):
            return 'off'
        return 'error'

    def do_set_status(self, val, channel=1):
        '''
        Sets the status of the specified channel

        Input:
            val (string)  : 'on' or 'off'
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status for channel %d to %s' % (channel, val))
        if ((val.upper()=='ON') | (val.upper()=='OFF')):
			logging.debug(__name__ + ' : setting status for channel %d to %s' % (channel, val))
            #self._visainstrument.write('OUTP' + str(channel) + ":PULSE:STAT " + val)
        else:
            logging.error('Tried to set status to "' + str(val) + '" (value must be "on"/"off")')

    def set_mode_continuous(self):
        '''
        Sets the instrument in 'auto' mode

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting instrument to continuous mode')
        #self._visainstrument.write('INP:TRIG:MODE AUTO')

    # shortcuts
    def off(self):
        '''
        Set status to 'off' - both channels

        Input:
            None

        Output:
            None
        '''
        self.do_set_status('off', 1)
        self.do_set_status('off', 2)

    def on(self, channel=1):
        '''
        Set status to 'on' for specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel (default 1)

        Output:
            None
        '''
        if channel == 1:
            self.do_set_status('on', channel)
            self.error_check_timing()
        elif channel == 2:
            self.do_set_status('on', channel)
            self.error_check_timing()
        else:            
            logging.warning(__name__ + ' : Nothing switched on - channel must be 1 or 2')

    def error_check_timing(self):
        '''
        Ask the instrument if there are device dependant errors, send to logging.warning
        
        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : checking instrument for errors')
        #errval = self._visainstrument.ask('SYST:DERR? STR')
        #if errval != "0,<No Error>":
        #    logging.warning(__name__ + ' : Device Error - ' + errval)


    def error_check_low(self, val, channel=1):
        '''
        Compare intended value with real value, send discrepancy to logging.warning
        
        Input:
            Low (float) : low level intended to be set

        Output:
            None
        '''
        logging.debug(__name__ + ' : checking for ignored input')
        #errval = self._visainstrument.ask('SYST:DERR? STR')
        #if val != self.do_get_low(channel):
        #    logging.warning(__name__ + ' : Command Ignored - tried to set low > high or amplitude > 5')

            
    def error_check_high(self, val, channel=1):
        '''
        Compare intended value with real value, send discrepancy to logging.warning
        
        Input:
            Low (float) : low level intended to be set

        Output:
            None
        '''
        logging.debug(__name__ + ' : checking for ignored input')
        if val != self.do_get_high(channel):
            logging.warning(__name__ + ' : Command Ignored - tried to set high < low or amplitude > 5')

            
        