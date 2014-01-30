# FieldFox_N9918A.py class, to perform the communication between the Wrapper and the device
# Markus Künzl <m.kunzl@unsw.edu.au> 2014
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
import qt
import telnetlib
import types
import logging
import numpy

class FieldFox_N9918A(Instrument):
    '''
    This is the driver for the FieldFox N9918A Microwave Analyzer

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'FieldFox_N9918A', address='<ip address>',
                                port='<networkport>', timeout='<float>' reset='<bool>')
    '''

    def __init__(self, name, ipaddress, port=5024, timeout=1, reset=False):
        '''
        Initializes the FieldFox N9918A, and communicates with the wrapper.

        Input:self._create_invalid_ins
          name (string)    : name of the instrument
          address (string) : IP address
          port (integer)   : Network port
          timeout (float)  : Timeout in seconds
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument FieldFox_N9918A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._ipaddress = ipaddress
        self._port = port
        self._timeout = timeout
        self._telnetinstrument = telnetlib.Telnet(self._ipaddress,self._port)
        self._telnetinstrument.read_until('\n')

#        self.add_parameter('mean_power',
#             flags=Instrument.FLAG_GET, units='', type=types.FloatType, tags=['measure'])
        self.add_parameter('start_frequency',
             flags=Instrument.FLAG_GETSET, units='Hz', minval=0, maxval=26.5e9, type=types.FloatType)
        self.add_parameter('stop_frequency',
             flags=Instrument.FLAG_GETSET, units='Hz', minval=1, maxval=26.5e9, type=types.FloatType)
        self.add_parameter('frequency_span',
             flags=Instrument.FLAG_GETSET, units='Hz', minval=1, maxval=13e9, type=types.FloatType)
        self.add_parameter('center_frequency',
             flags=Instrument.FLAG_GETSET, units='Hz', minval=1, maxval=26e9, type=types.FloatType)
        self.add_parameter('resolution_bandwidth',
             flags=Instrument.FLAG_GETSET, units='Hz', minval=300, maxval=1e6, type=types.FloatType)
        self.add_parameter('average_count',
             flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=100, type=types.IntType)
        self.add_parameter('free_run_mode',
             flags=Instrument.FLAG_SET, type=types.BooleanType)
        self.add_parameter('sweep_time',
             flags=Instrument.FLAG_GET, units='s', minval=0, maxval=100, type=types.FloatType)

        #self.add_parameter('status',
        #    flags=Instrument.FLAG_GETSET, type=types.StringType)

        #self.add_function('reset')
        self.add_function ('get_all')
        self.add_function('restart_averaging')
        self.add_function('aquire_single_trace')
        self.add_function('ask')
        self.add_function('get_power')
        self.add_function('get_mean_power')


        if (reset):
            self.reset()
        else:
            self.get_all()

    def _bool_to_str(self, val):
        '''
        Function to convert boolean to 'ON' or 'OFF'
        '''
        if val == True:
            return "ON"
        else:
            return "OFF"

    def _query(self, command):
        '''
        Sends a command, while adding CR and returns device responce
        
        Input:
            command (string)
        Output:
            responce (string)
        '''
        self._telnetinstrument.write(command + '\n')
        qt.msleep(1e-3)
        response = self._telnetinstrument.read_until('\n')
        return response[response.rfind('SCPI>')+6:-2]

    def ask(self, command):
        '''
        Sends a command and reads the response
        '''
        self._telnetinstrument.write(command + '\n')
        return self._telnetinstrument.read_until('\n')

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._telnetinstrument.write('*RST\n')
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None
       self.add_function ('get_all')
        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_mean_power()
        self.get_start_frequency()
        self.get_stop_frequency()
        self.get_frequency_span()
        self.get_center_frequency()
        self.get_resolution_bandwidth()
        self.get_average_count()


    def get_mean_power(self, units='dBm'):
        '''
        Reads the mean power per hertz within the set frequency span. The returend value is a tuple of numbers where the first (index 0) represents
        the meanpower in dBm, and the second number (index 1) represents the mean power in mW.
        
        Input:
            none
        Output:
            mean power (float)
        '''
        resolution = float(self.get_resolution_bandwidth())
        rawdata = self.get_power()
        data_mW = numpy.zeros(len(rawdata))
        for i in range (0, len(rawdata)):
            data_mW[i] = 10 ** (rawdata[i]/10) / resolution
        meanpower_dBm = 10 * numpy.log10(numpy.mean(data_mW))
        meanpower_mW = numpy.mean(data_mW)
        if units == 'dBm':
            return meanpower_dBm
        else:
            return meanpower_mW

        

    def do_set_free_run_mode(self, value):
        '''
        Sets up the instrument for in free run mode, data aquired continuously
        '''
        value = self._bool_to_str(value)
        self._telnetinstrument.write('INIT:CONT %s\n' % value)
        print 'Continuous trigger %s' % value


    def aquire_single_trace(self):
        '''
        Aquires a single data trace and waits until finishing this before accepting new subsequent commands. Afterwards the response is read
        '''
        self._telnetinstrument.write('INIT:IMM; *OPC?\n')
        self._telnetinstrument.read_until('\n')
        return True

    def do_set_average_count(self, count):
        '''
        Sets the average count to the specified number. To switch off averaging, set count to 1.

        Input:
            count (integer)
        '''
        #print count
        self._telnetinstrument.write('SENS:AVER:COUN %s\n' % count)
        return True

    def do_get_average_count(self):
        '''
        Reads the average count. Count equals 1 = no averaging.
        '''
        return self._query('SENS:AVER:COUN?\n')

    def restart_averaging(self):
        '''
        Trigger aquisition of data in single trace mode
        '''
        self._query('INIT:REST; *OPC?\n')
        return True

 #   def do_get_sweep_time(self)
        '''
        Reads the current sweep time of the device.
        '''
 #       self._query('SENS:SWE:TIME?\n')

    def do_set_center_frequency(self, center):
        '''
        Sets the center frequency of the measurement range
        '''
        self._telnetinstrument.write('SENS:FREQ:CENT %s\n' % center)
        return True

    def do_get_center_frequency(self):
        '''
        Reads the center frequency of the measurement range
        '''
        return self._query('SENS:FREQ:CENT?\n')

    def do_set_start_frequency(self, start):
        '''
        Sets the start frequency of the measurement range
        '''
        self._telnetinstrument.write('SENS:FREQ:STAR %s\n' % start)
        return True

    def do_get_start_frequency(self):
        '''
        Reads the start frequency of the measurement range
        '''
        return self._query('SENS:FREQ:STAR?\n')

    def do_get_stop_frequency(self):
        '''
        Reads the stop frequency of the measurement range
        '''
        return self._query('SENS:FREQ:STOP?\n')
        

    def do_set_stop_frequency(self, stop):
        '''
        Sets the stop frequency of the measurement range
        '''
        self._telnetinstrument.write('SENS:FREQ:STOP %s\n' % stop)
        return True

    def do_set_frequency_span(self, span):
        '''
        Sets the frequency span of the measurement
        '''
        self._telnetinstrument.write('SENS:FREQ:SPAN %s\n' % span)
        return True

    def do_get_frequency_span(self):
        '''
        Reads the frequency span of the measurement range
        '''
        return self._query('SENS:FREQ:SPAN?\n')

    def do_set_resolution_bandwidth(self, value):
        '''
        Sets the resolution bandwidth of the device to the specified value.
        '''
        self._telnetinstrument.write('SENS:BAND:RES %s\n' % value)
        return True

    def do_get_resolution_bandwidth(self):
        '''
        Reads the currently set resolution bandwidth of the device.
        '''
        return self._query('SENS:BAND:RES?')

    def get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        data = self._query('TRACE:DATA?')
        return map(float,data.split(','))
