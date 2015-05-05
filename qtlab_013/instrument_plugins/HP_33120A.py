# HP_33120A.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Gabriele de Boo <ggdeboo@gmail.com>, 2015
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
from visa import VisaIOError
import types
import logging
from time import sleep
from qt import msleep

#TODO
#1 put modes/shapes/status as parameter with list of options?
#   burst_state { on, off }
#   trigger_state { cont, external, gpib }
#   function_shape { see below }
#2 put above in get_all()
def get_bit_set(byteval, idx):
    '''Return True if a certain bit is set.'''
    return bool(((byteval&(1<<idx))!=0))

class HP_33120A(Instrument):
    '''
    This is the python driver for the HP 33120A
    arbitrary waveform generator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_33120A', 
                                address='<GPIB address>', reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the HP_33120A, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
#        self._visainstrument.baud_rate = 9600L
        self._visainstrument.term_chars = '\n'
        self._visainstrument.timeout = 2.0
        print('Instrument identification string: %s' 
                % self._visainstrument.ask('*IDN?'))
        event_register = self.get_event_register()
        if event_register > 128:
            print(__name__ + ' : Power has been turned off and on since the'+
                             ' last time the driver was loaded.')

        self.wait_time = 0.3 # if the instrument generates an error, it takes at least 0.3 s for it to finish a query

        self.add_parameter('frequency',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=100e-6, maxval=15e6,
                units='Hz')
        self.add_parameter('amplitude',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=0, maxval=10,
                units='V')
        self.add_parameter('amplitude_units',
                type=types.StringType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('offset',
                type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                minval=-10, maxval=10,
                units='V')
        self.add_parameter('burst_count',
                type=types.IntType,
                flags=Instrument.FLAG_GETSET,
                minval=1, maxval=10000,
                units='#')
        self.add_parameter('burst_status',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=(
                    'on',
                    'off'
                ))
        self.add_parameter('output_function',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=(
                    'sinusoid',
                    'square',
                    'triangle',
                    'ramp',
                    'noise',
                    'DC',
                    'user')
                )
        self.add_parameter('last_error_message',
                type=types.StringType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('trigger_source',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=(
                    'IMM',
                    'EXT',
                    'BUS')
                )
        self.add_parameter('output_termination',
                type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=(
                    'HIGH',
                    'LOW')
                )
        self.add_parameter('selected_arbitrary_waveform',
                type=types.StringType,
                flags=Instrument.FLAG_GET,
                option_list=(
                    'SINC',
                    'NEG_RAMP',
                    'EXP_RISE',
                    'EXP_FALL',
                    'CARDIAC',
                    'VOLATILE')
                )
        self.add_parameter('waveforms_in_memory',
                type=types.ListType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('selected_arbitrary_waveform_length',
                type=types.IntType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('amplitude_modulation_state',
                type=types.BooleanType,
                flags=Instrument.FLAG_GET)
        self.add_parameter('amplitude_modulation_source',
                type=types.StringType,
                flags=Instrument.FLAG_GET,
                option_list=(
                    'BOTH',
                    'EXTERNAL')
                )

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('send_trigger')

        if reset:
            self.reset()
        else:
            self.get_all()

    def get_all(self):
        self.get_frequency()
        self.get_amplitude()
        self.get_amplitude_units()
        self.get_offset()
        self.get_burst_count()
        self.get_output_function()
        self.get_last_error_message()
        self.get_trigger_source()
        self.get_output_termination()
        self.get_selected_arbitrary_waveform()
        self.get_selected_arbitrary_waveform_length()
        self.get_waveforms_in_memory()
        self.get_amplitude_modulation_state()
        self.get_amplitude_modulation_source()

    def reset(self):
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        sleep(0.1)
        self.get_all()

    def get_error(self):
        logging.debug(__name__ + ' : Getting one error from error list')
        return self._visainstrument.ask('SYST:ERR?')

# Trigger

    def set_trigger_continuous(self):
        logging.debug(__name__ + ' : Set trigger to continuous')
        self._visainstrument.write('TRIG:SOUR IMM')
        msleep(self.wait_time)
        return self.check_event_register()

    def set_trigger_external(self):
        logging.debug(__name__ + ' : Set trigger to external')
        self._visainstrument.write('TRIG:SOUR EXT')
        msleep(self.wait_time)
        return self.check_event_register()

    def set_trigger_gpib(self):
        logging.debug(__name__ + ' : Set trigger to gpib')
        self._visainstrument.write('TRIG:SOUR BUS')
        msleep(self.wait_time)
        return self.check_event_register()

    def get_trigger_state(self):
        logging.debug(__name__ + ' : Getting trigger state')
        return self._visainstrument.ask('TRIG:SOUR?')

    def send_trigger(self):
        logging.debug(__name__ + ' : Sending Trigger')
        self._visainstrument.write('*TRG')

# Burst

    def do_set_burst_count(self, cnt):
        logging.debug(__name__ + ' : Setting burst count')
        self._visainstrument.write('BM:NCYC %d' % cnt)
        msleep(self.wait_time)
        return self.check_event_register()

    def do_get_burst_count(self):
        logging.debug(__name__ + ' : Getting burst count')
        return float(self._visainstrument.ask('BM:NCYC?'))

    def do_set_burst_status(self, stat):
        '''
        stat: { ON OFF }
        '''
        logging.debug(__name__ + ' : Setting burst status')
        self._visainstrument.write('BM:STAT %s' % stat)
        msleep(self.wait_time)
        return self.check_event_register()

    def do_get_burst_status(self):
        '''
        stat: { ON OFF }
        '''
        logging.debug(__name__ + ' : Getting burst status')
        return self._visainstrument.ask('BM:STAT?')

# Shape

#    def set_function_shape(self, shape):
#        '''
#        shape : { SIN, SQU, TRI, RAMP, NOIS, DC, USER }
#        '''
#        logging.debug(__name__ + ' : Sending Trigger')
#        self._visainstrument.write('SOUR:FUNC:SHAP %s' % shape)#
#	msleep(self.wait_time)
#	return self.check_event_register()

