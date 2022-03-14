"""Classes for odorants, mixtures, chemical orders, etc."""

from datetime import datetime
import json
import random
import re
import urllib.request
from urllib.request import urlopen
from urllib.error import HTTPError
import quantities as pq

from olfactometer.physics import mackay

ROOM_TEMP = 22 * pq.Celsius
GAS_MOLAR_DENSITY = pq.mol / (22.4 * pq.L)


class Solution:
    def __init__(self, components, date_created=None):
        self.total_volume = 0 * pq.mL
        assert isinstance(components, dict), "Components must be a dict"
        for component, volume in components.items():
            assert isinstance(component, (Compound, Solution)), \
                "Each component must be a Compound or a Solution"
            try:
                volume = volume.rescale(pq.mL)
            except ValueError:
                raise ValueError("Components must be provided with volumes")
            self.total_volume += volume  # Assume that volume is conserved
        self.components = components
        self.date_created = date_created if date_created else datetime.now()

    @property
    def compounds(self):
        return self._compounds()

    def _compounds(self, result=None):
        if result is None:
            result = {}
        for component, volume in self.components.items():
            if isinstance(component, Compound):
                if component in result:
                    result[component] += volume
                else:
                    result[component] = volume
            else:  # If it is a Solution
                component._compounds(result=result)
        return result

    @property
    def molecules(self):
        """Returns a dictionary with the moles of each Molecule"""
        compounds = self.compounds
        assert all([c.density for c, v in compounds.items() if v
                    and not c.is_solvent]), \
            ("All non-solvent compounds must have a known density "
             "in order to compute moles")
        assert all([c.molecular_weight for c, v in compounds.items() if v
                    and not c.is_solvent]), \
            ("All non-solvent compounds must have a known molecular weight "
             "in order to compute moles")
        return {c.molecule: (v * c.molarity).rescale(pq.mol)
                for c, v in self.compounds.items() if v}

    @property
    def molarities(self):
        """Returns a dictionary with the molarity of each Molecule"""
        return {m: mol/self.total_volume
                for m, mol in self.molecules.items() if mol}

    @property
    def mole_fractions(self):
        """Returns a dictionary with the mole fraction of each Molecule"""
        molecules = self.molecules
        assert([moles for molecule, moles in molecules.items()]), \
            ("All compounds must have a known number of moles "
             "in order to compute mole fraction")
        # A Quantities bug prevents me from simply summing molecules.values()
        total_moles = 0 * pq.mol
        for moles in molecules.values():
            total_moles += moles
        return {molecule: moles/total_moles
                for molecule, moles in molecules.items()}

    def mole_fraction(self, molecule):
        return self.mole_fractions[molecule] \
               if molecule in self.mole_fractions else 0

    @property
    def dilutions(self):
        return {c.molecule: self.total_volume/c.volume
                for c in self.compounds if not c.is_solvent}

    @property
    def partial_pressures(self):
        """Computes partial pressures for each odorant
        in the mixture using Raoult's law"""
        return {m: self.mole_fraction(m)*m.vapor_pressure
                for m in self.molecules if m.vapor_pressure}

    def partial_pressure(self, molecule):
        return self.partial_pressures[molecule]

    @property
    def total_pressure(self):
        """Computes total pressure of the vapor using Dalton's law"""
        partial_pressures = self.partial_pressures.values()
        return sum(partial_pressures)

    @property
    def vapor_fractions(self):
        """Fractions of each component in the vapor phase at steady state.
        Units are fraction of volume. Air is assumed to make up the balance"""
        pp = self.partial_pressures
        result = {}
        for m, _ in pp.items():
            ratio = (pp[m]/pq.atm).simplified
            assert ratio.units == pq.dimensionless
            result[m] = float(ratio)
        return result
    
    @property
    def vapor_concentrations(self):
        """Concentrations of each component in the vapor headspace"""
        return {m: v*GAS_MOLAR_DENSITY for m, v in self.vapor_fractions.items()}
            
    def vapor_fraction(self, molecule):
        return self.vapor_concentrations[molecule]
    
    def vapor_concentration(self, molecule):
        return self.vapor_fractions[molecule]

    @property
    def molar_evaporation_rates(self):
        mf = self.mole_fractions
        result = {molecule: mole_fraction*molecule.molar_evaporation_rate
                  for molecule, mole_fraction in mf.items()}
        return result


