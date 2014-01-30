# Rigol_DSA815.py class, to perform the communication between the Wrapper and the device
# Markus Künzl <m.kunzl@unsw.edu.au>, 2014
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
import visa
from visa import resource_manager
import pyvisa.vpp43 as vpp43
import types
import logging
import numpy

class Rigol_DSA815(Instrument):
    '''
    This is the driver for the Rigol DA815 Spectrum Analyzer
Rigol = qt.instruments.create('Rigol','Rigol_DSA815',ipaddress='TCPIP0::192.168.1.11::inst0::INSTR')
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Rigol_DSA815', address='<ip address>',
                                port='<networkport>', timeout='<float>' reset='<bool>')
    '''

    def __init__(self, name, ipaddress, reset=False):
        '''
        Initializes the Rigol DSA815, and communicates with the wrapper.

        Input:self._create_invalid_ins
          name (string)    : name of the instrument
          address (string) : IP address
          port (integer)   : Network port
          timeout (float)  : Timeout in seconds
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Rigol DSA815')
        Instrument.__init__(self, name)

        # Add some global constants
        self._ipaddress = ipaddress
        print 'ip address is %s' % self._ipaddress
      #  self._port = port
      #  self._timeout = timeout
      #  self._visainstrument = visa.instrument(self._ipaddress)

        self._vi = vpp43.open(resource_manager.session, self._ipaddress)


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
             flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=1000, type=types.IntType)
        self.add_parameter('continuous_trigger_mode',
             flags=Instrument.FLAG_GETSET, type=types.BooleanType)
        self.add_parameter('sweep_time_mode',
             flags=Instrument.FLAG_GETSET, type=types.BooleanType)
        self.add_parameter('sweep_time',
             flags=Instrument.FLAG_GETSET, units='ms', minval=0.02, maxval=1.5e6, type=types.FloatType)

        #self.add_parameter('status',
        #    flags=Instrument.FLAG_GETSET, type=types.StringType)

        #self.add_function('reset')
        self.add_function ('get_all')
        self.add_function('aquire_single_trace')
        self.add_function('ask')
        self.add_function('get_power')
        self.add_function('get_mean_power')
        self.add_function('clear_average')
        self.add_function('set_trace_mode_average')

     #   self._session = vpp43.open_default_resource_manager()
  


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

    def ask(self, command):
        '''
        Sends a command, while adding CR and returns device responce
        
        Input:
            command (string)
        Output:
            responce (string)
        '''
        logging.debug('Writing command %s.' %command)
        vpp43.write(self._vi, command + '\n')
        qt.msleep(1e-3)
        response = vpp43.read(self._vi, 1024)
        return response


    def _huge_ask(self, command):
        '''
        Sends a command, while adding CR and returns device responce
        
        Input:
            command (string)
        Output:
            responce (string)
        '''
        vpp43.write(self._vi, command + '\n')
        qt.msleep(1e-3)
        response = vpp43.read(self._vi, 18052)
        return response


    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        vpp43.write(self._vi, '*RST\n')
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
        self.get_start_frequency()
        self.get_stop_frequency()
        self.get_frequency_span()
        self.get_center_frequency()
        self.get_continuous_trigger_mode()
        self.get_resolution_bandwidth()
        self.get_sweep_time()
        self.get_average_count()
        self.get_mean_power()


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

        

    def do_set_continuous_trigger_mode(self, value):
        '''
        Sets up the instrument for in free run mode, data aquired continuously
        '''
        value = self._bool_to_str(value)
        vpp43.write(self._vi, 'INIT:CONT %s\n' % value)
        print 'Continuous trigger %s' % value

    def do_get_continuous_trigger_mode(self):
        '''
        Reads the trigger mode of the device.
        '''
        return self.ask('INIT:CONT?')


    def aquire_single_trace(self):
        '''
        Aquires a single data trace and waits until finishing this before
        accepting new subsequent commands. Afterwards the response is read
        '''
        return self.ask('INIT:IMM; *OPC?')

    def set_trace_mode_average(self):
        '''
        Set the type of the specified trace.
        '''
        vpp43.write('TRACe1:MODE POW\n')


    def do_set_average_count(self, count):
        '''
        Sets the average count to the specified number. To switch off 
        averaging, set count to 1.

        Input:
            count (integer)
        '''
        #print count
        vpp43.write(self._vi, 'TRAC:AVER:COUN %s\n' % count)
        return True

    def do_get_average_count(self):
        '''
        Reads the average count. Count equals 1 = no averaging.
        '''
        return self.ask('TRAC:AVER:COUN?')

    def clear_average(self):
        '''
        Clear the number of averages of the trace.
        '''
        vpp43.write(self._vi, 'TRAC:AVER:CLE\n')

    def do_set_sweep_time_auto(self, value):
        '''
        Sets up the instrument for auto determined sweep time.
        '''
        value = self._bool_to_str(value)
        vpp43.write(self._vi, 'SENS:SWE:TIME:AUTO %s\n' % value)


    def do_get_sweep_time_mode(self):
        '''
        Reads the sweep time mode of the device.
        '''
        return self.ask('SENS:SWE:TIME:AUTO?')


    def do_set_sweep_time(self, time):
        '''
        Sets the sweep time in ms.

        Input:
            time in ms (float)
        '''
        vpp43.write(self._vi, 'SENS:SWE:TIME %s\n' % str(float(time)/1000))
        return True

    def do_get_sweep_time(self):
        '''
        Reads the sweep time.
        '''
        return str(float(self.ask('SENS:SWE:TIME?'))*1000)


    def do_set_center_frequency(self, center):
        '''
        Sets the center frequency of the measurement range
        '''
        vpp43.write(self._vi, 'SENS:FREQ:CENT %s\n' % center)
        return True

    def do_get_center_frequency(self):
        '''
        Reads the center frequency of the measurement range
        '''
        return self.ask('SENS:FREQ:CENT?')

    def do_set_start_frequency(self, start):
        '''
        Sets the start frequency of the measurement range
        '''
        vpp43.write(self._vi, 'SENS:FREQ:STAR %s\n' % start)
        return True

    def do_get_start_frequency(self):
        '''
        Reads the start frequency of the measurement range
        '''
        return self.ask('SENS:FREQ:STAR?')

    def do_get_stop_frequency(self):
        '''
        Reads the stop frequency of the measurement range
        '''
        return self.ask('SENS:FREQ:STOP?')
        

    def do_set_stop_frequency(self, stop):
        '''
        Sets the stop frequency of the measurement range
        '''
        vpp43.write(self._vi, 'SENS:FREQ:STOP %s\n' % stop)
        return True

    def do_set_frequency_span(self, span):
        '''
        Sets the frequency span of the measurement
        '''
        vpp43.write(self._vi, 'SENS:FREQ:SPAN %s\n' % span)
        return True

    def do_get_frequency_span(self):
        '''
        Reads the frequency span of the measurement range
        '''
        return self.ask('SENS:FREQ:SPAN?')

    def do_set_resolution_bandwidth(self, value):
        '''
        Sets the resolution bandwidth of the device to the specified value.
        '''

        vpp43.write(self._vi, 'SENS:BAND:RES %s\n' % value)
        return True

    def do_get_resolution_bandwidth(self):
        '''
        Reads the currently set resolution bandwidth of the device.
        '''
        return self.ask('SENS:BAND:RES?')

    def get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        data = self._huge_ask('TRACE:DATA? Trace1')[12:]
        return map(float,data.split(','))
