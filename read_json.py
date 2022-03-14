import os
import numpy as np
import json
from collections import OrderedDict

samples = OrderedDict()



def myprint(d):
    for k, v in d.items():
        if isinstance(v, dict):
            myprint(v)
        else:
            print("{0} : {1}".format(k, v))

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
                        print(str(val[0])) 
                        samples[str(res)] = val[0]
                        # samples[list(v['target_concentration'])[0]] = [v['average']]                        
                myparse(el)

file_path = 'data/notebookssmell_engine_data.json'
with open(file_path) as f:
    data = json.loads(f.read())
    myparse(data)


# myprint(samples)
# print(json.dumps(samples, indent = 4, sort_keys=True))
# with open(os.getcwd() + 'limonene.json', 'w') as json_file:
#     json.dump(samples, json_file)