#    def get_function_shape(self):
#        logging.debug(__name__ + ' : Getting function shape')
#        return self._visainstrument.ask('SOUR:FUNC:SHAP?')

# Parameters

    def do_set_frequency(self, freq):
        logging.debug(__name__ + ' : Setting frequency')
        self._visainstrument.write('SOUR:FREQ %f' % freq)
        sleep(self.wait_time)
        return self.check_event_register()

    def do_get_frequency(self):
        logging.debug(__name__ + ' : Getting frequency')
        return self._visainstrument.ask('SOUR:FREQ?')

    def do_set_amplitude(self, amp):
        logging.debug(__name__ + ' : Setting amplitude')
        if self.get_output_function() != 'DC':
            self._visainstrument.write('SOUR:VOLT %.3f' % amp)
            sleep(0.1) # A hard sleep is really needed before checking the
                       # event register.
            return self.check_event_register()
        else:
            logging.info(__name__ + 
                        ' : Trying to adjust amplitude while in DC mode.')
            return False

    def do_get_amplitude(self):
        logging.debug(__name__ + ' : Getting amplitude')
        return self._visainstrument.ask('SOUR:VOLT?')

    def do_get_amplitude_units(self):
        '''Get the units of the amplitude. Should return VPP, VRMS or DBM.'''
        logging.debug(__name__ + ' : Getting the amplitude units')
        return self._visainstrument.ask('SOUR:VOLT:UNIT?')

    def do_set_offset(self, offset):
        logging.debug(__name__ + ' : Setting offset')
        self._visainstrument.write('SOUR:VOLT:OFFS %f' % offset)
        msleep(self.wait_time)
        return self.check_event_register()

    def do_get_offset(self):
        logging.debug(__name__ + ' : Getting offset')
        return self._visainstrument.ask('SOUR:VOLT:OFFS?')

    def do_get_output_function(self):
        '''
        Get the output function.
        '''
        logging.debug(__name__ + ' : Getting the output function')
        response = self._visainstrument.ask('FUNC:SHAP?')
        if response == 'SIN':
            self.set_parameter_bounds('frequency',100e-6,15e6)
            return 'sinusoid'
        elif response == 'SQU':
            self.set_parameter_bounds('frequency',100e-6,15e6)
            return 'square'
        elif response == 'TRI':
            self.set_parameter_bounds('frequency',100e-6,100e3)
            return 'triangle'
        elif response == 'RAMP':
            self.set_parameter_bounds('frequency',100e-6,100e3)
            return 'ramp'
        elif response == 'NOISE':
            return 'noise'
        elif response == 'DC':
            return 'DC'
        elif response == 'USER':
            # frequency bounds depend on the length of the waveform
            return 'user'
        else:
            logging.warning(__name__ + 
                ' : answer to FUNC:SHAP? was not expected : %s' % response)

    def do_set_output_function(self, function):
        '''
        Set the output function.
        '''
        logging.debug(__name__ + 
                ' : Setting the output function to %s' % function)
        function_dict = {
                        'SINUSOID' : 'SIN',
                        'SQUARE'   : 'SQU',
                        'TRIANGLE' : 'TRI',
                        'RAMP'     : 'RAMP',
                        'NOISE'    : 'NOISE',
                        'DC'       : 'DC',
                        'USER'     : 'USER'}
        bounds_dict = {
                        'SINUSOID' : [100e-6, 15e6],
                        'SQUARE'   : [100e-6, 15e6],
                        'TRIANGLE' : [100e-6, 100e3],
                        'RAMP'     : [100e-6, 100e3],
                        'NOISE'    : None,
                        'DC'       : None,
                        'USER'     : None}
        self._visainstrument.write('FUNC:SHAP %s' % function_dict[function])
        msleep(self.wait_time)
        if bounds_dict[function]:
            self.set_parameter_bounds('frequency',
                                    bounds_dict[function][0],
                                    bounds_dict[function][1])
	return self.check_event_register()
        
    def do_get_last_error_message(self):
        '''
        Read out the last error message from the instrument.
        '''
        message = self._visainstrument.ask('SYST:ERR?')
        if message.startswith('-221:,"Settings conflict: offset'):
            self.get_offset()
        return message

    def get_event_register(self):
        '''
        Read out the standard event register
        return an integer

        0 Operation Complete
        1 Not Used
        2 Query Error
        3 Device Error
        4 Execution Error
        5 Command Error
        6 Not Used
        7 Power On
        '''
        return int(self._visainstrument.ask('*ESR?')) 

    def check_event_register(self):
        '''
        Check whether the operation was completed successfully by reading 
        out the standard event register.
        If it wasn't raise an execution error with the error message.
        '''
        if self.get_message_available:
            logging.debug(__name__ + 
                            ': There is something in the output buffer')
        response = self._visainstrument.ask('*ESR?')
        event_register = int(response)

        if event_register == 0:
            # Operation Complete
            return True
        if get_bit_set(event_register, 2):
            # Query Error
            raise Exception(__name__+ ' : Query Error:' 
                            + self.get_last_error_message())
        if get_bit_set(event_register, 3):
            # Device Error
            raise Exception(__name__+ ' : Device Error:' 
                            + self.get_last_error_message())
        if get_bit_set(event_register, 4):
            # Execution Error
            raise Exception(__name__+ ' : Execution Error:' 
                            + self.get_last_error_message())
        if get_bit_set(event_register, 5):
            # Command Error
            raise Exception(__name__+ ' : Command Error:' 
                            + self.get_last_error_message())
        if get_bit_set(event_regsiter, 7):
            # Power On
            raise Exception(__name__ + ': Has been turned off and on.')
            
