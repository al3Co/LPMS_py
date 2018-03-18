
# Command Registers
LPMS_ACK                    = 0
LPMS_NACK                   = 1

#Sensor info
GET_FIRMWARE_VERSION                = 4   # 16bit
GET_HARDWARE_VERSION                = 5   # 16bit
GET_SERIAL_NUMBER                   = 6   

# Configuration and status
GET_CONFIG                          = 7
GET_STATUS                          = 8

# | format | baudrate | output rate | deg/rad type | 180/360 output | initial mode |
# Mode switching
GOTO_COMMAND_MODE                   = 9
GOTO_STREAM_MODE                    = 10

# Sensor data
GET_SENSOR_DATA                     = 11

# 180/360 output
SET_360_OUTPUT                      = 14
SET_180_OUTPUT                      = 15

# Stream freq output rate 
GET_STREAM_FREQ                     = 18
SET_STREAM_FREQ                     = 19

# UART baudrate
GET_UART_BAUDRATE                   = 20
SET_UART_BAUDRATE                   = 21

# Reset
RESET_BIAS                          = 23
RESET_HEADING                       = 24
RESET_SENSOR                        = 25 


LPMS_STREAM_FREQ = {
    0:'10Hz',
    1:'25Hz',
    2:'50Hz',
    3:'100Hz',
}

LPMS_STREAM_FREQ_10HZ   = 10
LPMS_STREAM_FREQ_25HZ   = 25
LPMS_STREAM_FREQ_50HZ   = 50
LPMS_STREAM_FREQ_100HZ  = 100