class Compound:
    def __init__(self, chemical_order, stock='',
                 date_arrived=None, date_opened=None, is_solvent=False):
        self.chemical_order = chemical_order
        self.date_arrived = date_arrived if date_arrived else datetime.now
        self.date_opened = date_opened
        self.is_solvent = is_solvent

    # ChemicalOrder
    chemical_order = None
    # Stock number (supplied by vendor, usually on bottle)
    stock = ''
    # Date arrived at the lab/clinic
    date_arrived = None
    # Date opened
    date_opened = None
    # Is it a solvent?
    is_solvent = False

    def __getattr__(self, attr):
        """If no attribute is found, try looking up on the
        ChemicalOrder or the Molecule"""
        try:
            return getattr(self.chemical_order, attr)
        except AttributeError:
            return getattr(self.chemical_order.molecule, attr)


class ChemicalOrder:
    def __init__(self, molecule, vendor, part_id,
                 purity=1, known_impurities=None):
        self.molecule = molecule
        self.vendor = vendor
        self.part_id = part_id
        self.purity = purity
        self.known_impurities = known_impurities

    # Molecule
    molecule = None
    # Vendor, e.g. Sigma-Aldrich
    vendor = None
    # ID number of compound at vendor
    part_id = ''
    # Reported purity as a fraction
    purity = 1
    # List of known impurities (Molecules)
    known_impurities = None


class Vendor:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    name = ''
    url = ''


