# Delta_PSC232.py driver for the PSC232 Delta Power Supply Controller
# Gabriele de Boo <g.deboo@student.unsw.edu.au>, 2012
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
import types
import visa
import logging
from time import sleep
import qt

class Delta_PSC232(Instrument):
    '''
    Wrapper to communicate with the Delta PSC232 power supply controller

    For a list of available commands write 'Help?' to the instrument
    For a list of available errors write 'Err?' to the instrument
    '''
    def __init__(self, 
                name, 
                address=None, 
                channel_list=[1, 2], 
                minvoltage_list=[0,0],
                maxvoltage_list=[30,30],
                mincurrent_list=[0,0],
                maxcurrent_list=[5,5],
                reset=False):
        Instrument.__init__(self, name, tags=['measure'])

        self._address = address
#	self._term_chars = '\n\r\x04'
        self._channel_list = channel_list
        self.minvoltage_list = minvoltage_list
        self.maxvoltage_list = maxvoltage_list
        self.mincurrent_list = mincurrent_list
        self.maxcurrent_list = maxcurrent_list

        rm = visa.ResourceManager()
        self._visains = rm.open_resource(address,
                                         read_termination = '\n\r\x04') 
        self._visains.baud_rate = 4800
        self._visains.timeout = 500 
        self._visains.write_termination = '\n\r'

        # The controller ends its messages with \n\r\x04, but when it reads
        # messages it wants to read \n\r. With the \x04 it complains about
        # receiving an unknown command.

#        self._visains.term_chars = '\n\r\x04'
        self._visains.clear()
        # identification
        self._idn = []

        for idx, ch in enumerate(channel_list):
            self._idn.append('')
            self._visains.write('CH %i' % ch)
            qt.msleep(0.1)
            self._idn[idx] += self._check_response(self._visains.query('*IDN?'))
#            self._idn[idx] += self._check_response(self._visains.read())
#            self._idn[idx] += self._check_response(self._visains.read())
        print self._idn
        
        self.add_parameter('minimum_voltage', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list,
                    units='V',
                    channel_prefix='ch%s_')
        self.add_parameter('maximum_voltage', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list,
                    units='V',
                    channel_prefix='ch%s_')
        self.add_parameter('minimum_current', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list,
                    units='A',
                    channel_prefix='ch%s_')
        self.add_parameter('maximum_current', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list,
                    units='A',
                    channel_prefix='ch%s_')
        self.add_parameter('voltage', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    tags=['sweep'],
                    maxstep=0.1, stepdelay=100,
                    channels=channel_list,
                    units='V',
                    channel_prefix='ch%s_')
        self.add_parameter('voltage_measured', type=types.FloatType,
                    flags=Instrument.FLAG_GET,
                    channels=channel_list,
                    units='V',
                    channel_prefix='ch%s_')
        self.add_parameter('current', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    tags=['sweep'],
                    maxstep=0.1, stepdelay=100,
                    channels=channel_list,
                    units='A',
                    channel_prefix='ch%s_')
        self.add_parameter('current_measured', type=types.FloatType,
                    flags=Instrument.FLAG_GET,
                    channels=channel_list,
                    units='A',
                    channel_prefix='ch%s_')
        self.add_parameter('active_channel', type=types.IntType,
                        flags=Instrument.FLAG_GETSET | Instrument.FLAG_SOFTGET)

        for idx, ch in enumerate(channel_list):
            self.set_parameter_options('ch%i_voltage' % ch,
                                        minval=minvoltage_list[idx],
                                        maxval=maxvoltage_list[idx])
            self.set_parameter_options('ch%i_current' % ch,
                                        minval=mincurrent_list[idx],
                                        maxval=maxcurrent_list[idx])
#        self.add_function('set_defaults')
        self.add_function('get_all')
        self.add_function('reset_channel')
   
