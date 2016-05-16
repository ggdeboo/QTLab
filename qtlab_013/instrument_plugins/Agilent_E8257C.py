# Agilent_E8257C.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Gabriele de Boo, 2012,2016
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

class Agilent_E8257C(Instrument):
    '''
    This is the driver for the Agilent E8257C Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Agilent_E8257C', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Agilent_E8257C, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Agilent_E8257D')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.term_chars = '\n'
        self._visainstrument.timeout = 0.5
        self._idn = self._visainstrument.ask('*IDN?')
        
        if not ('E8257C' in self._idn):
            raise Exception('Connected instrument is not an E8257C')

        self._installed_options = self._visainstrument.ask(':DIAG:INFO:OPT?')
        if '520' in self._installed_options:
            logging.info('Instrument frequency range is 250 kHz - 20 GHz')
            self._freq_max = 20e9
        elif '540' in self._installed_options:
            logging.info('Instrument frequency range is 250 kHz - 40 GHz')
            self._freq_max = 40e9
        if '1E1' in self._installed_options:
            logging.info('Instrument has option 1E1 ' + 
                        '(step attenuator) installed.')
            self._1E1 = True
        if '1E6' in self._installed_options:
            logging.info('Instrument has option 1E6 ' + 
                        '(narrow pulse modulation) installed.')
        # power
        self.add_parameter('power',
            flags=Instrument.FLAG_GETSET, 
            units='dBm',
            minval=-135, maxval=24, 
            type=types.FloatType)
        if self._1E1:
            self.add_parameter('ALC_level',
                flags=Instrument.FLAG_GET,
                units='dBm',
                minval=-20, maxval=25,
                type=types.FloatType,
                )
        self.add_parameter('ALC_state',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType,
            )

        # frequency
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET, 
            units='Hz', 
            minval=250e3, maxval=self._freq_max, 
            type=types.FloatType)
        self.add_parameter('frequency_mode',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            option_list=('CW', 'SWEEP', 'LIST'),
            )
        self.add_parameter('reference_oscillator',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            )

        self.add_parameter('status',
            flags=Instrument.FLAG_GETSET, 
            type=types.StringType)
        self.add_parameter('frequency_modulation_rate',
            flags=Instrument.FLAG_GETSET, 
            units='Hz', 
            minval=0.5, maxval=1e6, 
            type=types.FloatType)
        self.add_parameter('frequency_modulation_size',
            flags=Instrument.FLAG_GETSET, 
            units='Hz', 
            minval=0, maxval=8e6, 
            type=types.FloatType)
        self.add_parameter('frequency_modulation_state',
            flags=Instrument.FLAG_GET, 
            type=types.BooleanType)
        self.add_parameter('Frequency_List',
            flags=Instrument.FLAG_SET, 
            type=numpy.ndarray)
        self.add_parameter('Power_List',
            flags=Instrument.FLAG_SET, 
            type=numpy.ndarray)
        self.add_parameter('Dwell_Times_List',
            flags=Instrument.FLAG_SET, 
            type=numpy.ndarray)
        
        # amplitude modulation
        self.add_parameter('amplitude_modulation_state',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType,
            channels=(1,2),
            channel_prefix='path%i_',
            )
        self.add_parameter('amplitude_modulation_source',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            channels=(1,2),
            channel_prefix='path%i_',
            option_list = ('INT1', 'INT2', 'EXT1', 'EXT2'),
            )
#        self.add_parameter('amplitude_modulation_external_coupling',
#            flags=Instrument.FLAG_GET,
#            type=types.StringType,
#            channels=(1,2),
#            channel_prefix='input%i_',
#            option_list=('AC','DC'),
#            )
            

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('FM1_on')
        self.add_function('FM1_off')
        self.add_function('List_sweep_freq_on')
        self.add_function('List_sweep_freq_off')
        self.add_function('List_sweep_power_on')
        self.add_function('List_sweep_power_on')


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
        if self._1E1:
            self.get_ALC_level()
        self.get_ALC_state()
        self.get_frequency()
        self.get_frequency_mode()
        self.get_reference_oscillator()
        self.get_status()
        self.get_path1_amplitude_modulation_state()
        self.get_path2_amplitude_modulation_state()
        self.get_path1_amplitude_modulation_source()
        self.get_path2_amplitude_modulation_source()
#        self.get_input1_amplitude_modulation_external_coupling()
#        self.get_input2_amplitude_modulation_external_coupling()

    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in ?
        '''
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.ask('POW:AMPL?'))

    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in ??

        Output:
            None
        '''
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._visainstrument.write('POW:AMPL %s' % amp)

    def do_get_ALC_level(self):
        '''
        Get the ALC level when attenuator hold is active
        '''
        return float(self._visainstrument.ask(':POW:ALC:LEV?'))

    def do_get_ALC_state(self):
        '''
        Get whether the Automatic Leveling Control is on
        '''
        return bool(int(self._visainstrument.ask(':POW:ALC:STAT?')))

    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.ask('FREQ:CW?'))

    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ:CW %s' % freq)

    def do_get_frequency_mode(self):
        '''
        Get the frequency mode

        Input:
            None
        
        Output:
            CW
            SWEEP
            LIST
        '''
        logging.debug(__name__ + ' : get the frequency mode')
        response = self._visainstrument.ask('FREQ:MODE?')
        return response

    def do_get_reference_oscillator(self):
        return self._visainstrument.ask('ROSC:SOUR?')

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        logging.debug(__name__ + ' : get status')
        stat = self._visainstrument.ask('OUTP?')

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

    def do_get_frequency_modulation_rate(self):
        '''
        Get the size of the frequency modulation of FM channel 1
        '''
        logging.debug(__name__ + ' : get FM1 rate')
        return float(self._visainstrument.ask('FM1:INT:FREQ?'))

    def do_set_frequency_modulation_rate(self, size):
        '''
        Set the size of the frequency modulation of FM channel 1
        '''
        logging.debug(__name__ + ' : set FM1 rate to %s' % size)
        self._visainstrument.write('FM1:INT:FREQ %s' % size)

    def do_get_frequency_modulation_size(self):
        '''
        Get the size of the frequency modulation of FM channel 1
        '''
        logging.debug(__name__ + ' : get FM1 size')
        return float(self._visainstrument.ask('FM1:DEV?'))

    def do_set_frequency_modulation_size(self, size):
        '''
        Set the size of the frequency modulation of FM channel 1
        '''
        logging.debug(__name__ + ' : set FM1 size to %s' % size)
        self._visainstrument.write('FM1:DEV %s' % size)

    def do_get_frequency_modulation_state(self):
        '''
        Get the state of the frequency modulation of FM channel 1
        '''
        logging.debug(__name__ + ' : get FM1 state')
        response = self._visainstrument.ask('FM1:STAT?')
        if response == '0':
            return False
        if response == '1':
            return True

    def do_set_Frequency_List(self, Frequencies):
	Numbers = str(Frequencies[0])
	for Frequency in Frequencies[1:]:
	    Numbers += ','
            Numbers += str(Frequency)
	self._visainstrument.write('LIST:FREQ %s' % Numbers)

    def do_set_Power_List(self, Powers):
        Numbers = str(Powers[0])
        for Power in Powers[1:]:
            Numbers += ','
            Numbers += str(Power)
        self._visainstrument.write('LIST:POW %s' % Numbers)

    def do_set_Dwell_Times_List(self, Times):
        Numbers = str(Times[0])
        for Time in Times[1:]:
            Numbers += ','
            Numbers += str(Time)
        self._visainstrument.write('LIST:DWEL %s' % Numbers)

    def FM1_on(self):
        '''
        Set the state of the frequency modulation of FM channel 1
        '''
        self._visainstrument.write('FM1:STAT ON')

    def FM1_off(self):        
        self._visainstrument.write('FM1:STAT OFF')    

    def List_sweep_freq_on(self):
        self._visainstrument.write('FREQ:MODE LIST')

    def List_sweep_freq_off(self):
        self._visainstrument.write('FREQ:MODE FIX')

    def List_sweep_power_on(self):
        self._visainstrument.write('POW:MODE LIST')

    def List_sweep_power_off(self):
        self._visainstrument.write('POW:MODE FIX')

    def do_get_amplitude_modulation_state(self, channel):
        '''Get whether amplitde modulation is on or off on the chosen path

        returns:
            True    : AM modulation is on
            False   : AM modulation is off
        '''
        logging.debug(__name__ + 'Getting amplitude modulation state')
        response = self._visainstrument.ask('AM{0}:STAT?'.format(channel))
        if response == '0':
            return False
        elif response == '1':
            return True
        else:
            logging.warning('Unrecognized response: {0}'.format(channel))

    def do_get_amplitude_modulation_source(self, channel):
        '''Get the source for the amplitude modulation on the chosen path

        returns:
            INT1
            INT2
            EXT1
            EXT2
        '''
        logging.debug(__name__ + 'Getting amplitude modulation source')
        response = self._visainstrument.ask('AM{0}:SOUR?'.format(channel))
        if response == 'INT':
            response = 'INT1'
        if response == 'EXT':
            response = 'EXT1'
        return response

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

