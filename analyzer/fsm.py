import tkinter as tk
import graphviz
import pandas as pd
from transitions.extensions import GraphMachine as Machine
from transitions import State
import operator
import os
from os.path import expanduser
from utils import Observable
from metric_names import MetricName as MN
from metric_names import NonMetricName, KEY_METRICS, CATEGORIZED_METRICS, PLOT_METRICS
globals().update(MN.__members__)

"""
Examples of filtering points (operators: le, ge, ne, eq)

self.control.remove_points(operator=operator.le, metric=RATE_FP_GFLOP_P_S, threshold=1, level='Codelet')
self.control.remove_points(operator=operator.ne, metric=DATA_SET, threshold=1700, level='Codelet')

Example of changing axis scale

self.control.set_plot_scale(x_scale='linear', y_scale='log')

"""

class FSM(Observable):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.control = None
        self.file = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'my_state_diagram.png')

        self.transitions = [
                {'trigger':'proceed', 'source':'INIT', 'dest':'Setup', 'after':'Setup'},
                {'trigger':'proceed', 'source':'Setup', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'appCoverage', 'source':'BeginAnalysis', 'dest':'CoverageSummary', 'after':'CoverageSummary'},
                {'trigger':'libTime', 'source':'BeginAnalysis', 'dest':'TimeSummary', 'after':'TimeSummary'},
                {'trigger':'showMemLevel', 'source':'TimeSummary', 'dest':'MemLevelAdded', 'after':'MemLevelAdded'},
                {'trigger':'showSCurve', 'source':'MemLevelAdded', 'dest':'SCurve', 'after':'SCurve'},
                {'trigger':'showUCurve', 'source':'SCurve', 'dest':'UCurve', 'after':'UCurve'},
                {'trigger':'showL1ArithIntensity', 'source':'UCurve', 'dest':'L1ArithIntensityPlot', 'after':'L1ArithIntensityPlot'},
                {'trigger':'showMaxArithIntensity', 'source':'L1ArithIntensityPlot', 'dest':'MaxArithIntensityPlot', 'after':'MaxArithIntensityPlot'},

                # {'trigger':'showSCurve', 'source':'BeginAnalysis', 'dest':'SCurve', 'after':'SCurve'},
                # {'trigger':'showUCurve', 'source':'BeginAnalysis', 'dest':'UCurve', 'after':'UCurve'},
                # {'trigger':'showArithIntensity', 'source':'BeginAnalysis', 'dest':'ArithIntensityPlot', 'after':'ArithIntensityPlot'},
                # {'trigger':'sidoAnalysis', 'source':'BeginAnalysis', 'dest':'SIDOResults', 'after':'SIDOResults'},
                # {'trigger':'swbiasReco', 'source':'SIDOResults', 'dest':'SWBiasResults', 'after':'SWBiasResults'},
                # {'trigger':'showOneview', 'source':'SWBiasResults', 'dest':'Oneview', 'after':'Oneview'},

                # {'trigger':'previous', 'source':'Oneview', 'dest':'SWBiasResults', 'after':'SWBiasResults'},
                # {'trigger':'previous', 'source':'SWBiasResults', 'dest':'SIDOResults', 'after':'SIDOResults'},
                # {'trigger':'previous', 'source':'SIDOResults', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'MaxArithIntensityPlot', 'dest':'L1ArithIntensityPlot', 'after':'L1ArithIntensityPlot'},
                {'trigger':'previous', 'source':'L1ArithIntensityPlot', 'dest':'UCurve', 'after':'UCurve'},
                {'trigger':'previous', 'source':'UCurve', 'dest':'SCurve', 'after':'SCurve'},
                {'trigger':'previous', 'source':'SCurve', 'dest':'MemLevelAdded', 'after':'MemLevelAdded'},
                {'trigger':'previous', 'source':'MemLevelAdded', 'before':'returnFromMemLevelAdded', 'dest':'TimeSummary', 'after':'TimeSummary'},
                {'trigger':'previous', 'source':'TimeSummary', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'CoverageSummary', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'BeginAnalysis', 'dest':'Setup', 'after':'Setup'},
                {'trigger':'previous', 'source':'Setup', 'dest':'INIT', 'after':'INIT'}
                ]
        self.transition_names = { 'proceed': 'Proceed', 
                                  'previous': 'Previous', 
                                  'appCoverage': 'Application Coverage (CoverageSummary)', 
                                  'libTime': 'Library Time (TimeSummary)', 
                                  'showMemLevel': 'Add Memory Hierachy Level to label (showMemLevel)', 
                                  'showSCurve': 'Show S-Curve (showSCurve)', 
                                  'showUCurve': 'Show U-Curve (showUCurve)', 
                                  'showL1ArithIntensity': 'Show L1 Arithmetic Intensity (showL1ArithIntensity)', 
                                  'showMaxArithIntensity': 'Show Max Arithmetic Intensity (showMaxArithIntensity)', 
                                  'sidoAnalysis': 'SIDO Analysis (sidoAnalysis)', 
                                  'swbiasReco': 'SWBias Recommendations (swbiasReco)', 
                                  'showOneview': 'Show Oneview (showOneview)'
                                  }
        #states = ['INIT', 'Setup', 'BeginAnalysis', 'CoverageSummary', 'TimeSummary', 'SCurve', 'UCurve', 'ArithIntensityPlot',
        #          ]
        # Collect all the states from source and dest and after for transitons
        states = self.sorted([trans[node] for trans in self.transitions for node in ['source', 'dest', 'after']])

        # if self.tab.data.loadedData.transitions == 'showing':
        #     self.machine = Machine(model=self, states=states, initial='A11', transitions=transitions)
        # elif self.tab.data.loadedData.transitions == 'hiding':
        #     self.tab.data.loadedData.transitions = 'disabled'
        #     self.machine = Machine(model=self, states=states, initial='A1', transitions=transitions)
        # else:
        #     self.machine = Machine(model=self, states=states, initial='INIT', transitions=transitions)

        self.machine = Machine(model=self, states=states, initial='INIT', transitions=self.transitions)
        self.save_graph()

    @staticmethod
    def sorted(lst):
        return sorted(set(lst))

    def reset_state(self):
        self.to_INIT()
        self.updated_notify_observers()
        
    def get_all_transitions(self):
        transitions = self.sorted([transition['trigger'] for transition in self.transitions ])
        return transitions, [self.transition_names[transition] for transition in transitions]

    def get_next_transitions(self):
        return self.sorted([transition['trigger'] for transition in self.transitions if transition['source'] == self.state])

    def INIT(self):
        print("In INIT")
        # self.reset_buttons()
        # self.control.gui.guide_tab.proceed_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.minimizeOneview()
        self.updated_notify_observers()
    
    def Setup(self):
        print("In Setup")
        # TO ADD display mockup page to setup tool in Oneview tab
        self.control.load_url("https://datafront.maqao.exascale-computing.eu/public_html/oneview2020/")
        self.control.maximizeOneview()
        self.updated_notify_observers()

    def BeginAnalysis(self):
        print("In BeginAnslysis")
        self.control.minimizeOneview()
        # Auto-select plot
        self.control.change_codelet_tab('Summary')
        self.updated_notify_observers()

    def CoverageSummary(self):
        print("In CoverageSummary")
        # Auto-select plot
        self.control.change_codelet_tab('Summary')
        self.control.set_plot_axes(x_axis=None, y_axis=MN.COVERAGE_PCT, x_scale='linear', y_scale='linear')
        self.updated_notify_observers()

    def TimeSummary(self):
        print("In TimeSummary")
        # Auto-select plot
        self.control.change_codelet_tab('Summary')
        self.control.set_plot_axes(x_axis=None, y_axis=MN.TIME_LOOP_S, x_scale='linear', y_scale='log')
        self.updated_notify_observers()

    def returnFromMemLevelAdded(self):
        print("Back from MemLevelAdded")
        self.control.set_labels([])
        self.updated_notify_observers()
    
    def MemLevelAdded(self):
        print("In MemLevelAdded")
        self.control.set_labels([MN.MAX_MEM_LEVEL_85])
        self.updated_notify_observers()

    def SIDOResults(self):
        print("In sidoAnalysis")
        # Auto-select plot
        self.control.change_codelet_tab('SI Plot')
        self.updated_notify_observers()

    def SWBiasResults(self):
        print("In SWBiasResults")
        # TODO: May want to implement exit state action to take care of this minimization operation
        self.control.minimizeOneview()
        # Auto-select plot
        self.control.change_codelet_tab('SWbias')
        self.updated_notify_observers()

    def Oneview(self):
        print("In Oneview")
        self.control.maximizeOneview()
        self.updated_notify_observers()
        

    def SCurve(self):
        print("In SCurve")
        # Auto-select plot
        self.control.change_codelet_tab('S-Curve')
        self.updated_notify_observers()

    def UCurve(self):
        print("In UCurve")
        # Auto-select plot
        self.control.change_codelet_tab('S-Curve')
        self.updated_notify_observers()

    def L1ArithIntensityPlot(self):
        print("In L1ArithIntensityPlot")
        # Auto-select plot
        self.control.change_codelet_tab('QPlot')
        self.control.set_plot_axes(x_axis=None, y_axis=MN.CAP_L1_GB_P_S, x_scale=None, y_scale=None)
        self.updated_notify_observers()

    def MaxArithIntensityPlot(self):
        print("In MaxArithIntensityPlot")
        # Auto-select plot
        self.control.change_codelet_tab('QPlot')
        self.control.set_plot_axes(x_axis=None, y_axis=MN.CAP_MEMMAX_GB_P_S, x_scale=None, y_scale=None)
        self.updated_notify_observers()

    def setControl(self, control):
        self.control = control

    def save_graph(self):
        self.machine.get_graph(show_roi=True).draw(self.file, prog='dot')