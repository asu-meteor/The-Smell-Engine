import pandas as pd
from scipy.spatial import KDTree
import sys

class OdorTableLookup: 
    def __init__(self,data_frame=pd.DataFrame(),split_num = 0):
        #Check for construction errors
        '''
        if(data_frame.empty and kdtrees == None):
            raise ValueError('Constructor requires data_frame or kdtree object')
        elif(not data_frame.empty and kdtrees != None):
            raise ValueError('Constructor requires data_frame or kdtree object not both') '''

        try: 
            if(data_frame == None):
                data_frame = pd.DataFrame()
        except: 
            pass

        self.split_num = split_num
        self.kdtrees = []
        sys.setrecursionlimit(500000)

        if(not data_frame.empty):
            self.data_frame = data_frame
            if (split_num > 0):
                for i in range(1,self.split_num+1):
                    _data = self.data_frame.iloc[(self.data_frame.shape[0]//self.split_num)*(i -1):(self.data_frame.shape[0]//self.split_num)*(i),:]
                    print(f"Calculation KDTree {i} out of {self.split_num}")
                    _kdtree = KDTree(_data.values)
                    self.kdtrees.append(_kdtree)
            else:
                _data = self.data_frame
                # print(f"Calculation KDTree {i} out of {self.split_num}")
                _kdtree = KDTree(_data.values)
                self.kdtrees.append(_kdtree)

    def query(self,target):
        distance = float('inf')
        index = 0
        for idx, tree in enumerate(self.kdtrees):
            _distance, _index = tree.query(target)
            if(_distance < distance):
                index = _index 
                distance = _distance 
        return distance, (idx,index)

    def get_index(self,index):
        # i = index[0]
        # i2 = index[1]
        # _data = self.data_frame.iloc[(self.data_frame.shape[0]//self.split_num)*(i -1):(self.data_frame.shape[0]//self.split_num)*(i),:]
        return self.data_frame.index[index]