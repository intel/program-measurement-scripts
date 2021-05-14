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

"""

class FSM(Observable):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.control = None
        self.file = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'my_state_diagram.png')

        transitions = [
                {'trigger':'proceed', 'source':'INIT', 'dest':'Setup', 'after':'Setup'},
                {'trigger':'proceed', 'source':'Setup', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'appCoverage', 'source':'BeginAnalysis', 'dest':'CoverageSummary', 'after':'CoverageSummary'},
                {'trigger':'libTime', 'source':'BeginAnalysis', 'dest':'TimeSummary', 'after':'TimeSummary'},
                {'trigger':'showSCurve', 'source':'BeginAnalysis', 'dest':'SCurve', 'after':'SCurve'},
                {'trigger':'showUCurve', 'source':'BeginAnalysis', 'dest':'UCurve', 'after':'UCurve'},
                {'trigger':'showArithIntensity', 'source':'BeginAnalysis', 'dest':'ArithIntensityPlot', 'after':'ArithIntensityPlot'},
                {'trigger':'sidoAnalysis', 'source':'BeginAnalysis', 'dest':'SIDOResults', 'after':'SIDOResults'},
                {'trigger':'swbiasReco', 'source':'SIDOResults', 'dest':'SWBiasResults', 'after':'SWBiasResults'},
                {'trigger':'showOneview', 'source':'SWBiasResults', 'dest':'Oneview', 'after':'Oneview'},
                {'trigger':'previous', 'source':'Oneview', 'dest':'SWBiasResults', 'after':'SWBiasResults'},
                {'trigger':'previous', 'source':'SWBiasResults', 'dest':'SIDOResults', 'after':'SIDOResults'},
                {'trigger':'previous', 'source':'SIDOResults', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'ArithIntensityPlot', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'UCurve', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'SCurve', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'TimeSummary', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'CoverageSummary', 'dest':'BeginAnalysis', 'after':'BeginAnalysis'},
                {'trigger':'previous', 'source':'BeginAnalysis', 'dest':'Setup', 'after':'Setup'},
                {'trigger':'previous', 'source':'Setup', 'dest':'INIT', 'after':'INIT'}
                ]
        #states = ['INIT', 'Setup', 'BeginAnalysis', 'CoverageSummary', 'TimeSummary', 'SCurve', 'UCurve', 'ArithIntensityPlot',
        #          ]
        # Collect all the states from source and dest and after for transitons
        states = sorted(set([trans[node] for trans in transitions for node in ['source', 'dest', 'after']]))

        # if self.tab.data.loadedData.transitions == 'showing':
        #     self.machine = Machine(model=self, states=states, initial='A11', transitions=transitions)
        # elif self.tab.data.loadedData.transitions == 'hiding':
        #     self.tab.data.loadedData.transitions = 'disabled'
        #     self.machine = Machine(model=self, states=states, initial='A1', transitions=transitions)
        # else:
        #     self.machine = Machine(model=self, states=states, initial='INIT', transitions=transitions)

        self.machine = Machine(model=self, states=states, initial='INIT', transitions=transitions)
        self.save_graph()

    def reset_buttons(self):
        for button in self.control.gui.guide_tab.buttons:
            button.grid_remove()

    def INIT(self):
        print("In INIT")
        self.reset_buttons()
        self.control.gui.guide_tab.proceed_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.minimizeOneview()
        self.updated_notify_observers()
    
    def Setup(self):
        print("In Setup")
        # Setup buttons
        self.reset_buttons()
        self.control.gui.guide_tab.proceed_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.previous_button.grid(column=0, row=1, sticky=tk.NW, pady=2)
        # TO ADD display mockup page to setup tool in Oneview tab
        self.control.load_url("https://datafront.maqao.exascale-computing.eu/public_html/oneview2020/")
        self.control.maximizeOneview()
        self.updated_notify_observers()

    def BeginAnalysis(self):
        print("In BeginAnslysis")
        # Setup buttons
        self.reset_buttons()
        self.control.gui.guide_tab.abeg_1a_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.abeg_1b_button.grid(column=0, row=1, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.abeg_2a_button.grid(column=0, row=2, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.abeg_2b_button.grid(column=0, row=3, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.abeg_3_button.grid(column=0, row=4, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.sido_analysis_button.grid(column=0, row=5, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.previous_button.grid(column=0, row=6, sticky=tk.NW, pady=2)
        self.control.minimizeOneview()
        # Auto-select plot
        self.control.change_codelet_tab('Summary')
        self.updated_notify_observers()

    def CoverageSummary(self):
        print("In CoverageSummary")
        # Setup buttons
        self.reset_buttons()
        self.control.gui.guide_tab.previous_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        # Auto-select plot
        self.control.change_codelet_tab('Summary')
        self.updated_notify_observers()

    def TimeSummary(self):
        print("In TimeSummary")
        self.reset_buttons()
        self.control.gui.guide_tab.previous_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        # Auto-select plot
        self.control.change_codelet_tab('Summary')
        self.updated_notify_observers()

    def SIDOResults(self):
        print("In sidoAnalysis")
        self.reset_buttons()
        self.control.gui.guide_tab.swbias_reco_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.previous_button.grid(column=0, row=1, sticky=tk.NW, pady=2)
        # Auto-select plot
        self.control.change_codelet_tab('SI Plot')
        self.updated_notify_observers()

    def SWBiasResults(self):
        print("In SWBiasResults")
        self.reset_buttons()
        self.control.gui.guide_tab.show_oneview_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.gui.guide_tab.previous_button.grid(column=0, row=1, sticky=tk.NW, pady=2)
        # TODO: May want to implement exit state action to take care of this minimization operation
        self.control.minimizeOneview()
        # Auto-select plot
        self.control.change_codelet_tab('SWbias')
        self.updated_notify_observers()

    def Oneview(self):
        print("In Oneview")
        self.reset_buttons()
        self.control.gui.guide_tab.previous_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        self.control.maximizeOneview()
        self.updated_notify_observers()
        

    def SCurve(self):
        print("In SCurve")
        self.reset_buttons()
        self.control.gui.guide_tab.previous_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        # Auto-select plot
        self.control.change_codelet_tab('S-Curve')
        self.updated_notify_observers()

    def UCurve(self):
        print("In UCurve")
        self.reset_buttons()
        self.control.gui.guide_tab.previous_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        # Auto-select plot
        self.control.change_codelet_tab('S-Curve')
        self.updated_notify_observers()

    def ArithIntensityPlot(self):
        print("In ArithIntensityPlot")
        self.reset_buttons()
        self.control.gui.guide_tab.previous_button.grid(column=0, row=0, sticky=tk.NW, pady=2)
        # Auto-select plot
        self.control.change_codelet_tab('QPlot')
        self.updated_notify_observers()

    def setControl(self, control):
        self.control = control

    def save_graph(self):
        self.machine.get_graph(show_roi=True).draw(self.file, prog='dot')