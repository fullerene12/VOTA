'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .odor_gen_dev import OdorGenDev
from PyDAQmx import *
import numpy as np
import time

class OdorGenHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='odor_gen'

    def setup(self,num_of_sol=4,buffer_size=1,queue_size=10000):
        '''
        add settings for analog input event
        '''
        self.settings.New(name='num_of_sol',initial=num_of_sol,dtype=int,ro=False)
        self.settings.New(name='buffer_size',initial=buffer_size,dtype=int,ro=True)
        self.settings.New(name='queue_size',initial=queue_size,dtype=int,ro=False)
        self.settings.New(name='vmin',initial=1400,dtype=int,ro=False)
        self.settings.New(name='vmax',initial=3500,dtype=int,ro=False)

        
                
    def connect(self):
        self._dev=OdorGenDev(self.settings.num_of_sol.value(),
                          self.settings.buffer_size.value(),
                          self.settings.queue_size.value())
        
        self.flush=self._dev.flush
        self.read=self._dev.read
    
    def buffer_empty(self):
        return self._dev.is_empty()
    
    def run(self):
        output=self._dev.gen_sqr_ladder(vmin=self.settings.vmin.value(),vmax=self.settings.vmax.value(),dc=0.5)
        clean=self.settings.vmax.value()-output
        self._dev.set_sol(clean,0)
        self._dev.set_sol(output,1)
        self._dev.load_all()
    
        
    def disconnect(self):
        try:
            self._dev.close()
            del self._dev
            del self._flush
            del self.read
            
        except AttributeError:
            pass
        
if __name__ == '__main__':
    ai=DAQaiHW()
    ai.connect()
    print(ai._data)
    time.sleep(1)
    ai.disconnect()