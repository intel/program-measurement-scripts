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
from aggregate_summary import aggregate_runs_df
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
from capelib import succinctify
import clusters

# pywebcopy produces a lot of logging that clouds other useful information
logging.disable(logging.CRITICAL)

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
        self.source_order=[]
        self.common_columns_start = ['name', 'short_name', r'%coverage', 'apptime_s', 'C_FLOP [GFlop/s]', 'variant']
        self.common_columns_end = ['c=inst_rate_gi/s', 'timestamp#', 'color']
        self.mappings = pd.DataFrame()
        self.UIUCMap = pd.DataFrame()
        self.UIUCAnalytics = pd.DataFrame()
        self.UIUCNames = pd.DataFrame()
        self.UIUC = False
        # Track points/labels that have been hidden/highlighted by the user
        self.c_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.s_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.a_plot_state = {'hidden_names' : [], 'highlighted_names' : []}

    def resetTabValues(self):
        gui.c_qplotTab.x_axis = 'C_FLOP [GFlop/s]'
        gui.c_qplotTab.y_axis = 'C_max [GB/s]'
        gui.c_qplotTab.x_scale = 'linear'
        gui.c_qplotTab.y_scale = 'linear'

    def resetCurrentVariants(self):
        gui.c_qplotTab.current_variants = ['ORIG']
        gui.c_trawlTab.current_variants = ['ORIG']
        gui.c_customTab.current_variants = ['ORIG']
        gui.c_siPlotTab.current_variants = ['ORIG']
        gui.summaryTab.current_variants = ['ORIG']

    def add_data(self, sources, update=False):
        self.resetTabValues()
        self.resetCurrentVariants()
        self.sources = sources
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
        short_names_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\short_names.csv'
        mappings_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\mappings.csv'
        if not os.path.isfile(short_names_path):
            short_names_path = None
        if not os.path.isfile(mappings_path):
            mappings_path = None
        # Codelet summary
        mappingDf = self.UIUCMap if not self.UIUCMap.empty else None
        self.summaryDf, new_mappings = summary_report_df(in_files, in_files_format, user_op_file, request_no_cqa, \
            request_use_cpi, request_skip_energy, request_skip_stalls, request_succinct, short_names_path, \
            False, True, mappingDf)
        if self.UIUC: 
            # Add variants from UIUC .names.csv
            nameDf = self.UIUCNames[['name', 'variant']]
            nameDf.rename(columns={'name':'Name', 'variant':'Variant'}, inplace=True)
            self.summaryDf.drop(columns=['Variant'], inplace=True)
            self.summaryDf = pd.merge(left=self.summaryDf, right=nameDf, on='Name', how='outer')
            # Add diagnostic variables from .analytics.csv if supplied
            if not self.UIUCAnalytics.empty:
                diagnosticDf = self.UIUCAnalytics.drop(columns=['timestamp#'])
                diagnosticDf.rename(columns={'name':'Name'}, inplace=True)
                self.summaryDf = pd.merge(left=self.summaryDf, right=diagnosticDf, on='Name', how='outer')
        # Source summary
        if not self.UIUC:
            self.srcDf = aggregate_runs_df(self.summaryDf, level='src', name_file=short_names_path)
        # Application summary
        if not self.UIUC:
            self.appDf = aggregate_runs_df(self.summaryDf, level='app', name_file=short_names_path)
        # Multiple files setup
        if len(sources) > 1 and not update: # Ask user for the before and after order of the files
            self.source_order = []
            self.get_order()
        # Generate color column
        self.summaryDf = self.compute_colors(self.summaryDf)
        if not self.UIUC:
            self.srcDf = self.compute_colors(self.srcDf)
            self.appDf = self.compute_colors(self.appDf)
        if len(sources) > 1:
            if not self.UIUC: 
                self.mappings = self.getMappings()
                if self.mappings.empty:# Create default mappings
                    self.mappings = self.createMappings(self.summaryDf) # Add default codelet mappings
                    self.mappings = self.mappings.append(self.createMappings(self.srcDf), ignore_index=True) # Add default source mappings
        self.notify_observers()
    
    def cancelAction(self):
        # If user quits the window we set a default before/after order
        self.source_order = list(self.summaryDf['Timestamp#'].unique())
        self.win.destroy()

    def orderAction(self, button, df):
        self.source_order.append(df['Timestamp#'][0])
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
        for index, timestamp in enumerate(self.summaryDf['Timestamp#'].unique()):
            curDf = self.summaryDf.loc[self.summaryDf['Timestamp#']==timestamp].reset_index()
            b = tk.Button(self.win, text=curDf['Name'][0].split(':')[0])
            b['command'] = lambda b=b, df=curDf : self.orderAction(b, df) 
            b.grid(row=index+1, column=1, padx=5, pady=10)
        root.wait_window(self.win)

    def compute_colors(self, df):
        colors = ['blue', 'red', 'green', 'pink', 'black', 'yellow', 'purple']
        colorDf = pd.DataFrame() 
        if self.source_order:
            for index, timestamp in enumerate(self.source_order):
                curDf = df.loc[df['Timestamp#']==timestamp]
                curDf['Color'] = colors[index]
                colorDf = colorDf.append(curDf, ignore_index=True)
        else:
            colorDf = colorDf.append(df, ignore_index=True)
            colorDf['Color'] = colors[0]
        return colorDf

    def getMappings(self):
        # Create mappings csv if it doesn't already exist
        self.mappings_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\mappings.csv'
        self.mappings_dir_path = expanduser('~') + '\\AppData\\Roaming\\Cape'
        if not os.path.isfile(self.mappings_path):
            Path(self.mappings_dir_path).mkdir(parents=True, exist_ok=True)
            open(self.mappings_path, 'wb')
        # Generate mappings from the generated dataframes
        mappings = pd.DataFrame()
        self.all_mappings = pd.DataFrame()
        if os.path.getsize(self.mappings_path) > 0: # Check if we already having mappings between the current files
            self.all_mappings = pd.read_csv(self.mappings_path)
            before_mappings = self.all_mappings.loc[self.all_mappings['before_timestamp#']==self.source_order[0]]
            mappings = before_mappings.loc[before_mappings['after_timestamp#']==self.source_order[1]]
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
        self.all_mappings = self.all_mappings.append(mappings, ignore_index=True)
        self.all_mappings.to_csv(self.mappings_path, index=False)
        return mappings
        
class CustomData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear'):
        df = loadedData.summaryDf.copy(deep=True)
        if not gui.loadedData.UIUC:
            self.mappings = loadedData.mappings
        else:
            self.mappings = loadedData.UIUCMap
        if not update:
            self.variants = df['Variant'].dropna().unique()
        # codelet custom plot
        df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=variants, mappings=self.mappings)
        self.df = df
        self.fig = fig
        self.textData = textData

        # source custom plot
        if not gui.loadedData.UIUC:
            df = loadedData.srcDf
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=variants)
            self.srcDf = df
            self.srcFig = fig
            self.srcTextData = textData

        # application custom plot
        if not gui.loadedData.UIUC:
            df = loadedData.appDf
            df, fig, textData = custom_plot(df, 'test', scale, 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis, variants=variants)
            self.appDf = df
            self.appFig = fig
            self.appTextData = textData

        self.notify_observers()

