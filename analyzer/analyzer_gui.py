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
from summarize import summary_report
from aggregate_summary import aggregate_runs
from generate_QPlot import parse_ip as parse_ip_qplot
from generate_SI import parse_ip as parse_ip_siplot
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
import logging
import copy

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
    def add_data(self, sources):
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        print(tmpfile.name)
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
        #print(f'in_files_format[index]: {in_files_format[index]} \nsource: {source} \nin_files[index]:{in_files[index]}')
        # Codelet summary
        summary_report(in_files, tmpfile.name, in_files_format, user_op_file, request_no_cqa, \
            request_use_cpi, request_skip_energy, request_skip_stalls, request_succinct, short_names_path)
        # Application summary
        tmpfile_app = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        aggregate_runs([tmpfile.name], tmpfile_app.name)
        # Source summary
        tmpfile_src = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        aggregate_runs([tmpfile.name], tmpfile_src.name, level='src')
        # Just use file for data storage now.  May explore keeping dataframe in future if needed.
        # Currently assume only 1 run is loaded but we should extend this to aloow loading multiple
        # data and pool data together
        self.data_items=[tmpfile.name, tmpfile_src.name, tmpfile_app.name]
        #self.data_items.append(tmpfile.name)
        self.notify_observers()
    def get_data_items(self):
        return self.data_items

class CustomData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        # Watch for updates in loaded data
        loadedData.add_observers(self)

    def notify(self, loadedData, x_axis=None, y_axis=None):
        fname=loadedData.get_data_items()[0]
        df, fig, texts = custom_plot(fname, 'test', 'scalar', 'Custom', False, gui=True, x_axis=x_axis, y_axis=y_axis)
        self.df = df
        self.fig = fig
        self.texts = texts
        self.notify_observers()

class TRAWLData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        # Watch for updates in loaded data
        loadedData.add_observers(self)
    
    def notify(self, loadedData, x_axis=None, y_axis=None):
        fname=loadedData.get_data_items()[0]
        df, fig, texts = trawl_plot(fname, 'test', 'scalar', 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis)
        self.df = df
        self.fig = fig
        self.texts = texts

        # source trawl plot
        fname=loadedData.get_data_items()[1]
        df, fig, texts = trawl_plot(fname, 'test', 'scalar', 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis)
        self.srcDf = df
        self.srcFig = fig
        self.srcTexts = texts

        # application trawl plot
        fname=loadedData.get_data_items()[2]
        df, fig, texts = trawl_plot(fname, 'test', 'scalar', 'TRAWL', False, gui=True, x_axis=x_axis, y_axis=y_axis)
        self.appDf = df
        self.appFig = fig
        self.appTexts = texts

        self.notify_observers()
        
