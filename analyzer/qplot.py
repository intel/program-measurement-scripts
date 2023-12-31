import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_QPlot import parse_ip_df as parse_ip_qplot_df
from generate_QPlot import QPlot
from capeplot import CapacityData
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName as MN
#globals().update(MetricName.__members__)

class QPlotData(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'QPlot', x_axis=MN.CAP_FP_GFLOP_P_S, y_axis=MN.CAP_MEMMAX_GB_P_S)
        # TODO: Try removing all of these attributes
        # self.df = None
        self.fig = None
        self.ax = None
        self.appDf = None
        self.appFig = None
        self.appTextData = None

    # def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
    #     print("QPlotData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings)
    #     # Generate Plot 
    #     # chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]']) 

    #     # df = self.df.copy(deep=True)
    #     # data = CapacityData(df)
    #     # data.set_chosen_node_set(chosen_node_set) 
    #     # # data.compute()
    #     # # self.merge_metrics(data.df, [MetricName.CAP_L3_GB_P_S, MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S, MetricName.CAP_FP_GFLOP_P_S])


    #     # plot = QPlot(self.capacityData, 'ORIG', "test", scale, "QPlot", False, True, None, None, 
    #     #              loadedData.source_order, self.mappings, self.gui.loadedData.short_names_path)
    #     # plot.compute_and_plot()
        
    #     # #df_XFORM, fig_XFORM, plotData_XFORM, df_ORIG, fig_ORIG, plotData_ORIG = parse_ip_qplot_df\
    #     # #        (self.df.copy(deep=True), "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
    #     # #            source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=self.gui.loadedData.short_names_path)
    #     # self.fig = plot.fig
    #     # self.plotData = plot.plotData
    #     #self.merge_metrics(df_ORIG if df_ORIG is not None else df_XFORM, [MetricName.CAP_L3_GB_P_S, MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S, MetricName.CAP_FP_GFLOP_P_S])
    #     #self.fig = fig_ORIG 
    #     #self.plotData = plotData_ORIG 
    #     self.notify_observers()

class QPlotTab(PlotTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, QPlotData, 'QPlot', [MN.CAP_L1_GB_P_S, MN.CAP_L2_GB_P_S, MN.CAP_L3_GB_P_S, \
                MN.CAP_RAM_GB_P_S, MN.CAP_MEMMAX_GB_P_S])

    # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
        # self.axesTab = AxesTab(self.tableNote, self, 'QPlot')
        # self.tableNote.add(self.axesTab, text="Axes")

    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return QPlot()
        # return QPlot(self.analyzerData.capacityDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', "test", self.analyzerData.scale, "QPlot", 
        #              False, True, self.analyzerData.x_axis, self.analyzerData.y_axis, self.analyzerData.mappings, self.analyzerData.short_names_path)