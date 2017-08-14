'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .arduino_sol_dev import ArduinoSolDev
from PyDAQmx import *
import numpy as np
import time
from math import exp
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

        self.sols.append(self.settings.New(name='clean_cair',initial=0,dtype=int,ro=False,vmin=0,vmax=100))
        self.sols.append(self.settings.New(name='odor1',initial=0,dtype=int,ro=False,vmin=0,vmax=100))
        self.sols.append(self.settings.New(name='odor2',initial=0,dtype=int,ro=False,vmin=0,vmax=100))
        self.sols.append(self.settings.New(name='odor3',initial=0,dtype=int,ro=False,vmin=0,vmax=100))
        
        self.a=[]
        self.b=[]
        self.c=[]
        self.d=[]
        self.k=[]
        self.p=[]
        self.va=[]
        self.vb=[]
        
        for i in range(len(self.sols)):
            self.a.append(self.settings.New(name='a'+str(i),initial=797.4,dtype=float,ro=True))
            self.b.append(self.settings.New(name='b'+str(i),initial=0.009895,dtype=float,ro=True))
            self.c.append(self.settings.New(name='c'+str(i),initial=-164.4,dtype=float,ro=True))
            self.d.append(self.settings.New(name='d'+str(i),initial=-0.241,dtype=float,ro=True))
            self.k.append(self.settings.New(name='k'+str(i),initial=7.509,dtype=float,ro=True))
            self.p.append(self.settings.New(name='p'+str(i),initial=815.1,dtype=float,ro=True))
            self.va.append(self.settings.New(name='va'+str(i),initial=662,dtype=int,ro=True))
            self.vb.append(self.settings.New(name='vb'+str(i),initial=711,dtype=int,ro=True))
        
        self.load_sol_params()
        
        self.speed_coeffs=[]
        self.speed_coeffs.append(self.settings.New(name='clean_coeff',initial=1,dtype=float,ro=False))
        self.speed_coeffs.append(self.settings.New(name='speed_coeff1',initial=1,dtype=float,ro=False))
        self.speed_coeffs.append(self.settings.New(name='speed_coeff2',initial=1,dtype=float,ro=False))
        self.speed_coeffs.append(self.settings.New(name='speed_coeff3',initial=1,dtype=float,ro=False))


    def connect(self):
        self._dev=ArduinoSolDev(self.settings.port.value(),
                          self.settings.baud_rate.value())
    
    def write(self):
        sol_vals=[]
        for i in range(len(self.sols)):
            a=self.a[i].value()
            b=self.b[i].value()
            c=self.c[i].value()
            d=self.d[i].value()
            k=self.k[i].value()
            p=self.p[i].value()
            va=self.va[i].value()
            vb=self.vb[i].value()
            coeff=self.speed_coeffs[i].value()
            
            x=int(self.sols[i].value()*coeff)
            if x==0:
                sol_vals.append(0)
            elif x==1:
                sol_vals.append(int(va))
            elif x==2:
                sol_vals.append(int(vb))
            else:
                if x<20:
                    sol_vals.append(int(a*exp(b*x)+c*exp(d*x)))
                else:
                    sol_vals.append(int(p+k*x))
        
        self._dev.write(sol_vals)
        
    def write_raw(self):
        sol_vals=[]
        for i in range(len(self.sols)):
            x=self.sols[i].value()
            sol_vals.append(int(x))
        
        self._dev.write(sol_vals)
        
    def set_low(self):
        for sol in self.sols:
            sol.update_value(0)
    
    def write_low(self):
        self.set_low()
        self.write()
            
    def write_default(self):
        self.set_low()
        self.sols[0].update_value(100)
        self.write()
            
    def load(self,vals):
        for i in range(len(vals)):
            self.sols[i].update_value(vals[i])
        
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
        
    def load_sol_params(self):
        self.a[1].update_value(1170)
        self.b[1].update_value(0.001481)
        self.c[1].update_value(-119.6)
        self.d[1].update_value(-0.1885)
        self.k[1].update_value(1.369)
        self.p[1].update_value(1183)
        self.va[1].update_value(1068)
        self.vb[1].update_value(1090)

        self.a[2].update_value(1295)
        self.b[2].update_value(0.00337)
        self.c[2].update_value(-178)
        self.d[2].update_value(-0.157)
        self.k[2].update_value(3.761)
        self.p[2].update_value(1318)
        self.va[2].update_value(1158)
        self.vb[2].update_value(1176)
      
        self.a[3].update_value(1075)
        self.b[3].update_value(0.002775)
        self.c[3].update_value(-66.95)
        self.d[3].update_value(-0.2807)
        self.k[3].update_value(3.276)
        self.p[3].update_value(1061)
        self.va[3].update_value(1021)
        self.vb[3].update_value(1041)

if __name__ == '__main__':
    ai=DAQaiHW()
    ai.connect()
    print(ai._data)
    time.sleep(1)
    ai.disconnect()