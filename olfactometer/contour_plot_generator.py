import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.colors as colors
from collections import OrderedDict
import random
from matplotlib import cm
import matplotlib.collections as mcoll
import matplotlib.path as mpath
import quantities as pq
from matplotlib.tri import Triangulation
import os
import copy

n_jars = 10
total_vapor = [5.7743e-09, 5.7743e-09, 0.0000e+00, 0.0000e+00, 0.0000e+00,
        0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00]
num_steps = 50 # step size of 0.01
variables_names = ['w1MFC_A_High (s)', 'w2MFC_A_High (s)', 'w3MFC_A_High (s)', 'w4MFC_A_High (s)', 'w5MFC_A_High (s)', 'w6MFC_A_High (s)', 'w7MFC_A_High (s)', 'w8MFC_A_High (s)', 'w9MFC_A_High (s)', 'w10MFC_A_High (s)', 'w1MFC_B_Low (s)', 'w2MFC_B_Low (s)', 'w3MFC_B_Low (s)', 'w4MFC_B_Low (s)', 'w5MFC_B_Low (s)', 'w6MFC_B_Low (s)', 'w7MFC_B_Low (s)', 'w8MFC_B_Low (s)', 'w9MFC_B_Low (s)', 'w10MFC_B_Low (s)', 'fMFC_A_High (cc per min)', 'fMFC_B_Low (cc per min)']

