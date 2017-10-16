import ctypes
import logging
from numpy import zeros, float32, frombuffer, uint16, uint32, isnan
from scipy import nan
from struct import unpack

comedi = ctypes.cdll.LoadLibrary("libcomedi.so")
libc = ctypes.CDLL("libc.so.6")

AREF_GROUND = 0x00
AREF_COMMON = 0x01
AREF_DIFF   = 0x02
AREF_OTHER  = 0x03

TRIG_NONE	= 0x00000001	# never trigger 
TRIG_NOW    = 0x00000002
TRIG_FOLLOW	= 0x00000004	# trigger on next lower level trig 
TRIG_TIME	= 0x00000008	# trigger at time N ns 
TRIG_TIMER	= 0x00000010	# trigger at rate N ns 
TRIG_COUNT	= 0x00000020	# trigger when count reaches N 
TRIG_EXT	= 0x00000040	# trigger on external signal N 
TRIG_INT	= 0x00000080	# trigger on comedi-internal signal N 

SDF_LSAMPL  = 0x10000000    # subdevice flag when lsampl_t is 32 bit
SDF_SOFT_CALIBRATED = 0x2000 

COMEDI_INPUT = 0
COMEDI_OUTPUT = 1

def CR_PACK(chan, rng, aref):
    return ((((aref) & 0x3) << 24) | (((rng) & 0xff) << 16) | (chan))

sampl_t = ctypes.c_ushort
lsampl_t = ctypes.c_uint

class comedi_t(ctypes.Structure):
    pass

class comedi_range(ctypes.Structure):
     _fields_ = [("min", ctypes.c_double),
                ("max", ctypes.c_double),
                ("unit", ctypes.c_uint)] 

class comedi_cmd(ctypes.Structure):
    _fields_ = [
               ("subdev", ctypes.c_uint),
               ("flags", ctypes.c_uint),
               ("start_src", ctypes.c_uint),
               ("start_arg", ctypes.c_uint),
               ("scan_begin_src", ctypes.c_uint),
               ("scan_begin_arg", ctypes.c_uint),
               ("convert_src", ctypes.c_uint),
               ("convert_arg", ctypes.c_uint),
               ("scan_end_src", ctypes.c_uint),
               ("scan_end_arg", ctypes.c_uint),
               ("stop_src", ctypes.c_uint),
               ("stop_arg", ctypes.c_uint),

               ("chanlist", ctypes.POINTER(ctypes.c_uint)),
               ("chanlist_len", ctypes.c_uint),
               ("data", ctypes.POINTER(sampl_t)),
               ("data_len", ctypes.c_uint)]

class comedi_polynomial_t(ctypes.Structure):
    _fields_ = [
                ("coefficients", ctypes.c_double * 4),
                ("expansion_origin", ctypes.c_double),
                ("order", ctypes.c_uint)
            ]

class comedi_caldac_t(ctypes.Structure):
    __fields__ = [
                ("subdevice", ctypes.c_uint),
                ("channel", ctypes.c_uint),
                ("value", ctypes.c_uint)
            ]

class comedi_softcal_t(ctypes.Structure):
    __fields__ = [
                ("to_phys", ctypes.POINTER(comedi_polynomial_t)),
                ("from_phys", ctypes.POINTER(comedi_polynomial_t))
            ]

class comedi_calibration_settings_t(ctypes.Structure):
    __fields__ = [
                ("subdevice", ctypes.c_uint),
                ("channels", ctypes.POINTER(ctypes.c_uint)),
                ("num_channels", ctypes.c_uint),
                ("ranges", ctypes.POINTER(ctypes.c_uint)),
                ("num_ranges", ctypes.c_uint),
                ("arefs", ctypes.c_uint * 4),
                ("num_arefs", ctypes.c_uint),
                ("caldacs", ctypes.POINTER(comedi_caldac_t)),
                ("num_caldacs", ctypes.c_uint),
                ("soft_calibration", comedi_softcal_t)
            ]

class comedi_calibration_t(ctypes.Structure):
    __fields__ = [
                ("driver_name", ctypes.POINTER(ctypes.c_char)),
                ("board_name", ctypes.POINTER(ctypes.c_char)),
                ("settings", ctypes.POINTER(comedi_calibration_settings_t)),
                ("num_settings", ctypes.c_uint)
            ]



