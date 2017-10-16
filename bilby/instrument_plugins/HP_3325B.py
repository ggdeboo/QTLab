#  -*- coding: utf-8 -*-
# HP_3325B.py class, to perform the communication between the Wrapper and the device
# Gabriele de Boo <ggdeboo@gmail.com> 2014
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
from time import sleep

rm = visa.ResourceManager()

class HP_3325B(Instrument):
    '''
    This is the python driver for the HP 3325B
    synthesizer

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_3325B', address='<GPIB address>',
        reset=<bool>)
    '''

    def __init__(self, name, address, reset=False, baud_rate=4800):
        '''
        Initializes the HP_3325B, and communicates with the wrapper.
        Our model doesn't have the high voltage option so I didn't add the use 
        of that option in this wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = rm.open_resource(self._address)
        self._visainstrument.baud_rate = baud_rate
        self._visainstrument.write_termination = '\n'
        self._visainstrument.read_termination = '\r\n'
        self._visainstrument.clear()
        self._idn = self._visainstrument.query('*IDN?')
        self._serial_number = self._idn.split(',')[2]
        self._visainstrument.write('HEAD 1') # make sure the instrument sends
                                             # a head back after a command.
        # Query the options
        options = self._visainstrument.query('OPT?')
        self._instrument_options = []
        if options.lstrip('OPT')[0] == '1':
            self._instrument_options.append('oven')
        if options.lstrip('OPT')[2] == '1':
            self._instrument_options.append('high voltage')

        self.add_parameter('frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=0.0, maxval=60.999999e6,
                units='Hz')
        self.add_parameter('amplitude',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=0.001, maxval=40.0,
                units='V')
        self.add_parameter('phase',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=-720,maxval=+720,units='degree')
        self.add_parameter('offset',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=-5.0, maxval=5.0,
                units='V')
        self.add_parameter('connected_output',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=['front','rear'])
        self.add_parameter('output_function',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=[   'DC',
                                'sine',
                                'square',
                                'triangle',
                                'positive ramp',
                                'negative ramp'])
        self.add_parameter('amplitude_modulation_status',
                type=types.BooleanType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('status_byte',
                type=types.IntType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('enhancements_mode',
                type=types.BooleanType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('locked_to_external_reference',
                type=types.BooleanType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('modulation_source_amplitude',
                type=types.FloatType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('modulation_source_frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                minval=0, maxval=10000.0,
                units='Hz')
        self.add_parameter('modulation_source_waveform',
                type=types.StringType,
                flags=Instrument.FLAG_GET,
                option_list=['off','sine','square','arbitrary'])
        self.add_parameter('phase_modulation_status',
                type=types.BooleanType,
                flags=Instrument.FLAG_GET)
        # sweep parameters
        self.add_parameter('sweep_mode',
                type=types.StringType,
                flags=Instrument.FLAG_GET,
                option_list=['linear','logarithmic','discrete'])
        self.add_parameter('sweep_start_frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                minval=0.0, maxval=20999999.999,
                units='Hz')
        self.add_parameter('sweep_stop_frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                minval=0.0, maxval=20999999.999,
                units='Hz')
        self.add_parameter('sweep_time',
                type=types.FloatType,
                flags=Instrument.FLAG_GET,
                minval=0.0, maxval=1000.,
                units='s')
        self.add_parameter('error',
                type=types.StringType,
                flags=Instrument.FLAG_GET)

        self.add_function('reset')
        self.add_function('get_all')
 
        if reset:
            self.reset()
        else:
            self.get_all()
        print('HP 3325B with serial number %s has been initialized.' %
                self._serial_number)
        if len(self._instrument_options) > 0:
            print('Options installed: %s' % self._instrument_options) 
        else:
            print('No options installed.')

    def get_all(self):
        self.get_frequency()
        self.get_connected_output()
        self.get_amplitude()
        self.get_offset()
        self.get_phase()
        self.get_output_function()
        self.get_amplitude_modulation_status()
        self.get_status_byte()
        self.get_enhancements_mode()
        self.get_locked_to_external_reference()
        self.get_modulation_source_amplitude()
        self.get_modulation_source_frequency()
        self.get_modulation_source_waveform()
        self.get_phase_modulation_status()
        self.get_sweep_mode()
        self.get_sweep_start_frequency()
        self.get_sweep_stop_frequency()
        self.get_sweep_time()
        self.get_error()

    def reset(self):
        '''
        Reset state according to manual:
        Function                    Sine
        Frequency                   1000.0 Hz
        Amplitude                   1.0 mVpp
        Offset                      0.0 V
        Phase                       0.0 °
        Mod Source Function         Off
        Mod Source Frequency        1000.0 Hz
        Mod Source Amplitude        0.1 Vpp
        Start Frequency             1.0 MHz
        Stop Frequency              10.0 MHz
        Marker Frequency            5 MHz
        Sweep Time                  1.0 Sec
        High voltage                Off
        Front/Rear output           Front
        Amplitude Modulation        Off
        Phase Modulation            Off
        Sweep Mode                  Linear
        Status Byte (bits cleared)  0, 1, 2, 3 & 6
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        sleep(0.1)
        self.get_all()