class TRAWLData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        # Watch for updates in loaded data
        loadedData.add_observers(self)
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear'):
        print("TRAWLData Notified from ", loadedData)
        # mappings
        if not gui.loadedData.UIUC:
            self.mappings = loadedData.mappings
        else:
            self.mappings = loadedData.UIUCMap
        
        # Codelet trawl plot
        df = loadedData.summaryDf.copy(deep=True)
        if not update:
            self.variants = df['Variant'].dropna().unique()
        df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
            source_order=loadedData.source_order, mappings=self.mappings, variants=variants)
        self.df = df
        self.fig = fig
        self.textData = textData

        # source trawl plot
        if not gui.loadedData.UIUC:
            df = loadedData.srcDf
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.mappings, variants=variants)
            self.srcDf = df
            self.srcFig = fig
            self.srcTextData = textData

        # application trawl plot
        if not gui.loadedData.UIUC:
            df = loadedData.appDf
            df, fig, textData = trawl_plot(df, 'test', scale, 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                source_order=loadedData.source_order, mappings=self.mappings, variants=variants)
            self.appDf = df
            self.appFig = fig
            self.appTextData = textData

        self.notify_observers()
    
class CoverageData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        self.mappings = pd.DataFrame()
        # Watch for updates in loaded data
        loadedData.add_observers(self)
    
    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear'):
        # use qplot dataframe to generate the coverage plot
        df = loadedData.summaryDf.copy(deep=True)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        if not update: # Get all unique variants upon first load
            self.variants = df['Variant'].dropna().unique()
        if not gui.loadedData.UIUC and len(loadedData.sources) > 1: # Get default/custom mappings
            if update: self.mappings = loadedData.getMappings()
            else: self.mappings = loadedData.mappings
        else: # Get UIUC Mappings
            self.mappings = loadedData.UIUCMap
        df, fig, texts = coverage_plot(df, "test", scale, "Coverage", False, chosen_node_set, gui=True, mappings=self.mappings, variants=variants)
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

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, scale='linear', level='All'):
        print("QPlotData Notified from ", loadedData)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        # Mappings
        if len(loadedData.sources) > 1:
            if update: self.mappings = loadedData.getMappings()
            else: self.mappings = loadedData.mappings
        # Get all unique variants upon first load
        if not update: self.variants = loadedData.summaryDf['Variant'].dropna().unique()
        # Codelet plot
        if level == 'All' or level == 'Codelet':
            df = loadedData.summaryDf.copy(deep=True)
            # Get UIUC Mappings if they exist
            if gui.loadedData.UIUC: self.mappings = loadedData.UIUCMap
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.mappings, variants=variants)
            # TODO: Need to settle how to deal with multiple plots/dataframes
            # May want to let user to select multiple plots to look at within this tab
            # Currently just save the ORIG data
            self.df = df_ORIG if df_ORIG is not None else df_XFORM
            self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.textData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Codelet':
                gui.c_qplotTab.notify(self)
        
        # source qplot
        if (level == 'All' or level == 'Source') and not gui.loadedData.UIUC:
            df = loadedData.srcDf
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, mappings=self.mappings, variants=variants)
            self.srcDf = df_ORIG if df_ORIG is not None else df_XFORM
            self.srcFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
            self.srcTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM
            if level == 'Source':
                gui.s_qplotTab.notify(self)

        # application qplot
        if (level == 'All' or level == 'Application') and not gui.loadedData.UIUC:
            df = loadedData.appDf
            df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot_df\
                (df, "test", scale, "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis, \
                    source_order=loadedData.source_order, variants=variants)
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
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None, variants=['ORIG'], update=False, cluster=expanduser('~') + '\\AppData\\Roaming\\Cape\\Clusters\\FE_tier1.csv', title="FE_tier1", \
        filtering=False, filter_data=None, scale='linear'):
        print("SIPlotData Notified from ", loadedData)
        chosen_node_set = set(['RAM [GB/s]','L2 [GB/s]','FE','FLOP [GFlop/s]','L1 [GB/s]','VR [GB/s]','L3 [GB/s]'])
        # mappings
        if not gui.loadedData.UIUC and len(loadedData.sources) > 1:
            self.mappings = loadedData.mappings
        else:
            self.mappings = loadedData.UIUCMap
        # Plot only at Codelet level for now
        df = loadedData.summaryDf.copy(deep=True)
        if not update:
            self.variants = df['Variant'].dropna().unique()
        df_ORIG, fig_ORIG, textData_ORIG = parse_ip_siplot_df\
            (cluster, "FE_tier1", "row", title, chosen_node_set, df, variants=variants, filtering=filtering, filter_data=filter_data, mappings=self.mappings, scale=scale)
        self.df = df_ORIG
        if not self.loadedData.UIUCAnalytics.empty: # Merge diagnostic variables with SIPlot dataframe
                self.df.drop(columns=['ddg_artifical_cyclic', 'limits', 'ddg_true_cyclic', 'init_only', 'rhs_op_count'], inplace=True)
                diagnosticDf = self.loadedData.UIUCAnalytics.drop(columns=['timestamp#'])
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
        def __init__(self, path, name, container, time_stamp=None):
            super().__init__(path, name, container, time_stamp)
            self.cape_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\'
            self.children = []

        def open(self):
            print("remote node open:", self.name, self.id) 
            page = requests.get(self.path)
            content_type = page.headers['content-type']
            # Webpage node
            if content_type == 'text/html':
                gui.loadedData.UIUC = False
                self.open_webpage()
            # Directory node Oneview
            elif content_type == 'text/html;charset=ISO-8859-1':
                self.open_directory(page)
            # Directory or data node UIUC
            elif content_type == 'text/html;charset=UTF-8':
                if re.search('\d{2}_\d{2}_\d{4}/', self.name):
                    gui.loadedData.UIUC = True
                    self.open_data(page)
                else:
                    self.open_directory(page)

        def open_data(self, page):
            # Remove any OV HTML pages if they exist
            gui.oneviewTab.removePages()
            gui.loaded_url = None
            gui.loadedData.UIUCAnalytics = pd.DataFrame()
            local_dir_path = self.cape_path + 'UIUC'
            for directory in self.path[8:].split('/'):
                local_dir_path = local_dir_path + '\\' + directory
            local_dir_path = local_dir_path + self.time_stamp
            # Download .csv files if not already downloaded
            local_file_path = local_dir_path + '\\'
            if not os.path.isdir(local_dir_path):
                Path(local_dir_path).mkdir(parents=True, exist_ok=True)
                tree = html.fromstring(page.content)
                csv_file_names = []
                for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                    hyperlink = link_element.xpath('td[position()=2]/a')[0]
                    csv_file_names.append(hyperlink.get('href'))
                print("csv_file_names: ", csv_file_names)
                for file_name in csv_file_names:
                    csv_url = self.path + file_name
                    csv = requests.get(csv_url)
                    open(local_file_path + file_name, 'wb').write(csv.content)
                print("Done downloading csv files")
            for name in os.listdir(local_file_path):
                if name.endswith(".names.csv"):
                    local_short_names_path = local_file_path + name
                    df = pd.read_csv(local_short_names_path)
                    gui.loadedData.UIUCNames = df
                elif name.endswith('.raw.csv'):
                    local_data_path = local_file_path + name
                elif name.endswith('.mapping.csv'):
                    local_meta_path = local_file_path + name
                    gui.loadedData.UIUCMap = pd.read_csv(local_meta_path)
                elif name.endswith('.analytics.csv'):
                    local_analytics_path = local_file_path + name
                    gui.loadedData.UIUCAnalytics = pd.read_csv(local_analytics_path)
                    gui.loadedData.UIUCAnalytics.columns = succinctify(gui.loadedData.UIUCAnalytics.columns)
            shortnameTab = ShortNameTab(root)
            shortnameTab.addShortNames(df)
            # Remove any previous plots in Application/Source
            tabs = [gui.s_customTab.window, gui.s_qplotTab.window, gui.s_siPlotTab.window, gui.s_trawlTab.window, \
                    gui.a_customTab.window, gui.a_qplotTab.window, gui.a_siPlotTab.window, gui.a_trawlTab.window]
            for tab in tabs:
                for widget in tab.winfo_children():
                    widget.destroy()
            print("local_file_path: ", local_data_path)
            self.container.openLocalFile(local_data_path)

        def open_directory(self, page):
            tree = html.fromstring(page.content)
            for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                hyperlink = link_element.xpath('td[position()=2]/a')[0]
                name = hyperlink.get('href')
                # Only show html pages, xlsx will be auto loaded
                if name[-1] == '/' and name not in self.children:
                    self.children.append(name)
                    fullpath = self.path + name
                    time_stamp = link_element.xpath('td[position()=3]/text()')[0][:10] + '_' + link_element.xpath('td[position()=3]/text()')[0][11:13] + \
                        '-' + link_element.xpath('td[position()=3]/text()')[0][14:16]
                    self.container.insertNode(self, DataSourcePanel.RemoteNode(fullpath, name, self.container, time_stamp=time_stamp))

        def open_webpage(self):
            gui.loadedData.UIUCAnalytics = pd.DataFrame()
            gui.loadedData.UIUC = False
            # Replicate remote directory structure
            local_dir_path = self.cape_path + 'Oneview'
            for directory in self.path[66:].split('/'):
                local_dir_path = local_dir_path + '\\' + directory
            # Each file has its own directory with versions of that file labeled by time stamp
            local_dir_path = local_dir_path + self.time_stamp
            # Download Corresponding Excel file if not already downloaded
            local_file_path = local_dir_path + '\\' + self.name[:-1] + '.xlsx'
            if not os.path.isdir(local_dir_path):
                print("Downloading Excel File")
                Path(local_dir_path).mkdir(parents=True, exist_ok=True)
                excel_url = self.path[:-1] + '.xlsx'
                excel = requests.get(excel_url)
                open(local_file_path, 'wb').write(excel.content)
            # TODO: Download in background, currently just loading live HTML
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
            gui.loaded_url = self.path # Use live version for now TODO: Download in background
            # Open excel file from local directory and plot
            self.container.openLocalFile(local_file_path)

    class LocalFileNode(LocalTreeNode):
        def __init__(self, path, name, container, html_path=None, mappingsDf=pd.DataFrame(), analyticsDf=pd.DataFrame(), namesDf=pd.DataFrame(), UIUC=False):
            super().__init__(path, name, container)
            self.html_path = html_path
            self.UIUC = UIUC
            self.mappingsDf = mappingsDf
            self.analyticsDf = analyticsDf
            self.namesDf = namesDf

        def open(self):
            print("file node open:", self.name, self.id) 
            # TODO: Load live version and use this when you have the background downloading working
            if self.html_path:
                gui.loaded_url = self.html_path
            gui.loadedData.UIUC = False
            gui.loadedData.analyticsDf = pd.DataFrame()
            gui.loadedData.UIUCAnalytics = pd.DataFrame()
            gui.loadedData.UIUCNames = pd.DataFrame()
            if self.UIUC:
                # Remove any OV HTML pages if they exist
                gui.oneviewTab.removePages()
                gui.loaded_url = None
                gui.loadedData.UIUC = True
                # Remove any previous plots in Application/Source
                tabs = [gui.s_customTab.window, gui.s_qplotTab.window, gui.s_siPlotTab.window, gui.s_trawlTab.window, \
                    gui.a_customTab.window, gui.a_qplotTab.window, gui.a_siPlotTab.window, gui.a_trawlTab.window]
                for tab in tabs:
                    for widget in tab.winfo_children():
                        widget.destroy()
                # Setup mappings file if it exists
                if not self.mappingsDf.empty: gui.loadedData.UIUCMap = self.mappingsDf
                if not self.namesDf.empty: gui.loadedData.UIUCNames = self.namesDf
                if not self.analyticsDf.empty: gui.loadedData.UIUCAnalytics = self.analyticsDf
            self.container.openLocalFile(self.path)
    

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
                    if re.match('\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', d): # timestamp directory holding several files to be loaded
                        # Handle loading local Oneview and UIUC timestamp directories differently
                        if 'Oneview' in fullpath.split('\\'):
                            html_path = fullpath + '\\HTML'
                            for name in os.listdir(html_path): # add html files
                                if name.endswith("__index.html"):
                                    html_path = html_path + '\\' + name
                                    break
                            fullpath = fullpath + '\\' + fullpath.split('\\')[-2] + '.xlsx' # open excel file
                            self.container.insertNode(self, DataSourcePanel.LocalFileNode(fullpath, d, self.container, html_path=html_path))
                        elif 'UIUC' in fullpath.split('\\'):
                            mappingsDf=pd.DataFrame()
                            analyticsDf=pd.DataFrame()
                            for name in os.listdir(fullpath): # add html files
                                if name.endswith(".raw.csv"):
                                    datapath = fullpath + '\\' + name
                                elif name.endswith('.mapping.csv'):
                                    metapath = fullpath + '\\' + name
                                    mappingsDf = pd.read_csv(metapath)
                                elif name.endswith('.analytics.csv'):
                                    analyticspath = fullpath + '\\' + name
                                    analyticsDf = pd.read_csv(analyticspath)
                                    analyticsDf.columns = succinctify(analyticsDf.columns)
                                elif name.endswith(".names.csv"):
                                    shortnamespath = fullpath + '\\' + name
                                    namesDf = pd.read_csv(shortnamespath)
                            self.container.insertNode(self, DataSourcePanel.LocalFileNode(datapath, d, self.container, mappingsDf=mappingsDf, analyticsDf=analyticsDf, namesDf=namesDf, UIUC=True))
                    elif os.path.isdir(fullpath): # Normal directory
                        self.container.insertNode(self, DataSourcePanel.LocalDirNode(fullpath, d, self.container))
                    elif os.path.isfile(fullpath): # Normal file
                        self.container.insertNode(self, DataSourcePanel.LocalFileNode(fullpath, d, self.container))
                    else:
                        print('Skip special file:', d)


    def __init__(self, parent, loadDataSrcFn):
        ScrolledTreePane.__init__(self, parent)
        self.loadDataSrcFn = loadDataSrcFn
        self.dataSrcNode = DataSourcePanel.MetaTreeNode('Data Source')
        self.localNode = DataSourcePanel.MetaTreeNode('Local')
        self.remoteNode = DataSourcePanel.MetaTreeNode('Remote')
        self.insertNode(None, self.dataSrcNode)
        self.insertNode(self.dataSrcNode, self.localNode)
        self.insertNode(self.dataSrcNode, self.remoteNode)
        self.opening = False
        self.firstOpen = True

        self.setupLocalRoots()
        self.setupRemoteRoots()
        self.treeview.bind("<<TreeviewOpen>>", self.handleOpenEvent)

    def insertNode(self, parent, node):
        parent_str = parent.id if parent else ''
        self.treeview.insert(parent_str,'end',node.id,text=node.name)
        
    def openLocalFile(self, source):
        self.loadDataSrcFn(source)

    def handleOpenEvent(self, event):
        if not self.opening: # finish opening one file before another is started
            self.opening = True
            nodeId = int(self.treeview.focus())
            node = DataSourcePanel.DataTreeNode.lookupNode(nodeId)
            node.open()
            self.opening = False
        if self.firstOpen:
            self.firstOpen = False
            self.treeview.column('#0', minwidth=600, width=600)

    def setupLocalRoots(self):
        home_dir=expanduser("~")
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(home_dir, 'Home', self) )
        cape_cache_path= os.path.join(home_dir, 'AppData', 'Roaming', 'Cape')
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(cape_cache_path, 'Previously Visited', self) )

    def setupRemoteRoots(self):
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://datafront.maqao.exascale-computing.eu/public_html/oneview/', 'UVSQ', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://vectorization.computer/data/','UIUC', self))

