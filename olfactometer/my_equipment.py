"""Equipment currently in use."""

import quantities as pq
from olfactometer.equipment import Olfactometer, MFC, \
                                   Jar, Opening, get_unique_tuples

STUB_LENGTH = 4.0 * pq.cm


class MyOlfactometer(Olfactometer):
    pass

class MyMFC(MFC):

    @property
    def curr_flow_rate_uncertainty(self):
        # Fix this to use the correct values from the manual
        return self.curr_flow_rate * 0.005 + \
               self.max_flow_rate * 0.001


class MyLowMFC(MyMFC):
    model_name = 'MC-10SCCM-D'
    max_flow_rate = 10.0 * pq.cc / pq.min
    ao_channel = 0


class MyMediumMFC(MyMFC):
    model_name = 'check label'
    max_flow_rate = 1.0 * pq.L / pq.min
    ao_channel = 1


class MyHighMFC(MyMFC):
    model_name = 'MC-10SLPM-D'
    max_flow_rate = 10.0 * pq.L / pq.min
    ao_channel = 2

class MyValve():
    def __init__(self, v_num):
        valve_num = v_num
        model_number = 'SY5300R-5U1'
        # The current position is the first position listed        


class MyJar(Jar):
    height = 5 * pq.cm
    diameter = 5 * pq.cm
