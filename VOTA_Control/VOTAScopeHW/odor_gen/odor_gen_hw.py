'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .odor_gen_dev import OdorGenDev
from PyDAQmx import *
import numpy as np
import time
from random import randint

class OdorGenHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='odor_gen'

    def setup(self,num_of_sol=4,buffer_size=1,queue_size=10000):
        '''
        add settings for analog input event
        '''
        self.settings.New(name='pulse_duration_ms',initial=24,dtype=int,ro=False,vmin=24,vmax=1000)
        self.settings.New(name='preload_ms',initial=9,dtype=int,ro=False,vmin=2,vmax=15)
        self.settings.New(name='num_of_sol',initial=num_of_sol,dtype=int,ro=False)
        self.settings.New(name='buffer_size',initial=buffer_size,dtype=int,ro=True)
        
        self.settings.New(name='queue_size',initial=queue_size,dtype=int,ro=False)
        self.settings.New(name='vmin',initial=0,dtype=int,ro=False)
        self.settings.New(name='vmax',initial=100,dtype=int,ro=False)
        
        self.settings.New(name='selected_sol',initial=2,dtype=int,ro=False)
        self.settings.New(name='on_chance',initial=0,dtype=float,ro=False)

        

        
                
    def connect(self):
        self._dev=OdorGenDev(self.settings.num_of_sol.value(),
                          self.settings.buffer_size.value(),
                          self.settings.queue_size.value())
        
        self.flush=self._dev.flush
        self.read=self._dev.read
    
    def buffer_empty(self):
        return self._dev.is_empty()
    
    def make_ladder(self):
        sol=self.settings.selected_sol.value()
        duty_cycle=self.settings.pulse_duration_ms.value()/1000.0
        preload=self.settings.preload_ms.value()
        output=self._dev.gen_sqr_ladder(vmin=self.settings.vmin.value(),vmax=self.settings.vmax.value(),dc=duty_cycle,pre=preload)
        clean=100-output
        #self._dev.set_sol(clean,0)
        self._dev.set_sol(clean,clean,0)
        self._dev.set_sol(output.astype(int),output.astype(int),sol)
        self._dev.load_all()
        
    def make_ladder_clean(self):
        output=self._dev.gen_sqr_ladder(vmin=0,vmax=1600,dc=0.5)
        clean=1600-output
        #self._dev.set_sol(clean,0)
        self._dev.set_sol(clean,0)
        self._dev.load_all()
        
    def make_ladder_speed(self,vmini,vmaxi):
        output=self._dev.gen_sqr_ladder(vmini,vmaxi,dc=0.5)
        #self._dev.set_sol(clean,0)
        self._dev.set_sol(output,output,self.settings.selected_sol.value())
        self._dev.load_all()
    
    def random(self):
        sol=self.settings.selected_sol.value()
        on_chance=self.settings.on_chance.value()
        on_pulse_ms=self.settings.pulse_duration_ms.value()
        pre_pulse_ms=self.settings.preload_ms.value()
        vmini=self.settings.vmin.value()
        vmaxi=self.settings.vmax.value()
        self._dev.random(sol,on_chance,on_pulse_ms,pre_pulse_ms,vmini,vmaxi,randint)
        
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