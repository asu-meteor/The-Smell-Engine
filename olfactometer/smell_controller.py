from olfactometer.contour_plot_generator import plotterDim 
import numpy as np
import time
import pandas as pd
from collections import OrderedDict
import quantities as pq
from numba import jit
from olfactometer.equipment import MFC
from scipy.optimize import minimize, least_squares

class SmellController:
    def __init__(self, olfactometer, data_container=None,                 
                 valve_driver=None,kdtree_flag=False,kdtree=None,smell_data_frame = None):
        # Exclude solvent from most calculations        
        self.olfactometer = olfactometer
        self.data_container = data_container
        self._target_outflow_concs = {}
        self._target_outflow_rate = self.max_outflow_rate
        self._olfactometer_schedule = {}
        self._loaded_cids = {}
        self.vapor_phase_concentration_achieved = None
        self.valve_driver = valve_driver  
        self.vapor_phase_concentrations = []
        self.kdtree=kdtree
        self.kdtree_flag = kdtree_flag
        self.smell_data_frame = smell_data_frame 
        self.mutlidim_plotting = plotterDim(True, "./graphs")

    @property
    def target_outflow_concs(self):
        if not len(self._target_outflow_concs):
            self._target_outflow_concs = {m: 0*pq.M for m in self.olfactometer.loaded_molecules}
        return self._target_outflow_concs
    
    @target_outflow_concs.setter
    def target_outflow_concs(self, concs):
        self._target_outflow_concs = concs
    
    @property
    def target_outflow_rate(self):
        return self._target_outflow_rate
    
    @target_outflow_rate.setter
    def target_outflow_rate(self, rate):
        self._target_outflow_rate = rate
    
    @property
    def target_outflow(self):
        return self._target_outflow_concs, self._target_outflow_rate
        
    @target_outflow.setter
    def target_outflow(self, concs_rate):
        concs, rate = concs_rate
        self._target_outflow_concs = concs
        self._target_outflow_rate = rate
        self.update_target()

    @property
    def olfactometer_schedule(self):
        return self._olfactometer_schedule
        
    @olfactometer_schedule.setter
    def olfactometer_schedule(self, olfactometer_schedule):
        """
        Optimizer() is executed anytime Update Target method is executed and olfactometer_schedule prop is set.
        This method checks the olfactometer_schedule to determine if a new configuration is requested
        of the olfactometer. If so, it will convert a dictionary of configurations into 
        something compact for ValveDriver.issue_odorants() to parse and execute.

        Attributes:
            olfactometer_schedule: Dictionary specifying valve concentration strengths, MFC weights, and flow rates derived from LLS
        """        
        old = self._olfactometer_schedule  # Previous values
        self._olfactometer_schedule = olfactometer_schedule
        if self.valve_driver and olfactometer_schedule != old:
            # If the values are new and there is a logical olfactometer,
            # send the values to it            
            clean = self.clean_valve_mfc_values() 
            print("\nOptimizer clean values", clean)       
            self.valve_driver.issue_odorants(clean)

    def clean_valve_mfc_values(self, values=None, print_flow_rates=False):
        """
        Convert dictionary that looks like:
        {'w1MFC_A_High': 0.8840516038671588,
        'w2MFC_A_High': 0,
        'w1MFC_B_Low': 0.11551628411711523,
        'w2MFC_B_Low': 0,
        'fMFC_A_High': array(1.9601) * cc/min,
        'fMFC_B_Low': array(0.01) * cc/min,
        'MFC_Carrier': array(2198.0299) * cc/min}                
        """
        if values is None:  values = self.olfactometer_schedule
        clean = {'valves': [], 'mfcs': []}
        
        for j, _ in self.olfactometer.jars.items():
            high = values['w%dMFC_A_High' % j]
            low = values['w%dMFC_B_Low' % j]
            clean['valves'].append((j, high, low))            
        flow_values = {key: value for key, value in values.items() if ('f' in key or 'Carrier' in key)}
        
        if (print_flow_rates):  print("Flow Rates:", flow_values)
        clean['mfcs'] = self.mfc_flow_rates_to_voltages(flow_values)
        
        return clean

    def mfc_flow_rates_to_voltages(self, values):
        mfcs_flat = self.olfactometer.mfc_flat_list()
        mfc_voltages = {}
        for key, value in values.items():
            for mfc in mfcs_flat:
                if mfc.label in key:
                    mfc_voltages[mfc] = mfc.flow_rate_to_voltage(value)
        print("Voltages:", mfc_voltages)
        return mfc_voltages
                     
    def update_target(self, report=False):
        """
        Executed externally, ideally through the SmellEngineCommunicator class.
        This method takes the assigned target concentrations and flow rate then message
        passes target states through the Smell Engine pipeline.
        """
        # print(("Updating valve and MFC states to meet target concentrations "
        #        "and flow rates"))
        self.optimize(self.target_outflow_concs,
                      self.target_outflow_rate,
                      report=report)    

    # Search through manifold jars by odorant id.
    def find_odorant_id_by_index(self, m_index):
        return self.olfactometer.loaded_molecules[m_index]
            
    @property
    def max_outflow_rate(self):
        """The maximum possible flow rate if all connected-in-parallel MFCs are
        at their maximum flow rates"""
        def max_list_flow_rate(list_of_mfcs):
            result = 0 * pq.cc/pq.min
            for mfc_or_list in list_of_mfcs:
                if isinstance(mfc_or_list, MFC):
                    result += mfc_or_list.max_flow_rate
                else:
                    result += max_list_flow_rate(mfc_or_list)
            return result
        return max_list_flow_rate(self.olfactometer.mfcs)
    
    def get_vapor_concs_dense(self, target_odorants):
        # Make a matrix containing the vapor phase concentrations of each
        # odorant in each jar
        n_odorants = len(self.olfactometer.loaded_molecules)
        n_jars = len(self.olfactometer.jars)
        J = np.zeros((n_odorants, n_jars))*pq.M
        for j, jar in self.olfactometer.jars.items():
            for m, c in jar.vapor_concs.items():
                c_ = c.rescale(pq.M)
                i = self.olfactometer.loaded_molecules.index(m)
                J[i, j-1] = c_
        return J

    def get_max_flow_rates(self):
        mixing_mfcs = self.olfactometer.mfcs[0] # Th
        return np.array([float(mfc.max_flow_rate.rescale(pq.cc/pq.min)) for mfc in mixing_mfcs])

    @classmethod
    def calc_conc(cls, variables, n_jars, max_flow_rates, A):
            """
            This method is invoked externally to calculate concentration given olfactometer configuration
            variables: MUST BE np.array!  Contains olfactometer mfc values and valve duty cycles
            n_jars: assigneed from class instance
            max_flow_rates: assigneed from class instance
            A: Gas Phase Concentration of jars x odorants
            """
            return calc_conc_jit(variables, n_jars, max_flow_rates, A)

    @classmethod
    def residuals(cls, variables, x, n_jars, max_flow_rates, total_vapor, fixed_A, fixed_B, alpha):
            # print("residualVar: "+str(variables))
            """
            This method is invoked by the non-linear least squares solver.
            wNA: The fraction of time that valve N is in state A
            wNB: The fraction of the remaining time that valve N is in state B
            fA: The flow rate through MFC A
            fB: The flow rate through MFC B
            """
            # print("Variables:\t" + str(variables))
            # Unpack variables
            wA = variables[:n_jars]
            wB = variables[n_jars:(n_jars*2)]
            fA, fB = variables[(n_jars*2):]
            # Convert fraction-of-remaining time values (w1B, w2B, ...)
            # to absolute fractions
            wB = (1-wA)*wB                    
            # Pre-compute sums for efficiency
            wAs = wA.sum()# + fixed_A  # Change later 
            wBs = wB.sum()# + fixed_B        
            # print(f"fa: {str(fA)},fb: {str(fB)}, wAs: {str(wAs)}, wBs {str(wBs)}")
            # The residuals whose sum of squares will be minimized
            residuals = [fA*wA[i]/wAs + fB*wB[i]/wBs - x[i] for i in range(n_jars-2) if total_vapor[i]]
            # This code is probably slowing down optimization
            for valve_index, valve in enumerate(wA):
                cls.mutlidim_plotting.append_value("w"+str(valve_index)+"A",valve)
            for valve_index, valve in enumerate(wB):
                cls.mutlidim_plotting.append_value("w"+str(valve_index)+"B",valve)
            cls.mutlidim_plotting.append_value('fA',fA)
            cls.mutlidim_plotting.append_value('fB',fB)
            # self.mutlidim_plotting.append_value('w1MFC_A_High',values['w1MFC_A_High'])            
            # Try to sparsen the solution by penalizing the valves being open            
            #penalty = sum(np.array([np.sqrt(wA[i]*wB[i]) for i in range(n_jars-2)]))
            residuals = residuals #+ alpha*penalty
            return residuals
            
    
    def optimize(self, target_outflow_concs=None, target_outflow_rate=None, 
                 report=False):
        """Find the valve duty cycles and MFC settings that bring this route 
        closest to target. This will be done by varying actual valve positions 
        and flow rates, so it should only be done on a virtual olfactometer"""
        millis = int(round(time.time() * 1000))        
        if target_outflow_concs is None:    target_outflow_concs = self.target_outflow_concs
        else:                               self._target_outflow_concs = target_outflow_concs
        if target_outflow_rate is None:     target_outflow_rate = self.target_outflow_rate
        else:                               self._target_outflow_rate = target_outflow_rate
        
        # Make sure that the molecules we want in the outflow are all loaded into at least one jar in the olfactometer
        target_molecules = set(list(target_outflow_concs))        
        assert target_molecules.issubset(self.olfactometer.loaded_molecules)
        # Create a list of all molecules available in the olfactometer
        # and their desired outflow concentrations (including zeros)
        target_dense = OrderedDict([(m,(target_outflow_concs[m] if m in target_outflow_concs else 0*pq.M))
                                     for m in self.olfactometer.loaded_molecules])        
        mixing_mfcs = self.olfactometer.mfcs[0] # The other one (at index 1) is the carrier MFC
        mfc_names = [mfc.label for mfc in mixing_mfcs]
        n_mfcs = len(mfc_names)
        n_jars = len(self.olfactometer.jars)
        # Make this a self property other
        vapor_concs_dense = self.get_vapor_concs_dense(target_molecules)        
        # Make the matrix `A` in the least-squares minimization `argmin(|Ax - b|)`
        target_outflow_rate_ccm = target_outflow_rate.rescale(pq.cc/pq.min)
        self.vapor_phase_concentrations = vapor_concs_dense/target_outflow_rate_ccm
        if(self.kdtree_flag):   self.kdtree_lookup(target_dense, mfc_names, target_outflow_rate_ccm)
        else:                   self.lls_olfactometer_scheduler(vapor_concs_dense, target_outflow_rate_ccm, target_dense)
        # if (self.data_container != None):
        #     diff_time = int(round(time.time() * 1000)) - millis                
        #     print("Diff time to run optimizer:\t" + str(diff_time/1000))
        #     optimizer_results = {'optimizer_latency': diff_time/1000, 'olfactometer_schedule' : str(self.olfactometer_schedule), 'Error': ("Error is %.2g" % self.least_squares_result.cost)}
        #     self.data_container.append_value(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), optimizer_results)
        self.optimization_report()                

    def lls_olfactometer_scheduler(self, vapor_concs_dense, target_outflow_rate_ccm, target_dense):
        self.vapor_phase_concentrations = vapor_concs_dense/target_outflow_rate_ccm
        np.set_printoptions(precision=12)
        # Make the target vector `b` of vapor-phase concentrations
        b = np.array([float(c.rescale(pq.M)) for m,c in target_dense.items()])
        # Obtain the vector of state variables `x` that minimizes `|Ax - b|`            
        x, _residuals, _rank, _s = np.linalg.lstsq(self.vapor_phase_concentrations, b, rcond=None)
        self.lls_ = x                        

        # List of variables is all the jar-to-manifold times (all combinations)
        #and all the outflow fractions except for the last MFC
        mixing_mfcs = self.olfactometer.mfcs[0] # The other one (at index 1) is the carrier MFC
        mfc_names = [mfc.label for mfc in mixing_mfcs]
        n_mfcs = len(mfc_names)
        n_jars = len(self.olfactometer.jars)
        # Make this a self property other                        
        self.variables = ['w%d%s'%(j,mfc) for mfc in mfc_names for j in self.olfactometer.jars]
        self.variables += ['f%s'%mfc for mfc in mfc_names]
        # Set all initial guesses to 0.5
        # (for valve states this will mean 0.5 of the time spent in this state)
        initial_guesses = (np.ones(len(self.variables))*0.1)            
        total_vapor = vapor_concs_dense.sum(axis=0)
        def residuals_in(variables, x=x):
            """
            wNA: The fraction of time that valve N is in state A
            wNB: The fraction of the remaining time that valve N is in state B
            fA: The flow rate through MFC A
            fB: The flow rate through MFC B
            """
            #print(f"What you got {variables} and {x}")
            # Unpack variables
            wA = variables[:n_jars]
            wB = variables[n_jars:(n_jars*2)]
            fA, fB = variables[(n_jars*2):]
            # Convert fraction-of-remaining time values (w1B, w2B, ...)
            # to absolute fractions
            wB = (1-wA)*wB        
            fA = fA * 999.9999999999998
            fB = fB * 10.0
            # Pre-compute sums for efficiency
            wAs = wA.sum()
            wBs = wB.sum()
            if (wAs == 0): wAs=1e-20
            if (wBs == 0): wBs=1e-20
            # The residuals whose sum of squares will be minimized
            residuals = [fA*wA[i]/wAs + fB*wB[i]/wBs - x[i] for i in range(n_jars)
                        if total_vapor[i]]

            for valve_index, valve in enumerate(wA):    self.mutlidim_plotting.append_value("w"+str(valve_index)+"A",valve)
            for valve_index, valve in enumerate(wB):    self.mutlidim_plotting.append_value("w"+str(valve_index)+"B",valve)
            self.mutlidim_plotting.append_value('fA',fA)
            self.mutlidim_plotting.append_value('fB',fB)                            
            penalty = sum(np.array([np.sqrt(wA[i]*wB[i]) for i in range(n_jars)]))
            alpha = 1
            #residuals = residuals + penalty * alpha
            return residuals                    
        # Set low bounds to 0% of the time for valves, 0.001 of max flow rate for MFCs
        # an MFC is even used   
        bounds_low = [0]*((n_jars)*n_mfcs) + [0.001]*n_mfcs            
        # Set high bounds to 100% of the time for valves, 100% of max flow rate for MFCs            
        bounds_high = [1]*((n_jars)*n_mfcs) + [1]*n_mfcs            
        # Obtain variables of interest from linear least squares result using non-linear least squares                                            
        least_squares_result= least_squares(residuals_in, initial_guesses, method='dogbox',
                                                args=(x,), verbose=0, loss='linear',
                                                bounds=(bounds_low, bounds_high))            


        # Extract resulting solution into a dictionary of variable names and values
        # print("Variables: " + str(least_squares_result.x.tolist()))
        # print("X:\t"+ str(self.lls_.tolist()))
        values = {self.variables[i]: value
                for i, value in enumerate(least_squares_result.x)} 
        self.nlls_ = least_squares_result.x                   
        # Transform values for position B of the valves,
        # and determine the flow rate of the mixing MFC
        mixing_sum = 0 * pq.cc/pq.min
        for v in self.variables:
            if v[0]=='f':
                # Add to the flow rate sum of the odor channels
                # so the clean MFC can deliver the balance
                if (v == 'fMFC_A_High'):
                    values[v] = values[v]  * 1000
                if (v == 'fMFC_B_Low'):
                    values[v] = values[v]  * 10
                values[v] *= pq.cc/pq.min
                mixing_sum += values[v]
            else:
                # Zero minor components since the valves can't handle these                    
                values[v] = 0 if values[v] < 0.001 else values[v]
                if 'MFC_B' in v:
                    # Convert the B valves from 'fraction of time remaining'
                    # to 'absolute fraction'
                    values[v] *= (1-values[v.replace('B_Low', 'A_High')])
        # The flow rate for the clean MFC (the rest of the target flow rate)
        values['MFC_Carrier'] = target_outflow_rate_ccm - mixing_sum
        # print(f"\nequipment.optimize() - Values of MFC Carrier {values}")
        self.olfactometer_schedule = values
        self.least_squares_result = least_squares_result                    


    def kdtree_lookup(self, target_dense, mfc_names, F):
        concentration_list = np.array([float(c.rescale(pq.M)) for m,c in target_dense.items()])
        print("CONC LIST" + str(concentration_list))
        distance,index = self.kdtree.query(list(concentration_list))
        machine_config = self.smell_data_frame.index[index]
        #print(f"Index used:{index}, distance:{distance}, data return frame value:{machine_config}")
        # Initialize variables list
        self.variables = ['w%d%s'%(j,mfc) for mfc in mfc_names for j in self.olfactometer.jars]
        self.variables += ['f%s'%mfc for mfc in mfc_names]
        # Convert list into dict and populate with values from lookup table
        entry_results = list(machine_config)[2:]
        entry_results += list(machine_config)[0:2]
        # NOTE: Check for empty usage of MFC when generating Dataframe
        if (entry_results[20] == 0):    # For A
            for i in range(10):     entry_results[i] = 0
        if (entry_results[21] == 0):    # For B 
            for i in range(10):     entry_results[i+10] = 0   

        values = {self.variables[i]: value
                for i, value in enumerate(entry_results)} 
        mixing_sum = 0 * pq.cc/pq.min
        for v in self.variables:
            if v[0]=='f':
                # Add to flow rate sum for odor channels so clean MFC delivers balance
                if (v == 'fMFC_A_High'):    values[v] = values[v]  * 1000
                if (v == 'fMFC_B_Low'):     values[v] = values[v]  * 10
                values[v] *= pq.cc/pq.min
                mixing_sum += values[v]
            else:   # Zero minor components since the valves can't handle these                    
                values[v] = 0 if values[v] < 0.001 else values[v]
                if 'MFC_B' in v:    # Convert the B valves from 'fraction of time remaining' to 'absolute fraction'                        
                    values[v] *= (1-values[v.replace('B_Low', 'A_High')])            
        values['MFC_Carrier'] = F - mixing_sum  # The flow rate for the clean MFC (the rest of the target flow rate)            
        self.olfactometer_schedule = values # Call setter to invoke logical.issue_odorants()            

    def optimization_report(self):
        """Report on optimization quality"""
        print("\nValues:")
        # print(self.olfactometer_schedule)
        #print("\nError is %.2g" % self.least_squares_result.cost)        
        # Check that a configuration with these values will produce
        # the desired vapor concentration of each molecule
        print("\nVerifying...")
        v = self.olfactometer_schedule
        mixing_mfcs = self.olfactometer.mfcs[0] # The other one (at index 1) is the carrier MFC
        mfc_names = [mfc.label for mfc in mixing_mfcs]
        n_jars = len(self.olfactometer.jars)
        
        wA = np.array([v['w%d%s' % (i, mfc_names[0])] for i in range(1, n_jars+1)])
        wB = np.array([v['w%d%s' % (i, mfc_names[1])] for i in range(1, n_jars+1)])
        target_molecules = set(list(self.target_outflow_concs))
        J = self.get_vapor_concs_dense(target_molecules)
        if (wA.sum() == 0): wA[0] = 1
        if (wB.sum() == 0): wB[0] = 1
        self.vapor_phase_concentrationschieved = (v['fMFC_A_High']*(np.dot(J*pq.M, wA))/wA.sum() + \
                    v['fMFC_B_Low']*(np.dot(J*pq.M, wB))/wB.sum())/v['MFC_Carrier']
        
        # Create a list of all molecules available in the olfactometer
        # and their desired outflow concentrations (including zeros)
        target_dense = OrderedDict([(m,(self.target_outflow_concs[m] if m in self.target_outflow_concs else 0*pq.M))
                                     for m in self.olfactometer.loaded_molecules])
        report = pd.DataFrame(index=target_molecules, columns=['Target', 'Achieved', '% Error'])
        for i, m in enumerate(target_molecules):
            a = target_dense[m] * pq.M 
            b = self.vapor_phase_concentrationschieved[i]
            if (a != 0):    error_report = (100*(b-a)/a).magnitude
            else:           error_report = 0
            report.loc[m] = ['%.5g' % a, '%.5g' % b, '%.3g' % error_report]
        print("Completed verification.")
        print(report)
        return report
                            
    @property
    def outflow_rates(self):
        flows = np.array([mfc.flow_rate.rescale(self.flow_units) for mfc in self.olfactometer.mfcs])
        return flows*self.flow_units
       
    @property
    def outflow_fractions(self):
        x = self.outflow_rates
        return x/x.sum()

    def update_target_from_logical(self):
        if (self.valve_driver.mixtures is None):
            print("Error, mixture dequeue not initialized")
        else:
            self.target_outflow_concs = {self.cid_to_molecule(\
                                            self.valve_driver.cids[i]): conc
                                        for i, conc
                                        in enumerate(self.valve_driver.mixtures[-1])}
                

