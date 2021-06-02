from statistics import median
import math
import numpy as np
import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_scurve import scurve_plot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName as MN
#globals().update(MetricName.__members__)

class ScurveData(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Scurve', x_axis=MN.CAP_FP_GFLOP_P_S, y_axis=MN.CAP_FP_GFLOP_P_S)
    
    # def notify(self, loadedData, x_axis=None, y_axis=MetricName.CAP_FP_GFLOP_P_S, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
    #     print("ScurveData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings)
    #     # Generate Plot 
    #     scurve_df, self.fig, self.plotData = scurve_plot(self.df.copy(deep=True), 'test', scale, 'Rank Order', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
    #             mappings=self.mappings, variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
    #     self.notify_observers()

class ScurveTab(PlotTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, ScurveData, 'Scurve', [])

    #def notify(self, data):
    #    # Metrics to be displayed in the data table are unique for each plot
    #    metrics = self.data.df.columns.tolist()
    #    super().setup(metrics)
    #    self.buildTableTabs()

    # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
        # self.axesTab = AxesTab(self.tableNote, self, 'Scurve')
        # self.tableNote.add(self.axesTab, text="Axes")