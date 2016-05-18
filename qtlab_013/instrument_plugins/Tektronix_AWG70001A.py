# Tektronix_AWG70001A.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Sam hile  <samhile@gmail.com>
# Daniel Keith <danielkeith93@gmail.com>, 2016
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
import sys
import visa
import types
import logging
import numpy
from numpy import float32, uint8, zeros
import struct
from scipy import signal
from itertools import izip_longest as zip_longest

class Tektronix_AWG70001A(Instrument):
    '''
    This is the python driver for the Tektronix AWG70001A
    Arbitrary Waveform Generator

    Key performance specifications:
        Sample rates up to 50 GS/s
        -80 dBc spurious free dynamic range
        10 bits vertical resolution
        16 GSample waveform memory

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'Tektronix_AWG70001A', 
        address='<VISA address>', reset=<bool>, numpoints=<int>)

    '''

    def __init__(self, name, address, reset=False, clock=25e9, numpoints=1000):
        '''
        Initializes the AWG700001A

        Input:
            name (string)    : name of the instrument
            address (string) : VISA address
            reset (bool)     : resets to default values, default=false
            numpoints (int)  : sets the number of datapoints

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.term_chars = '\n'

        self._idn = self._visainstrument.ask('*IDN?')
        if not self._idn.startswith('TEKTRONIX,AWG70001A'):
            raise Exception('Connected instrument is not a Tektronix ' + 
                'AWG70001A, but identifies itself as {0}'.format(self._idn))
        self._installed_options = self._visainstrument.ask('*OPT?')
        if '150' in self._installed_options:
            self._max_samplerate = 50e9
        else:
            self._max_samplerate = 25e9

        self._values = {}
        self._values['files'] = {}
        self._clock = clock
        self._numpoints = numpoints

        # Add parameters
        self.add_parameter('mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            format_map = { 'AWG'    :   'arbitrary waveform generator',
                           'FGEN'   :   'function generator'},
            )
        self.add_parameter('waveform', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            )
        self.add_parameter('output', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            )
        self.add_parameter('wlist', type=types.StringType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('trigger_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('trigger_impedance', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=49, maxval=2e3, units='Ohm')
        self.add_parameter('trigger_level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-5, maxval=5, units='V')

        # function generator
        self.add_parameter('function_generator_amplitude',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            units='V')
        self.add_parameter('function_generator_DC',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            units='V')
        self.add_parameter('function_generator_frequency',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            units='Hz')
        self.add_parameter('function_generator_period',
            type=types.FloatType,
            flags=Instrument.FLAG_GET,
            units='s')
        self.add_parameter('function_generator_type',
            type=types.StringType,
            flags=Instrument.FLAG_GET,
            format_map={    'SINE'   :   'sine',
                            'SQU'   :   'square',
                            'TRI'   :   'triangle',
                            'NOIS'  :   'noise',
                            'DC'    :   'DC',
                            'GAUS'  :   'Gaussian',
                            'EXPR'  :   'exponential rise',
                            'EXPD'  :   'exponential decay',
                            'NONE'  :   'none'}
            )

        # AWG
        self.add_parameter('AWG_run_state', type=types.IntType,
            flags=Instrument.FLAG_GET,
            format_map = {  0   :   'AWG has stopped',
                            1   :   'AWG is waiting for trigger',
                            2   :   'AWG is running'},
            )

        # clock
        self.add_parameter('clock_rate', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=1.49e3, maxval=self._max_samplerate, units='Hz')
        self.add_parameter('clock_source', type=types.StringType,
            flags=Instrument.FLAG_GET,
            format_map={'INT'   :   'internal',
                        'EFIX'  :   '10 MHz external reference',
                        'EVAR'  :   'variable external reference',
                        'EXT'   :   'external clock'},
                        )
        self.add_parameter('dac_resolution', type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            format_map = {  8   :   '8 bits + 2 markers',
                            9   :   '9 bits + 1 marker',
                            10  :   '10 bits, no markers'})

        self.add_parameter('numpoints', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=100, maxval=1e9, units='Int')
#        self.add_parameter('filename', type=types.StringType,
#            flags=Instrument.FLAG_SET,
#            )

        # output parameters
        self.add_parameter('amplitude', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=2, units='V'
            )
        self.add_parameter('offset', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-2, maxval=2, units='V', 
            )
        self.add_parameter('marker1_low', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-2, maxval=2, units='V', 
            )
        self.add_parameter('marker1_high', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-2, maxval=2, units='V',
            )
        self.add_parameter('marker2_low', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-2, maxval=2, units='V', 
            )
        self.add_parameter('marker2_high', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-2, maxval=2, units='V', 
            )
        self.add_parameter('status', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            )

        # mode parameters
        self.add_parameter('run_mode', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            option_list=('CONT','TRIG','TCON')
            )

        # Add functions
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('clear_waveforms')
        self.add_function('set_trigger_mode_on')
        self.add_function('square_pulse')
        self.add_function('gaussian_pulse')
        self.add_function('sinc_pulse')
        self.add_function('level_pulse')


        # Make Load/Delete Waveform functions for each channel
#        for ch in range(1,5):
#            self._add_load_waveform_func(ch)
#            self._add_del_loaded_waveform_func(ch)

        if reset:
            self.reset()
        else:
            pass#self.get_all()
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
        self._visainstrument.write('*RST')

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Reading all data from instrument')

        self.get_mode()

        self.get_trigger_mode()
        self.get_trigger_impedance()
        self.get_trigger_level()

        self.get_function_generator_amplitude()
        self.get_function_generator_DC()
        self.get_function_generator_frequency()
        self.get_function_generator_period()
        self.get_function_generator_type()
    
        self.get_numpoints()

        self.get_AWG_run_state()

        self.get_clock_rate()
        self.get_clock_source()
        self.get_dac_resolution()

        self.get('amplitude')
        self.get('offset')
        self.get('marker1_low')
        self.get('marker1_high')
        self.get('marker2_low')
        self.get('marker2_high')
        self.get('status')

        self.get_wlist()

        self.get_run_mode()
        self.get_output()

    def clear_waveforms(self):
        '''
        Clears the waveform on both channels.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Clear waveforms from channels')
        self._visainstrument.write('SOUR1:FUNC:USER ""')
        self._visainstrument.write('SOUR2:FUNC:USER ""')
        self._visainstrument.write('SOUR3:FUNC:USER ""')
        self._visainstrument.write('SOUR4:FUNC:USER ""')

    def run(self):
        '''
        Initiates the output of a waveform or a sequence. This is equivalent to pressing
        Run/Delete/Stop button on the front panel. The instrument can be put in the run
        state only when output waveforms are assigned to channels.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Run/Initiate output of a waveform or sequence')
        self._visainstrument.write('AWGC:RUN:IMM')
        while self._visainstrument.ask('*OPC?') == '0':
            qt.msleep(0.01)
        self.get_AWG_run_state()

    def stop(self):
        '''
        Terminates the output of a waveform or a sequence. This is equivalent to pressing
        Run/Delete/Stop button on the front panel.

        Input:
            None

        Output:
            None

        See also: run
        '''
        logging.debug(__name__ + ' : Stop/Terminate output of a waveform or sequence')
        self._visainstrument.write('AWGC:STOP:IMM')
        while self._visainstrument.ask('*OPC?') == '0':
            qt.msleep(0.01)
        self.get_AWG_run_state()

    def do_set_output(self, state):
        '''
        This command sets the output state of the AWG.
        Input:
            state (Boolean) : True (On) or False (Off)

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set output state')
        if state:
            self._visainstrument.write('OUTP%s:STAT ON')
        else:
            self._visainstrument.write('OUTP%s:STAT OFF')

    def do_get_output(self):
        '''
        This command gets the output state of the AWG.
        Input:
            None

        Output:
            state (int) : on (1) or off (0)
        '''
        logging.debug(__name__ + ' : Get the output state')
        return self._visainstrument.ask('OUTP:STAT?')

    def do_set_waveform(self, waveform):
        '''
        This command sets the output waveform from the current waveform
        list when Run Mode is not Sequence.

        Input:
            waveform (str) : the waveform filename as loaded in waveform list. 
                             Start with * if calling for a predefined 
                             waveform.

        Output:
            None
        '''
        logging.debug(__name__ + 
                    ' : Set the output waveform to {0}'.format(waveform))
        self._visainstrument.write('SOUR:WAV "{0}"'.format(waveform))

    def do_get_mode(self):
        '''Get the mode of the instrument'''
        logging.debug(__name__ + ' : Get the mode of the instrument')
        return self._visainstrument.ask('INST:MODE?')

    def do_set_mode(self, mode):
        '''Set the mode of the instrument'''
        logging.debug(__name__ + ' : Setting the mode to {0}'.format(mode))
        self._visainstrument.write('INST:MODE {0}'.format(mode))

    def do_get_waveform(self):
        '''
        This command returns the output waveform from the current waveform
        list when Run Mode is not Sequence.

        Input:
            None

        Output:
            waveform (str) : the waveform filename as loaded in waveform list
        '''
        logging.debug(__name__ + ' : Get the output waveform')
        return self._visainstrument.ask('SOUR:WAV?')

    def do_get_wlist(self):
        '''
        This command returns the waveform list in an array.
        Input:
            None

        Output:
            wlist (array) : the waveform list in an array.
        '''
        size = int(self._visainstrument.ask('WLIST:SIZE?'))
        wlist = []
        for i in range(1, size + 1):                    # index starts at 1
            wname = self._visainstrument.ask('WLIST:NAME? {0:d}'.format(i))
            wname = wname.replace('"','')
            wlist.append(wname)
        return wlist

    def del_waveform(self, name):
        '''
        This command deletes the waveform from the waveform list.
        Input:
            name (str) : waveform name, as defined in the waveform list

        Output:
            None
        '''
        logging.debug(__name__ + ' : Delete the waveform "%s" from the waveform list' % name)
        self._visainstrument.write('WLIS:WAV:DEL "%s"' % name)

    def del_loaded_waveform(self, name):
        '''
        This command deletes the waveform from the waveform list which was loaded

        Input:
            name (str) : waveform name, as defined in the waveform list

        Output:
            None
        '''
        self.del_waveform(name)

    def del_waveform_all(self):
        '''
        This command deletes all waveforms in the user-defined waveform list.
        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Clear waveform list')
        self._visainstrument.write('WLIS:WAV:DEL ALL')

    def load_waveform(self, filename, drive='Z:', path='\\'):
        '''
        Use this command to directly load a sequence file or a waveform file 

        Input:
            filename (str) : the waveform filename (.wfm, .seq)
            drive (str) : the local drive where the file is located (e.g. 'Z:')
            path (str) : the local path where the file is located (e.g. '\waveforms')

        Output:
            None
        '''
        logging.debug(__name__ + 
            ' : Load waveform file {0}{1}{2}'.format(drive, path, filename))
        self._visainstrument.write(
            'SOUR:FUNC:USER "{0}/{1}","{2}"'.format((path, filename, drive)))

    def _add_load_waveform_func(self):
        '''
        Adds load_ch[n]_waveform functions, based on 
        load_waveform(filename, drive, path).
        '''
        func = lambda filename, drive='Z:', path='\\': self.load_waveform(channel, filename, drive, path)
        setattr(self, 'load_ch%s_waveform' % channel, func)

    def _add_del_loaded_waveform_func(self, channel):
        '''
        Adds load_ch[n]_waveform functions, based on load_waveform(channel, filename, drive, path).
        n = (1,2,3,4) for 4 channels.
        '''
        func = lambda: self.del_loaded_waveform(channel)
        setattr(self, 'del_ch%s_waveform' % channel, func)

    def load_settings(self, filename, drive='Z:', path='\\'):
        '''
        This command sets the AWG's setting from the specified settings file.

        Input:
            filename (str) : the settings filename (.set)
            drive (str) : the settings file drive
            path (str) : the settings file path

        Output:
            None
        '''
        logging.debug(__name__ + ' : Load settings file %s%s%s' % (drive, path, filename))
        self._visainstrument.write('AWGC:SRES "%s","%s"' % (filename, drive))

    def save_settings(self, filename, drive='Z:', path='\\'):
        '''
        This command saves the AWG's current setting to the specified settings file.
        Default path is the Z:\ drive, , which is located at
        "C:\Documents and Settings\All Users\Documents\Waveforms".

        Input:
            filename (str) : the settings file path (.set)
            drive (str) : the settings file drive
            path (str) : the settings file path

        Output:
            None
        '''
        logging.debug(__name__ + ' : Save current settings to file %s' % filename)
        self._visainstrument.write('AWGC:SSAV "%s","%s"' % (filename, drive))

    def do_get_run_mode(self):
        '''
        Get the run mode of the device
        '''
        logging.debug(__name__ + ' : Getting the run mode.')
        return self._visainstrument.ask('SOUR:RMOD?')

    def do_set_run_mode(self, run_mode):
        '''
        Set the Run Mode of the device to Continuous, Triggered, Gated or 
        Sequence.

        Input:
            run_mode (str) : The Run mode which can be set to 'CONT', 'TRIG', 
                            'TCON'

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set run mode to %s' % run_mode)
        self._visainstrument.write('AWGC:RMOD %s' % run_mode.upper())

    def set_sequence_mode_on(self):
        '''
        Sets the sequence mode to 'On'

        Input:
            None

        Output:
            None
        '''
        self.set_runmode('SEQ')

    def set_trigger_mode_on(self):
        '''
        Sets the trigger mode to 'On'

        Input:
            None

        Output:
            None
        '''
        self.set_runmode('TRIG')

    # Parameters
    def do_get_trigger_mode(self):
        '''
        Reads the trigger mode from the instrument

        Input:
            None

        Output:
            mode (string) : 'Trig' or 'Cont' depending on the mode
        '''
        logging.debug(__name__  + ' : Get trigger mode from instrument')
        return self._visainstrument.ask('AWGC:RMOD?')

    def do_set_trigger_mode(self, mod):
        '''
        Sets trigger mode of the instrument

        Input:
            mod (string) : Either 'Trig' or 'Cont' depending on the mode

        Output:
            None
        '''
        if (mod.upper()=='TRIG'):
            self.set_trigger_mode_on()
        elif (mod.upper()=='CONT'):
            self.set_runmode('CONT')
        else:
            logging.error(__name__ + ' : Unable to set trigger mode to %s, expected "TRIG" or "CONT"' % mod)

    def do_get_trigger_impedance(self):
        '''
        Reads the trigger impedance from the instrument

        Input:
            None

        Output:
            impedance (??) : 1e3 or 50 depending on the mode
        '''
        logging.debug(__name__  + ' : Get trigger impedance from instrument')
        return self._visainstrument.ask('TRIG:IMP?')

    def do_set_trigger_impedance(self, mod):
        '''
        Sets the trigger impedance of the instrument

        Input:
            mod (int) : Either 1e3 of 50 depending on the mode

        Output:
            None
        '''
        if (mod==1e3):
            self.set_trigger_impedance_1e3()
        elif (mod==50):
            self.set_trigger_impedance_50()
        else:
            logging.error(__name__ + ' : Unable to set trigger impedance to %s, expected "1e3" or "50"' % mod)

    def do_get_trigger_level(self):
        '''
        Reads the trigger level from the instrument

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__  + ' : Get trigger level from instrument')
        return float(self._visainstrument.ask('TRIG:LEV?'))

    def do_set_trigger_level(self, level):
        '''
        Sets the trigger level of the instrument

        Input:
            level (float) : trigger level in volts
        '''
        logging.debug(__name__  + ' : Trigger level set to %.3f' % level)
        self._visainstrument.write('TRIG:LEV %.3f' % level)

    def do_get_function_generator_amplitude(self):
        return float(self._visainstrument.ask('FGEN:AMPL?'))

    def do_get_function_generator_DC(self):
        return float(self._visainstrument.ask('FGEN:DCL?'))

    def do_get_function_generator_frequency(self):
        return float(self._visainstrument.ask('FGEN:FREQ?'))

    def do_get_function_generator_period(self):
        return float(self._visainstrument.ask('FGEN:PER?'))

    def do_get_function_generator_type(self):
        return self._visainstrument.ask('FGEN:TYPE?')

    def do_get_numpoints(self):
        '''
        Returns the number of datapoints in each wave

        Input:
            None

        Output:
            numpoints (int) : Number of datapoints in each wave
        '''
        return self._numpoints

    def do_set_numpoints(self, numpts):
        '''
        Sets the number of datapoints in each wave.
        This acts on all channels.

        Input:
            numpts (int) : The number of datapoints in each wave

        Output:
            None
        '''
        logging.debug(__name__ + ' : Trying to set numpoints to %s' % numpts)
        if numpts != self._numpoints:
            logging.warning(__name__ + ' : changing numpoints. This will clear all waveforms!')

        response = raw_input('type "yes" to continue')
        if response is 'yes':
            logging.debug(__name__ + ' : Setting numpoints to %s' % numpts)
            self._numpoints = numpts
            self.clear_waveforms()
        else:
            print 'aborted'

    def do_get_AWG_run_state(self):
        return self._visainstrument.ask('AWGC:RST?')

    def do_get_clock_rate(self):
        '''
        Returns the clock frequency, which is the rate at which the datapoints are
        sent to the designated output

        Input:
            None

        Output:
            clock (int) : frequency in Hz
        '''
        if self.get_clock_source() == 'EXT':
            logging.warning('Clock source is external, command not valid.')
        else:
            return self._visainstrument.ask('CLOCK:SRAT?')

    def do_set_clock_rate(self, clock):
        '''
        Sets the rate at which the datapoints are sent to the designated output channel

        Input:
            clock (int) : frequency in Hz

        Output:
            None
        '''
        #logging.warning(__name__ + ' : Clock set to %s. This is not fully functional yet. To avoid problems, it is better not to change the clock during operation' % clock)
        self._clock = clock
        self._visainstrument.write('CLOCK:SRAT {0:E}'.format(clock))

    def do_get_clock_source(self):
        '''Get the source for the clock'''
        logging.debug(__name__ + ' : Getting the clock source.')
        return self._visainstrument.ask('CLOCK:SOUR?')

    def do_get_dac_resolution(self):
        '''Get the resolution of the DAC'''
        logging.debug(__name__ + ' : Getting the DAC resolution.')
        return self._visainstrument.ask('SOUR:DAC:RES?')

    def do_set_dac_resolution(self, resolution):
        '''Set the resolution of the DAC'''
        logging.debug(__name__ + 
                ' : Setting the DAC resolution to {0}'.format(resolution))
        self._visainstrument.write('SOUR:DAC:RES {0}'.format(resolution))

    def do_set_filename(self, name, channel):#???
        '''
        Specifies which file has to be set on which channel
        Make sure the file exists, and the numpoints and clock of the file
        matches the instrument settings.

        If file doesn't exist an error is raised, if the numpoints doesn't match
        the command is neglected

        Input:
            name (string) : filename of uploaded file
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__  + ' : Try to set %s on channel %s' % (name, channel))
        exists = False
        if name in self._values['files']:
            exists= True
            logging.debug(__name__  + ' : File exists in local memory')
            self._values['recent_channel_%s' % channel] = self._values['files'][name]
            self._values['recent_channel_%s' % channel]['filename'] = name
        else:
            logging.debug(__name__  + ' : File does not exist in memory, \
            reading from instrument')
            lijst = self._visainstrument.ask('MMEM:CAT? "MAIN"')
            bool = False
            bestand=""
            for i in range(len(lijst)):
                if (lijst[i]=='"'):
                    bool=True
                elif (lijst[i]==','):
                    bool=False
                    if (bestand==name): exists=True
                    bestand=""
                elif bool:
                    bestand = bestand + lijst[i]
        if exists:
            data = self._visainstrument.ask('MMEM:DATA? "%s"' % name)
            logging.debug(__name__  + ' : File exists on instrument, loading \
            into local memory')
            # string alsvolgt opgebouwd: '#' <lenlen1> <len> 'MAGIC 1000\r\n' '#' <len waveform> 'CLOCK ' <clockvalue>
            len1=int(data[1])
            len2=int(data[2:2+len1])
            i=len1
            tekst = ""
            while (tekst!='#'):
                tekst=data[i]
                i=i+1
            len3=int(data[i])
            len4=int(data[i+1:i+1+len3])

            w=[]
            m1=[]
            m2=[]

            for q in range(i+1+len3, i+1+len3+len4,5):
                j=int(q)
                c,d = struct.unpack('<fB', data[j:5+j])
                w.append(c)
                m2.append(int(d/2))
                m1.append(d-2*int(d/2))

            clock = float(data[i+1+len3+len4+5:len(data)])

            self._values['files'][name]={}
            self._values['files'][name]['w']=w
            self._values['files'][name]['m1']=m1
            self._values['files'][name]['m2']=m2
            self._values['files'][name]['clock']=clock
            self._values['files'][name]['numpoints']=len(w)

            self._values['recent_channel_%s' % channel] = self._values['files'][name]
            self._values['recent_channel_%s' % channel]['filename'] = name
        else:
            logging.error(__name__  + ' : Invalid filename specified %s' % name)

        if (self._numpoints==self._values['files'][name]['numpoints']):
            logging.debug(__name__  + ' : Set file %s on channel %s' % (name, channel))
            self._visainstrument.write('SOUR%s:FUNC:USER "%s","MAIN"' % (channel, name))
        else:
            logging.warning(__name__  + ' : Verkeerde lengte %s ipv %s'
                % (self._values['files'][name]['numpoints'], self._numpoints))

    def do_get_amplitude(self):
        '''
        Reads the amplitude of the designated channel from the instrument

        Input:
            None

        Output:
            amplitude (float) : the amplitude of the signal in Volts
        '''
        logging.debug(__name__ + ' : Get amplitude from instrument')
        return float(self._visainstrument.ask('SOUR:VOLT:LEV:IMM:AMPL?'))

    def do_set_amplitude(self, amp):
        '''
        Sets the amplitude of the instrument

        Input:
            amp (float)   : amplitude in Volts

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set amplitude to {0:.6f}'.format(amp))
        self._visainstrument.write('SOUR:VOLT:LEV:IMM:AMPL {0:.6f}'.format(amp))

    def do_get_offset(self):
        '''
        Reads the offset of the instrument

        Input:

        Output:
            offset (float) : offset in Volts
        '''
        logging.debug(__name__ + ' : Get offset')
        return float(self._visainstrument.ask('SOUR:VOLT:LEV:IMM:OFFS?').strip('"'))

    def do_set_offset(self, offset):
        '''
        Sets the offset of the instrument

        Input:
            offset (float) : offset in Volts

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set offset to {0:.6f}'.format(offset))
        self._visainstrument.write('SOUR:VOLT:LEV:IMM:OFFS {0:.6f}'.format(offset))

    def do_get_marker1_low(self):
        '''
        Gets the low level for marker1

        Input:
            None

        Output:
            low (float) : low level in Volts
        '''
        logging.debug(__name__ + ' : Get lower bound of marker1')
        return float(self._visainstrument.ask('SOUR:MARK1:VOLT:LEV:IMM:LOW?'))

    def do_set_marker1_low(self, low):
        '''
        Sets the low level for marker1.

        Input:
            low (float)   : low level in Volts

        Output:
            None
         '''
        logging.debug(__name__ + ' : Set lower bound of marker1 to {0:.3f}'.format(low))
        self._visainstrument.write('SOUR:MARK1:VOLT:LEV:IMM:LOW {0:.3f}'.format(low))

    def do_get_marker1_high(self):
        '''
        Gets the high level for marker1.

        Input:
            None

        Output:
            high (float) : high level in Volts
        '''
        logging.debug(__name__ + ' : Get upper bound of marker1 of channel')
        return float(self._visainstrument.ask('SOUR:MARK1:VOLT:LEV:IMM:HIGH?'))

    def do_set_marker1_high(self, high):
        '''
        Sets the high level for marker1.

        Input:
            high (float)   : high level in Volts

        Output:
            None
         '''
        logging.debug(__name__ + ' : Set upper bound of marker1 to {0:.3f}'.format( high))
        self._visainstrument.write('SOUR:MARK1:VOLT:LEV:IMM:HIGH {0:.3f}'.format(high))

    def do_get_marker2_low(self):
        '''
        Gets the low level for marker2.

        Input:
            None

        Output:
            low (float) : low level in Volts
        '''
        logging.debug(__name__ + ' : Get lower bound of marker2')
        return float(self._visainstrument.ask('SOUR:MARK2:VOLT:LEV:IMM:LOW?'))

    def do_set_marker2_low(self, low):
        '''
        Sets the low level for marker2.

        Input:
            low (float)   : low level in Volts

        Output:
            None
         '''
        logging.debug(__name__ + ' : Set lower bound of marker2 to {0:.3f}'.format(low))
        self._visainstrument.write('SOUR:MARK2:VOLT:LEV:IMM:LOW {0:.3f}'.format(low))

    def do_get_marker2_high(self):
        '''
        Gets the high level for marker2.

        Input:
            None

        Output:
            high (float) : high level in Volts
        '''
        logging.debug(__name__ + ' : Get upper bound of marker2')
        return float(self._visainstrument.ask('SOUR:MARK2:VOLT:LEV:IMM:HIGH?'))

    def do_set_marker2_high(self, high):
        '''
        Sets the high level for marker2.

        Input:
            high (float)   : high level in Volts

        Output:
            None
         '''
        logging.debug(__name__ + ' : Set upper bound of marker2 to {0:.3f}'.format(high))
        self._visainstrument.write('SOUR:MARK2:VOLT:LEV:IMM:HIGH {0:.3f}'.format(high))

    def do_get_status(self):
        '''
        Gets the status 

        Input:
            None

        Output:
            True or False
        '''
        logging.debug(__name__ + ' : Get status')
        outp = self._visainstrument.ask('OUTP?')
        if (outp==u'0\n'):
            return False
        elif (outp==u'1\n'):
            return True
        else:
            logging.debug(__name__ + ' : Read invalid status from instrument %s' % outp)
            return 'an error occurred while reading status from instrument'

    def do_set_status(self, status):
        '''
        Sets the status.

        Input:
            status (Boolean) : True (On) or False (Off)

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set status to {0}'.format(status))
        if status:
            self._visainstrument.write('OUTP ON')
        else:
            self._visainstrument.write('OUTP OFF')
#        else:
#            logging.debug(__name__ + ' : Try to set status to invalid value %s' % status)
#            print 'Tried to set status to invalid value %s' % status

    #  Ask for string with filenames
    def get_filenames(self):
        logging.debug(__name__ + ' : Read filenames from instrument')
        return self._visainstrument.ask('MMEM:CAT? "MAIN"')

    # Send waveform to the device
    def send_waveform(self,w,mode,wfm_name, m1=None, m2=None, sample_rate=None):
        '''
        Sends a complete waveform. 
        See also: resend_waveform()

        Input:
            w (numpy float32 array numpoints) : waveform
            m1 (bool[numpoints])  : marker1
            m2 (bool[numpoints])  : marker2
            wfm_name (string)    : waveform name
            clock (int)          : frequency (Hz)
            mode (string)        : 'UND' 'REAL' 'I' 'Q'

        Output:
            None 
        '''
        logging.debug(__name__ + ' : Sending waveform %s to instrument' % wfm_name)
        # Check for errors
        dim = len(w)
        w.dtype = float32
        
        if (m1 is not None) or (m2 is not None):
            marker_vector = zeros(len(w), dtype=uint8)
            markers = True
        else:
            markers = False

        if m1 is not None:
            if not((len(w)==len(m1))):
                return 'marker length needs to be the same as waveform length'
            m1.dtype = uint8
            marker_vector += m1 * 128
        if m2 is not None:
            if not((len(w)==len(m2))):
                return 'marker length needs to be the same as waveform length'
            m2.dtype = uint8
            marker_vector += m2 * 64
        
#        if (not((len(w)==len(m1)) and ((len(m1)==len(m2))))):
#            return 'error inappropriate marker length'
        
        self._values['files'][wfm_name]             = {}
        self._values['files'][wfm_name]['w']        = w
        self._values['files'][wfm_name]['m1']       = m1
        self._values['files'][wfm_name]['m2']       = m2
        self._values['files'][wfm_name]['numpoints']=len(w)

        ws = ''
        
        # Delete the old waveform  
        self._visainstrument.write(
            'WLIS:WAV:DEL "{0}"'.format(wfm_name))

        # Create a new waveform with the specified name and size)
        self._visainstrument.write(
            'WLIS:WAV:NEW "{0}", {1}'.format(wfm_name, len(w)))
        self._visainstrument.write(
            'WLIS:WAV:SFOR "{0}", REAL'.format(wfm_name))   
        if sample_rate == None:
            sample_rate = self.get_clock_rate()
        self._visainstrument.write(
            'WLIS:WAV:SRATE "{0}", {1}'.format(wfm_name, sample_rate))    
        
        if mode.upper() == 'REAL':
#            m = m1 + numpy.multiply(m2,2) #2bit nibble
#            for i in range(0,len(w)):
#                ws = ws + struct.pack('<fB', w[i], int(m[i]) ) #pack floats into a bytearray (string)

                # < : LSB little-endian
                # f : float (4byte)
                # B : unsigned char (1byte)
#            self._visainstrument.write('WLIS:WAV:NEW "%s", %d, REAL' %(filename, len(w)))
            start_index = 0
            block_size = 8 * 2**20 # Megabit
            if len(w) > block_size:
                n_blocks = len(w) / block_size
                for i in range(n_blocks):
                    block_data = w[i*block_size:(i+1)*block_size]
                    sys.stdout.write('\rSending block {0} of {1}'.format(
                                                        i+1, n_blocks))
                    self._visainstrument.write_raw(
                        'WLIS:WAV:DATA "{0}", {1}, {2}, #9{3:09d}{4}'.format(
                                                    wfm_name,
                                                    i*block_size,
                                                    block_size,
                                                    block_size*4,
                                                    block_data.tostring())
                                                    )
                    if markers:
                        block_marker = marker_vector[i*block_size:(i+1)*block_size]
                        self._visainstrument.write_raw(
                            'WLIS:WAV:MARK:DATA "{0}", {1}, {2}, #9{3:09d}{4}'.format(
                                                    wfm_name,
                                                    i*block_size,
                                                    last_block_size,
                                                    last_block_size,
                                                    block_marker.tobytes())
                                                    )
                # remainder
                i += 1
                last_block_size = len(w) % block_size
                block_data = w[i*block_size:]
                self._visainstrument.write_raw(
                        'WLIS:WAV:DATA "{0}", {1}, {2}, #9{3:09d}{4}'.format(
                                                    wfm_name,
                                                    i*block_size,
                                                    last_block_size,
                                                    last_block_size*4,
                                                    block_data.tostring())
                                                    )
                if markers:
                    block_marker = marker_vector[i*block_size:]
                    self._visainstrument.write_raw(
                        'WLIS:WAV:MARK:DATA "{0}", {1}, {2}, #9{3:09d}{4}'.format(
                                                    wfm_name,
                                                    i*block_size,
                                                    last_block_size,
                                                    last_block_size,
                                                    block_marker.tobytes())
                                                    )
                
                sys.stdout.write('\rDone!') 
            else:
                self._visainstrument.write_raw(
                'WLIS:WAV:DATA "{0}",{1},{2},#9{3:09d}{4}'.format(
                                                        wfm_name,
                                                        start_index,
                                                        len(w),
                                                        len(w)*4,
                                                        w.tostring())
                                                        )
                if markers:
                    self._visainstrument.write_raw(
                        'WLIS:WAV:MARK:DATA "{0}",{1},{2},#9{3:09d}{4}'.format(
                                                    wfm_name,
                                                    start_index,
                                                    len(w),
                                                    len(w),
                                                    marker_vector.tobytes())
                                                    )
        else:
            logging.error('mode parameter has to be REAL')
        
#        header = 'WLIS:WAV:DATA "%s", 0, %d, #%d%d'%(filename, len(w), len(str(len(ws))), len(ws)) #0 is startposition
#        self._visainstrument.write_raw(header + ws) #encoding with write causes an UnicodeDecodeError

    def fetch_waveform(self,filename):
        '''
        TODOSends a complete waveform. All parameters need to be specified.
        See also: resend_waveform()

        Input:
            w (float[numpoints]) : waveform
            m1 (int[numpoints])  : marker1
            m2 (int[numpoints])  : marker2
            filename (string)    : filename
            clock (int)          : frequency (Hz)

        Output:
            None
        '''

        return self._visainstrument.ask('WLIS:WAV:DATA? "%s"' %(filename))
       
    def square_pulse(self, period, duty_cycle, filename ):
        '''
        Sends a complete square pulse waveform. Starts in low level and then switches to high level pulse.

        Input:
            period (float) : time length of the waveform (s)
            duty_cycle (float)  : duration of the high level pulse as a percentage of the waveform (%)
            filename (string)  : name to save the waveform

        Output:
            None 
        '''
        samp_rate = float( self.do_get_clock_rate() )
        off_period = int( samp_rate * period * ( 1 - ( duty_cycle / 100.0 ) ) )
        on_period = int( samp_rate * period * ( duty_cycle / 100.0 ) )
        
        wave = [-0.5] * off_period + [0.5] * on_period
        marker = [0] * int( period * samp_rate )
        self.send_waveform( wave, marker, marker, 'INT', filename)
    
    def level_pulse(self, level, duration ):
        '''
        Sends a pulse waveform at a constant level.

        Input:
            level (float) : amplitude between -0.5 and 0.5
            duration (float) : time length of the waveform (s)
            filename (string)  : name to save the waveform

        Output:
            wave (list) :  shape of the level pulse 
        '''
        samp_rate = float( self.do_get_clock_rate() )
        period = int( samp_rate * duration )
        
        wave = [level] * period
        # marker = [0] * int( period * samp_rate )
        # self.send_waveform( wave, marker, marker, 'INT', filename)
        return wave
    
    def gaussian_pulse(self, amplitude, duration, stand_dev ):
        '''
        Sends a complete gaussian pulse waveform.

        Input:
            amplitude (float) : between -1 and 1
            duration (float) : time length of the waveform (s)
            stand_dev (float) : standard deviation of the gaussian pulse
            filename (string)  : name to save the waveform

        Output:
            wave (list) :  shape of the gaussian pulse
        '''
        samp_rate = float( self.do_get_clock_rate() )
        num_points = int( duration * samp_rate )
                
        wave = amplitude * signal.gaussian( num_points, stand_dev )
        return wave
     
    def sinc_pulse(self, amplitude, duration, sinc_range ):
        '''
        Sends a complete sinc pulse waveform.

        Input:
            amplitude (float) : between -1 and 1
            duration (float) : time length of the waveform (s)
            sinc_range (float) : range of sinc function to include in waveform
            filename (string)  : name to save the waveform

        Output:
            wave (list) :  shape of the sinc pulse 
        '''
        samp_rate = float( self.do_get_clock_rate() )
        num_points = int( duration * samp_rate )
        wave = amplitude * numpy.sinc( numpy.arange( -sinc_range, sinc_range, 2 * sinc_range / float( num_points ) ) )
        # marker = [0] * num_points
        # self.send_waveform( wave, marker, marker, 'INT', filename)
        return wave
        
    def sequence(self, filename, channel, *args):
        '''
        Compiles a sequence of arbitrary waveforms

        Input:
            *args : a series of lists including the wave function type (GAUSS, SINC, SQUARE, WAIT, LEVEL)
            and its respective parameters
            GAUSS - amplitude, duration and standard deviation. See gauss_pulse
            SINC - amplitude, duration and sinc_range. See sinc_pulse
            SQUARE - duration 
            WAIT - duration
            LEVEL - amplitude and duration. See level_pulse     

        Output:
            wave (list) :  waveform sequence
        '''
        wave_num = len( args )
        wave = []
        amplitudes = [ arg[1] for arg in args ]
        max_amp1 = max(amplitudes)
        min_amp1 = min(amplitudes)
        print max_amp1
        for arg in args:
            if arg[0][:3].upper() not in [ 'GAU','SIN','LEV']:
                return 'error: %s not recognised' % arg[0]
            if arg[0][:3].upper() == 'GAU':
                if len( arg ) != 4:
                    return 'error: expected 3 arguments'
                else:
                    wave = numpy.concatenate((wave, self.gaussian_pulse( arg[1]/max_amp1, arg[2], arg[3] )))
            if arg[0][:3].upper() == 'SIN':
                if len( arg ) != 4:
                    return 'error: expected 3 arguments'
                else:
                    wave = numpy.concatenate((wave, self.sinc_pulse( arg[1]/max_amp1, arg[2], arg[3] )))
            if arg[0][:3].upper() == 'LEV':           
                if len( arg ) != 3:
                    return 'error: expected 2 arguments'
                else:
                    wave = numpy.concatenate((wave, self.level_pulse( arg[1]/max_amp1, arg[2] )))
        
        length = len( wave )        
        marker = [0] * length
        min_amp = min( wave )
        wave = [ point - min_amp for point in wave ]
        max_amp2 = max( wave )
        wave = [ point/max_amp2 - 0.5 for point in wave ]
        
        self.send_waveform( wave, marker, marker, 'INT', filename)    
        self._visainstrument.write('SOUR%s:WAV "%s"' % (channel, filename))  
        voltage = max_amp1*(1-min_amp)        
        offset = (0.5-((min_amp)/(min_amp-1)))*(voltage)
        self._visainstrument.write('SOUR%s:VOLT:OFFS %f' % (channel, offset ))

        self._visainstrument.write('SOUR%s:VOLT %f' % (channel, voltage))

    def get_next_error_message(self):
        return self._visainstrument.ask('SYSTEM:ERROR:NEXT?')

    def get_error_count(self):
        return self._visainstrument.ask('SYSTEM:ERROR:COUNT?')

    def get_all_error_codes(self):
        return self._visainstrument.ask('SYSTEM:ERROR:CODE:ALL?')
