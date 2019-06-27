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
import datetime
import time
now = datetime.datetime.now()

import csv
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
        self.newData=False
        self.data=[]
        #plot new data every plotCount data acquisitions
        self.plotCount=plotCount
        self.count=0
        #flag for header line
        self.isHeader=False
        #grab an OScope
        self.Oscope=OScope()
        #grab a TC Logger
        self.TC=TLogger()
        self.saveStr="ShearTest_"+now.strftime("%Y_%m_%d")+".csv"
    def getData(self):
        self.newData=False
        return self.data
    def run(self):
        while not self.stopped.wait(self.period):
            #get system time (for logging purposes)
            curTime = datetime.datetime.now()
            if not self.isHeader:
                self.startTime=curTime
            curTime=curTime-self.startTime
            #get temperature in C
            temp = self.TC.getTemp()

            #time, shear mod data

            data = self.Oscope.getData()

            self.data=[curTime,temp,data[0],data[1]]
            # saveData to csv format
            header=['time','temp', 'peak time', 'shear']
            with open(self.saveStr, 'a',newline='') as resultFile:

                wr = csv.writer(resultFile, dialect='excel')
                if not self.isHeader:
                    wr.writerow(header)
                    self.isHeader= True

                wr.writerow(self.data)
            self.count=self.count+1
            if self.count is self.plotCount:
                print("Shear is: {}".format(data[1]))
                print("Temp is {}".format(temp))
                print("Time is: {}".format(data[0]))

                #time to plot data, set plot Data flag
                self.newData = True
                self.count=0

timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)
## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    stopFlag = Event()
    rgaTimer = timerPP(plotCount=5, event=stopFlag, period=.1)
    rgaTimer.start()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()