class AnalysisResultsPanel(ScrolledTreePane):
    def __init__(self, parent):
        ScrolledTreePane.__init__(self, parent)
        self.treeview.insert('','0','item1',text='Analysis Results')  
        self.treeview.insert('','end','item3',text='Local')  
        self.treeview.insert('item3','end','D',text='Compare QMC against LORE')  
        self.treeview.insert('item3','end','E',text='Graph algorithm')  
        self.treeview.insert('item3','end','F',text='OpenCV study')  
        self.treeview.move('item3','item1','end')    

class ExplorerPanel(tk.PanedWindow):
    def __init__(self, parent, loadDataSrcFn):
        tk.PanedWindow.__init__(self, parent, orient="vertical")
        top = DataSourcePanel(self, loadDataSrcFn)
        top.pack(side = tk.TOP)
        self.add(top)
        bot = AnalysisResultsPanel(self)
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
        self.level = level
        self.current_variants = ['ORIG']
        self.x_scale = 'linear'
        self.y_scale = 'linear'
        self.x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = r'%coverage'
        self.current_labels = []
        self.parent = parent
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                    sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData, mappings=pd.DataFrame(), variants=None):
        self.variants = variants
        # Plot Setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        # Data table/tabs setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        if not gui.loadedData.UIUCAnalytics.empty:
            diagnosticDf = gui.loadedData.UIUCAnalytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        full_summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()
        table_button_frame = tk.Frame(self.summaryTab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Export", command=lambda: self.shortnameTab.exportCSV(full_summary_pt)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export Summary", command=lambda: self.exportCSV()).grid(row=0, column=1)

        self.shortnameTab.buildLabelTable(df, self.shortnameTab, textData)

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
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    def notify(self, coverageData):
        variants = coverageData.variants
        for w in self.window.winfo_children():
            w.destroy()
        self.update(coverageData.df, coverageData.fig, coverageData.textData, coverageData.mappings, variants=variants)