#comedi.comedi_open.restype = ctypes.pointer(comedi_t)
comedi.comedi_get_range.restype = ctypes.POINTER(comedi_range)
comedi.comedi_get_n_ranges.restype          = ctypes.c_int
comedi.comedi_get_board_name.restype = ctypes.c_char_p
comedi.comedi_get_cmd_generic_timed.restype = ctypes.c_int
comedi.comedi_to_phys.restype = ctypes.c_double
comedi.comedi_to_physical.restype = ctypes.c_double
comedi.comedi_to_physical.argtype           = [lsampl_t,
                                               ctypes.POINTER(comedi_polynomial_t)]
comedi.comedi_from_phys.restype = lsampl_t
comedi.comedi_command.restype               = ctypes.c_int
comedi.comedi_command_test.restype          = ctypes.c_int
comedi.comedi_to_phys.restype               = ctypes.c_double
comedi.comedi_to_phys.argtype               = [lsampl_t, 
                                              ctypes.POINTER(comedi_range), 
                                              lsampl_t]
comedi.comedi_get_max_buffer_size.restype   = ctypes.c_int
comedi.comedi_get_max_buffer_size.argtype   = [ctypes.POINTER(comedi_t),
                                                ctypes.c_uint]
comedi.comedi_get_buffer_size.restype   = ctypes.c_int
comedi.comedi_get_buffer_size.argtype   = [ctypes.POINTER(comedi_t),
                                                ctypes.c_uint]
comedi.comedi_get_buffer_offset.restype   = ctypes.c_int
comedi.comedi_get_buffer_offset.argtype   = [ctypes.POINTER(comedi_t),
                                                ctypes.c_uint]
comedi.comedi_get_subdevice_type.restype        = ctypes.c_int
comedi.comedi_get_subdevice_type.argtype        = [ctypes.POINTER(comedi_t),
                                                    ctypes.c_uint]
comedi.comedi_get_subdevice_flags.restype       = ctypes.c_int
comedi.comedi_get_subdevice_flags.argtype       = [ctypes.POINTER(comedi_t),
                                                    ctypes.c_uint]
#comedi.comedi_get_hardcal_convertor.restype     = ctypes.c_int
comedi.comedi_get_default_calibration_path.restype  = ctypes.c_char_p
comedi.comedi_get_softcal_converter.restype = ctypes.c_int
comedi.comedi_parse_calibration_file.restype = ctypes.POINTER(comedi_calibration_t)
comedi.comedi_get_softcal_converter.argtype     = [ctypes.c_uint,
                                                    ctypes.c_uint,
                                                    ctypes.c_uint,
                                                    ctypes.c_uint, #enum
                                                    ctypes.POINTER(comedi_calibration_t),
                                                    ctypes.POINTER(comedi_polynomial_t)]
comedi.comedi_dio_write.argtype = [ctypes.POINTER(comedi_t),
                                   ctypes.c_uint,
                                   ctypes.c_uint,
                                   ctypes.c_uint]
comedi.comedi_dio_write.restype = ctypes.c_int
comedi.comedi_dio_config.argtype = [ctypes.POINTER(comedi_t),
                                    ctypes.c_uint,
                                    ctypes.c_uint,
                                    ctypes.c_uint]
comedi.comedi_dio_config.restype = ctypes.c_int

# out of range behaviour: give a number, not a nan
comedi.comedi_set_global_oor_behavior(0)

