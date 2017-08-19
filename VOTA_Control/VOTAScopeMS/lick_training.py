'''
Created on Aug 9, 2017

@author: Lab Rat
'''
from math import sqrt
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
from random import randint,random

class VOTALickTrainingMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "lick_training"
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "lick_training_plot.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('tdelay', dtype=int, initial=0,ro=True)
        self.settings.New('trial_time',dtype=int,initial=10,ro=False)
        self.settings.New('lick_interval', dtype=int, initial=1,ro=False)
        self.settings.New('water_reward', dtype=bool, initial=False,ro=False)
        self.settings.New('total_drops', dtype=int, initial=0,ro=False)
        
        #self.settings.New('sampling_period', dtype=float, unit='s', initial=0.005)
        
        # Create empty numpy array to serve as a buffer for the acquired data
        #self.buffer = np.zeros(10000, dtype=float)
        
        # Define how often to update display during a run
        self.display_update_period = 0.1 
        
        # Convenient reference to the hardware used in the measurement
        self.daq_ai = self.app.hardware['daq_ai']
        self.arduino_sol =self.app.hardware['arduino_sol']
        self.odor_gen =self.app.hardware['odor_gen']
        self.arduino_wheel =self.app.hardware['arduino_wheel']
        self.water=self.app.hardware['arduino_water']

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.aux_graph_layout=pg.GraphicsLayoutWidget()
        self.ui.aux_plot_groupBox.layout().addWidget(self.aux_graph_layout)

        # Create PlotItem object (a set of axes)  
        self.plot1 = self.graph_layout.addPlot(row=1,col=1,title="PID",pen='r')
        self.plot2 = self.graph_layout.addPlot(row=2,col=1,title="Flowrate (L/min)")
        self.plot3 = self.graph_layout.addPlot(row=3,col=1,title="Lick")
        self.plot4 = self.graph_layout.addPlot(row=4,col=1,title="Position and Speed")
        self.plot5 = self.graph_layout.addPlot(row=5,col=1,title="Odor Output Target")
        # Create PlotDataItem object ( a scatter plot on the axes )
        self.plot_line1 = self.plot1.plot([0])    
        self.plot_line2 = self.plot2.plot([0])
        self.plot_line3 = self.plot3.plot([0])
        self.plot_line4 = self.plot3.plot([0])     
        self.clean_plot_line = self.plot5.plot([0])  
        self.odor_plot_line1 = self.plot5.plot([1])  
        self.odor_plot_line2 = self.plot5.plot([2])  
        self.odor_plot_line3 = self.plot5.plot([3])
        self.position_line=self.plot4.plot([0])
        self.speed_line=self.plot4.plot([1])
        
        self.plot_line1.setPen('r')
        self.plot_line2.setPen('w')
        self.plot_line3.setPen('b')
        
        self.clean_plot_line.setPen('b')
        self.odor_plot_line1.setPen('r')
        self.odor_plot_line2.setPen('g')
        self.odor_plot_line3.setPen('y')
        
        
        self.position_line.setPen('w')
        self.speed_line.setPen('r')

        self.T=np.linspace(0,10,10000)
        self.k=0
    
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        self.plot_line1.setData(self.k+self.T,self.buffer[:,0]) 
        self.plot_line2.setData(self.k+self.T,self.buffer[:,1]) 
        self.plot_line3.setData(self.k+self.T,self.buffer[:,2])
        
        self.clean_plot_line.setData(self.k+self.T,self.buffer[:,7])
        self.odor_plot_line1.setData(self.k+self.T,self.buffer[:,8]) 
        self.odor_plot_line2.setData(self.k+self.T,self.buffer[:,9]) 
        self.odor_plot_line3.setData(self.k+self.T,self.buffer[:,10])
        
       
        self.position_line.setData(self.k+self.T,self.buffer[:,3])
        self.speed_line.setData(self.k+self.T,self.buffer[:,4])
        #print(self.buffer_h5.size)
    
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        num_of_chan=self.daq_ai.settings.num_of_chan.value()
        self.buffer = np.zeros((10000,num_of_chan+2+2+len(self.arduino_sol.sols)), dtype=float)
        self.buffer[0:self.settings.tdelay.value(),3]=100;
        '''
        initialize position
        '''
        position = 0
        '''
        initialize number of water drops given
        '''
        total_drops=0
        self.settings.total_drops.update_value(total_drops)
        
        
        '''
        Decide whether to create HDF5 file or not
        '''
        # first, create a data file
        if self.settings['save_h5']:
            # if enabled will create an HDF5 file with the plotted data
            # first we create an H5 file (by default autosaved to app.settings['save_dir']
            # This stores all the hardware and app meta-data in the H5 file
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
            
            # create a measurement H5 group (folder) within self.h5file
            # This stores all the measurement meta-data in this group
            self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
            
            # create an h5 dataset to store the data
            self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
                                                          shape = self.buffer.shape,
                                                          dtype = self.buffer.dtype,
                                                          maxshape=(None,self.buffer.shape[1]))
        
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        '''
        start actual protocol
        '''
        try:
            '''
            initialize counter ticks
            '''
            i = 0 #counter tick for loading buffer
            j = 0 #counter tick for saving hdf5 file
            self.k=0 #number of seconds saved
            water_tick=0 #
            step_size=self.daq_ai.settings.buffer_size.value()
           
            '''
            Start DAQ, Default at 1kHz
            '''
            self.daq_ai.start()
            
            # Will run forever until interrupt is called.
            '''
            Expand HDF5 buffer when necessary
            '''
            while not self.interrupt_measurement_called:
                i %= self.buffer.shape[0]
                if self.settings['save_h5']:
                    if j>(self.buffer_h5.shape[0]-step_size):
                        self.buffer_h5.resize((self.buffer_h5.shape[0]+self.buffer.shape[0],self.buffer.shape[1]))
                        self.k +=10
                

                '''
                Update Progress Bar
                '''
                self.settings['progress'] = i * 100./self.buffer.shape[0]
                
                
                
                '''
                update water status
                '''
                if (water_tick<(self.settings.lick_interval.value()*1000)):
                    water_tick+=1
                else:
                    self.settings.water_reward.update_value(True)
                    water_tick=0
                

                
                '''
                Generate a random odor
                '''
                if (i%25==0):
                    self.odor_gen.random()
                
                
                
                '''
                Read DAQ sensor data(0:PID, 1:flowrate, 2:lick)
                '''
                # Fills the buffer with sine wave readings from func_gen Hardware
                self.buffer[i:(i+step_size),0:num_of_chan] = self.daq_ai.read_data()
                self.buffer[i,1]=(self.buffer[i,1]-1.245)/8.65 #convert flow rate from 0-1 L/min
                self.buffer[i,2]=int((5-self.buffer[i,2])/3) #convert lick sensor into 0(no lick) and 1(lick)
                
                #ask if the animal licked in this interval
                lick=bool(self.buffer[i,2])
                
                '''
                Decide whether water will be given, based on the status of reward and lick
                '''
                if self.settings.water_reward.value():
                    if lick:
                        self.water.give_water()
                        self.settings.water_reward.update_value(False)
                        '''
                        save water given (5:If water given 6:water opened time)
                        '''
                        self.buffer[i,num_of_chan+2]=1
                        self.buffer[i,num_of_chan+3]=self.water.settings.open_time.value()
                        total_drops+=1
                        self.settings.total_drops.update_value(total_drops)
                
                '''
                Read and save Position and Speed at 100Hz(default) (3:position 4:speed)
                '''
                if (i%10==0):
                    speed=self.arduino_wheel.settings.speed.read_from_hardware()
                    position+=speed
                    self.buffer[i:(i+10),num_of_chan]=position*0.000779262240246 #convert position into meters
                    self.buffer[i:(i+10),num_of_chan+1]=speed*0.0779262240246 #convert speed to m/s
                
                '''
                Read odor value from the odor generator, otherwise fill with clean air(default)
                '''
                if self.odor_gen.buffer_empty():
                    odor_value=[100,0,0,0]
                    odor_disp_value=odor_value
                else:
                    odor_value_packet=self.odor_gen.read()
                    odor_value=odor_value_packet[0]
                    odor_disp_value=odor_value_packet[1]
                    
                '''
                write odor value to valve
                '''
                self.arduino_sol.load(odor_value)
                self.arduino_sol.write()
                
                '''
                write odor value to display (7:clean air 8:odor1 9:odor2 10:odor3)
                '''
                self.buffer[i:(i+step_size),(num_of_chan+4):(num_of_chan+4+len(self.arduino_sol.sols))]=odor_disp_value
                
                '''
                Save hdf5 file
                '''
                if self.settings['save_h5']:
                    # if we are saving data to disk, copy data to H5 dataset
                    self.buffer_h5[j:(j+step_size),:] = self.buffer[i:(i+step_size),:]
                    # flush H5
                    self.h5file.flush()
            
                
                # wait between readings.
                # We will use our sampling_period settings to define time
                #time.sleep(self.settings['sampling_period'])
                
                i += step_size
                j += step_size
               
                
                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    self.arduino_sol.write_default()
                    self.daq_ai.stop()
                    self.odor_gen.flush()
                    break

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()