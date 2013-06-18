# SRS_SG386.py class, to perform the communication between the Wrapper and the device
# Chunming Yin 2013
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

class SRS_SG386(Instrument):
    '''
    This is the driver for the Stanford Research Systems (SRS) SG386 microwave source.
    Only the Type-N output is controlled in this driver.
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'SRS_SG386', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_E8257C, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument SRS_SG386')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, units='dBm', minval=-110, maxval=16.5, type=types.FloatType)

        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=0.95e6, maxval=6.075e9, type=types.FloatType)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('Frequency_Modulation_Rate',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=1e-6, maxval=50e3, type=types.FloatType)
        self.add_parameter('Frequency_Modulation_Size',
            flags=Instrument.FLAG_GETSET, units='Hz', minval=0.1, maxval=32e6, type=types.FloatType)
        self.add_parameter('Modulation_State',
            flags=Instrument.FLAG_GETSET, type=types.StringType)
##        self.add_parameter('Frequency_List',
##            flags=Instrument.FLAG_SET, type=numpy.ndarray)
##        self.add_parameter('Power_List',
##            flags=Instrument.FLAG_SET, type=numpy.ndarray)
##        self.add_parameter('Dwell_Times_List',
##            flags=Instrument.FLAG_SET, type=numpy.ndarray)

        self.add_function('reset')
        self.add_function('get_all')
##        self.add_function('List_sweep_freq_on')
##        self.add_function('List_sweep_freq_off')
##        self.add_function('List_sweep_power_on')
##        self.add_function('List_sweep_power_on')
##        self.add_function('Trigger')


        if (reset):
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
        logging.info(__name__ + ' : resetting instrument')
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
        logging.info(__name__ + ' : get all')
        self.get_power()
        self.get_frequency()
        self.get_status()

    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in dBm
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.ask('AMPR?'))

    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._visainstrument.write('AMPR%s' % amp)

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.ask('FREQ?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ%s' % freq)

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.ask('ENBR?')

        if (stat=='1'):
          return 'ON'
        elif (stat=='0'):
          return 'OFF'
        else:
          raise ValueError('Output status not specified : %s' % stat)
        return

    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if (status.upper()=='ON'):
            status = 1
        elif (status.upper()=='OFF'):
            status = 0
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('ENBR%s' % status)

    def do_get_Frequency_Modulation_Rate(self):
        '''
        Get the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : get FM rate')
        return float(self._visainstrument.ask('RATE?'))

    def do_set_Frequency_Modulation_Rate(self, size):
        '''
        Set the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : set FM rate to %s' % size)
        self._visainstrument.write('RATE%s' % size)

    def do_get_Frequency_Modulation_Size(self):
        '''
        Get the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : get FM size')
        return float(self._visainstrument.ask('FDEV?'))

    def do_set_Frequency_Modulation_Size(self, size):
        '''
        Set the size of the frequency modulation of FM
        '''
        logging.debug(__name__ + ' : set FM size to %s' % size)
        self._visainstrument.write('FDEV%s' % size)

    def do_get_Modulation_State(self):
        '''
        Get the status of the modulation
        '''
        logging.debug(__name__ + ' : get Modulation state')
        response = self._visainstrument.ask('MODL?')
        if response == '0':
            return 'OFF'
        if response == '1':
            return 'ON'
    def do_set_Modulation_State(self, status):
        '''
        Set the status of the modulation

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if (status.upper()=='ON'):
            status = 1
        elif (status.upper()=='OFF'):
            status = 0
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('MODL%s' % status)

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

