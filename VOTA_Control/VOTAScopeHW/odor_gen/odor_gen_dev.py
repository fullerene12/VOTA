'''
Created on Aug 9, 2017

@author: Hao Wu
'''
import numpy as np
from scipy import signal,pi
from queue import Queue
import matplotlib.pyplot as plt
from random import random,randint
from math import sqrt
class OdorGenDev(object):
    '''
    classdocs
    '''

    def __init__(self,num_of_sol=8,buffer_size=1,queue_size=100000,preload_level=40):
        '''
        Constructor
        '''
        self.num_of_sol=num_of_sol
        self.buffer_size=buffer_size
        self.step=buffer_size
        self.sec=1000/buffer_size;
        self.queue_size=queue_size
        self.max_tick=queue_size
        self.preload_level=preload_level
        self.tick=0
        
        self.data=np.zeros((queue_size,num_of_sol),dtype=float)
        self.disp_data=np.zeros((queue_size,num_of_sol),dtype=float)
        self.t=np.linspace(0,queue_size/self.sec,queue_size)
        self.buffer=Queue(queue_size)
        
    def gen_sqr_wave(self,freq=1,dc=0.5):
        return (signal.square(2*freq*pi*self.t,dc)+1)/2
    
    def gen_ladder_wave(self,vmin=0,vmax=1,pre=9):
        sec=int(self.sec);
        seglen=int(self.queue_size/sec)
        output=np.zeros((sec,seglen))
        vals=np.linspace(vmin,vmax,seglen)
        
        vals=vals.reshape((1,seglen))
        output[:]=vals
        output[0:pre,:]=self.preload_level
        return output.transpose().reshape((self.queue_size,))
    
    def gen_sqr_ladder(self,vmin=0,vmax=100,dc=0.5,pre=9):
        return np.multiply(self.gen_ladder_wave(vmin,vmax,pre),self.gen_sqr_wave(1,dc))
        
    def set_sol(self,wave,disp_wave,sol=0):
        self.data[:,sol]=wave
        self.disp_data[:,sol]=disp_wave
        
    def random(self,sol,on_chance,on_pulse_ms,pre_pulse_ms,vmini,vmaxi,level_rand_func=randint):
        dice=random()
        if dice<on_chance:
            sol_level=level_rand_func(vmini,vmaxi)
            data=np.zeros((on_pulse_ms,self.num_of_sol),dtype=float)
            disp_data=np.zeros((on_pulse_ms,self.num_of_sol),dtype=float)
            data[:,sol]=sol_level
            disp_data[:,sol]=sol_level
            data[0:pre_pulse_ms,sol]=self.preload_level
            data[:,0]=100-sol_level
            disp_data[:,0]=100-sol_level
            for i in range(on_pulse_ms):
                self.buffer.put([data[i,:].astype(int).squeeze().tolist(),disp_data[i,:].astype(int).squeeze().tolist()])
                
    def pulse(self,sol,pulse_ms,on_ms,pre_pulse_ms,sol_level,clean_factor,clean_delay):
        data=np.zeros((pulse_ms,self.num_of_sol),dtype=float)
        disp_data=np.zeros((pulse_ms,self.num_of_sol),dtype=float)
        data[0:on_ms,sol]=sol_level
        disp_data[0:on_ms:,sol]=sol_level
        data[0:pre_pulse_ms,sol]=self.preload_level
        sol_factor=(sol_level/100.0)*(sol_level/100.0)
        data[:,0]=100
        disp_data[:,0]=100
        data[clean_delay:on_ms,0]=100-sol_level*sol_factor*clean_factor
        disp_data[clean_delay:on_ms,0]=100-sol_level*sol_factor*clean_factor

        for i in range(pulse_ms):
            self.buffer.put([data[i,:].astype(int).squeeze().tolist(),disp_data[i,:].astype(int).squeeze().tolist()])
    
        
    
    def read(self):
        return self.buffer.get()
    
    def write(self,val):
        self.buffer.put(val)
    
    def load_all(self):
        self.flush_buffer()
        for i in range(self.queue_size):
            self.buffer.put([self.data[i,:].astype(int).squeeze().tolist(),self.disp_data[i,:].astype(int).squeeze().tolist()])
    
    def is_empty(self):
        return self.buffer.qsize()==0
    
    def flush_data(self):
        self.data[:]=0
        
    def flush_buffer(self):
            while not self.is_empty():
                self.buffer.get_nowait()

    def flush(self):
        self.flush_data()
        self.flush_buffer()

if __name__ == '__main__':
    odor_gen=OdorGenDev(queue_size=10000)
    odor_gen.set_sol(odor_gen.gen_sqr_ladder(),0)
    odor_gen.load_all()
    while not odor_gen.is_empty():
                print(odor_gen.read())