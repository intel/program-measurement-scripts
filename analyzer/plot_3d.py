import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, PlotAnalyzerData
import pandas as pd
from generate_3d import plot_3d
from generate_3d import Plot3d
from capeplot import CapacityData
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName as MN
#globals().update(MetricName.__members__)

class Data3d(PlotAnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, '3D', x_axis=MN.RATE_FP_GFLOP_P_S, y_axis=MN.COVERAGE_PCT)

#     def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
#         print("Data3d Notified from ", loadedData)
#         super().notify(loadedData, update, variants, mappings)
#         # Generate Plot 
#         # chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
#         # df = self.df.copy(deep=True)
#         # data = CapacityData(df)
#         # data.set_chosen_node_set(chosen_node_set)
# # #        data.compute()
# #         plot = Plot3d(self.capacityData, 'ORIG', 'test', scale, '3D', no_plot=False, gui=True, 
# #                       x_axis=x_axis, y_axis=y_axis, z_axis=None, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
# #         plot.compute_and_plot()
# #         self.fig = plot.fig
# #         self.plotData = plot.plotData
#         #df_3d, self.fig, self.plotData = plot_3d(self.df.copy(deep=True), 'test', scale, '3D', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
#         #    variants=self.variants, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
#         self.notify_observers()

class Tab3d(PlotTab):
    def __init__(self, parent):
        super().__init__(parent, Data3d, '3D', [])

    # def notify(self, data):
    #     # Metrics to be displayed in the data table are unique for each plot
    #     metrics = self.analyzerData.df.columns.tolist()
    #     super().setup(metrics)
    #     self.buildTableTabs()
    
    # Create meta tabs
    # def buildTableTabs(self):
    #     super().buildTableTabs()
        # self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        # self.tableNote.add(self.axesTab, text="Axes")
    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems).setZaxis(self.analyzerData.z_axis)

    def mk_plot(self):
        return Plot3d(self.analyzerData.capacityDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', 'test', self.analyzerData.scale, '3D', no_plot=False, gui=True, 
                      x_axis=self.analyzerData.x_axis, y_axis=self.analyzerData.y_axis, z_axis=None, mappings=self.mappings, 
                      short_names_path=self.analyzerData.short_names_path)