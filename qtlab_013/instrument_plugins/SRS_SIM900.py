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
            self._visainstrument.baud_rate = 115200
        self._visainstrument.clear()
        cts = int(self._visainstrument.ask('CTCR?'))

        self.occupied_ports = []
        self.bad_ports = []
        self.SIM928_modules = [] # list of the ports of the SIM928 modules
        self.SIM911_modules = [] # list of the ports of the SIM911 modules

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
                                flags=Instrument.FLAG_GET,
                                type=types.IntType,
                                option_list=(1,2,5,10,20,50,100),
                                get_func=self.SIM911_get_gain,
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

    def SIM911_get_gain(self, channel):
        '''Get the gain of a SIM911 BJT Preamp module'''
        self._visainstrument.write('FLSH %i' % channel)
        self._visainstrument.write('SNDT %i, "GAIN?"' % channel)
        qt.msleep(self.sleep_time)
        response = self._ask('GETN? %i,80' % channel)
        return int(response)

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
