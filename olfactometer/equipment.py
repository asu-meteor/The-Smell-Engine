from functools import lru_cache
import math
from numba import jit
from pprint import pprint
import numpy as np
import pandas as pd
import quantities as pq
from olfactometer.odorants import Molecule, GAS_MOLAR_DENSITY, fix_concs




class Olfactometer:
    """The whole olfactometer"""
    def __init__(self, jars, mfcs, data_container=None):
        """
        manifold: An equipment.Manifold instance
        jars: A dict of (station: odorant.Jar) mappings
        """                       
        self.connect_jars(jars)
        self.mfcs = mfcs               
        self._loaded_cids = {}                        
        
    mfcs = None
    host = None
    flow_units = pq.cc/pq.min
    
    def add_valve(self, valve, station):
        self.valves[station] = valve
        # self._connect_valve('%dB' % station, valve, 'B')

    def connect_jars(self, jars):
        if isinstance(jars, list):
            jars = {i+1: jar for i, jar in enumerate(jars)}
        self.jars = jars   
    
    def mfc_flat_list(self, mfcs=None):
        if mfcs is None:
            mfcs = self.mfcs
        flat = []
        for mfc_or_list in mfcs:
            if isinstance(mfc_or_list, MFC):
                flat.append(mfc_or_list)
            else:
                flat += self.mfc_flat_list(mfc_or_list)
        return flat

    # Search through manifold jars by odorant id.
    def find_odorant_id_by_index(self, m_index):
        return self.loaded_molecules[m_index]
    
    
    @property
    def loaded_molecules(self):
        """Provide a list of molecules loaded into this olfactometer"""
        res = [] #set()
        for jar in self.jars.values():
            for molecule in jar.contents.molecules:
                if molecule.vapor_pressure:
                    res.append(molecule)
                    # print(f"Molecule:{molecule}")
                    # if (molecule.cid not in self._loaded_cids):
                        # self._loaded_cids[molecule.cid] = molecule            
        # print("loaded_molecules", list(result))
        results = []
        [results.append(x) for x in res if x not in results]
        return results

    def cid_to_molecule(self, cid):
        try:            
            return self._loaded_cids[cid]
        except AttributeError:            
            for m in self.loaded_molecules:
                if m.cid == cid:
                    self._loaded_cids[cid] = m
                    return m
        raise Exception("CID %d not in loaded molecules" % cid)


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

class Pneumatic:
    """Base class for pneumatic components"""
    def __init__(self, label):
        self.label = label
        self.openings = []        
        self.internal_connections = []
        
    # A label to describe this instance
    label = None
    positions = None  # The available positions    
    position = None  # The current position        
    routes = None

    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__, self.label)


class Jar:
    def __init__(self, label):
        self.liquid_volume = 0 * pq.mL        
    vendor = None
    height = 0 * pq.cm
    diameter = 0 * pq.cm
    # A single odorants.Mixture object
    mixture = None
    liquid_volume = None
    _contents = None

    @property
    def contents(self):
        return self._contents
    
    @contents.setter
    def contents(self, contents):
        self._contents = contents
        # Clear all pre-computed values once contents of jar change        
    
    @property
    def density(self):
        return self.contents.density

    def fill(self, mixture_or_odorant, volume):
        if self.liquid_volume > 0:
            raise Exception(
                "Jar must be emptied and washed before it can be filled")
        self.liquid_volume += volume
        self.contents = mixture_or_odorant

    @property
    def max_volume(self):
        return self.area * self.height

    @property
    def area(self):
        return math.pi * (self.diameter/2)**2

    @property
    def max_evaporation_rates(self):
        """Rates of evaporation if vapor is cleared (e.g. by strong air flow)
        This is just the max evaporation rate for each molecule times its mole
        fraction in the solution"""
        return {m: m.molar_evaporation_rate*mole_fraction*self.area.simplified
                for m, mole_fraction in self.contents.mole_fractions.items()}

    @property
    def max_vapor_flow_rates(self):
        evap_rates = self.max_evaporation_rates
        result = {molecule: evap_rate/GAS_MOLAR_DENSITY
                  for molecule, evap_rate in evap_rates.items()}
        return result

    @property
    def molarities(self):
        return {m: moles/self.liquid_volume for m, moles in self.contents.molecules.items()}
    
    @property    
    def vapor_fractions(self):
        return self.contents.vapor_fractions
    
    @property
    @lru_cache(maxsize=16)
    def vapor_concs(self):
        return self.contents.vapor_concentrations
    
    @property
    def vapor_molecules(self):
        return list(self.vapor_concs.keys())
  

class MFC(Pneumatic):
    max_flow_rate = 0 * pq.L / pq.min
    _flow_rate = 0 * pq.L / pq.min
    voltage = 0 * pq.V
    voltage_min = 0 * pq.V
    voltage_max = 5 * pq.V
    ao_channel = None
    
    @property
    def flow_rate_uncertainty(self):
        return 0

    @property
    def flow_rate(self):
        return self._flow_rate
    
    @flow_rate.setter
    def flow_rate(self, flow_rate):
        self._flow_rate = flow_rate
        self.voltage = self.voltage_min + \
                       self.voltage_range*self.rel_flow_rate
    @property
    def voltage_range(self):
        return self.voltage_max - self.voltage_min

    def flow_rate_to_voltage(self, flow_rate):
        return self.voltage_min + \
               self.voltage_range*flow_rate/self.max_flow_rate

    def __repr__(self):
        return '%s (%s)' % (super().__repr__(), self.max_flow_rate)


class Opening:
    def __init__(self, host, label):
        self.host = host
        self.label = label
        self.connections = []

    # The object with the opening
    host = None
    # Up to two connections made by the opening
    connections = None
    # A label to describe the opening
    label = ''
    # The diameter of the opening
    diameter = 0 * pq.cm

    pressure = 0 * pq.psi
    velocity = 0 * pq.m/pq.s

    @property
    def area(self):
        return math.pi * (self.diameter/2)**2

    @property
    def volume_flow_rate(self):
        return self.area * self.velocity

    @property
    def mass_flow_rate(self):
        return self.density * self.area * self.velocity

    @property
    def density(self):
        return self.host.density

    def __repr__(self):
        return 'Opening: %s on %s' % (self.label, self.host)

    def __gt__(self, other):
        return self.label > other.label


def get_unique_tuples(x):
    """Get unique 2-tuples, ignoring order, from the list `x`."""
    unique_tuples = \
        list(frozenset([tuple(sorted((o1, o2))) for o1 in x
                        for o2 in x if o1 is not o2]))
    return unique_tuples


def host_class_names(node):
    return [x.__name__ for x in node.host.__class__.__mro__]
