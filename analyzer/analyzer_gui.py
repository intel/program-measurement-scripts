import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from argparse import ArgumentParser
#from idlelib.TreeWidget import ScrolledCanvas, FileTreeItem, TreeNode
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib
import matplotlib.pyplot as plt
from pandastable import Table
import pandas as pd
import pathlib
import os
import re
from os.path import expanduser
from summarize import summary_report_df
from summarize import compute_speedup
from aggregate_summary import aggregate_runs_df
from compute_transitions import compute_end2end_transitions
from generate_QPlot import parse_ip_df as parse_ip_qplot_df
from generate_SI import parse_ip_df as parse_ip_siplot_df
from generate_coveragePlot import coverage_plot
from generate_TRAWL import trawl_plot
from generate_custom import custom_plot
import tempfile
import pkg_resources.py2_warn
from web_browser import BrowserFrame
from cefpython3 import cefpython as cef
import sys
import requests
from lxml import html
import time
from pathlib import Path
from adjustText import adjust_text
from pywebcopy import WebPage, config
import shutil
import threading
import multiprocessing
import logging
import copy
import operator
from capelib import succinctify
from generate_QPlot import compute_capacity
import pickle
from datetime import datetime

# pywebcopy produces a lot of logging that clouds other useful information
logging.disable(logging.CRITICAL)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

# Simple implementation of Observer Design Pattern
class Observable:
    def __init__(self):
        self.observers = []
    def add_observers(self, observer):
        self.observers.append(observer)
    def notify_observers(self):
        for observer in self.observers:
            observer.notify(self)
            
class Observer:
    def __init__(self, observable):
        observable.add_observers(self)
        
    def notify(self, observable):
        print("Notified from ", observable)

class ScrolledTreePane(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.treeview = ttk.Treeview(self)
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.configure(command=self.treeview.yview)
        hsb.configure(command=self.treeview.xview)
        self.treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.treeview.pack(fill=tk.BOTH, expand=1)  

class LoadedData(Observable):
    def __init__(self):
        super().__init__()
        self.data_items=[]
        self.sources=[]
        self.source_order=[]
        self.common_columns_start = ['name', 'short_name', r'%coverage', 'apptime_s', 'time_s', 'C_FLOP [GFlop/s]', r'%ops[fma]', r'%inst[fma]', 'variant', 'memlevel']
        self.common_columns_end = ['c=inst_rate_gi/s', 'timestamp#', 'color']
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
        self.test_mapping_path = os.path.join(self.cape_path, 'demo_mappins.csv')
        self.test_summary_path = os.path.join(self.cape_path, 'demo_summary.csv')
        self.check_cape_paths()
        self.resetStates()
        self.data = {}
        self.restore = False
        self.removedIntermediates = False
        self.transitions = 'disabled'

    def check_cape_paths(self):
        if not os.path.isfile(self.short_names_path):
            Path(self.cape_path).mkdir(parents=True, exist_ok=True)
            open(self.short_names_path, 'wb') 
            pd.DataFrame(columns=['name', 'short_name', 'timestamp#']).to_csv(self.short_names_path, index=False)
        if not os.path.isfile(self.mappings_path):
            open(self.mappings_path, 'wb')
            pd.DataFrame(columns=['before_name', 'before_timestamp#', 'after_name', 'after_timestamp#', 'Speedup[Time (s)]', 'Speedup[AppTime (s)]', 'Speedup[FLOP Rate (GFLOP/s)]', 'Difference']).to_csv(self.mappings_path, index=False)
        if not os.path.isdir(self.analysis_results_path):
            Path(self.analysis_results_path).mkdir(parents=True, exist_ok=True)

    def set_meta_data(self, data_dir):
        for name in os.listdir(data_dir):
            local_path = os.path.join(data_dir, name)
            if name.endswith('.names.csv'): self.names = pd.read_csv(local_path)
            elif name.endswith('.mapping.csv'): self.mapping = pd.read_csv(local_path)
            elif name.endswith('.analytics.csv'): 
                # TODO: Ask for naming in analytics to be lowercase timestamp
                self.analytics = pd.read_csv(local_path)
                self.analytics.rename(columns={'Timestamp#':'timestamp#'}, inplace=True)
    
    def resetStates(self):
        # Track points/labels that have been hidden/highlighted by the user
        self.c_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.s_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.a_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.srcDf = pd.DataFrame()
        self.appDf = pd.DataFrame()
        self.mapping = pd.DataFrame()
        self.src_mapping = pd.DataFrame()
        self.app_mapping = pd.DataFrame()

    def resetTabValues(self):
        tabs = [gui.c_qplotTab, gui.c_trawlTab, gui.c_customTab, gui.c_siPlotTab, gui.summaryTab]
        for tab in tabs:
            tab.x_scale = tab.orig_x_scale
            tab.y_scale = tab.orig_y_scale
            tab.x_axis = tab.orig_x_axis
            tab.y_axis = tab.orig_y_axis
            tab.current_variants = ['ORIG']
            tab.current_labels = []

    def add_data(self, sources, data_dir='', update=False):
        self.restore = False
        self.resetTabValues() # Reset tab axis metrics/scale to default values (Do we want to do this if appending data?)
        self.resetStates() # Clear hidden/highlighted points from previous plots (Do we want to do this if appending data?)
        self.sources = sources
        # Add meta data from the timestamp directory
        if data_dir: self.set_meta_data(data_dir)
        # Add short names to cape short names file
        if not self.names.empty:
            shortnameTab = ShortNameTab(root)
            shortnameTab.addShortNames(self.names)
        in_files = sources
        in_files_format = [None] * len(sources)
        for index, source in enumerate(sources):
            in_files_format[index] = 'csv' if os.path.splitext(source)[1] == '.csv' else 'xlsx'
        user_op_file = None
        request_no_cqa = False
        request_use_cpi = False
        request_skip_energy = False
        request_skip_stalls = False
        request_succinct = False
        short_names_path = self.short_names_path if os.path.isfile(self.short_names_path) else None
        # Codelet summary
        self.summaryDf, self.mapping = summary_report_df(in_files, in_files_format, user_op_file, request_no_cqa, \
            request_use_cpi, request_skip_energy, request_skip_stalls, request_succinct, short_names_path, \
            False, True, self.mapping)
        # Add variants from namesDf
        if not self.names.empty: self.add_variants(self.names)
        # Add diagnostic variables from analyticsDf
        if not self.analytics.empty: self.add_analytics(self.analytics)
        # Source summary
        self.srcDf, self.src_mapping = aggregate_runs_df(self.summaryDf.copy(deep=True), level='src', name_file=short_names_path, mapping_df=self.mapping)
        #self.srcDf, self.src_mapping = aggregate_runs_df(self.summaryDf.copy(deep=True), level='src', name_file=short_names_path)
        # Application summary
        self.appDf, self.app_mapping = aggregate_runs_df(self.summaryDf.copy(deep=True), level='app', name_file=short_names_path, mapping_df=self.mapping)
        #self.appDf, self.app_mapping = aggregate_runs_df(self.summaryDf.copy(deep=True), level='app', name_file=short_names_path)
        # Add speedups to the corresponding dfs at each level
        if not self.mapping.empty: 
            self.add_speedup(self.mapping, self.summaryDf)
            self.orig_mapping = self.mapping.copy(deep=True) # Used to restore original mappings after viewing end2end
        if not self.src_mapping.empty: self.add_speedup(self.src_mapping, self.srcDf)
        if not self.app_mapping.empty: self.add_speedup(self.app_mapping, self.appDf)
        # Multiple files setup (Currently not using because the mapping generation algorithm isn't good enough)
        if False and len(self.sources) > 1 and not update: # Ask user for the before and after order of the files
            self.source_order = []
            # self.get_order()
            # Check if we have custom mappings stored in the Cape directory
            self.mapping = self.getMappings()
        # Generate color column (Currently doesn't support multiple UIUC files because each file doesn't have a unique timestamp like UVSQ)
        self.summaryDf = self.compute_colors(self.summaryDf)
        self.srcDf = self.compute_colors(self.srcDf)
        self.appDf = self.compute_colors(self.appDf)
        self.notify_observers()

    def add_saved_data(self, df, mappings=pd.DataFrame(), analytics=pd.DataFrame(), data={}):
        gui.oneviewTab.removePages()
        gui.loaded_url = None
        self.resetTabValues()
        self.resetStates()
        self.mappings = pd.DataFrame()
        self.summaryDf = df
        self.mapping = mappings
        if not mappings.empty: self.add_speedup(mappings, self.summaryDf)
        self.data = data
        self.sources = []
        self.restore = True
        # Notify the data for all the plots with the saved data
        for observer in self.observers:
            observer.notify(self, x_axis=data['Codelet'][observer.name]['x_axis'], y_axis=data['Codelet'][observer.name]['y_axis'], \
                scale=data['Codelet'][observer.name]['x_scale'] + data['Codelet'][observer.name]['y_scale'], level='Codelet', mappings=mappings)
            if data['Source']:
                observer.notify(self, x_axis=data['Source'][observer.name]['x_axis'], y_axis=data['Source'][observer.name]['y_axis'], \
                scale=data['Source'][observer.name]['x_scale'] + data['Source'][observer.name]['y_scale'], level='Source', mappings=mappings)
            if data['Application']:
                observer.notify(self, x_axis=data['Application'][observer.name]['x_axis'], y_axis=data['Application'][observer.name]['y_axis'], \
                scale=data['Application'][observer.name]['x_scale'] + data['Application'][observer.name]['y_scale'], level='Application', mappings=mappings)

    def add_variants(self, namesDf):
        namesDf = namesDf.rename(columns={'name':'Name', 'variant':'Variant', 'timestamp#':'Timestamp#'})
        self.summaryDf.drop(columns=['Variant'], inplace=True)
        self.summaryDf = pd.merge(left=self.summaryDf, right=namesDf[['Name', 'Variant', 'Timestamp#']], on=['Name', 'Timestamp#'], how='left')

    def add_analytics(self, analyticsDf):
        analyticsDf = analyticsDf.rename(columns={'name':'Name', 'timestamp#':'Timestamp#'})
        self.summaryDf = pd.merge(left=self.summaryDf, right=analyticsDf, on=['Name', 'Timestamp#'], how='left')

    def add_speedup(self, mappings, df):
        # TODO: Figure out naming convention
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
                                    'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
        speedup_time = []
        speedup_apptime = []
        speedup_gflop = []
        for i in df.index:
            row = mappings.loc[(mappings['before_name']==df['Name'][i]) & (mappings['before_timestamp#']==df['Timestamp#'][i])]
            speedup_time.append(row['Speedup[Time (s)]'].iloc[0] if not row.empty else 1)
            speedup_apptime.append(row['Speedup[AppTime (s)]'].iloc[0] if not row.empty else 1)
            speedup_gflop.append(row['Speedup[FLOP Rate (GFLOP/s)]'].iloc[0] if not row.empty else 1)
        speedup_metric = [(speedup_time, 'Speedup[Time (s)]'), (speedup_apptime, 'Speedup[AppTime (s)]'), (speedup_gflop, 'Speedup[FLOP Rate (GFLOP/s)]')]
        for pair in speedup_metric:
            df[pair[1]] = pair[0]

    def get_speedups(self, mappings):
        mappings.rename(columns={'before_name':'Before Name', 'before_timestamp#':'Before Timestamp', \
                                    'after_name':'After Name', 'after_timestamp#':'After Timestamp'}, inplace=True)
        mappings = compute_speedup(self.summaryDf, mappings)
        mappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
                                    'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
        return mappings
    
    def get_end2end(self, mappings, metric='Speedup[FLOP Rate (GFLOP/s)]'):
        newMappings = mappings.rename(columns={'before_name':'Before Name', 'before_timestamp#':'Before Timestamp', \
                                    'after_name':'After Name', 'after_timestamp#':'After Timestamp'})
        newMappings = compute_end2end_transitions(newMappings, metric)
        newMappings.rename(columns={'Before Name':'before_name', 'Before Timestamp':'before_timestamp#', \
                                    'After Name':'after_name', 'After Timestamp':'after_timestamp#'}, inplace=True)
        newMappings['before_timestamp#'] = newMappings['before_timestamp#'].astype(int)
        newMappings['after_timestamp#'] = newMappings['after_timestamp#'].astype(int)
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

    def compute_colors(self, df):
        colors = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple']
        colorDf = pd.DataFrame() 
        timestamps = df['Timestamp#'].dropna().unique()
        if self.source_order:
            for index, timestamp in enumerate(self.source_order):
                curDf = df.loc[df['Timestamp#']==timestamp]
                curDf['Color'] = colors[index]
                colorDf = colorDf.append(curDf, ignore_index=True)
        #TODO: This is a quick fix for getting multiple colors for whole files, use design doc specs in future
        elif len(self.sources) > 1 and len(timestamps <= 2):
            for index, timestamp in enumerate(df['Timestamp#'].dropna().unique()):
                curDf = df.loc[df['Timestamp#']==timestamp]
                curDf['Color'] = colors[index]
                colorDf = colorDf.append(curDf, ignore_index=True)
        else:
            colorDf = colorDf.append(df, ignore_index=True)
            colorDf['Color'] = colors[0]
        return colorDf

    def getMappings(self):
        mappings = pd.DataFrame()
        if os.path.getsize(self.mappings_path) > 0: # Check if we already having mappings between the current files
            self.all_mappings = pd.read_csv(self.mappings_path)
            mappings = self.all_mappings.loc[(self.all_mappings['before_timestamp#']==self.source_order[0]) & (self.all_mappings['after_timestamp#']==self.source_order[1])]
            #before_mappings = self.all_mappings.loc[self.all_mappings['before_timestamp#']==self.source_order[0]]
            #mappings = before_mappings.loc[before_mappings['after_timestamp#']==self.source_order[1]]
        #if mappings.empty: # Currently not using our mapping generation function as it needs to be improved
            #mappings = self.createMappings(self.summaryDf)
        if not mappings.empty: self.add_speedup(mappings, gui.loadedData.summaryDf)
        return mappings

    def createMappings(self, df):
        mappings = pd.DataFrame()
        df['map_name'] = df['Name'].map(lambda x: x.split(' ')[1].split(',')[-1].split('_')[-1])
        before = df.loc[df['Timestamp#'] == self.source_order[0]]
        after = df.loc[df['Timestamp#'] == self.source_order[1]]
        for index in before.index:
            match = after.loc[after['map_name'] == before['map_name'][index]].reset_index(drop=True) 
            if not match.empty:
                match = match.iloc[[0]]
                match['before_timestamp#'] = before['Timestamp#'][index]
                match['before_name'] = before['Name'][index]
                match['before_short_name'] = before['Short Name'][index]
                match['after_timestamp#'] = match['Timestamp#']
                match['after_name'] = match['Name']
                match['after_short_name'] = match['Short Name']
                match = match[['before_timestamp#', 'before_name', 'before_short_name', 'after_timestamp#', 'after_name', 'after_short_name']]
                mappings = mappings.append(match, ignore_index=True)
        if not mappings.empty: 
            mappings = self.get_speedups(mappings)
            self.all_mappings = self.all_mappings.append(mappings, ignore_index=True)
            self.all_mappings.to_csv(self.mappings_path, index=False)
        return mappings

class CustomData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.name = 'Custom'
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        # mappings
        self.mappings = loadedData.mapping
        self.src_mapping = loadedData.src_mapping
        self.app_mapping = loadedData.app_mapping
        # Get all unique variants upon first load
        if not update: self.variants = loadedData.summaryDf['Variant'].dropna().unique()
        if not update: self.src_variants = loadedData.srcDf['Variant'].dropna().unique()
        if not update: self.app_variants = loadedData.appDf['Variant'].dropna().unique()
        # codelet custom plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=self.variants, mappings=self.mappings, short_names_path=gui.loadedData.short_names_path)
            self.df = df
            self.fig = fig
            self.textData = textData
            if level == 'Codelet':
                gui.c_customTab.notify(self)

        # source custom plot
        if (level == 'All' or level == 'Source'):
            df = loadedData.srcDf.copy(deep=True)
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=self.src_variants, mappings=self.src_mapping, short_names_path=gui.loadedData.short_names_path)
            self.srcDf = df
            self.srcFig = fig
            self.srcTextData = textData
            if level == 'Source':
                gui.s_customTab.notify(self)

        # application custom plot
        if (level == 'All' or level == 'Application'):
            df = loadedData.appDf.copy(deep=True)
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=self.app_variants, mappings=self.app_mapping, short_names_path=gui.loadedData.short_names_path)
            self.appDf = df
            self.appFig = fig
            self.appTextData = textData
            if level == 'Application':
                gui.a_customTab.notify(self)

        if level == 'All':
            self.notify_observers()

