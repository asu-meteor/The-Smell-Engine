import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

class plotter(): 

    def __init__(self,numOdorants, numValves):
        matplotlib.use('TkAgg')
        plt.ion()
        self.fig = plt.figure()
        gs = gridspec.GridSpec(2, 2)

        self.odLine = self.fig.add_subplot(gs[0,0]) 
        self.odLineLables = [(f"Concentration {i}") for i in range(0,numOdorants)]
        self.odLineLines = []
        self.odLineInit(self.odLine)
        
        self.mfcLine = self.fig.add_subplot(gs[0,1]) 
        self.mfcLineLables = ["MFC 1", "MFC 2", "MFC 3"]
        self.mfcLineLines = []
        self.mfcLineInit(self.mfcLine)

        self.digValve = self.fig.add_subplot(gs[1,0])
        self.digValueLables = [(f"{i}") for i in range(0,numValves)]
        self.digValueBars = []
        self.digValueInit(self.digValve)

    def odLineInit(self,figure):
        #inital values 
        y = [0,1]
        x = [0,1]
        for name in (self.odLineLables):
            self.odLineLines.append(figure.plot(x,y, label=name))

        figure.legend()
        figure.set_title("Odorant Concentrations")
        figure.set_ylabel("Concentration Strength in mds")
        figure.set_xlabel("Time (seconds)")

    def odLineUpdate(self,data):
        # data is of the form [(x,y),(x,y)]
        for idx, (x,y) in enumerate(data):
            if(idx< len(self.odLineLables)):
                self.odLineLines[0][idx].set_data(x,y) 


    def mfcLineInit(self,figure):
        #inital values 
        y = [0,1]
        x = [0,1]
        for name in (self.mfcLineLables):
            self.mfcLineLines.append(figure.plot(x,y, label=name))

        figure.legend()
        figure.set_title("MFC Analog Setpoints")
        figure.set_ylabel("Analog Voltage Setpoint")
        figure.set_xlabel("Time (seconds)")


    def mfcLineUpdate(self,data):
        # data is of the form [(x,y),(x,y)]
        for idx, (x,y) in enumerate(data):
            if(idx< len(self.mfcLineLables)):
                self.mfcLineLines[0][idx].set_data(x,y) 

    def digValueInit(self,figure):

        #Intial Values
        high_means = [1]
        low_means = [.5]
        off_means = [.25]

        #Graph Characteristics
        width = 0.35 
        vHigh = figure.bar(self.digValueLables, high_means, width, label='Valve High')
        vLow = figure.bar(self.digValueLables, low_means, width, label='Valve Low')
        vOff = figure.bar(self.digValueLables, off_means, width, label='Valve Off')
        self.digValueBars = [vHigh,vLow,vOff]

        figure.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        figure.set_title("Digital Valve States")
        figure.set_ylabel("Time(ms)[0,1]") 

    def digValueUpdate(self,value):
        #Value assumed to be array of the form [[High],[Low],[Off]]
        #len([High]) = len(self.digValueLables)

        for i in range(0,len(self.digValueLables)):
            self.digValueBars[0][i].set_height(value[0][i])
            self.digValueBars[1][i].set_height(value[1][i])
            self.digValueBars[2][i].set_height(value[2][i])

    def draw(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


def main():
    plotterC = plotter(26,26)
    while True:
        plotterC.draw()
        plotterC.digValueUpdate([np.random.rand(26),np.random.rand(26),np.random.rand(26)])
        plotterC.odLineUpdate([(np.random.rand(10),np.random.rand(10))])
        plotterC.mfcLineUpdate([(np.random.rand(10),np.random.rand(10))])

if __name__ == "__main__":
    main()