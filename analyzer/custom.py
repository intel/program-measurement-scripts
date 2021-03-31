import tkinter as tk
from utils import Observable
from analyzer_base import PlotTab, AnalyzerData
import pandas as pd
from generate_custom import custom_plot
from generate_custom import CustomPlot
from capeplot import CapacityData
import copy
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, AxesTab, MappingsTab
from metric_names import MetricName as MN
#globals().update(MetricName.__members__)

class CustomData(AnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Custom')

    # def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
    #     print("CustomData Notified from ", loadedData)
    #     super().notify(loadedData, update, variants, mappings) 
        
        
        # df = self.df.copy(deep=True)
        # chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        # df[MetricName.CAP_FP_GFLOP_P_S] = df[RATE_FP_GFLOP_P_S]
        # data = CapacityData(df)
        # data.set_chosen_node_set(chosen_node_set)
#        data.compute()

        

        # plot = CustomPlot(self.capacityData, 'ORIG', 'test', scale, 'Custom', no_plot=False, gui=True, 
        #                   x_axis=x_axis, y_axis=y_axis, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        # plot.compute_and_plot()
        # self.fig = plot.fig
        # self.plotData = plot.plotData

        # Generate Plot
        #custom_df, self.fig, self.plotData = custom_plot(self.df.copy(deep=True), 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
        #    variants=self.variants, mappings=self.mappings, short_names_path=self.gui.loadedData.short_names_path)
        #self.notify_observers()

class CustomTab(PlotTab):
    def __init__(self, parent):
        super().__init__(parent, CustomData, 'Custom', MN.RATE_FP_GFLOP_P_S, MN.COVERAGE_PCT, [])

    # def notify(self, data):
    #     # Metrics to be displayed in the data table are unique for each plot
    #     metrics = self.analyzerData.df.columns.tolist()
    #     super().setup(metrics)

    def update_plot(self):
        return super().update_plot().setData(self.analyzerData.capacityDataItems)

    def mk_plot(self):
        return CustomPlot(self.analyzerData.capacityDataItems, self.analyzerData.levelData, self.analyzerData.level, 'ORIG', 'test', self.analyzerData.scale, 'Custom', no_plot=False, gui=True, 
                          x_axis=self.analyzerData.x_axis, y_axis=self.analyzerData.y_axis, 
                          mappings=self.mappings, short_names_path=self.analyzerData.short_names_path)