import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from argparse import ArgumentParser
#from idlelib.TreeWidget import ScrolledCanvas, FileTreeItem, TreeNode
from pandastable import Table
import pandas as pd
import os
from os.path import expanduser
import tempfile
import pkg_resources.py2_warn
from web_browser import BrowserFrame
from cefpython3 import cefpython as cef
import sys
from sys import platform
from pywebcopy import WebPage, config
import logging
#from generate_QPlot import compute_capacity
from transitions.extensions import GraphMachine as Machine
from transitions import State
from metric_names import MetricName
from explorer_panel import ExplorerPanel
from summary import SummaryTab
from trawl import TrawlTab
from qplot import QPlotTab
from si import SIPlotTab
from custom import CustomTab
from plot_3d import Data3d, Tab3d
from scurve import ScurveTab
from scurve_all import ScurveAllTab
from swbias import SWbiasTab
from meta_tabs import ShortNameTab, AxesTab, MappingsTab, GuideTab, FilteringTab, DataTab
from plot_interaction import PlotInteraction
from analyzer_model import LoadedData
from analyzer_base import HideableTab
from analyzer_controller import AnalyzerController

# pywebcopy produces a lot of logging that clouds other useful information
logging.disable(logging.CRITICAL)

class TabTrackingNB(ttk.Notebook): 
    def __init__(self, parent):
        super().__init__(parent)
        self.currentTab = None 
        self.bind('<<NotebookTabChanged>>', self.plotTabChanged)

    def change_tab(self, name):
        tabNames = [self.tab(i, option='text') for i in self.tabs()]
        self.select(tabNames.index(name))
        
    def plotTabChanged(self, evt):
        #print(f'updated ttnb tab:{self.index(self.select())}')
        if self.currentTab:
            self.currentTab.hide()
        self.currentTab = self.nametowidget(self.select())
        self.currentTab.expose()

    def updateAllTabStatus(self):
        for tabName in self.tabs():
            tab = self.nametowidget(tabName)
            if tab is self.currentTab:
                tab.expose()
            else:
                tab.hide()
                
