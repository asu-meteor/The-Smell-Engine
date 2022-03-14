import ipyvuetify as v
from ipywidgets import jslink
from traitlets import link 
from traitlets import directional_link
import math
import plotly.graph_objects as go
from collections import OrderedDict


class UI: 
    
    def __init__(self, molecules=OrderedDict([(439250, 'l-limonene'), (439570, 'l-carvone'), (440917, 'd-limonene')]), print_PID_average=False):
        # Constants
        self.NUM_JARS = 3
        self.NUM_VALVES = 10
        self.MFC_DATA = [("MFC Main",(0,10),"SLPM"),("MFC A",(0,1),"SLPM"),("MFC B",(0,10),"SCCM")]
        self.MFC_VOLTAGE = (0,5)
        self.CONCENTRATION_MIN_MAX = (-12,0) 
        self.print_PID_avg = print_PID_average

#         self.OdorantsList = ["(+)-carvone", "(-)-carvone", "α-pinene", "linalool", "isoamyl acetate", "benzaldehyde", "eucalyptol"]
        self.OdorantsList = list(molecules.values())
        self.OdorantsMaxCon = []
        
        # Task 1
        self.odorantsSelectorsDropDown = [v.Select(v_model=self.OdorantsList[0],class_ ="ma-2", label=f'Jar {i}', items=self.OdorantsList) for i in range(self.NUM_JARS)]
        
        # Task 2
        self.odorantsConcentrationSlider = [v.Slider(v_model=0,class_="ma-2",max = 0, min =-12,step=.5, hint=f"Odor(μM): {odor}" ,persistent_hint=True) for odor in self.OdorantsList]
        self.odorantsConcentrationsText = [v.TextField(v_model=0, hide_details=True, single_line=True, class_="mt-0 pt-0", style_="width: 80px") for odor in self.OdorantsList]
        self.odorantsConcentrationsSetButton = v.Btn(children=['Step'])
        self.odorantsConcentrationsMinButton = v.Btn(children=['Min'])
        self.odorantsConcentrationsMaxButton = v.Btn(children=['Max'])
        self.odorantsConcentrationsUpdateButton = v.Btn(children=['Update'])
        self.odorantsConcentrationsSetText = v.TextField(v_model=0.5, hide_details=True, single_line=True, style_="width: 100px") 
        self.odorantsConcentrationsMinText = v.TextField(v_model=1e-12, hide_details=True, single_line=True, style_="width: 100px")
        self.odorantsConcentrationsMaxText = v.TextField(v_model=0, hide_details=True, single_line=True, style_="width: 100px")
        
        #Duty Cycle UI
        self.dutyCycleText = [(v.TextField(v_model=0, single_line=True, rules=[True],persistent_hint=True,hint="A", class_="ma-2 pt-0", type='number',style_="width: 60px"),
                             v.TextField(v_model=0, single_line=True, rules=[True],persistent_hint=True,hint="B", class_="ma-2 pt-0", type='number',style_="width: 60px"))for valve in range(self.NUM_VALVES)] 
        self.dutyCycleUpdateBtn=v.Btn(children=['UpDate'])
        #Ocupancy Time UI

        #Duty Cycle UI
        self.ocupancyTimeText = [(v.TextField(v_model=0, single_line=True, rules=[True],persistent_hint=True,hint="A", class_="ma-2 pt-0", type='number',style_="width: 60px"),
                             v.TextField(v_model=0, single_line=True, rules=[True],persistent_hint=True,hint="B", class_="ma-2 pt-0", type='number',style_="width: 60px"))for valve in range(self.NUM_VALVES)] 
        self.ocupancyTimeUpdateBtn=v.Btn(children=['UpDate'])

        #MFC 
        self.mfcText = [(v.Slider(v_model=0, min = RangeV[0],max=RangeV[1],single_line=True,step="0.01", rules=[True], thumb_label="always",persistent_hint=True,hint=f"Flow Rate ({units})", class_="ma-2"),
                             v.TextField(v_model=0, single_line=True, rules=[True],persistent_hint=True, readonly = False, hint="Voltage (V)", class_="ma-2 pt-0",style_="width: 60px"))for (name,RangeV,units) in self.MFC_DATA] 
        self.mfcBtn=v.Btn(children=['UpDate'])
        #Graph 
        self.timeSeries = go.FigureWidget()
        self.timeSeries.layout.title = "Concentration vs Time"
        self.timeSeriesData = []
        self.timeSeries.add_scatter(y=self.timeSeriesData)
        #self.timeSeries.layout.yaxis=yaxis=dict(range=[-1,1])
        
    def getMaxConcentrations(self, smell_engine):
        for j, jar in smell_engine.olf.jars.items():
            print("jar number:\t" + str(j))
            for m, c in jar.vapor_concs.items():
                i = smell_engine.olf.loaded_molecules.index(m)
                c_ = float(c.rescale(pq.M))
                for slider in self.odorantsConcentrationSlider:
                    if(m in slider.hint):
                        self.OdorantsMaxCon.append(c_)
                        slider.max = math.log10(c_)
        
    
    def odorSelectorUI(self):
        sectionTitle = "Set Jar Odorants"
        selectors = [v.Col(children = [dropDown]) for dropDown in self.odorantsSelectorsDropDown] 
        sectionUI = v.Container(children = [
            v.Row(children = [
                v.Col(children = [
                      v.Html(tag = "h3", children =[sectionTitle]),
                    ])
            ]),
            v.Row(children = selectors)
        ])
        return(sectionUI)

    def odorSelectorsValues(self):
        return list(map(lambda x: x.v_model,self.odorantsSelectorsDropDown ))
    
    def sliderLog(self,x):
        return(10**x)
    
    def sliderLogR(self,x):
        return(x)
    
    def numberPrefix(self,x):
        if(x<=10**-12):
            return(str(round(x*10**12,3))+"p")
        elif(x<=10**-9):
            return(str(round(x*10**9,3))+'n')
        elif(x<=10**-6):
            return(str(round(x*10**6,3))+'μ')
        elif(x<=10**-3):
            return(str(round(x*10**3,3))+'m')
        else:
            return(round(x,3))
        
    def numberPrefixR(self,x):
        print(x)
        if('p' in x):
            return(float(x.replace('p',''))*10**-12)
        elif('n' in x):
            return(float(x.replace('n',''))*10**-9)
        elif('μ' in x):
            return(float(x.replace('μ',''))*10**-6)
        elif('m' in x):
            return(float(x.replace('m',''))*10**-3)
        else:
            return(float(x))
        
    
    def updateSliderValue(self,widget, event, data):
        for i in range(len(self.odorantsConcentrationSlider)):
            val = self.odorantsConcentrationsText[i].v_model
            self.odorantsConcentrationSlider[i].v_model = math.log10(float(self.odorantsConcentrationsText[i].v_model))
    
    def odorConcentrationUI(self, min_setpt = -12, max_setpt=0, step_size=0.5):
        sectionTitle = "Set Odorants Concentration"
        textAndSliders = []
        self.odorantsConcentrationsSetButton.on_event('click', self.odorConcentrationSetStepself)
        self.odorantsConcentrationsMinButton.on_event('click', self.odorConcentrationSetMinself)
        self.odorantsConcentrationsMaxButton.on_event('click', self.odorConcentrationSetMaxself)
        self.odorantsConcentrationsUpdateButton.on_event('click',self.updateSliderValue)
        
        for i in range(len(self.OdorantsList)):
            self.odorantsConcentrationSlider[i].min = min_setpt
            self.odorantsConcentrationSlider[i].max = max_setpt
            self.odorantsConcentrationSlider[i].step = step_size
            slider = self.odorantsConcentrationSlider[i]
            text = self.odorantsConcentrationsText[i]
            directional_link((slider, 'v_model'), (text, 'v_model'),lambda x: "{:.3e}".format(10**x))
                
            textAndSliders= textAndSliders + [
                v.Col(children=[
                    slider
                ]),
                v.Col(md = "auto", children=[
                    text
                ])]
            
        sectionUI = v.Container(children =[
            v.Row(children =[
                v.Col(children = [
                      v.Html(tag = "h3", children =[sectionTitle]),
                    ])
            ]),
            v.Row(children = textAndSliders),
            v.Row(children =[self.odorantsConcentrationsUpdateButton]),
            v.Row(children = [
                v.Col(children =[self.odorantsConcentrationsSetText,self.odorantsConcentrationsSetButton]),
                v.Col(children =[self.odorantsConcentrationsMinText,self.odorantsConcentrationsMinButton]),
                v.Col(children =[self.odorantsConcentrationsMaxText,self.odorantsConcentrationsMaxButton])
            ])
        ])
        
        return(sectionUI)
    
    def odorConcentrationValues(self):
        print(list(map(lambda x:10**x.v_model, self.odorantsConcentrationSlider)))
        return list(map(lambda x:10**x.v_model, self.odorantsConcentrationSlider))
    
    def odorConcentrationSetStepself(self,widget, event, data):
        step = self.odorantsConcentrationsSetText.v_model
        for slider in self.odorantsConcentrationSlider:
            slider.step = float(step)
            
    def odorConcentrationSetMinself(self,widget, event, data):
        Min = self.odorantsConcentrationsMinText.v_model
        for slider in self.odorantsConcentrationSlider:
            slider.min = math.log10(float(Min))
    
    def odorConcentrationSetMaxself(self,widget, event, data):
        Max = self.odorantsConcentrationsMaxText.v_model
        Maxf = float(Max)
        for idx, slider in enumerate(self.odorantsConcentrationSlider):
            if(idx < len(self.OdorantsMaxCon)):
                if(Maxf < self.OdorantsMaxCon[idx]):
                    if(Maxf != 0):
                        slider.max = math.log10(Maxf)

            elif(len(self.OdorantsMaxCon) == 0):
                if(Maxf != 0):
                    slider.max = math.log10(Maxf)
                else:
                    slider.max = 0
    
    def dutyCyclesUI(self):
        sectionTitle = "Valve Duty Cycles"
        textAndValveName = []
        self.dutyCycleUpdateBtn.on_event('click', self.dutyCyclesValidation)
        for idx, (textA,textB) in enumerate(self.dutyCycleText):
            textAndValveName.append(
                v.Col(children = [
                v.Html(tag="h5", children = [f"Valve {idx+1}"]),
                
                    textA,
                    textB
            ]))
            
        sectionUI = v.Container(children=[
            v.Row(children = [
                v.Col(children =[
                    v.Html(tag = "h3", children =[sectionTitle])
                ])
            ]),
            v.Row(children=textAndValveName),
            v.Row(children =[
                v.Col(children =[
                    self.dutyCycleUpdateBtn
                ])
            ])
        ])
        return(sectionUI)    
    
    
    def dutyCyclesValues(self):
        # return list(map(lambda x:(int(x[0].v_model),int(x[1].v_model)), self.dutyCycleText))
        return [(i+1,float(x[0].v_model),float(x[1].v_model)) for i, x in enumerate(self.dutyCycleText)]

    def dutyCyclesValidation(self,widget, event, data):
        for idx, (textA,textB) in enumerate(self.dutyCycleText):
            vA = 0
            vB = 0
            if(self.RepresentsInt(textA.v_model) and self.RepresentsInt(textB.v_model)):
                # print("FIRST CHECK")
                vA = int(textA.v_model)
                vB = int(textB.v_model)
                if(vA + vB > 1 or vA<0 or vB<0):
                    # print("SECOND CHECK")
                    textA.rules=[False]
                    textB.rules=[False]
                else:
                    textA.rules=[True]
                    textB.rules=[True]
            else:
                textA.rules=[False]
                textB.rules=[False]

    def occupancyTimeUI(self):
        sectionTitle = "Valve Occupancy TIme"
        textAndValveName = []
        self.ocupancyTimeUpdateBtn.on_event('click', self.occupancyTimeValidation)
        for idx, (textA,textB) in enumerate(self.ocupancyTimeText):
            textAndValveName.append(
                v.Col(children = [
                v.Html(tag="h5", children = [f"Valve {idx+1}"]),
                
                    textA,
                    textB
            ]))
            
        sectionUI = v.Container(children=[
            v.Row(children = [
                v.Col(children =[
                    v.Html(tag = "h3", children =[sectionTitle])
                ])
            ]),
            v.Row(children=textAndValveName),
            v.Row(children =[
                v.Col(children =[
                    self.ocupancyTimeUpdateBtn
                ])
            ])
        ])
        return(sectionUI)    

    def occupancyTimeValues(self):
        #return list(map(lambda x,i:(float(x[0].v_model),float(x[1].v_model)), self.ocupancyTimeText))
        return [(i+1,float(x[0].v_model),float(x[1].v_model)) for i, x in enumerate(self.ocupancyTimeText)]

    def occupancyTimeValidation(self,widget, event, data):
        for idx, (textA,textB) in enumerate(self.ocupancyTimeText):
            vA = 0
            vB = 0
            if(self.RepresentsFloat(textA.v_model) and self.RepresentsFloat(textB.v_model)):
                # print("FIRST CHECK")
                vA = float(textA.v_model)
                vB = float(textB.v_model)
                if(vA + vB > 1 or vA<0 or vB<0):
                    # print("SECOND CHECK")
                    textA.rules=[False]
                    textB.rules=[False]
                else:
                    textA.rules=[True]
                    textB.rules=[True]
            else:
                textA.rules=[False]
                textB.rules=[False]
    
    def RepresentsInt(self,s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
    
    def RepresentsFloat(self,s):
        try: 
            float(s)
            return True
        except ValueError:
            return False
                
                
    def mfcUI(self):
        sectionTitle = "Mass Flow Controlers Flow and Voltage"
        sliderAndText = []
        #self.mfcBtn.on_event('click', self.dutyCyclesValidation)
        for idx, (slider,text) in enumerate(self.mfcText):
            mapConstant = self.MFC_DATA[idx][1][1] / self.MFC_VOLTAGE[1]
            ### NOTE mapConstant not working for idx == 1. Hardcoded proper solution
            ### using print mapConstant is set to the right value but the directional_link does not work.
            ### Fix
            if(idx==1):
                link((slider,"v_model"),(text,"v_model"),(lambda x:round(x/0.2,2),(lambda x: round(float(x)*0.2,2))))
            else:
                link((slider,"v_model"),(text,"v_model"),(lambda x:round(x/mapConstant,2),lambda x:round(float(x)*mapConstant,2)))
                
            sliderAndText= sliderAndText+ [
                v.Col(children=[
                    v.Html(tag="h5", children = [self.MFC_DATA[idx][0]]),
                    v.Row(children=[v.Html(tag="h5", children = [" "])]),
                    v.Row(children=[
                         v.Col(children=[slider]),
                         v.Col(children=[text])
                    ])
                ])]
            
        sectionUI = v.Container(children=[
            v.Row(children = [
                v.Col(children =[
                    v.Html(tag = "h3", children =[sectionTitle])
                ])
            ]),
            v.Row(children=sliderAndText),
            v.Row(children =[
                v.Col(children =[
                    self.dutyCycleUpdateBtn
                ])
            ])
        ])
        return(sectionUI)
    
    def mfcValues(self):
        return list(map(lambda x:(x[0].v_model,x[1].v_model), self.mfcText))
    
    def allValues(self):
        values = {
            "odorSelector": self.odorSelectorsValues(),
            "concentrations": self.odorConcentrationValues(),
            "dutyCycles": self.dutyCyclesValues(),
            "mfc": self.mfcValues()
        }
        return(values)
    
    def timeSeriesUpdate(self,value,plotLast=5000):
        #number of previous data points to ge ploted
        #note value can be array or int
        scatterData = self.timeSeries.data[0]
        # if(type(value)==int):
        #     self.timeSeriesData.append(value)
        # else:
        if (len(self.timeSeriesData) >= plotLast*2):                 # Trim last 5000 values once reaching 10000 to prevent memory overflow.
            self.timeSeriesData = self.timeSeriesData[:-plotLast*2]
        self.timeSeriesData = self.timeSeriesData + value

        if(len(self.timeSeriesData)>plotLast):
            scatterData.y = self.timeSeriesData[-plotLast:]
            if (self.print_PID_avg): print(sum(scatterData.y)/plotLast)

    
            
        
