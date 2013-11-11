# JDSU_SWS15101 driver
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

class JDSU_SWS15101(Instrument):
    '''
    This is the driver for the JDSU SWS15101 Tunable Laser Source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'JDSU_SWS15101', address='<GPIB address>')
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
        self._visainstrument = visa.instrument(self._address)

        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, units='mW', minval=0, maxval=10, type=types.FloatType)
        self.add_parameter('diode_current',
            flags=Instrument.FLAG_GETSET, units='mA', minval=0, maxval=150, type=types.FloatType)
        self.add_parameter('wavelength',
            flags=Instrument.FLAG_GETSET, units='nm', minval=1460, maxval=1600, type=types.FloatType)
        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, type=types.StringType)
        self.add_parameter('FSCWaveL',
            flags=Instrument.FLAG_SET, units='pm', minval=-22.4, maxval=+22.4, type=types.FloatType)
        
        self.add_function ('get_all')

        #self.get_all()
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
        self.get_status()

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
        P = self._visainstrument.ask('P?')
        if P == ('DISABLED'):
            P = 0    
        else:
            P = P[2:]
        return float(P)
    
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

    def do_get_diode_current(self):
        '''
        Read the diode current.
        '''
        logging.debug(__name__ + ' : get diode_current.')
        I = self._visainstrument.ask('I?')
        if (I[0] != 'I'):
            logging.warning(__name__ + ' did not reply correctly: %s.' % I )
            return 0
        if I == ('DISABLED'):
            logging.info(__name__ + ' : Output is disabled.')
            return 0
        else:
            return float(I[2:])

    def do_set_diode_current(self, curr):
        '''
        Set the diode current.
        '''
        logging.debug(__name__ + ' : set diode_current to %.1f.' % curr)
        self._visainstrument.write('I=%.1f' % curr)

    def do_get_wavelength(self):
        '''
        Reads the wavelength from the laser

        Input:
            None

        Output:
            L (float) : Wavelength in nm
        '''
        logging.debug(__name__ + ' : get wavelength')
        '''return float(self._visainstrument.ask('L?'))
        '''
        L = self._visainstrument.ask('L?')
        if (L[0] != 'L'):
            logging.warning(__name__ + ' did not reply correctly: %s.' % L )
            return 0
        if L == ('DISABLED'):
            L = 0
        else:
            L = L[2:]
        return float(L)
    
    def do_set_wavelength(self, wavel):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set wavelength to %f' % wavel)
        self._visainstrument.write('L=%s' % wavel)

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

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.ask('P?')

        if (stat!='DISABLED'):
          return 'enabled'
        else:
          return 'disabled'

    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        if status.upper() in ('ENABLE', 'DISABLE'):
            status = status.upper()
        else:
            raise ValueError('set_status(): can only set on or off')
        self._visainstrument.write('%s' % status)
