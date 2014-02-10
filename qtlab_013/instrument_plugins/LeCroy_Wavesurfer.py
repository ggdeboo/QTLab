# LeCroy_Wavesurfer.py class, to perform the communication between the Wrapper and the device
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
# Timothy Lucas <t.w.lucas@gmail.com>, 2011 (Waverunner 44XS driver adapted for Wavesurfer 104MXs-A)
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

class LeCroy_Wavesurfer(Instrument):
    '''
    This is the python driver for the LeCroy Wavesurfer 104MXs-A
    Digital Oscilloscope

    Usage:
    Initialize with
    <name> = instruments.create('name', 'LeCroy_Wavesurfer', address='<VICP address>')
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
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._values = {}
        self._visainstrument.clear()
        #self._visainstrument.delay = 20e-3

        # Add parameters
##        self.add_parameter('timesteps', type=types.FloatType,
##                           flags = Instrument.FLAG_GETSET)


        # Make Load/Delete Waveform functions for each channel


    # Functions

    def set_trigger_normal(self):
        '''
        Change the trigger mode to Normal.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set trigger to normal')
        self._visainstrument.write('TRMD NORMAL')
      

    def set_trigger_auto(self):
        '''
        Change the trigger mode to Auto.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set trigger to auto')
        self._visainstrument.write('TRMD AUTO')
       

    def auto_setup(self):
        '''
        Adjust vertical, timebase and trigger parameters automatically

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Auto setup of vertical, timebase and trigger')
        self._visainstrument.write('ASET')
        
        
    def screen_dump(self, file, type='JPEG', background='BLACK', dir='C:\\', area='FULLSCREEN'):
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
        logging.info(__name__ + ' : Take a screenshot with filename %s, type %s and save on harddisk %s' % (file, type, dir))
        self._visainstrument.write('HCSU DEV, %s, BCKG, %s, DEST, FILE, DIR, %s, FILE, %s, AREA, %s; SCDP' % (type, background, dir, file, area))
        
    def set_timesteps(self, time):
        '''
        Set timesteps used per scale unit to the scope

        Input:
            Timesteps (eg. 1 ms = 1E-6)

        Output:
            none
        '''
        logging.info(__name__ + ' : Acquiring timesteps from instrument')
        self._visainstrument.write('TDIV %s' % time)
        

    def get_timesteps(self):
        '''
        Set timesteps used per scale unit to the scope

        Input:
            None

        Output:
            Timesteps (eg. 1 ms = 1E-6)
        '''
        logging.info(__name__ + ' : Getting timebase from the instrument')
        timebase = self._visainstrument.ask_for_values('TDIV?', format = double )
        return timebase
        

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

    def setup_storage(self, channel='C1', destination='HDD', mode='OFF', filetype='MATLAB'):
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
        self._visainstrument.write('STST %s, %s, AUTO, %s, FORMAT, %s' % (channel, destination, mode, filetype))

    def set_memsize(self, memsize):
        '''
        Starts measuring data, saves the data and sends it to the computer

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 5MA, 10MA, 25MA)
            

        Output:
            None
        '''
        logging.info(__name__ + ' : Setting memory size')
        self._visainstrument.write('MSIZ %s' % memsize)

    def measure_waveform(self):
        '''
        Starts measuring data, saves the data to the scope

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 5MA, 10MA, 25MA)
            

        Output:
            None
        '''
        logging.info(__name__ + ' : Measuring waveform')
        #self._visainstrument.write('MSIZ %s' % memsize)
        self._visainstrument.write('ARM')
        self._visainstrument.write('TRMD AUTO')
        #self._visainstrument.write('STO')

    def store_waveform(self):
        '''
        Starts measuring data, saves the data to the scope

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 5MA, 10MA, 25MA)
            

        Output:
            None
        '''
        logging.info(__name__ + ' : Measuring waveform')
        self._visainstrument.write('STO')

        
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
        
