# PAR_5210.py class, to perform the communication between the Wrapper and the device
# -*- coding: utf-8 -*-
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
import qt
import types
import logging
import numpy as np
from time import sleep
from math import log10
import visa

class PAR_5210(Instrument):
    '''
    This is the driver for the EG&G / Princecton Applied Research 
    Model 5210 Lock-in amplifier

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'EGandG_Model5209', address='<GBIP address>, reset=<bool>')
    '''
    def __init__(self, name, address, reset=False):
        logging.info(__name__ + ' : Initializing instrument PAR Model 5210')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.timeout = 1.0
        self._visainstrument.term_chars = '\r'
        self._visainstrument.write("REMOTE 1")
        #self.init_default()

        # Sensitivity
        self._sen = 1.0

        # Add functions
        self.add_function('init_default')
        self.add_function ('get_all')
        self.add_function ('auto_measure')
        self.add_function ('auto_phase')

        # Add parameters
#        self.add_parameter('value',
#            flags=Instrument.FLAG_GET, 
#            units='V', 
#           type=types.FloatType,
#            tags=['measure'])
        # oscillator
        self.add_parameter('oscillator_amplitude',
            flags=Instrument.FLAG_GETSET,
            units='Vrms',
            minval=0.0, maxval=2.0,
            format='%.3f',
            type=types.FloatType)
        self.add_parameter('oscillator_frequency',
            flags=Instrument.FLAG_GETSET,
            units='Hz',
            minval=0.5, maxval=120000,
            type=types.FloatType)

        # input
        self.add_parameter('filter_frequency_tuning_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list = ('manual','automatic'),
            ) 
        self.add_parameter('reference_frequency',
            flags=Instrument.FLAG_GET, 
            units='Hz', 
            type=types.FloatType)
        self.add_parameter('sensitivity',
            flags=Instrument.FLAG_GETSET, 
            units='', 
            minval=0, maxval=15, 
            format_map = {  0 : '100 nV',
                            1 : '300 nV',
                            2 : u'1 μV',
                            3 : u'3 μV',
                            4 : u'10 μV',
                            5 : u'30 μV',
                            6 : u'100 μV',
                            7 : u'300 μV',
                            8 : '1 mV',
                            9 : '3 mV',
                           10 : '10 mV',
                           11 : '30 mV',
                           12 : '100 mV',
                           13 : '300 mV',
                           14 : '1 V',
                           15 : '3 V',},
            type=types.IntType)
        self.add_parameter('time_constant',
            flags=Instrument.FLAG_GETSET, 
            units='', 
            minval=0, maxval=15, 
            format_map = {  0 : '1 ms',
                            1 : '3 ms',
                            2 : '10 ms',
                            3 : '30 ms',
                            4 : '100 ms',
                            5 : '300 ms',
                            6 : '1 s',
                            7 : '3 s',
                            8 : '10 s',
                            9 : '30 s',
                           10 : '100 s',
                           11 : '300 s',
                           12 : '1 ks',
                           13 : '3 ks',
                        },
            type=types.IntType)
#        self.add_parameter('sensitivity_v',
#            flags=Instrument.FLAG_GETSET, 
#            units='V', 
#            minval=0.0, maxval=15.0, 
#            type=types.FloatType)
#        self.add_parameter('timeconstant_t',
#            flags=Instrument.FLAG_GETSET, 
#            units='s', 
#            minval=0.0, maxval=15.0, 
#            type=types.FloatType)
        self.add_parameter('filter_mode',
            flags=Instrument.FLAG_GETSET, 
            minval=0, maxval=3, 
            format_map = {  0 : 'no filter',
                            1 : 'band-rejection',
                            2 : 'low-pass',
                            3 : 'band-pass'},
            type=types.IntType,
            )
        self.add_parameter('dac_output',
            flags=Instrument.FLAG_GETSET,
            units='V',
            minval=-15.0, maxval=15.0,
            format='%.3f',
            type=types.FloatType)
        for adc_input in range(1,5):
            self.add_parameter('adc_input_ch%i' % adc_input,
            flags=Instrument.FLAG_GET,
            units='V' ,
            format='%.3f',
            type=types.FloatType,
            get_func=self.get_adc_input,
            channel=adc_input)

        # output
        self.add_parameter('ch1_output',
            flags=Instrument.FLAG_GET,
            type=types.StringType)
        self.add_parameter('ch2_output',
            flags=Instrument.FLAG_GET,
            type=types.StringType)
        self.add_parameter('dynamic_reserve',
            flags=Instrument.FLAG_GET,
            type=types.StringType)
        self.add_parameter('output_expansion',
            flags=Instrument.FLAG_GET,
            type=types.BooleanType)
        # display
        self.add_parameter('display1',
            flags=Instrument.FLAG_GET,
            type=types.StringType)
        self.add_parameter('display2',
            flags=Instrument.FLAG_GET,
            type=types.StringType)
        
        if reset:
            self.init_default()
        self.get_all()

