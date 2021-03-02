import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from argparse import ArgumentParser
#from idlelib.TreeWidget import ScrolledCanvas, FileTreeItem, TreeNode
from pandastable import Table
import pandas as pd
import os
import re
from os.path import expanduser
from analyzer_base import PerLevelGuiState
from summarize import summary_report_df
from summarize import compute_speedup
from capedata import AnalyticsData
from capedata import SummaryData
from capedata import AggregateData
from aggregate_summary import aggregate_runs_df
from compute_transitions import compute_end2end_transitions
import tempfile
import pkg_resources.py2_warn
from web_browser import BrowserFrame
from cefpython3 import cefpython as cef
import sys
from sys import platform
import time
from pathlib import Path
from pywebcopy import WebPage, config
import shutil
import multiprocessing
import logging
import copy
import operator
#from generate_QPlot import compute_capacity
import pickle
from datetime import datetime
from transitions.extensions import GraphMachine as Machine
from transitions import State
from metric_names import MetricName
from explorer_panel import ExplorerPanel
from utils import center, Observable, resource_path
from summary import CoverageData, SummaryTab
from trawl import TRAWLData, TrawlTab
from qplot import QPlotData, QPlotTab
from si import SIPlotData, SIPlotTab
from custom import CustomData, CustomTab
from plot_3d import Data3d, Tab3d
from scurve import ScurveData, ScurveTab
from scurve_all import ScurveAllData, ScurveAllTab
from meta_tabs import ShortNameTab, LabelTab, VariantTab, AxesTab, MappingsTab, GuideTab, ClusterTab, FilteringTab
from plot_interaction import PlotInteraction
from capeplot import CapeData
from capeplot import CapacityData
from generate_SI import SiData
from sat_analysis import find_clusters as find_si_clusters
from sat_analysis import SatAnalysisData
from metric_names import NonMetricName, KEY_METRICS, NAME_FILE_METRICS
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

# pywebcopy produces a lot of logging that clouds other useful information
logging.disable(logging.CRITICAL)

