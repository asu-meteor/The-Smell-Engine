import os
import numpy as np
import json
from collections import OrderedDict

samples = OrderedDict()


def append_value(m_dict, key, value):
    # Check if key exist in dict or not
    if key in m_dict:
        # Key exist in dict.
        # Check if type of value of key is list or not
        if not isinstance(m_dict[key], list):
            # If type is not list then make it list
            m_dict[key] = [m_dict[key]]
        # Append the value in list
        m_dict[key].append(value)
    else:
        # As key is not in dict,
        # so, add key-value pair
        m_dict[key] = [value]

def average_pid_per_concentration(m_dict):
    for k, v in m_dict.items():
        if isinstance(v, list):
            v_sum = 0
            for el in v:
                v_sum += float(el[0])
            v_sum /= len(v)
            m_dict[k] = v_sum

def myprint(d):
    for k, v in d.items():
        if isinstance(v, dict):
            myprint(v)
        else:
            # print("{0} : {1}".format(k, v))
            # print("{0}".format(k))
            print("{0}".format(v))

def myparse(d):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict):
                myparse(v)
            elif isinstance(v, list):
                myparse(v)            
    elif isinstance(d, list):
        for el in d:
            if isinstance(el, dict):
                for k, v in el.items():
                    if (k == "PID_sensor_reading"):
                        # print(v['target_concentration'])
                        # print(type(v['target_concentration']))
                        res = [float(idx) for idx in v['target_concentration'].strip('][').split(', ')] 
                        val = [float(idx) for idx in v['average'].strip('][').split(', ')] 
                        # print(str(res[0]))
                        # print(str(val[0]))  
                        # samples[str(res[1])] = val[0]
                        append_value(samples, str(res[0]), [v['average']])
                        # samples[str(res[0])] = [v['average']]                        
                        # print(list(v['target_concentration'])[0])
                        # print(v['average'])
                myparse(el)


file_path = '../notebookssmell_engine_data.json'
with open(file_path) as f:
    data = json.loads(f.read())
    myparse(data)
    average_pid_per_concentration(samples)
    myprint(samples)


# print(json.dumps(samples, indent = 4, sort_keys=True))
# with open(os.getcwd() + 'carvone.json', 'w') as json_file:
#     json.dump(samples, json_file)