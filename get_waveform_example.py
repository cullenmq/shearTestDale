#-------------------------------------------------------------------------------
#  Get a screen catpure from DPO4000 series scope and save it to a file

# python        2.7         (http://www.python.org/)
# pyvisa        1.4         (http://pyvisa.sourceforge.net/)
# numpy         1.6.2       (http://numpy.scipy.org/)
# MatPlotLib    1.0.1       (http://matplotlib.sourceforge.net/)
#-------------------------------------------------------------------------------

import visa
import numpy as np
from struct import unpack
import pylab
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
rm = visa.ResourceManager()
scope = rm.get_instrument('USB::0x0699::0x0374::C012252::INSTR')


scope.write('DATA:SOU CH1')
scope.write('DATA:WIDTH 1')
scope.write('DATA:ENC RPB')


ymult = float(scope.query('WFMPRE:YMULT?'))
yzero = float(scope.query('WFMPRE:YZERO?'))
yoff = float(scope.query('WFMPRE:YOFF?'))
xincr = float(scope.query('WFMPRE:XINCR?'))


scope.write('CURVE?')
data = scope.read_raw()
headerlen = 2 + int(data[1])
header = data[:headerlen]
ADC_wave = data[headerlen:-1]

ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))

Volts = (ADC_wave - yoff) * ymult  + yzero

Time = np.arange(0, xincr * len(Volts), xincr)
peaks, _ = find_peaks(Volts,height=0.5)
plt.plot(Volts)
plt.plot(peaks,Volts[peaks],'bx')
#plt.plot(Time, Volts,'b')#,peaks)#,Volts[peaks],'bx')
plt.show()