class LoadedData(Observable):
        
    class PerLevelData(Observable):
        def __init__(self, level):
            super().__init__()
            self.level = level
            self.df = pd.DataFrame(columns=KEY_METRICS)
            self.capacityData = None
            self.satAnalysisData = None
            self.siData = None 
            self.mapping = pd.DataFrame()
            # Put this here but may move it out.
            self.guiState = PerLevelGuiState(self, level)
            
        def resetStates(self):
            self.df.drop(columns=self.df.columns, inplace=True)
            for col in KEY_METRICS:
                self.df[col] = None
            self.mapping = pd.DataFrame()

        # Invoke this method after updating this object (and underlying objects like 
        # GUI state)
        def updated(self):
            self.notify_observers() 

    #CHOSEN_NODE_SET = set(['L1','L2','L3','RAM','FLOP','VR','FE'])
    # Need to get all nodes as SatAnalysis will try to add any nodes in ALL_NODE_SET
    CHOSEN_NODE_SET = CapacityData.ALL_NODE_SET
    def __init__(self):
        super().__init__()
        self.allLevels = ['Codelet',  'Source', 'Application']
        self.levelData = { lvl : LoadedData.PerLevelData(lvl) for lvl in self.allLevels }
        self.data_items=[]
        self.sources=[]
        self.source_order=[]
        self.common_columns_start = [NAME, SHORT_NAME, COVERAGE_PCT, TIME_APP_S, TIME_LOOP_S, MetricName.CAP_FP_GFLOP_P_S, COUNT_OPS_FMA_PCT, COUNT_INSTS_FMA_PCT, VARIANT, MEM_LEVEL]
        self.common_columns_end = [RATE_INST_GI_P_S, TIMESTAMP, 'Color']
        self.analytic_columns = []
        self.mappings = pd.DataFrame()
        self.mapping = pd.DataFrame()
        self.src_mapping = pd.DataFrame()
        self.app_mapping = pd.DataFrame()
        self.analytics = pd.DataFrame()
        self.names = pd.DataFrame()
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.short_names_path = os.path.join(self.cape_path, 'short_names.csv')
        self.mappings_path = os.path.join(self.cape_path, 'mappings.csv')
        self.analysis_results_path = os.path.join(self.cape_path, 'Analysis Results')
        self.check_cape_paths()
        self.resetStates()
        self.data = {}
        self.restore = False
        self.removedIntermediates = False
        self.transitions = 'disabled'

    def get_df(self, level):
        return self.levelData[level].df

    def get_mapping(self, level):
        return self.levelData[level].mapping

    def remove_mapping(self, level, toRemove):
        self.levelData[level].guiState.remove_mapping(toRemove)

    def add_mapping(self, level, toAdd):
        self.levelData[level].guiState.add_mapping(toAdd)
    
    def check_cape_paths(self):
        if not os.path.isfile(self.short_names_path):
            Path(self.cape_path).mkdir(parents=True, exist_ok=True)
            #open(self.short_names_path, 'wb') 
            pd.DataFrame(columns=KEY_METRICS+NAME_FILE_METRICS+ ['Color']).to_csv(self.short_names_path, index=False)
        if not os.path.isfile(self.mappings_path):
            open(self.mappings_path, 'wb')
            pd.DataFrame(columns=['Before Name', 'Before Timestamp', 'After Name', 'After Timestamp', 'Before Variant', 'After Variant', SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']).to_csv(self.mappings_path, index=False)
        if not os.path.isdir(self.analysis_results_path):
            Path(self.analysis_results_path).mkdir(parents=True, exist_ok=True)

    def meta_filename(self, ext):
        data_dir = self.data_dir
        # data_dir is timestamped directory /path/to/datafile/<timestamp>
        # so dropped <timesampt> will get back datafile 
        datafile = os.path.basename(os.path.dirname(data_dir))
        return os.path.join(data_dir, re.sub(r'\.xlsx$|\.raw\.csv$', '', datafile)+ext)
        
    def set_meta_data(self):
        data_dir = self.data_dir
        if not data_dir:
            return
        datafile = os.path.basename(os.path.dirname(data_dir))
        shortnamefile = self.meta_filename('.names.csv')
        names = pd.read_csv(shortnamefile) if os.path.isfile(shortnamefile) else pd.DataFrame(columns=KEY_METRICS + NAME_FILE_METRICS)
        short_names_db = pd.read_csv(self.short_names_path) if os.path.isfile(self.short_names_path) else pd.DataFrame(columns=KEY_METRICS + NAME_FILE_METRICS)
        # Only add entries not already in short_names_db
        merged = pd.merge(left=short_names_db, right=names, on=KEY_METRICS, how='outer')
        updated = False
        for n in NAME_FILE_METRICS:
            need_update = merged[n+'_x'].isna()  
            merged.loc[need_update, n+'_x'] = merged.loc[need_update, n+'_y']
            updated = updated | need_update

        if updated.any():
            # For key metrics, move them as is
            for n in KEY_METRICS:
                short_names_db[n] = merged[n]
            # For short name metrics, move the merged metrics *_x to db
            for n in NAME_FILE_METRICS:
                short_names_db[n] = merged[n+'_x']
            short_names_db.to_csv(self.short_names_path, index=False)

        # self.analytics = pd.DataFrame()
        # for name in os.listdir(data_dir):
        #     local_path = os.path.join(data_dir, name)
        #     if name.endswith('.names.csv'): 
        #         self.names = pd.read_csv(local_path)
        #         self.names.rename(columns={'name':NAME, 'timestamp#':TIMESTAMP, \
        #             'short_name':SHORT_NAME, 'variant':VARIANT}, inplace=True)
        #     # elif name.endswith('.mapping.csv'): self.mapping = pd.read_csv(local_path)
        #     elif name.endswith('.analytics.csv'): 
        #         # TODO: Ask for naming in analytics to conform to naming convention
        #         self.analytics = pd.read_csv(local_path)
    
    # TODO: remove this property
    @property
    def summaryDf(self):
        return self.get_df('Codelet')

    def resetStates(self):
        # Track points/labels that have been hidden/highlighted by the user
        self.c_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.s_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.a_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        for level in self.allLevels:
            self.levelData[level].resetStates()

    def resetTabValues(self):
        #self.tabs = [gui.c_qplotTab, gui.c_trawlTab, gui.c_customTab, gui.c_siPlotTab, gui.summaryTab, \
        #             gui.c_scurveTab, gui.c_scurveAllTab, \
        #        gui.s_qplotTab,  gui.s_trawlTab, gui.s_customTab, \
        #        gui.a_qplotTab, gui.a_trawlTab, gui.a_customTab]
        self.tabs = [gui.c_qplotTab, gui.c_trawlTab, gui.c_customTab, gui.c_siPlotTab, gui.summaryTab, \
                     gui.c_scurveAllTab, \
                gui.s_qplotTab,  gui.s_trawlTab, gui.s_customTab, \
                gui.a_qplotTab, gui.a_trawlTab, gui.a_customTab]
        for tab in self.tabs:
            tab.x_scale = tab.orig_x_scale
            tab.y_scale = tab.orig_y_scale
            tab.x_axis = tab.orig_x_axis
            tab.y_axis = tab.orig_y_axis
            tab.variants = [gui.loadedData.default_variant] #TODO: edit this out
            tab.current_labels = []
        # Reset cluster var for SIPlotData so find_si_clusters() is called again 
        gui.c_siplotData.run_cluster = True

    def add_data(self, sources, data_dir='', update=False):
        self.restore = False
        if not update: self.resetStates() # Clear hidden/highlighted points from previous plots (Do we want to do this if appending data?)        
        dfs = { n : pd.DataFrame(columns = KEY_METRICS) for n in self.allLevels }
        summaryDf = dfs['Codelet']
        srcDf = dfs['Source']
        appDf = dfs['Application']
        # NOTE: sources is a list of loaded file and the last one is to be loaded
        # data_dir is the data directory of the last one which is to be loaded
        self.sources = sources
        last_source = sources[-1]  # Get the last source to be loaded
        self.data_dir = data_dir

        # Add meta data from the timestamp directory.  Will read short names to global database
        self.set_meta_data()

        # Get path to short name database
        short_names_path = self.short_names_path if os.path.isfile(self.short_names_path) else None
        CapeData.set_cache_dir(self.data_dir)
        SummaryData(summaryDf).set_sources([last_source]).set_short_names_path(short_names_path).compute('summary-Codelet')
        AnalyticsData(summaryDf).set_filename(self.meta_filename('.analytics.csv')).compute()
        AggregateData(srcDf).set_summary_df(summaryDf).set_level('src').set_short_names_path(short_names_path).compute('summary-Source')
        AggregateData(appDf).set_summary_df(summaryDf).set_level('app').set_short_names_path(short_names_path).compute('summary-Application')

        # TODO: Append other levels?
        self.names = summaryDf[KEY_METRICS+NAME_FILE_METRICS]

        # Add short names to cape short names file
        #if not self.names.empty:
        #    ShortNameTab.addShortNames(self.names)

        # TODO: get rid of special handling of VARIANT
        # Add variants from namesDf to summaryDf and mapping file if it exists
        # if not self.names.empty: self.add_variants(self.names)
        # Store all unique variants for variant tab options
        self.all_variants = summaryDf[VARIANT].dropna().unique()
        # Get default variant (most frequent)
        self.default_variant = summaryDf[VARIANT].value_counts().idxmax()

        # Reset tab axis metrics/scale to default values (Do we want to do this if appending data?)
        if not update: self.resetTabValues() 
        # if not self.mapping.empty: self.mapping = compute_speedup(self.summaryDf, self.mapping)
        # Add diagnostic variables from analyticsDf
        self.common_columns_end = [RATE_INST_GI_P_S, TIMESTAMP, 'Color']
        #if not self.analytics.empty: self.add_analytics(self.analytics)

        # Add speedups to the corresponding df at each level
        # if not self.mapping.empty: 
        #     self.add_speedup(self.mapping, self.get_df('Codelet'))
        #     self.orig_mapping = self.mapping.copy(deep=True) # Used to restore original mappings after viewing end2end
        
        # Add short names to each master dataframe TODO: Check if this is already happening in the summary df generators
        # chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        #chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]','VR [GB/s]','FE'])
        # CapeData.set_cache_dir(self.data_dir)
        for level in self.levelData:
            levelData = self.levelData[level]
            df = dfs[level]
            df = self.compute_colors(df)
            # self.addShortNames(level)
            # df[MetricName.CAP_FP_GFLOP_P_S] = df[RATE_FP_GFLOP_P_S]
            levelData.capacityData = CapacityData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'capacity-{level}')
            levelData.satAnalysisData = SatAnalysisData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'sat_analysis-{level}')
            cluster_df = levelData.satAnalysisData.cluster_df
            CapacityData(cluster_df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'cluster-{level}') 
            levelData.siData = SiData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET)\
                .set_norm("row").set_cluster_df(cluster_df).compute(f'si-{level}')
            LoadedData.append_df(self.get_df(level), df)
            # Add mappings to levelData for each level
            self.loadMapping(level)

        # self.mappings = {'Codelet' : self.mapping, 'Source' : self.src_mapping, 'Application' : self.app_mapping}
        self.notify_observers()


    @staticmethod
    def append_df(df, append_df):
        merged = df.append(append_df, ignore_index=True)
        df.drop(columns=df.columns, inplace=True)
        for col in merged.columns:
            df[col] = merged[col]
    
    def add_saved_data(self, levels=[]):
        gui.oneviewTab.removePages()
        gui.loaded_url = None
        self.resetStates()
        self.levels = {'Codelet' : levels[0], 'Source' : levels[1], 'Application' : levels[2]}
        self.summaryDf = self.levels['Codelet']['summary']
        self.srcDf = self.levels['Source']['summary']
        self.appDf = self.levels['Application']['summary']
        self.mapping = self.levels['Codelet']['mapping']
        self.src_mapping = self.levels['Source']['mapping']
        self.app_mapping = self.levels['Application']['mapping']
        # Get default variant (most frequent)
        self.default_variant = [self.summaryDf[VARIANT].value_counts().idxmax()]
        self.resetTabValues()
        self.analytics = pd.DataFrame()
        self.sources = []
        self.restore = True
        # Notify the data for all the plots with the saved data 
        for level in self.levels:
            for observer in self.observers:
                if observer.name in self.levels[level]['data']:
                    observer.notify(self, x_axis=self.levels[level]['data'][observer.name]['x_axis'], y_axis=self.levels[level]['data'][observer.name]['y_axis'], \
                        scale=self.levels[level]['data'][observer.name]['x_scale'] + self.levels[level]['data'][observer.name]['y_scale'], level=level, mappings=self.levels[level]['mapping'])
    
    def add_variants(self, namesDf):
        self.summaryDf.drop(columns=[VARIANT], inplace=True)
        namesDf.rename(columns={'name':NAME, 'timestamp':TIMESTAMP, 'timestamp#':TIMESTAMP, 'short_name':SHORT_NAME}, inplace=True)
        self.summaryDf = pd.merge(left=self.summaryDf, right=namesDf[[NAME, VARIANT, TIMESTAMP]], on=[NAME, TIMESTAMP], how='left')

    def add_analytics(self, analyticsDf):
        analyticsDf.rename(columns={'name':NAME, 'timestamp':TIMESTAMP, 'timestamp#':TIMESTAMP}, inplace=True)
        self.summaryDf = pd.merge(left=self.summaryDf, right=analyticsDf, on=[NAME, TIMESTAMP], how='left')
        self.summaryDf.rename(columns={'ArrayEfficiency_%_x':'ArrayEfficiency_%'}, inplace=True)
        self.analytics.drop(columns=[NAME, TIMESTAMP], inplace=True)
        self.analytic_columns = self.analytics.columns.tolist()
        self.common_columns_end.extend(self.analytics.columns)

    def add_speedup(self, mappings, df):
        if mappings.empty or df.empty:
            return
        speedup_time = []
        speedup_apptime = []
        speedup_gflop = []
        for i in df.index:
            row = mappings.loc[(mappings['Before Name']==df['Name'][i]) & (mappings['Before Timestamp']==df['Timestamp#'][i])]
            speedup_time.append(row[SPEEDUP_TIME_LOOP_S].iloc[0] if not row.empty else 1)
            speedup_apptime.append(row[SPEEDUP_TIME_APP_S].iloc[0] if not row.empty else 1)
            speedup_gflop.append(row[SPEEDUP_RATE_FP_GFLOP_P_S].iloc[0] if not row.empty else 1)
        speedup_metric = [(speedup_time, SPEEDUP_TIME_LOOP_S), (speedup_apptime, SPEEDUP_TIME_APP_S), (speedup_gflop, SPEEDUP_RATE_FP_GFLOP_P_S)]
        for pair in speedup_metric:
            df[pair[1]] = pair[0]

    def get_speedups(self, level, mappings):
        mappings = compute_speedup(self.get_df(level), mappings)
        return mappings
    
    def get_end2end(self, mappings, metric=SPEEDUP_RATE_FP_GFLOP_P_S):
        newMappings = compute_end2end_transitions(mappings, metric)
        newMappings['Before Timestamp'] = newMappings['Before Timestamp'].astype(int)
        newMappings['After Timestamp'] = newMappings['After Timestamp'].astype(int)
        self.add_speedup(newMappings, self.summaryDf)
        return newMappings
    
    def cancelAction(self):
        # If user quits the window we set a default before/after order
        self.source_order = list(self.summaryDf['Timestamp#'].unique())
        self.win.destroy()

    def orderAction(self, button, ts):
        self.source_order.append(ts)
        button.destroy()
        if len(self.source_order) == len(self.sources):
            self.win.destroy()

    def get_order(self):
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
        self.win.title('Order Data')
        message = 'Select the order of data files from oldest to newest'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        # Need to link the datafile name with the timestamp
        for index, source in enumerate(self.sources):
            expr_summ_df = pd.read_excel(source, sheet_name='Experiment_Summary')
            ts_row = expr_summ_df[expr_summ_df.iloc[:,0]=='Timestamp']
            ts_string = ts_row.iloc[0,1]
            date_time_obj = datetime.strptime(ts_string, '%Y-%m-%d %H:%M:%S')
            ts = int(date_time_obj.timestamp())
            path, source_file = os.path.split(source)
            b = tk.Button(self.win, text=source_file.split('.')[0])
            b['command'] = lambda b=b, ts=ts : self.orderAction(b, ts) 
            b.grid(row=index+1, column=1, padx=20, pady=10)
        root.wait_window(self.win)

    def compute_colors(self, df, clusters=False):
        colors = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple', 'cyan', 'lime', 'grey', 'brown', 'salmon', 'gold', 'slateblue']
        colorDf = pd.DataFrame() 
        timestamps = df['Timestamp#'].dropna().unique()
        # Get saved color column from short names file
        if not clusters and os.path.getsize(self.short_names_path) > 0:
            all_short_names = pd.read_csv(self.short_names_path)
            df.drop(columns=['Color'], inplace=True, errors='ignore')
            df = pd.merge(left=df, right=all_short_names[KEY_METRICS + ['Color']], on=KEY_METRICS, how='left')
            toAdd = df[df['Color'].notnull()]
            colorDf = colorDf.append(toAdd, ignore_index=True)
        elif clusters:
            toAdd = df[df['Color'] != '']
            colorDf = colorDf.append(toAdd, ignore_index=True)
        # Group data by timestamps if less than 2
        #TODO: This is a quick fix for getting multiple colors for whole files, use design doc specs in future
        if (self.source_order) or (len(self.sources) > 1 and len(timestamps) <= 2):
            if self.source_order: timestamps = self.source_order
            for index, timestamp in enumerate(timestamps):
                curDf = df.loc[(df['Timestamp#']==timestamp)]
                curDf = curDf[curDf['Color'].isna()]
                curDf['Color'] = colors[index]
                colorDf = colorDf.append(curDf, ignore_index=True)
        elif clusters:
            toAdd = df[df['Color'] == '']
            toAdd['Color'] = colors[0]
            colorDf = colorDf.append(toAdd, ignore_index=True)
        else:
            toAdd = df[df['Color'].isna()]
            toAdd['Color'] = colors[0]
            colorDf = colorDf.append(toAdd, ignore_index=True)
        return colorDf

    def loadMapping(self, level):
        df = self.get_df(level)
        all_mappings = pd.read_csv(self.mappings_path)
        before = pd.merge(left=df[KEY_METRICS], right=all_mappings, left_on=KEY_METRICS, right_on=['Before Name', 'Before Timestamp'], how='inner').drop(columns=KEY_METRICS)
        mappings = pd.merge(left=df[KEY_METRICS], right=before, left_on=KEY_METRICS, right_on=['After Name', 'After Timestamp'], how='inner').drop(columns=KEY_METRICS)
        if mappings.empty:
            mappings = pd.DataFrame(columns=['Before Timestamp', 'Before Name', 'After Timestamp', 'After Name', 'Difference'])
            mappings = mappings.append(pd.Series(name='temp'))
        self.get_speedups(level, mappings)
        # self.add_speedup(self.mapping, self.get_df('Codelet'))
        self.levelData[level].mapping = mappings

    def createMappings(self, df):
        mappings = pd.DataFrame()
        df['map_name'] = df['Name'].map(lambda x: x.split(' ')[1].split(',')[-1].split('_')[-1])
        before = df.loc[df['Timestamp#'] == self.source_order[0]]
        after = df.loc[df['Timestamp#'] == self.source_order[1]]
        for index in before.index:
            match = after.loc[after['map_name'] == before['map_name'][index]].reset_index(drop=True) 
            if not match.empty:
                match = match.iloc[[0]]
                match['Before Timestamp'] = before['Timestamp#'][index]
                match['Before Name'] = before['Name'][index]
                match['before_short_name'] = before['Short Name'][index]
                match['After Timestamp'] = match['Timestamp#']
                match['After Name'] = match['Name']
                match['after_short_name'] = match['Short Name']
                match = match[['Before Timestamp', 'Before Name', 'before_short_name', 'After Timestamp', 'After Name', 'after_short_name']]
                mappings = mappings.append(match, ignore_index=True)
        if not mappings.empty:
            mappings = self.get_speedups(mappings)
            self.all_mappings = self.all_mappings.append(mappings, ignore_index=True)
            self.all_mappings.to_csv(self.mappings_path, index=False)
        return mappings

    def addShortNames(self, level):
        all_short_names = pd.read_csv(self.short_names_path)
        self.merge_metrics(all_short_names, [SHORT_NAME, 'Color'], level)

    def merge_metrics(self, df, metrics, level):
        # Add metrics computed in plot functions to master dataframe
        metrics.extend(KEY_METRICS)
        #target_df = self.dfs[level]
        target_df = self.get_df(level)
        merged = pd.merge(left=target_df, right=df[metrics], on=KEY_METRICS, how='left')
        target_df.sort_values(by=NAME, inplace=True)
        target_df.reset_index(drop=True, inplace=True)
        merged.sort_values(by=NAME, inplace=True)
        merged.reset_index(drop=True, inplace=True)
        for metric in metrics:
            if metric + "_y" in merged.columns and metric + "_x" in merged.columns:
                merged[metric] = merged[metric + "_y"].fillna(merged[metric + "_x"])
            if metric not in KEY_METRICS: target_df[metric] = merged[metric]

class CodeletTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class ApplicationTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class SourceTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class OneviewTab(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # Oneview tab has a paned window to handle simultaneous HTML viewing
        self.window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)
        self.browser1 = None
        self.browser2 = None
        self.refreshButton = None

    def refresh(self):
        if self.browser1: self.browser1.refresh()
        if self.browser2: self.browser2.refresh()

    def addRefresh(self):
        self.refreshButton = tk.Button(self.window, text="Refresh", command=self.refresh)
        self.refreshButton.pack(side=tk.TOP, anchor=tk.NW)

    def loadPage(self):
        if len(gui.urls) == 1: self.loadFirstPage()
        elif len(gui.urls) > 1: self.loadSecondPage()
    
    def loadFirstPage(self):
        self.removePages()
        self.browser1 = BrowserFrame(self.window)
        self.window.add(self.browser1, stretch='always')
        self.addRefresh()
        current_tab = gui.main_note.select()
        gui.main_note.select(0)
        self.update()
        gui.main_note.select(current_tab)
        self.browser1.change_browser(url=gui.urls[0])

    def loadSecondPage(self):
        self.removePages()
        self.browser1 = BrowserFrame(self.window)
        self.browser2 = BrowserFrame(self.window)
        self.window.add(self.browser1, stretch='always')
        self.window.add(self.browser2, stretch='always')
        self.addRefresh()
        current_tab = gui.main_note.select()
        gui.main_note.select(0)
        self.update()
        gui.main_note.select(current_tab)
        self.browser1.change_browser(url=gui.urls[0])
        self.browser2.change_browser(url=gui.urls[1])

    def removePages(self):
        if self.browser1: 
            self.window.remove(self.browser1)
            self.refreshButton.destroy()
        if self.browser2: self.window.remove(self.browser2)

