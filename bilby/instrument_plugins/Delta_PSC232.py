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

class Delta_PSC232(Instrument):

    def __init__(self, name, address=None, channel_list=(1, 2), reset=False):
        Instrument.__init__(self, name, tags=['measure'])

        self._address = address
#	self._term_chars = '\n\r\x04'
        self._channel_list = channel_list
        self._visains = visa.instrument(address) #, term_chars = "\n\r\x04") # Hoo Rah
        self._visains.baud_rate = 4800L
        self._visains.clear()
        # identification
#        self._idn = []
#        for idx, ch in enumerate(channel_list):
#            self._idn.append('')
#            self._visains.write('CH %i' % ch)
#            self._idn[idx] += self._visains.ask('*IDN?')
#            self._idn[idx] += self._visains.read()
#            self._idn[idx] += self._visains.read()
#        print self._idn

        if reset:
            self._visains.write("*R")               # Reset the instrument

#        self._visains.write("CH "+str(channel)) # Talking to the correct instrument
#        for psc_channel in channel_list:
        self.add_parameter('minimum_voltage', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list)
        self.add_parameter('maximum_voltage', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list)
        self.add_parameter('minimum_current', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list)
        self.add_parameter('maximum_current', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    channels=channel_list)
        self.add_parameter('voltage', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    tags=['sweep'],
                    maxstep=0.1, stepdelay=100,
                    channels=channel_list,
                    units='V')
        self.add_parameter('voltage_measured', type=types.FloatType,
                    flags=Instrument.FLAG_GET,
                    channels=channel_list,
                    units='V')
        self.add_parameter('current', type=types.FloatType,
                    flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                    tags=['sweep'],
                    maxstep=0.1, stepdelay=100,
                    channels=channel_list,
                    units='A')
        self.add_parameter('current_measured', type=types.FloatType,
                    flags=Instrument.FLAG_GET,
                    channels=channel_list,
                    units='A')

        self.add_parameter('active_channel', type=types.IntType,
                        flags=Instrument.FLAG_GET)

#        self.add_function('set_defaults')
        self.add_function('get_all')
   
        if reset:
            self.set_defaults()
        self.get_all()

    def set_defaults(self):
        '''Set default parameters.
        
        These are accurate for the ES 030-5 power supplies
        '''
        self.set_minimum_voltage1(0)
        self.set_maximum_voltage1(30)
        self.set_minimum_current1(0)
        self.set_maximum_current1(5)
        self._visains.write("REMOTE")

    def get_all(self):
#        for ch in self.get_
#        self.get_voltage()
#        self.get_current()
        self.get_active_channel()

    def do_set_minimum_voltage(self, minvol, channel):
        '''Set minimum of the voltage range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self._visains.write('CH %i' % channel)
        self._visains.write("SOUR:VOLT:MIN %.3f" % minvol)

    def do_set_maximum_voltage(self, maxvol, channel):    
        '''Set maximum of the voltage range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self._visains.write('CH %i' % channel)
        self._visains.write("SOUR:VOLT:MAX %.3f" % maxvol)

    def do_set_minimum_current(self, mincur, channel):
        '''Set minimum of the current range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self._visains.write('CH %i' % channel)
        self._visains.write("SOUR:CURR:MIN %.3f" % mincur)

    def do_set_maximum_current(self, maxcur, channel):        
        '''Set maximum of the current range

        This is a device specific parameter that is used to define the range
        that the instrument controls. Use this only to set up the instrument. 
        '''
        self._visains.write('CH %i' % channel)
        self._visains.write("SOUR:CURR:MAX %.3f" % maxcur)

    def do_set_voltage(self, V, channel):
        '''Set the output voltage of the power supply'''
        self._visains.write('CH %i' % channel)
        self._visains.write("SOU:VOLT %.3f" % V)

    def do_set_current(self, I, channel):
        '''Set the output current of the power supply'''
        self._visains.write('CH %i' % channel)
        self._visains.write("SOU:CURR %.3f" % I)

    def do_get_voltage_measured(self, channel):
#        return self._remove_EOT(self._visains.ask("MEAS:VOLT?"))
#        with self.controlled_communication:
        self._visains.write('CH %i' % channel)
        response = self._visains.ask("MEAS:VOLT?")
        return float(response.lstrip('\x04'))

    def do_get_current_measured(self, channel):
        logging.debug(__name__ + 'Get the measured current.')
#        with self.controlled_communication:
        self._visains.write('CH %i' % channel)
        response = self._visains.ask("MEAS:CURR?")
        return float(response.lstrip('\x04'))

    def do_get_active_channel(self):
        response = self._visains.ask("CH?")
        return int(response.lstrip('\x04'))

#    class controlled_communication(self):
#        self._visains.write('CH %i' % self._channel)
#        def __exit__(self):
#            pass
    

