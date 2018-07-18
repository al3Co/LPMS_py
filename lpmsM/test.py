
import lpmspy

# User settings
port = '/dev/ttyUSB0'
baudrate = 115200


lpSensor = lpmspy.lpms()
print('Connected: {}'.format(lpSensor.connect(port, baudrate)))
