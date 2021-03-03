from statistics import median
import math
import numpy as np
import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_scurve_all import scurve_all_plot
from generate_scurve_all import ScurveAllPlot
from capeplot import CapeData
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class ScurveAllData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'Scurve_all')
    
    def notify(self, loadedData, x_axis=None, y_axis=MetricName.CAP_FP_GFLOP_P_S, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("Scurve_allData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot 
        plot = ScurveAllPlot(self.capacityData, 'ORIG', 'test', scale, 'S-Curve All', no_plot=False, gui=True, 
                             x_axis=x_axis, y_axis=y_axis, 
                             mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        plot.compute_and_plot()
        self.fig = plot.fig
        self.textData = plot.plotData
        self.notify_observers()


class ScurveAllTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'Scurve_all', 
                         MetricName.CAP_FP_GFLOP_P_S, MetricName.CAP_FP_GFLOP_P_S, [])

    def get_metrics(self):
        return self.data.df.columns.tolist()

    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'Scurve')
        self.tableNote.add(self.axesTab, text="Axes")

    def mk_plot(self):
        return ScurveAllPlot(self.data.capacityData, 'ORIG', 'test', self.data.scale, 'S-Curve All', no_plot=False, gui=True, 
                             x_axis=self.data.x_axis, y_axis=self.data.y_axis, 
                             mappings=self.mappings, short_names_path=self.data.gui.loadedData.short_names_path)