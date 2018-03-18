import sys, os
from collections import OrderedDict
import time
import threading
from lpmslib import LpmsNAV
from lpmslib import lputils

##############################
# User settings
port = 'COM3'
baudrate = 115200
##############################

TAG="MAIN"
printer_running = False
stop_running = True
lpmsSensor = LpmsNAV.LpmsNAV(port, baudrate)

def pretty_print_sensor_data(sensor_data):
    j = 25
    d = '.'
    print ("Frame Counter:".ljust(j, d), sensor_data[0])
    print ("Angle (deg):".ljust(j, d), sensor_data[1])
    print ("AngVel (deg/s):".ljust(j, d), sensor_data[2])
    print ("Acc (g):".ljust(j, d), ['%+.3f' % f for f in sensor_data[3]])
    print ("Press enter to quit")

def get_stream_data():
    sensor_data = lpmsSensor.get_stream_data()
    pretty_print_sensor_data(sensor_data)

def print_data():
    thread = threading.Thread(target=printer, args=())
    global stop_printing
    stop_printing = False
    thread.start()

def stop_print_data():
    global stop_printing
    global thread
    global printer_running
    stop_printing = True
    if printer_running and thread.isAlive():
        thread.join()        

def printer():
    global stop_printing
    global printer_running
    printer_running = True
    while not stop_printing:
        os.system('cls')
        get_stream_data()
        time.sleep(.05)
    printer_running = False


thread = threading.Thread(target=printer, args=())
def main():
    quit = False
    lputils.logd(TAG, "Connecting sensor")
    if not lpmsSensor.connect():
        lputils.loge(TAG, "Error connecting to sensor, terminating..")
        return

    lputils.logd(TAG, "Connected")
    print_data()

    while not quit:
        choice = raw_input(" >>  ")
        quit = True
    stop_print_data()
    
    lputils.logd(TAG, "Disconnecting sensor")
    lpmsSensor.disconnect()
    lputils.logd(TAG, "Disconnected")
    lputils.logd(TAG, "bye")

if __name__ == "__main__":
    # Launch main menu
    main()