class TRAWLData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.name = 'TRAWL'
        # Watch for updates in loaded data
        loadedData.add_observers(self)
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("TRAWLData Notified from ", loadedData)
        # mappings
        self.mappings = loadedData.mapping
        self.src_mapping = loadedData.src_mapping
        self.app_mapping = loadedData.app_mapping
        # Get all unique variants upon first load
        if not update: self.variants = loadedData.summaryDf['Variant'].dropna().unique()
        if not update: self.src_variants = loadedData.srcDf['Variant'].dropna().unique()
        if not update: self.app_variants = loadedData.appDf['Variant'].dropna().unique()
        # Codelet trawl plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=gui.loadedData.short_names_path)
            self.df = df
            self.fig = fig
            self.textData = textData
            if level == 'Codelet':
                gui.c_trawlTab.notify(self)

        # source trawl plot
        if level == 'All' or level == 'Source':
            df = loadedData.srcDf.copy(deep=True)
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.src_mapping, variants=self.src_variants, short_names_path=gui.loadedData.short_names_path)
            self.srcDf = df
            self.srcFig = fig
            self.srcTextData = textData
            if level == 'Source':
                gui.s_trawlTab.notify(self)

        # application trawl plot
        if level == 'All' or level == 'Application':
            df = loadedData.appDf.copy(deep=True)
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.app_mapping, variants=self.app_variants, short_names_path=gui.loadedData.short_names_path)
            self.appDf = df
            self.appFig = fig
            self.appTextData = textData
            if level == 'Application':
                gui.a_trawlTab.notify(self)

        if level == 'All':
            self.notify_observers()
    
class CoverageData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.name = 'Summary'
        # Watch for updates in loaded data
        loadedData.add_observers(self)
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        # use qplot dataframe to generate the coverage plot
        df = loadedData.summaryDf.copy(deep=True)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        if not update: # Get all unique variants upon first load
            self.variants = df['Variant'].dropna().unique()
        # mappings
        self.mappings = loadedData.mapping
        df, fig, texts = coverage_plot(df, "test", scale, "Coverage", False, chosen_node_set, gui=True, x_axis=x_axis, y_axis=y_axis, mappings=self.mappings, \
            variants=variants, short_names_path=gui.loadedData.short_names_path)
        self.df = df
        self.fig = fig
        self.textData = texts
        self.notify_observers()

class QPlotData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        # Watch for updates in loaded data
        loadedData.add_observers(self)
        self.loadedData = loadedData
        self.df = None
        self.fig = None
        self.ax = None
        self.appDf = None
        self.appFig = None
        self.appTextData = None
        self.mappings = pd.DataFrame()
        self.name = 'QPlot'

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear', level='All', mappings=pd.DataFrame()):
        print("QPlotData Notified from ", loadedData)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        # mappings
        self.mappings = loadedData.mapping
        self.src_mapping = loadedData.src_mapping
        self.app_mapping = loadedData.app_mapping
        # Get all unique variants upon first load
        if not update: self.variants = loadedData.summaryDf['Variant'].dropna().unique()
        if not update: self.src_variants = loadedData.srcDf['Variant'].dropna().unique()
        if not update: self.app_variants = loadedData.appDf['Variant'].dropna().unique()
        # Codelet plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.mappings, variants=self.variants, short_names_path=gui.loadedData.short_names_path)
            # TODO: Need to settle how to deal with multiple plots/dataframes
            # May want to let user to select multiple plots to look at within this tab
            # Currently just save the ORIG data
            self.df = df_ORIG if df_ORIG is not None else df_XFORM
            self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.textData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Codelet':
                gui.c_qplotTab.notify(self)
        
        # source qplot
        if (level == 'All' or level == 'Source'):
            df = loadedData.srcDf.copy(deep=True)
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.src_mapping, variants=self.src_variants, short_names_path=gui.loadedData.short_names_path)
            self.srcDf = df_ORIG if df_ORIG is not None else df_XFORM
            self.srcFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.srcTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Source':
                gui.s_qplotTab.notify(self)

        # application qplot
        if (level == 'All' or level == 'Application'):
            df = loadedData.appDf.copy(deep=True)
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.app_mapping, variants=self.app_variants, short_names_path=gui.loadedData.short_names_path)
            self.appDf = df_ORIG if df_ORIG is not None else df_XFORM
            self.appFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.appTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Application':
                gui.a_qplotTab.notify(self)

        if level == 'All':
            self.notify_observers()

class SIPlotData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        self.name = 'SIPlot'
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, cluster=resource_path(os.path.join('clusters', 'FE_tier1.csv')), title="FE_tier1", \
        filtering=False, filter_data=None, scale='linear', level='All', mappings=pd.DataFrame()):
        print("SIPlotData Notified from ", loadedData)
        df = loadedData.summaryDf.copy(deep=True)
        chosen_node_set = set(['RAM [GB/s]','L2 [GB/s]','FE','FLOP [GFlop/s]','L1 [GB/s]','VR [GB/s]','L3 [GB/s]'])
        # mappings
        self.mappings = loadedData.mapping
        self.src_mapping = loadedData.src_mapping
        self.app_mapping = loadedData.app_mapping
        # Plot only at Codelet level for now
        if not update: self.variants = df['Variant'].dropna().unique()
        if not update: self.src_variants = loadedData.srcDf['Variant'].dropna().unique()
        if not update: self.app_variants = loadedData.appDf['Variant'].dropna().unique()

        df_ORIG, fig_ORIG, textData_ORIG = parse_ip_siplot_df\
            (cluster, "FE_tier1", "row", title, chosen_node_set, df, variants=variants, filtering=filtering, filter_data=filter_data, mappings=self.mappings, scale=scale, short_names_path=gui.loadedData.short_names_path)
        self.df = df_ORIG
        # TODO: Figure out why we need to merge the diagnostic variables again, parse_ip_siplot_df probably removes those columns
        if not self.loadedData.analytics.empty: # Merge diagnostic variables with SIPlot dataframe
                self.df.drop(columns=['ddg_artifical_cyclic', 'limits', 'ddg_true_cyclic', 'init_only', 'rhs_op_count'], inplace=True)
                diagnosticDf = self.loadedData.analytics.drop(columns=['timestamp#'])
                self.df = pd.merge(left=self.df, right=diagnosticDf, on='name', how='left')
        self.fig = fig_ORIG
        self.textData = textData_ORIG

        self.notify_observers()