#        self.get_sensitivity_v()

    def _write(self, letter):
        self._visainstrument.write(letter)
        sleep(0.1)

    def _ask(self, question):
        response = self._visainstrument.ask(question+'\n')
        qt.msleep(0.05)
        return response

    def get_all(self):
#        self.get_value()
        self.get_filter_frequency_tuning_mode()
        self.get_filter_mode()
        self.get_reference_frequency()
        self.get_oscillator_amplitude()
        self.get_oscillator_frequency()

        self.get_sensitivity()
        self.get_time_constant()
#        self.get_sensitivity_v()
#        self.get_timeconstant_t()
        self.get_dac_output()
        for adc_input in range(1,5):
            self.get('adc_input_ch%i' % adc_input)
        self.get_display1()
        self.get_display2()
        self.get_ch1_output()
        self.get_ch2_output()
        self.get_dynamic_reserve()
        self.get_output_expansion()

    def init_default(self):
#      self._write("ASM")
        self._write("SEN 7")
        self._write("XTC 3")
        self._write("FLT 3")

    def auto_measure(self):
        self._write("ASM")

    def auto_phase(self):
        self._write("AQN")

    def do_get_reference_frequency(self):
        stringval = self._ask("FRQ?")
        return float(stringval)/1000.0

    def do_get_filter_frequency_tuning_mode(self):
        '''Get the tuning mode of the filter frequency'''
        stringval = self._ask("ATC?")
        if stringval == '0':
            return 'manual'
        elif stringval == '1':
            return 'automatic'
        else:
            logging.warning(__name__ + 'invalid response to ATC?: %s' % stringval)

    def do_set_filter_frequency_tuning_mode(self, mode):
        '''Set the tuning mode of the filter frequency'''
        if mode.lower() == 'manual':
            self._write('ATC 0')
        else:
            self._write('ATC 1')

    def do_get_oscillator_amplitude(self):
        '''Get the amplitude of the internal oscillator'''
        stringval = self._ask("OA?")
        return float(stringval)/1000.0

    def do_set_oscillator_amplitude(self, amplitude):
        '''Set the amplitude of the internal oscillator'''
        self._write("OA %i" % (amplitude * 1000))

    def do_get_oscillator_frequency(self):
        '''Get the frequency of the internal oscillator'''
        stringval = self._ask("OF?")
        n1 = int(stringval.split()[0]) # number between 2000 and 20000
        n2 = int(stringval.split()[1]) # frequency band 0 - 5
        multiplier = pow(10, (n2 - 4))
        return n1*multiplier
        
    def do_set_oscillator_frequency(self, frequency):
        '''Set the frequency of the internal oscillator'''
        frequency_band = int(log10(frequency*5))
        n1 = frequency * pow(10, (4 - frequency_band))
        self._write('OF %i %i' % (n1, frequency_band))

#    def do_get_value(self):
#        stringval =  self._ask("OUT?")
#        sd = stringval.split()
#        if len(sd)==2:
#            s=sd[0]
#            v = float(sd[1])
#        if (s=='-'):
#            v = -v
#        else:
#            v = float(sd[0])
#
#        return v*self._sen/10000.0

    def do_get_sensitivity(self):
        stringval = self._ask("SEN?")
