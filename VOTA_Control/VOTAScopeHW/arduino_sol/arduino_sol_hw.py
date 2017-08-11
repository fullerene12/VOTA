'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .arduino_sol_dev import ArduinoSolDev
from PyDAQmx import *
import numpy as np
import time

class ArduinoSolHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='arduino_sol'

    def setup(self,port='COM3',baud_rate=250000):
        '''
        add settings for analog input event
        '''
        self.settings.New(name='port',initial=port,dtype=str,ro=False)
        self.settings.New(name='baud_rate',initial=baud_rate,dtype=int,ro=False)
        
        self.sols=[]
        self.sols.append(self.settings.New(name='clean_cair',initial=0,dtype=int,ro=False,vmin=0,vmax=3500))
        self.sols.append(self.settings.New(name='odor1',initial=0,dtype=int,ro=False,vmin=0,vmax=3500))
        self.sols.append(self.settings.New(name='odor2',initial=0,dtype=int,ro=False,vmin=0,vmax=3500))
        self.sols.append(self.settings.New(name='odor3',initial=0,dtype=int,ro=False,vmin=0,vmax=3500))


        
                
    def connect(self):
        self._dev=ArduinoSolDev(self.settings.port.value(),
                          self.settings.baud_rate.value())
        self.write=self._dev.write
    
        
    def start(self):
        self._dev.open()
        
    def stop(self):
        self._dev.close()
        
    def disconnect(self):
        try:
            self.stop()
            del self._dev
            del self.write
            
        except AttributeError:
            pass
        
if __name__ == '__main__':
    ai=DAQaiHW()
    ai.connect()
    print(ai._data)
    time.sleep(1)
    ai.disconnect()