class PlotInteraction():
    def __init__(self, tab, df, fig, textData, level):
        self.tab = tab
        self.df = df
        self.fig = fig
        self.textData = textData
        self.adjusted = False
        self.adjusting = False
        self.xlim = self.textData['ax'].get_xlim()
        self.ylim = self.textData['ax'].get_ylim()
        # Create lists of tabs that need to be synchronized according to the level and update the plot with the saved state
        self.level = level
        if self.level == 'Codelet': 
            self.tabs = [gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab, gui.summaryTab]
            self.stateDictionary = gui.loadedData.c_plot_state
            self.restoreState(self.stateDictionary)
        elif self.level == 'Source': 
            self.tabs = [gui.s_trawlTab, gui.s_qplotTab, gui.s_customTab]
            self.stateDictionary = gui.loadedData.s_plot_state
            self.restoreState(self.stateDictionary)
        elif self.level == 'Application': 
            self.tabs = [gui.a_trawlTab, gui.a_qplotTab, gui.a_customTab]
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
        self.adjust_button = tk.Button(self.plotFrame3, text='Adjust Text', command=self.adjustText)
        self.toggle_labels_button = tk.Button(self.plotFrame3, text='Hide Labels', command=self.toggleLabels)
        self.show_markers_button = tk.Button(self.plotFrame3, text='Show Points', command=self.showMarkers)
        self.custom_label_ = tk.Button(self.plotFrame3, text='Show Points', command=self.showMarkers)
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
            options.append('[' + self.df['short_name'][i] + '] ' + self.df['name'][i])
        self.pointSelector = ChecklistBox(self.plotFrame2, options, options, listType='pointSelector', tab=self, bd=1, relief="sunken", background="white")
        self.pointSelector.restoreState(self.stateDictionary)
        # Grid Layout
        self.toolbar.grid(column=4, row=0, sticky=tk.S)
        self.action_menu.grid(column=3, row=0, sticky=tk.S)
        self.show_markers_button.grid(column=2, row=0, sticky=tk.S, pady=2)
        self.toggle_labels_button.grid(column=1, row=0, sticky=tk.S, pady=2)
        self.adjust_button.grid(column=0, row=0, sticky=tk.S, pady=2)
        self.plotFrame3.grid_rowconfigure(0, weight=1)
        self.pointSelector.pack(side=tk.RIGHT, anchor=tk.N, fill=tk.Y)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, anchor=tk.N, padx=10)
        self.toolbar.update()
        self.canvas.draw()

    def restoreState(self, dictionary):
        for name in dictionary['hidden_names']:
                self.textData['name:marker'][name].set_alpha(0)
                self.textData['name:text'][name].set_alpha(0)
        for name in dictionary['highlighted_names']:
            self.highlight(self.textData['name:marker'][name])

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
        # for child in self.textData['ax'].get_children():
        #     print(child)
        if self.action_selected.get() == 'Choose Action':
            pass
        elif self.action_selected.get() == 'Highlight Point':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.highlightPoint(marker)
                    return
        elif self.action_selected.get() == 'Remove Point':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.removePoint(marker)
                    return
        elif self.action_selected.get() == 'Toggle Label':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.toggleLabel(marker)
                    return

    def removePoint(self, marker):
        for tab in self.tabs:
            otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
            otherMarker.set_alpha(0)
            tab.plotInteraction.textData['marker:text'][otherMarker].set_alpha(0)
            try: 
                for mapping in tab.plotInteraction.textData['name:mapping'][marker.get_label()]:
                    mapping.set_alpha(0)
            except: pass
            try: tab.plotInteraction.textData['text:arrow'][tab.plotInteraction.textData['marker:text'][otherMarker]].set_visible(False)
            except: pass
            name = tab.plotInteraction.textData['marker:name'][otherMarker]
            index = tab.plotInteraction.pointSelector.names.index(name)
            tab.plotInteraction.pointSelector.vars[index].set(0)
            tab.plotInteraction.canvas.draw()

    def highlight(self, marker):
        if marker.get_marker() == 'o':
            marker.set_marker('*')
            marker.set_markeredgecolor('k')
            marker.set_markeredgewidth(0.5)
            marker.set_markersize(10.0)
        elif marker.get_marker() == '*':
            marker.set_marker('o')
            marker.set_markeredgecolor(marker.get_markerfacecolor())
            marker.set_markersize(6.0)
    
    def highlightPoint(self, marker):
        for tab in self.tabs:
            otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
            self.highlight(otherMarker)
            tab.plotInteraction.canvas.draw()

    def onDraw(self, event):
        if self.adjusted and (self.xlim != self.textData['ax'].get_xlim() or self.ylim != self.textData['ax'].get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            print("Ondraw adjusting")
            self.xlim = self.textData['ax'].get_xlim()
            self.ylim = self.textData['ax'].get_ylim() 
            self.adjustText()

    def thread_adjustText(self):
        plt.sca(self.textData['ax'])
        if self.adjusted: # Remove old adjusted texts/arrows and create new texts before calling adjust_text again
            # Store index of hidden texts to update the new texts
            hiddenTexts = []
            for i in range(len(self.textData['texts'])):
                if not self.textData['texts'][i].get_alpha(): hiddenTexts.append(i)
            # Remove all old texts and arrows
            for child in self.textData['ax'].get_children():
                if isinstance(child, matplotlib.text.Annotation) or (isinstance(child, matplotlib.text.Text) and child.get_text() not in [self.textData['title'], '']):
                    child.remove()
            # Create new texts that maintain the current visibility
            self.textData['texts'] = [plt.text(self.textData['xs'][i], self.textData['ys'][i], self.textData['mytext'][i], alpha=1 if i not in hiddenTexts else 0) for i in range(len(self.textData['mytext']))]
            # Update marker to text mappings with the new texts
            self.textData['marker:text'] = dict(zip(self.textData['markers'],self.textData['texts']))
        # Only adjust texts that are in the current axes (in case of a zoom)
        to_adjust = []
        for i in range(len(self.textData['texts'])):
            if self.textData['xs'][i] >= self.textData['ax'].get_xlim()[0] and self.textData['xs'][i] <= self.textData['ax'].get_xlim()[1] and \
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
            x_menu = self.custom_axes(self.x_selected)
            y_menu = self.custom_axes(self.y_selected)
        else:  
            if self.plotType == 'QPlot':
                y_options = ['Choose Y Axis Metric', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]']
            elif self.plotType == 'TRAWL':
                y_options = ['Choose Y Axis Metric', 'speedup[vec]', 'speedup[dl1]']
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

    def custom_axes(self, var):
        menubutton = tk.Menubutton(self, textvariable=var, indicatoron=True,
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
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='Summary', menu=summary_menu)
        metrics = [[r'%coverage', 'apptime_s'],
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
        self.save_state()
        # Set user selected metrics/scales if they have changed at least one
        if self.x_selected.get() != 'Choose X Axis Metric' or self.y_selected.get() != 'Choose Y Axis Metric' or self.xscale_selected.get() != 'Choose X Axis Scale' or self.yscale_selected.get() != 'Choose Y Axis Scale':
            if self.plotType == 'QPlot':
                self.tab.qplotData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale)
            elif self.plotType == 'TRAWL':
                self.tab.trawlData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale)
            elif self.plotType == 'Custom':
                self.tab.customData.notify(gui.loadedData, x_axis=self.tab.x_axis, y_axis=self.tab.y_axis, variants=self.tab.current_variants, scale=self.tab.x_scale+self.tab.y_scale)

    def save_state(self):
        # Get names of this tabs current hidden/highlighted data points
        if self.tab.level == 'Codelet': dictionary = gui.loadedData.c_plot_state
        elif self.tab.level == 'Source': dictionary = gui.loadedData.s_plot_state
        elif self.tab.level == 'Application': dictionary = gui.loadedData.a_plot_state
        dictionary['hidden_names'] = []
        dictionary['highlighted_names'] = []
        for marker in self.tab.plotInteraction.textData['markers']:
            if not marker.get_alpha():
                dictionary['hidden_names'].append(marker.get_label())
            if marker.get_marker() == '*':
                dictionary['highlighted_names'].append(marker.get_label())

