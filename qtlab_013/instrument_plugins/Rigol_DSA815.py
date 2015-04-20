#  -*- coding: utf-8 -*-
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
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Rigol_DSA815', address='<ip address>',
                                port='<networkport>', timeout='<float>' reset='<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Rigol DSA815, and communicates with the wrapper.
        
        The Rigol can be operated by LAN or USB. Only LAN functionality has
        been programmed into the wrapper.

        Input:self._create_invalid_ins
          name (string)    : name of the instrument
          address (string) : IP address
          port (integer)   : Network port
          timeout (float)  : Timeout in seconds
          reset (blool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Rigol DSA815')
        Instrument.__init__(self, name)

        # Add some global constants
        self._address = address
#        print 'ip address is %s' % self._ipaddress
      #  self._port = port
      #  self._timeout = timeout
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.term_chars = '\n' # needed when using TCPIP 
        self._idn = self._visainstrument.ask('*IDN?')
        self._fmw_version = self._idn.split(',')[-1]
        if self._fmw_version == '00.01.07.00.01':
            logging.warning('This version of the firmware of the spectrum'
                            ' analyser might cause communication problems.')
                        
#        vpp43.write(self._vi, ':SYST:OPT?\n')
#        qt.msleep(.1)
#        option_list = vpp43.read(self._vi, 9030)
#        TG = option_list.split('|')[6].startswith('Y')
        self.TG = True

#        self.add_parameter('mean_power',
#             flags=Instrument.FLAG_GET, units='', type=types.FloatType, tags=['measure'])
        self.add_parameter('start_frequency',
                            flags=Instrument.FLAG_GETSET, 
                            units='Hz', 
                            minval=0, 
                            maxval=1.5e9, 
                            type=types.FloatType)
        self.add_parameter('stop_frequency',
                            flags=Instrument.FLAG_GETSET, 
                            units='Hz', 
                            minval=1, 
                            maxval=1.5e9, 
                            type=types.FloatType)
        self.add_parameter('frequency_span',
                            flags=Instrument.FLAG_GETSET, 
                            units='Hz', 
                            minval=1, 
                            maxval=1.5e9, 
                            type=types.FloatType)
        self.add_parameter('center_frequency',
                            flags=Instrument.FLAG_GETSET, 
                            units='Hz', 
                            minval=1, maxval=1.5e9, 
                            type=types.FloatType)
        self.add_parameter('resolution_bandwidth',
                            flags=Instrument.FLAG_GETSET, 
                            units='Hz', 
                            minval=100, 
                            maxval=1e6, 
                            type=types.FloatType)
        self.add_parameter('average_count',
                            flags=Instrument.FLAG_GETSET, 
                            units='', 
                            minval=1, 
                            maxval=1000, 
                            type=types.IntType)
        self.add_parameter('sweep_count',
                            flags=Instrument.FLAG_GETSET, 
                            units='', 
                            minval=1, 
                            maxval=9999, 
                            type=types.IntType)
        self.add_parameter('continuous_trigger_mode',
                            flags=Instrument.FLAG_GETSET, 
                            type=types.BooleanType)
        self.add_parameter('sweep_time_auto',
                            flags=Instrument.FLAG_SET, 
                            type=types.BooleanType)
        self.add_parameter('sweep_time',
                            flags=Instrument.FLAG_GETSET, 
                            units='s', 
                            minval=0.01, maxval=1.5e6, 
                            type=types.FloatType)
        self.add_parameter('measurement_function',
                            flags=Instrument.FLAG_GET, 
                            type=types.StringType,
                            option_list=('OFF',
                                         'TPOW',
                                         'ACP',
                                         'CHP',
                                         'OBW',
                                         'EBW',
                                         'CNR',
                                         'HD',
                                         'TOI'))
        self.add_parameter('trace_mode',
                            flags=Instrument.FLAG_GET, 
                            type=types.StringType,
                            format_map={'WRIT' : 'clear write',
                                        'MAXH' : 'max hold',
                                        'MINH' : 'min hold',
                                        'VIEW' : 'view',
                                        'BLANk': 'off',
                                        'VID'  : 'video average',
                                        'POW'  : 'power average'})
        self.add_parameter('trace_format',
                           flags=Instrument.FLAG_GETSET,
                           type=types.StringType,
               format_map={'ASCII' : 'ASCII character separated by commas',
                           'REAL'  : '32 bit binary numbers'})             

        if self.TG:
            print 'Tracking generator option is installed.'
            self.add_parameter('tracking_generator_level', 
                                flags=Instrument.FLAG_GETSET, 
                                units='dBm', 
                                minval=-20.0, maxval=0.0, 
                                type=types.IntType)

        #self.add_parameter('status',
        #    flags=Instrument.FLAG_GETSET, type=types.StringType)

        #self.add_function('reset')
        self.add_function ('get_all')
        self.add_function('start_single_trace')
#        self.add_function('ask')
        self.add_function('get_power')
        self.add_function('get_mean_power')
        self.add_function('clear_average')
        self.add_function('set_trace_mode_average')
        self.add_function('ask_status')

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

    def _str_to_bool(self, val):
        '''
        Function to convert string into boolean value.
        '''
        if val == '1\n':
            return True
        else:
            return False

#    def ask(self, command):
#        '''
#        Sends a command, while adding CR and returns device responce
#        
#        Input:
#            command (string)
#        Output:
#            responce (string)
#        '''
#        logging.debug('Writing command %s.' %command)
#
#        unsuccesfull = True
#        attempt = 0
#        while unsuccesfull:
#            vpp43.write(self._vi, command + '\n')
#	    qt.msleep(.1)
#	    attempt+=1
#	    try:
#	        response = vpp43.read(self._vi, 9030)
#		unsuccesfull = False
#	    except visa.VisaIOError:
#                logging.warning('There was an error! %i' %attempt)
#                self.start_single_trace()

##        unsuccesfull = True
##        attempt = 0
##        while unsuccesfull:
##            vpp43.write(self._vi, command + '\n')
##            qt.msleep(.5)
##            attempt+=1
##            try:                
##                response = vpp43.read(self._vi, 9030)
##                unsuccesfull = False
##       except VisaIOError:
##            except:
##                logging.warning('There was an error! %i' %attempt)
#        return response

#    def read(self):
#        '''
#        Test function to read the buffer.
#        '''
#        logging.debug('Reading from the Rigol SA.')
#        return vpp43.read(self._vi, 1024)


#    def _huge_ask(self, command):
#        '''
#        Sends a command, while adding CR and returns device responce
#        
#        Input:
#            command (string)
#        Output:
#            responce (string)
#        '''
#        vpp43.write(self._vi, command + '\n')
#        qt.msleep(1e-3)
#        response = vpp43.read(self._vi, 9026)
#        return response


    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
#        vpp43.write(self._vi, '*RST\n')
        self._visainstrument.write('*RST')
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
#        self.get_continuous_trigger_mode()
        self.get_resolution_bandwidth()
        self.get_sweep_time()
        self.get_average_count()
        self.get_measurement_function()
        self.get_trace_mode()
        self.get_trace_format()
        if self.TG:
            self.get_tracking_generator_level()
#        self.get_mean_power()


    def get_mean_power(self, units='dBm'):
        '''
        Reads the mean power per hertz within the set frequency span. 
        The returend value is a tuple of numbers where the first (index 0) 
        represents the meanpower in dBm, and the second number (index 1) 
        represents the mean power in mW.
        
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
        return [meanpower_dBm, meanpower_mW]
#        if units == 'dBm':
#            return meanpower_dBm
#        else:
#            return meanpower_mW

        

    def do_set_continuous_trigger_mode(self, value):
        '''
        Sets up the instrument for in free run mode, data acquired continuously
        '''
        value = self._bool_to_str(value)
#        vpp43.write(self._vi, 'INIT:CONT %s\n' % value)
        self._visainstrument.write('INIT:CONT %s' % value)
        print 'Continuous trigger %s' % value

    def do_get_continuous_trigger_mode(self):
        '''
        Reads the trigger mode of the device.
        '''
        return self._str_to_bool(self._visainstrument.ask(':INIT:CONT?'))


    def start_single_trace(self):
        '''
        Aquires a single data trace and waits until finishing this before
        accepting new subsequent commands. Doesn't read out.
        '''
        logging.debug('Start a single trace with the Rigol SA.')
#        vpp43.write(self._vi, 'INIT:IMM\n')
        self._visainstrument.write('INIT:IMM')

    def ask_status(self):
        '''
        Check whether the previous operation is completed. 
        If yes, continue, if no, check again after 10ms.
        '''
        status = self._visainsrument.ask('*OPC?')
        while True:
            if status == True:
                break


    def set_trace_mode_average(self):
        '''
        Set the type of the specified trace.
        '''
        logging.info('Set trace mode to average.')
#        vpp43.write(self._vi, ':TRACe1:MODE POW\n')
        self._visainstrument.write(':TRACe1:MODE POW')


    def do_set_average_count(self, count):
        '''
        Sets the average count to the specified number. To switch off 
        averaging, set count to 1.

        Input:
            count (integer)
        '''
        #print count
#        vpp43.write(self._vi, ':TRAC:AVER:COUN %s\n' % count)
        self._visainstrument.write(':TRAC:AVER:COUNT %s' % count)
        return True

    def do_get_average_count(self):
        '''
        Reads the average count. Count equals 1 = no averaging.
        '''
        return self._visainstrument.ask(':TRAC:AVER:COUN?')

    def clear_average(self):
        '''
        Clear the number of averages of the trace.
        '''
#        vpp43.write(self._vi, ':TRAC:AVER:CLE\n')
        self._visainstrument.write(':TRAC:AVER:CLE')

    def do_set_sweep_count(self, count):
        '''
        Sets the sweep count to the specified number.

        Input:
            count (integer)
        '''
#        vpp43.write(self._vi, ':SENS:SWE:COUN %s\n' % count)
        self._visainstrument.write(':SENS:SWE:COUN %s' % count)
        return True

    def do_get_sweep_count(self):
        '''
        Reads the sweep count.
        '''
        return self._visainstrument.ask(':SENS:SWE:COUN?')

    def do_set_sweep_time_auto(self, value):
        '''
        Sets up the instrument for auto determined sweep time.
        '''
        value = self._bool_to_str(value)
#        vpp43.write(self._vi, ':SENS:SWE:TIME:AUTO %s\n' % value)
        self._visainstrument.write(':SENS:SWE:TIME:AUTO %f' % value)


    def do_get_sweep_time_mode(self):
        '''
        Reads the sweep time mode of the device.
        '''
        return self._visainstrument.ask(':SENS:SWE:TIME:AUTO?')


    def do_set_sweep_time(self, time):
        '''
        Sets the sweep time in s.

        Input:
            time in ms (float)
        '''
#        vpp43.write(self._vi, ':SENS:SWE:TIME %s\n' % str(float(time)))
        self._visainstrument.write(':SENS:SWE:TIME %f' % time)
        return True

    def do_get_sweep_time(self):
        '''
        Reads the sweep time in s.
        '''
        return float(self._visainstrument.ask(':SENS:SWE:TIME?'))


    def do_set_center_frequency(self, center):
        '''
        Sets the center frequency of the measurement range
        '''
#        vpp43.write(self._vi, ':SENS:FREQ:CENT %s\n' % center)
        self._visainstrument.write(':SENS:FREQ:CENT %s' % center)
        return True

    def do_get_center_frequency(self):
        '''
        Reads the center frequency of the measurement range
        '''
        return self._visainstrument.ask(':SENS:FREQ:CENT?')

    def do_set_start_frequency(self, start):
        '''
        Sets the start frequency of the measurement range
        '''
#        vpp43.write(self._vi, ':SENS:FREQ:STAR %s\n' % start)
        self._visainstrument.write(':SENS:FREQ:STAR %f' % start)
        self.get_frequency_span() # Update the frequency span
        return True

    def do_get_start_frequency(self):
        '''
        Reads the start frequency of the measurement range
        '''
        return self._visainstrument.ask(':SENS:FREQ:STAR?')

    def do_get_stop_frequency(self):
        '''
        Reads the stop frequency of the measurement range
        '''
        return float(self._visainstrument.ask(':SENS:FREQ:STOP?'))
        

    def do_set_stop_frequency(self, stop):
        '''
        Sets the stop frequency of the measurement range
        '''
#        vpp43.write(self._vi, ':SENS:FREQ:STOP %s\n' % stop)
        self._visainstrument.write(':SENS:FREQ:STOP %f' % stop)
        self.get_frequency_span()
        return True

    def do_set_frequency_span(self, span):
        '''
        Sets the frequency span of the measurement
        '''
#        vpp43.write(self._vi, ':SENS:FREQ:SPAN %s\n' % span)
        self._visainstrument.write(':SENS:FREQ:SPAN %f' % span)
        return True

    def do_get_frequency_span(self):
        '''
        Reads the frequency span of the measurement range
        '''
        return self._visainstrument.ask(':SENS:FREQ:SPAN?')

    def do_set_resolution_bandwidth(self, value):
        '''
        Sets the resolution bandwidth of the device to the specified value.
        '''

#        vpp43.write(self._vi, ':SENS:BAND:RES %s\n' % value)
        self._visainstrument.write(':SENS:BAND:RES %f' % value)
        return True

    def do_get_resolution_bandwidth(self):
        '''
        Reads the currently set resolution bandwidth of the device.
        '''
        return self._visainstrument.ask(':SENS:BAND:RES?')

    def get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        data = self._visainstrument.ask(':TRACE:DATA? Trace1')[12:]
        return map(float,data.split(','))

    def do_get_tracking_generator_level(self):
        '''
        Reads the power level of the tracking generator.
        '''
        logging.debug(__name__ + ' : get tracking generator level')
        level = float(self._visainstrument.ask(':SOUR:POW:LEV:IMM:AMPL?'))
        return level

    def do_set_tracking_generator_level(self, level):
        '''
        Sets the power level of the tracking generator.
        '''
        logging.debug(__name__ + ' : set tracking generator level to %i' %
level)
#        vpp43.write(self._vi, ':SOUR:POW:LEV:IMM:AMPL %i' % level)
        self._visainstrument.write(':SOUR:POW:LEV:IMM:AMPL %i' % level)

    def do_get_measurement_function(self):
        '''
        Gets the measurement function.
        The query returns OFF, TPOW, ACP, CHP, OBW, EBW, CNR, HD or TOI. 
        '''
        logging.debug(__name__ + ' : get the measurement function.')
        return self._visainstrument.ask(':CONF?')

    def do_get_trace_mode(self):
        '''
        Gets the trace mode.
        '''
        logging.debug(__name__ + ' : get the trace mode.')
        return self._visainstrument.ask(':TRAC:MODE?')

    def do_get_trace_format(self):
        logging.debug(__name__ + ' : get the trace format.')
        response = self._visainstrument.ask(':FORM:TRAC:DATA?')
        return response.rstrip(',32')

    def do_set_trace_format(self, tr_format):
        logging.debug(__name__ + ' : set the trace format to %s.')
        self._visainstrument.write(':FORM:TRAC:DATA %s' % tr_format)