class DataSourcePanel(ScrolledTreePane):
    class DataTreeNode:
        nextId = 0
        nodeDict = {}
        def __init__(self, name):
            self.name = name
            self.id = DataSourcePanel.DataTreeNode.nextId
            DataSourcePanel.DataTreeNode.nextId += 1
            DataSourcePanel.DataTreeNode.nodeDict[self.id]=self

        @classmethod
        def lookupNode(cls, id):
            return cls.nodeDict[id]

        def open(self):
            print("node open:", self.name, self.id) 

    class MetaTreeNode(DataTreeNode):
        def __init__(self, name):
            super().__init__(name)

    class LocalTreeNode(DataTreeNode):
        def __init__(self, path, name, container):
            super().__init__(name)
            self.container = container
            self.path = path

    class RemoteTreeNode(DataTreeNode):
        def __init__(self, path, name, container, time_stamp=None):
            super().__init__(name)
            self.container = container
            self.path = path
            self.time_stamp = time_stamp

    class RemoteNode(RemoteTreeNode):
        def __init__(self, url, path, name, container, time_stamp=None):
            super().__init__(path, name, container, time_stamp)
            self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
            self.UIUC_path = os.path.join(self.cape_path, 'UIUC')
            self.UVSQ_path = os.path.join(self.cape_path, 'UVSQ')
            self.children = []
            self.url = url
            self.local_dir_path = ''
            self.local_file_path = ''

        def open(self):
            print("remote node open:", self.name, self.id) 
            self.page = requests.get(self.url)
            content_type = self.page.headers['content-type']
            # Webpage node
            if content_type == 'text/html':
                self.container.show_options(file_type='html', select_fn=self.user_selection)
            # Data node
            elif self.path.endswith('.raw.csv') or self.path.endswith('.xlsx'):
                self.container.show_options(file_type='data', select_fn=self.user_selection)
            # Directory node
            else: self.open_directory()

        def user_selection(self, choice):
            if self.container.win: self.container.win.destroy()
            if choice == 'Cancel': return 
            elif choice in ['Overwrite', 'Append']: self.get_files()
            self.container.openLocalFile(choice, os.path.dirname(self.path), self.path, self.url[:-5] if self.url.endswith('.xlsx') else None)
        
        def get_files(self):
            #TODO: Look into combining this when opening LocalDir
            if not os.path.isfile(self.path): # Then we need to download the data from the server
                os.makedirs(os.path.dirname(self.path))
                self.download_data()

        def download_data(self):
            local_dir = os.path.dirname(self.path)
            dir_url = self.url.rsplit('/', 1)[0] + '/' # Get the data directory to download any corresponding files
            dir_page = requests.get(dir_url)
            tree = html.fromstring(dir_page.content)
            for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                file_name = (link_element.xpath('td[position()=2]/a')[0]).get('href')
                if file_name == self.name + '.xlsx' or file_name == self.name + '.raw.csv' or file_name == self.name + '.mapping.csv' or \
                    file_name == self.name + '.analytics.csv' or file_name == self.name + '.names.csv':
                    file_data = requests.get(dir_url + file_name)
                    open(os.path.join(local_dir, file_name), 'wb').write(file_data.content)

        def open_directory(self):
            tree = html.fromstring(self.page.content)
            names = []
            for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                hyperlink = link_element.xpath('td[position()=2]/a')[0]
                names.append(hyperlink.get('href'))
            names = self.remove_webpages(names)
            # Show directories and data files (.xlsx or .raw.csv)
            for name in names:
                if (name.endswith('/') or name.endswith('.raw.csv') or name.endswith('.xlsx')) and name not in self.children:
                    self.children.append(name)
                    full_url = self.url + name
                    short_name = name.split('.raw.csv')[0] if name.endswith('.raw.csv') else name.split('.xlsx')[0]
                    if name.endswith('.raw.csv') or name.endswith('.xlsx'): 
                        time_stamp = link_element.xpath('td[position()=3]/text()')[0][:10] + '_' + link_element.xpath('td[position()=3]/text()')[0][11:13] + '-' + link_element.xpath('td[position()=3]/text()')[0][14:16]
                        full_path = os.path.join(self.path, short_name, time_stamp, name)
                    elif name.endswith('/'): full_path = os.path.join(self.path, name[:-1])
                    self.container.insertNode(self, DataSourcePanel.RemoteNode(full_url, full_path, short_name, self.container))

        def remove_webpages(self, names):
            data_files = [i.split('.xlsx')[0]+'/' for i in names if i.endswith('.xlsx')]
            return [i for i in names if i not in data_files]
        
        # TODO: Integrate this function for downloading HTML, next step is to have it run in the background
        # def open_webpage(self):
            # Download Corresponding HTML files if they don't already exist
            # local_dir_path = local_dir_path + '\\HTML' 
            # if not os.path.isdir(local_dir_path):
            #     print("Downloading HTML Files")
            #     pages = ['index.html', 'application.html', 'fcts_and_loops.html', 'loops_index.html', 'topology.html']
            #     kwargs = {'project_folder': self.cape_path, 'project_name' : 'TEMP', 'zip_project_folder' : False, 'over_write' : True}
            #     for page in pages:
            #         url = self.path + page
            #         config.setup_config(url, **kwargs)
            #         wp = WebPage()
            #         wp.get(url)
            #         wp.parse()
            #         wp.save_html()
            #         wp.save_assets()
            #         for thread in wp._threads:
            #             thread.join()
            #     print("Done Downloading Webpages")
            #     # Move html files/assets to HTML directory and delete TEMP directory
            #     temp_dir_path = self.cape_path + 'TEMP'
            #     for directory in self.path[8:].split('/'):
            #         temp_dir_path = temp_dir_path + '\\' + directory
            #     shutil.move(temp_dir_path, local_dir_path)
            #     shutil.rmtree(self.cape_path + 'TEMP')
            # # Add local html file path to browser
            # for name in os.listdir(local_dir_path):
            #     if name.endswith("__index.html"):
            #         gui.loaded_url = (local_dir_path + '\\' + name)
            #         break
            # gui.loaded_url = self.path # Use live version for now

    class LocalFileNode(LocalTreeNode):
        def __init__(self, path, name, container):
            super().__init__(path, name, container)

        def open(self):
            print("file node open:", self.name, self.id) 
            pass
        
    class LocalDirNode(LocalTreeNode):
        def __init__(self, path, name, container):
            super().__init__(path, name+'/', container)
            self.children = []
            self.url = ''

        def open(self):
            print("dir node open:", self.name, self.id)
            if re.match('\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', self.name): # timestamp directory holding several files to be loaded
                self.container.show_options(file_type='data', select_fn=self.user_selection)
            else:
                for d in os.listdir(self.path):
                    if d not in self.children:
                        self.children.append(d)
                        self.fullpath= os.path.join(self.path, d)
                        if os.path.isdir(self.fullpath): # Currently only allow user to open files that were downloaded from a server or in the timestamp format
                            self.container.insertNode(self, DataSourcePanel.LocalDirNode(self.fullpath, d, self.container))

        def user_selection(self, choice):
            if self.container.win: self.container.win.destroy()
            if choice == 'Cancel': return 
            for data in os.listdir(self.path):
                if data.endswith('.xlsx') or data.endswith('.raw.csv'):
                    source_path = os.path.join(self.path, data)
                    break
            # Recreate URL from local directory structure if UVSQ file (.xlsx)
            if source_path.endswith('.xlsx'): self.create_url()
            self.container.openLocalFile(choice, self.path, source_path, self.url if source_path.endswith('.xlsx') else None)
        
        def create_url(self):
            self.url = 'https://datafront.maqao.exascale-computing.eu/public_html/oneview'
            dirs = []
            path, name = os.path.split(os.path.dirname(self.path)) # dir_path is self.path
            while name != 'UVSQ':
                dirs.append(name)
                path, name = os.path.split(path)
            dirs.reverse()
            for name in dirs:
                self.url += '/' + name

    def __init__(self, parent, loadDataSrcFn):
        ScrolledTreePane.__init__(self, parent)
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.UIUC_path = os.path.join(self.cape_path, 'UIUC')
        self.UVSQ_path = os.path.join(self.cape_path, 'UVSQ')
        self.loadDataSrcFn = loadDataSrcFn
        self.dataSrcNode = DataSourcePanel.MetaTreeNode('Data Source')
        self.localNode = DataSourcePanel.MetaTreeNode('Local')
        self.remoteNode = DataSourcePanel.MetaTreeNode('Remote')
        self.insertNode(None, self.dataSrcNode)
        self.insertNode(self.dataSrcNode, self.localNode)
        self.insertNode(self.dataSrcNode, self.remoteNode)
        self.opening = False
        self.firstOpen = True
        self.win = None
        self.setupLocalRoots()
        self.setupRemoteRoots()
        self.treeview.bind("<<TreeviewOpen>>", self.handleOpenEvent)

    def show_options(self, file_type, select_fn):
        if file_type == 'html': # OV webpage with no xlsx file
            self.create_dialog_win('Missing Data', 'This file is missing the corresponding data file.\nWould you like to clear any existing plots and\nonly load this webpage?', ['Open Webpage', 'Cancel'], select_fn)
        elif file_type == 'data':
            if len(gui.loadedData.sources) >= 2: # Currently can only append max 2 files
                self.create_dialog_win('Max Data', 'You have the max number of data files open.\nWould you like to overwrite with the new data?', ['Overwrite', 'Cancel'], select_fn)
            elif len(gui.loadedData.sources) >= 1: # User has option to append to existing file
                self.create_dialog_win('Existing Data', 'Would you like to append to the existing\ndata or overwrite with the new data?', ['Append', 'Overwrite', 'Cancel'], select_fn)
            if not gui.loadedData.sources: # Nothing currently loaded so just load the data with no need to warn the user
                select_fn('Overwrite')

    def create_dialog_win(self, title, message, options, select_fn):
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", lambda option='Cancel' : select_fn(option))
        self.win.title(title)
        tk.Label(self.win, text=message).grid(row=0, columnspan=len(options), padx=15, pady=10)
        for i, option in enumerate(options):
            tk.Button(self.win, text=option, command=lambda choice=option:select_fn(choice)).grid(row=1, column=i, pady=10)
        root.wait_window(self.win)

    def insertNode(self, parent, node):
        parent_str = parent.id if parent else ''
        self.treeview.insert(parent_str,'end',node.id,text=node.name)
        
    def openLocalFile(self, choice, data_dir, source, url):
        self.loadDataSrcFn(choice, data_dir, source, url)

    def handleOpenEvent(self, event):
        if not self.opening: # finish opening one file before another is started
            self.opening = True
            nodeId = int(self.treeview.focus())
            node = DataSourcePanel.DataTreeNode.lookupNode(nodeId)
            node.open()
            self.opening = False
        if self.firstOpen:
            self.firstOpen = False
            self.treeview.column('#0', minwidth=600, width=600) # Current fix for horizontal scrolling

    def setupLocalRoots(self):
        home_dir=expanduser("~")
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(home_dir, 'Home', self) )
        cape_cache_path= os.path.join(home_dir, 'AppData', 'Roaming', 'Cape')
        if not os.path.isdir(cape_cache_path): Path(cape_cache_path).mkdir(parents=True, exist_ok=True)
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(cape_cache_path, 'Previously Visited', self) )

    def setupRemoteRoots(self):
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://datafront.maqao.exascale-computing.eu/public_html/oneview/', self.UVSQ_path, 'UVSQ', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://vectorization.computer/data/', self.UIUC_path, 'UIUC', self))

class AnalysisResultsPanel(ScrolledTreePane):
    class DataTreeNode:
        nextId = 0
        nodeDict = {}
        def __init__(self, name):
            self.name = name
            self.id = AnalysisResultsPanel.DataTreeNode.nextId
            AnalysisResultsPanel.DataTreeNode.nextId += 1
            AnalysisResultsPanel.DataTreeNode.nodeDict[self.id]=self

        @classmethod
        def lookupNode(cls, id):
            return cls.nodeDict[id]

        def open(self):
            print("node open:", self.name, self.id) 

    class MetaTreeNode(DataTreeNode):
        def __init__(self, name):
            super().__init__(name)

    class LocalTreeNode(DataTreeNode):
        def __init__(self, path, name, container):
            super().__init__(name)
            self.container = container
            self.path = path

    class LocalFileNode(LocalTreeNode):
        def __init__(self, path, name, container, df=pd.DataFrame(), mappings=pd.DataFrame(), analytics=pd.DataFrame(), data={}):
            super().__init__(path, name, container)
            self.summary_df = df
            self.mappings = mappings
            self.analytics = analytics
            self.data = data

        def open(self):
            print("file node open:", self.name, self.id) 
            # Remove any previous plots in Application/Source
            tabs = [gui.s_customTab.window, gui.s_qplotTab.window, gui.s_siPlotTab.window, gui.s_trawlTab.window, \
                gui.a_customTab.window, gui.a_qplotTab.window, gui.a_siPlotTab.window, gui.a_trawlTab.window]
            for tab in tabs:
                for widget in tab.winfo_children():
                    widget.destroy()
            self.container.openLocalFile(self.summary_df, self.mappings, self.analytics, self.data)

    class LocalDirNode(LocalTreeNode):
        def __init__(self, path, name, container):
            super().__init__(path, name+'/', container)
            self.children = []

        def open(self):
            print("dir node open:", self.name, self.id) 
            for d in os.listdir(self.path):
                if d not in self.children:
                    self.children.append(d)
                    fullpath= os.path.join(self.path, d)
                    df = pd.DataFrame()
                    mappings = pd.DataFrame()
                    analytics = pd.DataFrame()
                    data = {}
                    for name in os.listdir(fullpath): # get saved data
                        if name == 'summary.xlsx': df = pd.read_excel(os.path.join(fullpath, name))
                        if name == 'mappings.xlsx': mappings = pd.read_excel(os.path.join(fullpath, name))
                        if name == 'analytics.xlsx': analytics = pd.read_excel(os.path.join(fullpath, name))
                        if name == 'data.pkl': 
                            data_file = open(os.path.join(fullpath, name), 'rb')
                            data = pickle.load(data_file)
                            data_file.close()
                    self.container.insertNode(self, AnalysisResultsPanel.LocalFileNode(fullpath, d, self.container, df=df, mappings=mappings, analytics=analytics, data=data))

    def __init__(self, parent, loadSavedStateFn):
        ScrolledTreePane.__init__(self, parent)
        self.loadSavedStateFn = loadSavedStateFn
        self.analysisResultsNode = AnalysisResultsPanel.MetaTreeNode('Analysis Results')
        self.insertNode(None, self.analysisResultsNode)
        self.opening = False
        self.firstOpen = True
        self.setupLocalRoots()
        self.treeview.bind("<<TreeviewOpen>>", self.handleOpenEvent)

    def insertNode(self, parent, node):
        parent_str = parent.id if parent else ''
        self.treeview.insert(parent_str,'end',node.id,text=node.name) 

    def openLocalFile(self, df=pd.DataFrame(), mappings=pd.DataFrame(), analytics=pd.DataFrame(), data={}):
        self.loadSavedStateFn(df, mappings, analytics, data)

    def handleOpenEvent(self, event):
        if not self.opening: # finish opening one file before another is started
            self.opening = True
            nodeId = int(self.treeview.focus())
            node = AnalysisResultsPanel.DataTreeNode.lookupNode(nodeId)
            node.open()
            self.opening = False
        if self.firstOpen:
            self.firstOpen = False
            self.treeview.column('#0', minwidth=300, width=300)

    def setupLocalRoots(self):
        cape_cache_path= os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape', 'Analysis Results')
        if not os.path.isdir(cape_cache_path): Path(cape_cache_path).mkdir(parents=True, exist_ok=True)
        self.insertNode(self.analysisResultsNode, AnalysisResultsPanel.LocalDirNode(cape_cache_path, 'Local', self) )

class ExplorerPanel(tk.PanedWindow):
    def __init__(self, parent, loadDataSrcFn, loadSavedStateFn):
        tk.PanedWindow.__init__(self, parent, orient="vertical")
        top = DataSourcePanel(self, loadDataSrcFn)
        top.pack(side = tk.TOP)
        self.add(top)
        bot = AnalysisResultsPanel(self, loadSavedStateFn)
        bot.pack(side = tk.TOP)
        self.add(bot)
        self.pack(fill=tk.BOTH,expand=True)
        self.configure(sashrelief=tk.RAISED)

class CodeletTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class SummaryTab(tk.Frame):
    def __init__(self, parent, coverageData, level):
        tk.Frame.__init__(self, parent)
        if coverageData is not None:
           coverageData.add_observers(self)
        self.coverageData = self.data = coverageData
        self.name = 'Summary'
        self.level = level
        self.current_variants = ['ORIG']
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = r'%coverage'
        self.current_labels = []
        self.parent = parent
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                    sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot Setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        # Data table/tabs setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        # Add diagnostic variables to summary data table
        if not gui.loadedData.analytics.empty:
            diagnosticDf = gui.loadedData.analytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summary_pt)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: self.exportCSV()).grid(row=0, column=1)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if (self.level == 'Codelet') and not gui.loadedData.mapping.empty:
            self.mappingsTab.buildMappingsTab(df, mappings)

    def exportCSV(self):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        gui.loadedData.summaryDf.to_csv(export_file_path, index=False, header=True)
    
    # Create tabs for data and labels
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'Summary')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        if not gui.loadedData.analytics.empty: self.guideTab = GuideTab(self.tableNote, self)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        if not gui.loadedData.analytics.empty: self.tableNote.add(self.guideTab, text='Guide')
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    def notify(self, coverageData):
        for w in self.window.winfo_children():
            w.destroy()
        self.update(coverageData.df, coverageData.fig, coverageData.textData, coverageData.mappings, coverageData.variants)

