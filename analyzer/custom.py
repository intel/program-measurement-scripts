import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_custom import custom_plot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class CustomData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'Custom')

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("CustomData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot
        custom_df, self.fig, self.textData = custom_plot(self.df.copy(deep=True), 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
            variants=self.variants, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        self.notify_observers()

class CustomTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'Custom', RATE_FP_GFLOP_P_S, COVERAGE_PCT, [])

    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = self.data.df.columns.tolist()
        super().setup(metrics)
        self.buildTableTabs()
    
    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        self.tableNote.add(self.axesTab, text="Axes")