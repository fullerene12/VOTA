'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
import simpleaudio as sa

class SoundHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='sound'

    def setup(self):
        pass
        
                
    def connect(self):
        self.wave_start = sa.WaveObject.from_wave_file('D:\\Hao\\VOTA\\VOTA_Control\\VOTAScopeHW\\sound\\beep_start.wav')
        self.wave_correct = sa.WaveObject.from_wave_file('D:\\Hao\\VOTA\\VOTA_Control\\VOTAScopeHW\\sound\\beep_correct.wav')
        self.wave_wrong = sa.WaveObject.from_wave_file('D:\\Hao\\VOTA\\VOTA_Control\\VOTAScopeHW\\sound\\beep_wrong.wav')
        
    def start(self):
        self.wave_start.play()
        
    def correct(self):
        self.wave_correct.play()
        
    def wrong(self):
        self.wave_wrong.play()
        
    def disconnect(self):
        try:
            pass
            
        except AttributeError:
            pass
        
if __name__ == '__main__':
    pass