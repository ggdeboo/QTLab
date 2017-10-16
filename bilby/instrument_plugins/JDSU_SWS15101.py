# JDSU_SWS15101 driver July 4, 2014
# 
# Gabriele de Boo <g.deboo@student.unsw.edu.au>
# Chunming Yin <c.yin@unsw.edu.au>
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
from time import sleep

class JDSU_SWS15101(Instrument):
    '''
    This is the driver for the JDSU SWS15101 Tunable Laser Source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'JDSU_SWS15101', 
                                address='<GPIB address>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
        '''
        logging.info(__name__ + ' : Initializing instrument JDSU_SWS15101')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address

        rm = visa.ResourceManager()
        self._visainstrument = rm.open_resource(self._address)
        if self._visainstrument.interface_type == 4:
            print('The JDSU laser is connected with the serial interface.')
            self._visainstrument.write_termination = '\r'
            self._visainstrument.read_termination = '\r'
            self._visainstrument.baud_rate = 9600
        self._visainstrument.clear()

        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, 
            units='mW', 
            minval=0, maxval=10, 
            type=types.FloatType)
        self.add_parameter('diode_current',
            flags=Instrument.FLAG_GETSET, 
            units='mA', 
            minval=0, maxval=150, 
            type=types.FloatType)
        self.add_parameter('wavelength',
            flags=Instrument.FLAG_GETSET, 
            units='nm', 
            minval=1460, maxval=1600, 
            type=types.FloatType)
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GET,
            units='GHz',
            type=types.FloatType)
        self.add_parameter('output_status',
            flags=Instrument.FLAG_GETSET, type=types.BooleanType)
        self.add_parameter('FSCWaveL',
            flags=Instrument.FLAG_SET, # Inst has no command to read FSC
            units='pm', 
            minval=-22.4, maxval=+22.4, 
            type=types.FloatType)
        self.add_parameter('current_limited',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType)
        
        self.add_function ('get_all')
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
        self.get_diode_current()
        self.get_wavelength()
        self.get_frequency()
        self.get_output_status()
        self.get_current_limited()

    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        '''return float(self._visainstrument.ask('P?'))
        '''
# Make sure that the information in buffer has been read out.
        if self._visainstrument.interface_type == 4:
            # Serial communication
            response = self._visainstrument.query('P?')
            response = response.lstrip('> ')
            if response.startswith('P='):
                return float(response.lstrip('P='))
            elif response == 'DISABLED':
                return 0
            else:
                logging.warning(__name__ + 
                ' get_power : incorrect response: %s' % response)
    
        attempt = 0
        Stat_word = self._visainstrument.stb
        while (Stat_word != 1) and (attempt<10):
            self._visainstrument.read()
            Stat_word = self._visainstrument.stb
            attempt += 1
            sleep(0.01)
        if attempt >= 10:
            logging.warning(__name__ + 
            ' may not be running properly: Status Code %s.' % Stat_word)
        self._visainstrument.write('P?')
# Wait until the status word shows the parameter available for reading.
        while ((Stat_word & 0b00010000) == 0) and (attempt<100):
            Stat_word = self._visainstrument.stb
            attempt += 1
            sleep(0.01)
        if attempt >= 100:
            logging.warning(__name__ + 
            ' may not be responding correctly: Status Code %s.' % Stat_word)

        P = self._visainstrument.read()
        if P == ('DISABLED'):
            return 0
        elif (P[0] == 'P'):
            return float(P[2:])
        else:
            logging.warning(__name__ + ' did not reply correctly: %s.' % P )
            return 0

    def do_set_power(self, pow):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in ??

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % pow)
        self._visainstrument.write('P=%s' % pow)
        return self._check_response()

    def do_get_diode_current(self):
        '''
        Read the diode current.
        '''
        logging.debug(__name__ + ' : get diode_current.')

        if self._visainstrument.interface_type == 4:
            # Serial communication
            response = self._visainstrument.query('I?')
            response = response.lstrip('> ')
            if response.startswith('I='):
                return float(response.lstrip('I='))
            elif response == 'DISABLED':
                return 0
            else:
                logging.warning(__name__ + 
                ' get_power : incorrect response: %s' % response)

        attempt = 0
        Stat_word = self._visainstrument.stb
        while (Stat_word != 1) and (attempt<10):
            self._visainstrument.read()
            Stat_word = self._visainstrument.stb
            attempt += 1
            sleep(0.01)
        if attempt >= 10:
            logging.warning(__name__ + 
            ' may not be running properly: Status Code %s.' % Stat_word)
        self._visainstrument.write('I?')
