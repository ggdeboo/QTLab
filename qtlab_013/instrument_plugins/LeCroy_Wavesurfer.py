# LeCroy_Wavesurfer.py class, to perform the communication between the Wrapper and the device
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
# Timothy Lucas <t.w.lucas@gmail.com>, 2011 (Waverunner 44XS driver adapted for Wavesurfer 104MXs-A)
# Gabriele de Boo <ggdeboo@gmail.com>, 2014
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
import types
import logging
import socket
import numpy as np #added later..!
import struct
from numpy import linspace

tdiv_options = [200e-9, 500e-9]
for i in range(-9,3):
    for j in [1, 2, 5]:
        tdiv_options.append(round(j*10**i,-i))
tdiv_options.append(1000)

class LeCroy_Wavesurfer(Instrument):
    '''
    This is the python driver for the LeCroy Wavesurfer 104MXs-A
    Digital Oscilloscope

    Usage:
    Initialize with
    <name> = instruments.create('name', 'LeCroy_Wavesurfer', 
                                address='<VICP address>')
    <VICP address> = VICP::<ip-address>
    '''

    def __init__(self, name, address):
        '''
        Initializes the LeCroy Wavesurfer 104MXs-A.

        Input:
            name (string)    : name of the instrument
            address (string) : VICP address

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])
        logging.debug(__name__ + ' : Initializing instrument')
        
        self._address = address
        self._visainstrument = visa.instrument(self._address)
#        self._values = {}
        self._visainstrument.clear()

        self._idn = self._visainstrument.ask('*IDN?')
        if '104MXs' in self._idn:
            self._bandwidth = 1e9
        if '64MXs' in self._idn:
            self._bandwidth = 600e6
        if '44MXs' in self._idn:
            self._bandwidth = 400e6
        if '24MXs' in self._idn:
            self._bandwidth = 200e6

        # All wavesurfer models have 4 input channels
        self._input_channels = ['C1', 'C2', 'C3', 'C4']
        self._channels = self._input_channels + ['M1','M2','M3','M4','TA']
        self._trig_source_options = ['C1','C2','C3','C4','LINE','EX','EX10']

        #self._visainstrument.delay = 20e-3

        # Add parameters
##        self.add_parameter('timesteps', type=types.FloatType,
##                           flags = Instrument.FLAG_GETSET)
#        self.add_parameter('enhanced_resolution', type=types.FloatType,
#                             flags=Instrument.FLAG_GETSET, minval=0, maxval=3)


        for ch_in in self._input_channels:
#            self.add_parameter('enhanced_resolution_bits_'+ch_in,
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                minval=0, maxval=3,
#                get_func=self.do_get_enhanced_resolution,
#                channel=ch_in)
            self.add_parameter(ch_in+'_vdiv',
                flags=Instrument.FLAG_GETSET,
                type=types.FloatType,
                get_func=self.do_get_vdiv,
                set_func=self.do_set_vdiv,
                channel=ch_in,
                units='V')
#            self.add_parameter(ch_in+'_tdiv',
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                get_func=self.do_get_tdiv,
#                channel=ch_in,
#                units='s')
            self.add_parameter(ch_in+'_vertical_offset',
                flags=Instrument.FLAG_GETSET,
                type=types.FloatType,
                get_func=self.do_get_voffset,
                set_func=self.do_set_voffset,
                channel=ch_in,
                units='V'
                )        
            self.add_parameter(ch_in+'_trace_on_display',
                flags=Instrument.FLAG_GETSET,
                type=types.BooleanType,
                get_func=self.do_get_trace_on_display,
                set_func=self.do_set_trace_on_display,
                channel=ch_in,
                )
            self.add_parameter(ch_in+'_coupling',
                flags=Instrument.FLAG_GETSET,
                type=types.StringType,
                get_func=self.do_get_coupling,
                set_func=self.do_set_coupling,
                channel=ch_in,
                option_list=('A1M','D1M','D50','GND'),
                )
            self.add_parameter(ch_in+'_eres_bits',
                flags=Instrument.FLAG_GET,
                type=types.FloatType,
                get_func=self.do_get_eres_bits,
                channel=ch_in,
                )
            self.add_parameter(ch_in+'_eres_bandwidth',
                flags=Instrument.FLAG_GET,
                type=types.FloatType,
                get_func=self.do_get_eres_bandwidth,
                channel=ch_in,
                )

        self.add_parameter('tdiv',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            units='s',option_list=tdiv_options)
        self.add_parameter('max_memsize',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            units='S',option_list=(10000000,
                                5000000,
                                2500000,
                                1000000,
                                500000,
                                100000,
                                10000,
                                1000,
                                500))
        self.add_parameter('samplerate',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            units='S/s',option_list=(),minval=500,maxval=5e9)
        # trigger block
        self.add_parameter('trigger_source',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=tuple(self._trig_source_options),
            )
        self.add_parameter('trigger_type',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            )
        self.add_parameter('trigger_mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('AUTO','NORM','SINGLE','STOP'),
            )
        self.add_parameter('trigger_level',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            )
        self.add_parameter('trigger_slope',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            option_list=('POS','NEG')
            )

        # Math functions
        self.add_parameter('math_function',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType,
            )
        self.add_parameter('math_equation',
            flags=Instrument.FLAG_GET,
            type=types.StringType,
            )
        
        self.add_function('arm_acquisition')
        self.add_function('get_all')
        self.add_function('stop_acquisition')
        self.add_function('get_esr')
        self.add_function('get_stb')
        self.add_function('trigger')
        self.get_all()


        # Make Load/Delete Waveform functions for each channel


    # Functions

    def get_all(self):
        logging.debug(__name__ + ' : Get all.')
        for ch_in in self._input_channels:
#            logging.info(__name__ + ' : Get '+ch_in)
            self.get(ch_in+'_vdiv')
#            self.get(ch_in+'_tdiv')
            self.get(ch_in+'_vertical_offset')
            self.get(ch_in+'_trace_on_display')
            self.get(ch_in+'_coupling')
            self.get(ch_in+'_eres_bits')
            self.get(ch_in+'_eres_bandwidth')
        self.get('tdiv')
        self.get('max_memsize')
        self.get('samplerate')
        self.get_trigger_source()
        self.get_trigger_type()
        self.get_trigger_mode()
        #self.get_trigger_level()
        self.get_trigger_slope()
#            self.get_enhanced_resolution(ch_in)

#    def do_get_enhanced_resolution(self, channel):
#        '''
#        Get the number of enhanced resolution bits.
#        Input:
#            Channel name {C1, C2, C3, C4}
#        Output:
#            {0, 0.5, 1, 1.5, 2, 2.5, 3}
#        '''
#        logging.info(__name__ + ' : Get number of ERES bits.')
#        if channel in self._input_channels:
#            value = self._visainstrument.ask('ERES '+channel+'?')
#            return value
#        else:
#            raise ValueError('Channel has to be C1, C2, C3, or C4')

    def do_get_vdiv(self, channel):
        '''
        Get the volts per div.
        '''
        logging.debug(__name__ + ' : Get volts per div %s.' %channel)
        response = self._visainstrument.ask(channel+':VDIV?')
        return float(response.lstrip(channel+':VDIV').rstrip('V'))  

    def do_set_vdiv(self, vdiv, channel):
        '''
        Set the volts per division.
        '''
        logging.debug(__name__ + ' : Set the volts per div for channel %s.' %
                        channel)
        self._visainstrument.write('%s:VDIV %.3fV' % (channel, vdiv))

    def do_get_tdiv(self):
        '''
        Get the volts per div.
        '''
        logging.debug(__name__ + ' : Get time per division.')
        response = self._visainstrument.ask('TDIV?')
        return float(response.lstrip('TDIV').rstrip('S'))  
    
    def do_get_max_memsize(self):
        '''
        Get the memory size.
        '''
        response = self._visainstrument.ask('MSIZ?')
        return int(float(response.lstrip('MSIZ').rstrip('SAMPLE')))

    def do_get_samplerate(self):
        '''
        Get the sample rate.
        The minimum samplerate is 500S/s, maximum 5GS/s.
        '''
        return int(self.get_max_memsize()/(self.get_tdiv()*10))

    def do_get_voffset(self, channel):
        response = self._visainstrument.ask(channel+':OFFSET?')
        return float(response.lstrip(channel+':OFFSET').rstrip('V'))

    def do_set_voffset(self, offset, channel):
        self._visainstrument.write('%s:OFFSET %.3fV' % (channel, offset))

    def do_get_trace_on_display(self, channel):
        response = self._visainstrument.ask(channel+':TRACE?')
        if response.lstrip(channel+':TRA ') == 'ON':
            return True
        else:
            return False

    def do_set_trace_on_display(self, enable, channel):
        '''
        Set whether the trace is displayd or not
        '''
        if enable:
            self._visainstrument.write('%s:TRA ON' % channel)
        else:
            self._visainstrument.write('%s:TRA OFF' % channel)

    def do_get_coupling(self, channel):
        response = self._visainstrument.ask(channel+':CPL?')
        return response.lstrip(channel+':CPL ')

    def do_set_coupling(self, coupling, channel):
        '''
        Set the input coupling of the oscilloscope channel
        '''
        self._visainstrument.write('%s:CPL %s' % (channel, coupling))

    def do_get_trigger_mode(self):
        '''
        Get the trigger mode
        '''
        return self._visainstrument.ask('TRMD?').lstrip(' TRMD')

    def do_set_trigger_mode(self, trigger_mode):
        '''
        Set the trigger mode.
        '''
        self._visainstrument.write('TRMD %s' % trigger_mode)

    def auto_setup(self):
        '''
        Adjust vertical, timebase and trigger parameters automatically

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + 
                    ' : Auto setup of vertical, timebase and trigger')
        self._visainstrument.write('ASET')
        
        
    def screen_dump(self, file, type='JPEG', background='BLACK', 
                    dir='C:\\', area='FULLSCREEN'):
        '''
        Initiate a screen dump

        Input:
            file(str) : destination filename, auto incremented
            type(str) : image type (PSD, BMP, BMPCOMP, JPEG (default), PNG, TIFF)
            background(str) : background color (BLACK (default), WHITE)
            dir(str) : destination directory (E:\\ is the default shared folder)
            area(str) : hardcopy area (GRIDAREAONLY, DSOWINDOW, FULLSCREEN)

        Output:
            None
        '''
        logging.info(__name__ + ' : Take a screenshot with filename %s, type' + 
                            ' %s and save on harddisk %s' % (file, type, dir))
        self._visainstrument.write('HCSU DEV, %s, BCKG, %s, DEST, FILE, DIR,' 
                                    ' %s, FILE, %s, AREA, %s; SCDP' 
                                    % (type, background, dir, file, area))
        
    def do_set_tdiv(self, time):
        '''
        Set timesteps used per scale unit to the scope

        Input:
            Timesteps (eg. 1 ms = 1E-6)

        Output:
            none
        '''
        logging.info(__name__ + ' : Setting tdiv on instrument')
        self._visainstrument.write('TDIV %s' % time)
        

#    def get_timesteps(self):
#        '''
#        Set timesteps used per scale unit to the scope
#
#        Input:
#            None
#
#        Output:
#            Timesteps (eg. 1 ms = 1E-6)
#        '''
#        logging.info(__name__ + ' : Getting timebase from the instrument')
#        timebase = self._visainstrument.ask_for_values('TDIV?', format = double )
#        return timebase
        

    def get_voltage_scale(self, channel):
        '''
        Gets the voltage scale from the instrument from a specified channel

        Input:
            Channel

        Output:
            Voltage (eg. 1 ms = 1E-6)
        '''
        logging.info(__name__ + ' : Getting timebase from the instrument')
        voltage = self._visainstrument.ask('C%s:VDIV?' % channel)
        #voltage = voltage.remove(channel)
        return voltage
        

    def set_voltage_scale(self, voltage, channel):
        '''
        Set the voltage scale from the instrument from a specified channel

        Input:
            Voltage (eg. 1 ms = 1E-6), Channel

        Output:
            None
        '''
        logging.info(__name__ + ' : Getting timebase from the instrument')
        self._visainstrument.write('C%s:VDIV %s' % (channel, voltage))

    def do_get_eres_bits(self, channel):
        '''
        Get the number of ERES bits for a channel.
        Since I haven't figured out a direct command, we'll just extract it 
        from a measured waveform.
        '''
        old_memsize = self.get_max_memsize()
        self.set_max_memsize(500)
        self.arm_acquisition()
        self._visainstrument.write('COMM_FORMAT DEF9,WORD,BIN')
        rawdata = self._visainstrument.ask(channel+':WAVEFORM?')

        self.set_max_memsize(old_memsize)
        offset = 21
        nominal_bits = struct.unpack('h',rawdata[172+offset:174+offset])
        eres_bits = nominal_bits[0] - 8
        if eres_bits == 8:
            eres_bits = 0
        return eres_bits

    def do_get_eres_bandwidth(self, channel):
        '''
        Calculate the bandwidth of a channel with the enhanced resolution option.
        '''
        bits = self.do_get_eres_bits(channel)
        Nyquist = self.get_samplerate()/2
        if bits == 0:
            return Nyquist
        bw_table = {0.5:0.5, 1.0:0.241, 1.5:0.121, 2.0:0.058, 3.0:0.016}
        return bw_table[bits]*Nyquist

    def reset(self):
        '''
        Resets the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting Instrument')
        self._visainstrument.clear()

    def setup_storage(self, channel='C1', destination='HDD', mode='OFF', 
                        filetype='MATLAB'):
        '''
        Sets up the waveform storage

        Input:
            Channel = C1, C2, C3 or C4 (C1 default)
            Destination = M1, M2, M3, M4, or HDD (what memory you want to save it to)
            Mode = Off, Fill or Wrap (Off default)
            Filetype = ASCII, BINARY, EXCEL, MATCAD or MATLAB (MATLAB)

        Output:
            None
        '''
        logging.info(__name__ + ' : Setting up waveform storage')
        self._visainstrument.write('STST %s, %s, AUTO, %s, FORMAT, %s' % 
                                    (channel, destination, mode, filetype))

    def do_set_max_memsize(self, memsize):
        '''
        Starts measuring data, saves the data and sends it to the computer

        Input:
            Maximum measurement size (Inputs possible = 
            500, 1000, 10K, 100K, 500K, 1MA, 2.5MA, 5MA, 10MA)

        Output:
            None
        '''
        memsizes_list = {
            500:'500',
            1000:'1K',
            10000:'10K',
            100000:'100K',
            500e3:'500K',
            1e6:'1MA',
            2.5e6:'2.5MA',
            5e6:'5MA',
            10e6:'10MA'}
        logging.debug(__name__ + ' : Setting memory size')
        
        self._visainstrument.write('MSIZ %s' % memsizes_list[memsize])

    def measure_waveform(self):
        '''
        Starts measuring data, saves the data to the scope

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 
            5MA, 10MA, 25MA)

        Output:
            None
        '''
        logging.debug(__name__ + ' : Measuring waveform')
        #self._visainstrument.write('MSIZ %s' % memsize)
        self._visainstrument.write('ARM')
        self._visainstrument.write('TRMD SINGLE')
        #self._visainstrument.write('STO')

    def store_waveform(self):
        '''
        Starts measuring data, saves the data to the scope

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 
            5MA, 10MA, 25MA)

        Output:
            None
        '''
        logging.info(__name__ + ' : Measuring waveform')
        self._visainstrument.write('STO')

    def get_waveform_memory(self, channel, xdata=True):
        '''
        Reads out the data directly from the memory. By doing this it also 
        changes the format to 'word', which is    a 16-bit read-out, instead 
        of other possible options as 8-bit for example.

        Output:
            Ydata = numpy array with measured values
            Xdata = numpy array with x axis values
        '''
        # Need a check to figure out whether the trace is on the display.
        self._visainstrument.write('COMM_FORMAT DEF9,WORD,BIN')
        rawdata = self._visainstrument.ask(channel+':WAVEFORM?')
        #Channel can be C1, C2, C3 or C4
        data_array_start = 348
        offset = 21
        floating = 4

        Yoffset = struct.unpack('f',rawdata[160+offset:164+offset])

        Ygain = struct.unpack('f',rawdata[156+offset:156+floating+offset])

        Xgain = struct.unpack('f',rawdata[176+offset:176+floating+offset])
        nominal_bits = struct.unpack('h',rawdata[172+offset:174+offset])
        eres_bits = nominal_bits[0] - 8
        logging.debug('Number of enhanced resolution bits of channel %s is %.1f.' 
                        %(channel, eres_bits))
        
        
        datapoints = len(rawdata[data_array_start+offset:])/2.0

        if int(datapoints) == datapoints:
            lastnumber = len(rawdata)
        else:
            lastnumber = len(rawdata)-1           
        
        logging.debug('Number of datapoints according to LeCroy %s is %.1f.' 
                        % (channel, datapoints))

        data1 = struct.unpack(str(int(datapoints))+'h',
                                rawdata[data_array_start+offset:lastnumber])

        YVperDIV = {'(0,)': 1e-6, 
                    '(1,)': 2e-6, 
                    '(2,)': 5e-6, 
                    '(3,)': 10e-6, 
                    '(4,)': 20e-6, 
                    '(5,)': 50e-6, 
                    '(6,)': 100e-6, 
                    '(7,)': 200e-6, 
                    '(8,)': 500e-6, 
                    '(9,)': 1e-3, 
                    '(10,)': 2e-3, 
                    '(11,)': 5e-3, 
                    '(12,)': 10e-3, 
                    '(13,)': 20e-3, 
                    '(14,)': 50e-3, 
                    '(15,)': 100e-3, 
                    '(16,)': 200e-3, 
                    '(17,)': 500e-3, 
                    '(18,)': 1, 
                    '(19,)': 2, 
                    '(20,)': 5, 
                    '(21,)': 10, 
                    '(22,)': 20, 
                    '(23,)': 50, 
                    '(24,)': 100, 
                    '(25,)': 200, 
                    '(26,)': 500, 
                    '(27,)': 1e3}

        #YVperDIV is given in V/div.

        YVperDIVgain = YVperDIV[str(struct.unpack('h',rawdata[332+offset:334+offset]))]

        XTIMEperDIV = {'(0,)': 1e-12, 
                    '(1,)': 2e-12, 
                    '(2,)': 5e-12, 
                    '(3,)': 10e-12, 
                    '(4,)': 20e-12, 
                    '(5,)': 50e-12, 
                    '(6,)': 100e-12, 
                    '(7,)': 200e-12, 
                    '(8,)': 500e-12, 
                    '(9,)': 1e-9, 
                    '(10,)': 2e-9, 
                    '(11,)': 5e-9, 
                    '(12,)': 10e-9, 
                    '(13,)': 20e-9, 
                    '(14,)': 50e-9, 
                    '(15,)': 100e-9, 
                    '(16,)': 200e-9, 
                    '(17,)': 500e-9, 
                    '(18,)': 1e-6, 
                    '(19,)': 2e-6, 
                    '(20,)': 5e-6, 
                    '(21,)': 10e-6, 
                    '(22,)': 20e-6, 
                    '(23,)': 50e-6, 
                    '(24,)': 100e-6, 
                    '(25,)': 200e-6, 
                    '(26,)': 500e-6, 
                    '(27,)': 1e-3, 
                    '(28,)': 2e-3, 
                    '(29,)': 5e-3, 
                    '(30,)': 10e-3, 
                    '(31,)': 20e-3, 
                    '(32,)': 50e-3, 
                    '(33,)': 100e-3, 
                    '(34,)': 200e-3, 
                    '(35,)': 500e-3, 
                    '(36,)': 1, 
                    '(37,)': 2, 
                    '(38,)': 5,         
                    '(39,)': 10, 
                    '(40,)': 20, 
                    '(41,)': 50, 
                    '(42,)': 100, 
                    '(43,)': 200, 
                    '(44,)': 500, 
                    '(45,)': 1e3, 
                    '(46,)': 2e3, 
                    '(47,)': 5e3, 
                    '(100,)': 0}

        #XTIMEperDIV is given in seconds/div. WATCH OUT: EXTERNAL timing per div is not implemented in the program. The output on the X-axis will be equal to zero when external is chosen!

        XTIMEperDIVgain = XTIMEperDIV[str(struct.unpack('h',rawdata[324+offset:326+offset]))]

        Ydata = Ygain[0]*np.array(data1)-Yoffset

        Xdata = Xgain[0]*np.linspace(0,datapoints-1,datapoints, endpoint=True)

        if xdata: 
            return Xdata, Ydata
        else:
            return Ydata

    def do_get_trigger_source(self):
        '''
        Get the source for the trigger.
        '''
        logging.debug(__name__ + ' Getting the source for the trigger.')
        response = self._visainstrument.ask('TRSE?') # TRig_Select
        if response.startswith('TRSE'):
            return response.lstrip('TRSE').split(',')[2]
        else:
            raise Warning('Unexpected response to TRSE?: %s' % response)

    def do_set_trigger_source(self, channel):
        '''
        Set the source for the trigger.
        '''
        trigger_type = self.get_trigger_type()
        self._visainstrument.write('TRSE %s,SR,%s' % (trigger_type, channel))

    def do_get_trigger_type(self):
        '''
        Get the type for the trigger.

        DROP : Dropout
        EDGE : Edge
        GLIT : Glitch
        '''
        logging.debug(__name__ + ' Getting the type for the trigger.')
        response = self._visainstrument.ask('TRSE?') # TRig_Select
        if response.startswith('TRSE'):
            return response.lstrip('TRSE').split(',')[0].strip()
        else:
            raise Warning('Unexpected response to TRSE?: %s' % response)

    def do_get_trigger_level(self):
        '''
        Get the trigger level for the active trigger source.
        '''
        logging.debug(__name__ + ' Getting the trigger level.')
        response = self._visainstrument.ask('TRLV?')
        start_idx = response.index('TRLV') + 5
        end_idx = response.index('V,')
        return float(response[start_idx:end_idx])

    def do_set_trigger_level(self, trigger_level):
        '''
        Set the trigger level for the active trigger source.
        '''
        trigger_source = self.get_trigger_source()
        self._visainstrument.write('%s:TRLV %.3fV' % 
                                    (trigger_source, trigger_level))
        
    def do_get_trigger_slope(self):
        '''
        Get the trigger slope for the active trigger source.
        '''
        logging.debug(__name__ + ' Getting the trigger slope.')
        trig_source = self.get_trigger_source()
        response = self._visainstrument.ask('TRSL?')
        return response.lstrip('%s:TRSL ' % trig_source)

    def do_set_trigger_slope(self, slope):
        '''
        Set the trigger slope for the active trigger source.
        '''
        trigger_channel = self.get_trigger_source()
        self._visainstrument.write('%s:TRSL %s' % (trigger_channel, slope))

    def arm_acquisition(self):
        '''
        Send the ARM_ACQUISITION command. 
        This arms the scope and forces a single acquisition.
        '''
        self._visainstrument.write('ARM_ACQUISITION')

    def stop_acquisition(self):
        '''
        Stop the acquisition.
        '''
        self._visainstrument.write('STOP')

    def get_esr(self):
        '''
        Read out the Event Status Register 
        '''
        return self._visainstrument.ask('*ESR?')

    def get_stb(self):
        '''
        Read out the Event Status Register 
        '''
        return self._visainstrument.ask('*STB?')

    def trigger(self):
        self._visainstrument.write('*TRG')

    def _get_math_string(self, channel):
        '''
        '''
        if channel not in self._channels:
            raise ValueError('Wavesurfer: channel not allowed.')

        return self._visainstrument.ask('%s:DEF?' % channel)

    def do_get_math_equation(self):
        '''Get the equation for the math channel'''
        math_string = self._get_math_string('TA').split(',')
        return math_string[1]

    def do_get_math_function(self):
        '''Get the function for the math channel'''
        return self._get_math_string('TA').lstrip('F1:DEF ')

    def do_set_math_function(self, math_string):
        '''Set the function for the math channel

        Examples:
        EQN,"AVG(C1)",AVERAGETYPE,CONTINUOUS,SWEEPS,10 SWEEP,INVALIDINPUTPOLICY,RESET
        EQN,"AVG(C1)",AVERAGETYPE,CONTINUOUS,SWEEPS,10 SWEEP,INVALIDINPUTPOLICY,SKIP
        EQN,"AVG(C1)",AVERAGETYPE,SUMMED,SWEEPS,10 SWEEP,INVALIDINPUTPOLICY,SKIP
        EQN,"ABS(C1)"
        EQN,"DERI(C1)",VERSCALE,2 V/S, VEROFFSET,-384E-3 V/S,ENABLEATOSCALE,ON'
            
        '''
        self._visainstrument.write('TA:DEF %s' % math_string)

    def clear_sweeps(self):
        '''Clears the sweeps in the math section'''
        self._visainstrument.write('CLSW')


# Next thing doesn't work yet, because in the transfer to the instrument visa throws away the \' needed to specify what file to get... Do not know how to solve this...
# Also, remember that you need qt lab to wait until we are sure that the entire waveform for the specified time is 
##    def receive_file(self, destination_filename, channel='1', filetype='MATLAB'):
##        '''
##        Receives the measured data from the scope, saves the file, then deletes the file from the scope
##
##        Input:
##            Filename (is generic, so should not be such a problem)
##            Channel from which measurement was just taken
##            filetype which was specified in setup_storage (in capitals!)
##            The name of the file to which is should be saved
##
##        Output:
##            The measurement in a prespecified filetype
##        '''
##        logging.info(__name__ + ' : Receiving & Deleting data from scope')
##        if filetype == 'MATLAB':
##            extension = '.dat'
##        elif filetype == 'ASCII':
##            extension = '.txt'
##        elif filetype == 'BINARY':
##            extension = '.trc'
##        elif filetype == 'EXCEL':
##            extension = '.csv'
##        elif filetype == 'MATCAD':
##            extension = '.prn'
##        
##        FILE = destination_filename+extension
##        filepath = 'D:\\xtalk\\C%sxtalk_chndir200000' %channel
##        filepath = filepath+extension
##        print 'TRFL DISK, HDD, FILE,  \' %s \' ' % filepath
##        data = self._visainstrument.ask('TRFL DISK, HDD, FILE,\'%s\'' % filepath)
##        FILE.write(data)
##        FILE.close()
##        self._visainstrument.write('DELF, DISK, HDD, FILE,\'%s\'' %filepath)
        
