# USB_DUX.py
# Gabriele de Boo <ggdeboo@gmail.com>
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
from instrument import Instrument
import qt
import logging
from numpy import asarray, average, ndarray

from lib.dll_support import comedi as comedi_lib

class USB_DUX(Instrument):
    '''
    Class implementing the USB_DUX instrument

    The USB-DUX-D operated using the comedi driver has 5 subdevices:
        0 : analog input    8 channels  12 bits
        1 : analog output   4 channels  12 bits
        2 : digital I/O     8 channels
        3 : counter         4 channels  max value 65535
        4 : pwm             8 channels  max value 512

    '''

    def __init__(self, name, id):
        Instrument.__init__(self, name, tags=['physical'])

        self._id = id
        self._boardname = comedi_lib.get_board_name(self._id)
        if self._boardname != 'usbdux':
            raise Exception('Connected board is not usbdux, but "{0}"'.format(
                                self._boardname))
        self._nsubdevices = comedi_lib.get_n_subdevices(self._id)

        print('This device has %i subdevices.' % self._nsubdevices)
        self._nchannels = []
        for subdevice in range(self._nsubdevices):
            self._nchannels.append(comedi_lib.get_n_channels(self._id, 
                                                                subdevice))
            logging.info('Subdevice {0} has {1} ranges.'.format(
                subdevice,
                comedi_lib.get_n_ranges(self._id, subdevice, 0)))

        for ch_in in range(self._nchannels[0]):
            # get the first range for the channels, should be [-4.096, 4.096]
            channel_range = comedi_lib.get_range(self._id, 0, ch_in, 0)
            self.add_parameter(('ai%i'%ch_in),
                flags=Instrument.FLAG_GET,
                type=ndarray,
                units='V',
                tags=['measure'],
                get_func=self.do_get_input,
                channel=ch_in,
                minval=channel_range.min,
                maxval=channel_range.max,
                format='%0.4f',
                )

        for ch_out in range(self._nchannels[1]):
            # get the first range for the channels, should be [-4.096, 4.096] for bipolar
            channel_range = comedi_lib.get_range(self._id, 1, ch_out, 0)
            self.add_parameter(('ao%i_bipolar'%ch_out),
                flags=Instrument.FLAG_GETSET,
                type=types.FloatType,
                units='V',
                tags=['measure'],
                get_func=self.do_get_output,
                set_func=self.do_set_output,
                channel=ch_out,
                minval=channel_range.min,
                maxval=channel_range.max,
                format='%0.4f',
                maxstep=0.010, stepdelay=50.0,
                )

        for ch_out in range(self._nchannels[1]):
            # get the first range for the channels, should be [0.0, 4.096]
            # for unipolar
            channel_range = comedi_lib.get_range(self._id, 1, ch_out, 1)
            self.add_parameter(('ao%i_unipolar'%ch_out),
                flags=Instrument.FLAG_GETSET,
                type=types.FloatType,
                units='V',
                tags=['measure'],
                get_func=self.do_get_output_unipolar,
                set_func=self.do_set_output_unipolar,
                channel=ch_out,
                minval=channel_range.min,
                maxval=channel_range.max,
                format='%0.4f',
                maxstep=0.010, stepdelay=50.0,
                )

        # The following settings should be made changeable in the future
        self._default_input_range = comedi_lib.get_range(self._id, 
                                                                0, 0, 0)
        self._default_input_maxdata = comedi_lib.lsampl_t(4095)
        self._default_output_range = comedi_lib.get_range(self._id, 
                                                                1, 0, 0)
        self._unipolar_output_range = comedi_lib.get_range(self._id,
                                                                1, 0, 1)
        self._default_output_maxdata = comedi_lib.lsampl_t(4095)

        self.get_all()

    def do_get_input(self, channel, samples=1, averaged=False,
                        sample_rate=8e3,
                        input_range=0):
        '''Get the value of the analog input

            Input:
                channel
                samples     :   number of samples
                averaged    :   True or False
                sample_rate :   Samples / second
                input_range :   0  [-4.096 V, 4.096 V]
                                1  [-2.048 V, 2.048 V]
                                2  [ 0.0   V, 4.096 V]
                                3  [ 0.0   V, 2.048 V]
            Output:
                data (numpy float32 array)
        '''
        if samples == 1:
            raw_data = comedi_lib.data_read(self._id, 
                                            0, channel, 
                                            input_range, 
                                            0)
            data = comedi_lib.convert_to_phys(raw_data,
                                    self._default_input_range,
                                    self._default_input_maxdata)
            return data
        elif samples > 1:
#            data =  comedi_lib.data_read_n(self._id,
#                                                0, channel, 0, 0, 
#                                                samples)
            if sample_rate > 2e3:
                # The daq needs 0.5 ms to set up, which messes up the first
                # samples in fast measurements.
                offset = 2
            else:
                offset = 0
            data = comedi_lib.data_read_n_async(self._id,
                                                0,
                                                channel,
                                                input_range,
                                                0,
                                                samples + offset,
                                                sample_rate)
            if averaged:
                return average(data[offset:])
            else:
                return data[offset:]
        else:
            logging.warning('Invalid number of samples requested')
            return False

    def do_get_output(self, channel):
        raw_data = comedi_lib.data_read(self._id, 1, channel, 0, 0)
        data = comedi_lib.convert_to_phys(raw_data,
                                    self._default_output_range,
                                    self._default_output_maxdata)
        return float(data)

    def do_get_output_unipolar(self, channel):
        raw_data = comedi_lib.data_read(self._id, 1, channel, 1, 0)
        data = comedi_lib.convert_to_phys(raw_data,
                                    self._unipolar_output_range,
                                    self._default_output_maxdata)
        return float(data)

    def do_set_output(self, output_value, channel):
        '''Set the output of an analog channel'''
        set_value = comedi_lib.convert_from_phys(output_value,
                                    self._default_output_range,
                                    self._default_output_maxdata)
        comedi_lib.data_write(self._id, 1, channel, 0, 0, set_value)
        self.get('ao{0}_unipolar'.format(channel))

    def do_set_output_unipolar(self, output_value, channel):
        '''Set the output of an analog channel'''
        set_value = comedi_lib.convert_from_phys(output_value,
                                    self._unipolar_output_range,
                                    self._default_output_maxdata)
        comedi_lib.data_write(self._id, 1, channel, 0, 0, set_value)
        self.get('ao{0}_bipolar'.format(channel))
        
    def get_all(self):
        ch_in = ['ai0','ai1','ai2','ai3','ai4','ai5','ai6','ai7']
        ch_out = ['ao0_bipolar','ao1_bipolar','ao2_bipolar','ao3_bipolar',
                 'ao0_unipolar','ao1_unipolar','ao2_unipolar','ao3_unipolar']
        for ch in ch_in:
            self.get(ch_in)
        for ch in ch_out:
            self.get(ch_out)