class AnalyzerGui(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.loadedData = LoadedData()

        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")#, command=self.configTab.new)
        filemenu.add_command(label="Open")#, command=self.configTab.open)
        filemenu.add_command(label="Save")#, command=lambda: self.configTab.save(False))
        filemenu.add_command(label="Save As...")#, command=lambda: self.configTab.save(True))
        filemenu.add_separator()
        filemenu.add_command(label="Exit")#, command=self.file_exit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        self.parent.config(menu=menubar)

        self.pw=tk.PanedWindow(parent, orient="vertical", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)

        right = self.buildTabs(self.pw)
        right.pack(side = tk.TOP, fill=tk.BOTH, expand=True)
        self.pw.add(right, stretch='always')

        self.explorerPanel = ExplorerPanel(self.pw, self.loadFile, self.loadSavedState, self, root)
        self.explorerPanel.pack(side = tk.BOTTOM)
        self.pw.add(self.explorerPanel, stretch='never')

        self.pw.pack(fill=tk.BOTH, expand=True)
        self.pw.configure(sashrelief=tk.RAISED)
        self.sources = []
        self.urls = []
        self.loaded_url = None
        self.loadType = ''
        self.choice = ''

    def appendData(self):
        self.choice = 'Append'
        self.win.destroy()

    def overwriteData(self):
        self.choice = 'Overwrite'
        self.win.destroy()

    def cancelAction(self):
        self.choice = 'Cancel'
        self.win.destroy()

    def appendAnalysisData(self, df, mappings, analytics, data):
        # need to combine df with current summaryDf
        self.loadedData.summaryDf = pd.concat([self.loadedData.summaryDf, df]).drop_duplicates(keep='last').reset_index(drop=True)
        # need to combine mappings with current mappings and add speedups
        
    def loadSavedState(self, levels=[]):
        print("restore: ", self.loadedData.restore)
        if len(self.sources) >= 1:
            self.win = tk.Toplevel()
            center(self.win)
            self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
            self.win.title('Existing Data')
            message = 'This tool currently doesn\'t support appending server data with\nAnalysis Results data. Would you like to overwrite\nany existing plots with this new data?'
            #if not self.loadedData.restore: message = 'This tool currently doesn\'t support appending server data with\nAnalysis Results data. Would you like to overwrite\nany existing plots with this new data?'
            #else: 
                #message = 'Would you like to append to the existing\ndata or overwrite with the new data?'
                #tk.Button(self.win, text='Append', command= lambda df=df, mappings=mappings, analytics=analytics, data=data : self.appendAnalysisData(df, mappings, analytics, data)).grid(row=1, column=0, sticky=tk.E)
            tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
            tk.Button(self.win, text='Overwrite', command=self.overwriteData).grid(row=1, column=1)
            tk.Button(self.win, text='Cancel', command=self.cancelAction).grid(row=1, column=2, pady=10, sticky=tk.W)
            root.wait_window(self.win)
        if self.choice == 'Cancel': return
        self.source_order = []
        self.sources = ['Analysis Result'] # Don't need the actual source path for Analysis Results
        self.loadedData.add_saved_data(levels)

    def loadFile(self, choice, data_dir, source, url):
        if choice == 'Open Webpage':
            self.overwrite()
            self.urls = [url]
            if sys.platform != 'darwin':
                self.oneviewTab.loadPage()
            return
        elif choice == 'Overwrite':
            self.overwrite()
            if url: 
                self.urls = [url]
                if sys.platform != 'darwin':
                    self.oneviewTab.loadPage()
            self.sources = [source]
            self.loadedData.add_data(self.sources, data_dir, update=False)
        elif choice == 'Append':
            if url: 
                self.urls.append(url)
                if sys.platform != 'darwin':
                    self.oneviewTab.loadPage()
            self.sources.append(source)
            self.loadedData.add_data(self.sources, data_dir, update=True)

    def overwrite(self): # Clear out any previous saved dataframes/plots
        self.sources = []
        gui.loadedData.analytics = pd.DataFrame()
        gui.loadedData.mapping = pd.DataFrame()
        gui.loadedData.names = pd.DataFrame()
        gui.oneviewTab.removePages() # Remove any previous OV HTML
        # Clear summary dataframes
        for level in self.loadedData.levelData:
            self.loadedData.levelData[level].df = pd.DataFrame()
        self.clearTabs()

    def clearTabs(self, levels=['All']):
        tabs = []
        if 'Codelet' in levels or 'All' in levels:
            tabs.extend([gui.summaryTab, gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab, gui.c_scurveAllTab])
            # tabs.extend([gui.summaryTab, gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab, gui.c_scurveTab, gui.c_scurveAllTab])
        if 'Source' in levels or 'All' in levels:
            tabs.extend([gui.s_trawlTab, gui.s_qplotTab, gui.s_customTab])
        if 'Application' in levels or 'All' in levels:
            tabs.extend([gui.a_trawlTab, gui.a_qplotTab, gui.a_customTab])
        for tab in tabs:
            for widget in tab.window.winfo_children():
                widget.destroy()

    def buildTabs(self, parent):
        infoPw=tk.PanedWindow(parent, orient="horizontal", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        # Oneview (Left Window)
        self.oneview_note = ttk.Notebook(infoPw)
        self.oneviewTab = OneviewTab(self.oneview_note)
        self.oneview_note.add(self.oneviewTab, text="Oneview")
        self.oneview_note.pack(side = tk.LEFT, expand=True)
        infoPw.add(self.oneview_note, stretch='always')
        # Plots (Right Window)
        self.main_note = ttk.Notebook(infoPw)
        self.applicationTab = ApplicationTab(self.main_note)
        self.sourceTab = SourceTab(self.main_note)
        self.codeletTab = CodeletTab(self.main_note)
        self.coverageData = CoverageData(self.loadedData, self, root, 'Codelet')
        self.summaryTab = SummaryTab(self.main_note, self.coverageData)
        self.main_note.add(self.summaryTab, text='Summary')
        self.main_note.add(self.applicationTab, text='Application')
        self.main_note.add(self.sourceTab, text='Source')
        self.main_note.add(self.codeletTab, text='Codelet')
        # Each level has its own plot tabs
        application_note = ttk.Notebook(self.applicationTab)
        source_note = ttk.Notebook(self.sourceTab)
        codelet_note = ttk.Notebook(self.codeletTab)
        # Codelet Plot Data
        self.c_siplotData = SIPlotData(self.loadedData, self, root, 'Codelet')
        self.c_qplotData = QPlotData(self.loadedData, self, root, 'Codelet')
        self.c_trawlData = TRAWLData(self.loadedData, self, root, 'Codelet')
        self.c_customData = CustomData(self.loadedData, self, root, 'Codelet')
        self.c_3dData = Data3d(self.loadedData, self, root, 'Codelet')
        # binned scurve break datapoint selection because of different text:marker map
        # Disable for now as not used.  
        # To enable, need to compute text:marker to-and-from regular text:marker to binned text:marker
        # self.c_scurveData = ScurveData(self.loadedData, self, root, 'Codelet')
        self.c_scurveAllData = ScurveAllData(self.loadedData, self, root, 'Codelet')
        # Codelet Plot Tabs
        self.c_siPlotTab = SIPlotTab(codelet_note, self.c_siplotData)
        self.c_qplotTab = QPlotTab(codelet_note, self.c_qplotData)
        self.c_trawlTab = TrawlTab(codelet_note, self.c_trawlData)
        self.c_customTab = CustomTab(codelet_note, self.c_customData)
        self.c_3dTab = Tab3d(codelet_note, self.c_3dData)
        # self.c_scurveTab = ScurveTab(codelet_note, self.c_scurveData)
        self.c_scurveAllTab = ScurveAllTab(codelet_note, self.c_scurveAllData)
        codelet_note.add(self.c_trawlTab, text='TRAWL')
        codelet_note.add(self.c_qplotTab, text='QPlot')
        codelet_note.add(self.c_siPlotTab, text='SI Plot')
        codelet_note.add(self.c_customTab, text='Custom')
        codelet_note.add(self.c_3dTab, text='3D')
        # codelet_note.add(self.c_scurveTab, text='S-Curve (Bins)')
        codelet_note.add(self.c_scurveAllTab, text='S-Curve')
        codelet_note.pack(fill=tk.BOTH, expand=True)
        # Source Plot Data
        self.s_qplotData = QPlotData(self.loadedData, self, root, 'Source')
        self.s_trawlData = TRAWLData(self.loadedData, self, root, 'Source')
        self.s_customData = CustomData(self.loadedData, self, root, 'Source')
        # Source Plot Tabs
        self.s_trawlTab = TrawlTab(source_note, self.s_trawlData)
        self.s_qplotTab = QPlotTab(source_note, self.s_qplotData)
        self.s_customTab = CustomTab(source_note, self.s_customData)
        source_note.add(self.s_trawlTab, text='TRAWL')
        source_note.add(self.s_qplotTab, text='QPlot')
        source_note.add(self.s_customTab, text='Custom')
        source_note.pack(fill=tk.BOTH, expand=True)
        # Application Plot Data
        self.a_qplotData = QPlotData(self.loadedData, self, root, 'Application')
        self.a_trawlData = TRAWLData(self.loadedData, self, root, 'Application')
        self.a_customData = CustomData(self.loadedData, self, root, 'Application')
        # Application Plot Tabs
        self.a_trawlTab = TrawlTab(application_note, self.a_trawlData)
        self.a_qplotTab = QPlotTab(application_note, self.a_qplotData)
        self.a_customTab = CustomTab(application_note, self.a_customData)
        application_note.add(self.a_trawlTab, text='TRAWL')
        application_note.add(self.a_qplotTab, text='QPlot')
        application_note.add(self.a_customTab, text='Custom')
        application_note.pack(fill=tk.BOTH, expand=True)
        self.main_note.pack(side = tk.RIGHT, expand=True)
        infoPw.add(self.main_note, stretch='always')

        return infoPw


def on_closing(root):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.quit()
        root.destroy()

def check_focus(event):
    # Embedded chrome browser takes focus from application
    if root.focus_get() is None:
        root.focus_force()

if __name__ == '__main__':
    parser = ArgumentParser(description='Cape Analyzer')
    global root
    root = tk.Tk()
    root.title("Cape Analyzer")
    root.bind("<Button-1>", check_focus)
    # Set opening window to portion of user's screen wxh
    width  = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry('%sx%s' % (int(width/1.2), int(height/1.2)))
    #root.geometry(f'{width}x{height}')

    # The AnalyzerGui is global so that the data source panel can access it
    global gui
    gui = AnalyzerGui(root)

    # Allow pyinstaller to find all CEFPython binaries
    # TODO: Add handling of framework nad resource paths for Mac
    if getattr(sys, 'frozen', False):
        if sys.platform == 'darwin':
            appSettings = {
                'cache_path': tempfile.gettempdir(),
                'resources_dir_path': os.path.join(expanduser('~'), 'Documents', 'Development', 'env', 'lib', 'python3.7', 'site-packages', 'cefpython3', 'Chromium Embedded Framework.framework', 'Resources'),
                'framework_dir_path': os.path.join(expanduser('~'), 'Documents', 'Development', 'env', 'lib', 'python3.7', 'site-packages', 'cefpython3', 'Chromium Embedded Framework.framework'),
                'browser_subprocess_path': os.path.join(sys._MEIPASS, 'subprocess.exe')
            }
        else:
            appSettings = {
            'cache_path': tempfile.gettempdir(),
            'resources_dir_path': sys._MEIPASS,
            'locales_dir_path': os.path.join(sys._MEIPASS, 'locales'),
            'browser_subprocess_path': os.path.join(sys._MEIPASS, 'subprocess.exe')
        }
    else:
        appSettings = {
            'cache_path': tempfile.gettempdir()
        }
    cef.Initialize(appSettings)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()
    cef.Shutdown()