def convert_to_phys(device_id, subdevice, channel,
                    data_value, channel_range, maxdata):
    '''Converts a data_value to a physical value.

    Input:
        data_value (tuple or float)
        channel_range
        maxdata

    Output:
        numpy array float
    '''
    if type(data_value) == tuple:
        physical_values = zeros(len(data_value))
    elif type(data_value) == long:
        physical_values = zeros(1)
        data_value = (data_value,)

    softcal = False
    if softcal:
        cal_file = get_default_calibration_path(device_id)
        calibration = parse_calibration_file(cal_file)
        conversion_polynomial = comedi_polynomial_t()
        comedi.comedi_get_softcal_converter(
                        ctypes.c_uint(subdevice),
                        ctypes.c_uint(channel),
                        ctypes.c_uint(channel_range),
                        0, # direction enum COMEDI_TO_PHYS
                        calibration,
                        ctypes.byref(conversion_polynomial))
                                          
        for idv, value in enumerate(data_value):
            if value > maxdata:
                raise ValueError('Value can not be larger than maxdata')
            elif value < 0:
                raise ValueError('Value can not be negative')
            elif (value == maxdata) or (value == 0):
                logging.debug('DAQ: hit the limit of the range.')
            physical_value = comedi.comedi_to_physical(
                            lsampl_t(value),
                            ctypes.byref(conversion_polynomial), 
                            )
            # check whether a nan is returned
            # out of range behaviour
            if not isnan(physical_value):
                physical_values[idv] = physical_value
            else:
                raise Exception('convert to phys failed')
        comedi.comedi_cleanup_calibration(calibration)

    else:
        channel_range_struct = get_range(device_id,
                                            subdevice,
                                            channel,
                                            channel_range)
        for idv, value in enumerate(data_value):
            if value > maxdata:
                raise ValueError('Value can not be larger than maxdata')
            elif value < 0:
                raise ValueError('Value can not be negative')
            elif (value == maxdata) or (value == 0):
                logging.debug('DAQ: hit the limit of the range.')
            physical_value = comedi.comedi_to_phys(lsampl_t(value),
                        ctypes.pointer(channel_range_struct), 
                        maxdata)
            # check whether a nan is returned
            # out of range behaviour
            if not isnan(physical_value):
                physical_values[idv] = physical_value
            else:
                raise Exception('convert to phys failed')

    if type(data_value) == tuple:
        return physical_values
    elif type(data_value) == float:
        return physical_values[0]

def convert_from_phys(physical_value, channel_range, maxdata):
    '''returns a c_double with the number that can be used by data_write'''
    return comedi.comedi_from_phys(ctypes.c_double(physical_value),
                                    ctypes.pointer(channel_range),
                                    maxdata)

def data_read(device_id, subdevice, channel, channel_range, aref):
    '''Return a single reading'''
    raw_data = ctypes.c_uint()
    with device_operation(device_id) as device:
        rc = comedi.comedi_data_read(device,
                                        subdevice,
                                        channel,
                                        channel_range, # int
                                        aref,
                                        ctypes.byref(raw_data))
    if rc == 1:
        return raw_data.value
    else:
        logging.warning('data_read was not successful')
        return False

def data_read_n(device_id, subdevice, channel, channel_range, aref, samples):
    '''
    Return multiple reading

    This function returns unevenly spaced readings in a single numpy array
    '''
    raw_data_type = ctypes.c_uint * samples
    raw_data = raw_data_type()
    
    channel_range_struct = get_range(device_id,
                                            subdevice,
                                            channel,
                                            channel_range)

    channel_max_data = get_max_data(device_id,
                                    subdevice,
                                    channel)
    
    with device_operation(device_id) as device:
        rc = comedi.comedi_data_read_n(device,
                                       subdevice,
                                       channel,
                                       channel_range, # int
                                       aref,
                                       ctypes.byref(raw_data),
                                       samples)
    if rc == 0:
        data = zeros((samples), dtype=float32)
        for idx, value in enumerate(raw_data):
            data[idx] = convert_to_phys(
                            device_id,
                            subdevice,
                            channel,
                            value,
                            channel_range,
                            channel_max_data)
        return data
    else:
        logging.warning('data_read was not successful')
        return False 

