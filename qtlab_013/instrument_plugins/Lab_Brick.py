# Lab_Brick.py, Vaunix Lab Brick instrument driver
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

import types
import ctypes
from lib.dll_support import labbrick
from instrument import Instrument
import logging
import sys
#import qt
#import numpy as np


class Lab_Brick(Instrument):
    '''
    This is a driver for Lab Brick frequency synthesizers. It is not finished yet and therefore not stable. If you load it more than once in a single QTlab instance, it will fail to communicate with the instrument.
    '''

    def __init__(self, name, id=0, reset=False):
        Instrument.__init__(self, name, tags=['physical'])
        
        labbrick.init()
        labbrick.set_testmode(True)
        logging.info('Number of labbrick devices configured: %i.' %labbrick.get_numdevices())
        labbrick.set_testmode(False)
        logging.info('Number of labbrick devices configured: %i.' %labbrick.get_numdevices())
        active_devices = labbrick.get_activedevices()
        logging.info('Number of labbrick devices found: %i.' %len(active_devices))
        self._id = active_devices[id]
        logging.info('Device id: %i.' %self._id)
        logging.info('Initializing lab brick...')
#        for device in labbrick.activeDevices:
#            sys.stdout.write(str(device))
        sys.stdout.write('\n')
        labbrick.init_device(self._id)

        self._modelname = labbrick.get_modelname(self._id)
        logging.info('Lab brick model connected: %s' % self._modelname)
	minfreq = labbrick.get_min_frequency(self._id)
	maxfreq = labbrick.get_max_frequency(self._id)
	minpower = labbrick.get_min_power(self._id)*0.25
	maxpower = labbrick.get_max_power(self._id)*0.25
            
        self.add_parameter('frequency',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            units='Hz',
	    minval=minfreq,
	    maxval=maxfreq)
	self.add_parameter('power',
            flags=Instrument.FLAG_GETSET,
	    type=types.FloatType,
	    units='dBm',
	    minval=minpower,
	    maxval=maxpower)
        self.add_parameter('sweep_start_frequency',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            units='Hz')

        self.add_function('reset')
        self.add_function('close')

        if reset:
            self.reset()
        else:
            self.get_all()

    def get_all(self):
        self.get_frequency()
	self.get_power()
        self.get_sweep_start_frequency()

    def reset(self):
        '''Reset device.'''

    def do_get_frequency(self):
        '''Get the frequency.'''
        return labbrick.get_frequency(self._id)

    def do_set_frequency(self, freq):
        '''
        Set the frequency.
        Smallest unit is 10 Hz.
        '''
        labbrick.set_frequency(self._id, int(round(freq, -1))) 

    def do_get_power(self):
        '''
        Get the power. The called function returns the power in .25 dB units.
        '''
        power = labbrick.get_power_level(self._id)
        return power/4.0

    def do_set_power(self, power):
        '''
	Set the power.
	'''
	labbrick.set_power_level(self._id, power*4)

    def do_get_sweep_start_frequency(self):
        '''Get the start frequency for a sweep.'''
        return labbrick.get_start_frequency(self._id)

    def do_set_sweep_start_frequency(self):
        '''Set the start frequency for a sweep.'''
        labbrick.set_start_frequency(self._id, int(round(freq, -1)))

    def close(self):
        '''
        Close the labbrick connection.
        '''
        labbrick.close_device(self._id)