class ShortNameTab(tk.Frame):
    def __init__(self, parent, level=None):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.level = level
        self.short_names_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\short_names.csv'
        self.short_names_dir_path = expanduser('~') + '\\AppData\\Roaming\\Cape'
        if not os.path.isfile(self.short_names_path):
            Path(self.short_names_dir_path).mkdir(parents=True, exist_ok=True)
            open(self.short_names_path, 'wb')

    # Create table for Labels tab and update button
    def buildLabelTable(self, df, tab, texts=None):
        table_labels = df[['name', r'%coverage', 'timestamp#', 'color']]
        table_labels['short_name'] = table_labels['name']
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            short_names = short_names[['name', 'short_name']]
            inner = pd.merge(left=table_labels, right=short_names, left_on='name', right_on='name')
            inner.rename(columns={'short_name_y':'short_name'}, inplace=True)
            inner = inner[['name', 'short_name', 'timestamp#', 'color', r'%coverage']]
            merged = pd.concat([table_labels, inner]).drop_duplicates('name', keep='last')
        else:
            merged = table_labels
        # sort label table by coverage to keep consistent with data table
        merged = merged.sort_values(by=r'%coverage', ascending=False)
        merged = merged[['name', 'short_name', 'timestamp#', 'color']]
        table = Table(tab, dataframe=merged, showtoolbar=False, showstatusbar=True)
        table.show()
        table.redraw()
        table_button_frame = tk.Frame(tab)
        table_button_frame.grid(row=3, column=1)
        tk.Button(table_button_frame, text="Update", command=lambda: self.updateLabels(table, texts)).grid(row=0, column=0)
        tk.Button(table_button_frame, text="Export", command=lambda: self.exportCSV(table)).grid(row=0, column=1)
        return table

    # Merge user input labels with current mappings and replot
    def updateLabels(self, table, texts=None):
        df = table.model.df
        if self.checkForDuplicates(df):
            return
        else:
            self.addShortNames(df)
        gui.loadedData.add_data(gui.sources, update=True)

    def addShortNames(self, df):
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            short_names = short_names[['name', 'short_name']]
            table_names = df[['name', 'short_name']]
            outer = pd.merge(left=short_names, right=table_names, left_on='name', right_on='name', how='outer')
            outer.rename(columns={'short_name_y':'short_name'}, inplace=True)
            outer = outer[['name', 'short_name']].dropna()
            merged = pd.concat([short_names, outer]).drop_duplicates('name', keep='last')
        else:
            merged = df[['name', 'short_name']]
        merged.to_csv(self.short_names_path)

    def checkForDuplicates(self, df):
        # Check if there are duplicates in short names for a single file
        df = df.reset_index(drop=True)
        duplicate_df = pd.DataFrame()
        for color in df['color'].unique():
            curfile = df.loc[df['color'] == color]
            duplicates = curfile['short_name'].duplicated(keep=False)
            duplicate_df = duplicate_df.append(curfile[duplicates])
        if not duplicate_df.empty:
            message = str()
            for index, row in duplicate_df.iterrows():
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
        self.mappings_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\mappings.csv'
        self.mappings_dir_path = expanduser('~') + '\\AppData\\Roaming\\Cape'
        self.short_names_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\short_names.csv'

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
        toAdd['before_timestamp#'] = self.df.loc[self.df['name']==self.before_selected.get().split('[')[0][:-1]]['timestamp#']
        toAdd['before_name'] = self.before_selected.get().split('[')[0][:-1]
        toAdd['before_short_name'] = self.df.loc[self.df['name']==self.before_selected.get().split('[')[0][:-1]]['short_name']
        toAdd['after_timestamp#'] = self.df.loc[self.df['name']==self.after_selected.get().split('[')[0][:-1]].iloc[0]['timestamp#']
        toAdd['after_name'] = self.after_selected.get().split('[')[0][:-1]
        toAdd['after_short_name'] = self.df.loc[self.df['name']==self.after_selected.get().split('[')[0][:-1]].iloc[0]['short_name']
        self.mappings = self.mappings.append(toAdd, ignore_index=True)
        self.updateTable()
    
    def removeMapping(self):
        self.mappings.drop(self.mappings[(self.mappings['before_name']==self.before_selected.get().split('[')[0][:-1]) & \
            (self.mappings['before_timestamp#']==(self.df.loc[self.df['name']==self.before_selected.get().split('[')[0][:-1]].reset_index(drop=True)['timestamp#'][0])) & \
            (self.mappings['after_timestamp#']==(self.df.loc[self.df['name']==self.after_selected.get().split('[')[0][:-1]].reset_index(drop=True)['timestamp#'][0])) & \
            (self.mappings['after_name']==self.after_selected.get().split('[')[0][:-1])].index, inplace=True)
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
        self.tab.qplotData.notify(gui.loadedData, level=self.level, update=True)

    def buildMappingsTab(self, df, mappings):
        self.df = df
        self.mappings = mappings
        self.all_mappings = pd.read_csv(self.mappings_path)
        self.source_order = gui.loadedData.source_order
        self.table = Table(self, dataframe=mappings, showtoolbar=False, showstatusbar=True)
        self.table.show()
        self.table.redraw()
        before = df.loc[df['timestamp#'] == self.source_order[0]]
        after = df.loc[df['timestamp#'] == self.source_order[1]]
        short_names = pd.read_csv(self.short_names_path)
        for index in before.index:
            before['name'][index] = before['name'][index] + ' [' + \
                short_names.loc[short_names['name']==before['name'][index]].reset_index(drop=True)['short_name'][0] + ']'
        for index in after.index:
            after['name'][index] = after['name'][index] + ' [' + \
                short_names.loc[short_names['name']==after['name'][index]].reset_index(drop=True)['short_name'][0] + ']'
        tk.Button(self, text="Edit", command=lambda before=list(before['name']), after=list(after['name']) : \
            self.editMappings(before, after)).grid(row=10, column=0)
        tk.Button(self, text="Update", command=self.updateMappings).grid(row=10, column=1, sticky=tk.W)

