import json
import sys
import pickle
import datetime
import pandas as pd
import sys
from collections import OrderedDict
from collections import deque 
from scipy.spatial import KDTree
from olfactometer.smell_controller import SmellController
import quantities as pq
import numpy as np
np.set_printoptions(precision=4)
from olfactometer.equipment import Olfactometer
from olfactometer.my_equipment import MyValve, MyJar, MyLowMFC, \
                                      MyMediumMFC, MyHighMFC
from olfactometer.odorants import Solution, Compound, ChemicalOrder, \
                                  Vendor, Molecule
from pprint import pprint
from olfactometer.valve_driver import ValveDriver

class SmellEngine:

    _om_ids = []
    _om_dilutions = []

    def __init__(self, total_flow_rate=4000, n_odorants= 3, data_container = None, debug_mode=True, 
                write_flag=False, PID_mode=False, look_up_table_path = None, oms=None):    
        self.N_ODORANTS = n_odorants
        print("Initializing")       
        self.odorant_molecules = oms        
        self.write_flag = write_flag
        self.PID_mode = PID_mode
        self.total_flow_rate = total_flow_rate
        self.debug_mode = debug_mode
        self.data_container = data_container
        self.starting_concentration_vector = None
        self.target_concentration = []        
        self.look_up_table_path = look_up_table_path 

    # def load_odorant_molecules(self, oms):
    #     if (isinstance(oms, list)):
    #         print("List")
    #     elif (isinstance(oms, OrderedDict)):
    #         print("Dict")

    @property
    def om_ids(self):
        return self._om_ids

    @om_ids.setter
    def om_ids(self, ids):
        self._om_ids = ids

    @property
    def om_dilutions(self):
        return self._om_dilutions

    @om_dilutions.setter
    def om_dilutions(self, dilutions):
        self._om_dilutions = dilutions

    def append(self, val):
        if isinstance(val, (tuple, list)):
            self.om_ids = self.om_ids + [val[0]]
            self.om_dilutions = self.om_dilutions + [val[1]]
        else:
            self.om_ids = self.om_ids + [val]
            self.om_dilutions = self.om_dilutions + [1]
        return self.om_ids

    def initialize_smell_engine_system(self, with_nidaq=True):
        """
        Presumes user has manually set OM ids before initializing
        system pipeline
        """
        self.initialize_equipment()
        if with_nidaq:
            self.initialize_olfactometer()
        self.starting_concentration_vector = [10**-12 * pq.M] * len(self.smell_controller.target_outflow_concs.keys())
        # print("Starting:\t" + str(self.starting_concentration_vector))

    
    def initialize_equipment(self):
        """
        Configure olfactometer equipment via Smell Composer component(s).
        First we specify molecules by CID number and define their vapor
        pressure, densities, and solution.
        Instantiate the olfactometer.
        Determines the jars and dilutions required to achieve the target
        specified per molecule.
        Perform optimization to configure olfactometer
        Format values for ValveDriver to execute.           
        """
        # Instantiate two molecules by CID number
        # self.molecules = [Molecule(om_id, fill=True) for om_id in self.om_ids]
        if (self.odorant_molecules == None):    self.molecules = [Molecule(om_id, fill=True) for om_id in self.om_ids]
        else:                                   self.molecules = [Molecule(om, self.odorant_molecules[om], fill=True) for om in self.odorant_molecules]
        # Light mineral oil, an odorless solvent
        self.molecules.append(Molecule(347911206, 'Light Mineral Oil', fill=True, vapor_press=0, dens=0.85))
        light_mineral_oil = self.molecules[-1]
        light_mineral_oil.molecular_weight = 500 * pq.g / pq.mol

        # Vapor pressures at 25 degrees Celsius (obtained from PubChem)        
        for num_molecules in range(len(self.molecules)):
            self.molecules[num_molecules].vapor_pressure *= pq.mmHg
            self.molecules[num_molecules].density *= pq.g/pq.cc
            print(f"OM {self.molecules[num_molecules].name} has vapor pressure of {self.molecules[num_molecules].vapor_pressure} and density of {self.molecules[num_molecules].density}")
           
        # Mineral oil does not have a proper molecular weight since
        # it is itself a mixture, but we have to put something reasonable
        # in order compute mole fraction of the solute        
        # Create a vendor
        sigma_aldrich = Vendor('Sigma Aldrich', 'http://www.sigma.com')
        # Specify two chemicals ordered from this vendor,
        # which are nominally the above molecules
        self.solvent_order = ChemicalOrder(light_mineral_oil, sigma_aldrich, '')        
        self.chemical_orders = [ChemicalOrder(mol, sigma_aldrich, '')
                                for mol in self.molecules[:-1]]

        # These are now actual chemical on the shelf, with potential stock numbers
        # dates arrived, dates opened.
        self.solvent = Compound(self.solvent_order, is_solvent=True)
        self.compounds = [Compound(chemical_order) for chemical_order in self.chemical_orders]
        self.n_odorants = len(self.compounds)
        # Two odorants stocks that we produced by diluting the compounds above        
        self.solutions = []
        self.solution_volume = 100*pq.mL
        self.solvent_volumes = [self.solution_volume*(dilution-1)/dilution
                           for dilution in self.om_dilutions]
        self.solute_volumes = [self.solution_volume/dilution
                          for dilution in self.om_dilutions]        
        # Jars [10]
        for i in range(10):
            if (i < len(self.compounds)):
                self.solutions.append(
                    Solution({self.compounds[i]: self.solute_volumes[i],
                            self.solvent: self.solvent_volumes[i]}))  
            else:
                self.solutions.append(Solution({self.solvent: self.solution_volume}))
        print(f"Odor Compounds Length:{len(self.compounds)}")
     
        self.n_solutions = len(self.solutions)
        # Create `n_odorants` valves of the type that we use
        self.valves = [MyValve('Valve #%d' % (i+1))
                       for i in range(self.n_solutions)]        
        self.jars = [MyJar('Jar #%d' % (i+1))
                     for i in range(self.n_solutions)]
        # Fill each of those jars with one of our odorants        
        for i, jar in enumerate(self.jars):
            jar.fill(self.solutions[i], 25*pq.mL)
        # Add two MFCs (one for low flow and one for high flow),
        # set their setpoints
        self.mfc_high = MyMediumMFC('MFC_A_High')
        self.mfc_low = MyLowMFC('MFC_B_Low')
        self.mfc_carrier = MyHighMFC('MFC_Carrier')
        self.mfc_high.curr_flow_rate = 0.2 * pq.L / pq.min
        self.mfc_low.curr_flow_rate = 1.0 * pq.cc / pq.min
        self.mfc_carrier.curr_flow_rate = 1.8 * pq.L / pq.min
        self.mfcs = [(self.mfc_high, self.mfc_low), self.mfc_carrier]
        #Load KD-Tree
        if(self.look_up_table_path != None):
            print("Initialzing KD-Tree")
            df = pd.read_pickle(self.look_up_table_path)
            sys.setrecursionlimit(1000000)
            kdtree = KDTree(df.values)
            self.olfactometer = Olfactometer(self.jars, self.mfcs)
            self.smell_controller = SmellController(self.olfactometer, self.data_container, kdtree_flag=True,kdtree=kdtree, smell_data_frame=df)

        else: 
            self.olfactometer = Olfactometer(self.jars, self.mfcs)
            self.smell_controller = SmellController(self.olfactometer, self.data_container, kdtree_flag=False)
                
        self.desired = {molecule: (10**-i)*1e-7*pq.M
                        for i, molecule in enumerate(self.molecules[:-1])}

        ##################### OPTIMIZATION SECTION ##############################
        # Get the optimization results directly                
        self.smell_controller.optimize(self.desired, self.total_flow_rate*pq.cc/pq.min, report=False)
        self.olfactometer.loaded_molecules


    def initialize_olfactometer(self):
        """
        Initialize Smell Driver instance which instantiates a
        ValveDriver instance.
        This instance is then assigned to the Smell Composer so the
        communication line of
        odorant mixtures is established.

        Attributes:
            debug_mode: Flag denoting physical vs simulated hardware.
        """        
        self.smell_controller.valve_driver = ValveDriver(self.olfactometer,
                                               data_container=self.data_container,                                               
                                               PID_mode=self.PID_mode,
                                               debug_mode=self.debug_mode)        
        self.smell_controller.valve_driver.timer_setup(interval=0.5)
        self.smell_controller.valve_driver.timer_start()


    def set_odorant_molecule_ids(self, ids):
        """
        Assign PubChemID's on startup to the Valve Driver cid's.

        Attributes:
            ids: List containing uniquely identifiable int values of OM ids
        """
        self.om_ids = ids

    def set_odorant_molecule_dilutions(self, dilutions):
        """
        Assign PubChemID's on startup to the Valve Driver cid's.

        Attributes:
            ids: List containing uniquely identifiable int values of OM ids
        """
        
        self.om_dilutions = dilutions
        

    def set_valve_duty_cycles(self, valves):
        """
        Override valve duty cycles for system tests.

        Attributes:
            ids: Valve states
        """
        print("Set valves", valves)
        self.smell_controller.valve_driver.set_valve_states(valves)
        self.smell_controller.valve_driver.issue_odorants(self.smell_controller.clean_valve_mfc_values())

    def get_valve_duty_cycles(self):
        # TODO: Dynamically determine # of valves
        valve_states = self.print_data_binary(self.smell_controller.valve_driver.valve_durations)  
        valve_duty_cycles = []
        for x in range(5):
            digital_data = [valve_states[x][i] for i in range(3)]
            valve_duty_cycles.append(digital_data)
        return valve_duty_cycles

    def set_starting_concentration(self, starting_vector):
        self.starting_concentration_vector = starting_vector 
    
    def calculate_target_achieved_error(self):
        target_achieved = {}
        target_achieved = OrderedDict()
        target_achieved= target_achieved.fromkeys(self.smell_controller.target_outflow_concs.keys(),[])
        for index, tkey in enumerate(target_achieved.keys()):
            # Calculate error as change achieved concentration rate - change in target concentration rate 
            print("achieved:\t" + str(self.smell_controller.achieved[index]) + ", target:\t" + str(self.smell_controller.target_outflow_concs[tkey]))
            if (self.smell_controller.achieved[index] == 0):
                self.smell_controller.achieved[index] = 10**-12 * pq.M
            # error_rate = 10**(abs((math.log10(self.olfactometer.achieved[index]) - math.log10(self.olfactometer.target_outflow_concs[tkey]))))
            error_rate = (abs(self.smell_controller.achieved[index] - self.smell_controller.target_outflow_concs[tkey]) / self.smell_controller.target_outflow_concs[tkey]) * 100
            # Populate ordered dictionary with values
            target_achieved[tkey] = (self.smell_controller.target_outflow_concs[tkey], self.smell_controller.achieved[index], error_rate)
            # Print out formatted results
            print('ID: %s, starting: %s, target: %s, achieved: %s, Error Rate: %5d%%' % (tkey, self.starting_concentration_vector[index], target_achieved[tkey][0], target_achieved[tkey][1], target_achieved[tkey][2]))            
            if (self.data_container):   # WRITE MODE
                generate_samples = {'odorant_id' : str(tkey), 'starting_odorant_concentration' : str(self.starting_concentration_vector[index]), 'target_odorant_concentration' : str(target_achieved[tkey][0]), 'achieved_odorant_concentration' : str(target_achieved[tkey][1]), 'error_rate': str(target_achieved[tkey][2]) }
                self.data_container.append_value(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), generate_samples)
        self.starting_concentration_vector = [target_achieved[tkey][1] for tkey in target_achieved.keys()]
        # print("Starting:\t" + str(self.starting_concentration_vector))
    
    def print_data_binary(self, concentration):
        """
        A debug method for printing binary representations of concentrations (digital states of olfactometer).

        Args:
            concentration(:obj:`list` of :obj:`float`): List of concentration states.
        """
        bin_format_valves = []
        for i, odorant in enumerate(concentration):
            vlv_print = ""
            vlv_state = []
            for state in odorant:
                #valve_write = str('{0:032b}'.format(state[0][0]))
                t = state[1]
                # vlv_print += valve_write + "," + str(t) + ","
                vlv_print += str(t) + ","
                vlv_state.append(t)
                # print("[ " + valve_write + ", " + str(t) + "]\n")
            bin_format_valves.append(vlv_state)
        # print("BIN", bin_format_valves)
        return bin_format_valves

    def set_mfc_setpoints(self, mfc_setpoints):
        """
        Override mfc setpoints

        Attributes:
            ids: mfc setpoints 
        """
        print("Setpoints", mfc_setpoints)
        self.smell_controller.valve_driver.set_mfc_setpoints(mfc_setpoints)
        self.smell_controller.valve_driver.issue_odorants(self.smell_controller.clean_valve_mfc_values())

    def automation_set_mfc_setpoints(self, mfc_setpoints):
        """
        Override mfc setpoints in order B, A, C 

        Attributes:
            ids: List[] specifying each MFCs flow rate relative to its max.
        """
        print("Setpoints", mfc_setpoints)
        mfc_configurations = []
        mfc_configurations.append((mfc_setpoints[0]*10, mfc_setpoints[0]*5))
        mfc_configurations.append((mfc_setpoints[1]*1000, mfc_setpoints[1]*5))
        # mfc_configurations.append((2000-(mfc_setpoints[1]*1000-mfc_setpoints[0]*10), 5*((1-mfc_setpoints[0]*.01 - mfc_setpoints[1])/10))) # 2000 for 2L balanced flow
        # mfc_configurations.append((0,0)) # 2000 for 2L balanced flow
        mfc_configurations.append((450,0.245)) # 500 for 0.5L balanced flow
        self.smell_controller.valve_driver.set_mfc_setpoints(mfc_configurations)
        self.smell_controller.valve_driver.issue_odorants(self.smell_controller.clean_valve_mfc_values())

    def get_mfc_setpoints(self):
        analog_data = [self.smell_controller.valve_driver.analog_values[0][0],\
                        self.smell_controller.valve_driver.analog_values[1][0],\
                        self.smell_controller.valve_driver.analog_values[2][0]]
        return analog_data

    def add_molecule_id(self, id):
        """
        Add Odorant Molecule to system
        
        Attributes:
            id: int values uniquely identifying OM
        """
        self.om_ids.append(id)

    def get_molecular_ids(self):
        return self.om_ids

    def set_desired_concentrations(self, concentrations):
        """
        Reads and writes concentration values to Smell Engine and Valve Driver

        Attributes:
            concentrations: List containing concentration values
        """
        
        self.target_concentration = concentrations        
        self.desired = OrderedDict([
            (self.olfactometer.find_odorant_id_by_index(i), concentrations[i]*pq.M) for i in range(self.N_ODORANTS)])
        # Run optimizer and receive optimization results by setting concentrations and flow rate                
        self.smell_controller.target_outflow = (self.desired, self.total_flow_rate*pq.cc/pq.min) #change to 4000 when operating
        self.smell_controller.valve_driver.mixtures.append(concentrations)        
    
    def get_desired_concentrations(self):
        return self.target_concentration
    
    def set_olfactometer_target_outflow(self, m_flowrate):
        self.smell_controller.target_outflow = (self.desired, m_flowrate*pq.cc/pq.min) #change to 4000 when operating

    def close_smell_engine(self):
        self.data_container.create_json()
        self.smell_controller.valve_driver.timer_stop()
        