#        self._channel_has_been_reset = len(channel_list)*[False]
        if reset:
            self.set_defaults()

        self.get_all()

    def set_defaults(self):
        '''Set default parameters.
        
        These are accurate for the ES 030-5 power supplies
        '''
        for idx, channel in enumerate(self._channel_list):
            self.set('ch%i_minimum_voltage' % channel,
                                        self.minvoltage_list[idx])
            self.set('ch%i_maximum_voltage' % channel, 
                                        self.maxvoltage_list[idx])
            self.set('ch%i_minimum_current' % channel,
                                        self.mincurrent_list[idx])
            self.set('ch%i_maximum_current' % channel, 
                                        self.maxcurrent_list[idx])
            self.set_parameter_options('ch%i_voltage' % channel, value=0.0)
            self.set_parameter_options('ch%i_current' % channel, value=0.0)
        # it doesn't like getting these commands twice...
            self._visains.write("REMOTE")

    def get_all(self):
#        for ch in self.get_
#        self.get_voltage()
#        self.get_current()
#        self.get_active_channel()
        for channel in self._channel_list:
            self.get('ch%i_current_measured' % channel)
            self.get('ch%i_voltage_measured' % channel)

    def reset_channel(self, channel):
        '''Not sure whether this works properly
        Instrument doesn't seem to recognize *RST
        '''
        self._visains.write('CH {0:d}'.format(channel))
        self._visains.write('*RST')

    def do_set_minimum_voltage(self, minvol, channel):
        '''Set minimum of the voltage range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self.set_active_channel(channel)
        self._visains.write("SOUR:VOLT:MIN %.3f" % minvol)

    def do_set_maximum_voltage(self, maxvol, channel):    
        '''Set maximum of the voltage range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self.set_active_channel(channel)
        self._visains.write("SOUR:VOLT:MAX %.3f" % maxvol)

    def do_set_minimum_current(self, mincur, channel):
        '''Set minimum of the current range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self.set_active_channel(channel)
        self._visains.write("SOUR:CURR:MIN %.3f" % mincur)

    def do_set_maximum_current(self, maxcur, channel):        
        '''Set maximum of the current range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self.set_active_channel(channel)
        self._visains.write("SOUR:CURR:MAX %.3f" % maxcur)

    def do_set_voltage(self, V, channel):
        '''Set the output voltage of the power supply'''
        self.set_active_channel(channel)
        self._visains.write("SOU:VOLT {0:.3f}".format(V))

    def do_set_current(self, I, channel):
        '''Set the output current of the power supply'''
        self.set_active_channel(channel)
        self._visains.write("SOU:CURR {0:.3f}".format(I))

    def do_get_voltage_measured(self, channel):
        self.set_active_channel(channel)
        response = self._check_response(self._visains.query("MEAS:VOLT?"))
        return float(response)

    def do_get_current_measured(self, channel):
        logging.debug(__name__ + 'Get the measured current.')
        self.set_active_channel(channel)
        response = self._check_response(self._visains.query("MEAS:CURR?"))
        return float(response)

    def do_get_active_channel(self):
        response = self._check_response(self._visains.querquery("CH?"))
        return int(response)

    def do_set_active_channel(self, channel):
        '''Set the active channel for communication

        If there is no wait after changing the channel, the controller could
        lock up. If it does it needs to be power cycled.
        '''
        if self.get_active_channel() != channel:
            self._visains.write("CH {0:d}".format(channel))
            qt.msleep(.1)
        else:
            logging.debug('Active channel already is {0:d}'.format(channel))

    def _check_response(self, response):
        '''Check the response for error messages'''
        if 'unknown command !' in response:
            logging.warning('Instrument replied with unknown command')
            new_response = self._check_response(self._visains.read())
            return new_response
        elif 'error max current range' in response:
            logging.warning('Instrument replied: {0}'.format(response))
            logging.warning('The maximum current has not been set yet.')
            # Need to set max current range?
        elif 'error max voltage range' in response:
            logging.warning('Instrument replied: {0}'.format(response))
            logging.warning('The maximum voltage has not been set yet.')
        if 'COMMAND LIST' in response:
            logging.info('We got a command list as the response.')
            self._visains.read()
        return response

