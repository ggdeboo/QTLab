# alazar.py python auxiliary library to access the alazar dlls
# Gabriele de Boo, 2015 <ggdeboo@gmail.com>
import ctypes
import logging
import numpy
from time import sleep

aapi = ctypes.cdll.ATSApi

HANDLE  = ctypes.c_void_p
U8      = ctypes.c_ubyte
U16     = ctypes.c_ushort
U32     = ctypes.c_ulong

c_CHANNEL_A  = U8(1)
c_CHANNEL_B  = U8(2)
c_CHANNEL_C  = U8(4)
c_CHANNEL_D  = U8(8)

SAMPLE_RATE_1KSPS   = U32(0x1)
SAMPLE_RATE_2KSPS   = U32(0x2)
SAMPLE_RATE_5KSPS   = U32(0x4)
SAMPLE_RATE_10KSPS  = U32(0x8)
SAMPLE_RATE_20KSPS  = U32(0xA)
SAMPLE_RATE_50KSPS  = U32(0xC)
SAMPLE_RATE_100KSPS = U32(0xE)
SAMPLE_RATE_200KSPS = U32(0x10)
SAMPLE_RATE_500KSPS = U32(0x12)
SAMPLE_RATE_1MSPS   = U32(0x14)
SAMPLE_RATE_2MSPS   = U32(0x18)
SAMPLE_RATE_5MSPS   = U32(0x1A)
SAMPLE_RATE_10MSPS  = U32(0x1C)
SAMPLE_RATE_20MSPS  = U32(0x1E)
SAMPLE_RATE_50MSPS  = U32(0x22)
SAMPLE_RATE_100MSPS = U32(0x24)
SAMPLE_RATE_125MSPS = U32(0x25)

sample_rate_dict = { 
    0x1   : 1000,
    0x2   : 2000,
    0x4   : 5000,
    0x8   : 10000,
    0xA   : 20000,
    0xC   : 50000,
    0xE   : 100000,
    0x10  : 200000,
    0x12  : 500000,
    0x14  : 1000000,
    0x18  : 2000000,
    0x1A  : 5000000,
    0x1C  : 10000000,
    0x1E  : 20000000,
    0x22  : 50000000,
    0x24  : 100000000,
    0x25  : 125000000,
    }

rev_sample_rate_dict = dict((v,k) for k,v in sample_rate_dict.iteritems())

c_INPUT_RANGE_PM_100mV  =   U32(5)
c_INPUT_RANGE_PM_200mV  =   U32(6)
c_INPUT_RANGE_PM_400mV  =   U32(7)
c_INPUT_RANGE_PM_1V     =   U32(10)
c_INPUT_RANGE_PM_2V     =   U32(11)
c_INPUT_RANGE_PM_4V     =   U32(12)

input_range_dict = {
    0.1 : c_INPUT_RANGE_PM_100mV,
    0.2 : c_INPUT_RANGE_PM_200mV,
    0.4 : c_INPUT_RANGE_PM_400mV,
    1.0 : c_INPUT_RANGE_PM_1V,   
    2.0 : c_INPUT_RANGE_PM_2V,   
    4.0 : c_INPUT_RANGE_PM_4V,   
    }

c_IMPEDANCE_1M_OHM      =   U32(1)
c_IMPEDANCE_50_OHM      =   U32(2)

c_AC_COUPLING           =   U32(1)
c_DC_COUPLING           =   U32(2)

c_TRIG_CHAN_A   =   U32(0)    #Source Id
c_TRIG_CHAN_B   =   U32(1)    #Source Id
c_TRIG_CHAN_C   =   U32(4)    #Source Id
c_TRIG_CHAN_D   =   U32(5)    #Source Id
c_TRIG_EXTERNAL =   U32(2)    #Source Id
c_TRIG_DISABLE  =   U32(3)    #Source Id

