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
import os
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
        self.settings.New('save_movie', dtype=bool, initial=False,ro=False)
        self.settings.New('movie_on', dtype=bool, initial=False,ro=True)
        #self.settings.New('sampling_period', dtype=float, unit='s', initial=0.005)
        
        # Create empty numpy array to serve as a buffer for the acquired data
        #self.buffer = np.zeros(10000, dtype=float)
        
        # Define how often to update display during a run
        self.display_update_period = 0.04 
        
        # Convenient reference to the hardware used in the measurement
        self.daq_ai = self.app.hardware['daq_ai']
        self.arduino_sol = self.app.hardware['arduino_sol']
        self.water=self.app.hardware['arduino_water']
        self.camera=self.app.hardware['camera']

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
        self.settings.save_movie.connect_to_widget(self.ui.save_movie_checkBox)
        
        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.aux_graph_layout=pg.GraphicsLayoutWidget()
        self.ui.aux_plot_groupBox.layout().addWidget(self.aux_graph_layout)
        
        self.camera_layout=pg.GraphicsLayoutWidget()
        self.ui.camera_groupBox.layout().addWidget(self.camera_layout)

        # Create PlotItem object (a set of axes)  
     
        self.plot1 = self.graph_layout.addPlot(row=1,col=1,title="Lick")
        self.plot2 = self.graph_layout.addPlot(row=2,col=1,title="breathing")

        # Create PlotDataItem object ( a scatter plot on the axes )
        self.breathing_plot = self.plot2.plot([0])
        self.lick_plot_0 = self.plot1.plot([0])
        self.lick_plot_1 = self.plot1.plot([1])     
        
        self.lick_plot_0.setPen('y')
        self.lick_plot_1.setPen('g')
        
        self.T=np.linspace(0,10,10000)
        self.k=0
        
        self.camera_view=pg.ViewBox()
        self.camera_layout.addItem(self.camera_view)
        self.camera_image=pg.ImageItem()
        self.camera_view.addItem(self.camera_image)
        
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        self.lick_plot_0.setData(self.k+self.T,self.buffer[:,1]) 
        self.lick_plot_1.setData(self.k+self.T,self.buffer[:,2]) 
        self.breathing_plot.setData(self.k+self.T,self.buffer[:,0]) 
       
        if self.settings.movie_on.value():
            self.camera_image.setImage(self.camera.read())
            if self.settings.save_movie.value():
                self.camera.write()
    
        #print(self.buffer_h5.size)
    
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        if self.camera.connected.value():
            self.settings.movie_on.update_value(True)
        
        
        num_of_chan=self.daq_ai.settings.num_of_chan.value()
        self.buffer = np.zeros((10000,num_of_chan+2), dtype=float)
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
            file_name_index=0
            file_name=os.path.join(self.app.settings.save_dir.value(),self.app.settings.sample.value())+'_'+str(file_name_index)+'.h5'
            while os.path.exists(file_name):
                file_name_index+=1
                file_name=os.path.join(self.app.settings.save_dir.value(),self.app.settings.sample.value())+'_'+str(file_name_index)+'.h5'
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self,fname = file_name)
            
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
                #no addition
                
                
                
                '''
                Read DAQ sensor data(0:lick_left, 1:lick_right, 2:flowmeter)
                '''
                # Fills the buffer with sine wave readings from func_gen Hardware
                self.buffer[i:(i+step_size),0:num_of_chan] = self.daq_ai.read_data()

                lick_0 = (self.buffer[i,1]<4)
                lick_1 = (self.buffer[i,2]<4)
                self.buffer[i,1]=lick_0 #convert lick sensor into 0(no lick) and 1(lick)
                self.buffer[i,2]=lick_1
#                 ask if the animal licked in this interval

#                  print(self.buffer[i,0:1])
                lick = (lick_0 or lick_1)
                
                '''
                Decide whether water will be given, based on the status of reward and lick
                '''
                if self.settings.water_reward.value():
                    if lick:
                        if lick_0:
                            side = 0
                        else:
                            side = 1
                        self.water.give_water(side)
                        self.settings.water_reward.update_value(False)
                
                        '''
                        save water given (5:If water given 6:water opened time)
                        '''
                        self.buffer[i,num_of_chan+side]=1
                        #self.buffer[i,num_of_chan+2]=self.water.open_time[side].value()
                        total_drops+=1
                        self.settings.total_drops.update_value(total_drops)
                
                else:
                    '''
                    The mouse gets a timeout if it licks repetitively or hold the water port (when it is not suppose to lick)
                    '''
                    if lick:
                        water_tick = 0
                '''
                Read and save Position and Speed at 100Hz(default) (3:position 4:speed)
                '''
                # to be implemented
                '''
                Read odor value from the odor generator, otherwise fill with clean air(default)
                '''
                
                '''
                write odor value to valve
                '''
                self.arduino_sol.write()
                '''
                write odor value to display (7:clean air 8:odor1 9:odor2 10:odor3)
                '''
                #to be implemented
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
                    self.daq_ai.stop()
                    break

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
                
            if self.camera.connected.value():
                self.settings.movie_on.update_value(False)                