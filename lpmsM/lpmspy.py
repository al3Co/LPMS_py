
#    Lpms class to interface with LpmsSensors
#    Known Issues:
#    - Serial Interrupt routine blocks main processing thread
#    when transferring at data rate > 100Hz
#
#    TODO:
#    - Implement 16bit data parsing
#
#    Author: H.E.Yap
#    Date: 2016/07/19
#    Revision: 0.1
#    Copyright: LP-Research Inc. 2016

import numpy as np
import serial

class lpms:
    PACKET_ADDRESS0     = 0
    PACKET_ADDRESS1     = 1
    PACKET_FUNCTION0    = 2
    PACKET_FUNCTION1    = 3
    PACKET_LENGTH0      = 4
    PACKET_LENGTH1      = 5
    PACKET_RAW_DATA     = 6
    PACKET_LRC_CHECK0   = 7
    PACKET_LRC_CHECK1   = 8
    PACKET_END          = 9
    MAX_BUFFER          = 4096

    # Command register
    REPLY_ACK             = 0
    REPLY_NACK            = 1
    GET_CONFIG            = 4
    GET_STATUS            = 5
    GOTO_COMMAND_MODE     = 6
    GOTO_STREAM_MODE      = 7
    GET_SENSOR_DATA       = 9

    GET_SERIAL_NUMBER     = 90
    GET_DEVICE_NAME       = 91
    GET_FIRMWARE_INFO     = 92

    # Configuration register contents
    LPMS_GYR_AUTOCAL_ENABLED        = (1<<30)
    LPMS_LPBUS_DATA_MODE_16BIT_ENABLED = (1<<22)
    LPMS_LINACC_OUTPUT_ENABLED      =  (1<<21)
    LPMS_DYNAMIC_COVAR_ENABLED      =  (1<<20)
    LPMS_ALTITUDE_OUTPUT_ENABLED    =  (1<<19)
    LPMS_QUAT_OUTPUT_ENABLED        =  (1<<18)
    LPMS_EULER_OUTPUT_ENABLED       =  (1<<17)
    LPMS_ANGULAR_VELOCITY_OUTPUT_ENABLED =  (1<< 16)
    LPMS_GYR_CALIBRA_ENABLED        =  (1<<15)
    LPMS_HEAVEMOTION_OUTPUT_ENABLED =  (1<<14)
    LPMS_TEMPERATURE_OUTPUT_ENABLED =  (1<<13)
    LPMS_GYR_RAW_OUTPUT_ENABLED     =  (1<<12)
    LPMS_ACC_RAW_OUTPUT_ENABLED     =  (1<<11)
    LPMS_MAG_RAW_OUTPUT_ENABLED     =  (1<<10)
    LPMS_PRESSURE_OUTPUT_ENABLED    =  (1<<9)
    LPMS_STREAM_FREQ_5HZ_ENABLED      = 0
    LPMS_STREAM_FREQ_10HZ_ENABLED     = 1
    LPMS_STREAM_FREQ_25HZ_ENABLED     = 2
    LPMS_STREAM_FREQ_50HZ_ENABLED     = 3
    LPMS_STREAM_FREQ_100HZ_ENABLED    = 4
    LPMS_STREAM_FREQ_200HZ_ENABLED    = 5
    LPMS_STREAM_FREQ_400HZ_ENABLED    = 6
    LPMS_STREAM_FREQ_MASK             = 7

    LPMS_STREAM_FREQ_5HZ    = 5
    LPMS_STREAM_FREQ_10HZ   = 10
    LPMS_STREAM_FREQ_25HZ   = 25
    LPMS_STREAM_FREQ_50HZ   = 50
    LPMS_STREAM_FREQ_100HZ  = 100
    LPMS_STREAM_FREQ_200HZ  = 200
    LPMS_STREAM_FREQ_400HZ  = 400

    PARAMETER_SET_DELAY = 0.01
    DATA_QUEUE_SIZE = 64

    def __init__(self):
        self.serConn = None
        self.isSensorConnected = False
        # define the properties of the class here, (like fields of a struct)
        self.rxBuffer = np.uint8(np.zeros(self.MAX_BUFFER))
        self.rawTxBuffer = np.uint8(np.zeros(self.MAX_BUFFER))
        self.inBytes = np.uint8(np.zeros(2))
        self.rxState = self.PACKET_END
        self.rxIndex = 0
        self.currentAddress = 0
        self.currentFunction = 0
        self.currentLength = 0
        self.lrcCheck = 0
        self.lastTimestamp = 0
        self.fps = 0
        #
        self.waitForAck = False
        self.waitForData = False

        # Settings related
        self.imuId = 0
        self.gyrRange = 0
        self.accRange = 0
        self.magRange = 0
        self.streamingFrequency = 0
        self.filterMode = 0
        self.isStreamMode = True

        self.configurationRegister = 0
        self.configurationRegisterReady = False
        self.sensorDataLength = 0
        self.serialNumber = None
        self.serialNumberReady = False
        self.deviceName = None
        self.deviceNameReady = False
        self.firmwareInfo= None
        self.firmwareInfoReady = False
        self.firmwareVersion = None

        self.accEnable = False
        self.gyrEnable = False
        self.magEnable = False
        self.angularVelEnable = False
        self.quaternionEnable = False
        self.eulerAngleEnable = False
        self.linAccEnable = False
        self.pressureEnable = False
        self.altitudeEnable = False
        self.temperatureEnable = False
        self.heaveEnable = False
        self.sixteenBitDataEnable = False
        self.resetTimestampFlag = False
        # sensorData
        self.three = 3
        self.four = 4
        self.sensorData = {
            'timestamp': 0.0,
            'gyr':  np.zeros(self.three),
            'acc':  np.zeros(self.three),
            'mag':  np.zeros(self.three),
            'angVel':  np.zeros(self.three),
            'quat':  np.zeros(self.four),
            'euler':  np.zeros(self.three),
            'linAcc':  np.zeros(self.three),
            'pressure': 0.0,
            'altitude': 0.0,
            'temperature': 0.0,
            'heave': 0.0
        }
        self.dataQueue = []

    def connect(self, serPort, baudrate):
        # TODO: clear serial ports
        # connecting to serial port
        try:
            self.serConn = serial.Serial(serPort, baudrate, timeout=None, xonxoff=False, rtscts=False, dsrdtr=False)
            # print('Sensor connected')
            # Force put sensor in command mode
            if not (self.serConn.is_open):
                self.serConn.open()
            self.lpBusSetDataNone(self.GOTO_COMMAND_MODE)
            self.serConn.close()
            self.isSensorConnected = self.serConn.is_open
        except serial.SerialException:
            print('Could not open port {}'.format(serPort))
        return(self.isSensorConnected)

    def lpBusSetDataNone(self, command):
        self.sendData(command, 0)

    def sendData(self, command, length):
        txBuffer = np.zeros(11+length)
        txBuffer[0] = int(('3A'), 16)
        txBuffer[1:2] = np.uint8(np.uint16(self.imuId))
        txBuffer[3:4] = np.uint8(np.uint16(command))
        txBuffer[5:6] = np.uint8(np.uint16(length))
        txLrcCheck = 0
        for i in range(1,6):
            txLrcCheck = txLrcCheck + txBuffer[i]
        for i in range(length):
            txBuffer[6+i] = self.rawTxData[i]
            txLrcCheck = txLrcCheck + This.rawTxData[i]
        