#        elif event_register == 4:
#            # Message Available Bit (MAV) is set
#        elif event_register > 128:
#            raise Exception(__name__ + ': Has been turned off and on.')
#        else:
#            print event_register
#            raise Exception(__name__+ ' : ' + self.get_last_error_message())
             
    def operation_complete_query(self):
        '''
        This is only used in the triggered burst mode and triggered sweep mode.
        '''
        return bool(int(self._visainstrument.ask('*OPC?')))

    def do_get_trigger_source(self):
        '''
        Get the trigger source.
        '''
        logging.debug(__name__ + ' : Getting the trigger source.')
        return self._visainstrument.ask('TRIG:SOUR?')

    def do_set_trigger_source(self, source):
        '''
        Set the trigger source.
        Options are:
            IMM
            EXT
            BUS
        '''
        logging.debug(__name__ + ' : Setting the trigger source to %s.' % source)
        self._visainstrument.write('TRIG:SOUR %s' % source)
        msleep(self.wait_time)
        return self.check_event_register()

    def do_get_output_termination(self):
        '''
        Get the output termination.
        Returns HIGH or LOW.
            LOW  : 50 Ohm
            HIGH : Open circuit
        '''
        logging.debug(__name__ + ' Get the output termination.')
        answer = self._visainstrument.ask('OUTP:LOAD?')
        if answer == '+5.00000E+01':
            return 'LOW'
        else:
            return 'HIGH'

    def do_set_output_termination(self, termination):
        '''
        Set the output termination.
        LOW : 50 Ohm
        HIGH : Open circuit
        '''
        logging.debug(__name__ + 
                    ' Set the output termination to %s.' % termination)
        if termination == 'LOW':
            self._visainstrument.write('OUTP:LOAD 50')
        else:
            self._visainstrument.write('OUTP:LOAD INF')
        msleep(self.wait_time)
        return self.check_event_register()

    def do_get_selected_arbitrary_waveform(self):
        '''
        Get the selected arbitrary waveform.
        '''
        logging.debug(__name__ + ' Get the selected arbitrary waveform.')
        return self._visainstrument.ask('FUNC:USER?')

    def do_get_selected_arbitrary_waveform_length(self):
        '''
        Get the number of points in the selected arbitrary waveform.
        '''
        logging.debug(__name__ + ' Get the number of points in the selected waveform')
