'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from VOTAScopeHW.arduino_water.arduino_water_dev import ArduinoWaterDev
import time
from math import exp
class ArduinoWaterHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='arduino_water'

    def setup(self,port='COM6',baud_rate=250000):
        '''
        add settings for analog input event
        '''
        self.settings.New(name='port',initial=port,dtype=str,ro=False)
        self.settings.New(name='baud_rate',initial=baud_rate,dtype=int,ro=False)
        self.settings.New(name='water_on',initial=False,dtype=bool,ro=False)
        self.settings.New(name='open_time',initial=20,dtype=int,ro=False,vmin=1,vmax=1000)


    def give_water(self):
        self._dev.drop_water(self.settings.open_time.value())
       
    def connect(self):
        self._dev=ArduinoWaterDev(self.settings.port.value(),
                          self.settings.baud_rate.value())
        time.sleep(2)

    
  
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