# Parameters

    def do_set_frequency(self, freq):
        '''
        Sets the frequency. Uses Hz.
        '''
        logging.debug(__name__ + ' : Setting frequency')
        self._visainstrument.write('FR%8.3fHZ' % freq)

    def do_get_frequency(self):
        logging.debug(__name__ + ' : Getting frequency')
        response = self._visainstrument.query('IFR')
        if response.startswith('FR'):
            response = response.lstrip('FR')
            if response[-2:] == 'HZ':
                freq = response[2:-2]
            elif response[-2:] == 'KH':
                freq = response[2:-2]*1e3
            elif response[-2:] == 'MH':
                freq = response[2:-2]*1e6
            else:
                logging.warning(__name__ + ' : Response incorrect.')
                return False
            return float(freq)
        else:
                logging.warning(__name__ + 
                                ' get_frequency : Response incorrect: %s' 
                                % response)

    def do_set_amplitude(self, amp):
        '''Set the output amplitude in Vpp'''
        logging.debug(__name__ + ' : Setting amplitude')
        self._visainstrument.write('AM%5.6fVO' % amp)

    def do_get_amplitude(self):
        '''
        Gets the amplitude in V.
        '''
        logging.debug(__name__ + ' : Getting amplitude')
        response = self._visainstrument.query('IAM')
        if not response.startswith('AM'):
            logging.warning(__name__ + ' get_amplitude : Wrong response: %s' % response)
            raise ValueError('Response from instrument was wrong.')
        amp = response[2:-2]
        if response[-2:] == 'VO':
            return amp
        elif response[-2:] == 'MV':
            return amp*1000