# Wait until the status word shows the parameter available for reading.
        while ((Stat_word & 0b00010000) == 0) and (attempt<100):
            Stat_word = self._visainstrument.stb
            attempt += 1
            sleep(0.01)
        if attempt >= 100:
            logging.warning(__name__ + 
            ' may not be responding correctly: Status Code %s.' % Stat_word)
        
        I = self._visainstrument.read()
        if I == ('DISABLED'):
            logging.info(__name__ + ' : Output is disabled.')
            return 0
        elif (I[0] == 'I'):
            return float(I[2:])
        else:
            logging.warning(__name__ + ' did not reply correctly: %s.' % I )
            return 0

    def do_set_diode_current(self, curr):
        '''
        Set the diode current.
        '''
        logging.debug(__name__ + ' : set diode_current to %.1f.' % curr)
        self._visainstrument.write('I=%.1f' % curr)
        return self._check_response()

    def do_get_wavelength(self):
        '''
        Reads the wavelength from the laser

        Input:
            None

        Output:
            L (float) : Wavelength in nm
        '''
        logging.debug(__name__ + ' : get wavelength')
        attempt = 0

        if self._visainstrument.interface_type == 4:
            # Serial communication
            response = self._visainstrument.query('L?')
            response = response.lstrip('> ')
            if response.startswith('L='):
                return float(response.lstrip('L='))
#            elif response == 'DISABLED':
#                return 0
            else:
                logging.error(__name__ + 
                ' get_power : incorrect response: %s' % response)

        Stat_word = self._visainstrument.stb
        while (Stat_word != 1) and (attempt<10):
            self._visainstrument.read()
            Stat_word = self._visainstrument.stb
            attempt += 1
            sleep(0.01)
        if attempt >= 10:
            logging.warning(__name__ + 
            ' may not be running properly: Status Code %s.' % Stat_word)
        self._visainstrument.write('L?')
# Wait until the status word shows the parameter available for reading.
        while ((Stat_word & 0b00010000) == 0) and (attempt<100):
            Stat_word = self._visainstrument.stb
            attempt += 1
            sleep(0.01)
        if attempt >= 100:
            logging.warning(__name__ + 
            ' may not be responding correctly: Status Code %s.' % Stat_word)
        
        L = self._visainstrument.read()


        if L == ('DISABLED'):
            L = 0
        elif (L[0] == 'L'):
            return float(L[2:])
        else:
            logging.warning(__name__ + ' did not reply correctly: %s.' % L )
            return 0

    def do_get_frequency(self):
        '''Get the optical frequency of the laser'''
        logging.debug(__name__ + ': Getting the optical frequency.')
        if self._visainstrument.interface_type == 4:
            # Serial communication
            response = self._visainstrument.query('f?')
            response = response.lstrip('> ')
            if response.startswith('f='):
                return float(response.lstrip('f='))
            else:
                logging.error(__name__ + 
                ' get_power : incorrect response: %s' % response)
        else:
            response = self._visainstrument.query('f?')
            return float(response.lstrip('f='))

    def do_set_wavelength(self, wavel):
        '''
        Set the coarse wavelength of the laser

        Input:
            wavel (float) : wavelength in nm

        Output:
            None
        '''
        logging.debug(__name__ + ' : set wavelength to %f' % wavel)
        self._visainstrument.write('L=%s' % wavel)
        return self._check_response()

    def do_set_FSCWaveL(self, FSCL):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set FSCwavelength to %f' % FSCL)
        self._visainstrument.write('FSCL=%s' % FSCL)
        return self._check_response()

    def do_get_output_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (Boolean) : True for 'on' or False for 'off'
        '''
        logging.debug(__name__ + ' : get status')
        P = self.get_power()
        if P == 0:
            return False 
        else:
            return True

    def do_set_output_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (Boolean) : True or False

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status:
            self._visainstrument.write('ENABLE')
        else:
            self._visainstrument.write('DISABLE')
        return self._check_response()

    def do_get_current_limited(self):
        '''Get whether the current is limited'''
        logging.debug(__name__ + ' : get current limited')
        if self._visainstrument.interface_type == 4:
            # Serial communication
            response = self._visainstrument.query('LIMIT?')
            response = response.lstrip('> ')
            if response == 'YES':
                return True
            elif response == 'NO':
                return False
            else:
                logging.error(__name__ + 
                ' get_power : incorrect response: %s' % response)
        else:
            # GPIB communication
            response = self._visainstrument.query('f?')
            if response == 'YES':
                return True
            elif response == 'NO':
                return False
            else:
                logging.error(__name__ + 
                ' get_power : incorrect response: %s' % response)

    def _check_response(self):
        '''Check whether the instrument has finished executing.
        
        For serial communication the instrument should write an 'OK' back
        Other options are:
            Value error     Value outside valid limits
            Command error   Syntax error
        '''
        if self._visainstrument.interface_type == 4:
            response = self._visainstrument.read()
            if response.lstrip('> ') == 'OK':
                return True
            elif response.lstrip('> ') == 'COMMAND ERROR':
                logging.warning(__name__ + ' set_wavelength : Command error')
            elif response.lstrip('> ') == 'VALUE ERROR':
                logging.warning(__name__ + ' set_wavelength : Value error')
            else:
                logging.warning(__name__ + 
                ' set_wavelength : Did not receive OK, but %s' % response)
        