class ClusterTab(tk.Frame):
    def __init__(self, parent, tab):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.cluster_path = os.path.realpath(__file__).rsplit('\\', 1)[0]
        self.cluster_path += '\\' + 'clusters' 
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
            path = self.cluster_path + '\\' + self.cluster_selected.get() + '.csv'
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
            self.names.append(choice.split(' ', 1)[-1])
            cb = tk.Checkbutton(self, var=var, text=choice,
                                onvalue=1, offvalue=0,
                                anchor="w", width=100, background=bg,
                                relief="flat", highlightthickness=0
            )
            self.cbs.append(cb)
            if listType == 'pointSelector':
                cb['command'] = lambda name=choice, index=index : self.updatePlot(name, index)
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
        codelet_name = name.split(' ', 1)[-1]
        if selected:
            for tab in self.tab.tabs:
                tab.plotInteraction.pointSelector.vars[index].set(1)
                marker = tab.plotInteraction.textData['name:marker'][codelet_name]
                marker.set_alpha(1)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(1)
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(True)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][codelet_name]:
                        mapping.set_alpha(1)
                except: pass
                tab.plotInteraction.canvas.draw()
        else:
            for tab in self.tab.tabs:
                tab.plotInteraction.pointSelector.vars[index].set(0)
                marker = tab.plotInteraction.textData['name:marker'][codelet_name]
                marker.set_alpha(0)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(0)
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(False)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][codelet_name]:
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

    def updateVariants(self):
        self.parent.tab.current_variants = self.getCheckedItems()
        # Update the rest of the plots at the same level with the new checked variants
        for tab in self.parent.tab.plotInteraction.tabs:
            for i, cb in enumerate(self.cbs):
                tab.variantTab.checkListBox.vars[i].set(self.vars[i].get())
            tab.current_variants = self.parent.tab.current_variants
        gui.siplotData.notify(gui.loadedData, variants=self.parent.tab.current_variants, update=True, cluster=gui.c_siPlotTab.cluster, title=gui.c_siPlotTab.title)
        gui.qplotData.notify(gui.loadedData, variants=self.parent.tab.current_variants, update=True)
        gui.trawlData.notify(gui.loadedData, variants=self.parent.tab.current_variants, update=True)
        gui.customData.notify(gui.loadedData, variants=self.parent.tab.current_variants, update=True)
        gui.coverageData.notify(gui.loadedData, variants=self.parent.tab.current_variants, update=True)

    def updateLabels(self):
        self.parent.tab.current_labels = self.getCheckedItems()
        textData = self.parent.tab.plotInteraction.textData

        # TODO: Update the rest of the plots at the same level with the new checked variants
        # for tab in self.parent.tab.plotInteraction.tabs:
        #     for i, cb in enumerate(self.cbs):
        #         tab.labelTab.checkListBox.vars[i].set(self.vars[i].get())
        #     tab.current_labels = self.parent.tab.current_labels

        # If nothing selected, revert labels and legend back to original
        if not self.parent.tab.current_labels:
            for i, text in enumerate(textData['texts']):
                text.set_text(textData['orig_mytext'][i])
                textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
                textData['legend'].get_title().set_text(textData['orig_legend'])
        else: 
            # Update existing plot texts by adding user specified metrics
            df = self.parent.tab.plotInteraction.df
            for i, text in enumerate(textData['texts']):
                toAdd = textData['orig_mytext'][i][:-1]
                for choice in self.parent.tab.current_labels:
                    codeletName = textData['names'][i]
                    value = df.loc[df['name']==codeletName][choice].iloc[0]
                    if isinstance(value, int) or isinstance(value, float):
                        toAdd += ', ' + str(round(value, 2))
                    else:
                        toAdd += ', ' + str(value)
                toAdd += ')'
                text.set_text(toAdd)
                textData['mytext'][i] = toAdd
            # Update legend for user to see order of metrics in the label
            newTitle = textData['orig_legend'][:-1]
            for choice in self.parent.tab.current_labels:
                newTitle += ', ' + choice
            newTitle += ')'
            textData['legend'].get_title().set_text(newTitle)
        self.parent.tab.plotInteraction.canvas.draw()
        # Adjust labels if already adjusted
        if self.parent.tab.plotInteraction.adjusted:
            self.parent.tab.plotInteraction.adjustText()

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
        choices = ['C_FLOP [GFlop/s]', r'%coverage', 'apptime_s']
        if not gui.loadedData.UIUCAnalytics.empty:
            diagnosticDf = gui.loadedData.UIUCAnalytics.drop(columns=['name', 'timestamp#'])
            choices.extend(diagnosticDf.columns.tolist())
        self.checkListBox = ChecklistBox(self, choices, tab.current_labels, bd=1, relief="sunken", background="white")
        update = tk.Button(self, text='Update', command=self.checkListBox.updateLabels)
        self.checkListBox.pack(side=tk.LEFT, anchor=tk.NW)
        update.pack(side=tk.LEFT, anchor=tk.NW)

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
        self.level = level
        self.trawlData = trawlData
        self.x_scale = 'linear'
        self.y_scale = 'linear'
        self.x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = 'speedup[vec]'
        self.current_variants = ['ORIG']
        self.current_labels = []
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData=None, mappings=None, variants=None):
        self.variants = variants
        # Plot setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        # Data table/tabs setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.extend(['speedup[vec]', 'speedup[dl1]'])
        if not gui.loadedData.UIUCAnalytics.empty:
            diagnosticDf = gui.loadedData.UIUCAnalytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        column_list.extend(gui.loadedData.common_columns_end)
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        tk.Button(self.summaryTab, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=3, column=1)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)

        #if self.level == 'Codelet' and len(gui.sources) > 1:
            #self.mappingsTab.buildMappingsTab(df, self.mappingsTab, mappings)

    # Create tabs for TRAWL Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'TRAWL')
        #self.mappingsTab = MappingsTab(self.tableNote, self.level)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        #self.tableNote.add(self.mappingsTab, text="Mappings")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, trawlData):
        variants = trawlData.variants
        mappings = trawlData.mappings
        if self.level == 'Codelet':
            df = trawlData.df
            fig = trawlData.fig
            textData = trawlData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, mappings=mappings, variants=variants)

        elif self.level == 'Source' and not gui.loadedData.UIUC:
            df = trawlData.srcDf
            fig = trawlData.srcFig
            textData = trawlData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, variants=variants)

        elif self.level == 'Application' and not gui.loadedData.UIUC:
            df = trawlData.appDf
            fig = trawlData.appFig
            textData = trawlData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData=textData, variants=variants)

