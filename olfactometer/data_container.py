import time
import datetime
import json
import os

class DataContainer:

    def __init__(self):    
        print("Initializing")    
        self.file_text = ""
        self.timestamps = {}
        self.target_concentrations = {}

    def append_value(self, key, value):
        # Check if key exist in dict or not
        if key in self.timestamps:
            # Key exist in dict.
            # Check if type of value of key is list or not
            if not isinstance(self.timestamps[key], list):
                # If type is not list then make it list
                self.timestamps[key] = [self.timestamps[key]]
            # Append the value in list
            self.timestamps[key].append(value)
        else:
            # As key is not in dict,
            # so, add key-value pair
            self.timestamps[key] = value

    def append_target_concentration(self, key, value):
        # Check if key exist in dict or not
        if key in self.target_concentrations:
            # Key exist in dict.
            # Check if type of value of key is list or not
            if not isinstance(self.target_concentrations[key], list):
                # If type is not list then make it list
                self.timestamps[key] = [self.timestamps[key]]
            # Append the value in list
            self.timestamps[key].append(value)
        else:
            # As key is not in dict,
            # so, add key-value pair
            self.timestamps[key] = value

    def create_json(self):
        # data_json = json.dumps(self.timestamps)
        # Pretty Printing JSON string back
        # print(json.dumps(self.timestamps, indent = 4, sort_keys=True))
        with open(os.getcwd() + 'smell_engine_data.json', 'w') as json_file:
            json.dump(self.timestamps, json_file)