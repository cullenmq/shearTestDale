#-------------------------------------------------------------------------------
#  Get a screen catpure from DPO4000 series scope and save it to a file

# python        2.7         (http://www.python.org/)
# pyvisa        1.4         (http://pyvisa.sourceforge.net/)
# numpy         1.6.2       (http://numpy.scipy.org/)
# MatPlotLib    1.0.1       (http://matplotlib.sourceforge.net/)
#-------------------------------------------------------------------------------

import csv
import visa
import numpy as np
import datetime
from struct import unpack
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import time
#bounds in GPa
upper=60E9
lower=30E9
class OScope:
    def __init__(self, port='USB0::0x0699::0x0374::C012252::INSTR',saveLoc=""):
        self.saveLoc=saveLoc
        self.rm = visa.ResourceManager()
        scope = self.rm.get_instrument(port)
        self.scope=scope
        scope.write('DATA:SOU CH1')
        scope.write('DATA:WIDTH 1')
        scope.write('DATA:ENC RPB')
        print(scope.query('WFMOutpre?'))
        #scope.write('HOR:MODE:SAMPLERATE')
        self.scope=scope
        self.getConfigData()
        self.configTempChannel()
        self.configPyro()
    def __del__(self):
        print("closing oscope")
        self.ymult = float(self.scope.query('WFMPRE:YMULT?'))
        self.scope.clear()
        self.scope.close()
        self.rm.close()
        #self.configSample()
    #h is height of sample (m), rho is density of sample (kg/m^3)

    def configSample(self,h=.00948,rho=8960):
        self.h=h
        self.rho=rho
    def configTempChannel(self):
        self.scope.write('DATA:SOU CH2')
        print(self.scope.query('WFMPRE:XINCR?'))
        self.Tymult = float(self.scope.query('WFMPRE:YMULT?'))
        self.Tyzero = float(self.scope.query('WFMPRE:YZERO?'))
        self.Tyoff = float(self.scope.query('WFMPRE:YOFF?'))
    def configPyro(self):
        self.scope.write('DATA:SOU CH3')
        self.Pyroymult = float(self.scope.query('WFMPRE:YMULT?'))
        self.Pyroyzero = float(self.scope.query('WFMPRE:YZERO?'))
        self.Pyroyoff = float(self.scope.query('WFMPRE:YOFF?'))
    def getTemp(self):
        #set scope to channel 2
        self.scope.write('DATA:SOU CH2')

        #acquire data
        data = self.scope.write('CURVE?')
        data = self.scope.read_raw()
        #throw out header
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave), ADC_wave))
        #convert to voltage
        Volts = (ADC_wave - self.Tyoff) * self.Tymult + self.Tyzero
        volt=np.average(Volts[3900:4000])
        #save first element in voltage
        return((volt-1.25)/.005)
    def getPyro(self):
        #set scope to channel 2
        self.scope.write('DATA:SOU CH3')

        #acquire data
        data = self.scope.write('CURVE?')
        data = self.scope.read_raw()
        #throw out header
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave), ADC_wave))
        #convert to voltage
        Volts = (ADC_wave - self.Pyroyoff) * self.Pyroymult + self.Pyroyzero
        volt=np.average(Volts[3900:4000])
        #save first element in voltage
        return(volt*80+200)
    def getConfigData(self):
        self.ymult = float(self.scope.query('WFMPRE:YMULT?'))
        self.yzero = float(self.scope.query('WFMPRE:YZERO?'))
        self.yoff = float(self.scope.query('WFMPRE:YOFF?'))
        self.xincr = float(self.scope.query('WFMPRE:XINCR?'))
        self.scope.write('DATA:Start 0')
        self.scope.write('DATA:Stop 12000')
    def getData(self,isPlot=False,saveData=False):
        now = datetime.datetime.now()
        self.scope.write('DATA:SOU CH1')
        #self.getConfigData()
        #print("time 1 is: {}".format(datetime.datetime.now()-now))

        data=self.scope.write('CURVE?')


        data = self.scope.read_raw()
        #print("time 2 is: {}".format(datetime.datetime.now() - now))
        #print(datetime.datetime.now() - now)
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))
        Volts = (ADC_wave - self.yoff) * self.ymult  + self.yzero
        Time = np.arange(0, self.xincr * len(Volts), self.xincr)
        #peaks, _ = find_peaks(Volts,distance=500,height=.9,prominence=1)
        peaks, _ = find_peaks(Volts, distance=500, height=.2, prominence=1)
        numpeaks=peaks.size
        #print("time 3 is: {}".format(datetime.datetime.now() - now))
        if numpeaks>=2:
            G=0
            i=0
            while(G<(lower) or G>(upper)):
                time=Time[peaks[i+1]]-Time[peaks[i]]
            #print("Time is: {}".format(time))
                G = ((2 * self.h / time) * (2 * self.h / time)) * self.rho
                i=i+1
                if i == numpeaks-1:
                    break
         #   print("peaks used: {} and {}".format(i,(i+1)))
        else:
            time=-1
            G=-1
        #print("time 4 is: {}".format(datetime.datetime.now() - now))
        if (isPlot):
            plt.plot(Volts)
            plt.plot(peaks, Volts[peaks], 'bx')
            # plt.plot(Time, Volts,'b')#,peaks)#,Volts[peaks],'bx')
            plt.show()
        # G=(2h/t)^2/rho, h=height of sample, t is time between peaks 3 and 4, rho=density


        #print("Shear is: {}".format(G))
        data=[time,G]
        #print("oscope acquisition time is {}".format(datetime.datetime.now()-now))
        if saveData:
            print("saving data!")
            saveStr = self.saveLoc+"ShearTest_" + now.strftime("%Y_%m_%d_%H%M%S") + ".csv"
            with open(saveStr, 'a',newline='') as resultFile:
                wr = csv.writer(resultFile, dialect='excel')
                wr.writerow(peaks)
                for i in range(Time.size):
                    saveThis=[Time[i],Volts[i]]
                    wr.writerow(saveThis)
        return data