class QPlotTab(tk.Frame):
    def __init__(self, parent, qplotData, level):
        tk.Frame.__init__(self, parent)
        if qplotData is not None:
           qplotData.add_observers(self)
        self.level = level
        self.qplotData = qplotData
        self.x_scale = 'linear'
        self.y_scale = 'linear'
        self.x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = 'C_max [GB/s]'
        self.current_variants = ['ORIG']
        self.current_labels = []
        # QPlot tab has a paned window with the data tables and qplot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData=None, mappings=None, variants=None):
        self.variants = variants
        # Plot/Table setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()

        # Summary Data Table
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
                'C_RAM [GB/s]', 'C_max [GB/s]', 'memlevel'])
        if not gui.loadedData.UIUCAnalytics.empty:
            diagnosticDf = gui.loadedData.UIUCAnalytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        column_list.extend(gui.loadedData.common_columns_end)
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        tk.Button(self.summaryTab, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=3, column=1)

        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
        if (self.level == 'Codelet') and len(gui.sources) > 1:
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
        variants = qplotData.variants
        mappings = qplotData.mappings
        if self.level == 'Codelet':
            df = qplotData.df
            fig = qplotData.fig
            textData = qplotData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

        elif self.level == 'Source' and not gui.loadedData.UIUC:
            df = qplotData.srcDf
            fig = qplotData.srcFig
            textData = qplotData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, mappings, variants=variants)

        elif self.level == 'Application' and not gui.loadedData.UIUC:
            df = qplotData.appDf
            fig = qplotData.appFig
            textData = qplotData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants)

