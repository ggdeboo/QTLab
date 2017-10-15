# AnaPico_APSYN420.py class, to perform the communication between the Wrapper 
# and the device
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
from numpy import pi

class AnaPico_APSYN420(Instrument):
    '''
    This is the driver for the AnaPico Synthesizer

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 
                                'AnaPico_APSYN420', 
                                address='<VISA address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the AnaPico_APSYN420, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : IP address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Agilent_E8257D')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        rm = visa.ResourceManager()
        self._visainstrument = rm.open_resource(self._address)

        # Output power of the synthesizer cannot be changed.
        self.add_parameter('phase',
            flags=Instrument.FLAG_GETSET, 
            units='rad', minval=-pi, maxval=pi, type=types.FloatType)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, 
            units='Hz', minval=1e5, maxval=20e9, type=types.FloatType)
        self.add_parameter('frequency_mode',
            flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=types.StringType)


        self.add_function('reset')
        self.add_function ('get_all')
        
        self.add_function('on')
        self.add_function ('off')

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
        self.get_phase()
        self.get_frequency()
        self.get_status()

    def do_get_phase(self):
        '''
        Reads the phase of the signal from the instrument
        Input:
            None
        Output:
            phase (float) : Phase in radians
        '''
        logging.debug(__name__ + ' : get phase')
        return float(self._visainstrument.query('PHAS?'))

    def do_set_phase(self, phase):
        '''
        Set the phase of the signal
        Input:
            phase (float) : Phase in radians
        Output:
            None
        '''
        logging.debug(__name__ + ' : set phase to %f' % phase)
        self._visainstrument.write('PHAS %sradians' % phase)

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument
        Input:
            None
        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.query('FREQ:CW?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument
        Input:
            freq (float) : Frequency in Hz
        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ:CW %sHz' % freq)

    def do_get_frequency_mode(self):
        '''
        Reads the frequency mode from the instrument
        Input:
            None
        Output:
            mode (string) : 'FIX', 'CW', 'SWP', 'LIST', or 'CHIR'
        '''
        logging.debug(__name__ + ' : set frequency mode')
        return self._visainstrument.query('FREQ:MODE?')

    def do_set_frequency_mode(self, mode):
        '''
        Set the frequency mode of the instrument
        Input:
            mode (string) : 'FIX', 'CW', 'SWP', 'LIST', or 'CHIR'
        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency mode to %s' % status)
        if mode.upper() in ('FIX', 'CW', 'SWP', 'LIST', 'CHIR'):
            status = status.upper()
        else:
            raise ValueError(
                'set_frequency_mode(): can only set FIX, CW, SWP, LIST, or CHIR')
        self._visainstrument.write('FREQ:MODE %s' % status)

    def do_get_status(self):
        '''
        Reads the output status from the instrument
        Input:
            None
        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.query('OUTP?')

        if (stat=='1'):
          return 'on'
        elif (stat=='0'):
          return 'off'
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
        if status.upper() in ('ON', 'OFF'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('OUTP %s' % status)
        
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