def data_read_n_async(device_id, subdevice, channel, channel_range, aref, 
    samples, sample_rate):
    '''Perform a synchronous acquisition at a specified sample rate
   
    Input:
        device_id       :   typically '/dev/comedi0'
        subdevice       :   For USB-DUX-D analog in is subdevice 0
        channel         :   input channel (0-7) for USB-DUX-D
        channel_range   :   input range
       *aref            :   not used?
        samples         :   number of samples
        sample_rate     :   sample_rate

       *not implemented yet...

    Output:
        numpy array with length of number of samples


    Problems:
        samples > buffer_size (65k) doesn't work
        The device needs 2 * 0.125 ms before good samples come out
        At 4 kS/s the first sample is bad
        At 8 kS/s the first two samples are bad
    '''
    device = comedi.comedi_open(device_id)
    cmd = comedi_cmd()
    scan_period_ns = int(1e9/sample_rate)   # scan_period_ns
    result = comedi.comedi_get_cmd_generic_timed(
                          device,                               # device
                          subdevice,                            # subdevice
                          ctypes.byref(cmd),                    # command
                          1,                                    # chanlist_len
                          ctypes.c_uint(scan_period_ns)
                          )  
    if result < 0:
        logging.error('comedi_get_cmd_generic_timed failed')
        return False

    chanlist = (ctypes.c_uint * 1)(
            CR_PACK(channel, channel_range, AREF_GROUND))
    cmd.chanlist = ctypes.cast(chanlist, 
                                    ctypes.POINTER(ctypes.c_uint)
                                   )
    # Acquisition stops when
    cmd.stop_src = TRIG_COUNT
    # For some reason the first 2 samples are not right
    cmd.stop_arg = samples

    result = comedi.comedi_command_test(
                          device,
                          ctypes.byref(cmd))
    if result < 0:
        logging.error('comedi_command_test failed')
        comedi.comedi_close(device_id)
        return False
    elif result > 0:
        print('Command test: {0}'.format(result))

    result = comedi.comedi_command_test(
                          device,
                          ctypes.byref(cmd))
    if result < 0:
        logging.error('comedi_command_test 2 failed')
        comedi.comedi_close(device_id)
        return False
    elif result > 0:
        print('Command test: {0}'.format(result))

    # Check what the sample rate of the comedi command is.
    if scan_period_ns < cmd.scan_begin_arg:
        logging.info('Sample rate changed to maximum ({0:.1f} kS/s).'.format(
            1/(cmd.scan_begin_arg/1e6)))

    # This starts the acquisition
    result = comedi.comedi_command(device, 
                            ctypes.byref(cmd))
    if result < 0:
        logging.error('comedi_command failed')
        comedi.comedi_close(device_id)
        return False

    fileno = comedi.comedi_fileno(device)

    BUFSIZE = comedi.comedi_get_buffer_size(device, subdevice)
    buf = (ctypes.c_char * BUFSIZE)()
    data = zeros(samples, dtype=float32)
    maxdata = comedi.comedi_get_maxdata(device, 
                                        subdevice, 
                                        channel)
    rng = comedi.comedi_get_range(device, 
                                subdevice, 
                                channel, 
                                channel_range)

    if (comedi.comedi_get_subdevice_flags(device, subdevice) & SDF_LSAMPL):
        bytes_per_sample = 4
#        data_type = uint32
        unpack_type = 'I'
    else:
        bytes_per_sample = 2
#        data_type = uint16
        unpack_type = 'H'

    idx = 0

    try:
        while idx < samples:
            # Read the acquired values into the buffer
            # There might be several values in the buffer, that's why there is 
            # a second loop 
            ret = libc.read(fileno, ctypes.byref(buf), BUFSIZE)
            if ret == 0:
                print('Reached end of read-out')
                break

#            for ids, sample in enumerate(range(ret/bytes_per_sample)):
                # This is ugly, should figure out how to read the buffer into lsampl_t
                # directly
#                raw = frombuffer(
#                        buf[bytes_per_sample*ids:bytes_per_sample*(ids + 1)], 
#                        dtype=data_type)
            raw_values = unpack((ret/bytes_per_sample)*unpack_type,
                            buf[:ret])

            physical_values = convert_to_phys(
                        device_id,
                        subdevice,
                        channel,
                        raw_values,
                        channel_range,
                        maxdata)
            for physical_value in physical_values:
                data[idx] = physical_value
                idx += 1

    except (KeyboardInterrupt, IndexError):
        # If we abourt the acquisition with Ctrl-C, make sure the device is
        # closed
        comedi.comedi_close(device)
        raise 

    comedi.comedi_close(device)
    return data

def data_write(device_id, subdevice, channel, channel_range, aref, set_value):
    '''Write a single value to a channel'''
    with device_operation(device_id) as device:
        rc = comedi.comedi_data_write(device, 
                                    subdevice,
                                    channel, 
                                    channel_range,
                                    aref,
                                    set_value)
    if rc == 1:
        return True
    else:
        logging.warning('data_write was not successful')
        return False
                
