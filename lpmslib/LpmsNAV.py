import time
import serial
import threading
import struct
import sys
from datetime import datetime, timedelta
from .LpmsConfig import *
from .lputils import *
from .LpmsConfigurationSettings import LpmsConfigurationSettings

#TODO:
# check serial port opened before executing commands
# add wait for ack routine

class LpmsNAV(object):
    TAG = "LPMSNAV"
    runOnce = True
    verbose = True
    is_thread_running = False

    sensor_configuration = LpmsConfigurationSettings()

    PACKET_START        = 0
    PACKET_FUNCTION     = 1
    PACKET_INDEX        = 2
    PACKET_LENGTH       = 3
    PACKET_RAW_DATA     = 4
    PACKET_LRC_CHECK    = 5
    PACKET_END_LB       = 6
    PACKET_END_HB       = 7

    current_length = 0
    current_function = 0
    rx_state = PACKET_START
    in_bytes = []
    rx_buffer = []
    raw_tx_data = []
    rx_index  = 0
    lrc_check = 0
    wait_for_ack = False
    wait_for_data = False

    is_sensor_connected = False
    is_command_mode = False
    config_register = 0
    status_register = 0
    frame_counter = 0
    acc_x = 0
    acc_y = 0
    acc_z = 0
    gyr_z = 0
    angular_vel_z = 0

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.__init_params()

    def __clear_params(self):
        self.current_length = 0
        self.current_function = 0
        self.rx_state = self.PACKET_START
        self.in_bytes = []
        self.rx_buffer = []
        self.raw_tx_data = []
        self.rx_index  = 0
        self.lrc_check = 0
        self.frame_counter = 0
        self.acc_x = 0
        self.acc_y = 0
        self.acc_z = 0
        self.gyr_z = 0
        self.angular_vel_z = 0
        self.wait_for_ack = False
        self.wait_for_data = False

    def __init_params(self):
        self.__clear_params()

    def __thread_is_alive(self):
        try:
            return self.thread.isAlive()
        except AttributeError:
            return False

    def __run(self):
        """ Method that runs forever """
        self.is_thread_running = True
        while not self.quit:
            self.is_sensor_connected = True
            bytesToRead = self.serial_port.inWaiting()
            if bytesToRead > 0:
                reading = self.serial_port.read(bytesToRead)
                self.__parse(reading)
        self.serial_port.close()
        self.is_sensor_connected = False
        self.is_thread_running = False


    # TODO: add offset length check
    def __convert_rxbytes_to_uint8(self, offset, dataList):
        """
        dataList is a list
        """
        (i,) = struct.unpack("B", ''.join(dataList[offset:offset+2]))
        return i

    def __convert_rxbytes_to_int16(self, offset, dataList):
        """
        dataList is a list
        """
        (i,) = struct.unpack("h", ''.join(dataList[offset:offset+2]))
        return i

    def __convert_rxbytes_to_int(self, offset, dataList):
        """
        dataList is a list
        """
        (i,) = struct.unpack("i", ''.join(dataList[offset:offset+4]))
        return i

    def __convert_rxbytes_to_float(self, offset, dataList):

        """
        dataList is a list
        """
        (i,) = struct.unpack("f", ''.join(dataList[offset:offset+4]))
        return i

    def __convert_uint8_to_txbytes(self, v):
        """
        return bytesarray
        """
        return struct.pack("B", v)

    def __convert_int16_to_txbytes(self, v):
        """
        return bytesarray
        """
        return struct.pack("h", v)

    def __convert_int_to_txbytes(self, v):
        """
        return bytesarray
        """
        return struct.pack("i", v)
        
    def __print_str_to_hex(self, s):
        print (":".join("{:02x}".format(ord(c)) for c in s))

    # Parser
    def __parse_function(self):
        cf = self.current_function
        if cf == LPMS_ACK:
            if self.verbose: logd(self.TAG , "Received Ack")
            self.wait_for_ack = False

        elif cf == LPMS_NACK:
            if self.verbose: logd(self.TAG , "Received Nack")
            self.wait_for_ack = False

        elif cf == GET_CONFIG:
            self.config_register = self.__convert_rxbytes_to_int(0, self.rx_buffer)
            #if self.verbose: print"{0:b}".format(self.config_register).zfill(32)
            self.__parse_configuration_register(self.config_register)
            self.wait_for_data = False

        elif cf == GET_SENSOR_DATA:
            self.__parse_sensor_data(16)
            self.wait_for_data = False


    def __parse(self, data):
        self.lrcReceived = 0
        for b in data:
            if self.rx_state == self.PACKET_START:
                if (b == ':'):
                    self.rx_state = self.PACKET_FUNCTION

            elif self.rx_state == self.PACKET_FUNCTION:
                self.current_function = ord(b)
                self.rx_state = self.PACKET_INDEX

            elif self.rx_state == self.PACKET_INDEX:
                self.frame_counter = ord(b)
                self.rx_state = self.PACKET_LENGTH

            elif self.rx_state == self.PACKET_LENGTH:
                self.current_length = ord(b)
                self.rx_index = 0
                self.rx_buffer = []
                if (self.current_length > 0):
                    self.rx_state = self.PACKET_RAW_DATA
                else:
                    self.rx_state = self.PACKET_LRC_CHECK
                
            elif self.rx_state == self.PACKET_RAW_DATA:
                # add length check
                self.rx_buffer.append(b)
                self.rx_index = self.rx_index + 1
                if self.rx_index == self.current_length:
                    self.rx_state = self.PACKET_LRC_CHECK
            
            elif self.rx_state == self.PACKET_LRC_CHECK:
                self.lrcReceived = ord(b)
                self.lrc_check = self.current_function + self.frame_counter + self.current_length 
                self.lrc_check = (self.lrc_check + sum([ord(c) for c in self.rx_buffer]) )%256
                if self.lrcReceived == self.lrc_check:
                    self.__parse_function()
                self.rx_state = self.PACKET_START
           
            else:
                self.rx_state = self.PACKET_START
   

    def __parse_sensor_data(self, data_mode=32):
        o = 0
        r2d = 57.2958
        if data_mode == 16:
            converter = lambda offset, l: float(self.__convert_rxbytes_to_int16(offset, l)) / 100.0
            increment = 2
        else:
            converter = lambda offset, l: self.__convert_rxbytes_to_float(offset, l)
            increment = 4

        self.gyr_z = converter(o, self.rx_buffer)
        o += increment
        self.angular_vel_z = converter(o, self.rx_buffer)
        o += increment

        self.acc_x = converter(o, self.rx_buffer)
        o += increment
        self.acc_y = converter(o, self.rx_buffer)
        o += increment
        self.acc_z = converter(o, self.rx_buffer)
        o += increment


    # communication
    def __get_config_register(self):
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return None
        if self.verbose: logd(self.TAG, "Get config register")
        time.sleep(.1)
        self.__lpbus_set_none(GET_CONFIG)
        self.wait_for_data = True
        self.__wait_for_response()

    def __send_data(self, function, length):
        txlrc_check = 0
        txBuffer = chr(0x3a)
        txBuffer += self.__convert_uint8_to_txbytes(function)
        txBuffer += self.__convert_uint8_to_txbytes(length)
        if length > 0:
            txBuffer += self.raw_tx_data
        txlrc_check = function + length
        if length > 0:
            txlrc_check += sum([ord(c) for c in self.raw_tx_data])

        txBuffer += self.__convert_uint8_to_txbytes(txlrc_check)
        txBuffer += chr(0x0d)
        txBuffer += chr(0x0a)
        
        bytesSent = self.serial_port.write(txBuffer)
        
    def __lpbus_set_none(self, command):
        self.__send_data(command, 0)

    def __lpbus_set_int32(self, command, v):
        self.raw_tx_data = self.__convert_int_to_txbytes(v)
        self.__send_data(command, 4)

    def __lpbus_set_data(self, command, length, dataBuffer):
        self.raw_tx_data = dataBuffer
        self.__send_data(command, length)

    def __wait_for_response(self):
        while self.wait_for_ack or self.wait_for_data:
            time.sleep(.1)

    def __parse_configuration_register(self, cr):
        self.sensor_configuration.parse(cr)


    # User command
    def connect(self):
        if self.__thread_is_alive():
            loge(self.TAG, "Another connection established")
            return False

        try:
            self.__clear_params()
            self.thread = threading.Thread(target=self.__run, args=())
            self.serial_port = serial.Serial(self.port, self.baudrate, timeout=None,xonxoff=False, rtscts=False,  dsrdtr=False)        
            self.quit = False
            logd(self.TAG , "Sensor connected")
            self.thread.start()                              # Start the execution
            time.sleep(1)
            self.set_command_mode()                        # Start the execution
            time.sleep(.2)
            self.__get_config_register()                        # Start the execution
            time.sleep(.2)
            self.set_streaming_mode()
            return True
        except serial.SerialException:
            loge(self.TAG, "Could not open port " + self.port)
            loge(self.TAG, "Please try again")

        return False

    def disconnect(self):
        self.quit = True
        if self.__thread_is_alive():
            self.thread.join()
        if self.verbose: logd(self.TAG , "sensor disconnected")
        return True

    def is_connected(self):
        return self.is_sensor_connected

    # Configuration and Status
    def get_config_register(self):
        return self.sensor_configuration

    def get_status_register(self):
        pass


    # Mode switching
    def set_command_mode(self):
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return False

        if self.verbose: logd(self.TAG, "Set command mode")
        self.__lpbus_set_none(GOTO_COMMAND_MODE)
        self.wait_for_ack = True
        self.__wait_for_response()
        self.is_command_mode = True

    def set_streaming_mode(self):
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return False
        self.set_command_mode()
        if self.verbose: logd(self.TAG, "Set streaming mode")
        self.__lpbus_set_none(GOTO_STREAM_MODE)
        self.wait_for_ack = True
        self.__wait_for_response()
        self.is_command_mode = False

    # Data transmision
    def get_sensor_data(self):
        """
        get sensor data during command Mode
        """
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return False

        if self.verbose: logd(self.TAG, "Get sensor data")
        self.__lpbus_set_none(GET_SENSOR_DATA)
        self.wait_for_data = True
        self.__wait_for_response()
        return self.get_stream_data()


    def get_stream_data(self):
        """
        get sensor data during stream Mode
        """
        data = []
        data.append(self.frame_counter)
        data.append(self.gyr_z)
        data.append(self.angular_vel_z)
        data.append([self.acc_x, self.acc_y, self.acc_z])
        return data

    def set_transmit_data(self):
        pass

    def set_baudrate(self, baud):
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return None
        self.set_command_mode()
        if self.verbose: logd(self.TAG, "Set baudrate: "+str(baud)+"bps")
        self.__lpbus_set_int32(SET_UART_BAUDRATE ,baud)
        self.wait_for_ack = True
        self.__wait_for_response()
        self.__get_config_register()
        self.set_streaming_mode()
	
    def set_stream_frequency(self, freq):
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return None
        self.set_command_mode()
        if self.verbose: logd(self.TAG, "Set stream freq: "+str(freq)+"Hz")
        self.__lpbus_set_int32(SET_STREAM_FREQ , freq)
        self.wait_for_ack = True
        self.__wait_for_response()
        self.__get_config_register()
        self.set_streaming_mode()

    def set_stream_frequency_10Hz(self):
        self.set_stream_frequency(LPMS_STREAM_FREQ_10HZ)

    def set_stream_frequency_25Hz(self):
        self.set_stream_frequency(LPMS_STREAM_FREQ_25HZ)

    def set_stream_frequency_50Hz(self):
        self.set_stream_frequency(LPMS_STREAM_FREQ_50HZ)

    def set_stream_frequency_100Hz(self):
        self.set_stream_frequency(LPMS_STREAM_FREQ_100HZ)


    def reset_factory(self):
        if not self.is_connected():
            loge(self.TAG, "sensor not connected")
            return None
        self.set_command_mode()
        if self.verbose: logd(self.TAG, "Reset factory settings")
        self.__lpbus_set_none(RESET_SENSOR)
        self.wait_for_ack = True
        self.__wait_for_response()
        self.__get_config_register()
        self.set_streaming_mode()

	    

   
