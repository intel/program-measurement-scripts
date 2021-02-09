import tkinter as tk
from utils import Observable, resource_path
from analyzer_base import AnalyzerTab, AnalyzerData
import pandas as pd
from generate_SI import parse_ip_df as parse_ip_siplot_df
import copy
import os
import pickle
from tkinter import ttk
from plot_interaction import PlotInteraction
from pandastable import Table
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, ClusterTab, FilteringTab, DataTab
from metric_names import MetricName
from metric_names import NonMetricName
from sat_analysis import find_clusters as find_si_clusters
globals().update(MetricName.__members__)

class SIPlotData(AnalyzerData):
    def __init__(self, loadedData, gui, root, level):
        super().__init__(loadedData, gui, root, level, 'SIPlot')
        self.run_cluster = True

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=[], update=False, cluster=resource_path(os.path.join('clusters', 'FE_tier1.csv')), title="FE_tier1", \
        filtering=False, filter_data=None, scale='linear', level='All', mappings=pd.DataFrame()):
        print("SIPlotData Notified from ", loadedData)
        super().notify(loadedData, update, variants, mappings)
        # Generate Plot
        chosen_node_set = set(['RAM [GB/s]','L2 [GB/s]','FE','FLOP [GFlop/s]','L1 [GB/s]','VR [GB/s]','L3 [GB/s]'])
        if self.run_cluster:
            self.cluster_df = pd.DataFrame()
            self.si_df = pd.DataFrame()
            # cluster_dest = os.path.join(loadedData.data_dir, 'cluster_df.pkl')
            # si_dest = os.path.join(loadedData.data_dir, 'si_df.pkl')
            # Check to see if we can use cached cluster and si dataframes
            # for name in os.listdir(loadedData.data_dir):
            #     if name.endswith('cluster_df.pkl'):
            #         data = open(cluster_dest, 'rb') 
            #         self.cluster_df = pickle.load(data)
            #         data.close()
            #     elif name.endswith('si_df.pkl'): 
            #         data = open(si_dest, 'rb') 
            #         self.si_df = pickle.load(data)
            #         data.close()
            # if self.cluster_df.empty or self.si_df.empty:
            #     self.cluster_df, self.si_df = find_si_clusters(loadedData.dfs[self.level])
            #     data = open(cluster_dest, 'wb')
            #     pickle.dump(self.cluster_df, data)
            #     data.close()
            #     data = open(si_dest, 'wb')
            #     pickle.dump(self.si_df, data)
            #     data.close()
            cluster_dest = os.path.join(loadedData.data_dir, 'cluster_df.xlsx')
            si_dest = os.path.join(loadedData.data_dir, 'si_df.xlsx')
            for name in os.listdir(loadedData.data_dir):
                if name.endswith('cluster_df.xlsx'):
                    self.cluster_df = pd.read_excel(cluster_dest)
                elif name.endswith('si_df.xlsx'): 
                    self.si_df = pd.read_excel(si_dest)
            if self.cluster_df.empty or self.si_df.empty:
                self.cluster_df, self.si_df = find_si_clusters(loadedData.dfs[self.level])
                self.cluster_df.to_excel(cluster_dest)
                self.si_df.to_excel(si_dest)
            self.run_cluster = False
        new_columns = [NAME, TIMESTAMP, NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES]
        self.df.drop(columns=[NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES], inplace=True, errors='ignore')
        self.df = pd.merge(left=self.df, right=self.si_df[new_columns], how='left', on=[NAME, TIMESTAMP])
        #cluster_df = pd.read_csv(cluster)
        self.df, self.fig, self.textData = parse_ip_siplot_df\
            (self.cluster_df, "FE_tier1", "row", title, chosen_node_set, self.df, variants=self.variants, filtering=filtering, filter_data=filter_data, \
                mappings=self.mappings, scale=scale, short_names_path=self.gui.loadedData.short_names_path)
        # Add new metrics to shared dataframe
        self.loadedData.dfs[self.level].drop(columns=['Saturation', 'Intensity'], inplace=True, errors='ignore')
        self.loadedData.dfs[self.level] = pd.merge(self.loadedData.dfs[self.level], self.df[[NAME, TIMESTAMP, 'Saturation', 'Intensity']], on=[NAME, TIMESTAMP], how='left')
        # TODO: Fix analytic variables being dropped in 'def compute_extra' in generate_SI.py
        if not loadedData.analytics.empty:
            self.df.drop(columns=loadedData.analytic_columns, errors='ignore', inplace=True)
            self.df = pd.merge(left=self.df, right=loadedData.summaryDf[loadedData.analytic_columns + [NAME, TIMESTAMP]], on=[NAME, TIMESTAMP], how='left')
        self.notify_observers()

class SIPlotTab(AnalyzerTab):
    def __init__(self, parent, data):
        super().__init__(parent, data, 'FE_tier1', 'Intensity', 'Saturation',
                         ['Saturation', 'Intensity', 'SI', NonMetricName.SI_CLUSTER_NAME])
        self.cluster = resource_path(os.path.join('clusters', 'FE_tier1.csv'))
    
    # Create meta tabs
    def buildTableTabs(self):
        super().buildTableTabs()
        self.clusterTab = ClusterTab(self.tableNote, self)
        self.filteringTab = FilteringTab(self.tableNote, self)
        self.tableNote.add(self.clusterTab, text='Clusters')
        self.tableNote.add(self.filteringTab, text='Filtering')
        