c_TRIG_ENGINE_OP_J              =   U32(0) #Trigger operation
c_TRIG_ENGINE_OP_K              =   U32(1) #Trigger operation
c_TRIG_ENGINE_OP_J_OR_K         =   U32(2) #Trigger operation
c_TRIG_ENGINE_OP_J_AND_K        =   U32(3) #Trigger operation
c_TRIG_ENGINE_OP_J_XOR_K        =   U32(4) #Trigger operation
c_TRIG_ENGINE_OP_J_AND_NOT_K    =   U32(5) #Trigger operation
c_TRIG_ENGINE_OP_NOT_J_AND_K    =   U32(6) #Trigger operation

c_TRIG_ENGINE_J =   U32(0)    #TriggerEngine Id
c_TRIG_ENGINE_K =   U32(1)    #TriggerEngine Id

c_TRIG_SLOPE_POSITIVE = U32(1) #Slope Id
c_TRIG_SLOPE_NEGATIVE = U32(2) #Slope Id

GET_SERIAL_NUMBER           = U32(0x10000024)
GET_LATEST_CAL_DATE         = U32(0x10000026)
GET_LATEST_CAL_DATE_MONTH   = U32(0x1000002D)
GET_LATEST_CAL_DATE_DAY     = U32(0x1000002E)
GET_LATEST_CAL_DATE_YEAR    = U32(0x1000002F)
MEMORY_SIZE                 = U32(0x1000002A)
BOARD_TYPE                  = U32(0x1000002B)
ASOPC_TYPE                  = U32(0x1000002C)
GET_PCIE_LINK_SPEED         = U32(0x10000030)
GET_PCIE_LINK_WIDTH         = U32(0x10000031)
GET_MAX_PRETRIGGER_SAMPLES  = U32(0x10000046)
GET_CPF_DEVICE              = U32(0x10000071)

board_type_dict = {
                    1 : 'ATS850',
                    2 : 'ATS310',
                    3 : 'ATS330',
                    7 : 'ATS460',
                    8 : 'ATS860',
                    9 : 'ATS660',
                   11 : 'ATS9462',
                   13 : 'ATS9870',
                   14 : 'ATS9350',
                   15 : 'ATS9325',
                   16 : 'ATS9440',
                   17 : 'ATS9410',
                   18 : 'ATS9351',
                   21 : 'ATS9850',
                   22 : 'ATS9625',
                   24 : 'ATS9626',
                   25 : 'ATS9360'}

aapi.AlazarGetBoardBySystemID.restype = HANDLE
aapi.AlazarRead.restype = U32

def get_boardID():
    c_SystemId = ctypes.c_uint(1)
    c_BoardId = ctypes.c_uint(1)
    ahandle = aapi.AlazarGetBoardBySystemID(c_SystemId,
                                            c_BoardId)
    return ahandle

def get_board_type(ahandle):
    value = U32()
    status = aapi.AlazarQueryCapability(ahandle,
                               BOARD_TYPE,
                               U32(0),
                               ctypes.byref(value))
    if status == 512:
        return board_type_dict[value.value]
    else:
        raise RuntimeError('alazar failed with status: %i' % status)
   