#        self.get_sensitivity_v()
        return int(stringval)

    def do_set_sensitivity(self,val):
        self._write("SEN %d"%val)
        self.get_sensitivity()

    def do_get_filter_mode(self):
        stringval = self._ask("FLT?")
        print stringval
        return int(stringval)

    def do_set_filter_mode(self,val):
        self._write("FLT %d"%val)

    def do_get_time_constant(self):
        '''Get the filter time constant'''
        stringval = self._ask("XTC?")
        return int(stringval)

    def do_set_time_constant(self,val):
        '''Set the filter time constant'''
        self._write("XTC %d"%val)

#    def do_get_sensitivity_v(self):
#        stringval = self._ask("SEN?")
#        n = int(stringval)
#        self._sen = pow(10,(int(n/2)-7+np.log10(3)*np.mod(n,2)))
#        return self._sen

#    def do_set_sensitivity_v(self,val):
#        n = np.log10(val)*2.0+13.99
#        if (np.mod(n,2) > 0.9525) & (np.mod(n,2) < 1.1):
#            n = n+0.1
#        self._write("SEN %d"%n)
#        self.get_sensitivity_v()

#    def do_get_timeconstant_t(self):
#        stringval = self._ask("XTC?")
#        n = int(stringval)
#        sen = pow(10,
#                int(n/2)-3+np.log10(3)*mod(n,2)
#                )
#        return sen

#    def do_set_timeconstant_t(self,val):
#        n = np.log10(val)*2.0+5.99
#        if (mod(n,2) > 0.9525) & (mod(n,2) < 1.1):
#            n = n+0.1
#        self._write("XTC %d"%n)

    def do_get_dac_output(self):
        '''Get the output voltage of the DAC output'''
        V = self._ask("DAC?")
        return int(V)/1000.0

    def do_set_dac_output(self, V):
        '''Set the output voltage of the DAC output'''
        self._write("DAC %i" % (V*1000))

    def get_adc_input(self, channel):
        '''Get the input of the auxiliary analog to digital inputs'''
        response = self._ask("ADC %i" % channel)
        return int(response)/1000.0

    def do_get_ch1_output(self):
        '''Get the type of the output appearing at the CH1 analog output'''
        response = self._ask("D2?")
        response_options = {'0' : 'X-channel output',
                            '1' : 'X-channel output',
                            '2' : 'Magnitude output',
                            '3' : 'X-channel output',
                            '4' : 'Noise output',
                            '5' : ''}
        return response_options[response]

    def do_get_ch2_output(self):
        '''Get the type of the output appearing at the CH2 analog output'''
        response = self._ask("D2?")
        response_options = {'0' : 'Y-channel output',
                            '1' : 'Y-channel output',
                            '2' : 'Phase output',
                            '3' : 'Y-channel output',
                            '4' : 'Magnitude output',
                            '5' : ''}
        return response_options[response]

    def do_get_dynamic_reserve(self):
        '''Get the dynamic reserve control setting'''
        response = self._ask("DR?")
        if response == '0':
            return 'high stability'
        elif response == '1':
            return 'normal'
        elif response == '2':
            return 'high dynamic reserve'
        else:
            logging.warning(__name__ + 'invalid response to DR?: %s' % response)

    def do_get_output_expansion(self):
        '''Get whether the output expansion is on (X-channel * 10)'''
        response = self._ask("EX?")
        if response == '0':
            return False
        elif response == '1':
            return True
        else:
            logging.warning(__name__ + 'invalid response to EX?: %s' % response)

    def do_get_display1(self):
        response = self._ask("D1?")
        response_options = {'0' : 'reference phase',
                            '1' : 'oscillator amplitude',
                            '2' : 'oscillator frequency',
                            '3' : 'filter frequency',
                            '4' : 'display reference frequency',
                            '5' : 'display output'}
        return response_options[response]

    def do_get_display2(self):
        response = self._ask("D2?")
        response_options = {'0' : 'XY %',
                            '1' : 'XY V',
                            '2' : u'RΘ',
                            '3' : 'OFFSET',
                            '4' : 'NOISE',
                            '5' : 'SPEC'}
        return response_options[response]
