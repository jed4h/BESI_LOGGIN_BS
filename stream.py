# the stream_process function receives and plots sensor data from a single BBB
from datetime import datetime
from pyqtgraph.Qt import QtGui, QtCore
from streamUtils import *
from parameters import *
from processSession import processSession
from colorama import init
import time

# NOTE: colorama does not work when run from eclipse


# initialize file names so they can be accessed in the update() function
faccel = None
soundFile = None
tempFile = None
doorFile = None
flight = None
plotStartTime = None
sensorTimeouts = [0] * 5 #tracks time since last packet received for each sensor
# connection status indicator:
# 0 - disconnected
# 1 - connection in progress
# 2 - connected
connected = 0




# receives data from the BBB using a different socket for each sensor
# the port number for the accelerometer is given, and the other sockets are consecutive numbers following PORT
def stream_process(commQueue = None, PORT = 9999, USE_ACCEL = True, USE_LIGHT = True, USE_ADC = True, ShimmerIDs = [None, None, None], PLOT=True, fileLengthSec = 600, fileLengthDay = 0, DeploymentID = 1, networkNum = 1, ProcNum = 0, lock=None):
    global faccel
    global soundFile
    global tempFile
    global doorFile
    global flight
    global plotStartTime
    global sensorTimeouts
    global connected
    
    
    #
    global connection
    global connection2
    global connection3
    global connection4
    global connection5
   
    printOffset = ProcNum * 5 + 1
    
    # need locks around print statements from each process to get them to display in the correct location
    #######################################
    # critical section
    lock.acquire()
    # colorama init
    init()
    # Colorama is used to set curse position for printing
    # format is \x1b[y;xH where y = position down, x = position across
    print '\x1b[{};1H'.format(printOffset + 0)
    print '-------Relay Station {}-------------'.format(PORT)
     ####################################
    # end of critial section
    lock.release() 
    
    while True:
        #try:
        connection = connectRecv(PORT, networkNum, None)
        connection.settimeout(5)
        # format is <sensor name> <number of samples>
        sensorStatus = connection.recv(1024).split(" ")
        #######################################
        # critical section
        lock.acquire()
        # print update based on sensor and message from relay station
        if len(sensorStatus) >= 2:
            if sensorStatus[1] == "Accelerometer":
                printRSstatus(line1 = 'Accel: {}  {}                          '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[1] == "ADC":
                printRSstatus(line2 = 'ADC:   {}  {}                          '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[1] == "light":
                printRSstatus(line3 = 'Light: {}  {}                          '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[1] == "weather":
                printRSstatus(line4 = 'Weather: {}  {}                        '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[0] == "starting":
                printRSstatus(line1 = 'Accel: {}  {}                          '.format(datetime.now(), 000), offset = printOffset)
                printRSstatus(line2 = 'ADC:   {}  {}                          '.format(datetime.now(), 000), offset = printOffset)
                printRSstatus(line3 = 'Light: {}  {}                          '.format(datetime.now(), 000), offset = printOffset)
                printRSstatus(line4 = 'Weather: {}  {}                       '.format(datetime.now(), 000), offset = printOffset)
            elif sensorStatus[1] == "Connected":
                printRSstatus(line1 = 'Accel: {}  Connected                    '.format(datetime.now()), offset = printOffset)
            elif sensorStatus[1] == "Disconnected":
                pass
                
            else:
                print "error parsing RS status"
                print sensorStatus
        ####################################
        # end of critial section
        lock.release() 
        
        # send back Shimmer IDs and Start Time
        # Shimmer IDs is only needed on first connect, and timestamp is only needed when the relay station starts a new file
        configMsg = "{},{},{},".format( ShimmerIDs[0], ShimmerIDs[1], datetime.now())
        connection.sendall("{:03}".format(len(configMsg)) + configMsg)
        connection.close()
        #except:
            #print "error updating relay station"

    
   
