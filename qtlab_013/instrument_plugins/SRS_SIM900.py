#  -*- coding: utf-8 -*-
# SRS_SIM900.py driver for SRS SIM900 mainframe
# Gabriele de Boo <ggdeboo@gmail.com>

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
import re

import qt

class SRS_SIM900(Instrument):
    '''
    This is the driver for the SRS SIM900 mainframe

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'HP_34401A',
        address='<VISA address>',
        reset=<bool>,

    Supported modules;
        SIM928 : Isolated voltage source
        SIM911 : BJT preamplifier
        SIM965 : Bessel & Butterworth filter
    '''

    def __init__(self, name, address, reset=False,
        change_display=False, change_autozero=False):
        '''
        Initializes the SRS_SIM900, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : VISA address 
            reset (bool)            : resets to default values
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument SRS_SIM900')
        Instrument.__init__(self, name, tags=['physical', 'measure'])

        # Add some global constants
        self.__name__ = name
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        if self._visainstrument.interface_type == 4: # serial?
            self._visainstrument.term_chars = '\r\n'
            self._visainstrument.baud_rate = 9600
        self._visainstrument.clear()
        cts = int(self._visainstrument.ask('CTCR?'))

        self.occupied_ports = []
        self.bad_ports = []
        self.SIM928_modules = [] # list of the ports of the SIM928 modules
        self.SIM911_modules = [] # list of the ports of the SIM911 modules
        self.SIM965_modules = [] # list of the ports of the SIM965 modules

        for i in range(1,9):
            if bin(cts)[-(i+1)] == '1':
                self.occupied_ports.append(i)
        print self.occupied_ports

        if reset:
            self.reset()

        self.sleep_time = 0.08

        self.installed_modules = []
        self.serial_numbers = []
        for port in self.occupied_ports:
            self._visainstrument.write('SNDT %i,"*IDN?"' % port)
            qt.msleep(self.sleep_time)
            idn = self._ask('GETN? %i,80' % port)
            if idn == '':
                logging.warning('Module in port %i is not responding ' + 
                                    'properly and will not be loaded.' % port)
                self.bad_ports.append(port)
            else:
                print idn
                self.installed_modules.append((port, idn.split(',')[1]))
                self.serial_numbers.append((port, idn.split(',')[2]))

        # internal baud_rate
        # if this is too high, the communication with the modules
        # can stall
        self.module_baud_rate = 38400 
        self.set_modules_baud_rate()

        for port in self.bad_ports:
            self.occupied_ports.remove(port)

        print(self.installed_modules)
        print(self.serial_numbers)
        for port, module in self.installed_modules:
            if module == 'SIM928':
                self.SIM928_modules.append(port)
                self.add_parameter('port%i_voltage' % port,
                                flags=Instrument.FLAG_GETSET,
                                type=types.FloatType,
                                units='V',
                                minval=-10.0, maxval=10.0,
                                maxstep=0.1, stepdelay=50,
                                format='%.3f',
                                get_func=self.SIM928_get_voltage,
                                set_func=self.SIM928_set_voltage,
                                channel=port,
                                )
                self.add_parameter('port%i_status' % port,
                                flags=Instrument.FLAG_GETSET,
                                type=types.BooleanType,
                                get_func=self.SIM928_get_status,
                                set_func=self.SIM928_set_status,
                                channel=port,
                                )
                self.add_parameter('port%i_battery_status' % port,
                                flags=Instrument.FLAG_GET,
                                type=types.StringType,
                                get_func=self.SIM928_get_battery_status,
                                channel=port,
                                )
                self.add_parameter('port%i_last_pressed_button' % port,
                                flags=Instrument.FLAG_GET,
                                type=types.StringType,
                                get_func=self.SIM928_get_last_pressed_button,
                                channel=port,
                                )
            if module == 'SIM911':
                self.SIM911_modules.append(port)
                self.add_parameter('port%i_gain' % port,
                                flags=Instrument.FLAG_GETSET,
                                type=types.IntType,
                                option_list=(1,2,5,10,20,50,100),
                                get_func=self.SIM911_get_gain,
                                set_func=self.SIM911_set_gain,
                                channel=port,
                                )
                self.add_parameter('port%i_coupling' % port,
                                flags=Instrument.FLAG_GET,
                                type=types.StringType,
                                option_list=('AC','DC'),
                                get_func=self.SIM911_get_coupling,
                                channel=port,
                                )
                self.add_parameter('port%i_input' % port,
                                flags=Instrument.FLAG_GET,
                                type=types.StringType,
                                option_list=('A','A-B','GND'),
                                get_func=self.SIM911_get_input,
                                channel=port,
                                )
                self.add_parameter('port%i_shield' % port,
                                flags=Instrument.FLAG_GET,
                                type=types.StringType,
                                option_list=('FLOATING','GROUNDED'),
                                get_func=self.SIM911_get_shield,
                                channel=port,
                                )
            if module == 'SIM965':
                self.SIM965_modules.append(port)
                self.add_parameter('port{0}_filter_frequency'.format(port),
                                flags=Instrument.FLAG_GETSET,
                                type=types.FloatType,
                                units='Hz',
                                minval=1.0, maxval=5.00e5,
                                get_func=self.SIM965_get_filter_frequency,
                                set_func=self.SIM965_set_filter_frequency,
                                channel=port,
                                )
                self.add_parameter('port{0}_filter_type'.format(port),
                                flags=Instrument.FLAG_GETSET,
                                type=types.StringType,
                                option_list = ['butterworth', 'bessel'],
                                get_func=self.SIM965_get_filter_type,
                                set_func=self.SIM965_set_filter_type,
                                channel=port,
                                )
                self.add_parameter('port{0}_filter_passband'.format(port),
                                flags=Instrument.FLAG_GETSET,
                                type=types.StringType,
                                option_list = ['low pass', 'high pass'],
                                get_func=self.SIM965_get_filter_passband,
                                set_func=self.SIM965_set_filter_passband,
                                channel=port,
                                )
                self.add_parameter('port{0}_filter_slope'.format(port),
                                flags=Instrument.FLAG_GETSET,
                                type=types.IntType,
                                option_list = [12, 24, 36, 48],
                                units='dB/octave',
                                get_func=self.SIM965_get_filter_slope,
                                set_func=self.SIM965_set_filter_slope,
                                channel=port,
                                )
                self.add_parameter('port{0}_input_coupling'.format(port),
                                flags=Instrument.FLAG_GET,
                                type=types.StringType,
                                option_list=('AC','DC'),
                                get_func=self.SIM965_get_input_coupling,
                                channel=port,
                                )
                            
        # Housekeeping parameters
        self.add_parameter('external_timebase',
                        flags=Instrument.FLAG_GET,
                        type=types.BooleanType,
                        )
        self.add_parameter('timebase_vco_voltage',
                        flags=Instrument.FLAG_GET,
                        type=types.IntType,
                        units='mV',
                        )
        self.add_parameter('primary_voltage',
                        flags=Instrument.FLAG_GET,
                        type=types.FloatType,
                        units='V',
                        )
        self.add_parameter('primary_current',
                        flags=Instrument.FLAG_GET,
                        type=types.IntType,
                        units='mA',
                        )
        self.add_parameter('time_since_power_on',
                        flags=Instrument.FLAG_GET,
                        type=types.FloatType,
                        units='s',
                        format='%.0f',
                        )

        self.add_function('reset')
        self.add_function('get_all')

        self.get_all()
            #self.set_defaults()

# --------------------------------------
#           functions
# --------------------------------------

    def reset(self):
        '''
        Resets instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting instrument')
        for port in range(1,9):
            # flush buffers
