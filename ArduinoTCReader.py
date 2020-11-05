import serial
import time
class arduinoTC:
    def __init__(self,port='COM6',baud=57600):
        self.port = serial.Serial(port, baud)
        self.readDataStr="*R"
    def getTemp(self):
        self.port.write(str.encode(self.readDataStr))
        data=self.port.readline().decode()
        data=data.split(",")
        data[0]=float(data[0])
        data[1]=int(data[1])*.08+200
        return data

#test=arduinoTC()
#startTime=time.perf_counter()
#test.getTemp()
#print(time.perf_counter()-startTime)