class SIPlotTab(tk.Frame):
    def __init__(self, parent, siplotData, level):
        tk.Frame.__init__(self, parent)
        if siplotData is not None:
            siplotData.add_observers(self)
        self.level = level
        self.siplotData = siplotData
        self.cluster = expanduser('~') + '\\AppData\\Roaming\\Cape\\Clusters\\FE_tier1.csv'
        self.title = 'FE_tier1'
        self.current_variants = ['ORIG']
        self.x_scale = 'linear'
        self.y_scale = 'linear'
        self.x_axis = 'Intensity'
        self.y_axis = 'Saturation'
        self.current_labels = []
        # SIPlot tab has a paned window with the data tables and sipLot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)
    
    def update(self, df, fig, textData=None, mappings=None, variants=None):
        self.variants = variants
        self.df = df
        # Plot/Table Setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        # Summary Data table
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        if gui.loadedData.UIUC:
            column_list.extend(['Saturation', 'Intensity', 'SI'])
            if not gui.loadedData.UIUCAnalytics.empty: # Add diagnostic variables if file .analytics.csv was supplied
                diagnosticDf = gui.loadedData.UIUCAnalytics.drop(columns=['name', 'timestamp#'])
                column_list.extend(diagnosticDf.columns.tolist())
        else:
            column_list.extend(['Saturation', 'Intensity', 'SI', 'C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
                'C_RAM [GB/s]', 'C_max [GB/s]', 'memlevel'])
        column_list.extend(gui.loadedData.common_columns_end)
        self.summaryDf = df[column_list]
        self.buildTableTabs()
        self.summaryDf = self.summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=self.summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()
        tk.Button(self.summaryTab, text="Export", command=lambda: self.shortnameTab.exportCSV(summaryTable)).grid(row=3, column=1)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)

    # Create tabs for QPlot Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.clusterTab = ClusterTab(self.tableNote, self)
        self.filteringTab = FilteringTab(self.tableNote, self)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.add(self.clusterTab, text='Clusters')
        self.tableNote.add(self.filteringTab, text='Filtering')
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, siplotData):
        if self.level == 'Codelet':
            df = siplotData.df
            fig = siplotData.fig
            textData = siplotData.textData
            variants = siplotData.variants
            # TODO: Separate coverage plot from qplot data
            plotTabs = [self.window]
            for tab in plotTabs:
                for w in tab.winfo_children():
                    w.destroy()
            self.update(df, fig, textData=textData, variants=variants)

class CustomTab(tk.Frame):
    def __init__(self, parent, customData, level):
        tk.Frame.__init__(self, parent)
        if customData is not None:
            customData.add_observers(self)
        self.level = level
        self.customData = customData
        self.current_variants = ['ORIG']
        self.x_scale = 'linear'
        self.y_scale = 'linear'
        self.x_axis = 'C_FLOP [GFlop/s]'
        self.y_axis = r'%coverage'
        self.current_labels = []
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, textData, variants=None):
        self.variants = variants
        # Plot setup
        self.plotInteraction = PlotInteraction(self, df, fig, textData, self.level)
        # Data table/tabs under plot setup
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        column_list = copy.deepcopy(gui.loadedData.common_columns_start)
        column_list.extend(['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
            'C_RAM [GB/s]', 'C_max [GB/s]', 'memlevel', 'C_FLOP [GFlop/s]', 'speedup[vec]', 'speedup[dl1]', \
            'num_cores', 'dataset/size', 'prefetchers', 'repetitions', \
            'total_pkg_energy_j', 'total_dram_energy_j', 'total_pkg+dram_energy_j', 'total_pkg_power_w', 'total_dram_power_w', 'total_pkg+dram_power_w', \
            'o=inst_count_gi', 'c=inst_rate_gi/s', \
            'l1_rate_gb/s', 'l2_rate_gb/s', 'l3_rate_gb/s', 'ram_rate_gb/s', 'flop_rate_gflop/s', 'register_addr_rate_gb/s', 'register_data_rate_gb/s', 'register_simd_rate_gb/s', 'register_rate_gb/s', \
            r'%ops[vec]', r'%ops[fma]', r'%ops[div]', r'%ops[sqrt]', r'%ops[rsqrt]', r'%ops[rcp]', \
            r'%inst[vec]', r'%inst[fma]', r'%inst[div]', r'%inst[sqrt]', r'%inst[rsqrt]', r'%inst[rcp]', \
            'timestamp#', 'color'])
        if not gui.loadedData.UIUCAnalytics.empty:
            diagnosticDf = gui.loadedData.UIUCAnalytics.drop(columns=['name', 'timestamp#'])
            column_list.extend(diagnosticDf.columns.tolist())
        summaryDf = df[column_list]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()
        tk.Button(self.summaryTab, text="Export", command=lambda: self.shortnameTab.exportCSV(summary_pt)).grid(row=3, column=1)
        self.shortnameTab.buildLabelTable(df, self.shortnameTab)
    
    # Create tabs for Custom Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.shortnameTab = ShortNameTab(self.tableNote)
        self.labelTab = LabelTab(self.tableNote, self)
        self.variantTab = VariantTab(self.tableNote, self, self.variants, self.current_variants)
        self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.shortnameTab, text="Short Names")
        self.tableNote.add(self.labelTab, text='Labels')
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.add(self.variantTab, text="Variants")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, customData):
        variants = customData.variants
        if self.level == 'Codelet':
            df = customData.df
            fig = customData.fig
            textData = customData.textData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants)

        elif self.level == 'Source' and not gui.loadedData.UIUC:
            df = customData.srcDf
            fig = customData.srcFig
            textData = customData.srcTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants)

        elif self.level == 'Application' and not gui.loadedData.UIUC:
            df = customData.appDf
            fig = customData.appFig
            textData = customData.appTextData
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig, textData, variants=variants)

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

        self.explorerPanel = ExplorerPanel(self.pw, self.loadDataSource)
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

    def loadDataSource(self, source):
        if len(self.sources) >= 1:
            self.win = tk.Toplevel()
            center(self.win)
            self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
            self.win.title('Existing Data')
            if len(self.sources) >= 2:
                message = 'You have the max number of data files open.\nWould you like to overwrite with the new data?'
            else:
                message = 'Would you like to append to the existing\ndata or overwrite with the new data?'
                tk.Button(self.win, text='Append', command=self.appendData).grid(row=1, column=0, sticky=tk.E)
            tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
            tk.Button(self.win, text='Overwrite', command=self.overwriteData).grid(row=1, column=1)
            tk.Button(self.win, text='Cancel', command=self.cancelAction).grid(row=1, column=2, pady=10, sticky=tk.W)
            root.wait_window(self.win)
            if self.choice == 'Cancel':
                self.loaded_url = None
                return
            elif self.choice == 'Overwrite':
                gui.loadedData.source_order = [] # reset ordered list of timestamps if there were multiple files loaded before
                if self.loaded_url:
                    self.urls = [self.loaded_url]
                    self.oneviewTab.loadFirstPage()
                self.sources.clear()
            elif self.choice == 'Append':
                self.sources.append(source)
                print("DATA source to be loaded", source)
                if self.loaded_url:
                    self.urls.append(self.loaded_url)
                    self.oneviewTab.loadSecondPage()
                self.loadedData.add_data(self.sources)
                return
        elif self.loaded_url:
            self.urls.append(self.loaded_url)
            self.oneviewTab.loadFirstPage()

        self.sources.append(source)
        print("DATA source to be loaded", source)
        self.loadedData.add_data(self.sources)

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
            'locales_dir_path': sys._MEIPASS + os.sep + 'locales',
            'browser_subprocess_path': sys._MEIPASS + os.sep + 'subprocess.exe',
        }
    else:
        appSettings = {
            'cache_path': tempfile.gettempdir()
        }
    cef.Initialize(appSettings)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()
    cef.Shutdown()
