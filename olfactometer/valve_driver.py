from olfactometer.equipment import Olfactometer
import time
import datetime
import threading
import random
import collections
import os
import numpy as np
import nidaqmx
from nidaqmx.constants import (
    LineGrouping, AcquisitionType,Edge,    
    OverflowBehavior, TaskMode, Polarity, RegenerationMode)
from nidaqmx.error_codes import DAQmxErrors, DAQmxWarnings
from nidaqmx.errors import (
    check_for_error, is_string_buffer_too_small, DaqError, DaqResourceWarning)

# import winsound

SAMPLES_PER_FRAME = 50
FRAMES_PER_S = 1


class ValveDriver:
    """
    ValveDriver is responsible for interfacing with NI-DAQmx hardware using the nidaqmx API.
    Provides continuous virtual communication lines with MFCs (analog) and olfactometer valves (digital).

    Attributes:
        olf: List of mfc voltage values indexed accurately.
        cids: A ordered list of concentration ids for each valve.
    """
    def __init__(self, olfactometer=None, data_container=None, debug_mode=False, PID_mode=False):                 
        self.digital_device_name = "cDAQ1Mod1"
        self.analog_device_name = "cDAQ1Mod2"
        self.analog_in_device_name = "cDAQ1Mod3"
        self.tasks = {}                
        self.mixtures = collections.deque([])        
        self.valve_duty_cycles = []
        self.mfc_setpoints = []
        self.PID_sensor_readings = []
        self.DAQ_analog_channels = []
        self.specified_valve_states = []
        self.specified_analog_setpoints = []
        self.override_digital = False
        self.override_analog = False
        self.data_container = data_container
        self.debug_mode = debug_mode
        self.PID_mode = PID_mode
        self.num_pid_samples = SAMPLES_PER_FRAME             
        self.channels_initialized = False
        self.initialize()
        self.init_digital_task(task_name="DigitalTask")
        self.init_analog_task(olfactometer.mfc_flat_list(), task_name="AnalogTask")
        if (self.debug_mode is False and self.PID_mode):
            self.init_analog_in_task()            


    
        
    def initialize(self):
        """
        Reading and saving device information from NI-DAQmx hardware.
        Existing device references and tasks are reset. 

        Returns:
            Success/error status.
        Raises:
            nidaqmx.DaqError: An error occurred when attempting to read NIDAQ hardware information. 
            Error codes can be found in the nidaqmx errors.py system file.
        """
        try:
            system = nidaqmx.system.System.local(self.debug_mode)
            for device in system.devices:
                if device.name in [self.digital_device_name,
                                   self.analog_device_name,
                                   self.analog_in_device_name]:
                    device.reset_device()
                    self.device = device
            if not self.debug_mode:
                for tsk in system.tasks:
                    try:
                        tsk.close()
                    except AttributeError:
                        pass
        except nidaqmx.DaqError as e:
            print(e)
            return -1
        return 1    # Return success

    def init_analog_in_task(self, num_samples = SAMPLES_PER_FRAME, task_name='Analog_In', channel_name="analog_in_channel"):
        """
        Initializing an Analog Input Task to read samples from the specified channel.

        Args:
            num_samples (int): Specify # of samples per channel, default is 50
            task_name (str): Task name, used for uniquely identifying task instance.
        Returns:
            Success/error status represented with 1/-1.
        Raises:
            nidaqmx.DaqError: An error occured when trying to add an analog voltage virtual communication channel.
        """
        if not self.PID_mode:
            return
        task = nidaqmx.task.Task(task_name, self.debug_mode) # init task object.
        try:
            NIDAQMX_Analog_In_Channel = task.ai_channels.add_ai_voltage_chan("cDAQ1Mod3/ai0")
            print("Added analog in channel")
            if (self.debug_mode):       # Must add into simulator's backend task manager.
                task.add_task_channel(NIDAQMX_Analog_In_Channel)
            self.tasks['Analog_In'] = task
            self.channels_initialized = True
            print("Initialized analog in successfully")
            return 1
        except nidaqmx.DaqError as e:
            print(e)
            return -1

    def init_analog_task(self, mfc_flat_list, task_name='Analog_Task', channel_name="analog_channel"):
        """
        Initializing an Analog Output Task and Channel communication line.
        List of analog channels [0:3] along with voltage rates are initialized via nidaqmx API.

        Args:
            mfc_flat_list: A 1D list containing analog channels and voltages.
            task_name (str): Task name, used for uniquely identifying task instance.
        Returns:
            Success/error status represented with 1/-1.
        Raises:
            nidaqmx.DaqError: An error occured when trying to add an analog voltage virtual communication channel.
        """
        self.DAQ_analog_channels = []
        task = nidaqmx.task.Task(task_name, self.debug_mode) # init task object.
        for mfc in mfc_flat_list:
            assert isinstance(mfc.ao_channel, int)
            assert mfc.ao_channel in [0, 1, 2, 3]
            self.DAQ_analog_channels.append(mfc.ao_channel)
        assert len(set(self.DAQ_analog_channels)) == len(self.DAQ_analog_channels)
        try:
            chann_counter = 1
            for chan in self.DAQ_analog_channels:
                # print("Chan:\t", chan)
                ao = "cDAQ1Mod2/ao%d" % chan
                # Add digital out comm for writing task to device.
                NIDAQMX_analog_channel = task.ao_channels.add_ao_voltage_chan(ao,(channel_name+str(chann_counter)))
                if (self.debug_mode):
                    task.add_task_channel(NIDAQMX_analog_channel)
                chann_counter += 1
            self.set_task_clock(task)
            self.tasks['Analog'] = task            
            return 1
        except nidaqmx.DaqError as e:
            print(e)
            return -1

    def init_digital_task(self, task_name="DigitalTask", channel_name="digital_channel"):
        """
        Create task object with digital out on port0.
        Configure task to use 1 channel for all liens of communication.
        Append to list of tasks and update state of olfactometer.   

        Args:
            task_name (str): Task name, used for uniquely identifying task instance.
            channel_name (str): Channel name, used for unuquely identifying different channel comm lines.
        Returns:
            Success/error status represented with 1/-1.
        Raises:
            nidaqmx.DaqError: An error occured when trying to add an analog voltage virtual communication channel.
        """
        try:
            task = nidaqmx.task.Task(task_name, self.debug_mode) # init task object.
            # Add digital out comm for writing task to device.
            NIDAQMXChannel = task.do_channels.add_do_chan(
                self.digital_device_name + "/port0",
                name_to_assign_to_lines=channel_name,
                line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
            if (self.debug_mode):
                task.add_task_channel(NIDAQMXChannel)
            self.set_task_clock(task)
            self.tasks['Digital'] = task
            self.channels_initialized = True
            return 1
        except nidaqmx.DaqError as e:
            print(e)
            return -1
            
    def format_bits(self, valve_index, state):
        """
        Each valve state is identified by A, B, None. The valve state is represented as a 32 bit unsigned integer.
        If state A, first 16 bits are used to configure digital state of olfactometer.
        If state B, last 16 bits are used.

        Args:
            valve_index(int): Integer indexing of valve state (non-zero).
            state(str): A,B,None. 
        Returns:
            uint32: Binary representation of olfactometer state.
        Raises:
            Exception: Invalid state requested.
        """
        valve_index -= 1 # Switch to 0-indexed        
        if state == 'A':                # Increment up to last 16 bits to turn on.
            return 2**(valve_index+16)
        elif state=='B':                # Remains in red state for index.            
            return 2**valve_index
        elif state=='None':
            return 0
        raise Exception("Invalid state")        
        

    def convert_concentration_format(self, data_input, debug=False):    
        """
        Read in a list of concentrations, convert each individual concentration
        A/B/off state into a sequence of binary control signals for olfactometer.
        Args:
            d_in(`list` of `)
        Returns:
            A list of 5 concentration values and there states in A/B.           
        """        
        cntrl_signals = [ [ self.format_bits(data_input[0], 'A'), data_input[1]], 
                  [ self.format_bits(data_input[0], 'B'), data_input[2]], 
                  [ self.format_bits(data_input[0], 'None'), 1-(data_input[1]+data_input[2])] ]
        
        if (debug):     self.print_data_binary(cntrl_signals)
        return cntrl_signals
     
    def determine_clean_air_pair(self, valve_sched):
        end_range = len(valve_sched)-1     # becuase 0-indexed, we subtract 1 but add again for indexing in for loop
        for x in range(len(valve_sched)//2):
            if (valve_sched[x][1] > 0):
                valve_sched[end_range - x] = ((end_range-x + 1), 1-valve_sched[x][1], 0)
            if (valve_sched[x][2] > 0):
                valve_sched[end_range - x] = ((end_range-x + 1), 0, 1-valve_sched[x][2])
        return valve_sched

    def print_data_binary(self, concentration):
        """
        A debug method for printing binary representations of concentrations (digital states of olfactometer).

        Args:
            concentration(:obj:`list` of :obj:`float`): List of concentration states.
        """
        for i, odorant in enumerate(concentration):
            print(f"For odorant:\t {str(i+1)}")
            valve_write = str('{0:032b}'.format(odorant[0][0]))
            t = odorant[1]
            print(f"[ {valve_write},  {str(t)} ]\n")
    
    
    def print_valve_durations(self, valves):        
        for vd in valves:
            self.print_data_binary(vd)

    def set_valve_states(self, valve_states):
        """
        Toggle overrides for digital valve states and assign user-defined valve states
        
        Args:
            valve_states: A list of tuples containing high/low toggles for valve
        """
        print("set valve states invoked")
        self.override_digital = True
        self.specified_valve_states = valve_states

    def set_mfc_setpoints(self, setpoints):
        """
        Toggle override for analog mfc setpoints and assign user defined setpoints

        Args:
            setpoints: List containing voltage values per mfc
        """
        print("set valve states invoked")
        self.override_analog = True
        self.specified_analog_setpoints = setpoints

    def issue_odorants(self, valve_mfc_values):
        """
        Executed externally to update olfactometer schedule of odor samples,
        this method converts the olfactometer schedule into digital and analog control signals.
        Olfactometer Schedule Examples: 
        {'valves': 
                    [
                        (Valve Number, time in state A, time in state B)
                        (1, 0.6523873263385962, 0.3433522990024116), 
                        (2, 0.6523929695332448, 0.34373085569547107)
                    ], 'mfcs': 
                        {MyMediumMFC: MFC_A_High (1.0 L/min): array(value) * V, 
                        MyLowMFC: MFC_B_Low (10.0 cc/min): array(value) * V, 
                        MyHighMFC: MFC_Carrier (10.0 L/min): array(values) * V}
                    }
        Args:
            valve_mfc_values (:obj:`dictionary` of :obj:`(str, float)`): Expected dictionary of mfc voltages and valve state durations.
        """
        millis = int(round(time.time() * 1000))
        # Per valve, read the time in each state and convert it to a 32-bit representation of the valve state.
        valve_mfc_values['valves'] = self.determine_clean_air_pair(valve_mfc_values['valves'])
        valve_durations = [self.convert_concentration_format(vd)
                           for vd in valve_mfc_values['valves']]
        
        mfc_voltages = valve_mfc_values['mfcs']           
        if self.override_digital == False:  self.valve_duty_cycles = self.generate_digital_frame_writes(valve_durations)
        else:                               self.valve_duty_cycles = self.specify_digital_frame_writes(self.specified_valve_states)            
        
        if self.override_analog == False:   self.mfc_setpoints = self.generate_analog_frame_writes(mfc_voltages)        
        else:                               self.mfc_setpoints = self.specify_analog_frame_writes(self.specified_analog_setpoints)
        
        if (self.data_container != None):   # Write data into data container
            diff_time = int(round(time.time() * 1000)) - millis            
            generate_samples = {'digital_samples' : str(self.valve_duty_cycles), 'analog_samples': str(self.mfc_setpoints), 'generate_samples_latency' : diff_time/1000}
            self.data_container.append_value(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), generate_samples)

    def close_tasks(self):
        """
        Closes all created/open NIDAQ tasks.                
        """
        for task in self.tasks:            
            self.tasks[task].stop()            
            self.tasks[task].close()
            print(f"Task closed: str{str(task)}")

    def generate_analog_frame_writes(self, analog_states):
        """
        Creates list of analog states to be written to MFCs.

        Args:
            analog_states (:obj:`dictionary` of :obj:`(int, float)`): A index identifier for MFC and the requested voltage values supplied.
        Returns:
            (:obj:`list` of :obj:`float`): List of voltage values per MFC.
        """
        analog_cntrl_signals = np.zeros((len(analog_states), self.samples_per_frame))
        for mfc, voltage in analog_states.items():
            ao_index = self.DAQ_analog_channels.index(mfc.ao_channel)
            analog_cntrl_signals[ao_index, :] = float(voltage.rescale('V'))
        return analog_cntrl_signals
            
    def generate_digital_frame_writes(self, valve_durations):
        """
        Create list (of size samples_per_frame) to populate with 32 bit values representative 
        of the digital states for each valve.

        To turn a respective valve on, it's index location within first 16 bits of a 32-bit write must be set to high.
        To turn a respective valve off, it's index location within last 16 bits of a 32-bit write must be set to high.
        
        Args:
            valve_durations (:obj:`dictionary` of :obj:`(int, float)`): Dictionary of valve indexes and their respective states (time in ms for A,B,off).
        Returns:
            (:obj:`list` of :obj:`uint32`):  Writes will be written to olfactometer as multiline/channel write.
        """        
        spf = self.samples_per_frame = SAMPLES_PER_FRAME
        digital_cntrl_signals = np.zeros(spf, dtype='uint32') # Elements required to be formatted as uint32 np array.
        n_valves = len(valve_durations)
        for i in range(spf):                # Iterate over num of digital_cntrl_signals in frame
            # Iterate over all concentrations to create binary write for respective states.
            for valve_num in range(n_valves//2):            
                occupancy_times = valve_durations[valve_num]
                if (i < (occupancy_times[0][1]*spf)):     # Check state A time to see if included in frame write.
                    digital_cntrl_signals[i] += occupancy_times[0][0] # Write binary index value to this line.
                if (i >= (occupancy_times[0][1]*spf)) and (i < (occupancy_times[0][1]*spf + occupancy_times[1][1]*spf)): # check state B
                    digital_cntrl_signals[i] += occupancy_times[1][0]            
                else:
                    digital_cntrl_signals[i] += occupancy_times[2][0]
            # Iterate over all concentrations to create binary write for respective states.
            for valve_num in range(n_valves//2):            
                occupancy_times = valve_durations[(n_valves-valve_num-1)]
                occupancy_times_pair = valve_durations[valve_num]
                if (occupancy_times_pair[0][1] > 0 and i > (occupancy_times_pair[0][1])*spf):     # Check state A time to see if included in frame write.
                    digital_cntrl_signals[i] += occupancy_times[0][0] # Write binary index value to this line.                                   
                if (occupancy_times_pair[1][1] > 0 and i > ((occupancy_times_pair[1][1])*spf)): # check state B
                    digital_cntrl_signals[i] += occupancy_times[1][0]                                                                
                else:
                    digital_cntrl_signals[i] += occupancy_times[2][0]        
        return digital_cntrl_signals

    def specify_analog_frame_writes(self, analog_states):
        """
        Provide a defined list of analog states to be written to MFCs.

        Args:
            analog_states (:obj:`list` of :obj:`(float, int)`): A index identifier for MFC and the requested voltage values supplied.
        Returns:
            (:obj:`list` of :obj:`float`): List of voltage values per MFC.
        """        
        analog_cntrl_signals = np.zeros((len(analog_states), self.samples_per_frame))
        for mfc, voltage in enumerate(analog_states):
            ao_index = self.DAQ_analog_channels.index(mfc)
            analog_cntrl_signals[ao_index, :] = voltage[1]        
        return analog_cntrl_signals

    def specify_digital_frame_writes(self, valve_states):
        """
        Given valve states, samples are generated with half containing given valve state other half being off

        Args:
            valve_states (:obj:`list`): List of tuples representing A,B states for each valve
        """
        spf = self.samples_per_frame = SAMPLES_PER_FRAME        
        digital_cntrl_signals = np.zeros(spf, dtype='uint32') # Elements required to be formatted as uint32 np array.
        n_valves = len(valve_states)
        for i in range(spf):                # Iterate over num of digital_cntrl_signals in frame
            # Iterate over all concentrations to create binary write for respective states.
            for valve_num in range(n_valves):            
                y = valve_states[valve_num]                     
                if (i < (y[1]*spf)):
                    digital_cntrl_signals[i] += self.format_bits(valve_num+1, 'A')
                elif (i >= (y[1]*spf)) and (i < (y[1]*spf +y[2]*spf)): # check state B
                    digital_cntrl_signals[i] += self.format_bits(valve_num+1, 'B')
                else:
                    digital_cntrl_signals[i] += self.format_bits(valve_num+1, 'None')                        
        return digital_cntrl_signals

    def write_zeroes(self):
        """
        This method will write a list of valve commands to olfactometer.

        Returns:
            A list of 5 concentration values and there states in A/B.
        """        
        digital_values = self._last_digital_values * 0
        analog_values = self._last_analog_values * 0
        self.write_output(digital_values, analog_values)

    def write_output_digital(self, digital_values):
        if not self.channels_initialized:   return
        self._last_digital_values = digital_values
        try:
            if (len(digital_values) > 0):       
                if (self.tasks['Digital'].is_task_done()):
                    self.tasks['Digital'].stop()
                self.tasks['Digital'].write(digital_values, auto_start=True)
            return 0
        except nidaqmx.DaqError as e:
            print(e)
            return -1

    
    def write_output(self, digital_values, analog_values=[]):
        """
        This method will write a list of valve commands to olfactometer.

        Args:
            None
        Returns:
            int: Success/error message. 0 success, -1 error.
        """
        if not self.channels_initialized:
            return
        self._last_digital_values = digital_values
        self._last_analog_values = analog_values
        try:
            if (len(digital_values) > 0 and len(analog_values) > 0):                
                if (self.tasks['Digital'].is_task_done() and self.tasks['Analog'].is_task_done()):
                    self.tasks['Digital'].stop()
                    self.tasks['Analog'].stop()
                self.tasks['Digital'].write(digital_values, auto_start=True)
                self.tasks['Analog'].write(analog_values, auto_start=True)
                if not self.debug_mode and self.PID_mode: # Read values from PID             
                    self.PID_sensor_readings = self.tasks["Analog_In"].read(number_of_samples_per_channel=self.num_pid_samples)
                    if (self.data_container != None):                        
                        samples = self.PID_sensor_readings
                        pid_average = sum(samples)/ len(samples)
                        generate_samples = {'PID_sensor_reading' : {
                            'data' : str(samples), 'average' : str(pid_average), 'target_concentration' : str(self.mixtures[-1])
                        }}
                        self.data_container.append_value(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], generate_samples)                                                           
            return 0
        except nidaqmx.DaqError as e:
            print(e)
            return -1

    def set_task_clock(self, task, samples_per_frame=SAMPLES_PER_FRAME,
                       frames_per_s=FRAMES_PER_S, repeats=1):
        """
        Sets rate, number of samples, and source of the Sample Clock for developer-specified task.

        Args:
            task (:obj:`nidaqmx.task.Task`): Task object to which sample clock is being configured for.
            samples_per_frame (int): Samples generated per frame.
            frames_per_s (int): Frames per second for sampling.
            repeats (int, optional): Duplicating samples across each channel. 
        """
        self.samples_per_frame = samples_per_frame
        self.frames_per_s = frames_per_s
        self.samples_per_s = samples_per_frame * frames_per_s
        task.timing.cfg_samp_clk_timing(\
            50,
            active_edge=Edge.RISING,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=50)
        # print(f"Clock sampling rate: {self.samples_per_s}, samps per chan: {samples_per_frame}")
        if not self.debug_mode:
            # Do not allow NI-DAQmx to generate same data multiple times.
            task.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION

    ############# THREAD METHODS #############
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
        print("Starting Valve Driver main thread.")
        self.timer_thread.start()

    def timer_run(self):
        """
        The 'update' method for the thread instance. Writes digital valve states 
        to olfactometer at the defined timer_interval rate. 
        If writing values is unsuccessfull thread instance halts.
        """
        while self.timer_interval:          # While the timer is valid
            if not self.timer_paused:       # Try and write the data                                
                self.write_output(self.valve_duty_cycles, self.mfc_setpoints)
                time.sleep(self.timer_interval)
            else:
                # print("Timer paused")
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
        self.timer_interval = None
        if (self.data_container != None):
            self.data_container.create_json()
        self.write_zeroes()
        self.close_tasks()   

    def abort(self):
        """
        Resets NI-DAQmx device to initialized state. 
        All prior tasks and defined channel lines are aborted. 
        """
        system = nidaqmx.system.System.local()
        for d in system.devices:
            d.reset_device()