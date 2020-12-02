import tkinter as tk
from utils import Observable
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_QPlot import parse_ip_df as parse_ip_qplot_df
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab
from metric_names import MetricName
globals().update(MetricName.__members__)

class QPlotData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'QPlot')
        # TODO: Try removing all of these attributes
        self.df = None
        self.fig = None
        self.ax = None
        self.appDf = None
        self.appFig = None
        self.appTextData = None

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("QPlotData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot 
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (self.df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
        self.df = df_ORIG if df_ORIG is not None else df_XFORM
        self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
        self.textData = textData_ORIG if textData_ORIG is not None else textData_XFORM
        self.notify_observers()

class QPlotTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'QPlot', 'C_FLOP [GFlop/s]', 'C_max [GB/s]')

    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        metrics = copy.deepcopy(self.data.gui.loadedData.common_columns_start)
        metrics.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
                'C_RAM [GB/s]', 'C_max [GB/s]'])
        metrics.extend(self.data.gui.loadedData.common_columns_end)
        super().setup(data, metrics)
        self.buildTableTabs()

    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.axesTab = AxesTab(self.tableNote, self, 'QPlot')
        self.tableNote.add(self.axesTab, text="Axes")