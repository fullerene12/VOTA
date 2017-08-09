from ScopeFoundry import BaseMicroscopeApp

class FancyMicroscopeApp(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'fancy_microscope'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        print("Adding Hardware Components")
        from ScopeFoundryHW.virtual_function_gen.vfunc_gen_hw import VirtualFunctionGenHW
        self.add_hardware(VirtualFunctionGenHW(self))

        #Add measurement components
        print("Create Measurement objects")
        from ScopeFoundryHW.virtual_function_gen.sine_wave_measure import SineWavePlotMeasure
        self.add_measurement(SineWavePlotMeasure(self))
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys
    
    app = FancyMicroscopeApp(sys.argv)
    sys.exit(app.exec_())