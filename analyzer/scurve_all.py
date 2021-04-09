from statistics import median
import math
import numpy as np
import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_scurve_all import scurve_all_plot
from generate_scurve_all import ScurveAllPlot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName as MN
#globals().update(MetricName.__members__)

class ScurveAllData(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Scurve_all', x_axis=MN.CAP_FP_GFLOP_P_S, y_axis=MN.CAP_FP_GFLOP_P_S)
    
    # def notify(self, loadedData, x_axis=None, y_axis=MetricName.CAP_FP_GFLOP_P_S, variants=[], update=False, scale='linear', level='Codelet', mappings=pd.DataFrame()):
    #     print("Scurve_allData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings)
    #     # Generate Plot 
    #     # plot = ScurveAllPlot(self.capacityDataItems, self.loadedData, level, 'ORIG', 'test', scale, 'S-Curve All', no_plot=False, gui=True, 
    #     #                      x_axis=x_axis, y_axis=y_axis, 
    #     #                      mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
    #     # plot.compute_and_plot()
    #     # self.fig = plot.fig
    #     # self.plotData = plot.plotData
    #     self.notify_observers()


class ScurveAllTab(PlotTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, ScurveAllData, 'Scurve_all', [])

    def get_metrics(self):
        return self.analyzerData.df.columns.tolist()

    # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
        # self.axesTab = AxesTab(self.tableNote, self, 'Scurve')
        # self.tableNote.add(self.axesTab, text="Axes")
    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return ScurveAllPlot()
        # return ScurveAllPlot(self.analyzerData.capacityDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', 'test', self.analyzerData.scale, 'S-Curve All', no_plot=False, gui=True, 
        #                      x_axis=self.analyzerData.x_axis, y_axis=self.analyzerData.y_axis, 
        #                      mappings=self.mappings, short_names_path=self.analyzerData.short_names_path)