# -*- coding: utf-8 -*-
"""
Various methods of drawing scrolling plots.
"""
# inputs from user:
    #height, density, sample rate
    # ratio of points to graph vs save default (5:1)
    # data to save: time,temp. time between peaks, sheer mod,
    # data to plot: Shear mod vs temp
    #buttons: Start, stop, pause, Check Peaks
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
from threading import Thread
from threading import Event
from Oscope import OScope
from temperature import TLogger
from ArduinoTCReader import arduinoTC
import datetime
from multiprocessing.pool import ThreadPool
import time
import ctypes
now = datetime.datetime.now()
import csv
import sys
##########################
##########################
###EDIT CONFIG PARAMS HERE:
H=.006 #m
RHO= 7800#7715#kg/m3
saveloc="C:\\Users\\LAB\\PycharmProjects\\shearTest\\ShearDaleReb\\"
sampleName= "Ni239 test piece"
#aqcuire data from pyrometer
isPyrometer=True
##########################
##########################


isSaveData=ctypes.windll.user32.MessageBoxW(0, "Do you want to save waveforms?","Save Waveforms?",4)
if (isSaveData  == 6):
    print("will save data")
    isSaveData=True
else:
    print("will not save data")
    isSaveData=False

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
win = pg.GraphicsWindow()
win.setWindowTitle('Shear Data')
#need shear mod, temp data
nData=2
# 2) Allow data to accumulate. In these examples, the array doubles in length
#    whenever it is full.
#p3 = win.addPlot()
#win.nextRow()
p4 = win.addPlot()
# Use automatic downsampling and clipping to reduce the drawing load
#p3.setDownsampling(mode='peak')
p4.setDownsampling(mode='peak')
#p3.setClipToView(True)
p4.setClipToView(True)
#p3.setRange(xRange=[-1000, 0])
p4.setLogMode(False,False)

#p3.setLimits(xMax=0)
#curve3 = p3.plot()
curve = []
names=['Shear Mod']
#legend=p4.addLegend()
curve.append(p4.plot())
#for i in range(nData):
    #curve.append(p4.plot())
    #legend.addItem(curve[i],names[i])
data = np.empty([nData,100])
ptr3 = 0



def update():
        if (rgaTimer.newData):
            data=rgaTimer.getData()
            # data format: time,temp. time between peaks, sheer mod
            #grab temp, shear mod
            plotData=[data[1],data[3]]
            plot(plotData)
#data should besent as columns of temp, shear mod
def plot(newData):
    colors=['b']
    global data, ptr3
    data[:,ptr3] = newData
    ptr3 += 1
    if ptr3 >= data.shape[1]:
        tmp = data
        data = np.empty([nData,data.shape[1] * 2])
        data[:,0:tmp.shape[1]] = tmp
    #x data is temperature, y data is shear modulus
    curve[0].setData(data[0, :ptr3],data[1, :ptr3], pen=colors[0], symbol='o', symbolBrush=colors[0])
    #for i in range(nData):
        # Blue Dots
        #curve[i].setData(data[i,:ptr3], pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=(colors[i]))
       #curve[i].setData(data[i,:ptr3],  pen=colors[i],symbol='o',symbolBrush=colors[i])


#timer = pg.QtCore.QTimer()
#timer.timeout.connect(update)
#timer.start(50)


class timerPP(Thread):
    def __init__(self,plotCount,event,period):
        Thread.__init__(self)
        self.stopped = event
        self.period=period
        self.waitTime=0
        self.newData=False
        self.data=[]
        #plot new data every plotCount data acquisitions
        self.plotCount=plotCount
        self.count=0
        #flag for header line
        self.isHeader=False
        #grab an OScope
        self.Oscope=OScope(saveLoc=saveloc)
        self.Oscope.configSample(h=H,rho=RHO)
        #grab a TC Logger
        if (not isPyrometer):
            self.TC=TLogger()
        else:
            self.TC=arduinoTC()
            self.pyro=arduinoTC('COM7')
        #os.mkdir("/ShearTest_"+now.strftime("%Y_%m_%d"))
        self.saveStr=saveloc+"ShearTest_"+now.strftime("%Y_%m_%d")+".csv"
    def getData(self):
        self.newData=False
        return self.data
    def getPyroTemp(self):
        TCdata=self.TC.getTemp()
        if isPyrometer:
            pyroData=self.pyro.getTemp()
        else:
            pyroData=[-1,-1]
        result=[]
        result.append(TCdata[0])
        result.append(pyroData[1])
        return result
    def run(self):
        while not self.stopped.wait(self.waitTime):
            #record loop time
            startTime=time.time()
            #get system time (for logging purposes)
            if not self.isHeader:
                data = self.Oscope.getData(isPlot=True)
            curTime = datetime.datetime.now()
            now= datetime.datetime.now()
            if not self.isHeader:
                self.startTime=curTime
            curTime=now.strftime("%H:%M:%S.%f")#curTime-self.startTime
            #get temperature in C

            self.count = self.count + 1

            #multithread
            now = (datetime.datetime.now())
            tcThread = ThreadPool(processes=1)  # (target=self.TC.getTemp)

            async_result = tcThread.apply_async(self.getPyroTemp)
            data = self.Oscope.getData(saveData=isSaveData)
            #if self.count is self.plotCount:

                #data = self.Oscope.getData(saveData=isSaveData)
            #else:
             #   data = self.Oscope.getData()

            TCdata= async_result.get()  # get return value from getTemp
            #print("getting results")
            if not isPyrometer:
                temp =TCdata[0]
                pyro=-1
            else:
                temp=TCdata[0]
                pyro=TCdata[1]
            print(datetime.datetime.now() - now)


            #temp = self.TC.getTemp()
            #time, shear mod data


            self.data=[curTime,temp,pyro,data[0],data[1]]
            # saveData to csv format
            configData="H= {},RHO={}, sample={}".format(H,RHO,sampleName)
            header=['time','temp','pyro', 'peak time', 'shear',configData]
            with open(self.saveStr, 'a',newline='') as resultFile:

                wr = csv.writer(resultFile, dialect='excel')
                if not self.isHeader:
                    wr.writerow(header)
                    self.isHeader= True

                wr.writerow(self.data)
            if self.count is self.plotCount:
                print("Shear is: {}".format(data[1]))
                print("Temp TC is {}".format(temp))
                print("Pyro Te is {}".format(pyro))
                print("Time is: {}".format(data[0]))

                #time to plot data, set plot Data flag
                self.newData = True
                self.count=0
            self.waitTime=self.period-(time.time()-startTime)
            if self.waitTime<0:
                self.waitTime=0

timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)
if __name__ == '__main__':
    import sys

    stopFlag = Event()
    rgaTimer = timerPP(plotCount=5, event=stopFlag, period=.1)
    rgaTimer.start()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()  ## Start Qt event loop unless running in interactive mode or using pyside.





