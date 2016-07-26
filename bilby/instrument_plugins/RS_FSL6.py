# RS_FSL6.py class, to perform the communication between the Wrapper and the device
# Pablo Asshoff <techie@gmx.de>, 2013
# Gabriele de Boo <ggdeboo@gmail.com>, 2016
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
from numpy import frombuffer, float32
import math

class RS_FSL6(Instrument):
    '''
    This is the driver for the Rohde & Schwarz FSL6 Spectrum Analyser

    Usage:
    Initialize with
    <name> = instruments.create('name', 'RS_FSL6', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the RS_FSL6, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.timeout = 1
        self._visainstrument.term_chars = '\n'

        self._installed_options = self._visainstrument.ask('*OPT?')
        bw_min = 300

        if 'B4' in self._installed_options:
            logging.info('Option B4 (OCXO reference frequency) is installed')
            logging.info(
                'Aging per year and 50 degrees temperature drift: .1 ppm')
        else:
            logging.info('Standard reference frequency is installed ')
            logging.info(
                'Aging per year and 50 degrees temperature drift: 1 ppm')
        if 'B7' in self._installed_options:
            logging.info('Option B7 (narrow resolution filters) is installed')
            bw_min = 10
        if 'B10' in self._installed_options:
            logging.info('Option B10 (GPIB interface) is instaleld')
        if 'B22' in self._installed_options:
            logging.info('Option B22 (RF amplifier) is installed')

        self._visainstrument.write('FORM REAL, 32')

        # Add parameters
        # frequency section
        self.add_parameter('center_frequency', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=9e3, maxval=6e9,
            units='Hz', format='%.04e')
        self.add_parameter('span', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=6e9, 
            units='Hz', format='%.04e')
        self.add_parameter('start_frequency', type=types.FloatType,
            flags=Instrument.FLAG_GET,
            minval=9e3, maxval=6e9,
            units='Hz', format='%.04e')
        self.add_parameter('stop_frequency', type=types.FloatType,
            flags=Instrument.FLAG_GET,
            minval=9e3, maxval=6e9,
            units='Hz', format='%.04e')
        self.add_parameter('bandwidth_resolution', type=types.FloatType,
            flags=Instrument.FLAG_GET,
            units='Hz', format='%.0f',
            minval=bw_min, maxval=10e6)

        # sweep
        self.add_parameter('sweep_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('continuous','single'))
        self.add_parameter('sweep_count', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=32767)
        self.add_parameter('sweep_time', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=1e-6, maxval=60,
            units='s', format='%.04e')
        self.add_parameter('sweep_points', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=101, maxval=32001,
            )
        
        # input section
        self.add_parameter('reference_level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-80, maxval=30,
            units='dBm', format='%.04e')
        self.add_parameter('input_attenuation', type=types.FloatType,
            flags=Instrument.FLAG_GET,
            minval=-30, maxval=0, minstep=5.0,
            units='dB', format='%.1f')
        self.add_parameter('input_impedance', type=types.IntType,
            flags=Instrument.FLAG_GET,
            option_list=(50, 75), units='Ohm')
        if 'B22' in self._installed_options:
            self.add_parameter('preamp_status', type=types.BooleanType,
                flags=Instrument.FLAG_GET,
                )

        self.add_parameter('channel_power', type=types.FloatType,
            flags=Instrument.FLAG_GET, 
            units='W', format='%.3e')

        # trace
        self.add_parameter('trace_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            format_map = { 'WRIT' : 'clear write',
                           'MAXH' : 'max hold',
                           'MINH' : 'min hold',
                           'AVER' : 'average',
                           'VIEW' : 'view',
                           'OFF'  : 'blank'})

        self.add_parameter('detector_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            format_map = { 'APE'  : 'auto peak',
                           'POS'  : 'positive peak',
                           'NEG'  : 'negative peak',
                           'SAMP' : 'sample',
                           'RMS'  : 'RMS',
                           'AVER' : 'average',
                           'QPE'  : 'quasi peak'})

        self.add_parameter('timetracemarkerpower', type=types.FloatType,
            flags=Instrument.FLAG_GET, 
            units='W', format='%.10e')
        self.add_parameter('display_onoff',
            flags=Instrument.FLAG_SET,
            type=types.StringType, units='')

        # IQ
        self.add_parameter('IQ_sample_rate', type=types.FloatType,
            flags=Instrument.FLAG_GET,
            units='S/s', minval=10e3, maxval=65.83e6,
            format='%.3e')
        self.add_parameter('IQ_samples', type=types.IntType,
            flags=Instrument.FLAG_GET,
            units='S', minval=1, maxval=523776)
        self.add_parameter('IQ_pretrigger_samples', type=types.IntType,
            flags=Instrument.FLAG_GET,
            units='S')
        self.add_parameter('IQresult', type=types.StringType,
            flags=Instrument.FLAG_GET, 
            units='')

        # trigger
        self.add_parameter('trigger_level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0.5, maxval=3.5,
            units='V', format='%.04e')
        self.add_parameter('trigger_delay', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=-100.0, maxval=100.0,
            units='s', format='%.03e')
        self.add_parameter('trigger_source', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            format_map = { 'IMM' : 'immediate',
                           'EXT' : 'external',
                           'IFP' : 'ifpower',
                           'VID' : 'video' })

        # reference
        self.add_parameter('reference_oscillator', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            format_map = { 'INT' : 'internal',
                           'EXT' : 'external'})

        self.add_parameter('measurement_mode', type=types.StringType,
            flags=Instrument.FLAG_GET,
            format_map={ 'SAN' : 'spectrum analyser'})

        # Add functions
        self.add_function('reset')
        self.add_function('get_all')

        self.add_function('init_power_measurement')
        self.add_function('init_IQ_measurement')
        self.add_function('init_zero_span')
        self.add_function('init_trace_readout')
        self.add_function('start_sweep')
        self.add_function('stop_power_measurement')
        self.add_function('convert_dBuV_to_V')  # works but apparently not 
                                                # needed, device returns 
                                                # usually V by default
#        self.add_function('stop_remote_control')
#        self.add_function('trigger_mode')
#        self.add_function('enable_trigger')


        if reset:
            self.reset()
        else:
            self.get_all()

    # Functions
    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST;*CLS')    # zuvor nur *RST
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
        self.get_center_frequency()
        self.get_span()
        self.get_start_frequency()
        self.get_stop_frequency()
        self.get_bandwidth_resolution()
        self.get_sweep_count()
        self.get_reference_level()
        self.get_sweep_mode()
        self.get_sweep_time()
        self.get_sweep_points()
        self.get_channel_power()
        self.get_trace_mode()
        self.get_detector_mode()

        self.get_input_attenuation()
        self.get_input_impedance()
        if 'B22' in self._installed_options:
            self.get_preamp_status()
        self.get_reference_oscillator()
        self.get_measurement_mode()
        self.get_IQ_sample_rate()
        self.get_IQ_samples()
        self.get_IQ_pretrigger_samples()
        self.get_trigger_level()
        self.get_trigger_delay()
        self.get_trigger_source()

    def do_set_display_onoff(self, type):
        '''
        Set the display on or off

        Input:
            type (string) : 'on' or 'off'

        Output:
            None
        '''

        logging.debug('set display to %s', type)
        if type is 'on':
            self._visainstrument.write('SYST:DISP:UPD ON') 
        elif type is 'off':
            self._visainstrument.write('SYST:DISP:UPD OFF') 
        else:
            logging.error('invalid type %s' % type)

    def init_IQ_measurement(self):
        '''
        Initializes an I/Q measurement

        Input:
            None

        Output:
            None
       '''
        logging.debug(__name__ + ' : initialization of I/Q (quadrature) measurement')
        
        #setting the trigger level to 0.5 V (bounds: 0.5 V to 3.5 V, p.1590 
        # of operating manual, RST value 1.4 V)
        self._visainstrument.write('TRIG:LEV 0.5 V')
        #self._visainstrument.write('BAND:RES 20MHz')     #resultion bandwidth. 20 MHz, only for test
        self._visainstrument.write('FREQ:SPAN 0Hz')        
        self._visainstrument.write('TRAC:IQ:STAT ON')       
        # enables acquisition of I/Q data, trace display on device not 
        # possible in this operation mode
        self._visainstrument.write('TRAC:IQ:SET NORM,20MHz,64MHz,EXT,POS,0,640')     
        #self._visainstrument.write('TRAC:IQ:SET NORM,100kHz,32MHz,EXT,POS,0,512') 
        #sample measurement configuration
        #filter: NORM, RBW: 10MHz, sample rate: 32 MHz, trigger source: 
        # external (EXT) / internal (IMM), trigger slope: positive, 
        #pretrigger samples: 0, numer of samples: 512
        self._visainstrument.write('FORMat ASC') # selects format of response 
                                                 # data (either REAL,32 or 
                                                 # ASC for ASCII)
        self._visainstrument.write('FREQ:CONT OFF')
        #return self._visainstrument.write('TRAC:IQ:DATA?')         #starts measurements and reads results
        #self._visainstrument.write('INIT;*WAI')             #apparently not necessary
        #self._visainstrument.write('TRAC:IQ OFF')        #close I/Q operation mode

    def init_power_measurement(self):
        '''
        Initializes a channel power measurement

        Input:
            None

        Output:
            None

        maybe add sweep time parameter etc. later and measure both sidebands for better statistics
        '''
        logging.debug(__name__ + ' : initialization of channel power measurement')
        self._visainstrument.write('POW:ACH:ACP 0')      
        self._visainstrument.write('POW:ACH:BAND 5KHZ')       
        #self._visainstrument.write('POW:ACH:BAND:ACH 40KHZ')          
        #self._visainstrument.write('POW:ACH:BAND:ALT1 50KHZ')      
        #self._visainstrument.write('POW:ACH:BAND:ALT2 60KHZ')       
        #self._visainstrument.write('POW:ACH:SPAC 30KHZ') 
        #self._visainstrument.write('POW:ACH:SPAC:ALT1 100KHZ')      
        #self._visainstrument.write('POW:ACH:SPAC:ALT2 140KHZ')        
        self._visainstrument.write('POW:ACH:MODE ABS')      # Switches on absolute power measurement.     
        self._visainstrument.write('INIT:CONT ON')    	# Switches over to single sweep mode (for OFF!!).     
        self._visainstrument.write('INIT;*WAI')    		# Starts a sweep and waits for the end of the sweep.

    def stop_power_measurement(self):
        '''
        Initializes a channel power measurement

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : stop channel power measurement') 
        self._visainstrument.write('INIT:CONT ON')    # Switches over to continuous sweep mode.   

    def init_zero_span(self, resbw, vidbw):
        '''
        Initializes a zero span measurement

        Input:
            resolution bandwidth, video bandwidth

        Output:
            None
       '''
        logging.debug(__name__ + ' : initialization of zero span measurement')
        self._visainstrument.write('FREQ:SPAN 0Hz')   
        self._visainstrument.write('BAND:RES %s' % resbw)     #resolution bandwidth, suggested: 100kHz
        self._visainstrument.write('BAND:VID %s' % vidbw)     #video bandwidth, suggested: 100kHz       
        #sweep time --> set from measurement script
        #self._visainstrument.write('CALC:MARK:FUNC:SUMM:PPE ON ')  # not required if time trace is evaluate in control computer
        self._visainstrument.write('INIT;*WAI')           # starts a sweep and waits for the end of the sweep.

    def start_sweep(self):
        logging.debug(__name__ + ' : start a sweep and wait till finished')
        self._visainstrument.write('INIT')
        #self._visainstrument.write('*WAI')

    def init_trace_readout(self):
        '''
        Read a trace
        p. 230 operating manual

        Input:
            mode, either ASCII or binary

        Output:
            None
        '''
        logging.debug(__name__ + ' : initialization of trace readout')
        self._visainstrument.write('FORM ASC')
        #if mode == 'ASCII':
        #    self._visainstrument.write('FORM ASC')         
        #elif mode == 'binary':
        #    self._visainstrument.write('FORM REAL,32')      
        #else: 
        #    print 'Not a valid mode, function requires mode as argument, parameter either ASC for ASCII file or binary for binary file'
        #    # ASCII file format, alternative: FORMat REAL,32 (binary file) / FORM ASC for ASCII
        ##self._visainstrument.write('MMEM:STOR:TRAC 1,'TEMPTRACE.DAT'')   
        #    #the previous command just creates a file locally on the analyer
        ##self._visainstrument.write('TRAC? TRACE1')
      
    def convert_dBuV_to_V(self,dBuV):
        '''
        converts dBuV to Volt

        Input:
            Voltage in dBuV

        Output:
            Voltage in Volt
        '''
        logging.debug(__name__ + ' : convert dBuV to Volt') 
        UinV = 10**(dBuV/20)/1E6    # formula from http://www.kathrein.de/include/pegelumrechnung.cfm
        return UinV

    def convert_dBm_to_W(self,dBm):
        '''
        converts dBm to Watt

        Input:
            power in dBm

        Output:
            power in Watt
        '''
        logging.debug(__name__ + ' : convert dBm to Watt') 
        PinW = 10**(dBm/10)/1E3    # formula from http://www.kathrein.de/include/pegelumrechnung.cfm
        return PinW

