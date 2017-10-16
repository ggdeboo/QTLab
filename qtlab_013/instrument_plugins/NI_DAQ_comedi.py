# NI_DAQ_comedi.py
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

class NI_DAQ_comedi(Instrument):
    '''
    Class implementing the NI_DAQ_comedi instrument

    Supported:
        PCI-6023E
        PCI-6289

    '''

    def __init__(self, name, id):
        Instrument.__init__(self, name, tags=['physical'])

        self._id = id
        self._boardname = comedi_lib.get_board_name(self._id)
        if not self._boardname in ['pci-6023e', 'pci-6289']:
            raise Exception('Connected board ({0})is not supported'.format(
                                self._boardname))
        logging.info('Connected device is {0}'.format(self._boardname))
        self._nsubdevices = comedi_lib.get_n_subdevices(self._id)

        print('This device has %i subdevices.' % self._nsubdevices)
        self._nchannels = []
        for subdevice in range(self._nsubdevices):
            self._nchannels.append(
                (comedi_lib.get_n_channels(self._id, subdevice),
                 comedi_lib.get_subdevice_type(self._id, subdevice),
                ))
            
#            logging.info('Subdevice {0} has {1} ranges.'.format(
#                subdevice,
#                comedi_lib.get_n_ranges(self._id, subdevice, 0)))

        # Analog inputs
        for subdevice in range(self._nsubdevices):
            if self._nchannels[subdevice][1] == 1: 
                self._default_input_range = comedi_lib.get_range(self._id, 
                                                                 subdevice, 
                                                                 0, 0)
                for ch_in in range(self._nchannels[subdevice][0]):
                    # get the first range for the channels, should be [-4.096, 4.096]
                    channel_range = comedi_lib.get_range(self._id, subdevice, ch_in, 0)
                    self.add_parameter('ai{0:d}'.format(ch_in),
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

        # Analog outputs
        for subdeviddce in range(self._nsubdevices):
            if self._nchannels[subdevice][1] == 2: 
                self._default_output_range = comedi_lib.get_range(self._id, 
                                                            subdevice, 0, 0)
                self._output_maxdata = comedi_lib.get_max_data(self._id,
                                            1,
                                            0)
                for ch_out in range(self._nchannels[subdevice][0]):
                    # get the first range for the channels, should be [-4.096, 4.096] for bipolar
                    channel_range = comedi_lib.get_range(self._id, subdevice, ch_out, 0)
                    self.add_parameter('ao{0:d}'.format(ch_out),
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

        # Digital outputs
        self.dio_subdevice = 2
        if self._nchannels[self.dio_subdevice][1] == 5:
            for ch_dio in range(self._nchannels[self.dio_subdevice][0]):
                self.add_parameter('dio{0:d}'.format(ch_dio),
                    flags=Instrument.FLAG_SET,
                    type=types.BooleanType,
                    set_func=self.do_set_dio_output,
                    channel=ch_dio)

        # The following settings should be made changeable in the future
#        self._default_input_maxdata = comedi_lib.lsampl_t(4095)
#        self._unipolar_output_range = comedi_lib.get_range(self._id,
#                                                                1, 0, 1)
#        self._default_output_maxdata = comedi_lib.lsampl_t(4095)

        self.get_all(outputs=False)

    def do_get_input(self, channel, samples=1, averaged=False,
                        sample_rate=8e3,
                        input_range=0):
        '''Get the value of the analog input

            Input:
                channel
                samples     :   number of samples
                averaged    :   True or False
                sample_rate :   Samples / second
                input_range :  
            Output:
                data (numpy float32 array)
        '''
        input_maxdata = comedi_lib.get_max_data(self._id,
                                            0,
                                            channel)
        if samples == 1:
            raw_data = comedi_lib.data_read(self._id, 
                                            0, channel, 
                                            input_range, 
                                            0)
            data = comedi_lib.convert_to_phys(
                                    self._id, 0, channel,
                                    raw_data,
#                                    self._default_input_range,
                                    input_range,
                                    input_maxdata)
            return data
        elif samples > 1:
            data = comedi_lib.data_read_n_async(self._id,
                                                0,
                                                channel,
                                                input_range,
                                                0,
                                                samples,
                                                sample_rate)
            if averaged:
                return average(data)
            else:
                return data
        else:
            logging.warning('Invalid number of samples requested')
            return False

    def do_get_output(self, channel, output_range=0):
        raw_data = comedi_lib.data_read(self._id, 1, channel, output_range, 0)
        data = comedi_lib.convert_to_phys(
                                    self._id, 1, channel,
                                    raw_data,
#                                    self._default_output_range,
                                    output_range,
                                    self._output_maxdata)
        return float(data)

    def do_set_output(self, output_value, channel,
            output_range=0):
        '''Set the output of an analog channel'''
        range_struct = comedi_lib.get_range(self._id, 1, channel, output_range)
        if output_value > float(range_struct.max):
            raise ValueError('Set value larger than range max: {0:.1f} V - {1:.1f}'.format(
                range_struct.max, output_value))
        elif output_value < float(range_struct.min):
            raise ValueError('Set value smaller than range min: {0:.1f} V - {1:.1f}'.format(
                range_struct.min, output_value))
        set_value = comedi_lib.convert_from_phys(output_value,
                                            range_struct,
                                            self._output_maxdata)
        comedi_lib.data_write(self._id, 
                                1, 
                                channel, 
                                output_range, # int
                                0, 
                                set_value)
#        self.get('ao{0}_unipolar'.format(channel))

    def do_set_dio_output(self, output_value, channel):
        '''
        Set a digital output
        '''
        # set the channel to digital output
        comedi_lib.dio_config(self._id,
                        self.dio_subdevice,
                        channel,
                        1)
        comedi_lib.dio_write(self._id, 
                         self.dio_subdevice,
                         channel,
                         output_value)       

    def get_all(self, outputs=True):
        '''When the driver is initialized there is no way of knowing what
        the output value is on the NI DAQ cards without measuring it physically
        If it has not been set before comedi returns the raw value of 0
        which gets converted to the first value of the range.
        
        '''
        ch_in = ['ai0','ai1','ai2','ai3','ai4','ai5','ai6','ai7']
        ch_out = ['ao0','ao1','ao2','ao3']
        for ch in ch_in:
            self.get(ch_in)
        if outputs:
            for ch in ch_out:
                self.get(ch_out)