def open(device_id):
    '''Open device'''
    return comedi.comedi_open(device_id)

def close(device):
    comedi.comedi_close(device)

def get_board_name(device_id):
    with device_operation(device_id) as device:
        board_name = comedi.comedi_get_board_name(device)
    return board_name

def get_n_subdevices(device_id):
    with device_operation(device_id) as device:
        n_subdevices = comedi.comedi_get_n_subdevices(device)
    return n_subdevices

def get_n_channels(device_id, subdevice):
    with device_operation(device_id) as device:
        n_channels = comedi.comedi_get_n_channels(device, subdevice)
    return n_channels

def get_n_ranges(device_id, subdevice, channel):
    '''Get the number of ranges on a subdevice channel'''
    with device_operation(device_id) as device:
        n_ranges = comedi.comedi_get_n_ranges(device, subdevice, channel)
    return n_ranges

def get_range(device_id, subdevice, channel, channel_range):
    '''Returns a comedi_range struct that containts the channel range'''
    range_struct = comedi_range()
    with device_operation(device_id) as device:
        range_s =  comedi.comedi_get_range(device,
                                        subdevice,
                                        channel,
                                        channel_range)
        if range_s == None:
            raise Exception('comedi_get_range failed')
        range_struct.min = range_s.contents.min
        range_struct.max = range_s.contents.max
        range_struct.unit = range_s.contents.unit
    return range_struct

def get_range_struct(device_id, subdevice, channel, channel_range):
    with device_operation(device_id) as device:
        range_struct =  comedi.comedi_get_range(device,
                                        subdevice,
                                        channel,
                                        channel_range)
    return range_struct

def get_max_data(device_id, subdevice, channel):
    with device_operation(device_id) as device:
        return comedi.comedi_get_maxdata(device, subdevice, channel)

def get_max_buffer_size(device_id, subdevice):
    with device_operation(device_id) as device:
        return comedi.comedi_get_max_buffer_size(device, subdevice)

def get_buffer_size(device_id, subdevice):
    '''
    This function returns the size (in bytes) of the streaming buffer for the
    subdevice specified by 'device' and 'subdevice'.
    '''
    with device_operation(device_id) as device:
        return comedi.comedi_get_buffer_size(device, subdevice)

def get_buffer_offset(device_id, subdevice):
    '''
    This function returns the offset (in bytes) of the streaming buffer for the
    subdevice specified by 'device' and 'subdevice'.
    '''
    with device_operation(device_id) as device:
        return comedi.comedi_get_buffer_offset(device, subdevice)

def get_subdevice_type(device_id, subdevice):
    with device_operation(device_id) as device:
        return comedi.comedi_get_subdevice_type(device, subdevice)

def get_subdevice_flags(device_id, subdevice):
    with device_operation(device_id) as device:
        return comedi.comedi_get_subdevice_flags(device, subdevice)

def get_default_calibration_path(device_id):
    with device_operation(device_id) as device:
        return comedi.comedi_get_default_calibration_path(device)

def parse_calibration_file(file_path):
    return comedi.comedi_parse_calibration_file(file_path)

#def cleanup_calibration(calibration):
#    comedi.comedi_cleanup_calibration(calibration)

#def get_softcal_converter(subdevice,
#                          channel,
#                          channel_range,
#                          direction,
#                          parsed_calibration,
#                          converter):

def dio_write(device_id, subdevice, channel, bit):
    '''
    Write a single bit to a digital channel

    bit should be a boolean value
    '''
    with device_operation(device_id) as device:
        rc = comedi.comedi_dio_write(device, subdevice, channel, int(bit))
    if rc == 1:
        return True
    else:
        logging.warning('dio_write was not successful')
        return False

def dio_config(device_id, subdevice, channel, direction):
    '''
    Set the direction of a digital input/output channel
    '''
    with device_operation(device_id) as device:
        rc = comedi.comedi_dio_config(device, 
                                      subdevice, 
                                      channel, 
                                      direction)
    if rc == 0:
        return True
    else:
        logging.warning('dio_config was not successful')
        return False

class device_operation:
    def __init__(self, device_id):
        self.device_id = device_id

    def __enter__(self):    
        self.device = open(self.device_id)
        return self.device

    def __exit__(self, type, value, traceback):
        close(self.device)
        