class PlotInteraction():
    def __init__(self, tab, df, fig, textData, level):
        self.tab = tab
        self.df = df
        self.fig = fig
        self.textData = textData
        self.adjusted = False
        self.adjusting = False
        self.cur_xlim = self.home_xlim = self.textData['ax'].get_xlim()
        self.cur_ylim = self.home_ylim = self.textData['ax'].get_ylim()
        # Create lists of tabs that need to be synchronized according to the level and update the plot with the saved state
        self.level = level
        self.codelet_tabs = [gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab, gui.summaryTab]
        self.source_tabs = [gui.s_trawlTab, gui.s_qplotTab, gui.s_customTab]
        self.application_tabs = [gui.a_trawlTab, gui.a_qplotTab, gui.a_customTab]
        if self.level == 'Codelet': 
            self.tabs = self.codelet_tabs
            self.stateDictionary = gui.loadedData.c_plot_state
            self.restoreState(self.stateDictionary)
        elif self.level == 'Source': 
            self.tabs = self.source_tabs
            self.stateDictionary = gui.loadedData.s_plot_state
            self.restoreState(self.stateDictionary)
        elif self.level == 'Application': 
            self.tabs = self.application_tabs
            self.stateDictionary = gui.loadedData.a_plot_state
            self.restoreState(self.stateDictionary)
        # Setup Frames
        self.plotFrame = tk.Frame(self.tab.window)
        self.plotFrame2 = tk.Frame(self.plotFrame)
        self.plotFrame3 = tk.Frame(self.plotFrame)
        self.tab.window.add(self.plotFrame, stretch='always')
        self.plotFrame3.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.plotFrame2.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Plot interacting buttons
        self.save_state_button = tk.Button(self.plotFrame3, text='Save State', command=self.saveState)
        self.adjust_button = tk.Button(self.plotFrame3, text='Adjust Text', command=self.adjustText)
        self.toggle_labels_button = tk.Button(self.plotFrame3, text='Hide Labels', command=self.toggleLabels)
        self.show_markers_button = tk.Button(self.plotFrame3, text='Show Points', command=self.showMarkers)
        #self.star_speedups_button = tk.Button(self.plotFrame3, text='Star Speedups', command=self.star_speedups)
        self.action_selected = tk.StringVar(value='Choose Action')
        action_options = ['Choose Action', 'Highlight Point', 'Remove Point', 'Toggle Label']
        self.action_menu = tk.OptionMenu(self.plotFrame3, self.action_selected, *action_options)
        self.action_menu['menu'].insert_separator(1)
        # Plot/toolbar
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame2)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('draw_event', self.onDraw)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame3)
        # Point selection table
        options=[]
        for i in range(len(self.df['short_name'])):
            options.append('[' + self.df['short_name'][i] + '] ' + self.df['name'][i] + ' [' + str(self.df['timestamp#'][i]) + ']')
        self.pointSelector = ChecklistBox(self.plotFrame2, options, options, listType='pointSelector', tab=self, bd=1, relief="sunken", background="white")
        self.pointSelector.restoreState(self.stateDictionary)
        # Check if we are loading an analysis result and restore if so
        if gui.loadedData.restore: self.restoreAnalysisState()
        # Grid Layout
        self.toolbar.grid(column=7, row=0, sticky=tk.S)
        self.action_menu.grid(column=5, row=0, sticky=tk.S)
        self.show_markers_button.grid(column=3, row=0, sticky=tk.S, pady=2)
        self.toggle_labels_button.grid(column=2, row=0, sticky=tk.S, pady=2)
        self.adjust_button.grid(column=1, row=0, sticky=tk.S, pady=2)
        self.save_state_button.grid(column=0, row=0, sticky=tk.S, pady=2)
        self.plotFrame3.grid_rowconfigure(0, weight=1)
        self.pointSelector.pack(side=tk.RIGHT, anchor=tk.N, fill=tk.Y)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, anchor=tk.N, padx=10)
        self.toolbar.update()
        self.canvas.draw()

    def restoreAnalysisState(self):
        if gui.loadedData.data['Codelet']: 
            self.restoreState(gui.loadedData.data['Codelet'])
            self.pointSelector.restoreState(gui.loadedData.data['Codelet'])

    def cancelAction(self):
        self.choice = 'cancel'
        self.win.destroy()

    def selectAction(self, option):
        self.choice = option
        self.win.destroy()

    def saveState(self):
        # Create popup dialog that asks user to select either save selected or save all
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
        self.win.title('Save State')
        message = 'Would you like to save data for all of the codelets\nor just for those selected?'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        for index, option in enumerate(['Save All', 'Save Selected']):
            b = tk.Button(self.win, text=option, command= lambda metric=option : self.selectAction(option))
            b.grid(row=index+1, column=1, padx=20, pady=10)
        root.wait_window(self.win)
        if self.choice == 'cancel': return        
        # Ask user to name the directory for this state to be saved
        dest_name = tk.simpledialog.askstring('Analysis Result', 'Provide a name for this analysis result')
        if not dest_name: return
        dest = os.path.join(gui.loadedData.analysis_results_path, dest_name)
        if not os.path.isdir(dest):
            Path(dest).mkdir(parents=True, exist_ok=True)
        # Store hidden/highlighted points for each level
        # Codelet
        # Each level has its set of tabs, hidden/highlighted points, and variants
        # Each tab has its axes, scales
        data = {}
        codelet = {}
        source = {}
        application = {}
        # Store hidden/highlighted points at the Codelet level
        hidden_names = []
        highlighted_names = []
        visible_names = []
        for marker in self.textData['markers']:
            name = self.textData['marker:name'][marker]
            if marker.get_alpha():
                visible_names.append(name)
                if marker.get_marker() == '*': # Highlighted point
                    highlighted_names.append(name)
            elif self.choice == 'Save All':
                hidden_names.append(name)
        codelet['hidden_names'] = hidden_names
        codelet['highlighted_names'] = highlighted_names
        # Save either full or selected codelets in dataframes to notify observers upon restoring
        summary_dest = os.path.join(dest, 'summary.xlsx')
        mappings_dest = os.path.join(dest, 'mappings.xlsx')
        end2end_mappings_dest = os.path.join(dest, 'end2end_mappings.xlsx')
        analytics_dest = os.path.join(dest, 'analytics.xlsx')
        df = gui.loadedData.summaryDf
        if self.choice == 'Save All':
            df.to_excel(summary_dest, index=False)
            if not gui.loadedData.orig_mapping.empty: gui.loadedData.orig_mapping.to_excel(mappings_dest, index=False)
            if gui.loadedData.removedIntermediates: gui.loadedData.mapping.to_excel(end2end_mappings_dest, index=False)
            if not gui.loadedData.analytics.empty: gui.loadedData.analytics.to_excel(analytics_dest, index=False)
        elif self.choice == 'Save Selected':
            if not gui.loadedData.orig_mapping.empty and visible_names:
                selected_mappings, visible_names = self.getSelectedMappings(visible_names, gui.loadedData.orig_mapping)
                selected_mappings.to_excel(mappings_dest, index=False)
                if gui.loadedData.removedIntermediates:
                    selected_mappings, visible_names = self.getSelectedMappings(visible_names, gui.loadedData.mapping)
                    selected_mappings.to_excel(end2end_mappings_dest, index=False)
            if not gui.loadedData.analytics.empty:
                a_df = gui.loadedData.analytics
                selected_analytics = a_df.loc[(a_df['name']+a_df['timestamp#'].astype(str)).isin(visible_names)]
                selected_analytics.to_excel(analytics_dest, index=False)
            selected_summary = df.loc[(df['Name']+df['Timestamp#'].astype(str)).isin(visible_names)]
            selected_summary.to_excel(summary_dest, index=False)
        # Store current selected variants at this level
        variants = gui.summaryTab.current_variants
        codelet['variants'] = variants
        # Each tab has it's own nested dictionary with it's current plot selections
        for tab in self.codelet_tabs:
            codelet[tab.name] = {'x_axis':tab.x_axis, 'y_axis':tab.y_axis, 'x_scale':tab.x_scale, 'y_scale':tab.y_scale}
        # Save the all the stored data into a nested dictionary
        data['Codelet'] = codelet
        data['Source'] = source
        data['Application'] = application
        data_dest = os.path.join(dest, 'data.pkl')
        data_file = open(data_dest, 'wb')
        pickle.dump(data, data_file)
        data_file.close()
        # Need to save: save the whole current dataframe 
        # - add (true/false) columns: highlighted, visible, 
        # Need to save axes/scales for each plot and variants for all plots
        # - save 3 pickle nested dictionaries (Application, Source, Codelet)
        # - Ex. {'Summary' : {'x_axis' : 'GFLOPS', 'y_axis' : '%coverage', 'x_scale': 'linear', 'y_scale':'linear', 'variants':['ORIG']}, 'TRAWL' : {} ...}
        # create all the plots as usual, except now there is a flag in plotInteraction that restores the state.

    #TODO: Possibly unhighlight any other highlighted points or show all points to begin with
    def A_filter(self, relate, metric, threshold, highlight, remove=False, show=False, points=[]):
        df = gui.loadedData.summaryDf
        names = []
        if metric: names = [name + timestamp for name,timestamp in zip(df.loc[relate(df[metric], threshold)]['Name'], df.loc[relate(df[metric], threshold)]['Timestamp#'].astype(str))]
        # Temporary hardcoded option while Dave works on specific formulas
        names.extend(points)
        for name in names:
            try: 
                marker = self.textData['name:marker'][name]
                if highlight and marker.get_marker() == 'o': self.highlightPoint(marker)
                elif not highlight and marker.get_marker() == '*': self.highlightPoint(marker)
                if remove: self.togglePoint(marker, visible=False)
                elif show: self.togglePoint(marker, visible=True)
            except: pass
        self.drawPlots()
        return names

    def save_plot_state(self):
        # Get names of this tabs current hidden/highlighted data points
        if self.level == 'Codelet': dictionary = gui.loadedData.c_plot_state
        elif self.level == 'Source': dictionary = gui.loadedData.s_plot_state
        elif self.level == 'Application': dictionary = gui.loadedData.a_plot_state
        dictionary['hidden_names'] = []
        dictionary['highlighted_names'] = []
        # try: dictionary['guide_A_state'] = gui.summaryTab.guideTab.aTab.aLabel['text']
        # except: pass
        for marker in self.textData['markers']:
            if not marker.get_alpha():
                dictionary['hidden_names'].append(marker.get_label())
            if marker.get_marker() == '*':
                dictionary['highlighted_names'].append(marker.get_label())

    def restoreState(self, dictionary):
        for name in dictionary['hidden_names']:
            try:
                self.textData['name:marker'][name].set_alpha(0)
                self.textData['name:text'][name].set_alpha(0)
            except:
                pass
        self.filterArrows(dictionary['hidden_names'])
        for name in dictionary['highlighted_names']:
            try: 
                if self.textData['name:marker'][name].get_marker() != '*': self.highlight(self.textData['name:marker'][name], self.textData['name:text'][name])
            except: pass
        
    def filterArrows(self, names):
        if self.tab.mappings.empty or not names: return
        transitions = pd.DataFrame()
        for name in names:
            row = self.tab.mappings.loc[(self.tab.mappings['before_name']+self.tab.mappings['before_timestamp#'].astype(str))==name]
            while not row.empty:
                try: self.togglePoint(self.textData['name:marker'][name], visible=False)
                except: pass
                transitions = transitions.append(row, ignore_index=True)
                name = str(row['after_name'].iloc[0]+row['after_timestamp#'].iloc[0].astype(str))
                row = self.tab.mappings.loc[(self.tab.mappings['before_name']+self.tab.mappings['before_timestamp#'].astype(str))==name]

    def getSelectedMappings(self, names, mappings):
        if mappings.empty or not names: return
        selected_mappings = pd.DataFrame()
        all_names = copy.deepcopy(names)
        for name in names:
            row = mappings.loc[(mappings['before_name']+mappings['before_timestamp#'].astype(str))==name]
            while not row.empty:
                selected_mappings = selected_mappings.append(row, ignore_index=True)
                name = str(row['after_name'].iloc[0]+row['after_timestamp#'].iloc[0].astype(str))
                all_names.append(name)
                row = mappings.loc[(mappings['before_name']+mappings['before_timestamp#'].astype(str))==name]
        return selected_mappings, list(set(all_names))

    def toggleLabels(self):
        if self.toggle_labels_button['text'] == 'Hide Labels':
            print("Hiding Labels")
            for text in self.textData['texts']:
                text.set_alpha(0)
                if self.adjusted:
                    # possibly called adjustText after a zoom and no arrow is mapped to this label outside of the current axes
                    try: self.textData['text:arrow'][text].set_visible(False)
                    except: pass
            self.canvas.draw()
            self.toggle_labels_button['text'] = 'Show Labels'
        elif self.toggle_labels_button['text'] == 'Show Labels':
            print("Showing Labels")
            for marker in self.textData['marker:text']:
                if marker.get_alpha(): 
                    self.textData['marker:text'][marker].set_alpha(1) 
                    if self.adjusted: 
                        try: self.textData['text:arrow'][self.textData['marker:text'][marker]].set_visible(True)
                        except: pass
            self.canvas.draw()
            self.toggle_labels_button['text'] = 'Hide Labels'

    def toggleLabel(self, marker):
        label = self.textData['marker:text'][marker]
        if label.get_alpha():
            label.set_alpha(0)
            try: self.textData['text:arrow'][label].set_visible(False)
            except: pass 
        else:
            label.set_alpha(1)
            try: self.textData['text:arrow'][label].set_visible(True)
            except: pass 
        self.canvas.draw()

    def showMarkers(self):
        print("Showing markers")
        for tab in self.tabs:
            for marker in tab.plotInteraction.textData['markers']:
                marker.set_alpha(1)
                if tab.plotInteraction.textData['mappings']: 
                    for i in range(len(tab.plotInteraction.textData['mappings'])): 
                        tab.plotInteraction.textData['mappings'][i].set_alpha(1) 
                if tab.plotInteraction.toggle_labels_button['text'] == 'Hide Labels': # Know we need to show the labels/arrows as well
                    tab.plotInteraction.textData['marker:text'][marker].set_alpha(1)
                    if tab.plotInteraction.adjusted:
                        try: tab.plotInteraction.textData['text:arrow'][tab.plotInteraction.textData['marker:text'][marker]].set_visible(True)
                        except: pass
            for var in tab.plotInteraction.pointSelector.vars:
                var.set(1)
            tab.plotInteraction.canvas.draw()

    def onClick(self, event):
        #print("(%f, %f)", event.xdata, event.ydata)
        # for child in self.textData['ax'].get_children():
        #     print(child)
        if self.action_selected.get() == 'Choose Action':
            pass
        elif self.action_selected.get() == 'Highlight Point':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.highlightPoint(marker)
                    self.drawPlots()
                    return
        elif self.action_selected.get() == 'Remove Point':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.togglePoint(marker, visible=False)
                    self.drawPlots()
                    return
        elif self.action_selected.get() == 'Toggle Label':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.toggleLabel(marker)
                    return

    def togglePoint(self, marker, visible):
        for tab in self.tabs:
            otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
            otherMarker.set_alpha(visible)
            tab.plotInteraction.textData['marker:text'][otherMarker].set_alpha(visible)
            try: 
                for mapping in tab.plotInteraction.textData['name:mapping'][marker.get_label()]:
                    mapping.set_alpha(visible)
            except: pass
            try: tab.plotInteraction.textData['text:arrow'][tab.plotInteraction.textData['marker:text'][otherMarker]].set_visible(visible)
            except: pass
            name = tab.plotInteraction.textData['marker:name'][otherMarker]
            index = tab.plotInteraction.pointSelector.names.index(name)
            tab.plotInteraction.pointSelector.vars[index].set(visible)

    def highlight(self, marker, otherText=None):
        if marker.get_marker() == 'o':
            marker.set_marker('*')
            marker.set_markeredgecolor('k')
            marker.set_markeredgewidth(0.5)
            marker.set_markersize(11)
            if otherText:
                otherText.set_color('r')
        elif marker.get_marker() == '*':
            marker.set_marker('o')
            marker.set_markeredgecolor(marker.get_markerfacecolor())
            marker.set_markersize(6.0)
            if otherText:
                otherText.set_color('k')
    
    def highlightPoint(self, marker):
        for tab in self.tabs:
            otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
            otherText = tab.plotInteraction.textData['marker:text'][otherMarker]
            self.highlight(otherMarker, otherText)
    
    def drawPlots(self):
        for tab in self.tabs:
            tab.plotInteraction.canvas.draw()

    def onDraw(self, event):
        if self.adjusted and (self.cur_xlim != self.textData['ax'].get_xlim() or self.cur_ylim != self.textData['ax'].get_ylim()) and \
            (self.home_xlim != self.textData['ax'].get_xlim() or self.home_ylim != self.textData['ax'].get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            print("Ondraw adjusting")
            self.cur_xlim = self.textData['ax'].get_xlim()
            self.cur_ylim = self.textData['ax'].get_ylim()
            self.adjustText()

    def thread_adjustText(self):
        plt.sca(self.textData['ax'])
        if self.adjusted: # Remove old adjusted texts/arrows and create new texts before calling adjust_text again
            # Store index of hidden texts to update the new texts
            hiddenTexts = []
            highlightedTexts = []
            for i in range(len(self.textData['texts'])):
                if not self.textData['texts'][i].get_alpha(): hiddenTexts.append(i)
                if self.textData['texts'][i].get_color() == 'r': highlightedTexts.append(i)
            # Remove all old texts and arrows
            for child in self.textData['ax'].get_children():
                if isinstance(child, matplotlib.text.Annotation) or (isinstance(child, matplotlib.text.Text) and child.get_text() not in [self.textData['title'], '', self.textData['ax'].get_title()]):
                    child.remove()
            # Create new texts that maintain the current visibility
            self.textData['texts'] = [plt.text(self.textData['xs'][i], self.textData['ys'][i], self.textData['mytext'][i], alpha=1 if i not in hiddenTexts else 0, color='k' if i not in highlightedTexts else 'r') for i in range(len(self.textData['mytext']))]
            # Update marker to text mappings with the new texts
            self.textData['marker:text'] = dict(zip(self.textData['markers'],self.textData['texts']))
        # Only adjust texts that are in the current axes (in case of a zoom)
        to_adjust = []
        for i in range(len(self.textData['texts'])):
            if self.textData['texts'][i].get_alpha() and \
                self.textData['xs'][i] >= self.textData['ax'].get_xlim()[0] and self.textData['xs'][i] <= self.textData['ax'].get_xlim()[1] and \
                self.textData['ys'][i] >= self.textData['ax'].get_ylim()[0] and self.textData['ys'][i] <= self.textData['ax'].get_ylim()[1]:
                to_adjust.append(self.textData['texts'][i])
        adjust_text(to_adjust, ax=self.textData['ax'], arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        # Map each text to the corresponding arrow
        index = 0
        for child in self.textData['ax'].get_children():
            if isinstance(child, matplotlib.text.Annotation):
                self.textData['text:arrow'][to_adjust[index]] = child # Mapping
                if not to_adjust[index].get_alpha(): child.set_visible(False) # Hide arrows with hidden texts
                index += 1
        root.after(0, self.canvas.draw)
        self.adjusted = True
        self.adjusting = False
    
    def adjustText(self):
        if not self.adjusting: 
            self.adjusting = True
            threading.Thread(target=self.thread_adjustText, name='adjustText Thread').start()

class AxesTab(tk.Frame):
    @staticmethod
    def custom_axes(parent, var):
        menubutton = tk.Menubutton(parent, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        # TRAWL
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='TRAWL', menu=menu)
        for metric in ['speedup[vec]', 'speedup[dl1]', 'C_FLOP [GFlop/s]', 'c=inst_rate_gi/s']:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # QPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='QPlot', menu=menu)
        for metric in ['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]', 'C_FLOP [GFlop/s]', 'c=inst_rate_gi/s']:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Speedups (If mappings):
        if not parent.tab.mappings.empty:
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label='Speedups', menu=menu)
            for metric in ['Speedup[Time (s)]', 'Speedup[AppTime (s)]', 'Speedup[FLOP Rate (GFLOP/s)]', 'Difference']:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Diagnostic Variables
        if not gui.loadedData.analytics.empty:
            diagnosticDf = gui.loadedData.analytics.drop(columns=['name', 'timestamp#'])
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label='Diagnostics', menu=menu)
            for metric in diagnosticDf.columns.tolist():
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='Summary', menu=summary_menu)
        metrics = [[r'%coverage', 'apptime_s', 'time_s'],
                    ['num_cores', 'dataset/size', 'prefetchers', 'repetitions'],
                    ['total_pkg_energy_j', 'total_dram_energy_j', 'total_pkg+dram_energy_j'], 
                    ['total_pkg_power_w', 'total_dram_power_w', 'total_pkg+dram_power_w'],
                    ['o=inst_count_gi', 'c=inst_rate_gi/s'],
                    ['l1_rate_gb/s', 'l2_rate_gb/s', 'l3_rate_gb/s', 'ram_rate_gb/s', 'flop_rate_gflop/s', 'c=inst_rate_gi/s', 'register_addr_rate_gb/s', 'register_data_rate_gb/s', 'register_simd_rate_gb/s', 'register_rate_gb/s'],
                    [r'%ops[vec]', r'%ops[fma]', r'%ops[div]', r'%ops[sqrt]', r'%ops[rsqrt]', r'%ops[rcp]'],
                    [r'%inst[vec]', r'%inst[fma]', r'%inst[div]', r'%inst[sqrt]', r'%inst[rsqrt]', r'%inst[rcp]']]
        categories = ['Time/Coverage', 'Experiment Settings', 'Energy', 'Power', 'Instructions', 'Rates', r'%ops', r'%inst']
        for index, category in enumerate(categories):
            menu = tk.Menu(summary_menu, tearoff=False)
            summary_menu.add_cascade(label=category, menu=menu)
            for metric in metrics[index]:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        return menubutton

    def __init__(self, parent, tab, plotType):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.plotType = plotType
        # Axes metric options
        metric_label = tk.Label(self, text='Metrics:')
        self.y_selected = tk.StringVar(value='Choose Y Axis Metric')
        self.x_selected = tk.StringVar(value='Choose X Axis Metric')
        x_options = ['Choose X Axis Metric', 'C_FLOP [GFlop/s]', 'c=inst_rate_gi/s']
        if self.plotType == 'Custom':
            x_menu = AxesTab.custom_axes(self, self.x_selected)
            y_menu = AxesTab.custom_axes(self, self.y_selected)
        else:  
            if self.plotType == 'QPlot':
                y_options = ['Choose Y Axis Metric', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]']
            elif self.plotType == 'TRAWL':
                y_options = ['Choose Y Axis Metric', 'speedup[vec]', 'speedup[dl1]']
            elif self.plotType == 'Summary':
                x_options.append('reciptime_mhz')
                y_options = ['Choose Y Axis Metric', r'%coverage', 'time_s', 'apptime_s', 'reciptime_mhz']
            y_menu = tk.OptionMenu(self, self.y_selected, *y_options)
            x_menu = tk.OptionMenu(self, self.x_selected, *x_options)
            y_menu['menu'].insert_separator(1)
            x_menu['menu'].insert_separator(1)
        # Axes scale options
        scale_label = tk.Label(self, text='Scales:')
        self.yscale_selected = tk.StringVar(value='Choose Y Axis Scale')
        self.xscale_selected = tk.StringVar(value='Choose X Axis Scale')
        yscale_options = ['Choose Y Axis Scale', 'Linear', 'Log']
        xscale_options = ['Choose X Axis Scale', 'Linear', 'Log']
        yscale_menu = tk.OptionMenu(self, self.yscale_selected, *yscale_options)
        xscale_menu = tk.OptionMenu(self, self.xscale_selected, *xscale_options)
        yscale_menu['menu'].insert_separator(1)
        xscale_menu['menu'].insert_separator(1)
        # Update button to replot
        update = tk.Button(self, text='Update', command=self.update_axes)
        # Tab grid
        metric_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        scale_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        x_menu.grid(row=1, column=0, padx=5, sticky=tk.W)
        y_menu.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        xscale_menu.grid(row=1, column=1, padx=5, sticky=tk.W)
        yscale_menu.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        update.grid(row=3, column=0, padx=5, sticky=tk.NW)
    
    def update_axes(self):
        # Get user selected metrics
        if self.x_selected.get() != 'Choose X Axis Metric':
            self.tab.x_axis = self.x_selected.get()
        if self.y_selected.get() != 'Choose Y Axis Metric':
            self.tab.y_axis = self.y_selected.get()
        # Get user selected scales
        if self.xscale_selected.get() != 'Choose X Axis Scale':
            self.tab.x_scale = self.xscale_selected.get().lower()
        if self.yscale_selected.get() != 'Choose Y Axis Scale':
            self.tab.y_scale = self.yscale_selected.get().lower()
        # Save current plot states
        self.tab.plotInteraction.save_plot_state()
        # Set user selected metrics/scales if they have changed at least one
        if self.x_selected.get() != 'Choose X Axis Metric' or self.y_selected.get() != 'Choose Y Axis Metric' or self.xscale_selected.get() != 'Choose X Axis Scale' or self.yscale_selected.get() != 'Choose Y Axis Scale':
            if self.plotType == 'QPlot':
                self.tab.qplotData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale, level=self.tab.level)
            elif self.plotType == 'TRAWL':
                self.tab.trawlData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale, level=self.tab.level)
            elif self.plotType == 'Custom':
                self.tab.customData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale, level=self.tab.level)
            elif self.plotType == 'Summary':
                self.tab.coverageData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale)

