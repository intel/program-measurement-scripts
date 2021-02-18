import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_3d import plot_3d
from generate_3d import Plot3d
from capeplot import CapacityData
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
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        df = self.df.copy(deep=True)
        data = CapacityData(df)
        data.set_chosen_node_set(chosen_node_set)
        data.compute()
        plot = Plot3d(data, 'ORIG', 'test', scale, '3D', chosen_node_set, no_plot=False, gui=True, 
                      x_axis=x_axis, y_axis=y_axis, z_axis=None, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        plot.compute_and_plot()
        self.fig = plot.fig
        self.textData = plot.plotData
        #df_3d, self.fig, self.textData = plot_3d(self.df.copy(deep=True), 'test', scale, '3D', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
        #    variants=self.variants, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        self.notify_observers()

class Tab3d(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, '3D', RATE_FP_GFLOP_P_S, COVERAGE_PCT, [])

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