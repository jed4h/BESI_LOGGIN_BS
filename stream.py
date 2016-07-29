# the stream_process function receives and plots sensor data from a single BBB
from datetime import datetime
from pyqtgraph.Qt import QtGui, QtCore
from streamUtils import *
from parameters import *
from BikeCadence import peakDetection
from streamAccel import update_accel
from streamLight import update_light
from streamSound import update_sound
from streamTemp import update_temp
from streamDoor import update_door
from processSession import processSession
from colorama import init
import time


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
def stream_process(commQueue = None, PORT = 9999, USE_ACCEL = True, USE_LIGHT = True, USE_ADC = True, ShimmerIDs = [None, None, None], PLOT=True, fileLengthSec = 600, fileLengthDay = 0, DeploymentID = 1, networkNum = 1, ProcNum = 0):
    global faccel
    global soundFile
    global tempFile
    global doorFile
    global flight
    global plotStartTime
    global sensorTimeouts
    global connected
    t = []
    x = []
    y = []
    z = []
    light = []
    sound = []
    temp = []
    sound_sum = []
    door1 = []
    door2 = []
    
    #
    global connection
    global connection2
    global connection3
    global connection4
    global connection5
    
    
   
    # write start time
    # Now done in stream when data is first received
    #faccel.write(str(datetime.now()) + '\n')
    #flight.write(str(datetime.now()) + '\n')
    #soundFile.write(str(datetime.now()) + '\n')
    #tempFile.write(str(datetime.now()) + '\n')
    
    # send info to the BBB: Shimmer Bluetooth ID and what sensors to use
    # this uses the same port as the accelerometer and closes it after sending the info
    
    # process raw data from last deployment
    #processSession(PORT)
    
    #root = Tk()
    #root.title("RS {}".format(PORT))
    #root.geometry("230x150+100+100")
   
    time.sleep(ProcNum)
   
    printOffset = ProcNum * 5 + 1
    init()
    print '\x1b[{};1H'.format(printOffset + 0)
    print '-------Relay Station {}-------------'.format(PORT)
    """
    print '\x1b[{};1H'.format(printOffset + 1)
    print 'Accel: 0000-00-00 00:00:00.000000  000'
    print '\x1b[{};1H'.format(printOffset + 2)
    print 'ADC:   0000-00-00 00:00:00.000000  000'
    print '\x1b[{};1H'.format(printOffset + 3) 
    print 'Light: 0000-00-00 00:00:00.000000  000'
    """   
    while True:
        #try:
        connection = connectRecv(PORT, networkNum, None)
        connection.settimeout(5)
        # format is <sensor name> <number of samples>
        sensorStatus = connection.recv(1024).split(" ")
        if len(sensorStatus) >= 2:
            if sensorStatus[1] == "Accelerometer":
                printRSstatus(line1 = 'Accel: {}  {}         '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[1] == "ADC":
                printRSstatus(line2 = 'ADC:   {}  {}  '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[1] == "light":
                printRSstatus(line3 = 'Light: {}  {}  '.format(datetime.now(), sensorStatus[0]), offset = printOffset)
            elif sensorStatus[0] == "starting":
                printRSstatus(line1 = 'Accel: {}  {}'.format(datetime.now(), 000), offset = printOffset)
                printRSstatus(line2 = 'ADC:   {}  {}'.format(datetime.now(), 000), offset = printOffset)
                printRSstatus(line3 = 'Light: {}  {}'.format(datetime.now(), 000), offset = printOffset)
            elif sensorStatus[1] == "Connected":
                printRSstatus(line1 = 'Accel: {}  Connected'.format(datetime.now()), offset = printOffset)
            elif sensorStatus[1] == "Disconnected":
                pass
                
            else:
                print "error parsing RS status"
                print sensorStatus
            
        configMsg = "{},{},{},".format( ShimmerIDs[0], ShimmerIDs[1], datetime.now())
        connection.sendall("{:03}".format(len(configMsg)) + configMsg)
        connection.close()
        #except:
            #print "error updating relay station"

    
    connected = 2
    app = QtGui.QApplication([])
    if PLOT:
        win, curves = init_plot(PORT)
        
    plotStartTime = datetime.now()
    
    # update is called every 5 ms and updates the data for each plot
    def update():
        global connected
        global faccel
        global soundFile
        global tempFile
        global doorFile
        global flight
        global plotStartTime
        global sensorTimeouts
        global connection
        global connection2
        global connection3
        global connection4
        global connection5
        
        plotCurrTime = datetime.now()
        # periodically process the raw data received and open new raw data files (old ones are deleted)
        if (((plotCurrTime - plotStartTime).seconds == fileLengthSec) and ((plotCurrTime - plotStartTime).days == fileLengthDay) or connected == 0):
            plotStartTime = datetime.now()
            
            # close files
            if USE_ACCEL:
                faccel.close()
                
            if USE_ADC:
                soundFile.close()
                tempFile.close()
                doorFile.close()
                
            if USE_LIGHT:
                flight.close()
            
            # process data (result is written to new files)
            processSession(PORT)
            
            # open new files that overwrite old temporary files
            if USE_ACCEL:
                faccel = open("Data_Deployment_{}/relay_Station_{}/accel{}".format(DeploymentID, PORT, PORT), "w")
                
            if USE_ADC:
                soundFile = open("Data_Deployment_{}/relay_Station_{}/sound{}".format(DeploymentID, PORT, PORT), "w")
                tempFile = open("Data_Deployment_{}/relay_Station_{}/temp{}".format(DeploymentID, PORT, PORT), "w")
                doorFile = open("Data_Deployment_{}/relay_Station_{}/door{}".format(DeploymentID, PORT, PORT), "w")
                
            if USE_LIGHT:
                flight = open("Data_Deployment_{}/relay_Station_{}/light{}".format(DeploymentID, PORT, PORT), "w")
        
        # if connection is lost, wait set up the port to listen for the reconnect from the relay station
        if connected == 0:
            connected = 1
            conectFromRS(PORT, networkNum, ShimmerIDs, DeploymentID, USE_ACCEL, USE_ADC, USE_LIGHT)
            
            connected = 2
            
            
        if connected == 2:  
            plot_update_all(commQueue, connection, connection2, connection3, connection4, connection5, faccel, flight, soundFile, tempFile, doorFile, t, x, y ,z, light, sound, sound_sum, temp, door1, door2, sensorTimeouts, USE_ACCEL, USE_LIGHT, USE_ADC, PORT)
            if PLOT:
                curves[0].setData(x)
                curves[1].setData(y)
                curves[2].setData(z)
                curves[3].setData(t)
                curves[4].setData(light)
                curves[5].setData(sound)
                curves[7].setData(temp)
                curves[8].setData(door1)
                curves[9].setData(door2)
            
            # application that prints the cadence of someone biking       
            #if BIKE_CADENCE:
                # intervals is meaningless because only raw timestamps are available
                #pedal_count, intervals = peakDetection(x[120:], y[120:], t[120:])
                #print pedal_count
    
    # set up a timer to run update() every 5 ms   
    timer1 = QtCore.QTimer()
    timer1.timeout.connect(update)
    timer1.start(5)
    
    # keeps the program running while the plot window is open
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    
    # cleanup: close files and write end time to accel file
    # I don't think this code is ever called
    # TODO: find a way to close the files when done
    #faccel.write(str(datetime.now()) + '\n')
    faccel.close()
    flight.close()
    soundFile.close()
    tempFile.close()
    doorFile.close()
    processSession(PORT)
    print "Exiting {}".format(PORT)
    
# runs update functions for each sensor used
# update functions check if data is ready and update the plot ifit is
#con1 = accel, con2 = light, con3 = sound, con4 = temp
def plot_update_all(q, con1, con2, con3, con4, con5, faccel, flight, soundFile, tempFile, doorFile, t, x, y ,z, light, sound, sound_sum, temp, door1, door2, sensorTimeouts, USE_ACCEL, USE_LIGHT, USE_ADC, PORT):
    # sensorTimeouts is used to to check if no messages have been received about a particular sensor for a period of time 
    # every time update_<sensor> is called and there is no data waiting sensorTimeout is incremented. When sensorTimeout reaches some threshold, an alert is triggered
    # update accel
    global connected
    """
    if USE_ACCEL:
        update_accel(con1, faccel, t, x, y, z)
         
    # update light
    if USE_LIGHT:
        update_light(con2, flight, light)

    # update ADC (noise and temp)
    if USE_ADC:
        update_sound(con3, soundFile, sound, sound_sum)
        update_temp(con4, tempFile, temp)
        update_door(con5, doorFile, door1, door2)
    """
    if USE_ACCEL:
        if (update_accel(con1, faccel, t, x, y, z) == 1):
            sensorTimeouts[0] = sensorTimeouts[0] + 1
            
        else:
            sensorTimeouts[0] = 0
            
        if sensorTimeouts[0] == 10 * LOST_CONN_TIMEOUT:
            #q.put(["{0} no connection from shimmer".format(PORT)])
            sensorTimeouts[0] = 0
        
    
               
    # update ADC (noise and temp)
    if USE_ADC:
        if (update_sound(con3, soundFile, sound) == 1):
            sensorTimeouts[2] = sensorTimeouts[2] + 1   
        else:
            sensorTimeouts[2] = 0
        if sensorTimeouts[2] == 10 * LOST_CONN_TIMEOUT:
            #q.put(["{0} no data from microphone".format(PORT)])
            sensorTimeouts[2] = 0
            
        if (update_temp(con4, tempFile, temp) == 1):
            sensorTimeouts[3] = sensorTimeouts[3] + 1
        else:
            sensorTimeouts[3] = 0 
        if sensorTimeouts[3] == LOST_CONN_TIMEOUT:
            #q.put(["{0} no data from temperature sensor".format(PORT)])
            sensorTimeouts[3] = 0
            #############################################################
            #Reset if connection lost (use light sensor to measure this)#
            #############################################################
            connected = 0
            con1.close()
            con2.close()
            con3.close()
            con4.close()
            con5.close()
            print "Ports Closed"
            return
            
        if (update_door(con5, doorFile, door1, door2) == 1):
            sensorTimeouts[4] = sensorTimeouts[4] + 1 
        else:
            sensorTimeouts[4] = 0 
        if sensorTimeouts[4] == 10 * LOST_CONN_TIMEOUT:
            #q.put(["{0} no data from door sensor".format(PORT)])
            sensorTimeouts[4] = 0
            
    # update light
    if USE_LIGHT:
        if (update_light(con2, flight, light) == 1):
            sensorTimeouts[1] = sensorTimeouts[1] + 1
            
        else:
            sensorTimeouts[1] = 0
            
        if sensorTimeouts[1] == LOST_CONN_TIMEOUT:
            #q.put(["{0} no data from light sensor".format(PORT)])
            sensorTimeouts[1] = 0
            
            
            #############################################################
            #Reset if connection lost (use light sensor to measure this)#
            #############################################################
            connected = 0
            con1.close()
            con2.close()
            con3.close()
            con4.close()
            con5.close()
            print "Ports Closed"

def conectFromRS(PORT, networkNum, ShimmerIDs, DeploymentID, USE_ACCEL, USE_ADC, USE_LIGHT):
    global faccel
    global soundFile
    global tempFile
    global doorFile
    global flight
    
    global connection
    global connection2
    global connection3
    global connection4
    global connection5
    
    isConnected = False
    while not isConnected:
        try:
            # first connection does not have a timeout
            connection = connectRecv(PORT, networkNum, None)
            configMsg = "{},{},{},{},{},{},{},".format(USE_ACCEL, USE_ADC, USE_LIGHT, ShimmerIDs[0], ShimmerIDs[1], ShimmerIDs[2], datetime.now())
            connection.sendall("{:03}".format(len(configMsg)) + configMsg)
            connection.close()
        except:
            print "error sending config info"
            continue
        """
        # establish socket connections for each sensor used
        if USE_ACCEL:
            connection = connectRecv(PORT, networkNum, INITIAL_CONNECT_TIMEOUT)
            # these connections should happen quickly, so if one times out, go back to the beginning of the connection sequence
            if connection == None:
                print "Accel connect timeout"
                continue
            faccel = open("Data_Deployment_{}/relay_Station_{}/accel{}".format(DeploymentID, PORT, PORT), "w")
        else:
        """
        connection = None
        """   
        if USE_LIGHT:
            connection2 = connectRecv(PORT + 1, networkNum, INITIAL_CONNECT_TIMEOUT)
            if connection2 == None:
                print "Light connect timeout"
                continue
            flight = open("Data_Deployment_{}/relay_Station_{}/light{}".format(DeploymentID, PORT, PORT), "w")
        else:
            connection2 = None
         """
        connection2 = None
        """
        if USE_ADC:
            connection3 = connectRecv(PORT + 2, networkNum, INITIAL_CONNECT_TIMEOUT)
            if connection3 == None:
                print "Sound connect timeout"
                continue
            connection4 = connectRecv(PORT + 3, networkNum, INITIAL_CONNECT_TIMEOUT)
            if connection4 == None:
                print "Temp connect timeout"
                continue
            connection5 = connectRecv(PORT + 4, networkNum, INITIAL_CONNECT_TIMEOUT)
            if connection5 == None:
                print "Door connect timeout"
                continue
            soundFile = open("Data_Deployment_{}/relay_Station_{}/sound{}".format(DeploymentID, PORT, PORT), "w")
            tempFile = open("Data_Deployment_{}/relay_Station_{}/temp{}".format(DeploymentID, PORT, PORT), "w")
            doorFile = open("Data_Deployment_{}/relay_Station_{}/door{}".format(DeploymentID, PORT, PORT), "w")
        else:
        """
        connection3 = None
        connection4 = None
        connection5 = None
         
        isConnected = True
    return connection, connection2, connection3, connection4, connection5