class QPlotData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        # Watch for updates in loaded data
        loadedData.add_observers(self)
        self.df = None
        self.fig = None
        self.ax = None
        self.coverageFig = None
        self.coverageTexts = None
        self.appDf = None
        self.appFig = None
        self.appTextData = None

    def notify(self, loadedData, x_axis=None, y_axis=None):
        print("Notified from ", loadedData)
        chosen_node_set = set(['L1 [GB/s]','L2 [GB/s]','L3 [GB/s]','RAM [GB/s]','FLOP [GFlop/s]'])
        #fname=tmpfile.name
        # Assume only one set of data loaded for now
        fname=loadedData.get_data_items()[0]
        df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot\
            (fname, "test", "scalar", "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis)
        # TODO: Need to settle how to deal with multiple plots/dataframes
        # May want to let user to select multiple plots to look at within this tab
        # Currently just save the ORIG data
        self.df = df_ORIG if df_ORIG is not None else df_XFORM
        self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
        self.textData = textData_ORIG if textData_ORIG is not None else textData_XFORM

        # use qplot dataframe to generate the coverage plot
        fig, texts = coverage_plot(self.df, fname, "test", "scalar", "Coverage", False, gui=True)
        self.coverageFig = fig
        self.coverageTexts = texts
        
        # source qplot
        fname=loadedData.get_data_items()[1]
        df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot\
            (fname, "test", "scalar", "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis)
        self.srcDf = df_ORIG if df_ORIG is not None else df_XFORM
        self.srcFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
        self.srcTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM

        # application qplot
        fname=loadedData.get_data_items()[2]
        df_XFORM, fig_XFORM, textData_XFORM, df_ORIG, fig_ORIG, textData_ORIG = parse_ip_qplot\
            (fname, "test", "scalar", "Testing", chosen_node_set, False, gui=True, x_axis=x_axis, y_axis=y_axis)
        self.appDf = df_ORIG if df_ORIG is not None else df_XFORM
        self.appFig = fig_ORIG if fig_ORIG is not None else fig_XFORM
        self.appTextData = textData_ORIG if textData_ORIG is not None else textData_XFORM

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
                self.open_webpage()

            # Directory node
            elif content_type == 'text/html;charset=ISO-8859-1':
                self.open_directory(page)
        
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
            # Replicate remote directory structure
            local_dir_path = self.cape_path + 'Oneview'
            for directory in self.path[66:].split('/'):
                local_dir_path = local_dir_path + '\\' + directory
            # Each file has its own directory with versions of that file labeled by time stamp
            local_dir_path = local_dir_path + self.time_stamp
            # Download Corresponding Excel file if it doesn't already exist
            local_file_path = local_dir_path + '\\' + self.name[:-1] + '.xlsx'
            if not os.path.isdir(local_dir_path):
                Path(local_dir_path).mkdir(parents=True, exist_ok=True)
                excel_url = self.path[:-1] + '.xlsx'
                excel = requests.get(excel_url)
                open(local_file_path, 'wb').write(excel.content)
            # Download Corresponding HTML files if they don't already exist
            local_dir_path = local_dir_path + '\\HTML' 
            if not os.path.isdir(local_dir_path):
                pages = ['index.html', 'application.html', 'fcts_and_loops.html', 'loops_index.html', 'topology.html']
                kwargs = {'project_folder': self.cape_path, 'project_name' : 'TEMP', 'zip_project_folder' : False, 'over_write' : True}
                for page in pages:
                    url = self.path + page
                    config.setup_config(url, **kwargs)
                    wp = WebPage()
                    wp.get(url)
                    wp.parse()
                    wp.save_html()
                    wp.save_assets()
                    for thread in wp._threads:
                        thread.join()
                print("Done Downloading Webpages")
                # Move html files/assets to HTML directory and delete TEMP directory
                temp_dir_path = self.cape_path + 'TEMP'
                for directory in self.path[8:].split('/'):
                    temp_dir_path = temp_dir_path + '\\' + directory
                shutil.move(temp_dir_path, local_dir_path)
                shutil.rmtree(self.cape_path + 'TEMP')
            # Add local html file path to browser
            for name in os.listdir(local_dir_path):
                if name.endswith("__index.html"):
                    gui.urls.append(local_dir_path + '\\' + name)
            # Open excel file from local directory and plot
            self.container.openLocalFile(local_file_path)

    class LocalFileNode(LocalTreeNode):
        def __init__(self, path, name, container):
            super().__init__(path, name, container)

        def open(self):
            print("file node open:", self.name, self.id) 
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
                    if re.match('\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', d): # timestamp
                        html_path = fullpath + '\\HTML'
                        for name in os.listdir(html_path): # add html files
                            if name.endswith("__index.html"):
                                gui.urls.append(html_path + '\\' + name)
                        fullpath = fullpath + '\\' + fullpath.split('\\')[-2] + '.xlsx' # open excel file
                        self.container.insertNode(self, DataSourcePanel.LocalFileNode(fullpath, d, self.container))
                    elif os.path.isdir(fullpath):
                        self.container.insertNode(self, DataSourcePanel.LocalDirNode(fullpath, d, self.container))
                    elif os.path.isfile(fullpath):
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

        self.setupLocalRoots()
        self.setupRemoteRoots()
        self.treeview.bind("<<TreeviewOpen>>", self.handleOpenEvent)

    def insertNode(self, parent, node):
        parent_str = parent.id if parent else ''
        self.treeview.insert(parent_str,'end',node.id,text=node.name)  

        
    def openLocalFile(self, source):
        self.loadDataSrcFn(source)

    def handleOpenEvent(self, event):
        nodeId = int(self.treeview.focus())
        node = DataSourcePanel.DataTreeNode.lookupNode(nodeId)
        node.open()


    def setupLocalRoots(self):
        home_dir=expanduser("~")
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(home_dir, 'Home', self) )
        cape_cache_path= os.path.join(home_dir, 'AppData', 'Roaming', 'Cape')
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(cape_cache_path, 'Previously Visited', self) )

    def openLocalChildren(self):
        pass

    def setupRemoteRoots(self):
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://datafront.maqao.exascale-computing.eu/public_html/oneview/', 'Oneview', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteTreeNode('','uvsq', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteTreeNode('','uiuc', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteTreeNode('','uta', self))

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
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                    sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig, texts):
        self.plotFrame = tk.Frame(self.window)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()

        canvas = FigureCanvasTkAgg(fig, self.plotFrame)
        toolbar = NavigationToolbar2Tk(canvas, self.plotFrame)
        toolbar.update()
        canvas.get_tk_widget().pack()
        canvas.draw()

        summaryDf = df[['name', 'short_name', r'%coverage', 'apptime_s', 'C_FLOP [GFlop/s]']]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()

        self.labelTab.buildLabelTable(df, self.labelTab, texts)
    
    # Create tabs for QPlot Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.labelTab = LabelTab(self.tableNote)
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.labelTab, text="Labels")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

