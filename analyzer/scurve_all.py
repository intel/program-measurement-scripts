from statistics import median
import math
import numpy as np
import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_scurve_all import scurve_all_plot
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
    
    def notify(self, loadedData, x_axis=None, y_axis='C_FLOP [GFlop/s]', variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("Scurve_allData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot 
        scurve_df, self.fig, self.textData = scurve_all_plot(self.df.copy(deep=True), 'test', scale, 'S-Curve All', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
        self.notify_observers()

class ScurveAllTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'Scurve_all', 
                         'C_FLOP [GFlop/s]', 'C_FLOP [GFlop/s]', [])

    def get_metrics(self):
        return self.data.df.columns.tolist()

    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'Scurve')
        self.tableNote.add(self.axesTab, text="Axes")