class ShortNameTab(tk.Frame):
    def __init__(self, parent, level=None):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.level = level
        self.cape_path = gui.loadedData.cape_path
        self.short_names_path = gui.loadedData.short_names_path
        self.mappings_path = gui.loadedData.mappings_path

    # Create table for Labels tab and update button
    def buildLabelTable(self, df, tab):
        short_name_table = df[['name', 'timestamp#']]
        short_name_table['short_name'] = short_name_table['name']
        merged = self.getShortNames(short_name_table)
        merged = pd.merge(left=merged, right=df[['name', 'timestamp#', r'%coverage', 'color']], on=['name', 'timestamp#'], how='right')
        # sort label table by coverage to keep consistent with data table
        merged.sort_values(by=r'%coverage', ascending=False, inplace=True)
        table = Table(tab, dataframe=merged[['name', 'short_name', 'timestamp#', 'color']], showtoolbar=False, showstatusbar=True)
        table.show()
        table.redraw()
        table_button_frame = tk.Frame(tab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Update", command=lambda: self.updateLabels(table)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export", command=lambda: self.exportCSV(table)).grid(row=0, column=1)
        return table

    # Merge user input labels with current mappings and replot
    def updateLabels(self, table):
        df = table.model.df
        if self.checkForDuplicates(df):
            return
        else:
            self.addShortNames(df)
        gui.loadedData.add_data(gui.sources, update=True)
    
    def getShortNames(self, df):
        if os.path.getsize(self.short_names_path) > 0:
            existing_shorts = pd.read_csv(self.short_names_path)
            current_shorts = df[['name', 'short_name', 'timestamp#']]
            merged = pd.concat([current_shorts, existing_shorts]).drop_duplicates(['name', 'timestamp#'], keep='last').reset_index(drop=True)
        else: 
            merged = df[['name', 'short_name', 'timestamp#']]
        return merged

    def addShortNames(self, namesDf):
        if os.path.getsize(self.short_names_path) > 0:
            existing_shorts = pd.read_csv(self.short_names_path)
            new_shorts = namesDf[['name', 'short_name', 'timestamp#']]
            merged = pd.concat([existing_shorts, new_shorts]).drop_duplicates(['name', 'timestamp#'], keep='last').reset_index(drop=True)
        else: 
            merged = namesDf[['name', 'short_name', 'timestamp#']]
        merged.to_csv(self.short_names_path, index=False)

    def checkForDuplicates(self, df):
        # Check if there are duplicates short names with the same timestamp
        df.reset_index(drop=True, inplace=True)
        duplicate_rows = df.duplicated(subset=['short_name', 'timestamp#'], keep=False)
        if duplicate_rows.any():
            message = str()
            for index, row in df[duplicate_rows].iterrows():
                message = message + 'row: ' + str(index + 1) + ', short_name: ' + row['short_name'] + '\n'
            messagebox.showerror("Duplicate Short Names", "You currently have two or more duplicate short names from the same file. Please change them to continue. \n\n" \
                + message)
            return True
        return False

    def exportCSV(self, table):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        table.model.df.to_csv(export_file_path, index=False, header=True)