#        elif response[-2:] == 'DB':
#        elif response[-2:] == 'DV':

    def do_set_offset(self, amp):
        logging.debug(__name__ + ' : Setting amplitude')
        self._visainstrument.write('OF%5.6fVO' % amp)

    def do_get_offset(self):
        '''
        Gets the amplitude in V.
        '''
        logging.debug(__name__ + ' : Getting amplitude')
        response = self._visainstrument.query('IOF')
        if not response.startswith('OF'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        amp = response[2:-2]
        if response[-2:] == 'VO':
            return amp
        elif response[-2:] == 'MV':
            return amp*1000

    def do_get_phase(self):
        '''Get the phase of the output signal.'''
        response = self._visainstrument.query('PH?')
        if response.startswith('PH'):
            phase = float(response.lstrip('PH').rstrip('DE'))
            return phase
        else:
            logging.warning(__name__ + ' get_phase : Wrong response: %s'
                            % response)

    def do_set_phase(self, phase):
        '''Set the phase of the output signal.'''
        self._visainstrument.write('PH %.3f' % phase)

    def do_get_connected_output(self):
        logging.debug(__name__ + ' : Getting which output is connected.')
        response = self._visainstrument.query('IRF')
        if response == 'RF1':
            return 'front'
        elif response == 'RF2':
            return 'rear'
        else:
            logging.warning(__name__ + ' get_connected_output : Response incorrect.')
            return False

    def do_set_connected_output(self, output):
        '''
        Options are 'front' and 'rear'.
        '''
        logging.debug(__name__ + ' : Setting the connected output to %s.' 
                        % output)
        if output == 'FRONT':
            self._visainstrument.write('RF1')
        else:
            self._visainstrument.write('RF2')

    def do_get_output_function(self):
        '''
        Get the current waveform function of the instrument.
        options are:
            'DC'
            'sine'
            'square'
            'triangle'
            'positive ramp'
            'negative ramp'
        '''
        logging.debug(__name__ + ' : Getting the waveform function.')
        response = self._visainstrument.query('IFU')
        if not response.startswith('FU'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        if response[2] == '0':
            return 'DC'
        elif response[2] == '1':
            return 'sine'
        elif response[2] == '2':
            return 'square'
        elif response[2] == '3':
            return 'triangle'
        elif response[2] == '4':
            return 'positive ramp'
        elif response[2] == '5':
            return 'negative ramp'

    def do_set_output_function(self, function):
        '''
        Set the current waveform function of the instrument.
        options are:
            'DC'
            'sine'
            'square'
            'triangle'
            'positive ramp'
            'negative ramp'
        '''
        logging.debug(__name__ + ' : Setting the waveform function to %s.' 
                      % function)
        if function == 'DC':
            self._visainstrument.write('FU0')
        if function == 'SINE':
            self._visainstrument.write('FU1')
        if function == 'SQUARE':
            self._visainstrument.write('FU2')
        if function == 'TRIANGLE':
            self._visainstrument.write('FU3')
        if function == 'POSITIVE RAMP':
            self._visainstrument.write('FU4')
        if function == 'NEGATIVE RAMP':
            self._visainstrument.write('FU5')

    def do_get_amplitude_modulation_status(self):
        '''
        Get the amplitude modulation status.
        Returns True or False
        '''
        logging.debug(__name__ + ' : Getting the amplitude modulation status.')
        response = self._visainstrument.query('IMA')
        if not response.startswith('MA'):
            logging.warning(__name__ + ' : Wrong response.')
            raise ValueError('Response from instrument was wrong.')
        if response[2] == '0':
            return False
        if response[2] == '1':
            return True

    def do_get_status_byte(self):
        '''Get the value of the status byte.

        Bit Value   Name    Description
        0   1       ERR     Program or keyboard entry error
        1   2       STOP    Sweep stopped
        2   4       START   Sweep started
        3   8       FAIL    Hardware failure
        4   16      BIT4    Always zero
        5   32      SWEEP   Sweep in progress
        6   64      RQS     This corresponds to the HP-IB SRQ signal
        7   128     BUSY    Set while a command is being executed
        '''
        response = self._visainstrument.query('QSTB?')
        if response.startswith('QSTB'):
            return int(response.lstrip('QSTB'))
        else:
            logging.warning(__name__ + ' get_status_byte : Wrong response %s'
            % response)

    def do_get_enhancements_mode(self):
        '''Get whether the instrument is in enhancements mode''' 
        response = self._visainstrument.query('ENH?')
        if response.startswith('ENH'):
            if response.lstrip('ENH') == '1':
                return True
            else:
                return False
        else:
            logging.warning(__name__+ 
                    ' get_enhancements_mode : Wrong response %s' % response)

    def do_get_locked_to_external_reference(self):
        '''Get whether the oscillator is locked to an external input'''
        response = self._visainstrument.query('EXTR?')
        if response.startswith('EXTR'):
            if response.lstrip('EXTR') == '1':
                return True
            else:
                return False
        else:
            logging.warning(__name__+ 
                    ' get_locked_to_external_reference : Wrong response %s' 
                    % response)

    def do_get_modulation_source_amplitude(self):
        '''Get the amplitude of the modulation source'''
        response = self._visainstrument.query('MOAM?')
        value = response.lstrip('MOAM')[:-2]
        units = response[-2:]
#        if units == 'VO':
        return float(value)

    def do_get_modulation_source_frequency(self):
        '''Get the frequency of the modulation source'''
        response = self._visainstrument.query('MOFR?')
        if response.startswith('MOFR'):
            value = float(response.lstrip('MOFR').rstrip('HZ'))
            return value
        else:
            logging.warning(__name__+ 
                    ' get_modulation_source_frequency : Wrong response %s' 
                    % response)

    def do_get_modulation_source_waveform(self):
        '''Get the waveform function of the modulation source'''
        response = self._visainstrument.query('MOFU?')
        if response.startswith('MOFU'):
            value = response.lstrip('MOFU')
            if value == '0':
                return 'off'
            elif value == '1':
                return 'sine'
            elif value == '2':
                return 'square'
            elif value == '3':
                return 'arbitrary'
            else:
                logging.warning(__name__ +
                ' get_modulation_source_waveform : Wrong response %s'
                % response)
        else:
            logging.warning(__name__ +
            ' get_modulation_source_waveform : Wrong response %s'
            % response)

    def do_get_phase_modulation_status(self):
        '''Get whether the phase modulation is enabled or not.'''
        response = self._visainstrument.query('MP?')
        if response.startswith('MP'):
            if response.lstrip('MP') == '0':
                return False
            elif response.rstrip('MP') == '1':
                return True
        logging.warning(__name__ +
                        ' get_modulation_source_waveform : Wrong response %s'
                        % response)

    def do_get_sweep_mode(self):
        '''Get the sweep mode of the signal generator'''
        response = self._visainstrument.query('SM?')
        if response == 'SM1':
            return 'linear'
        elif response == 'SM2':
            return 'logarithmic'
        elif response == 'SM3':
            return 'discrete'
        else:
            logging.warning(__name__ + 
                            ' get_sweep_mode : Wrong response %s'
                            % response)

    def do_get_sweep_start_frequency(self):
        '''Get the frequency at which the sweep starts'''
        response = self._visainstrument.query('ST?')
        if response.startswith('ST'):
            return float(response.lstrip('ST').rstrip('HZ'))
        else:
            logging.warning(__name__ + 
                            ' get_sweep_start_frequency : Wrong response %s'
                            % response)
            
    def do_get_sweep_stop_frequency(self):
        '''Get the frequency at which the sweep stops'''
        response = self._visainstrument.query('SP?')
        if response.startswith('SP'):
            return float(response.lstrip('SP').rstrip('HZ'))
        else:
            logging.warning(__name__ + 
                            ' get_sweep_stop_frequency : Wrong response %s'
                            % response)

    def do_get_sweep_time(self):
        '''Get the sweep time'''
        response = self._visainstrument.query('TI?')
        if response.startswith('TI'):
            return float(response.lstrip('TI').rstrip('SE'))
        else:
            logging.warning(__name__ + 
                            ' get_sweep_time : Wrong response %s'
                            % response)
        
    def do_get_error(self):
        error_dict = {  'ERR000' : 'no error',
            'FAIL010': 'Hardware failure, DAC range',
            'FAIL011': 'Bad checksum, low byte of ROM',
            'FAIL012': 'Bad checksum, high byte of ROM',
            'FAIL013': 'Machine data bus line stuck low',
            'FAIL014': 'Keyboard shift register test failed',
            'FAIL021': 'Signal too big during calibration',
            'FAIL022': 'Signal too small during calibration',
            'FAIL023': 'DC offset too positive during cal',
            'FAIL024': 'DC offset too negative during cal',
            'FAIL025': 'Unstable/ noisy calibration',
            'FAIL026': 'Calibration factor out of range: AC gain offset',
            'FAIL027': 'Calibration factor out of range: AC gain slope',
            'FAIL028': 'Calibration factor out of range: DC offset',
            'FAIL029': 'Calibration factor out of range: DC slope',
            'FAIL030': 'External ref unlocked',
            'FAIL031': 'Oscillator unlocked, VCO voltage too low',
            'FAIL032': 'Oscillator unlocked, VCO voltage too high',
            'FAIL033': 'HP-IB isolation circuits test failed self test',
            'FAIL034': 'HP-IB IC failed self test',
            'FAIL035': 'RS-232 test failed loop-back test',
            'FAIL036': 'Memory lost (battery dead)',
            'FAIL037': 'Unexpected interrupt',
            'FAIL038': 'Sweep-limit-flag signal failed self test',
            'FAIL039': 'Fractional-N IC failed self test',
            'FAIL040': 'Modulation Source failed self test',
            'FAIL041': 'Function-integrity-flag flip-flop always set',
            'ERR100' : 'Entry parameter out of bounds',
            'ERR200' : 'Invalid units suffix for entry',
            'ERR201' : 'Invalid units suffix with high voltage',
            'ERR300' : 'Frequency too large for function',
            'ERR400' : 'Sweep time too large (same as sweep rate too small)',
            'ERR500' : 'Amplitude/offset incompatible',
            'ERR501' : 'Offset too big for amplitude',
            'ERR502' : 'Amplitude too big for offset',
            'ERR503' : 'Amplitude too small',
            'ERR600' : 'Sweep frequency improper',
            'ERR601' : 'Sweep frequency too large for function',
            'ERR602' : 'Sweep bandwidth too small',
            'ERR603' : 'Log sweep start freq too small',
            'ERR604' : 'Log sweep stop frequency less than start frequency',
            'ERR605' : 'Discrete sweep element is empty',
            'ERR700' : 'Unknown command',
            'ERR701' : 'Illegal query',
            'ERR751' : 'Key ignored - in remote (press LOCAL)*',
            'ERR752' : 'Key ignored - local lockout*',
            'ERR753' : 'Feature disabled in compatibility mode',
            'ERR754' : ('Attempt to recall a register that has not been ' + 
                        'stored since power up *'),
            'ERR755' : ('Amplitude modulation not allowed on selected ' + 
                        'function (warning only)*'),
            'ERR756' : 'Modulation source arbitrary waveform is empty',
            'ERR757' : 'Too many modulation source arbitrary waveform points',
            'ERR758' : 'Firmware failure',
            'ERR759' : 'Error while running XRUN routine',
            'ERR800' : 'Illegal character received',
            'ERR801' : 'Illegal digit for selection item',
            'ERR802' : 'Illegal binary data block header',
            'ERR803' : 'Illegal string, string overflow',
            'ERR810' : 'RS-232 overrun - characters lost',
            'ERR811' : 'RS-232 parity error',
            'ERR812' : 'RS-232 frame error',
            'ERR900' : 'Option not installed'
                     }
        response = self._visainstrument.query('ERR?')
        return error_dict.get(response, response)
