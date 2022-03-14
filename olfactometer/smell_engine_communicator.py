import struct
import select
import socket
import sys
import binascii
import getopt
import time
import quantities as pq

from collections import deque 
import numpy as np
import datetime
import typer
from typing import Optional
from pprint import pprint
from olfactometer.smell_engine import SmellEngine
from olfactometer.data_container import DataContainer

class SmellEngineCommunicator:
    """
    SmellEngineCommunicator establishes a network comm line between Unity and Smell Engine.
    First the equipment is configured, then the socket waits for a connection (client devices)
    Once client connection is established, PubChemID's are assigned, ValveDriver is instantiated,
    then socket loops continuously listening for sets of data.

    Attributes:
        debug_mode: flag for physical vs simulated hardware specified via command-line.
    """
    def __init__(self, debug_mode=False, odor_table=None, write_flag=False):    
        print("Initializing")    
        self.write_flag = write_flag
        self.debug_mode = debug_mode
        self.odor_table = odor_table
        self.data_container = DataContainer()                     
        # CREATE TCP/IP SOCKET
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.settimeout(1)
        self.server.bind(('localhost', 12345))
        self.num_odorants = 0
        self.last_concentrations = []
        print("Listening for clients..")
        self.server.listen(1)
        # Sockets from which we expect to read
        self.inputs = [ self.server ]
        # Sockets to which we expect to write
        self.outputs = [ ]
        self.smell_engine = None
        self.initialized = False
        self.init_main_loop()

    def init_main_loop(self):
        while self.inputs:
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, 1)
            if not readable:
                print("Skip")
                time.sleep(1)
            else:
                # Handle inputs
                for select_readables in readable:
                    if select_readables is self.server:
                        # A "readable" server socket is ready to accept a connection
                        self.client, self.client_adr = self.server.accept()
                        print("Client connected at:\t" + str(self.client_adr))        
                        self.inputs.append(self.client)
                        self.client.setblocking(0)
                        self.inputs.append(self.client)
                    else:
                        if (self.num_odorants == 0):    self.receive_quantity_odorants()
                        else:
                            if not self.smell_engine:                                
                                self.smell_engine = SmellEngine(data_container=self.data_container, debug_mode=self.debug_mode, 
                                                            write_flag=self.write_flag,PID_mode=False, look_up_table_path=self.odor_table)
                            elif not len(self.smell_engine.om_ids) > 0:
                                self.smell_engine.set_odorant_molecule_ids(self.receive_pub_chemIDs())

                            elif (self.smell_engine.om_dilutions != None) and not len(self.smell_engine.om_dilutions) > 0:
                                self.smell_engine.set_odorant_molecule_dilutions(self.recieve_dilutions())
                            elif not self.initialized:                              
                                #NEED TO SET smell_engine.set_odorant_molecule_dilutions([10, 10])  
                                #I am not sure whats the best way to do this should we do this in unity editor and then send over a socket connection. 
                                self.smell_engine.set_odorant_molecule_dilutions([10, 10,10])
                                self.smell_engine.initialize_smell_engine_system()  
                                self.initialized = True      
                            else:
                                self.main_thread_loop()        
                  
    def receive_quantity_odorants(self):
        """
        Assign PubChemID's on startup to the LogicalOlfactomete cid's.
        Method is called from LogicalOlfactometer instantiation, so it waits 
        until the first set of values are transmitted from Unity (which are the PubChemIDs)
        """
        print('\nwaiting for a connection')
        self.unpacker = struct.Struct('i')      # Receive list of ints
        data = self.client.recv(self.unpacker.size)
        if data:
            # print('received # of PubChemIDs:\t{!r}'.format(binascii.hexlify(data)))
            unpacked_data = list(self.unpacker.unpack(data))
            print('Received  # of PubChem IDs:\t', unpacked_data)
            self.num_odorants = unpacked_data[0]
        

    def receive_pub_chemIDs(self):
        """
        Assign PubChemID's on startup to the LogicalOlfactomete cid's.
        Method is called from LogicalOlfactometer instantiation, so it waits 
        until the first set of values are transmitted from Unity (which are the PubChemIDs)
        """
        print('\nreceiving pub chem IDS')
        self.unpacker = struct.Struct(self.num_odorants * 'i')      # Receive list of ints
        data = self.client.recv(self.unpacker.size)
        if (data):
            print('received PubChemIDs:\t{!r}'.format(binascii.hexlify(data)))
            unpacked_data = list(self.unpacker.unpack(data))
            print('unpacked PubChem IDs:\t', unpacked_data)
            return unpacked_data            # This data is assigned to the PID's prop of Valve Driver.


    def recieve_dilutions(self):
        """
        Recieve Dilutions values for self.smell_engine.set_odorant_molecule_dilutions([10, 10,10])
        """
        print('\nreceiving Dilutions')
        self.unpacker = struct.Struct(self.num_odorants * 'i')      # Receive list of ints
        try:
            data = self.client.recv(self.unpacker.size)
            if (data):
                print('received Dilutions:\t{!r}'.format(binascii.hexlify(data)))
                unpacked_data = list(self.unpacker.unpack(data))
                print('unpacked Dilutions:\t', unpacked_data)
                return unpacked_data            # This data is assigned to the PID's prop of Valve Driver.
        except socket.error as e:
                if str(e) == "[Errno 35] Resource temporarily unavailable":
                    time.sleep(0.1)
    
    def main_thread_loop(self):
        """
        LoopConnection continuously listens for a list of doubles, converts the bytes,
        then issues them to the Smell Composer and Valve Driver via the method load_concentrations()
        """
        self.client.setblocking(1)
        self.unpacker = struct.Struct((self.num_odorants) * 'd')
        try:            
            millis = int(round(time.time() * 1000))            
            data = self.client.recv(self.unpacker.size)                    
            if data:                                            
                unpacked_data = list(self.unpacker.unpack(data))                    
                print("Received:\t" + str(unpacked_data))  
                self.load_concentrations(unpacked_data)                                                                       
            diff_time = int(round(time.time() * 1000)) - millis
            if (self.write_flag):
                print("Diff time to receive values:\t" + str(diff_time))
                target_conc = {'target_concentration' : unpacked_data, 'receive_target_conc_latency' : diff_time/1000}
                self.data_container.append_value(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), target_conc)                           
        except socket.error as e:
            print(("Couldnt connect with the socket-server: "
                "%s\n terminating program") % e)
            print("struct error, aborting connection")
            print("connection aborted")
            if (self.write_flag):   self.data_container.create_json()
            self.smell_engine.close_smell_engine()
            self.client.close()
            print("Client disconnected, server shutting down.")                            
            sys.exit(1)            
        except struct.error:
            print("Skipping odor frame")
            

    
    def load_concentrations(self, concentration_mixtures):
        """
        Append list of concentrations to mixtures deque within Smell Composer,
        which in turn issues odorants to the Valve Driver for the Olfactometer.
        The desired odorant concentration vector is formatted then passed down the 
        Smell Engine pipeline.         

        Attributes:
            concentration_mixtures: List of desired odorant concentrations
        """
        try:
            antilog_concentration_mixtures = [] 
            for concentration in concentration_mixtures:
                if abs(10**concentration)==float('inf'):    # If overflow
                    antilog_concentration_mixtures.append(0)    
                else:
                    antilog_concentration_mixtures.append(10**concentration)
            if (self.smell_engine.smell_controller.valve_driver.timer_paused):    self.smell_engine.smell_controller.valve_driver.timer_pause()
            # Match the odorant concentration value to its odorant ID via index
            self.desired = {self.smell_engine.olfactometer.find_odorant_id_by_index(0): antilog_concentration_mixtures[0]*pq.M, \
                            self.smell_engine.olfactometer.find_odorant_id_by_index(1): antilog_concentration_mixtures[1]*pq.M, \
                            self.smell_engine.olfactometer.find_odorant_id_by_index(2): antilog_concentration_mixtures[2]*pq.M}
            # Run optimizer and receive optimization results by setting concentrations and flow rate
            if (self.last_concentrations is not concentration_mixtures):            
                self.smell_engine.set_desired_concentrations(antilog_concentration_mixtures)
                self.last_concentrations = concentration_mixtures
            else:   # skip every other repeated instance
                self.last_concentrations = []   
        except OverflowError as err:
            print('Hit overflow, skipping this odor frame')

    

def main(debug_mode: bool, 
        odor_table_mode: Optional[str] = typer.Argument(None, help="Can specify odor table pkl file."),  
        write_data: Optional[bool] = typer.Argument(False, help="Can specift if data should be saved in session.")):    
    if (debug_mode is None):
        typer.echo("Must specify if running in debug mode")
        return    
    sc = SmellEngineCommunicator(debug_mode, odor_table_mode, write_data)
    sc.main_thread_loop()
    

if __name__ == "__main__":
    typer.run(main)