#            self._visainstrument.write('FLSH %i' % port)
            # reset individual modules
            self._visainstrument.write('SRST %i' % port)
            self._visainstrument.write('BAUD %i,%i' % (port, 9600))
            self._visainstrument.write('SNDT %i, "*RST"' % port)
            qt.msleep(0.1)
        self._visainstrument.write('*RST')
        qt.msleep(0.1)

    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.debug('Get all relevant data from device')
        self.get_external_timebase()
        self.get_timebase_vco_voltage()
        self.get_primary_voltage()
        self.get_primary_current()
        self.get_time_since_power_on()

        for module in self.SIM928_modules:
            self.get('port%i_voltage' % module)
            self.get('port%i_status' % module)
            self.get('port%i_battery_status' % module)
            self.get('port%i_last_pressed_button' % module)
        for module in self.SIM911_modules:
            self.get('port%i_gain' % module)
            self.get('port%i_coupling' % module)
            self.get('port%i_input' % module)
            self.get('port%i_shield' % module)
        for module in self.SIM965_modules:
            self.get('port{0}_filter_frequency'.format(module))
            self.get('port{0}_filter_type'.format(module))
            self.get('port{0}_filter_passband'.format(module))
            self.get('port{0}_filter_slope'.format(module))
            self.get('port{0}_input_coupling'.format(module))

    def _ask(self, message):
        '''
        '''
        response = self._visainstrument.ask(message)
        self._visainstrument.clear()
        if response.startswith('#3'):
            n_bytes = int(response[2:5])

            if n_bytes == 0:
                return ''
            else:
                return response[5:5+n_bytes]
        else:
            logging.warning('SIM900 responded to %s with: %s' % 
                            (message, response))

    # SIM928 isolated voltage source

    def SIM928_get_voltage(self, channel):
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "VOLT?"' % channel)
        qt.msleep(self.sleep_time)
        return float(self._ask('GETN? %i,80' % channel))

    def SIM928_set_voltage(self, voltage, channel):
        self._visainstrument.write('SNDT %i, "VOLT %.3f"' % 
                            (channel, voltage))
        qt.msleep(self.sleep_time)

    def SIM928_get_status(self, channel):
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "EXON?"' % channel)
        qt.msleep(self.sleep_time)
        return bool(int(self._ask('GETN? %i,80' % channel)))

    def SIM928_set_status(self, status, channel):
        if status:
            self._visainstrument.write('SNDT %i, "OPON"' % channel)
        else:
            self._visainstrument.write('SNDT %i, "OPOF"' % channel)
        qt.msleep(self.sleep_time)

    def SIM928_get_battery_status(self, channel):
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "BATS?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel).split(',')
        if len(response) == 0:
            logging.warning('SIM928 module battery status response: %s' % 
                            response)
            return ''
        return_string = ''
        if response[0] == '1':
            return_string += 'battery A in use, '
        elif response[0] == '2':
            return_string += 'battery A charging, '
        elif response[0] == '3':
            return_string += 'battery A ready, '
        if response[1] == '1':
            return_string += 'battery B in use'
        elif response[1] == '2':
            return_string += 'battery B charging'
        elif response[1] == '3':
            return_string += 'battery B ready'
        if response[2] == '1':
            return_string += ', service batteries'
        return return_string

    def SIM928_get_last_pressed_button(self, channel):
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "LBTN?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        if response == '0':
            return 'no button pressed since last LBTN?'
        elif response == '1':
            return '[On/Off]'
        elif response == '2':
            return '[100 mV increase]'
        elif response == '3':
            return '[100 mV decrease]'
        elif response == '4':
            return '[10 mV increase]'
        elif response == '5':
            return '[10 mV decrease]'
        elif response == '6':
            return '[1 mV increase]'
        elif response == '7':
            return '[1 mV decrease]'
        elif response == '8':
            return '[Battery Override]'

    # SIM911 BJT preamplifier

    def SIM911_get_gain(self, channel):
        '''Get the gain of a SIM911 BJT Preamp module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "GAIN?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        return int(response)

    def SIM911_set_gain(self, gain, channel):
        '''Set the gain of a SIM911 BJT Preamp module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "GAIN %i"' % (channel,gain))

    def SIM911_get_coupling(self, channel):
        '''Get the input coupling of a SIM911 BJT Preamp module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "COUP?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        if response == '1':
            return 'AC'
        if response == '2':
            return 'DC'

    def SIM911_get_input(self, channel):
        '''Get the input configuration of a SIM911 BJT Preamp module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "INPT?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        if response == '1':
            return 'A'
        if response == '2':
            return 'A-B'
        if response == '3':
            return 'GND'

    def SIM911_get_shield(self, channel):
        '''Get the shield configuration of a SIM911 BJT Preamp module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "SHLD?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        if response == '1':
            return 'FLOATING'
        if response == '2':
            return 'GROUNDED'

    # SIM 965 Bessel & Butterworth filter

    def SIM965_get_filter_frequency(self, channel):
        '''Get the filter frequency of a SIM965 filter module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "FREQ?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        return float(response)

    def SIM965_set_filter_frequency(self, frequency, channel):
        '''Set the filter frequency of a SIM965 filter module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT {:d}, "FREQ {:.2E}"'.format(channel,
                                                            frequency))

    def SIM965_get_filter_type(self, channel):
        '''Get the filter type of a SIM965 filter module

        input:
            None       
 
        output:
            butterworth or bessel
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        self._visainstrument.write('SNDT {0}, "TYPE?"'.format(channel))
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? {0},80'.format(channel))
        if response == '0':
            return 'butterworth'
        elif respone == '1':
            return 'bessel'
        else:
            logging.warning('Filter type query returned invalid response: ' + 
                            '{0}'.format(response))

    def SIM965_set_filter_type(self, filter_type, channel):
        '''Set the filter type of a SIM965 filter module

        input:
            butterworth or bessel
 
        output:
            None
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        if filter_type.upper() == 'BUTTERWORTH':
            self._visainstrument.write(
                'SNDT {0}, "TYPE {1}"'.format(channel, 'BUTTER'))
        elif filter_type.upper() == 'BESSEL':
            self._visainstrument.write(
                'SNDT {0}, "TYPE {1}"'.format(channel, 'BESSEL'))
        else:
            raise ValueError(
            'set_filter_type got an invalid input: {0}'.format(filter_type))

    def SIM965_get_filter_passband(self, channel):
        '''Get the filter passband of a SIM965 filter module

        input:
            None       
 
        output:
            'low pass' or 'high pass'
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        self._visainstrument.write('SNDT {0}, "PASS?"'.format(channel))
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? {0},80'.format(channel))
        if response == '0':
            return 'low pass'
        elif respone == '1':
            return 'high pass'
        else:
            logging.warning('Filter passband query returned invalid response:' 
                            + ' {0}'.format(response))

    def SIM965_set_filter_passband(self, filter_passband, channel):
        '''Set the filter pass band of a SIM965 filter module

        input:
            'low pass' or 'high pass'
 
        output:
            None
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        if filter_type.upper() == 'LOW PASS':
            self._visainstrument.write(
                'SNDT {0}, "PASS {1}"'.format(channel, 'LOWPASS'))
        elif filter_type.upper() == 'HIGH PASS':
            self._visainstrument.write(
                'SNDT {0}, "TYPE {1}"'.format(channel, 'HIGHPASS'))
        else:
            raise ValueError(
                'set_filter_passband got an invalid input:' +
                ' {0}'.format(filter_passband))

    def SIM965_get_filter_slope(self, channel):
        '''Get the filter slope of a SIM965 filter module

        input:
            None       
 
        output:
            12, 24, 36, or 48
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        self._visainstrument.write('SNDT {0}, "SLPE?"'.format(channel))
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? {0},80'.format(channel))
        return int(response)

    def SIM965_set_filter_slope(self, filter_slope, channel):
        '''Set the filter slope of a SIM965 filter module

        input:
            12, 24, 36, or 48
 
        output:
            None       
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        self._visainstrument.write(
            'SNDT {0}, "SLPE {1}"'.format(channel, filter_slope))

    def SIM965_get_input_coupling(self, channel):
        '''Get the input coupling of a SIM965 filter module

        input:
            None       
 
        output:
            'DC' or 'AC'
        '''
        self._visainstrument.write('FLSH {0}'.format(channel))
        self._visainstrument.write('SNDT {0}, "COUP?"'.format(channel))
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? {0},80'.format(channel))
        if response == '0':
            return 'DC'
        elif response =='1':
            return 'AC'
        else:
            logging.warning('Filter coupling query returned invalid response:' 
                            + ' {0}'.format(response))

    # internal functions

    def do_get_external_timebase(self):
        '''Query whether an external timbease input is detected'''
        response = self._visainstrument.ask('TBIN?')
        if response == '0':
            return False
        elif response == '1':
            return True
        else:
            logging.warning('Get external timebase responded with: %s' %
                            response)

    def do_get_timebase_vco_voltage(self):
        '''
        '''
        response = self._visainstrument.ask('VVCO?')
        return int(response)

    def do_get_primary_voltage(self):
        '''
        '''
        response = self._visainstrument.ask('VMON?')
        return int(response)/1000.0

    def do_get_primary_current(self):
        '''
        '''
        response = self._visainstrument.ask('IMON?')
        return int(response)

    def do_get_time_since_power_on(self):
        '''
        '''
        response = self._visainstrument.ask('TICK?')
        return int(response)/20.0

    def set_modules_baud_rate(self):
        for port, module in self.installed_modules:
            if module == 'SIM928':
                self._visainstrument.write('SNDT %i,"BAUD %i"' % (port, 
                                            self.module_baud_rate))
                qt.msleep(0.1)
                self._visainstrument.write('BAUD %i,%i' % 
                            (port, self.module_baud_rate))