class MappingsTab(tk.Frame):
    def __init__(self, parent, tab, level):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.level = level
        self.mappings_path = gui.loadedData.mappings_path
        self.short_names_path = gui.loadedData.short_names_path

    def editMappings(self, before_names, after_names):
        self.win = tk.Toplevel()
        center(self.win)
        self.win.title('Edit Mappings')
        message = 'Select a before and after codelet to create a new\nmapping or remove an existing one.'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        self.before_selected = tk.StringVar(value='Choose Before Codelet')
        self.after_selected = tk.StringVar(value='Choose After Codelet')
        before_menu = tk.OptionMenu(self.win, self.before_selected, *before_names)
        after_menu = tk.OptionMenu(self.win, self.after_selected, *after_names)
        before_menu.grid(row=1, column=0, padx=10, pady=10)
        after_menu.grid(row=1, column=2, padx=10, pady=10)
        tk.Button(self.win, text="Add", command=self.addMapping).grid(row=2, column=1, padx=10, pady=10)
        tk.Button(self.win, text="Remove", command=self.removeMapping).grid(row=3, column=1, padx=10, pady=10)

    def addMapping(self):
        toAdd = pd.DataFrame()
        toAdd['before_timestamp#'] = self.source_order[0]
        toAdd['before_name'] = self.before_selected.get().split('[')[0]
        toAdd['before_short_name'] = self.before_selected.get().split('[')[1][:-1]
        toAdd['after_timestamp#'] = self.source_order[1]
        toAdd['after_name'] = self.after_selected.get().split('[')[0]
        toAdd['after_short_name'] = self.after_selected.get().split('[')[1][:-1]
        self.mappings = self.mappings.append(toAdd, ignore_index=True)
        self.updateTable()
    
    def removeMapping(self):
        self.mappings.drop(self.mappings[(self.mappings['before_name']==self.before_selected.get().split('[')[0]) & \
            (self.mappings['before_timestamp#']==self.source_order[0]) & \
            (self.mappings['after_timestamp#']==self.source_order[1]) & \
            (self.mappings['after_name']==self.after_selected.get().split('[')[0])].index, inplace=True)
        self.updateTable()
    
    def updateTable(self):
        self.table.destroy()
        self.table = Table(self, dataframe=self.mappings, showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.table.redraw()
        self.win.destroy()

    def updateMappings(self):
        # Replace any previous mappings for the current files with the current mappings in the table
        self.all_mappings = self.all_mappings.loc[(self.all_mappings['before_timestamp#']!=self.source_order[0]) & \
                                (self.all_mappings['after_timestamp#']!=self.source_order[1])].reset_index(drop=True)
        self.all_mappings = self.all_mappings.append(self.mappings, ignore_index=True)
        self.all_mappings.to_csv(self.mappings_path, index=False)
        # TODO: Extend custom mappings to other tabs instead of only qplot
        self.tab.qplotData.notify(gui.loadedData, level=self.level, update=True)

    def buildMappingsTab(self, df, mappings):
        self.df = df
        self.all_mappings = pd.read_csv(self.mappings_path)
        self.source_order = gui.loadedData.source_order
        self.mappings = mappings
        self.table = Table(self, dataframe=mappings, showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.table.redraw()
        if gui.loadedData.removedIntermediates: tk.Button(self, text="Show Intermediates", command=self.showIntermediates).grid(row=3, column=1)
        else: tk.Button(self, text="Remove Intermediates", command=self.removeIntermediates).grid(row=3, column=1)
        # Add options for custom mapppings if multiple files loaded
        if len(self.source_order) > 1: self.addCustomOptions(df)

    def addCustomOptions(self, df):
        before = df.loc[df['timestamp#'] == self.source_order[0]]
        after = df.loc[df['timestamp#'] == self.source_order[1]]
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            for index in before.index:
                short_name = short_names.loc[(short_names['name']==before['name'][index]) & (short_names['timestamp#']==self.source_order[0])].reset_index(drop=True)
                if not short_name.empty: # Add short name to end of full codelet name in brackets
                    before['name'][index] += '[' + short_name['short_name'][0] + ']'
            for index in after.index:
                short_name = short_names.loc[(short_names['name']==after['name'][index]) & (short_names['timestamp#']==self.source_order[1])].reset_index(drop=True)
                if not short_name.empty: after['name'][index] = after['name'][index] + '[' + \
                    short_name['short_name'][0] + ']'
        tk.Button(self, text="Edit", command=lambda before=list(before['name']), after=list(after['name']) : \
            self.editMappings(before, after)).grid(row=10, column=0)
        tk.Button(self, text="Update", command=self.updateMappings).grid(row=10, column=1, sticky=tk.W)

    def showIntermediates(self):
        gui.loadedData.mapping = gui.loadedData.orig_mapping.copy(deep=True)
        gui.loadedData.add_speedup(gui.loadedData.mapping, gui.loadedData.summaryDf)
        gui.loadedData.removedIntermediates = False
        data_tab_pairs = [(gui.qplotData, gui.c_qplotTab), (gui.trawlData, gui.c_trawlTab), (gui.siplotData, gui.c_siPlotTab), (gui.customData, gui.c_customTab), (gui.coverageData, gui.summaryTab)]
        for data, tab in data_tab_pairs:
            data.notify(gui.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.current_variants, scale=tab.x_scale+tab.y_scale)
    
    def cancelAction(self):
        self.choice = 'cancel'
        self.win.destroy()

    def selectAction(self, metric):
        self.choice = metric
        self.win.destroy()
    
    def removeIntermediates(self):
        # Ask the user which speedup metric they'd like to use for end2end transitions
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
        self.win.title('Select Speedup')
        message = 'Select the speedup to maximize for\nend-to-end transitions.'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        for index, metric in enumerate(['Speedup[Time (s)]', 'Speedup[AppTime (s)]', 'Speedup[FLOP Rate (GFLOP/s)]']):
            b = tk.Button(self.win, text=metric)
            b['command'] = lambda metric=metric : self.selectAction(metric) 
            b.grid(row=index+1, column=1, padx=20, pady=10)
        root.wait_window(self.win)
        if self.choice == 'cancel': return
        gui.loadedData.mapping = gui.loadedData.get_end2end(gui.loadedData.mapping, self.choice)
        gui.loadedData.mapping = gui.loadedData.get_speedups(gui.loadedData.mapping)
        gui.loadedData.add_speedup(gui.loadedData.mapping, gui.loadedData.summaryDf)
        gui.loadedData.removedIntermediates = True
        data_tab_pairs = [(gui.qplotData, gui.c_qplotTab), (gui.trawlData, gui.c_trawlTab), (gui.siplotData, gui.c_siPlotTab), (gui.customData, gui.c_customTab), (gui.coverageData, gui.summaryTab)]
        for data, tab in data_tab_pairs:
            data.notify(gui.loadedData, x_axis=tab.x_axis, y_axis=tab.y_axis, variants=tab.current_variants, scale=tab.x_scale+tab.y_scale)

class ClusterTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.cluster_path = resource_path('clusters')
        self.cluster_selected = tk.StringVar(value='Choose Cluster')
        cluster_options = ['Choose Cluster']
        for cluster in os.listdir(self.cluster_path):
            cluster_options.append(cluster[:-4])
        self.cluster_menu = tk.OptionMenu(self, self.cluster_selected, *cluster_options)
        self.cluster_menu['menu'].insert_separator(1)
        update = tk.Button(self, text='Update', command=self.update)
        self.cluster_menu.pack(side=tk.LEFT, anchor=tk.NW)
        update.pack(side=tk.LEFT, anchor=tk.NW)
    
    def update(self):
        if self.cluster_selected.get() != 'Choose Cluster':
            path = os.path.join(self.cluster_path, self.cluster_selected.get() + '.csv')
            self.tab.cluster = path
            self.tab.title = self.cluster_selected.get()
            self.tab.siplotData.notify(gui.loadedData, variants=self.tab.current_variants, update=True, cluster=path, title=self.cluster_selected.get())

class ChecklistBox(tk.Frame):
    def __init__(self, parent, choices, current_choices, listType='', tab=None, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent=parent
        self.tab=tab
        scrollbar = tk.Scrollbar(self)
        scrollbar_x = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        checklist = tk.Text(self, width=40)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        checklist.pack(fill=tk.Y, expand=True)
        self.vars = []
        self.names = []
        self.cbs = []
        bg = self.cget("background")
        for index, choice in enumerate(choices):
            var = tk.IntVar(value=1)
            if choice not in current_choices:
                var.set(0)
            self.vars.append(var)
            self.names.append(choice.split(' ', 1)[-1].rsplit(' ', 1)[0] + choice.rsplit(' ', 1)[-1][1:-1])
            cb = tk.Checkbutton(self, var=var, text=choice,
                                onvalue=1, offvalue=0,
                                anchor="w", width=100, background=bg,
                                relief="flat", highlightthickness=0
            )
            self.cbs.append(cb)
            if listType == 'pointSelector':
                cb['command'] = lambda name=self.names[index], index=index : self.updatePlot(name, index)
            checklist.window_create("end", window=cb)
            checklist.insert("end", "\n")
        checklist.config(yscrollcommand=scrollbar.set)
        checklist.config(xscrollcommand=scrollbar_x.set)
        scrollbar.config(command=checklist.yview)
        scrollbar_x.config(command=checklist.xview)
        checklist.configure(state="disabled")

    def restoreState(self, dictionary):
        for name in dictionary['hidden_names']:
            try: 
                index = self.names.index(name)
                self.vars[index].set(0)
            except: pass

    def updatePlot(self, name, index):
        selected = self.vars[index].get()
        if selected:
            for tab in self.tab.tabs:
                tab.plotInteraction.pointSelector.vars[index].set(1)
                marker = tab.plotInteraction.textData['name:marker'][name]
                marker.set_alpha(1)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(1)
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(True)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][name]:
                        mapping.set_alpha(1)
                except: pass
                tab.plotInteraction.canvas.draw()
        else:
            for tab in self.tab.tabs:
                tab.plotInteraction.pointSelector.vars[index].set(0)
                marker = tab.plotInteraction.textData['name:marker'][name]
                marker.set_alpha(0)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(0)
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(False)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][name]:
                        mapping.set_alpha(0)
                except: pass
                tab.plotInteraction.canvas.draw()

    def getCheckedItems(self):
        values = []
        for i, cb in enumerate(self.cbs):
            value =  self.vars[i].get()
            if value:
                values.append(cb['text'])
        return values

    def showAllVariants(self):
        for i, cb in enumerate(self.cbs):
            self.vars[i].set(1)
        self.updateVariants() 
    
    def showOrig(self):
        for i, cb in enumerate(self.cbs):
            if cb['text'] == 'ORIG': self.vars[i].set(1)
            else: self.vars[i].set(0)
        self.updateVariants()

    def updateVariants(self):
        self.parent.tab.current_variants = self.getCheckedItems()
        # Update the rest of the plots at the same level with the new checked variants
        for tab in self.parent.tab.plotInteraction.tabs:
            for i, cb in enumerate(self.cbs):
                tab.variantTab.checkListBox.vars[i].set(self.vars[i].get())
            tab.current_variants = self.parent.tab.current_variants
        self.parent.tab.plotInteraction.save_plot_state()
        for tab in self.parent.tab.plotInteraction.tabs:
            if tab.name == 'SIPlot': tab.data.notify(gui.loadedData, variants=tab.current_variants, x_axis=tab.x_axis, y_axis=tab.y_axis, scale=tab.x_scale+tab.y_scale, update=True, cluster=tab.cluster, title=tab.title)
            else: tab.data.notify(gui.loadedData, variants=tab.current_variants, x_axis=tab.x_axis, y_axis=tab.y_axis, scale=tab.x_scale+tab.y_scale, update=True)

class VariantTab(tk.Frame):
    def __init__(self, parent, tab, variants, current_variants):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.checkListBox = ChecklistBox(self, variants, current_variants, bd=1, relief="sunken", background="white")
        update = tk.Button(self, text='Update', command=self.checkListBox.updateVariants)
        self.checkListBox.pack(side=tk.LEFT)
        update.pack(side=tk.LEFT, anchor=tk.NW)

class LabelTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.metric1 = tk.StringVar(value='Metric 1')
        self.metric2 = tk.StringVar(value='Metric 2')
        self.metric3 = tk.StringVar(value='Metric 3')
        self.menu1 = AxesTab.custom_axes(self, self.metric1)
        self.menu2 = AxesTab.custom_axes(self, self.metric2)
        self.menu3 = AxesTab.custom_axes(self, self.metric3)
        self.updateButton = tk.Button(self, text='Update', command=self.updateLabels)
        self.resetButton = tk.Button(self, text='Reset', command=self.reset)
        # Grid layout 
        self.menu1.grid(row=0, column=0, padx = 10, pady=10, sticky=tk.NW)
        self.menu2.grid(row=0, column=1, pady=10, sticky=tk.NW)
        self.menu3.grid(row=0, column=2, padx = 10, pady=10, sticky=tk.NW)
        self.updateButton.grid(row=1, column=0, padx=10, sticky=tk.NW)
        self.resetButton.grid(row=1, column=1, sticky=tk.NW)

    def resetMetrics(self):
        self.metric1.set('Metric 1')
        self.metric2.set('Metric 2')
        self.metric3.set('Metric 3')

    def reset(self):
        self.resetMetrics()
        textData = self.tab.plotInteraction.textData
        self.tab.current_labels = []
        for i, text in enumerate(textData['texts']):
            text.set_text(textData['orig_mytext'][i])
            textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
            textData['legend'].get_title().set_text(textData['orig_legend'])
        self.tab.plotInteraction.canvas.draw()
        # Adjust labels if already adjusted
        if self.tab.plotInteraction.adjusted:
            self.tab.plotInteraction.adjustText()

    def updateLabels(self):
        current_metrics = []
        if self.metric1.get() != 'Metric 1': current_metrics.append(self.metric1.get())
        if self.metric2.get() != 'Metric 2': current_metrics.append(self.metric2.get())
        if self.metric3.get() != 'Metric 3': current_metrics.append(self.metric3.get())
        if not current_metrics: return # User hasn't selected any label metrics
        self.tab.current_labels = current_metrics
        textData = self.tab.plotInteraction.textData

        # TODO: Update the rest of the plots at the same level with the new checked variants
        # for tab in self.parent.tab.plotInteraction.tabs:
        #     for i, cb in enumerate(self.cbs):
        #         tab.labelTab.checkListBox.vars[i].set(self.vars[i].get())
        #     tab.current_labels = self.parent.tab.current_labels

        # If nothing selected, revert labels and legend back to original
        if not self.tab.current_labels:
            for i, text in enumerate(textData['texts']):
                text.set_text(textData['orig_mytext'][i])
                textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
                textData['legend'].get_title().set_text(textData['orig_legend'])
        else: 
            # Update existing plot texts by adding user specified metrics
            df = self.tab.plotInteraction.df
            for i, text in enumerate(textData['texts']):
                toAdd = textData['orig_mytext'][i][:-1]
                for choice in self.tab.current_labels:
                    codeletName = textData['names'][i]
                    # TODO: Clean this up so it's on the edges and not the data points
                    if choice in ['Speedup[Time (s)]', 'Speedup[AppTime (s)]', 'Speedup[FLOP Rate (GFLOP/s)]', 'Difference']:
                        tempDf = pd.DataFrame()
                        if not self.tab.mappings.empty: # Mapping
                            tempDf = self.tab.mappings.loc[(self.tab.mappings['before_name']+self.tab.mappings['before_timestamp#'].astype(str))==codeletName]
                        if tempDf.empty: 
                            if choice == 'Difference': 
                                tempDf = self.tab.mappings.loc[(self.tab.mappings['after_name']+self.tab.mappings['after_timestamp#'].astype(str))==codeletName]
                                if tempDf.empty:
                                    value = 'Same'
                            else: value = 1
                        else: value = tempDf[choice].iloc[0]
                    else:
                        value = df.loc[(df['name']+df['timestamp#'].astype(str))==codeletName][choice].iloc[0]
                    if isinstance(value, int) or isinstance(value, float):
                        toAdd += ', ' + str(round(value, 2))
                    else:
                        toAdd += ', ' + str(value)
                toAdd += ')'
                text.set_text(toAdd)
                textData['mytext'][i] = toAdd
            # Update legend for user to see order of metrics in the label
            newTitle = textData['orig_legend'][:-1]
            for choice in self.tab.current_labels:
                newTitle += ', ' + choice
            newTitle += ')'
            textData['legend'].get_title().set_text(newTitle)
        self.tab.plotInteraction.canvas.draw()
        # Adjust labels if already adjusted
        if self.tab.plotInteraction.adjusted:
            self.tab.plotInteraction.adjustText()

class FilteringTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        # Metric drop down menu
        self.metric_selected = tk.StringVar(value='Choose Metric')
        to_remove = ['name', 'short_name', 'variant', 'timestamp#', 'color']
        metric_options = [metric for metric in tab.summaryDf.columns.tolist() if metric not in to_remove]
        metric_options.insert(0, 'Choose Metric')
        self.metric_menu = tk.OptionMenu(self, self.metric_selected, *metric_options)
        self.metric_menu['menu'].insert_separator(1)
        # Min threshold option
        min_label = tk.Label(self, text='Min Threshold: ')
        self.min_num = tk.IntVar()
        self.min_entry = tk.Entry(self, textvariable=self.min_num)
        # Max threshold option
        max_label = tk.Label(self, text='Max Threshold: ')
        self.max_num = tk.IntVar()
        self.max_entry = tk.Entry(self, textvariable=self.max_num)
        # Grid setup
        update = tk.Button(self, text='Update', command=self.update)
        self.metric_menu.grid(row=0, column=0)
        min_label.grid(row=1, column=0)
        self.min_entry.grid(row=1, column=1)
        max_label.grid(row=2, column=0)
        self.max_entry.grid(row=2, column=1)
        update.grid(row=3, column=0)

    def update(self):
        if self.metric_selected.get() == 'Choose Metric': pass
        else:
            filter_data = (self.metric_selected.get(), self.min_num.get(), self.max_num.get())
            gui.siplotData.notify(gui.loadedData, variants=self.tab.current_variants, update=True, cluster=self.tab.cluster, title=self.tab.title, \
                filtering=True, filter_data=filter_data)

class GuideTab(tk.Frame):
    class ATab(tk.Frame):
        def __init__(self, parent):
            tk.Frame.__init__(self, parent)
            self.parent = parent
            self.tab = parent.tab
            # Text for states
            self.a_state = 'State: A-Start'
            self.a1_state = 'State: A1'
            # self.a1_state = 'State: B1'
            self.a1_trans_state = 'State: A11'
            self.a2_state = 'State: A2'
            # self.a2_state = 'State: B2'
            self.a3_state = 'State: A3'
            # self.a3_state = 'State: B-End'
            self.a_end_state = 'State: A-End'
            # self.a_end_state = 'State: End'
            self.title = self.tab.plotInteraction.textData['title']
            # Initial Title
            self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a_state, pad=40)
            # Temporary hardcoded points for each state
            self.a2_points = ['livermore_default: lloops.c_kernels_line1340_01587402719', 'NPB_2.3-OpenACC-C: sp.c_compute_rhs_line1452_01587402719']
            self.a3_points = ['TSVC_default: tsc.c_vbor_line5367_01587481116', 'NPB_2.3-OpenACC-C: cg.c_conj_grad_line549_01587481116', 'NPB_2.3-OpenACC-C: lu.c_pintgr_line2019_01587481116']
            # Labels for the current state of the plot
            self.customFont = tk.font.Font(family="Helvetica", size=11)
            self.aLabel = tk.Label(self, text=self.a_state, borderwidth=2, relief="solid", font=self.customFont, padx=10)
            # Buttons: Next (go to next level of filtering), Previous, Transitions (show transitions for the current codelets)
            self.nextButton = tk.Button(self, text='Next State', command=self.nextState)
            self.prevButton = tk.Button(self, text='Previous State', command=self.prevState)
            self.transButton = tk.Button(self, text='Show Transitions', command=self.toggleTrans)
            # Grid layout
            self.aLabel.grid(row=0, column=0, pady=10, padx=10, sticky=tk.NW)
            self.nextButton.grid(row=1, column=0, padx=10, sticky=tk.NW)
            if gui.loadedData.transitions == 'showing': self.show_trans_state()
            elif gui.loadedData.transitions == 'hiding': self.hide_trans_state()


        def nextState(self):
            if self.aLabel['text'] == self.a_state: # Go to A1 (SIDO) state
                self.aLabel['text'] = self.a1_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a1_state, pad=40)
                self.prevButton.grid(row=2, column=0, padx=10, pady=10, sticky=tk.NW)
                self.transButton.grid(row=3, column=0, padx=10, sticky=tk.NW)
                self.a1_highlighted = self.tab.plotInteraction.A_filter(relate=operator.gt, metric='Speedup[Time (s)]', threshold=1, highlight=True) # Highlight SIDO codelets
                self.updateLabels('Speedup[Time (s)]')
            elif self.aLabel['text'] == self.a1_state: # Go to A2 (RHS=1) state
                self.aLabel['text'] = self.a2_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a2_state, pad=40)
                self.transButton.grid_remove()
                self.tab.plotInteraction.A_filter(relate=operator.gt, metric='Speedup[Time (s)]', threshold=1, highlight=False, remove=True) # Remove SIDO codelets
                self.a2_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='rhs_op_count', threshold=1, highlight=True, points=self.a2_points) # Highlight RHS codelets
                self.updateLabels('rhs_op_count')
            elif self.aLabel['text'] == self.a2_state: # Go to A3 (FMA) state
                self.aLabel['text'] = self.a3_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a3_state, pad=40)
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='rhs_op_count', threshold=1, highlight=False, remove=True, points=self.a2_points) # Remove RHS codelets
                self.a3_highlighted = self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, points=self.a3_points) # Highlight FMA codelets
                self.updateLabels(r'%ops[fma]')
            elif self.aLabel['text'] == self.a3_state: # Go to A_END state
                self.aLabel['text'] = self.a_end_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a_end_state, pad=40)
                self.nextButton.grid_remove()
                self.all_highlighted = self.a1_highlighted + self.a2_highlighted + self.a3_highlighted
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True, points=self.all_highlighted) # Highlight all previously highlighted codelets
                self.updateLabels('advice')
        
        def prevState(self):
            if self.aLabel['text'] == self.a1_state: # Go back to the starting view
                self.aLabel['text'] = self.a_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title, pad=40)
                self.prevButton.grid_remove()
                self.transButton.grid_remove()
                self.tab.plotInteraction.A_filter(relate=operator.gt, metric='Speedup[Time (s)]', threshold=1, highlight=False)
                self.tab.labelTab.reset()
            elif self.aLabel['text'] == self.a2_state: # Go back to A1 (SIDO) state
                self.aLabel['text'] = self.a1_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a1_state, pad=40)
                self.transButton.grid(row=3, column=0, padx=10, sticky=tk.NW)
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='rhs_op_count', threshold=1, highlight=False, points=self.a2_points)
                self.tab.plotInteraction.A_filter(relate=operator.gt, metric='Speedup[Time (s)]', threshold=1, highlight=True, show=True)
                self.updateLabels('Speedup[Time (s)]')
            elif self.aLabel['text'] == self.a3_state: # Go back to A2 (RHS=1) state
                self.aLabel['text'] = self.a2_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a2_state, pad=40)
                self.nextButton.grid()
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=False, points=self.a3_points)
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='rhs_op_count', threshold=1, highlight=True, show=True, points=self.a2_points)
                self.updateLabels('rhs_op_count')
            elif self.aLabel['text'] == self.a_end_state: # Go back to A3 (FMA) state
                self.aLabel['text'] = self.a3_state
                self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a3_state, pad=40)
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=False, remove=True, points=self.all_highlighted)
                self.tab.plotInteraction.A_filter(relate=operator.eq, metric='', threshold=1, highlight=True, show=True, points=self.a3_points)
                self.updateLabels(r'%ops[fma]')

        def toggleTrans(self):
            if self.transButton['text'] == 'Show Transitions':
                gui.loadedData.transitions = 'showing'
                # Remove any points that aren't currently highglighted
                for name in self.tab.plotInteraction.textData['names']:
                    if name not in self.a1_highlighted:
                        self.tab.plotInteraction.togglePoint(self.tab.plotInteraction.textData['name:marker'][name], visible=False)
                # Auto-check all variants and call update variants
                self.tab.variantTab.checkListBox.showAllVariants()
            else:
                gui.loadedData.transitions = 'hiding'
                self.tab.plotInteraction.showMarkers()
                self.tab.variantTab.checkListBox.showOrig()

        def show_trans_state(self):
            self.nextButton.grid_remove()
            self.transButton.grid(row=3, column=0, padx=10, sticky=tk.NW)
            self.aLabel['text'] = self.a1_trans_state
            self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a1_trans_state, pad=40)
            self.updateLabels('Speedup[Time (s)]')
            self.transButton['text'] = 'Hide Transitions'
        
        def hide_trans_state(self):
            self.prevButton.grid(row=2, column=0, padx=10, pady=10, sticky=tk.NW)
            self.transButton.grid(row=3, column=0, padx=10, sticky=tk.NW)
            self.aLabel['text'] = self.a1_state
            self.tab.plotInteraction.textData['ax'].set_title(self.title + ', ' + self.a1_state, pad=40)
            self.updateLabels('Speedup[Time (s)]')
            self.a1_highlighted = gui.loadedData.c_plot_state['highlighted_names']
            self.transButton['text'] = 'Show Transitions'

        def updateLabels(self, metric):
            self.tab.labelTab.resetMetrics()
            self.tab.labelTab.metric1.set(metric)
            self.tab.labelTab.updateLabels()
            

    class BTab(tk.Frame):
        def __init__(self, parent):
            tk.Frame.__init__(self, parent)

    class CTab(tk.Frame):
        def __init__(self, parent):
            tk.Frame.__init__(self, parent)

    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.guideNote = ttk.Notebook(self)
        # A, B, C are tabs in the GuideTab (Currently only have A tab defined)
        self.aTab = GuideTab.ATab(self)
        self.bTab = GuideTab.BTab(self)
        self.cTab = GuideTab.CTab(self)
        # Add buttons to Guide Tab
        self.guideNote.add(self.aTab, text="A")
        self.guideNote.add(self.bTab, text="B")
        self.guideNote.add(self.cTab, text="C")
        self.guideNote.pack(fill=tk.BOTH, expand=True)


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

    def loadPage(self):
        if len(gui.urls) == 1: self.loadFirstPage()
        elif len(gui.urls) > 1: self.loadSecondPage()
    
    def loadFirstPage(self):
        self.removePages()
        self.browser1 = BrowserFrame(self.window)
        self.window.add(self.browser1, stretch='always')
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
        current_tab = gui.main_note.select()
        gui.main_note.select(0)
        self.update()
        gui.main_note.select(current_tab)
        self.browser1.change_browser(url=gui.urls[0])
        self.browser2.change_browser(url=gui.urls[1])

    def removePages(self):
        if self.browser1:
            self.window.remove(self.browser1)
        if self.browser2:
            self.window.remove(self.browser2)

