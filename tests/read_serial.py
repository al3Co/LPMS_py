import serial
import serial.tools.list_ports

# https://pythonhosted.org/pyserial/shortintro.html#opening-serial-ports

#SERIAL_PORT = '/dev/ttyAMA0'
SERIAL_RATE = 9600

def list_ports():
	list = serial.tools.list_ports.comports()
	connected = []
	for element in list:
		connected.append(element.device)
	print("Connected COM ports: " + str(connected))
	return connected

def main(connected):
	print(connected)
	ser = serial.Serial(connected, SERIAL_RATE)
	while True:
		# using ser.readline() assumes each line contains a single reading
		# sent using Serial.println() on the Arduino
		reading = ser.readline().decode('utf-8')
		# reading is a string...do whatever you want from here
		print(reading)


if __name__ == "__main__":
	connected = list_ports()
	main(connected)