import time
import threading
from random import seed
from random import random
from IPython.display import display
import math

class PID_Tester:
    
    def __init__(self, ui=False, smell_engine=False, PID_MODE=False, cont_read_conc=False,sampling_rate=50):
        self.ui = ui
        self.smell_engine = smell_engine        
        self.PID_MODE = PID_MODE
        self.smell_engine.smell_controller.valve_driver.PID_MODE = PID_MODE
        self.cont_read_conc = cont_read_conc
        self.seed = seed(1)
        self.sampling_rate = sampling_rate
        
    def read_concentration_values(self):
        concentration_mixtures = self.ui.odorConcentrationValues() # Read in user-specified concentrations
        print(concentration_mixtures)
        self.smell_engine.set_desired_concentrations(concentration_mixtures)  # Assign target concentrations
    
    def timer_setup(self, interval=None):
        """
        Configuration of thread instance. 
        Thread runs at a user-defined time interval to which it issues commands to hardware.

        Args:
            interval (float): Rate at which thread executs write commands to olfactometer.
        """
        if interval is None:
            try:
                interval = (0.5 / self.frames_per_s)
            except:
                interval = 0.1
        self.timer_interval = interval
        self.timer_paused = False
        self.timer_thread = threading.Thread(target=self.timer_run, args=())
        self.timer_thread.daemon = True

    def timer_start(self):
        """
        Starts thread instance.
        """
        print("Thread started")
        self.timer_thread.start()

    def timer_run(self):
        """
        The 'update' method for the thread instance. Writes digital valve states 
        to olfactometer at the defined timer_interval rate. 
        If writing values is unsuccessfull thread instance halts.
        """
        while self.timer_interval:          # While the timer is valid
            if not self.timer_paused:       # Try and write the data
                time.sleep(self.timer_interval)            
                # IF RUNNING FOR PID TESTS
                if (self.PID_MODE):
                    # if (self.cont_read_conc):
                    #     self.read_concentration_values()
                    self.ui.timeSeriesUpdate(self.smell_engine.smell_controller.valve_driver.PID_sensor_readings, 
                                            10*self.sampling_rate)
                # print("Thread running")                
            else:
                time.sleep(self.timer_interval)

    def timer_pause(self):
        """
        Halts thread instance.
        """
        self.timer_paused = True

    def timer_resume(self):
        """
        Continues thread after being paused.
        """
        self.timer_paused = False

    def timer_stop(self):
        """
        Pauses thread, turns off all valve, ends defined virtual communication, 
        and releases Task object instance from memory. 
        """
        self.timer_pause()
    