#    def stop_remote_control(self):
#        '''
#        Initializes a channel power measurement
#
#        Input:
#            None
#
#        Output:
#            None
#        '''
#        logging.debug(__name__ + ' : set to local control') 
#        self._visainstrument.write('INIT:CONT OFF')    	#GPIB  COMMAND  ??????



    # communication with machine
    def do_get_center_frequency(self):
        '''
        Get center frequency from device

        Input:
            None

        Output:
            center_frequency (float) : center frequency in Hz
        '''
        logging.debug(__name__ + ' : reading center frequency from instrument')
        return float(self._visainstrument.ask('FREQ:CENT?'))

    def do_set_center_frequency(self, center_frequency):
        '''
        Set center frequency of device

        Input:
            center_frequency (float) : center frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + 
            ' : setting center frequency to {0} Hz'.format(center_frequency))
        self._visainstrument.write('FREQ:CENT {0:e}'.format(center_frequency))

    def do_get_bandwidth_resolution(self):
        '''
        Get the resolution bandwidth
        '''
        return float(self._visainstrument.ask('SENS:BWID:RES?'))

    def do_get_sweep_mode(self):
        '''
        Get whether the instrument is in continuous sweep mode or single 
        measurements mode.
        '''
        logging.debug(__name__ + ' : getting the sweep mode.')
        sweep_mode = self._visainstrument.ask('INIT:CONT?')
        if sweep_mode == '0':
            return 'single'
        elif sweep_mode == '1':
            return 'continuous'
        else:
            logging.error(
                'Unknown response to INIT:CONT? : {0}'.format(sweep_mode))

    def do_set_sweep_mode(self, sweep_mode):
        '''
        Set the sweep mode to single or continuous
        '''
        logging.debug(__name__ + 
            ' : setting the sweep mode to {0}.'.format(sweep_mode))
        if sweep_mode.upper() == 'SINGLE':
            self._visainstrument.write('INIT:CONT OFF')
        elif sweep_mode.upper() == 'CONTINUOUS':
            self._visainstrument.write('INIT:CONT ON')

    def do_get_sweep_count(self):
        '''
        Get the sweep count
        '''
        logging.debug(__name__ + ' : Getting the sweep count.')
        return int(self._visainstrument.ask('SWE:COUN?'))

    def do_set_sweep_count(self, sweep_count):
        '''
        Set the sweep count
        '''
        logging.debug(__name__ + 
                    ' : Setting the sweep count to {0:d}'.format(sweep_count))
        self._visainstrument.write('SWE:COUN {0:d}'.format(sweep_count))

    def do_get_trigger_level(self):
        '''
        Get the trigger level
        '''
        logging.debug(__name__ + ' : getting trigger level.')
        return float(self._visainstrument.ask('TRIG:LEV?'))

    def do_set_trigger_level(self, triggerlevel):
        '''
        Set trigger level for TTL input

        Input:
            trigger level (float) : center frequency in V

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting trigger level to %s V' % triggerlevel)
        self._visainstrument.write('TRIG:LEV %e V' % triggerlevel)        

    def do_get_trigger_delay(self):
        '''
        Get the holdoff time of the trigger
        '''
        logging.debug(__name__ + ' : getting the trigger delay.')
        return float(self._visainstrument.ask('TRIG:HOLD?'))

    def do_set_trigger_delay(self, delay):
        '''
        Set the holdoff time of the trigger
        '''
        logging.debug(__name__ + 
                ' : setting the trigger delay to {0:.3f} s'.format(delay))
        if delay < 0.0:
            # negative delay only allowed when instrument is in zero span
            if not (self.get_span() == 0.0):
                logging.error(
                    'A negative delay can only be set if the span is zero.')
                return None
        self._visainstrument.write('TRIG:HOLD {0:f}s'.format(delay))

    def do_get_trigger_source(self):
        '''
        Get the source for the trigger
        '''
        logging.debug(__name__ + ' : getting the trigger source.')
        return(self._visainstrument.ask('TRIG:SOUR?')) 

    def do_set_trigger_source(self, source):
        '''
        Set the source for the trigger
        '''
        logging.debug(__name__ + 
                ' : setting the trigger source to {0}'.format(source))
        self._visainstrument.write('TRIG:SOUR {0}'.format(source))

    def do_get_span(self):
        '''
        Get span from device

        Input:
            None

        Output:
            span (float) : span in Hz
        '''
        logging.debug(__name__ + ' : reading span from instrument')
        return float(self._visainstrument.ask('FREQ:SPAN?'))

    def do_set_span(self,span):
        '''
        Set span of device

        Input:
            span (float) : span in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self._visainstrument.write('FREQ:SPAN %e' % span)

    def do_get_start_frequency(self):
        '''
        Get start frequency from spectrum analyser

        Input:
            None

        Output:
            start_frequency (float) : spart frequency in Hz
        '''
        logging.debug(__name__ + ' : reading start frequency from instrument')
        return float(self._visainstrument.ask('FREQ:STAR?'))

    def do_get_stop_frequency(self):
        '''
        Get stop frequency from spectrum analyser

        Input:
            None

        Output:
            stop_frequency (float) : spart frequency in Hz
        '''
        logging.debug(__name__ + ' : reading stop frequency from instrument')
        return float(self._visainstrument.ask('FREQ:STOP?'))

    def do_get_reference_level(self):
        '''
        Get reference level from device

        Input:
            None

        Output:
            reference_level (float) : reference level in dBm
        '''
        logging.debug(__name__ + ' : reading reference level from instrument')
        return float(self._visainstrument.ask('DISP:TRAC:Y:RLEV?'))

    def do_set_reference_level(self, reference_level):
        '''
        Set reference level of device

        Input:
            reference_level (float) : reference level in dBm(??)

        Output:
            None
        '''
        logging.debug(__name__ + 
            ' : setting reference level to {0} dBm'.format(reference_level))
        self._visainstrument.write(
                        'DISP:TRAC:Y:RLEV {0:e}'.format(reference_level))

    def do_get_input_attenuation(self):
        '''
        Get the input attenuation level
        '''
        return float(self._visainstrument.ask('INP:ATT?'))

    def do_get_input_impedance(self):
        '''
        Get the input impedance setting. The setting of 75 Ohm should only
        be used when a 25 Ohm resistor is placed in series with the input.
        '''
        return int(self._visainstrument.ask('INP:IMP?'))

    def do_get_preamp_status(self):
        '''
        Get the status of the preamp. The preamp adds 20 dB of amplification.
        
        Input:
            None
        
        Output:
            True:   preamp is on
            False:  preamp is off
        '''
        status = self._visainstrument.ask('INP:GAIN:STAT?')
        if status == '1':
            return True
        elif status == '0':
            return False
        else:
            logging.error(
                'Incorrect response to INP:GAIN:STAT? : {0}'.format(status))

    def do_get_sweep_time(self):
        '''
        Get sweep time level from device

        Input:
            None

        Output:
            sweep_time (float) : sweep time in s
        '''
        logging.debug(__name__ + ' : reading sweep time from instrument')
        return float(self._visainstrument.ask('SWE:TIME?'))

    def do_set_sweep_time(self, sweep_time):
        '''
        Set sweep time of device

        Input:
            sweep_time (float) : sweep time in s

        Output:
            None
        '''
        logging.debug(__name__ + 
                    ' : setting sweep time to {0} s'.format(sweep_time))
        self._visainstrument.write('SWE:TIME {0:e}'.format(sweep_time))

    def do_get_sweep_points(self):
        '''
        Get the number of points in a sweep
        '''
        logging.debug(__name__ + ' : getting the number of sweep points.')
        return int(self._visainstrument.ask('SWE:POIN?'))

    def do_set_sweep_points(self, sweep_points):
        '''
        Set the number of points in a sweep
        '''
        logging.debug(__name__ + 
            ' : setting the number of points in a sweep to {0:d}'.format(
                    sweep_points))
        self._visainstrument.write('SWE:POIN {0:d}'.format(sweep_points))

    def do_get_reference_oscillator(self):
        '''
        Get the reference oscillator

        Input: 
            None
        
        Output:
            internal
            external
        '''
        logging.debug(__name__ + 
                    ' : Getting the reference oscillator')
        return self._visainstrument.ask('ROSC:SOUR?')

    def do_set_reference_oscillator(self, reference):
        '''
        Set the reference oscillator
    
        Input:
            INT
            EXT

        Output:
            None
        '''
        logging.debug(__name__ + 
            ' Setting the reference oscillator to {0}'.format(reference))
        if reference == 'INT':
            self._visainstrument.write('ROSC:SOUR INT')
        elif reference == 'EXT':
            self._visainstrument.write('ROSC:SOUR EXT')

    def do_get_measurement_mode(self):
        '''
        Get the measurement mode. Without options the only mode is spectrum 
        analyser
        '''
        logging.debug(__name__ + ' : getting the measurement mode.')
        return self._visainstrument.ask('INST?')

    def do_get_trace_mode(self):
        '''
        Get the trace mode.
        '''
        logging.debug(__name__ + ' : getting the trace mode.')
        return self._visainstrument.ask('DISP:TRAC:MODE?')

    def do_set_trace_mode(self, trace_mode):
        '''
        Set the trace mode.
        '''
        logging.debug(__name__ + 
                ' : setting the trace mode to {0}.'.format(trace_mode))
        self._visainstrument.write('DISP:TRAC:MODE {0}'.format(trace_mode))

    def do_get_detector_mode(self):
        '''
        Get the detector mode.
        '''
        logging.debug(__name__ + ' : getting the detector mode.')
        return self._visainstrument.ask('DET?')

    def do_set_detector_mode(self, detector_mode):
        '''
        Set the detector mode.
        '''
        logging.debug(__name__ + 
                ' : setting the detector mode to {0}.'.format(detector_mode))
        self._visainstrument.write('DET {0}'.format(detector_mode))

    def initialize_measurement(self, wait=True):
        '''
        Initialize a measurement
        '''
        if wait:
            self._visainstrument.write('INIT;*WAI')
        else:
            self._visainstrument.write('INIT')

    def get_error_message(self):
        '''
        Queries the earliest error queue entry and deletes it
        '''
        return self._visainstrument.ask('SYST:ERR?')

##############################

    def do_get_IQresult(self):
        '''
        Get IQresult level from device in I/Q mode

        Input:
            None

        Output:
            IQresult (string) : either REAL,32 or ASCII, depending on choice 
                                in init_IQ_measurement
        '''
        logging.debug(__name__ + 
                ' : reading result of I/Q measurement from instrument')
        #self._visainstrument.write('INIT,*WAI')        
        #self._visainstrument.write('*CLS')
        self._visainstrument.write('INIT') 
        return self._visainstrument.ask('TRAC:IQ:DATA?')
        #self._visainstrument.write('INIT,*WAI')        
        #return self._visainstrument.ask('TRAC:IQ:DATA:MEM? 0,4096')

    def do_get_IQ_sample_rate(self):
        '''
        Get the sample rate for the IQ demodulation
        '''
        logging.debug(__name__ + ' : reading the IQ measurement sample rate.')
        return self._visainstrument.ask('TRAC:IQ:SRAT?')

    def do_get_IQ_samples(self):
        '''
        Get the number of samples for the IQ demodulation
        '''
        logging.debug(__name__ + 
            ' : reading the number of IQ measurement samples')
        settings = self._visainstrument.ask('TRAC:IQ:SET?').split(',')
        return int(settings[-1])

    def do_get_IQ_pretrigger_samples(self):
        '''
        Get the number of pretrigger samples for the IQ demodulation
        '''
        logging.debug(__name__ + 
            ' : reading the number of IQ measurement pretrigger samples')
        settings = self._visainstrument.ask('TRAC:IQ:SET?').split(',')
        return int(settings[-2])

    def get_trace_data(self, trace_number=1):
        '''
        read out trace data from device

        Input:
            None

        Output:
            trace_data (numpy array)
        '''
        logging.debug(__name__ + 
                    ' : reading result of I/Q measurement from instrument')
#        self._visainstrument.write('INIT,*WAI')
        self._visainstrument.write(
                'TRAC?  TRACE{0:d}'.format(trace_number))
        trace = self._visainstrument.read_raw() # header + data + termination
        trace_start = 2 + int(trace[1]) # second character is header length
        return frombuffer(trace[trace_start:-1], dtype=float32)

    def do_get_channel_power(self):
        '''
        Get channel power from device (in MEAS. menu on front panel of the RS-FSL6, 
        command CP/ACP/MC-ACP)
        
        In measurement, call self.init_power_measurement() before reading channelpower!

        Documentation for remote control command in 'Operating manual', p. 821

        Input:
            None

        Output:
            channel_power (float) : channel power in ??unit
        '''
        logging.debug(__name__ + ' : reading channel_power from instrument')
        self._visainstrument.write('*WAI') # Starts a sweep and waits for 
                                           # the end of the sweep.
        return float(self._visainstrument.ask('CALC:MARK:FUNC:POW:RES? ACP'))

    def do_get_timetracemarkerpower(self):
        '''
        Get marker power from device in zero span mode
        
        In measurement, call init_zero_span() before reading mean power!

	    Documentation for remote control command in 'Operating manual', p. 1609

        Input:
            None

        Output:
            timetracemarkerpower (float) : marker power in V!! (even if display shows dBuV)
        '''
        logging.debug(__name__ + 
                ' : reading marker power in zero span mode from instrument')
        self._visainstrument.write('INIT;*WAI') # Starts a sweep and waits for 
                                                # the end of the sweep.
        return float(self._visainstrument.ask('CALC:MARK:FUNC:SUMM:PPE:RES?'))