class TrawlTab(tk.Frame):
    def __init__(self, parent, trawlData, level):
        tk.Frame.__init__(self, parent)
        if trawlData is not None:
           trawlData.add_observers(self)
        self.name = 'TRAWL'
        self.level = level
        self.trawlData = self.data = trawlData
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = 'speedup[vec]'
        self.current_variants = ['ORIG']
        self.current_labels = []
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData=None, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        # Data table/tabs setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.extend(['speedup[vec]', 'speedup[dl1]'])
        if not gui.loadedData.analytics.empty:
            diagnosticDf = gui.loadedData.analytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        column_list.extend(gui.loadedData.common_columns_end)
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: gui.summaryTab.exportCSV()).grid(row=0, column=1)

        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if not mappings.empty:
            self.mappingsTab.buildMappingsTab(df, mappings)

    # Create tabs for TRAWL Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'TRAWL')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, trawlData):
        if self.level == 'Codelet':
            df = trawlData.df
            fig = trawlData.fig
            mappings = trawlData.mappings
            variants = trawlData.variants
            textData = trawlData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)

        elif self.level == 'Source':
            df = trawlData.srcDf
            fig = trawlData.srcFig
            mappings = trawlData.src_mapping
            variants = trawlData.src_variants
            textData = trawlData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)

        elif self.level == 'Application':
            df = trawlData.appDf
            fig = trawlData.appFig
            mappings = trawlData.app_mapping
            variants = trawlData.app_variants
            textData = trawlData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)

