# Agilent_N9918A.py class, to perform the communication between the Wrapper 
# and the device
# Takashi Kobayashi, Apr. 2014
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

class Agilent_N9918A(Instrument):
    '''
    This is the driver for the Agilent FieldFox 9918A

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 
                                'Agilent_9918A', 
                                address='TCPIP::<IP.ADDRESS>::7020::SOCKET')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_9918A, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : visa address (TCPIP)
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Agilent_9918A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.timeout = 120

        self.add_parameter('mode', 
                        flags=Instrument.FLAG_GETSET, 
                        type=types.StringType, option_list=('NA', 'SA'))
        self.add_parameter('sweep_time', 
                        flags=Instrument.FLAG_GETSET, 
                        units='s', minval=100e-9, maxval=2000.0, 
                        type=types.FloatType)
        self.add_parameter('sweep_time_read', 
                        flags=Instrument.FLAG_GET, units='s', 
                        type=types.FloatType)
        self.add_parameter('sweep_points', 
                        flags=Instrument.FLAG_GETSET,  
                        units='', minval=3, maxval=10001, type=types.IntType)

        self.add_parameter('frequency_center', 
                        flags=Instrument.FLAG_GETSET, 
                        units='Hz', minval=3e4, maxval=26.5e9, 
                        type=types.FloatType)
        self.add_parameter('frequency_span', 
                        flags=Instrument.FLAG_GETSET, 
                        units='Hz', minval=0, maxval=26.5e9, 
                        type=types.FloatType)
        self.add_parameter('frequency_start', 
                        flags=Instrument.FLAG_GETSET,  
                        units='Hz', minval=3e4, maxval=26.5e9,
                        type=types.FloatType)
        self.add_parameter('frequency_stop', 
                        flags=Instrument.FLAG_GETSET,  
                        units='Hz', minval=3e5, maxval=26.5e9,
                        type=types.FloatType)

        self.add_parameter('source_power', 
                        flags=Instrument.FLAG_GETSET, 
                        units='dBm', minval=-45, maxval=0,
                        type=types.FloatType)
        self.add_parameter('source_frequency', 
                        flags=Instrument.FLAG_GETSET,  
                        units='Hz', minval=3e4, maxval=26.5e9,
                        type=types.FloatType)
        self.add_parameter('source_mode', 
                        flags=Instrument.FLAG_GETSET, type=types.StringType, 
                        option_list=('CW', 'S/R'))


        self.add_parameter('RBW', 
                        flags=Instrument.FLAG_GETSET,  
                        units='Hz', minval=10, maxval=5e6,
                        type=types.FloatType)
        self.add_parameter('VBW', 
                        flags=Instrument.FLAG_GETSET,  
                        units='Hz', minval=10, maxval=5e6,
                        type=types.FloatType)
        self.add_parameter('IFBW', 
                        flags=Instrument.FLAG_GETSET,  
                        units='Hz', minval=10, maxval=100e3,
                        type=types.FloatType)


        self.add_parameter('trigger_source', 
                        flags=Instrument.FLAG_GETSET, 
                        type=types.StringType, 
                        option_list=('E', 'V', 'RFB', 'F')
                        format_map = {  'E'     : 'external',
                                        'V'     : 'video',
                                        'RFB'   : 'RF burst',
                                        'F'     : 'free run',}
                        )
        self.add_parameter('trigger_slope', 
                        flags=Instrument.FLAG_GETSET, 
                        type=types.StringType, option_list=('P', 'N'))
        self.add_parameter('trigger_delay', 
                        flags=Instrument.FLAG_GETSET,  
                        units='s', minval=-0.15, maxval=10,
                        type=types.FloatType)
        self.add_parameter('trigger_delay_state', 
                        flags=Instrument.FLAG_GETSET, 
                        type=types.StringType, option_list=('ON', 'OFF'))

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('send_trigger')
        self.add_function('get_trace') 
        self.add_function('get_NAtrace') 
        self.add_function('get_SAtrace') 
        self.add_function('get_xvalue') 

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
        self._visainstrument.write('*RST\n')
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
        self.get_mode()
        self.get_trigger_source()

    def send_trigger(self):
        '''
        send a trigger signal via the GPIB interface

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : sending trigger signal')
        self._visainstrument.write('INIT')
       
    def get_trace(self):
        '''
        get measured data array

        Input:
            None

        Output:
            formatted measured data
        '''
        mode = self._visainstrument.ask("INST?")
        if mode == "NA":
            return self.get_NAtrace()
        elif mode == "SA":
            return self.get_SAtrace()
        else:
            return self.get_NAtrace()

    def get_NAtrace(self):
        return self._visainstrument.ask("CALC:DATA:FDAT?")

    def get_SAtrace(self):
        return self._visainstrument.ask("TRAC:DATA?")

    def get_xvalue(self):
        '''
        get measured data array

        Input:
            None

        Output:
            formatted measured data
        '''
        return self._visainstrument.ask("SENS:FREQ:DATA?")


    def do_set_mode(self, s):
        self._visainstrument.write('INST %s' % s) 

    def do_get_mode(self):
        return self._visainstrument.ask('INST?')

    def do_set_sweep_time(self, t):
        self._visainstrument.write('SWE:TIME %f' % t) 

    def do_get_sweep_time(self):
        return self._visainstrument.ask('SWE:TIME?')

    def do_get_sweep_time_read(self):
        return self._visainstrument.ask('SWE:MTIM?')

    def do_set_sweep_points(self, pts):
        self._visainstrument.write('SWE:POIN %i' % pts) 

    def do_get_sweep_points(self):
        return self._visainstrument.ask('SWE:POIN?')

    def do_set_frequency_center(self, fc):
        self._visainstrument.write('FREQ:CENT %f' % fc) 

    def do_get_frequency_center(self):
        return self._visainstrument.ask('FREQ:CENT?')

    def do_set_frequency_span(self, fp):
        self._visainstrument.write('FREQ:SPAN %f' % fp) 

    def do_get_frequency_span(self):
        return self._visainstrument.ask('FREQ:SPAN?')

    def do_set_frequency_start(self, f1):
        self._visainstrument.write('FREQ:STAR %f' % f1)

    def do_get_frequency_start(self):
        return self._visainstrument.ask('FREQ:STAR?')

    def do_set_frequency_stop(self, f2):
        self._visainstrument.write('FREQ:STOP %f' % f2)

    def do_get_frequency_stop(self):
        return self._visainstrument.ask('FREQ:STOP?')

    def do_set_source_power(self, p):
        self._visainstrument.write('SOUR:POW %f' % p) 

    def do_get_source_power(self):
        return self._visainstrument.ask('SOUR:POW?')

    def do_set_source_frequency(self, fs):
        self._visainstrument.write('SOUR:FREQ %f' % fs) 

    def do_get_source_frequency(self):
        return self._visainstrument.ask('SOUR:FREQ?')

    def do_set_source_mode(self, m):
        self._visainstrument.write('SOUR:MODE %s' % m) 

    def do_get_source_mode(self):
        return self._visainstrument.ask('SOUR:MODE?')

    def do_set_IFBW(self, IFBW):
        self._visainstrument.write('BWID %f' % IFBW) 

    def do_get_IFBW(self):
        return self._visainstrument.ask('BWID?')

    def do_set_RBW(self, RBW):
        self._visainstrument.write('BAND %f' % RBW) 

    def do_get_RBW(self):
        return self._visainstrument.ask('BAND?')

    def do_set_VBW(self, VBW):
        self._visainstrument.write('BAND:VID %f' % VBW) 

    def do_get_VBW(self):
        return self._visainstrument.ask('BAND:VID?')

    def do_set_trigger_source(self, s):
        '''
        Set the trigger source

        '''
        logging.debug('{0} : Setting trigger source to {1}.'.format(
            __name__, s))
        self._visainstrument.write('TRIG:SOUR %s' % s) 

    def do_get_trigger_source(self):
        '''
        Get the trigger source
    
        '''
        return self._visainstrument.ask('TRIG:SOUR?')

    def do_set_trigger_slope(self, s):
        self._visainstrument.write('TRIG:SLOP %s' % s) 

    def do_get_trigger_slope(self):
        return self._visainstrument.ask('TRIG:SLOP?')

    def do_set_trigger_delay(self, t):
        self._visainstrument.write('TRIG:DEL %f' % t) 

    def do_get_trigger_delay(self):
        return self._visainstrument.ask('TRIG:DEL?')

    def do_set_trigger_delay_state(self, s):
        self._visainstrument.write('TRIG:DEL:STAT %s' % s)

    def do_get_trigger_delay_state(self):
        return self._visainstrument.ask('TRIG:DEL:STAT?')
