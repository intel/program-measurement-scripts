import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_TRAWL import trawl_plot
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class TRAWLData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'TRAWL')
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("TRAWLData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot 
        self.df, self.fig, self.textData = trawl_plot(self.df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
        self.notify_observers()

class TrawlTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'TRAWL', 'C_FLOP [GFlop/s]', SPEEDUP_VEC)

    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        metrics.extend([SPEEDUP_VEC, SPEEDUP_DL1])
        metrics.extend(self.data.gui.loadedData.common_columns_end)
        super().setup(metrics)
        self.buildTableTabs()

    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'TRAWL')
        self.tableNote.add(self.axesTab, text="Axes")