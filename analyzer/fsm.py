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

class FSM(Observable):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        # self.tab = self.parent.tab
        self.control = None
        # self.title = self.tab.plotInteraction.plotData['title']
        self.file = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'my_state_diagram.png')
        # Temporary hardcoded points for each state
        # self.a2_points = ['livermore_default: lloops.c_kernels_line1340_01587402719', 'NPB_2.3-OpenACC-C: sp.c_compute_rhs_line1452_01587402719']
        # self.a3_points = ['TSVC_default: tsc.c_vbor_line5367_01587481116', 'NPB_2.3-OpenACC-C: cg.c_conj_grad_line549_01587481116', 'NPB_2.3-OpenACC-C: lu.c_pintgr_line2019_01587481116']
        transitions = [{'trigger':'proceed', 'source':'INIT', 'dest':'AStart', 'after':'AStart'},
                {'trigger':'details', 'source':'AStart', 'dest':'A1', 'after':'A1'},
                {'trigger':'details', 'source':'A1', 'dest':'A11', 'after':'A11'},
                {'trigger':'proceed', 'source':'A1', 'dest':'A2', 'after':'A2'},
                {'trigger':'proceed', 'source':'A2', 'dest':'A3', 'after':'A3'},
                {'trigger':'proceed', 'source':'A3', 'dest':'AEnd', 'after':'AEnd'},
                {'trigger':'proceed', 'source':'AStart', 'dest':'AEnd', 'after':'AEnd'},
                {'trigger':'proceed', 'source':'AEnd', 'dest':'B1', 'after':'B1'},
                {'trigger':'proceed', 'source':'B1', 'dest':'B2', 'after':'B2'},
                {'trigger':'proceed', 'source':'B2', 'dest':'BEnd', 'after':'BEnd'},
                {'trigger':'proceed', 'source':'BEnd', 'dest':'End', 'after':'End'},
                {'trigger':'previous', 'source':'End', 'dest':'BEnd', 'after':'BEnd'},
                {'trigger':'previous', 'source':'BEnd', 'dest':'B2', 'after':'B2'},
                {'trigger':'previous', 'source':'B2', 'dest':'B1', 'after':'B1'},
                {'trigger':'previous', 'source':'B1', 'dest':'AEnd', 'after':'AEnd'},
                {'trigger':'previous', 'source':'AEnd', 'dest':'AStart', 'after':'AStart'},
                {'trigger':'previous', 'source':'AStart', 'dest':'INIT', 'after':'INIT'},
                {'trigger':'previous', 'source':'A3', 'dest':'A2', 'after':'A2'},
                {'trigger':'previous', 'source':'A2', 'dest':'A1', 'after':'A1'},
                {'trigger':'previous', 'source':'A1', 'dest':'AStart', 'after':'AStart'},
                {'trigger':'previous', 'source':'A11', 'dest':'A1', 'after':'A1'}]
        states = ['INIT', 'AStart', State('A1', ignore_invalid_triggers=True), State('A11', ignore_invalid_triggers=True), 'A2', 'A3', 'AEnd', 'B1', 'B2', 'BEnd', 'End']

        # if self.tab.data.loadedData.transitions == 'showing':
        #     self.machine = Machine(model=self, states=states, initial='A11', transitions=transitions)
        # elif self.tab.data.loadedData.transitions == 'hiding':
        #     self.tab.data.loadedData.transitions = 'disabled'
        #     self.machine = Machine(model=self, states=states, initial='A1', transitions=transitions)
        # else:
        #     self.machine = Machine(model=self, states=states, initial='INIT', transitions=transitions)

        self.machine = Machine(model=self, states=states, initial='INIT', transitions=transitions)
        self.save_graph()

        # Get points that we want to save for each state
        # self.a1_highlighted = self.tab.plotInteraction.A_filter(relate=operator.gt, metric=MN.SPEEDUP_TIME_LOOP_S, threshold=1, getNames=True) # Highlight SIDO codelets
        # self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric=MN.SRC_RHS_OP_COUNT, threshold=1, getNames=True) # Highlight RHS codelets
        # self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, getNames=True) # Highlight FMA codelets

    def INIT(self):
        print("In INIT")
        # self.tab.plotInteraction.plotData['ax'].set_title(self.title + ', ' + 'INIT', pad=40)
        self.updated_notify_observers()
    
    def AStart(self):
        print("In AStart")
        # self.tab.plotInteraction.showMarkers()
        # self.tab.plotInteraction.unhighlightPoints()
        # self.tab.labelTab.reset()
        # self.tab.plotInteraction.plotData['ax'].set_title(self.title + ', ' + 'A-Start', pad=40)
        self.updated_notify_observers()

    def A1(self):
        print("In A1")
        # if self.tab.data.loadedData.transitions == 'showing':
        #     print("going back to orig variants")
        #     self.tab.data.loadedData.transitions = 'hiding'
        #     self.tab.plotInteraction.showMarkers()
        #     self.tab.variantTab.checkListBox.showOrig()
        # else:
        #     print("A1 state after orig variants")
        #     self.tab.plotInteraction.showMarkers()
        #     self.tab.plotInteraction.unhighlightPoints()
        #     # self.tab.plotInteraction.plotData['ax'].set_title(self.title + ', ' + 'A1 (SIDO>1)', pad=40)
        #     self.a1_highlighted = self.tab.plotInteraction.A_filter(relate=operator.gt, metric=SPEEDUP_TIME_LOOP_S, threshold=1, show=True, highlight=True) # Highlight SIDO codelets
        #     self.updateLabels(SPEEDUP_TIME_LOOP_S)
        self.updated_notify_observers()

    def A11(self):
        print("In A11")
        # if self.tab.data.loadedData.transitions != 'showing':
        #     self.tab.data.loadedData.transitions = 'showing'
        #     for name in self.tab.plotInteraction.plotData['names']:
        #         if name not in self.a1_highlighted:
        #             self.tab.plotInteraction.togglePoint(self.tab.plotInteraction.plotData['name:marker'][name], visible=False)
        #     self.tab.variantTab.checkListBox.showAllVariants()
        self.updated_notify_observers()

    def A2(self):
        print("In A2")
        # self.tab.plotInteraction.unhighlightPoints()
        # self.tab.plotInteraction.plotData['ax'].set_title(self.title + ', ' + 'A2 (RHS=1)', pad=40)
        # self.tab.plotInteraction.A_filter(relate=operator.gt, metric=SPEEDUP_TIME_LOOP_S, threshold=1, highlight=False, remove=True) # Remove SIDO codelets
        # self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric=SRC_RHS_OP_COUNT, threshold=1, highlight=True, show=True) # Highlight RHS codelets
        # self.updateLabels(SRC_RHS_OP_COUNT)
        self.updated_notify_observers()

    def A3(self):
        print("In A3")
        # self.tab.plotInteraction.unhighlightPoints()
        # self.tab.plotInteraction.plotData['ax'].set_title(self.title + ', ' + 'A3 (FMA)', pad=40)
        # self.tab.plotInteraction.A_filter(relate=operator.eq, metric=SRC_RHS_OP_COUNT, threshold=1, highlight=False, remove=True) # Remove RHS codelets
        # self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True) # Highlight FMA codelets
        # self.updateLabels(COUNT_OPS_FMA_PCT)
        self.updated_notify_observers()

    def AEnd(self):
        print("In AEnd")
        # self.tab.plotInteraction.plotData['ax'].set_title(self.title + ', ' + 'A-End', pad=40)
        # self.all_highlighted = self.a1_highlighted + self.a2_highlighted + self.a3_highlighted
        # self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True, points=self.all_highlighted) # Highlight all previously highlighted codelets
        # self.updateLabels('advice')
        self.updated_notify_observers()

    def B1(self):
        print("In B1")
        self.updated_notify_observers()

    def B2(self):
        print("In B2")
        self.updated_notify_observers()

    def BEnd(self):
        print("In BEnd")
        self.updated_notify_observers()

    def End(self):
        print("In End")
        self.updated_notify_observers()

    def setControl(self, control):
        self.control = control

    def save_graph(self):
        self.machine.get_graph(show_roi=True).draw(self.file, prog='dot')
    
    # def updateLabels(self, metric):
    #     self.tab.labelTab.resetMetrics()
    #     self.tab.labelTab.metric1.set(metric)
    #     self.tab.labelTab.updateLabels()