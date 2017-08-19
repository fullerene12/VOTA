'''
Created on Aug 9, 2017

@author: Hao Wu
'''
import numpy as np
import serial
import time
from queue import Queue
import h5py as h5

class ArduinoWaterDev(object):
    '''
    classdocs
    '''

    def __init__(self, port='COM6',baud_rate=250000):
        '''
        Constructor
        '''
        self.port=port
        self.baud_rate=baud_rate
        self.ser=serial.Serial(self.port,self.baud_rate,timeout=1)
        #self.open()
        
        
    def drop_water(self,wait_time=20):
        output=b'\x77'
        output=output+int(wait_time).to_bytes(1,'little')
        self.ser.write(output)
        #print(output)

    def read(self):
        return self.ser.readline()
    
    def open(self):
        self.ser.open()
        time.sleep(2)
        
    def close(self):
        self.ser.close()
        
    def water_on(self):
        output=bytes('o','utf-8')
        self.ser.write(output)
        self.read()
    
    def water_off(self):
        output=bytes('f','utf-8')
        self.ser.write(output)
        self.read()
    
    def __del__(self):
        self.close()
        del self.ser


if __name__ == '__main__':
    water=ArduinoWaterDev()
    time.sleep(2)
    for i in range(10):
        time.sleep(0.3)
        water.drop_water(20)
