# Metatdata.py class, to store sample related metadata
# Sam Gorman <samuel.gorman@student.unsw.edu.au>, 2013
# Sam Hile <samhile@gmail.com> 2013
# Charley Peng <cpeng92@gmail.com> 2013
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
import logging

class x_Metadata(Instrument):
    '''
    This is the python driver for the metadate faux-instrument

    Usage:
    Initialize with
    <name> = instruments.create('name', 'x_Metadata')

    TODO:
    1) multi line textbox for user.
    -> will have to change gui/frontpanel.py
    
    Store Metadata on 
        User
        Notes
        Time            
        Device Number        
    '''

    def __init__(self, name, reset=False):
        '''
        Initializes the metadata thingy.

        Input:
            name (string)    : name of the instance

        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing meta')
        Instrument.__init__(self, name, tags=['virtual'])

        self.add_parameter('user', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET | \
              Instrument.FLAG_PERSIST)
        self.add_parameter('notes', type=types.FileType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET | \
              Instrument.FLAG_PERSIST)
        self.add_parameter('device', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET | \
              Instrument.FLAG_PERSIST)
        self.add_parameter('dip', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET | \
              Instrument.FLAG_PERSIST)            
        self.add_parameter('time', type=types.StringType,
            flags=Instrument.FLAG_GET)   
            
        # self.add_function('do_get_user')
        # self.add_function('do_set_user')
        
        # self.add_function('do_get_notes')
        # self.add_function('do_set_notes')
        
        # self.add_function('do_get_device')
        # self.add_function('do_set_device')
        
        # self.add_function('do_get_dip')
        # self.add_function('do_set_dip')              
        
        # self.add_function('do_get_time')
        
        if reset:
            self.reset()
        else:
            self.get_all()
        self._dip = ''
        self._exp = ''
        self._notes = ''
        self._user = ''

    def get_all(self):
        '''
        Reads all implemented parameters that have been set,
        and updates the wrapperself.

        Input:
            None

        Output:
            None
        '''
        logging.info('reading all settings from metadata instrument')               
        # TODO ? is this necessary

    def do_get_time(self):
        '''
        Returns the current time in this format
        %a, %d %b %Y %H:%M:%S
        '''
        import time        
        logging.info("returning the current time")
        return time.strftime("%a, %d %b %Y %H:%M:%S",time.localtime())

           
        
    def do_get_user(self):
        '''
        Returns the user

        Input:
            none

        Output:
            user (string)
        '''        
        return self._user
        
    def do_set_user(self, val):
        '''
        Set user to val

        Input:
            user (str)

        Output:
            None
        '''
        self._user = str(val)

    def do_get_notes(self):
        '''
        Returns the notes

        Input:
            none

        Output:
            notes (string)
        '''
        logging.debug(__name__ + ' : getting notes')        
        return self._notes
        
    def do_set_notes(self, val):
        '''
        Set notes to val

        Input:
            None

        Output:
            None
        '''
        self._notes = str(val)
        
        
    def do_get_dip(self):
        '''
        Returns the dip number

        Input:
            none

        Output:
            dip (string)
        '''
        logging.debug(__name__ + ' : getting dip')        
        return self._dip
        
    def do_set_dip(self, val):
        '''
        Set dip notes to val

        Input:
            Dip.

        Output:
            None
        '''
        self._dip = str(val)
    
    def do_get_device(self):
        '''
        Returns the device

        Input:
            none

        Output:
            notes (string)
        '''
        logging.debug(__name__ + ' : getting experiment')        
        return self._exp
        
    def do_set_device(self, val):
        '''
        Set device to val

        Input:
            device (str)

        Output:
            None
        '''
        self._exp = str(val)