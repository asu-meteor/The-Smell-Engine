import unittest
import pkgutil
import importlib
import time
import datetime
import threading
import random
import collections
import numpy as np
import sys
from os import path
# sys.path.insert(0,path.abspath(path.join(path.dirname(__file__))))
# sys.path.insert(0,path.abspath(path.join(path.dirname("../"))))
# import nidaqmx
# print(sys.path)
import nidaqmx
from nidaqmx.constants import (
LineGrouping, AcquisitionType)
from nidaqmx.task import Task 

'''
TODO:
- Determine whether debug_mode can be a custom object 
with flags for printing additional text.
'''

class NIDAQmxTests(unittest.TestCase):

    def test_device_creation(self):
        print("Testing device creation")
        system = nidaqmx.system.System.local(True)
        for device in system.devices:
            if (device.debug_mode):
                print("Testing device return:\t" + str(device.name))

    
    def test_duty_cycle(self):
        task = Task("Digital Task", debug_mode=True)
        digital_device_name = "cDAQ1Mod1"
        channel_name="channel"
        print("Task name", task.name)
        NIDAQMXChannel =task.do_channels.add_do_chan(
                    digital_device_name + "/port0",
                    name_to_assign_to_lines=channel_name,
                    line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        task.add_task_channel(NIDAQMXChannel)
        task.duty_cycle = 0.1
        while not task.is_task_done():
            print("Is task done?:\t" + str(task.is_task_done()))
        print("Is task done?:\t" + str(task.is_task_done()))
        task.stop()

    def test_sampling_clock_configuration(self):
        task = Task("Digital Task", debug_mode=True)
        print("Task name", task.name)
        repeats = 1
        samples_per_frame = 50
        frames_per_s = 2
        samples_per_s = samples_per_frame * frames_per_s
        if (task.timing.cfg_samp_clk_timing(\
                samples_per_s,
                sample_mode=AcquisitionType.CONTINUOUS,
                samps_per_chan=samples_per_frame*repeats) == 0):
            print("Configured clock successfully")
        else:
            print("Clock not configured successfully")

    def test_digital_task_creation(self):
        task = Task("Digital Task", debug_mode=True)
        digital_device_name = "cDAQ1Mod1"
        channel_name="channel"
        print("Task name", task.name)
        NIDAQMXChannel =task.do_channels.add_do_chan(
                    digital_device_name + "/port0",
                    name_to_assign_to_lines=channel_name,
                    line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        task.add_task_channel(NIDAQMXChannel)
        print("Channels:\t" + str(task.do_channels))
        print("Channels:\t" + str(task.channels))

    def test_digital_write_task(self):
        task = Task("Digital Task", debug_mode=True)
        digital_device_name = "cDAQ1Mod1"
        channel_name="channel"
        NIDAQMXChannel =task.do_channels.add_do_chan(
                    digital_device_name + "/port0",
                    name_to_assign_to_lines=channel_name,
                    line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        task.add_task_channel(NIDAQMXChannel)
        # print("Channels:\t" + str(task.task_channels))
        print("Channels:\t" + str(task.channels))
        task.write([True,False,True], True)

    def test_analog_task_creation(self):
        task = Task("Analog Task", debug_mode=True)
        print("Task name", task.name)
        analog_device_name = "cDAQ1Mod2"
        channel_name="analog_channel"
        analog_channels = []
        mfc_flat_list = [1,0,2]
        for mfc in mfc_flat_list:
            analog_channels.append(mfc)
        for chan in analog_channels:
            ao = analog_device_name + "/ao%d" % chan
            task.ao_channels.add_ao_voltage_chan(ao, channel_name)

    def test_analog_write_task(self):
        task = Task("Analog Task", debug_mode=True)
        print("Task name", task.name)
        analog_device_name = "cDAQ1Mod2"
        channel_name="analog_channel"
        analog_channels = []
        mfc_flat_list = [1,0,2]
        for mfc in mfc_flat_list:
            analog_channels.append(mfc)
        for chan in analog_channels:
            ao = analog_device_name + "/ao%d" % chan
            analog_task = task.ao_channels.add_ao_voltage_chan(ao, channel_name)
            task.add_task_channel(analog_task)
        print("Channels Test:\t" + str(task.channels) + "\n")
        analog_values = np.array([[0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165, 0.0165,
            0.0165, 0.0165, 0.0165, 0.0165],
        [0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 , 0.005 ,
            0.005 , 0.005 , 0.005 , 0.005 ],
        [1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983, 1.0983,
            1.0983, 1.0983, 1.0983, 1.0983]])
        task.write(analog_values, True)
    

if __name__ == "__main__":
    # test_device_creation()
    # print("\nDigital Task Creation")
    # test_digital_task_creation()
    # print("\nTest Duty Cycle")
    # test_duty_cycle()
    # print("\nTest Analog Task Creation")
    # test_analog_task_creation()
    # print("\nTest Sample Clock")
    # test_sampling_clock_configuration()
    # print("\nTest Digital Write")
    # test_digital_write_task()
    # print("\nTest Analog Write")
    # test_analog_write_task()
    unittest.main()