class AxesTab(tk.Frame):
    def __init__(self, parent, tab, plotType):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.y_selected = tk.StringVar(value='Choose Y Axis')
        self.x_selected = tk.StringVar(value='Choose X Axis')
        self.tab = tab
        self.plotType = plotType
        x_options = ['C_FLOP [GFlop/s]', 'c=inst_rate_gi/s']
        if self.plotType == 'Custom':
            x_menu = self.custom_axes(self.x_selected)
            y_menu = self.custom_axes(self.y_selected)
        else:  
            if self.plotType == 'QPlot':
                y_options = ['C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', 'C_RAM [GB/s]', 'C_max [GB/s]']
            elif self.plotType == 'TRAWL':
                y_options = ['vec', 'DL1']
            y_menu = tk.OptionMenu(self, self.y_selected, *y_options)
            x_menu = tk.OptionMenu(self, self.x_selected, *x_options)
        y_menu.pack(side=tk.TOP, anchor=tk.NW)
        x_menu.pack(side=tk.TOP, anchor=tk.NW)

        # Update button to replot
        update = tk.Button(self, text='Update', command=self.update_axes)
        update.pack(side=tk.TOP, anchor=tk.NW)

    def custom_axes(self, var):
        menubutton = tk.Menubutton(self, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        # TRAWL
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='TRAWL', menu=menu)
        for metric in ['vec', 'DL1', 'C_FLOP [GFlop/s]', 'c=inst_rate_gi/s']:
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
        if self.x_selected.get() == 'Choose X Axis':
            x_axis = None
        else:
            x_axis = self.x_selected.get()
        if self.y_selected.get() == 'Choose Y Axis':
            y_axis = None
        else:
            y_axis = self.y_selected.get()
        if x_axis or y_axis:
            if self.plotType == 'QPlot':
                self.tab.qplotData.notify(gui.loadedData, x_axis=x_axis, y_axis=y_axis)
            elif self.plotType == 'TRAWL':
                self.tab.trawlData.notify(gui.loadedData, x_axis=x_axis, y_axis=y_axis)
            elif self.plotType == 'Custom':
                self.tab.customData.notify(gui.loadedData, x_axis=x_axis, y_axis=y_axis)