def get_memory_size(ahandle):
    value = U32() 
    status = aapi.AlazarQueryCapability(ahandle,
                               MEMORY_SIZE,
                               U32(0),
                               ctypes.byref(value))
    if status == 512:
        return value.value
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def get_pcie_link_speed(ahandle):
    value = U32() 
    status = aapi.AlazarQueryCapability(ahandle,
                               GET_PCIE_LINK_SPEED,
                               U32(0),
                               ctypes.byref(value))
    if status == 512:
        return value.value
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def get_pcie_link_width(ahandle):
    value = U32() 
    status = aapi.AlazarQueryCapability(ahandle,
                               GET_PCIE_LINK_WIDTH,
                               U32(0),
                               ctypes.byref(value))
    if status == 512:
        return value.value
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def get_channel_info(ahandle):
    '''Get the memory size and sample size in bits per channel'''
    c_NS = U32(0)
    c_S = U8(0)
    status = aapi.AlazarGetChannelInfo(ahandle,
                                     ctypes.byref(c_NS),
                                     ctypes.byref(c_S))
    if status == 512:
        return c_NS.value, c_S.value
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def set_clock(ahandle, clock_rate, source='internal', edge='rising', 
                decimation=0):
    '''Set the sample clock
        source: internal, external fast, external slow or external 10MHz
        edge: rising or falling
    '''
    if source == 'internal':
        c_CLOCK_ID = U32(1)
    elif source == 'external fast':
        c_CLOCK_ID = U32(2)
    elif source == 'external slow':
        c_CLOCK_ID = U32(4)
    elif source == 'external 10MHz':
        c_CLOCK_ID = U32(7)
        
    if clock_rate in sample_rate_dict.values():
        SAMPLE_RATE = rev_sample_rate_dict[clock_rate]
    else:
        raise ValueError('alazar.py: Clock rate not supported')

    if edge == 'rising':
        c_EDGE               =   U32(0) #EdgeID arg3
    elif edge == 'falling':
        c_EDGE               =   U32(1) #EdgeID arg3
    else:
        raise ValueError('alazar.py: Parameter edge must be rising or falling')
    
    if decimation == 0:    
        c_DEC               =   U32(0) #Decimation arg4
    else:
        c_DEC               =   U32(decimation)

    status = aapi.AlazarSetCaptureClock(ahandle,
                                        c_CLOCK_ID,
                                        SAMPLE_RATE,
                                        c_EDGE,
                                        c_DEC)
    if status == 512:
        return True
    else:
        raise RuntimeError('alazar failed with status: %i' % status)
    

