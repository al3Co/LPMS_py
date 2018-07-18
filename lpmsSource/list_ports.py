# Create a list "Connected", which contains the elements attached on serial ports
import serial.tools.list_ports


list = serial.tools.list_ports.comports()
connected = []
for element in list:
    connected.append(element.device)
print(list)
print("Connected COM ports: " + str(connected))