class LevelContainerTab(HideableTab):
    # NOTE: some parameter notes: parent is the GUI level parent (e.g. notebook object of tab) while container is logical level parent (which may skip a few level of GUI parents)
    #       The control object will therefore be retrieved from container rather than parent to avoid extra hoppes of references.
    def __init__(self, parent, container, level):
        super().__init__(parent)
        self.level = level
        self.container = container
        self.plotTabs = []
        self.dataTabs = []
        parent.add(self, text=level)
        # Each level has its own paned window
        plotPw = tk.PanedWindow(self, orient="vertical", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        # Each level has its own plot tabs
        self.plot_note = TabTrackingNB(plotPw)

        # Codelet Plot Data
        # 3D breaks 'name:marker' because of different plotting
        # self.3dData = Data3d(self.loadedData, self, root, level)
        # binned scurve break datapoint selection because of different text:marker map
        # Disable for now as not used.  
        # To enable, need to compute text:marker to-and-from regular text:marker to binned text:marker
        # self.scurveData = ScurveData(self.loadedData, self, root, level)
        # Codelet Plot Tabs
        # self.3dTab = Tab3d(self.plot_note, self.3dData)
        # self.scurveTab = ScurveTab(self.plot_note, self.scurveData)
        self.addPlotTab(SummaryTab(self.plot_note, container), name='Summary')
        self.addPlotTab(TrawlTab(self.plot_note, container), name='TRAWL')
        self.addPlotTab(QPlotTab(self.plot_note, container), name='QPlot')
        self.addPlotTab(SIPlotTab(self.plot_note, container), name='SI Plot')
        self.addPlotTab(CustomTab(self.plot_note, container), name='Custom')
        # self.addPlotTab(self.3dTab, name='3D')
        # self.addPlotTab(self.scurveTab, name='S-Curve (Bins)')
        self.addPlotTab(ScurveAllTab(self.plot_note, container), name='S-Curve')
        self.addPlotTab(SWbiasTab(self.plot_note, container), name='SWbias')
        # Create Per Level Tabs Underneath Plot Notebook
        self.data_note = TabTrackingNB(plotPw)
        # Data tabs
        self.addDataTab(DataTab(self.data_note), name='Data')
        # Short name tabs
        self.addDataTab(ShortNameTab(self.data_note), name='Short Names')
        # Mapping tabs
        self.addDataTab(MappingsTab(self.data_note), name='Mappings')
        # Filtering tabs
        self.addDataTab(FilteringTab(self.data_note), name='Filtering')
        # Packing
        self.plot_note.pack(side = tk.TOP, expand=True)
        self.data_note.pack(side = tk.BOTTOM, expand=True)
        plotPw.add(self.plot_note, stretch='always')
        plotPw.add(self.data_note, stretch='always')
        plotPw.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.levelData = None

    @property
    def control(self):
        return self.container.control

    def change_tab(self, name):
        self.plot_note.change_tab(name)
        
    def getPausables(self):
        return [self.levelData] if self.levelData else []
        

    def addTab(self, tab, name, tabs, notebook):
        tabs.append(tab)
        notebook.add(tab, text=name)

    def addPlotTab(self, tab, name):
        self.addTab(tab, name, self.plotTabs, self.plot_note)

    def addDataTab(self, tab, name):
        self.addTab(tab, name, self.dataTabs, self.data_note)

    def resetTabValues(self):
        for tab in self.plotTabs:
            tab.resetTabValues()

    def setLevelData(self, levelData):
        self.levelData = levelData
        for tab in self.plotTabs + self.dataTabs:
            tab.setLevelData(levelData)

    def setLoadedData(self, loadedDataArg):
        self.setLevelData(loadedDataArg.levelData[self.level])
        # Update notebook to set the right exposed/hidden status to underlying gui states
        self.plot_note.updateAllTabStatus()
        self.data_note.updateAllTabStatus()
        


    
class CodeletTab(LevelContainerTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, 'Codelet')

class ApplicationTab(LevelContainerTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, 'Application')

class SourceTab(LevelContainerTab):
    def __init__(self, parent, container):
        super().__init__(parent, container, 'Source')

class ExplorerPanelTab(tk.Frame):
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
        self.loadedData = None

    @property
    def urls(self):
        return self.loadedData.urls

    def setLoadedData(self, loadedData):
        self.loadedData = loadedData

    def refresh(self):
        if self.browser1: self.browser1.refresh()
        if self.browser2: self.browser2.refresh()

    def addRefresh(self):
        self.refreshButton = tk.Button(self.window, text="Refresh", command=self.refresh)
        self.refreshButton.pack(side=tk.TOP, anchor=tk.NW)

    def loadPage(self):
        if len(self.urls) == 1: self.loadFirstPage()
        elif len(self.urls) > 1: self.loadSecondPage()
    
    def loadFirstPage(self):
        self.removePages()
        self.browser1 = BrowserFrame(self.window)
        self.window.add(self.browser1, stretch='always')
        self.addRefresh()
        current_tab = gui.main_note.select()
        gui.main_note.select(0)
        self.update()
        gui.main_note.select(current_tab)
        self.browser1.change_browser(url=self.urls[0])

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
        self.browser1.change_browser(url=self.urls[0])
        self.browser2.change_browser(url=self.urls[1])

    def removePages(self):
        if self.browser1: 
            self.window.remove(self.browser1)
            self.refreshButton.destroy()
        if self.browser2: self.window.remove(self.browser2)


class AnalyzerGui(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        #self.loadedData = LoadedData()

        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        # filemenu.add_command(label="Save State", command=self.saveState)
        # filemenu.add_command(label="Save State(Testing)", command=self.saveStateTest)
        filemenu.add_command(label="New Window", command=self.newWindow)
        # filemenu.add_command(label="Open")#, command=self.configTab.open)
        # filemenu.add_command(label="Save")#, command=lambda: self.configTab.save(False))
        # filemenu.add_command(label="Save As...")#, command=lambda: self.configTab.save(True))
        # filemenu.add_separator()
        # filemenu.add_command(label="Exit")#, command=self.file_exit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        parent.config(menu=menubar)

        self.pw=tk.PanedWindow(parent, orient="vertical", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)

        fullPw = self.buildTabs(self.pw)
        fullPw.pack(side = tk.TOP, fill=tk.BOTH, expand=True)
        self.pw.add(fullPw, stretch='always')

        # Explorer Panel and Guide tab in global notebook
        self.global_note = ttk.Notebook(self.pw)

        self.explorerPanel = ExplorerPanel(self.global_note, self)
        self.global_note.add(self.explorerPanel, text='Data Source')

        # TODO: Refactor Guide Tab to not need a specific tab as a parameter
        # self.guide_tab = GuideTab(self.global_note, self.c_summaryTab)
        self.guide_tab = GuideTab(self.global_note)
        self.global_note.add(self.guide_tab, text='Guide')

        self.global_note.pack(side = tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.pw.add(self.global_note, stretch='never')

        self.pw.pack(fill=tk.BOTH, expand=True)
        self.pw.configure(sashrelief=tk.RAISED)
        # self.sources = []
        # self.loaded_url = None
        # self.loadType = ''
        # self.choice = ''
        self.control = None

    def newWindow(self):
        window = tk.Toplevel(self.master)
        window.geometry(self.winfo_toplevel().geometry())
        self.fillWindow(window)

    @staticmethod
    def fillWindow(window):
        gui = AnalyzerGui(window)
        loadedData = LoadedData()
        # Will also link loadedData to gui 
        control = AnalyzerController(gui, loadedData)
        gui.guide_tab.fsm.setControl(control)
    
    def setControl(self, control):
        self.control = control
        
    # def appendData(self):
    #     self.choice = 'Append'
    #     self.win.destroy()

    # def overwriteData(self):
    #     self.choice = 'Overwrite'
    #     self.win.destroy()

    # def cancelAction(self):
    #     self.choice = 'Cancel'
    #     self.win.destroy()

    def appendAnalysisData(self, df, mappings, analytics, data):
        # need to combine df with current summaryDf
        self.loadedData.summaryDf = pd.concat([self.loadedData.summaryDf, df]).drop_duplicates(keep='last').reset_index(drop=True)
        # need to combine mappings with current mappings and add speedups
        
    def loadSavedState(self, levels=[]):
        pass
        # print("restore: ", self.loadedData.restore)
        # if len(self.sources) >= 1:
        #     self.win = tk.Toplevel()
        #     center(self.win)
        #     self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
        #     self.win.title('Existing Data')
        #     message = 'This tool currently doesn\'t support appending server data with\nAnalysis Results data. Would you like to overwrite\nany existing plots with this new data?'
        #     #if not self.loadedData.restore: message = 'This tool currently doesn\'t support appending server data with\nAnalysis Results data. Would you like to overwrite\nany existing plots with this new data?'
        #     #else: 
        #         #message = 'Would you like to append to the existing\ndata or overwrite with the new data?'
        #         #tk.Button(self.win, text='Append', command= lambda df=df, mappings=mappings, analytics=analytics, data=data : self.appendAnalysisData(df, mappings, analytics, data)).grid(row=1, column=0, sticky=tk.E)
        #     tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        #     tk.Button(self.win, text='Overwrite', command=self.overwriteData).grid(row=1, column=1)
        #     tk.Button(self.win, text='Cancel', command=self.cancelAction).grid(row=1, column=2, pady=10, sticky=tk.W)
        #     root.wait_window(self.win)
        # if self.choice == 'Cancel': return
        # #self.sources = ['Analysis Result'] # Don't need the actual source path for Analysis Results
        # self.resetTabValues()
        # self.loadedData.add_saved_data(levels)

    def setLoadedData(self, loadedData):
        self.loadedData = loadedData
        self.oneviewTab.setLoadedData(loadedData) 
        for tab in self.allTabs:
            tab.setLoadedData(loadedData)
        # Update notebook to set the right exposed/hidden status to underlying gui states
        self.level_plot_note.updateAllTabStatus()
        
    def resetTabValues(self):
        #self.tabs = [gui.c_qplotTab, gui.c_trawlTab, gui.c_customTab, gui.c_siPlotTab, gui.c_summaryTab, \
        #             gui.c_scurveTab, gui.c_scurveAllTab, \
        #        gui.s_qplotTab,  gui.s_trawlTab, gui.s_customTab, \
        #        gui.a_qplotTab, gui.a_trawlTab, gui.a_customTab]
        for tab in self.allTabs:
            tab.resetTabValues()
        # self.tabs = [gui.c_qplotTab, gui.c_trawlTab, gui.c_customTab, gui.c_siPlotTab, gui.c_summaryTab, \
        #              gui.c_scurveAllTab, \
        #         gui.s_qplotTab,  gui.s_trawlTab, gui.s_customTab, \
        #         gui.a_qplotTab, gui.a_trawlTab, gui.a_customTab]
        # for tab in self.tabs:
        #     tab.x_scale = tab.orig_x_scale
        #     tab.y_scale = tab.orig_y_scale
        #     tab.x_axis = tab.orig_x_axis
        #     tab.y_axis = tab.orig_y_axis
        #     tab.variants = [gui.loadedData.default_variant] #TODO: edit this out
        #     tab.current_labels = []
        # # Reset cluster var for SIPlotData so find_si_clusters() is called again 
        # gui.c_siplotData.run_cluster = True

    class ProgressDialog(tk.simpledialog.Dialog):
        # modal - if True, make this window taking all inputs from user
        def __init__(self, parent, work_name, work_function, modal=True):
            self.modal = modal
            self.work_name = work_name
            self.work_function = work_function
            self.parent = parent
            self.progress = None
            # Need to launch thread first because the constructor will block code execution
            threading.Thread(target=self.run, name=work_name).start()
            # Pass Toplevel to make sure dialog in better position
            super().__init__(parent.winfo_toplevel())
            
        # This method will cause the dialog window take all inputs from users, making results of GUI not accepting user inputs
        def grab_set(self):
            if self.modal: 
                super().grab_set()
        
        def body(self, master):
            label = tk.Label(master, text=f'In progress: {self.work_name}')
            self.progress = ttk.Progressbar(master, mode='indeterminate', maximum=50)
            label.pack()
            self.progress.pack()
            self.progress.start(25)

        def run(self):
            self.work_function()
            self.progress.stop()
            self.ok()

        # Override to get rid of the "OK", "Cancel" buttons
        def buttonbox(self):
            pass
            
    # work_function will be invoked as work_function()
    def wait_for_work(self, work_name, work_function):
        AnalyzerGui.ProgressDialog(self, work_name, work_function, modal=True)

    def display_work(self, work_name, work_function):
        AnalyzerGui.ProgressDialog(self, work_name, work_function, modal=False)

    def loadUrl(self, choice, url):
        if choice != 'Append':
            self.oneviewTab.removePages() # Remove any previous OV HTML

        if url:
            if sys.platform != 'darwin':
                self.oneviewTab.loadPage()

    # def clearTabs(self, levels=['All']):
    #     tabs = []
    #     if 'Codelet' in levels or 'All' in levels:
    #         tabs.extend([gui.c_summaryTab, gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab, gui.c_scurveAllTab])
    #         # tabs.extend([gui.c_summaryTab, gui.c_trawlTab, gui.c_qplotTab, gui.c_siPlotTab, gui.c_customTab, gui.c_scurveTab, gui.c_scurveAllTab])
    #     if 'Source' in levels or 'All' in levels:
    #         tabs.extend([gui.s_summaryTab, gui.s_trawlTab, gui.s_qplotTab, gui.s_customTab])
    #     if 'Application' in levels or 'All' in levels:
    #         tabs.extend([gui.a_summaryTab, gui.a_trawlTab, gui.a_qplotTab, gui.a_customTab])
    #     for tab in tabs:
    #         for widget in tab.window.winfo_children():
    #             widget.destroy()

    @property
    def allTabs(self):
        return [self.codeletTab, self.sourceTab, self.applicationTab]

    def buildTabs(self, parent):
        infoPw=tk.PanedWindow(parent, orient="horizontal", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        # Oneview (Left Window)
        self.oneview_note = ttk.Notebook(infoPw)
        self.oneviewTab = OneviewTab(self.oneview_note)
        self.oneview_note.add(self.oneviewTab, text="Oneview")
        # Plots (Right Window)
        self.level_plot_note = TabTrackingNB(infoPw)
        #self.codeletTab = CodeletTab(self.level_plot_note, self, root)
        self.codeletTab = CodeletTab(self.level_plot_note, self)
        #self.codeletTab.setLoadedData(self.loadedData)
        #self.sourceTab = SourceTab(self.level_plot_note, self, root)
        self.sourceTab = SourceTab(self.level_plot_note, self)
        #self.codeletTab.setLoadedData(self.loadedData)
        #self.applicationTab = ApplicationTab(self.level_plot_note, self, root)
        self.applicationTab = ApplicationTab(self.level_plot_note, self)
        #self.codeletTab.setLoadedData(self.loadedData)

        # self.level_plot_note.add(self.codeletTab, text='Codelet')
        # self.level_plot_note.add(self.sourceTab, text='Source')
        # self.level_plot_note.add(self.applicationTab, text='Application')
        #self.level_plot_note.bind('<<NotebookTabChanged>>', lambda evt: print(f'updated level tab:{self.level_plot_note.index(self.level_plot_note.select())}'))


        # # Each level has its own paned window
        # c_plotPw = tk.PanedWindow(self.codeletTab, orient="vertical", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        # s_plotPw = tk.PanedWindow(self.sourceTab, orient="vertical", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        # a_plotPw = tk.PanedWindow(self.applicationTab, orient="vertical", sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)


        # # Each level has its own plot tabs
        # c_plot_note = ttk.Notebook(c_plotPw)
        # s_plot_note = ttk.Notebook(s_plotPw)
        # a_plot_note = ttk.Notebook(a_plotPw)


        # # Codelet Plot Data
        # c_coverageData = CoverageData(self.loadedData, self, root, 'Codelet')
        # self.c_siplotData = SIPlotData(self.loadedData, self, root, 'Codelet')
        # c_qplotData = QPlotData(self.loadedData, self, root, 'Codelet')
        # c_trawlData = TRAWLData(self.loadedData, self, root, 'Codelet')
        # c_customData = CustomData(self.loadedData, self, root, 'Codelet')
        # # 3D breaks 'name:marker' because of different plotting
        # # self.c_3dData = Data3d(self.loadedData, self, root, 'Codelet')
        # # binned scurve break datapoint selection because of different text:marker map
        # # Disable for now as not used.  
        # # To enable, need to compute text:marker to-and-from regular text:marker to binned text:marker
        # # self.c_scurveData = ScurveData(self.loadedData, self, root, 'Codelet')
        # c_scurveAllData = ScurveAllData(self.loadedData, self, root, 'Codelet')
        # # Codelet Plot Tabs
        # self.c_summaryTab = SummaryTab(c_plot_note, c_coverageData)
        # self.c_siPlotTab = SIPlotTab(c_plot_note, self.c_siplotData)
        # self.c_qplotTab = QPlotTab(c_plot_note, c_qplotData)
        # self.c_trawlTab = TrawlTab(c_plot_note, c_trawlData)
        # self.c_customTab = CustomTab(c_plot_note, c_customData)
        # # self.c_3dTab = Tab3d(c_plot_note, self.c_3dData)
        # # self.c_scurveTab = ScurveTab(c_plot_note, self.c_scurveData)
        # self.c_scurveAllTab = ScurveAllTab(c_plot_note, c_scurveAllData)
        # c_plot_note.add(self.c_summaryTab, text='Summary')
        # c_plot_note.add(self.c_trawlTab, text='TRAWL')
        # c_plot_note.add(self.c_qplotTab, text='QPlot')
        # c_plot_note.add(self.c_siPlotTab, text='SI Plot')
        # c_plot_note.add(self.c_customTab, text='Custom')
        # # c_plot_note.add(self.c_3dTab, text='3D')
        # # c_plot_note.add(self.c_scurveTab, text='S-Curve (Bins)')
        # c_plot_note.add(self.c_scurveAllTab, text='S-Curve')
        # # Source Plot Data
        # self.s_coverageData = CoverageData(self.loadedData, self, root, 'Source')
        # self.s_qplotData = QPlotData(self.loadedData, self, root, 'Source')
        # self.s_trawlData = TRAWLData(self.loadedData, self, root, 'Source')
        # self.s_customData = CustomData(self.loadedData, self, root, 'Source')
        # # Source Plot Tabs
        # self.s_summaryTab = SummaryTab(s_plot_note, self.s_coverageData)
        # self.s_trawlTab = TrawlTab(s_plot_note, self.s_trawlData)
        # self.s_qplotTab = QPlotTab(s_plot_note, self.s_qplotData)
        # self.s_customTab = CustomTab(s_plot_note, self.s_customData)
        # s_plot_note.add(self.s_summaryTab, text='Summary')
        # s_plot_note.add(self.s_trawlTab, text='TRAWL')
        # s_plot_note.add(self.s_qplotTab, text='QPlot')
        # s_plot_note.add(self.s_customTab, text='Custom')
        # # Application Plot Data
        # self.a_coverageData = CoverageData(self.loadedData, self, root, 'Application')
        # self.a_qplotData = QPlotData(self.loadedData, self, root, 'Application')
        # self.a_trawlData = TRAWLData(self.loadedData, self, root, 'Application')
        # self.a_customData = CustomData(self.loadedData, self, root, 'Application')
        # # Application Plot Tabs
        # self.a_summaryTab = SummaryTab(a_plot_note, self.a_coverageData)
        # self.a_trawlTab = TrawlTab(a_plot_note, self.a_trawlData)
        # self.a_qplotTab = QPlotTab(a_plot_note, self.a_qplotData)
        # self.a_customTab = CustomTab(a_plot_note, self.a_customData)
        # a_plot_note.add(self.a_summaryTab, text='Summary')
        # a_plot_note.add(self.a_trawlTab, text='TRAWL')
        # a_plot_note.add(self.a_qplotTab, text='QPlot')
        # a_plot_note.add(self.a_customTab, text='Custom')
        # # Create Per Level Tabs Underneath Plot Not
        # c_data_note = ttk.Notebook(c_plotPw)
        # s_data_note = ttk.Notebook(s_plotPw)
        # a_data_note = ttk.Notebook(a_plotPw)
        # # Data tabs
        # self.c_dataTableData = DataTabData(self.loadedData, self, root, 'Codelet')
        # self.s_dataTableData = DataTabData(self.loadedData, self, root, 'Source')
        # self.a_dataTableData = DataTabData(self.loadedData, self, root, 'Application')
        # self.c_dataTable = DataTab(c_data_note, self.c_dataTableData)
        # self.s_dataTable = DataTab(s_data_note, self.s_dataTableData)
        # self.a_dataTable = DataTab(a_data_note, self.a_dataTableData)
        # c_data_note.add(self.c_dataTable, text='Data')
        # s_data_note.add(self.s_dataTable, text='Data')
        # a_data_note.add(self.a_dataTable, text='Data')
        # # Short name tabs
        # self.c_shortNameData = ShortNameData(self.loadedData, self, root, 'Codelet')
        # self.s_shortNameData = ShortNameData(self.loadedData, self, root, 'Source')
        # self.a_shortNameData = ShortNameData(self.loadedData, self, root, 'Application')
        # self.c_shortNameTable = ShortNameTab(c_data_note, self.c_shortNameData)
        # self.s_shortNameTable = ShortNameTab(s_data_note, self.s_shortNameData)
        # self.a_shortNameTable = ShortNameTab(a_data_note, self.a_shortNameData)
        # c_data_note.add(self.c_shortNameTable, text='Short Names')
        # s_data_note.add(self.s_shortNameTable, text='Short Names')
        # a_data_note.add(self.a_shortNameTable, text='Short Names')
        # # Mapping tabs
        # self.c_mappingsData = MappingsData(self.loadedData, self, root, 'Codelet')
        # self.s_mappingsData = MappingsData(self.loadedData, self, root, 'Source')
        # self.a_mappingsData = MappingsData(self.loadedData, self, root, 'Application')
        # self.c_mappingsTab = MappingsTab(c_data_note, self.c_mappingsData)
        # self.s_mappingsTab = MappingsTab(s_data_note, self.s_mappingsData)
        # self.a_mappingsTab = MappingsTab(a_data_note, self.a_mappingsData)
        # c_data_note.add(self.c_mappingsTab, text='Mappings')
        # s_data_note.add(self.s_mappingsTab, text='Mappings')
        # a_data_note.add(self.a_mappingsTab, text='Mappings')
        # # Filtering tabs
        # self.c_filteringData = FilteringData(self.loadedData, self, root, 'Codelet')
        # self.s_filteringData = FilteringData(self.loadedData, self, root, 'Source')
        # self.a_filteringData = FilteringData(self.loadedData, self, root, 'Application')
        # self.c_filteringTab = FilteringTab(c_data_note, self.c_filteringData)
        # self.s_filteringTab = FilteringTab(s_data_note, self.s_filteringData)
        # self.a_filteringTab = FilteringTab(a_data_note, self.a_filteringData)
        # c_data_note.add(self.c_filteringTab, text='Filtering')
        # s_data_note.add(self.s_filteringTab, text='Filtering')
        # a_data_note.add(self.a_filteringTab, text='Filtering')
        # # Packing
        # c_plot_note.pack(side = tk.TOP, expand=True)
        # s_plot_note.pack(side = tk.TOP, expand=True)
        # a_plot_note.pack(side = tk.TOP, expand=True)
        # c_data_note.pack(side = tk.BOTTOM, expand=True)
        # s_data_note.pack(side = tk.BOTTOM, expand=True)
        # a_data_note.pack(side = tk.BOTTOM, expand=True)
        # c_plotPw.add(c_plot_note, stretch='always')
        # c_plotPw.add(c_data_note, stretch='always')
        # s_plotPw.add(s_plot_note, stretch='always')
        # s_plotPw.add(s_data_note, stretch='always')
        # a_plotPw.add(a_plot_note, stretch='always')
        # a_plotPw.add(a_data_note, stretch='always')
        # c_plotPw.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # s_plotPw.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # a_plotPw.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.oneview_note.pack(side = tk.LEFT, expand=True)
        self.level_plot_note.pack(side=tk.RIGHT, expand=True)
        infoPw.add(self.oneview_note, stretch='always')
        infoPw.add(self.level_plot_note, stretch='always')
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
    root = tk.Tk()
    root.title("Cape Analyzer")
    root.bind("<Button-1>", check_focus)
    # Set opening window to portion of user's screen wxh
    width  = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry('%sx%s' % (int(width/1.2), int(height/1.2)))
    #root.geometry(f'{width}x{height}')

    # The AnalyzerGui is global so that the data source panel can access it
    # global gui

    AnalyzerGui.fillWindow(root)

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