def set_input_channel_parameters(ahandle, channel, coupling, input_range,
                                impedance=50):
    '''Set the coupling, range and input impedance of a channel

        
        ATS9440 only supports 50 Ohm input impedance
    '''
    if channel == 'A':
        c_CHANNEL = c_CHANNEL_A
    elif channel == 'B':
        c_CHANNEL = c_CHANNEL_B
    elif channel == 'C':
        c_CHANNEL = c_CHANNEL_C
    elif channel == 'D':
        c_CHANNEL = c_CHANNEL_D
    else:
        raise ValueError('alazar.py: channel must be A, B, C or D')

    if coupling == 'DC':
        c_COUPLING = c_DC_COUPLING
    elif coupling == 'AC':
        c_COUPLING = c_AC_COUPLING
    else:
        raise ValueError('alazar.py: coupling must be AC or DC')

    if input_range not in  input_range_dict.keys():
        raise ValueError('alazar.py: selectable input range is: %s' 
                    % input_range_dict.keys())

    c_INPUT_RANGE = input_range_dict[input_range]

    if impedance == 50:
        c_IMPEDANCE = c_IMPEDANCE_50_OHM
    elif impedance == 1000000:
        c_IMPEDANCE = c_IMPEDANCE_1M_OHM

    status = aapi.AlazarInputControl(ahandle,
                                     c_CHANNEL,
                                     c_COUPLING,
                                     c_INPUT_RANGE,
                                     c_IMPEDANCE)
    if status == 512:
        return True
    elif status == 513:
        raise RuntimeError('specified input range, coupling or impedance not supported')
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def set_trigger(ahandle, 
                operation   = 'J',
                engine1     = 'J',
                source1     = 'disable',
                slope1      = 'positive',
                level1      = 0,
                engine2     = 'K',
                source2     = 'disable',
                slope2      = 'positive',
                level2      = 0):
    '''
    Configures the trigger system

    The digitizer has two trigger systems, J and K.

    RETURN_CODE
        AlazarSetTriggerOperation (
        HANDLE BoardHandle,
        U32 TriggerOperation,
        U32 TriggerEngineId1,
        U32 SourceId1,
        U32 SlopeId1,
        U32 Level1,
        U32 TriggerEngineId2,
        U32 SourceId2,
        U32 SlopeId2,
        U32 Level2
        );

    '''
    if operation == 'J':
        c_TRIG_ENGINE_OP = c_TRIG_ENGINE_OP_J

    if engine1 == 'J':
        c_TRIG_ENGINE1 = c_TRIG_ENGINE_J
    elif engine1 == 'K':
        c_TRIG_ENGINE1 = c_TRIG_ENGINE_K
    else:
        raise ValueError('alazar.py: engine must be J or K')

    if source1.lower() == 'disable':
        c_TRIG_CHAN1 = c_TRIG_DISABLE
    else:
        raise ValueError('alazar.py: wrong trigger source: %s' % source1)

    if slope1.lower() == 'positive':
        c_TRIG_SLOPE1 = c_TRIG_SLOPE_POSITIVE
    elif slope1.lower() == 'negative':
        c_TRIG_SLOPE1 = c_TRIG_SLOPE_NEGATIVE

    if (-1 < level1 < 256):
        c_Level1 = U32(level1)
    else:
        raise ValueError('alazar.py: trigger level must be between 0 and 255')
    if (-1 < level2 < 256):
        c_Level2 = U32(level2) 
    else:
        raise ValueError('alazar.py: trigger level must be between 0 and 255')

    if engine2 == 'K':
        c_TRIG_ENGINE2 = c_TRIG_ENGINE_K
    elif engine2 == 'J':
        c_TRIG_ENGINE2 = c_TRIG_ENGINE_J
    else:
        raise ValueError('alazar.py: engine must be J or K')

    if source2.lower() == 'disable':
        c_TRIG_CHAN2 = c_TRIG_DISABLE
    else:
        raise ValueError('alazar.py: wrong trigger source: %s' % source2)

    if slope2.lower() == 'positive':
        c_TRIG_SLOPE2 = c_TRIG_SLOPE_POSITIVE
    elif slope2.lower() == 'negative':
        c_TRIG_SLOPE2 = c_TRIG_SLOPE_NEGATIVE

    triggerLevel_volts = 2
    triggerRange_volts = 5
    triggerLevel_code  = int(round(
                        (128+127*triggerLevel_volts/triggerRange_volts)))

    status = aapi.AlazarSetTriggerOperation(ahandle,
                                            c_TRIG_ENGINE_OP, 
                                            c_TRIG_ENGINE1,
                                            c_TRIG_CHAN1,
                                            c_TRIG_SLOPE1,
                                            c_Level1,
                                            c_TRIG_ENGINE2,
                                            c_TRIG_CHAN2,
                                            c_TRIG_SLOPE2,
                                            c_Level2)
    if status == 512:
        return True
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def set_trigger_timeout(ahandle, timeout=10e-6):
    '''Set the trigger time out in seconds

    minimum = 10e-6
    '''
    timeout = int(round(timeout*1e5, 0))
    if timeout == 0:
        logging.warning('Setting the timeout to 0 means the digitizer will'
                        ' wait forever.')
    status = aapi.AlazarSetTriggerTimeOut( ahandle,
                                           U32(timeout))
    if (status == 512):
        return True
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def set_trigger_delay(ahandle, sample_rate, delay=1e-3):
    sampleRate = sample_rate
    triggerDelay_samples=U32(int(round(delay*sampleRate+0.5)))

    status = aapi.AlazarSetTriggerDelay(ahandle,
                                        triggerDelay_samples)
    if status == 512:
        return True
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

#def get_sample_rate(sample_rate):
#    return sample_rate_dict[sample_rate.value]