class plotterDim():

    # Data is a multi-dimentional array of the form [(Name,[1,2,3]),(Name,[1,2,3]),(Name,[1,2,3])]
    # Each sub array must have the same number of values
    def __init__(self,saveData=False, saveRootPath="./"):
        self.data = [(0,0) for i in range(22)]
        self.saveData = saveData 
        self.saveRootPath = saveRootPath
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(111)
        self.m_dict = OrderedDict()

    def set_data(self):
        self.saveData = True
        for idx, k in enumerate(self.m_dict.keys()):
            # print("Key:{0}, Val:{1}, idx:{2}".format(str(k), str(self.m_dict[k]), str(idx)))
            self.data[idx]=(str(k), self.m_dict[k])
        # self.fig = plt.figure()
        self.rowPlot(0)

    def append_value(self, key, value):
        # Check if key exist in dict or not
        if key in self.m_dict:
            # Key exist in dict.
            # Check if type of value of key is list or not
            if not isinstance(self.m_dict[key], list):
                # If type is not list then make it list
                self.m_dict[key] = [self.m_dict[key]]
            # Append the value in list
            self.m_dict[key].append(value)
        else:
            # As key is not in dict,
            # so, add key-value pair
            self.m_dict[key] = [value]

    def graphPair(self,x,y):
        plt.clf()
        xName = str(x[0])
        yName = str(y[0])
        plt.xlabel(xName)
        plt.ylabel(yName)
        plt.title(xName + " vs " +yName)
        self.fig.set_size_inches(18.5, 10.5)
        # print("xlen:{0}, ylen:{1}".format(len(x), len(y)))
        #norm = colors.Normalize(vmin=min(x[1]), vmax= max(x[1]))
        plt.plot(x[1], y[1], marker="*")


        MAP = 'jet'
        #Label Points
        labels = ['x'.format(i) for i in range(len(x[1]))]
        length = len(x[1])
        r = b = g = 0      
        #print(len(x[1]))  
        _jankCOunt = 0
        for i in range(len(x[1])-1):#x, y in zip(x[1], y[1]):
            # print("r:{0}.g:{1},b:{2}".format(str(r), str(g), str(b)))
            if(i%25==0):
                if(r<.9):
                    r = r + .1
                if(r>.9 and b<.9):
                    b = b + .1
                if(b>.9 and g<.9):
                    g = g + .1
                _jankCOunt = _jankCOunt + 1
                cm = plt.get_cmap(MAP)
                self.ax1.set_prop_cycle('color',[cm(1.0*i/(len(x[1])-1)) for i in range(len(x[1])-1)])
                plt.annotate("{0}".format(_jankCOunt), xy=(x[1][i], y[1][i]), xytext=(x[1][i], y[1][i]),color=(r, g, b))
                plt.plot([x[1][i],x[1][i+1]], [y[1][i],y[1][i+1]],color=(r, g, b))
        #Label Points

        if(self.saveData):
            plt.savefig("{0}/{1}vs{2}".format(self.saveRootPath, xName,yName))
            # plt.savefig("./multidimplot",  dpi=100)
        else:
            plt.show()
        
        

    def rowPlot(self,index):
        pivot = self.data[index]
        for idx, data in enumerate(self.data):
            if(idx != index):
                self.graphPair(pivot,data)
        print("DONE")

    

    def residuals(self, variables, x):
        """
        This method is invoked by the non-linear least squares solver.
        wNA: The fraction of time that valve N is in state A
        wNB: The fraction of the remaining time that valve N is in state B
        fA: The flow rate through MFC A
        fB: The flow rate through MFC B
        """
        # print("Variables:\t" + str(variables))
        # Unpack variables
        variables = np.array(variables)
        x = np.array(x)
        wA = variables[:n_jars]
        wB = variables[n_jars:(n_jars*2)]
        fA, fB = variables[(n_jars*2):]

        # Convert fraction-of-remaining time values (w1B, w2B, ...)
        # to absolute fractions
        wB = (1-wA)*wB
        # Convert fa,fb to liters 
        # max_flow_rate_A = 1000 # * pq.L / pq.min
        # max_flow_rate_B = 10.0 # * pq.cc / pq.min
        fA = fA * 999.99
        fB = fB * 10.0
        # print("fa:{0}, fb:{1}".format(str(fA), str(fB)))
        # Pre-compute sums for efficiency
        wAs = wA.sum()
        wBs = wB.sum()
        # print("fa: {0},fb: {1},wA[i]: {2},wA: {3},wB[i]: {4},wB: {5}".format(str(fA), str(fB), str(wA[0]), str(wAs), str(wB[0]), str(wBs)))
        # The residuals whose sum of squares will be minimized
        residuals = [fA*wA[i]/wAs + fB*wB[i]/wBs - x[i] for i in range(n_jars)
                        if total_vapor[i]]

        # for valve_index, valve in enumerate(wA):
        #     append_value("w"+str(valve_index)+"A",valve)
        # for valve_index, valve in enumerate(wB):
        #     append_value("w"+str(valve_index)+"B",valve)
        # append_value('fA',fA)
        # append_value('fB',fB)
        # self.mutlidim_plotting.append_value('w1MFC_A_High',values['w1MFC_A_High'])
        # print("Len of res:\t{0}, Res:\t{1}".format(str(len(residuals)), str(residuals)))
        # Try to sparsen the solution by penalizing the valves being open
        #residuals += list(wA*1e-6)
        #residuals += list(wB*1e-6)
        return sum(residuals)

    # def solution_to_
    def generate_contour_points(self,variables_in,index1,index2,desired_conc):
        variables = copy.deepcopy(variables_in)
        x_list = []
        y_list  = []
        z_list = []
        for x in range(0,num_steps):
            for y in range(0,num_steps):
                variables[index1]=float(x/num_steps)
                variables[index2]=float(y/num_steps)
                z_list.append(self.residuals(variables,desired_conc))
                x_list.append(float(x/num_steps))
                y_list.append(float(y/num_steps))
                # print("X {0}, Y {1}".format(x, y))
        return x_list, y_list, z_list

    def graph_contour_points(self,variables,index1,index2,desired_conc,save_fig=False,save_fig_name="1"):
        picked_solution = (variables[index1],variables[index2])
        #print(picked_solution)
        x_list, y_list, z_list = self.generate_contour_points(variables,index1,index2,desired_conc)
        
        tri = Triangulation(x_list,y_list)

        fig2 = plt.figure()
        plt.scatter([picked_solution[0]],[picked_solution[1]])
        plt.annotate("({0},{1})".format(str(round(picked_solution[0],2)),str(round(picked_solution[1],2))), 
        xy=(picked_solution[0], picked_solution[1]-0.05), xytext=(picked_solution[0], picked_solution[1]-0.05),color="black")   
        cp = plt.tricontour(tri, z_list, )
        plt.clabel(cp, cp.levels, inline=True,fontsize=10)
        color_bar = fig2.colorbar(cp)
        color_bar.set_label("Residuals Sum")
        plt.title("RCost of Config for {0} and {1} vs Chosen".format(variables_names[index1],variables_names[index2]))
        plt.xlabel(variables_names[index1])
        plt.ylabel(variables_names[index2])
        #plt.scatter(x,y, c=z)
        if(save_fig):
            plt.savefig(save_fig_name+".jpg")
        else:
            plt.show()
        
    def constants_text(self,variables,index1,index2,desired_conc):
        constants_string ="Constants\n"
        for idx, name in enumerate(variables_names):
            if(idx==index1 or idx == index2):
                constants_string = constants_string + name + " = variable\n"
            else:
                constants_string = constants_string + name + " = " + str(round(variables[idx],3)) +"\n"
        return(constants_string)

    def row_graph_contour_points(self,variables,index,desired_conc,root_path="./",make_path=True):
        if(make_path):
            root_path = root_path+"/"+variables_names[index]+"_graphs/"
            os.mkdir(root_path)
        # for i in range(10,len(variables-2)):            
        for i in range(len(variables)):
            #print(variables)
            if(i!=index):
                self.graph_contour_points(variables,index,i,desired_conc,True,root_path+"{0}vs{1}".format(variables_names[index],variables_names[i]))
                plt.cla()
        '''
        3D Method
        fig2 = plt.figure()
        ax = fig2.add_subplot(111,projection='3d')
        xx, yy = np.meshgrid(range(2), range(2))
        z = xx* 0 

        ax.set_xlabel(name1)
        ax.set_ylabel(name2)
        ax.set_zlabel('Residuals Sum')

        ax.plot_surface(xx, yy, z, alpha=0.5,color="black")
        ax.scatter3D(x_list, y_list, z_list)
        plt.show()
        '''


# dataT = [("W",[1,2,3]),("B",[1,2,3]),("C",[1,2,3])]

# p = plotterDim(dataT,True,"./graphs")
# p.rowPlot(0)