class Molecule:
    """
        This module extracts various chemical and physical properties of odorous molecular compounds
        using PUG REST API. Portions of the codebase have benefitted from work by Maxim Shevelev <mdshev7@gmail.com>

        For details about PubChem's PUG REST API please visit
        https://pubchem.ncbi.nlm.nih.gov/pug_rest/PUG_REST.html
    """
    def __init__(self, cid=None, name=None, fill=False, vapor_press=None, dens=None):        
        self.name = name        
        if (cid is None):   self.cid = self.get_cid_by_name(name)
        else:               self.cid = cid        
        # Molecular weight (pq.g / pq.mol)
        self.molecular_weight = None
        if fill:            self.fill_details()
        # Vapor pressure (pq.Pa)    
        if (vapor_press is None):   self.vapor_pressure = float(self.get_vapor_pressure())
        else:                       self.vapor_pressure = vapor_press
        # Density (pq.g / pq.ml)
        if (dens is None):          self.density = float(self.get_density())
        else:                       self.density = dens
    
    # Integer Chemical ID number (CID) from PubChem
    # cid = 0
    # Chemical Abstract Service (CAS) number
    cas = ''
    # Principal name
    # name = ''
    # Synonyms
    synonyms = ''
    # IUPAC name (long, unique name)
    iupac = ''            

    @property
    def molarity(self):
        if not self.molecular_weight:
            result = None
        else:
            result = self.density / self.molecular_weight
            result = result.rescale(pq.mol / pq.L)
        return result

    @property
    def molar_evaporation_rate(self):
        return mackay(self.vapor_pressure)

    def fill_details(self):
        """
        Populate odorant molecule properties to include molecular weight and cid/name.
        """
        assert self.cid is not None
        self.cid = int(self.cid) # Fixed duplication error in order dict 
        url_template = ("https://pubchem.ncbi.nlm.nih.gov/"
                        "rest/pug/compound/cid/%d/property/"
                        "%s/JSON")
        property_list = ['MolecularWeight', 'IsomericSMILES']
        url = url_template % (self.cid, ','.join(property_list))
        json_data = self.url_to_json(url)
        details = json_data['PropertyTable']['Properties'][0]
        def convert(name):
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        for key, value in details.items():
            if key == 'CID':
                assert value == self.cid, \
                    "REST API CID does not match provided CID"
            key = convert(key)
            if key == 'molecular_weight':
                value = float(value)
                # print(f"value: {value.dtype}")
                value *= pq.g / pq.mol
            setattr(self, key, value)
        if not self.name or self.name == None:
            self.name = self.get_name_from_api()
    

    def get_name_from_api(self):
        url_template = ("https://pubchem.ncbi.nlm.nih.gov/"
                        "rest/pug/compound/cid/%d/synonyms/JSON")
        url = url_template % (self.cid)
        json_data = self.url_to_json(url)
        name = None
        if json_data:
            information = json_data['InformationList']['Information'][0]
            synonyms = information['Synonym']
            name = synonyms[0].lower()
        return name

    def get_cid_from_api(self):
        """
        Obtain pub chem ID from OM name.
        """
        url_template = ("https://pubchem.ncbi.nlm.nih.gov/"
                        "rest/pug/compound/%s/%s/cids/JSON")
        options = [getattr(self, x) for x in ('cas', 'name')
                   if len(getattr(self, x))]
        cid = None
        query = self.name
        for option in options:
            url = url_template % (option, query)
            json_data = self.url_to_json(url)
        cid = json_data['IdentifierList']['CID'][0]
        return cid

    def pubchem_parsing(self, url):
        """
            Get the link to PubChem API, parse it for JSON and then translate that
            to Python dictionary;
            This is just to follow the DRY principle
        """
        req = urllib.request.Request(url)
        res = urllib.request.urlopen(req).read()
        fin = json.loads(res.decode())
        return fin


    def get_cid_by_name(self, compound_name):
        """
            1. Accepts the compound name
            2. Searches PubChem by this name
            3. Returns the compound's PubChem CID
        """
        # Construct the link to PubChem's PUG REST API
        pubchem_record_link = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/"
        pubchem_record_link += "name/%s/record/JSON" % compound_name
        # Parse the JSON received from PubChem to Python Dictionary
        general_info = self.pubchem_parsing(pubchem_record_link)
        # Get the CID
        cid = general_info['PC_Compounds'][0]['id']['id']['cid']
        return cid

    def get_vapor_pressure(self):
        """
        Obtain odorant molecule Vapor Pressure from PubChem.
        """
        vapor_pressure = self.get_addtional_om_props(['Vapor Pressure'])        
        return vapor_pressure['Vapor Pressure'][0]['Value']['StringWithMarkup'][0]['String'].split()[0]

    def get_density(self):
        """
        Obtain odorant molecule density by searching density property and extra additional properties from PubChem.
        """
        density = self.get_addtional_om_props(['Density'])           
        if (len(density) == 0):
            density_container = self.get_addtional_om_props(['Other Experimental Properties'])
            parsed_extra_details = density_container['Other Experimental Properties'][1]['Value']['StringWithMarkup'][0]['String'].split()
            for x in range(len(parsed_extra_details)):  # Density value comes after density property
                if (parsed_extra_details[x] == 'density:'):                    
                    return parsed_extra_details[x+1]
        else:
            # print(f"Density {density}")
            return density['Density'][0]['Value']['StringWithMarkup'][0]['String'].split()[0]        
        if (density is None or len(density) == 0):   # If density is still None after parsing experimental properties, return 1.
            return 1

    def get_addtional_om_props(self, required_properties):
        """
            Found method as courtesy of Maxim Shevelev (Github: @mawansui)
            1. Accepts the compound name
            2. Gets the CID for this compound
            3. Searches PubChem for data for the specified CID
            4. Cycles through the fetched data to select required fields
            5. Returns a dictionary with specified properties of specified compound
        """
        # Contsruct the link
        pubchem_all_data_link = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/"
        pubchem_all_data_link += "data/compound/%s/JSON" % self.cid
        # Get the JSON from the constructed link and convert it to Python Dictionary
        all_the_data = self.pubchem_parsing(pubchem_all_data_link)

        # Get to the data sections, get rid of References
        data_sections = all_the_data['Record']['Section']

        """
            Out of all the sections

            (2D structure, 3D conformer, LCSS, Names and Idenrifers, Chemical and 
            Physical Properties, Related Records, Chemical Vendors, Food additives, 
            Agrochemical Info, Pharmacology and Biochemistry, Use and Manufacturing,
            Identification, Safety and Hazards, Toxicity, Literature, Patents, 
            Biomolecular Interactions, Biological Tests Result, Classification)

            choose only the most chemically interesting ones: 

            <Names and Identifies> and <Chemical and Physical Properties>
        """

        # this could be customizable, actually - please send PR or raise an issue
        # if you'd like to have this done
        sections_of_interests = ['Names and Identifiers',
                                'Chemical and Physical Properties']

        # Empty array to store all the data of the sections of interes
        sections_of_interests_data = []

        # the required parameters can be accesed via
        # dictionary in the array => Section => TOCHeading == 'parameter name' =>
        # => Information

        # Construct an array of only interesting data
        for section_title in sections_of_interests:
            sample_list = list(filter(lambda section: section['TOCHeading'] == section_title, data_sections))
            sections_of_interests_data.append(sample_list[0])

        # However, we are still away from getting the parameters values
        # The sections_of_interests_data contains lots of interesting information,
        # however it is not that useful for the chemist's everyday usage,
        # so I limit the data we can get to 3 identifiers listed below:

        required_identifiers = ['Computed Descriptors',
                                'Other Identifiers',
                                'Experimental Properties']

        # The data for each identifier (stated above) will be stored in this array
        # To get the parameters for these identifiers one will have to look for
        # dictionary => 'Section' array, which will yield yet another array,
        # but this time it will be full of parameters one can grab
        all_pubchem_data_array_for_section = []

        # if section_dictionary['Section'] contains a dictionary with
        # 'TOCHeading' equaling to anything from required_identifiers,
        # add the matching dictionary into the new array initialized above
        for section_dictionary in sections_of_interests_data:
            sample_list = list(
                filter(lambda section: section['TOCHeading'] in required_identifiers, section_dictionary['Section']))
            all_pubchem_data_array_for_section = all_pubchem_data_array_for_section + sample_list

        # it's not full, though, you can also extract more data from PubChem
        # but I've just found these parameters to be of the most interest
        # for a chemist's everyday use
        list_of_all_possible_params = ['IUPAC Name',
                                    'Canonical SMILES',
                                    'Wikipedia',
                                    'Boiling Point',
                                    'Melting Point',
                                    'Flash Point',
                                    'Solubility',
                                    'Density',
                                    'Vapor Density',
                                    'Vapor Pressure',
                                    'LogP',
                                    'Stability',
                                    'Auto-Ignition',
                                    'Viscosity',
                                    'Heat of Combustion',
                                    'Heat of Vaporization',                                   
                                    'Ionization Potential',
                                    'Dissociation Constants',
                                    'Other Experimental Properties']

        # this array will later store the data about requested parameters
        # in the PubChem format
        required_data_in_pubchem_format = []
        for molecule_desc_object in all_pubchem_data_array_for_section:
            sample_list = list(
                filter(lambda section: section['TOCHeading'] in required_properties, molecule_desc_object['Section']))
            required_data_in_pubchem_format = required_data_in_pubchem_format + sample_list

        # Final dictionary of compound properties that will be returned in the end
        compound_properties_dictionary = {}
        for property_object in required_data_in_pubchem_format:
            compound_properties_dictionary[property_object['TOCHeading']] = property_object['Information']
        return compound_properties_dictionary

    def url_to_json(self, url):
        json_data = None
        msgs = []
        try:
            page = urlopen(url)
            string = page.read().decode('utf-8')
            json_data = json.loads(string)
        except HTTPError:
            msgs.append("HTTPError for query '%s'" % url)
        if json_data is None:
            for msg in msgs:
                print(msg)
        return json_data

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
    
    def __lt__(self, other):
        return self.__hash__() < other.__hash__()

    def __hash__(self):
        if self.cid:
            return self.cid
        elif self.name:
            return hash(self.name)
        else:
            return random.randint(0, 1e24) 

    def __repr__(self):
        if self.cid and self.name:
            result = '%d (%s)' % (self.cid, self.name)
        elif self.cid:
            result = '%d' % self.cid
        elif self.name:
            result = '%s' % self.name
        else:
            result = 'Unknown'
        return result


def fix_concs(molecules_concs):
        assert isinstance(molecules_concs, dict)
        assert all([isinstance(m, Molecule)
                   for m in molecules_concs.keys()])
        assert all([isinstance(conc, pq.Quantity)
                    for conc in molecules_concs.values()])
        molecules_concs = {m: conc.rescale(pq.M)
                           for m, conc in molecules_concs.items()}
        return molecules_concs

    
if __name__ == '__main__':
    x = Molecule(325, fill=True)
    print(x.__dict__)

    
