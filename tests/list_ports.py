import serial.tools.list_ports
list = serial.tools.list_ports.comports()
connected = []
for element in list:
    connected.append(element.device)
print("Connected COM ports: " + str(connected))