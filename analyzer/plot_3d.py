import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_3d import plot_3d
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class Data3d(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, '3D')

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("Data3d Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot
        self.df, self.fig, self.textData = plot_3d(self.df, 'test', scale, '3D', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
            variants=self.variants, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        self.notify_observers()

class Tab3d(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, '3D', RATE_FP_GFLOP_P_S, COVERAGE_PCT, [])

    # TODO: Check with Elias - why the complication 
    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = self.data.df.columns.tolist()
        # TODO: Have a cleaner fix, complicated as can't send in shared dataframe to plot functions but want to add new metrics to shared
        df = self.data.loadedData.dfs[self.level]
        if set(['Saturation', 'Intensity']).issubset(df.columns):
            self.data.df.drop(columns=['Saturation', 'Intensity'], inplace=True, errors='ignore')
            self.data.df = pd.merge(self.data.df, df[[NAME, TIMESTAMP, 'Saturation', 'Intensity']], on=[NAME, TIMESTAMP])
        super().setup(metrics)
        self.buildTableTabs()
    
    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        self.tableNote.add(self.axesTab, text="Axes")