class QPlotTab(tk.Frame):
    def __init__(self, parent, qplotData, level):
        tk.Frame.__init__(self, parent)
        if qplotData is not None:
           qplotData.add_observers(self)
        self.name = 'QPlot'
        self.level = level
        self.qplotData = self.data = qplotData
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = 'C_max [GB/s]'
        self.current_variants = ['ORIG']
        self.current_labels = []
        # QPlot tab has a paned window with the data tables and qplot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData=None, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot/Table setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        # Summary Data Table
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
                'C_RAM [GB/s]', 'C_max [GB/s]'])
        if not gui.loadedData.analytics.empty:
            diagnosticDf = gui.loadedData.analytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        column_list.extend(gui.loadedData.common_columns_end)
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: gui.summaryTab.exportCSV()).grid(row=0, column=1)

        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if not mappings.empty:
            self.mappingsTab.buildMappingsTab(df, mappings)

    # Create tabs for QPlot Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'QPlot')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, qplotData):
        if self.level == 'Codelet':
            df = qplotData.df
            fig = qplotData.fig
            mappings = qplotData.mappings
            variants = qplotData.variants
            textData = qplotData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

        elif self.level == 'Source':
            df = qplotData.srcDf
            fig = qplotData.srcFig
            mappings = qplotData.src_mapping
            variants = qplotData.src_variants
            textData = qplotData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

        elif self.level == 'Application':
            df = qplotData.appDf
            fig = qplotData.appFig
            mappings = qplotData.app_mapping
            variants = qplotData.app_variants
            textData = qplotData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

class SIPlotTab(tk.Frame):
    def __init__(self, parent, siplotData, level):
        tk.Frame.__init__(self, parent)
        if siplotData is not None:
            siplotData.add_observers(self)
        self.name = 'SIPlot'
        self.level = level
        self.siplotData = self.data = siplotData
        self.cluster = resource_path(os.path.join('clusters', 'FE_tier1.csv'))
        self.title = 'FE_tier1'
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'Intensity'
        self.y_axis = self.orig_y_axis = 'Saturation'
        self.current_variants = ['ORIG']
        self.current_labels = []
        # SIPlot tab has a paned window with the data tables and sipLot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)
    
    def update(self, df, fig, textData=None, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        self.mappings = mappings
        # Plot/Table Setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        # Summary Data table
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.extend(['Saturation', 'Intensity', 'SI'])
        # Add diagnostic variables to summary data table
        if not gui.loadedData.analytics.empty:
            diagnosticDf = gui.loadedData.analytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        # column_list.extend(['Saturation', 'Intensity', 'SI', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
        #       'C_RAM [GB/s]', 'C_max [GB/s]'])
        column_list.extend(gui.loadedData.common_columns_end)
        self.summaryDf = df[column_list]
        self.buildTableTabs()
        self.summaryDf = self.summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=self.summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: gui.summaryTab.exportCSV()).grid(row=0, column=1)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if (self.level == 'Codelet') and not gui.loadedData.mapping.empty:
            self.mappingsTab.buildMappingsTab(df, mappings)

    # Create tabs for QPlot Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.clusterTab = ClusterTab(self.tableNote, self)
        self.filteringTab = FilteringTab(self.tableNote, self)
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.clusterTab, text='Clusters')
        self.tableNote.add(self.filteringTab, text='Filtering')
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, siplotData):
        for w in self.window.winfo_children():
            w.destroy()
        self.update(siplotData.df, siplotData.fig, textData=siplotData.textData, mappings=siplotData.mappings, variants=siplotData.variants)

class CustomTab(tk.Frame):
    def __init__(self, parent, customData, level):
        tk.Frame.__init__(self, parent)
        if customData is not None:
            customData.add_observers(self)
        self.name = 'Custom'
        self.level = level
        self.customData = self.data = customData
        self.current_variants = ['ORIG']
        self.x_scale = self.orig_x_scale = 'linear'
        self.y_scale = self.orig_y_scale = 'linear'
        self.x_axis = self.orig_x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = self.orig_y_axis = r'%coverage'
        self.current_labels = []
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData, variants=None, mappings=pd.DataFrame()):
        self.variants = variants
        self.mappings = mappings
        # Plot setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        # Data table/tabs under plot setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.remove(r'%ops[fma]')
        column_list.remove(r'%inst[fma]')
        column_list.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
            'C_RAM [GB/s]', 'C_max [GB/s]', 'C_FLOP [GFlop/s]', 'speedup[vec]', 'speedup[dl1]', \
            'num_cores', 'dataset/size', 'prefetchers', 'repetitions', \
            'total_pkg_energy_j', 'total_dram_energy_j', 'total_pkg+dram_energy_j', 'total_pkg_power_w', 'total_dram_power_w', 'total_pkg+dram_power_w', \
            'o=inst_count_gi', 'c=inst_rate_gi/s', \
            'l1_rate_gb/s', 'l2_rate_gb/s', 'l3_rate_gb/s', 'ram_rate_gb/s', 'flop_rate_gflop/s', 'register_addr_rate_gb/s', 'register_data_rate_gb/s', 'register_simd_rate_gb/s', 'register_rate_gb/s', \
            r'%ops[vec]', r'%ops[fma]', r'%ops[div]', r'%ops[sqrt]', r'%ops[rsqrt]', r'%ops[rcp]', \
            r'%inst[vec]', r'%inst[fma]', r'%inst[div]', r'%inst[sqrt]', r'%inst[rsqrt]', r'%inst[rcp]', \
            'timestamp#', 'color'])
        if not gui.loadedData.analytics.empty:
            diagnosticDf = gui.loadedData.analytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        if not mappings.empty:
            column_list.extend(['Speedup[Time (s)]', 'Speedup[AppTime (s)]', 'Speedup[FLOP Rate (GFLOP/s)]'])
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(summary_pt)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: gui.summaryTab.exportCSV()).grid(row=0, column=1)
        
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if not mappings.empty:
            self.mappingsTab.buildMappingsTab(df, mappings)
    
    # Create tabs for Custom Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        self.mappingsTab = MappingsTab(self.tableNote, self, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, customData):
        if self.level == 'Codelet':
            df = customData.df
            fig = customData.fig
            mappings = customData.mappings
            variants = customData.variants
            textData = customData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants, mappings=mappings)

        elif self.level == 'Source':
            df = customData.srcDf
            fig = customData.srcFig
            mappings = customData.src_mapping
            variants = customData.src_variants
            textData = customData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants, mappings=mappings)

        elif self.level == 'Application':
            df = customData.appDf
            fig = customData.appFig
            mappings = customData.app_mapping
            variants = customData.app_variants
            textData = customData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants, mappings=mappings)

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

        self.pw=tk.PanedWindow(parent, orient="horizontal")

        self.explorerPanel = ExplorerPanel(self.pw, self.loadFile, self.loadSavedState)
        self.explorerPanel.pack(side = tk.LEFT)
        self.pw.add(self.explorerPanel)
        right = self.buildTabs(self.pw)
        right.pack(side = tk.LEFT)
        self.pw.add(right)
        self.pw.pack(fill=tk.BOTH,expand=True)
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
        
    def loadSavedState(self, df=pd.DataFrame(), mappings=pd.DataFrame(), analytics=pd.DataFrame(), data={}):
        print("restore: ", self.loadedData.restore)
        if len(self.sources) >= 1:
            self.win = tk.Toplevel()
            center(self.win)
            self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
            self.win.title('Existing Data')
            if not self.loadedData.restore: message = 'This tool currently doesn\'t support appending server data with\nAnalysis Results data. Would you like to overwrite\nany existing plots with this new data?'
            else: 
                message = 'Would you like to append to the existing\ndata or overwrite with the new data?'
                tk.Button(self.win, text='Append', command= lambda df=df, mappings=mappings, analytics=analytics, data=data : self.appendAnalysisData(df, mappings, analytics, data)).grid(row=1, column=0, sticky=tk.E)
            tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
            tk.Button(self.win, text='Overwrite', command=self.overwriteData).grid(row=1, column=1)
            tk.Button(self.win, text='Cancel', command=self.cancelAction).grid(row=1, column=2, pady=10, sticky=tk.W)
            root.wait_window(self.win)
        if self.choice == 'Cancel': return
        self.source_order = []
        self.sources = ['Analysis Result'] # Don't need the actual source path for Analysis Results
        self.loadedData.add_saved_data(df, mappings=mappings, analytics=analytics, data=data)

    def loadFile(self, choice, data_dir, source, url):
        if choice == 'Open Webpage':
            self.overwrite()
            self.urls = [url]
            self.oneviewTab.loadPage()
            return
        elif choice == 'Overwrite':
            self.overwrite()
            if url: 
                self.urls = [url]
                self.oneviewTab.loadPage()
            self.sources = [source]
        elif choice == 'Append':
            if url: 
                self.urls.append(url)
                self.oneviewTab.loadPage()
            self.sources.append(source)
        self.loadedData.add_data(self.sources, data_dir)

    def overwrite(self): # Clear out any previous saved dataframes/plots
        self.sources = []
        gui.loadedData.analytics = pd.DataFrame()
        gui.loadedData.mapping = pd.DataFrame()
        gui.loadedData.names = pd.DataFrame()
        gui.oneviewTab.removePages() # Remove any previous OV HTML
        self.clearTabs()

    def clearTabs(self, levels=['All']):
        tabs = []
        if 'Codelet' in levels or 'All' in levels:
            tabs.extend([gui.summaryTab, gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab])
        if 'Source' in levels or 'All' in levels:
            tabs.extend([gui.s_trawlTab, gui.s_qplotTab, gui.s_siPlotTab, gui.s_customTab])
        if 'Application' in levels or 'All' in levels:
            tabs.extend([gui.a_trawlTab, gui.a_qplotTab, gui.a_siPlotTab, gui.a_customTab])
        for tab in tabs:
            for widget in tab.window.winfo_children():
                widget.destroy()

    def buildTabs(self, parent):
        # 1st level notebook
        self.main_note = ttk.Notebook(parent)
        self.applicationTab = ApplicationTab(self.main_note)
        self.sourceTab = SourceTab(self.main_note)
        self.codeletTab = CodeletTab(self.main_note)
        self.oneviewTab = OneviewTab(self.main_note)
        self.coverageData = CoverageData(self.loadedData)
        self.summaryTab = SummaryTab(self.main_note, self.coverageData, 'Codelet')
        self.main_note.add(self.oneviewTab, text="Oneview")
        self.main_note.add(self.summaryTab, text="Summary")
        self.main_note.add(self.applicationTab, text="Application")
        self.main_note.add(self.sourceTab, text="Source")
        self.main_note.add(self.codeletTab, text="Codelet")
        # Application, Source, and Codelet each have their own 2nd level tabs
        application_note = ttk.Notebook(self.applicationTab)
        source_note = ttk.Notebook(self.sourceTab)
        codelet_note = ttk.Notebook(self.codeletTab)
        # Codelet tabs
        self.siplotData = SIPlotData(self.loadedData)
        self.qplotData = QPlotData(self.loadedData)
        self.trawlData = TRAWLData(self.loadedData)
        self.customData = CustomData(self.loadedData)
        self.c_trawlTab = TrawlTab(codelet_note, self.trawlData, 'Codelet')
        self.c_qplotTab = QPlotTab(codelet_note, self.qplotData, 'Codelet')
        self.c_siPlotTab = SIPlotTab(codelet_note, self.siplotData, 'Codelet')
        self.c_customTab = CustomTab(codelet_note, self.customData, 'Codelet')
        codelet_note.add(self.c_trawlTab, text="TRAWL")
        codelet_note.add(self.c_qplotTab, text="QPlot")
        codelet_note.add(self.c_siPlotTab, text="SI Plot")
        codelet_note.add(self.c_customTab, text="Custom")
        codelet_note.pack(fill=tk.BOTH, expand=1)
        # Source Tabs
        self.s_trawlTab = TrawlTab(source_note, self.trawlData, 'Source')
        self.s_qplotTab = QPlotTab(source_note, self.qplotData, 'Source')
        self.s_siPlotTab = SIPlotTab(source_note, self.siplotData, 'Source')
        self.s_customTab = CustomTab(source_note, self.customData, 'Source')
        source_note.add(self.s_trawlTab, text="TRAWL")
        source_note.add(self.s_qplotTab, text="QPlot")
        source_note.add(self.s_siPlotTab, text="SI Plot")
        source_note.add(self.s_customTab, text="Custom")
        source_note.pack(fill=tk.BOTH, expand=True)
        # Application tabs
        self.a_trawlTab = TrawlTab(application_note, self.trawlData, 'Application')
        self.a_qplotTab = QPlotTab(application_note, self.qplotData, 'Application')
        self.a_siPlotTab = SIPlotTab(application_note, self.siplotData, 'Application')
        self.a_customTab = CustomTab(application_note, self.customData, 'Application')
        application_note.add(self.a_trawlTab, text="TRAWL")
        application_note.add(self.a_qplotTab, text="QPlot")
        application_note.add(self.a_siPlotTab, text="SI Plot")
        application_note.add(self.a_customTab, text="Custom")
        application_note.pack(fill=tk.BOTH, expand=True)
        return self.main_note


def on_closing(root):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.quit()
        root.destroy()

def check_focus(event):
    # Embedded chrome browser takes focus from application
    if root.focus_get() is None:
        root.focus_force()

def center(win):
    windowWidth = win.winfo_reqwidth()
    windowHeight = win.winfo_reqheight()            
    positionRight = int(win.winfo_screenwidth()/2 - windowWidth/2)
    positionDown = int(win.winfo_screenheight()/2 - windowHeight/2)
    win.geometry("+{}+{}".format(positionRight, positionDown))

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
    if getattr(sys, 'frozen', False):
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