@jit
def calc_conc_jit(variables, n_jars, max_flow_rates, A):
    wA = variables[2:12]        # first 2 are MFCs, proceeding 10 are wAs
    wB = variables[12:22]
    fA = variables[0]
    fB = variables[1]
    fA = fA * max_flow_rates[0]
    fB = fB * max_flow_rates[1] 
    # Pre-compute sums for efficiency
    wAs = 0
    wBs = 0
    for x in range(len(wA)):
        if (wA[x] > 0):
            wAs += 1
        if (wB[x] > 0):
            wBs += 1
    # wAs = wA.sum() 
    # wBs = wB.sum()                         
    # Flux is equal to flow rates * valve occupancy times

    flux = [fA*wA[i]/wAs + fB*wB[i]/wBs for i in range(n_jars)]
    
    # # If a valve is in use, ensure the balance is included in flux calculation by subtracting 1-wA[i] or wB[i]
    # flux = []
    # for i in range(n_jars):    
    #     if (wA[i] > 0):
    #         flux.append(fA*wA[i]/(wAs+(1-wA[i])) + fB*wB[i]/wBs)
    #     elif (wB[i] > 0):
    #         flux.append(fA*wA[i]/wAs + fB*wB[i]/(wBs+(1-wB[i])))
    #     else:
    #         flux.append(fA*wA[i]/wAs + fB*wB[i]/wBs)
    # concentration = gas phase concentrations of jar odorants * flux of airflow going through valves
    concentrations = A * np.array(flux)
    return concentrations