#        waveform = self.get_selected_arbitrary_waveform()
        answer = self._visainstrument.ask('DATA:ATTR:POIN?')
        return(int(float(answer)))

    def do_get_waveforms_in_memory(self):
        '''
        Get all the waveforms that are currently in the memory of the instrument.
        '''
        logging.debug(__name__ + ' Get the waveforms in memory.')
        answer = self._visainstrument.ask('DATA:CAT?')
        return answer.replace('"','').split(',')

    def do_get_amplitude_modulation_state(self):
        '''
        Get the state of the amplitude modulation.
        Returns True if on, False if off.
        '''
        logging.debug(__name__ + ' Get the amplitude modulation state.')
        answer = self._visainstrument.ask('AM:STAT?')
        if answer == '0':
            return False
        else:
            return True

    def do_get_amplitude_modulation_source(self):
        '''
        Get the source of the amplitude modulation.
        Options:
            'BOTH'
            'EXTERNAL'
        '''
        logging.debug(__name__ + ' Get the source of the amplitude modulation')
        answer = self._visainstrument.ask('AM:SOUR?')
        if answer == 'BOTH':
            return 'BOTH'
        else:
            return 'EXT'

    def get_message_available(self):
        '''
        Query the status byte to see if there is a message.
        '''
        response = self._visainstrument.ask('*STB?')
        if get_bit_set(int(response),4):
            return True
        else:
            return False
        
    