def set_record_size(ahandle, pre_trig_samples=0, post_trig_samples=256):
    '''
    For ATS9440 minimum=256
    Number of alignment samples: 32

    Board       minimum pre align   buffer align    buffer align in NPT
    ===================================================================
    ATS9626     256     32          32              32
    ATS9850     256     64          64              64
    ATS9870     256     64          64              64
    ATS9440     256     32          32              32

    If the values for pre trigger samples and post trigger samples are not
    multiples of the alignment number, the buffer is made bigger to align.
    This is done by increasing the number of post trigger samples.

    The function returns the real number of pre trigger and post trigger samples
    '''
    pre_alignment       = 32
    buffer_alignment    = 32
    record_size = int(pre_trig_samples + post_trig_samples)

    if record_size < 256:
        raise ValueError('alazar.py: record size must be bigger than 255')

    if (pre_trig_samples % pre_alignment) != 0:
        real_pre_trig_samples = (pre_alignment * 
                                (pre_trig_samples / pre_alignment + 1))
    else:
        real_pre_trig_samples = pre_trig_samples

    if (post_trig_samples % buffer_alignment) != 0:
        real_post_trig_samples = (buffer_alignment * 
                                (post_trig_samples / buffer_alignment + 1))
    else:
        real_post_trig_samples = post_trig_samples

    c_PreTrigSamples = U32(real_pre_trig_samples)
    c_PostTrigSamples= U32(real_post_trig_samples)
    status = aapi.AlazarSetRecordSize(ahandle,
                                      c_PreTrigSamples,
                                      c_PostTrigSamples)
    if status == 512:
        return True, real_pre_trig_samples, real_post_trig_samples
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def set_records_per_capture(ahandle, records):
    c_RecordsPerCapture = U32(records)
    status = aapi.AlazarSetRecordCount(ahandle,     
                                       c_RecordsPerCapture)
    if status == 512:
        return True
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def start_capture(ahandle):
    status = aapi.AlazarStartCapture(ahandle)
    if status == 512:
        return True
    else:
        raise RuntimeError('alazar failed with status: %i' % status)

def is_busy(ahandle):
    return bool(aapi.AlazarBusy(ahandle))

def read(ahandle, 
            channel='A', 
            record=0,
            samples=512, 
            offset=0,
            ):
    '''
    Read out one channel, return numpy array of bytes       

    U32
        AlazarRead (
        HANDLE BoardHandle,
        U32 ChannelId,
        void *Buffer,
        int ElementSize,
        long Record,
        long TransferOffset,
        U32 TransferLength
        );
    '''
#    c_PreTrigSamples    = pre_trig_samples
#    c_PostTrigSamples   = post_trig_samples
    c_RecordsPerCapture = 1

    if (samples % 32) != 0:
        real_samples = (32 * (samples / 32 + 1))
    else:
        real_samples = samples

    # Now get the data ##########################################################
#    l = c_RecordsPerCapture*(c_PreTrigSamples+c_PostTrigSamples)
    l = c_RecordsPerCapture * real_samples
    # Need to check if sizeof(c_short) is 2 !!!
    bytes_per_sample    =   2
    c_DB_type           =  U16 * (l + 32)
    c_buffer            =  c_DB_type()

    if channel == 'A':
        c_CHANNEL = c_CHANNEL_A
    elif channel == 'B':
        c_CHANNEL = c_CHANNEL_B
    elif channel == 'C':
        c_CHANNEL = c_CHANNEL_C
    elif channel == 'D':
        c_CHANNEL = c_CHANNEL_D
    else:
        raise ValueError('alazar.py: channel must be A, B, C or D')

    status = aapi.AlazarRead(ahandle,
                             c_CHANNEL,
                             ctypes.byref(c_buffer),
#                             ctypes.sizeof(ctypes.c_ushort), # 2
                             U32(2),
                             ctypes.c_long(record+1),
                             ctypes.c_long(offset),
                             U32(real_samples),
                            )

    if not (status == 512):
        raise RuntimeError('alazar failed with status: %i' % status)

#    return numpy.array(c_DB[:] , dtype=numpy.uint16)
    return c_buffer[:samples]

def get_who_triggered(handle, board, record):
    '''Function to read out what the last trigger event was

    0 : This board did not cause the system to trigger.
    1 : CH A on this board caused the system to trigger.
    2 : CH B on this board caused the system to trigger.
    3 : EXT TRIG IN on this board caused the system to trigger.
    4 : Both CH A and CH B on this board caused the system to trigger.
    5 : Both CH A and EXT TRIG IN on this board caused the system to trigger.
    6 : Both CH B and EXT TRIG IN on this board caused the system to trigger.
    7 : A trigger timeout on this board caused the system to trigger.
    '''
    result = aapi.AlazarGetWhoTriggeredBySystemHandle(handle,
                                                      U32(1),
                                                      U32(record))
    return result
                                                      