class LabelTab(tk.Frame):
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
        table_labels = df[['name', r'%coverage', 'color']]
        table_labels['short_name'] = table_labels['name']
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            short_names = short_names[['name', 'short_name']]
            inner = pd.merge(left=table_labels, right=short_names, left_on='name', right_on='name')
            inner.rename(columns={'short_name_y':'short_name'}, inplace=True)
            inner = inner[['name', 'short_name', 'color']]
            merged = pd.concat([table_labels, inner]).drop_duplicates('name', keep='last')
        else:
            merged = table_labels
        # sort label table by coverage to keep consistent with data table
        merged = pd.merge(merged, df[['name',r'%coverage']], on='name')
        merged = merged.sort_values(by=r'%coverage_y', ascending=False)
        merged = merged[['name', 'short_name', 'color']]
        table = Table(tab, dataframe=merged, showtoolbar=False, showstatusbar=True)
        table.show()
        table.redraw()
        tk.Button(tab, text="Update", command=lambda: self.updateLabels(table, texts)).grid(row=10, column=0)
        tk.Button(tab, text="Export", command=lambda: self.exportCSV(table)).grid(row=10, column=1, sticky=tk.W)
        return table

    # Merge user input labels with current mappings and replot
    def updateLabels(self, table, texts=None):
        # Check if there are duplicates in short names for a single file
        df = table.model.df
        for color in df['color'].unique():
            curfile = df.loc[df['color'] == color]
            if curfile['short_name'].duplicated().any():
                messagebox.showerror("Duplicate Short Names", "You currently have two or more duplicate short names \
                    \n from the same file. Please change them to continue.")
                return
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            short_names = short_names[['name', 'short_name']]
            table_names = table.model.df[['name', 'short_name']]
            outer = pd.merge(left=short_names, right=table_names, left_on='name', right_on='name', how='outer')
            outer.rename(columns={'short_name_y':'short_name'}, inplace=True)
            outer = outer[['name', 'short_name']].dropna()
            merged = pd.concat([short_names, outer]).drop_duplicates('name', keep='last')
        else:
            merged = table.model.df[['name', 'short_name']]
        merged.to_csv(self.short_names_path)
        gui.loadedData.add_data(gui.sources)

    def exportCSV(self, table):
        export_file_path = tk.filedialog.asksaveasfilename(defaultextension='.csv')
        table.model.df.to_csv(export_file_path, index=False, header=True)

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
        self.level = level
        self.trawlData = trawlData
        if trawlData is not None:
            trawlData.add_observers(self)
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig):
        self.plotFrame = tk.Frame(self.window)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        self.df = df
        self.fig = fig
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

        summaryDf = df[['name', 'short_name', r'%coverage', 'variant', 'vec', 'DL1','C_FLOP [GFlop/s]', 'version', 'color']]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()

        self.labelTab.buildLabelTable(df, self.labelTab)

    # Create tabs for TRAWL Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.labelTab = LabelTab(self.tableNote)
        self.axesTab = AxesTab(self.tableNote, self, 'TRAWL')
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.labelTab, text="Labels")
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, trawlData):
        if self.level == 'Codelet':
            df = trawlData.df
            fig = trawlData.fig
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig)

        elif self.level == 'Source':
            df = trawlData.srcDf
            fig = trawlData.srcFig
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig)

        elif self.level == 'Application':
            df = trawlData.appDf
            fig = trawlData.appFig
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig)

class QPlotTab(tk.Frame):
    def __init__(self, parent, qplotData, level):
        tk.Frame.__init__(self, parent)
        self.level = level
        self.qplotData = qplotData
        if qplotData is not None:
            qplotData.add_observers(self)
        # QPlot tab has a paned window with the data tables and qplot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def adjust_texts(self):
        for child in self.textData['ax'].get_children():
            if isinstance(child, matplotlib.text.Annotation):
                child.remove()
        self.texts = [plt.text(self.textData['xs'][i], self.textData['ys'][i], self.textData['text'][i]) \
            for i in range(len(self.textData['xs']))]
        adjust_text(self.texts, ax=self.textData['ax'], arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame)
        self.toolbar.destroy()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

    def update(self, df, fig, textData=None):
        self.plotFrame = tk.Frame(self.window)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        self.df = df
        self.fig = fig
        self.textData = textData
        # tk.Button(self.plotFrame, text='Adjust Texts', command=self.adjust_texts).pack()
        # if textData:
        #     orig_texts = []
            #print('\n\n\n')
            # self.texts = [plt.text(self.textData['xs'][i], self.textData['ys'][i], self.textData['text'][i]) \
            #     for i in range(len(self.textData['xs']))]
            # for text in self.texts:
            #     print(text)
                # orig_texts.append(plt.text(text.get_position()[0], text.get_position()[1], text.get_text()))
                # r = self.ax.get_figure().canvas.get_renderer()
                # print(text.get_window_extent(r).expanded(*(1,1)).transformed(self.ax.transData.inverted()))
            #print('\n\n\n')
            # adjust_text(self.texts, ax=self.textData['ax'], arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

        # TODO: Hardcode op node name but it could be something else.
        summaryDf = df[['name', 'short_name', r'%coverage', 'variant','C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
            'C_RAM [GB/s]', 'C_max [GB/s]', 'memlevel', 'C_FLOP [GFlop/s]', 'version', 'color']]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summaryTable = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summaryTable.show()
        summaryTable.redraw()

        self.labelTab.buildLabelTable(df, self.labelTab)

    # Create tabs for QPlot Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.labelTab = LabelTab(self.tableNote)
        self.axesTab = AxesTab(self.tableNote, self, 'QPlot')
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.labelTab, text="Labels")
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, qplotData):
        if self.level == 'Codelet':
            df = qplotData.df
            fig = qplotData.fig
            textData = qplotData.textData
            coverageFig = qplotData.coverageFig
            coverageTexts = qplotData.coverageTexts
            # TODO: Separate coverage plot from qplot data
            plotTabs = [self.window, gui.summaryTab.window]
            for tab in plotTabs:
                for w in tab.winfo_children():
                    w.destroy()
            gui.summaryTab.update(df, coverageFig, coverageTexts)
            self.update(df, fig, textData)

        elif self.level == 'Source':
            df = qplotData.srcDf
            fig = qplotData.srcFig
            plotTabs = [self.window]
            for tab in plotTabs:
                for w in tab.winfo_children():
                    w.destroy()
            self.update(df, fig)

        elif self.level == 'Application':
            df = qplotData.appDf
            fig = qplotData.appFig
            plotTabs = [self.window]
            for tab in plotTabs:
                for w in tab.winfo_children():
                    w.destroy()
            self.update(df, fig)

class SIPlotTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class CustomTab(tk.Frame):
    def __init__(self, parent, customData, level):
        tk.Frame.__init__(self, parent)
        self.level = level
        self.customData = customData
        if customData is not None:
            customData.add_observers(self)
        # TRAWL tab has a paned window with the data tables and trawl plot
        self.window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.window.pack(fill=tk.BOTH,expand=True)

    def update(self, df, fig):
        self.plotFrame = tk.Frame(self.window)
        self.tableFrame = tk.Frame(self.window)
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tableFrame, stretch='always')
        self.buildTableTabs()
        self.df = df
        self.fig = fig
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

        summaryDf = df[['name', 'short_name', r'%coverage', 'apptime_s', 'variant','C_L1 [GB/s]', 'C_L2 [GB/s]', 'C_L3 [GB/s]', \
            'C_RAM [GB/s]', 'C_max [GB/s]', 'memlevel', 'C_FLOP [GFlop/s]', 'c=inst_rate_gi/s', 'vec', 'dl1', \
            'num_cores', 'dataset/size', 'prefetchers', 'repetitions', \
            'total_pkg_energy_j', 'total_dram_energy_j', 'total_pkg+dram_energy_j', 'total_pkg_power_w', 'total_dram_power_w', 'total_pkg+dram_power_w', \
            'o=inst_count_gi', 'c=inst_rate_gi/s', \
            'l1_rate_gb/s', 'l2_rate_gb/s', 'l3_rate_gb/s', 'ram_rate_gb/s', 'flop_rate_gflop/s', 'c=inst_rate_gi/s', 'register_addr_rate_gb/s', 'register_data_rate_gb/s', 'register_simd_rate_gb/s', 'register_rate_gb/s', \
            r'%ops[vec]', r'%ops[fma]', r'%ops[div]', r'%ops[sqrt]', r'%ops[rsqrt]', r'%ops[rcp]', \
            r'%inst[vec]', r'%inst[fma]', r'%inst[div]', r'%inst[sqrt]', r'%inst[rsqrt]', r'%inst[rcp]', \
            'version', 'color']]
        summaryDf = summaryDf.sort_values(by=r'%coverage', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summaryDf, showtoolbar=False, showstatusbar=True)
        summary_pt.show()
        summary_pt.redraw()

        self.labelTab.buildLabelTable(df, self.labelTab)
    
    # Create tabs for Custom Summary, Labels, and Axes
    def buildTableTabs(self):
        self.tableNote = ttk.Notebook(self.tableFrame)
        self.summaryTab = tk.Frame(self.tableNote)
        self.labelTab = LabelTab(self.tableNote)
        self.axesTab = AxesTab(self.tableNote, self, 'Custom')
        self.tableNote.add(self.summaryTab, text="Data")
        self.tableNote.add(self.labelTab, text="Labels")
        self.tableNote.add(self.axesTab, text="Axes")
        self.tableNote.pack(fill=tk.BOTH, expand=True)

    # plot data to be updated
    def notify(self, customData):
        if self.level == 'Codelet':
            df = customData.df
            fig = customData.fig
            for w in self.window.winfo_children():
                w.destroy()
            self.update(df, fig)

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

        explorerPanel = ExplorerPanel(self.pw, self.loadDataSource)
        explorerPanel.pack(side = tk.LEFT)
        self.pw.add(explorerPanel)
        right = self.buildTabs(self.pw)
        right.pack(side = tk.LEFT)
        self.pw.add(right)
        self.pw.pack(fill=tk.BOTH,expand=True)
        self.pw.configure(sashrelief=tk.RAISED)
        self.sources = []
        self.urls = []
        self.choice = ''

    def appendData(self):
        self.choice = 'Append'
        self.win.destroy()

    def overwriteData(self):
        self.choice = 'Overwrite'
        self.win.destroy()

    def cancelAction(self):
        if len(self.sources) > 1:
            self.sources.pop(-1)
        self.choice = 'Cancel'
        self.win.destroy()

    def orderAction(self, button):
        self.source_order.append(self.button_to_source.pop(button))
        button.destroy()
        if not self.button_to_source:
            self.win.destroy()

    def loadDataSource(self, source):
        if self.sources:
            self.win = tk.Toplevel()
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
                if self.urls:
                    self.urls.pop(-1)
                return
            elif self.choice == 'Overwrite':
                if self.urls:
                    self.urls = [self.urls.pop(-1)]
                    self.oneviewTab.loadFirstPage()
                self.sources.clear()
            elif self.choice == 'Append':
                self.sources.append(source)
                print("DATA source to be loaded", source)
                self.win = tk.Toplevel()
                self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
                self.win.title('Order Data')
                message = 'Select the order of data files from oldest to newest'
                tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
                self.source_order = []
                self.button_to_source = {}
                for index, source in enumerate(self.sources):
                    b = tk.Button(self.win, text=source.split('\\')[-1].split('.')[0])
                    b['command'] = lambda b=b : self.orderAction(b) 
                    self.button_to_source[b] = source
                    b.grid(row=index+1, column=1, padx=5, pady=10)
                if self.urls:
                    self.oneviewTab.loadSecondPage()
                root.wait_window(self.win)
                self.loadedData.add_data(self.source_order)
                return
        elif self.urls:
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
        self.summaryTab = SummaryTab(self.main_note)
        self.main_note.add(self.oneviewTab, text="Oneview")
        self.main_note.add(self.applicationTab, text="Application")
        self.main_note.add(self.sourceTab, text="Source")
        self.main_note.add(self.codeletTab, text="Codelet")
        self.main_note.add(self.summaryTab, text="Summary")
        # Application, Source, and Codelet each have their own 2nd level tabs
        application_note = ttk.Notebook(self.applicationTab)
        source_note = ttk.Notebook(self.sourceTab)
        codelet_note = ttk.Notebook(self.codeletTab)
        # Codelet tabs
        self.qplotData = QPlotData(self.loadedData)
        self.trawlData = TRAWLData(self.loadedData)
        self.customData = CustomData(self.loadedData)
        self.c_trawlTab = TrawlTab(codelet_note, self.trawlData, 'Codelet')
        self.c_qplotTab = QPlotTab(codelet_note, self.qplotData, 'Codelet')
        self.c_siPlotTab = SIPlotTab(codelet_note)
        self.c_customTab = CustomTab(codelet_note, self.customData, 'Codelet')
        codelet_note.add(self.c_trawlTab, text="TRAWL")
        codelet_note.add(self.c_qplotTab, text="QPlot")
        codelet_note.add(self.c_siPlotTab, text="SI Plot")
        codelet_note.add(self.c_customTab, text="Custom")
        codelet_note.pack(fill=tk.BOTH, expand=1)
        # Source Tabs
        self.s_trawlTab = TrawlTab(source_note, self.trawlData, 'Source')
        self.s_qplotTab = QPlotTab(source_note, self.qplotData, 'Source')
        self.s_siPlotTab = SIPlotTab(source_note)
        source_note.add(self.s_trawlTab, text="TRAWL")
        source_note.add(self.s_qplotTab, text="QPlot")
        source_note.add(self.s_siPlotTab, text="SI Plot")
        source_note.pack(fill=tk.BOTH, expand=True)
        # Application tabs
        self.w_trawlTab = TrawlTab(application_note, self.trawlData, 'Application')
        self.w_qplotTab = QPlotTab(application_note, self.qplotData, 'Application')
        self.w_siPlotTab = SIPlotTab(application_note)
        application_note.add(self.w_trawlTab, text="TRAWL")
        application_note.add(self.w_qplotTab, text="QPlot")
        application_note.add(self.w_siPlotTab, text="SI Plot")
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
