#-------------------------------------------------------------------------------
#  Get a screen catpure from DPO4000 series scope and save it to a file

# python        2.7         (http://www.python.org/)
# pyvisa        1.4         (http://pyvisa.sourceforge.net/)
# numpy         1.6.2       (http://numpy.scipy.org/)
# MatPlotLib    1.0.1       (http://matplotlib.sourceforge.net/)
#-------------------------------------------------------------------------------


import visa
import numpy as np
import datetime
from struct import unpack
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

class OScope:
    def __init__(self, port='USB0::0x0699::0x0374::C012252::INSTR'):
        rm = visa.ResourceManager()
        scope = rm.get_instrument(port)
        #scope.timeout = 25000
        scope.write('DATA:SOU CH1')
        scope.write('DATA:WIDTH 1')
        scope.write('DATA:ENC RPB')
        self.scope=scope
        self.getConfigData()
        #self.configSample()
    #h is height of sample (m), rho is density of sample (kg/m^3)
    def configSample(self,h=.00948,rho=8960):
        self.h=h
        self.rho=rho
    def getConfigData(self):
        self.ymult = float(self.scope.query('WFMPRE:YMULT?'))
        self.yzero = float(self.scope.query('WFMPRE:YZERO?'))
        self.yoff = float(self.scope.query('WFMPRE:YOFF?'))
        self.xincr = float(self.scope.query('WFMPRE:XINCR?'))
    def getData(self,isPlot=False):
        now = datetime.datetime.now()
        data=self.scope.write('CURVE?')

        data = self.scope.read_raw()
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))
        Volts = (ADC_wave - self.yoff) * self.ymult  + self.yzero
        Time = np.arange(0, self.xincr * len(Volts), self.xincr)
        peaks, _ = find_peaks(Volts,distance=200,height=2)
        if peaks.size>=4:
            time=Time[peaks[3]]-Time[peaks[2]]
            #print("Time is: {}".format(time))
        if (isPlot):
            plt.plot(Volts)
            plt.plot(peaks, Volts[peaks], 'bx')
            # plt.plot(Time, Volts,'b')#,peaks)#,Volts[peaks],'bx')
            plt.show()
        # G=(2h/t)^2/rho, h=height of sample, t is time between peaks 3 and 4, rho=density

        G= (2*self.h/time)*(2*self.h/time)/self.rho
        #print("Shear is: {}".format(G))
        data=[time,G]
        #print("oscope acquisition time is {}".format(datetime.datetime.now()-now))

        return data

