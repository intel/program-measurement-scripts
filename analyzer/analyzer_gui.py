import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from argparse import ArgumentParser
#from idlelib.TreeWidget import ScrolledCanvas, FileTreeItem, TreeNode
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from pandastable import Table
import pandas as pd
import pathlib
import os
from os.path import expanduser
from summarize import summary_report
from generate_QPlot import parse_ip as parse_ip_qplot
from generate_SI import parse_ip as parse_ip_siplot
import tempfile
import pkg_resources.py2_warn
from web_browser import (MainFrame, BrowserFrame)
from cefpython3 import cefpython as cef
import sys
import requests
from lxml import html
import time
from pathlib import Path


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
    def add_data(self, source):
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        print(tmpfile.name)
        in_files = [source]
        in_file_format ='csv' if os.path.splitext(source)[1] == '.csv' else 'xlsx'
        user_op_file = None
        request_no_cqa = False
        request_use_cpi = False
        request_skip_energy = False
        request_skip_stalls = False
        request_succinct = False
        short_names_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\short_names.csv'
        if os.path.isfile(short_names_path):
            short_names = short_names_path
        else: 
            short_names = None
        summary_report(in_files, tmpfile.name, in_file_format, user_op_file, request_no_cqa, \
            request_use_cpi, request_skip_energy, request_skip_stalls, request_succinct, short_names)
        # Just use file for data storage now.  May explore keeping dataframe in future if needed.
        # Currently assume only 1 run is loaded but we should extend this to aloow loading multiple
        # data and pool data together
        self.data_items=[tmpfile.name]
        #self.data_items.append(tmpfile.name)
        self.notify_observers()
    def get_data_items(self):
        return self.data_items
        
class QPlotData(Observable):
    def __init__(self, loadedData):
        super().__init__()
        self.loadedData = loadedData
        # Watch for updates in loaded data
        loadedData.add_observers(self)
        self.df = None
        self.fig = None

    def getDf(self):
        return self.df
    
    def getFig(self):
        return self.fig

    def notify(self, loadedData, x_axis=None, y_axis=None):
        print("Notified from ", loadedData)
        chosen_node_set = set(['L1','L2','L3','RAM','FLOP'])
        #fname=tmpfile.name
        # Assume only one set of data loaded for now
        fname=loadedData.get_data_items()[0]
        df_XFORM, fig_XFORM, df_ORIG, fig_ORIG = parse_ip_qplot\
            (fname, "test", "scalar", "Testing", chosen_node_set, False, gui=True, y_axis=y_axis)
        # TODO: Need to settle how to deal with multiple plots/dataframes
        # May want to let user to select multiple plots to look at within this tab
        # Currently just save the ORIG data
        self.df = df_ORIG if df_ORIG is not None else df_XFORM
        self.fig = fig_ORIG if fig_ORIG is not None else fig_XFORM
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
            self.children = []

        def open(self):
            print("remote node open:", self.name, self.id) 
            page = requests.get(self.path)
            content_type = page.headers['content-type']

            # Webpage node
            if content_type == 'text/html':
                # Load this webpage into Oneview tab
                gui.mainFrame.browser_frame.change_browser(url=self.path)
                # Replicate remote directory structure
                local_file_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\Oneview'
                dirs = self.path[66:].split('/')
                for directory in dirs:
                    local_file_path = local_file_path + '\\' + directory
                # Each file has its own directory with versions of that file labeled by time stamp
                local_dir_path = local_file_path
                local_file_path = local_file_path + '\\' + self.time_stamp + '.xlsx'
                print(f'LOCAL PATH:{local_file_path}')
                # Download Corresponding Excel file if it doesn't already exist
                if not os.path.isfile(local_file_path):
                    Path(local_dir_path).mkdir(parents=True, exist_ok=True)
                    excel_url = self.path[:-1] + '.xlsx'
                    excel = requests.get(excel_url)
                    open(local_file_path, 'wb').write(excel.content)
                # Open excel file from local directory and plot
                self.container.openLocalFile(local_file_path)

            # Directory node
            elif content_type == 'text/html;charset=ISO-8859-1':
                tree = html.fromstring(page.content)
                for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                    hyperlink = link_element.xpath('td[position()=2]/a')[0]
                    name = hyperlink.get('href')
                    # Only show html pages, xlsx will be auto loaded
                    if name[-1] == '/' and name not in self.children:
                        self.children.append(name)
                        fullpath = self.path + name
                        # Time stamp will be the date last modified (TODO: Distinguish between same day versions)
                        time_stamp = link_element.xpath('td[position()=3]/text()')[0][:10]
                        self.container.insertNode(self, DataSourcePanel.RemoteNode(fullpath, name, self.container, time_stamp=time_stamp))

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
                    if os.path.isdir(fullpath):
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
        self.insertNode(self.localNode, DataSourcePanel.LocalDirNode(expanduser("~"), 'Home', self) )

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

class WorkLoadTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class CodeletTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class SummaryTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class DetailedSummaryTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class AxesTab(tk.Frame):
    def __init__(self, parent, qplotTab):
        tk.Frame.__init__(self, parent)
        self.qplotTab = qplotTab
        self.parent = parent
        # Options for y axis
        self.y_selected = tk.StringVar()
        self.y_selected.set('Choose Y Axis')
        y_options = ['C_L1', 'C_L2', 'C_L3', 'C_RAM', 'C_max']
        y_menu = tk.OptionMenu(self, self.y_selected, *y_options)
        y_menu.pack(side=tk.TOP, anchor=tk.NW)

        # Update button to replot
        update = tk.Button(self, text='Update', command=self.update_axes)
        update.pack(side=tk.TOP, anchor=tk.NW)
    
    def update_axes(self):
        if self.y_selected.get() == 'Choose Y Axis':
            pass
        else:
            self.qplotTab.qplotData.notify(gui.loadedData, y_axis=self.y_selected.get())

class LabelTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class ApplicationTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class OneviewTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)     
        # Oneview embedded in this frame
        self.oneview_frame = tk.Frame(self)
        self.oneview_frame.pack(fill=tk.BOTH, expand=True)   

class TrawlTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class QPlotTab(tk.Frame):
    def __init__(self, parent, qplotData):
        tk.Frame.__init__(self, parent)
        self.qplotData = qplotData
        if qplotData is not None:
            qplotData.add_observers(self)
        # QPlot tab has paned window with summary table and qplot
        self.c_qplot_window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.c_qplot_window.pack(fill=tk.BOTH,expand=True)

        # Create short names mapping file if it doesn't already exist
        self.short_names_path = expanduser('~') + '\\AppData\\Roaming\\Cape\\short_names.csv'
        self.short_names_dir_path = expanduser('~') + '\\AppData\\Roaming\\Cape'
        if not os.path.isfile(self.short_names_path):
            Path(self.short_names_dir_path).mkdir(parents=True, exist_ok=True)
            open(self.short_names_path, 'wb')

    # Create tabs for summary table and short labels
    def buildSummaryTabs(self):
        self.summary_note = ttk.Notebook(self.summary_frame)
        self.summaryTab = SummaryTab(self.summary_note)
        self.labelTab = LabelTab(self.summary_note)
        self.detailedSummaryTab = DetailedSummaryTab(self.summary_note)
        self.axesTab = AxesTab(self.summary_note, self)
        self.summary_note.add(self.summaryTab, text="Summary")
        self.summary_note.add(self.labelTab, text="Labels")
        self.summary_note.add(self.detailedSummaryTab, text="Detailed Summary")
        self.summary_note.add(self.axesTab, text="Axes")
        self.summary_note.pack(fill=tk.BOTH, expand=True)

    # Create table for Labels tab and update button
    def buildLabelTable(self, df):
        table_labels = df[['name']]
        table_labels['short_name'] = table_labels['name']
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            short_names = short_names[['name', 'short_name']]
            inner = pd.merge(left=table_labels, right=short_names, left_on='name', right_on='name')
            inner.rename(columns={'short_name_y':'short_name'}, inplace=True)
            inner = inner[['name', 'short_name']]
            merged = pd.concat([table_labels, inner]).drop_duplicates('name', keep='last')
        else:
            merged = table_labels

        self.label_table = Table(self.labelTab, dataframe=merged, showtoolbar=True, showstatusbar=True)
        self.label_table.show()

        update_b = tk.Button(self.labelTab, text="Update", command=self.updateLabels)
        update_b.grid()

    # Merge user input labels with current mappings and replot
    def updateLabels(self):
        if os.path.getsize(self.short_names_path) > 0:
            short_names = pd.read_csv(self.short_names_path)
            short_names = short_names[['name', 'short_name']]
            table_names = self.label_table.model.df[['name', 'short_name']]
            outer = pd.merge(left=short_names, right=table_names, left_on='name', right_on='name', how='outer')
            outer.rename(columns={'short_name_y':'short_name'}, inplace=True)
            outer = outer[['name', 'short_name']].dropna()
            merged = pd.concat([short_names, outer]).drop_duplicates('name', keep='last')
        else:
            merged = self.label_table.model.df[['name', 'short_name']]
        merged.to_csv(self.short_names_path)
        gui.loadDataSource(gui.source)

    # QPlot data updated
    def notify(self, qplotData):
        df = qplotData.getDf()
        fig = qplotData.getFig()

        for w in self.c_qplot_window.winfo_children():
            w.destroy()

		# Display QPlot from QPlot tab
        qplot_frame = tk.Frame(self.c_qplot_window)
        qplot_frame.pack()
        qplot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.c_qplot_window.add(qplot_frame, stretch='always')
        canvas = FigureCanvasTkAgg(fig, qplot_frame)
        toolbar = NavigationToolbar2Tk(canvas, qplot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.summary_frame = tk.Frame(self.c_qplot_window)
        self.summary_frame.pack()
        self.buildSummaryTabs()
        self.buildLabelTable(df)
        self.c_qplot_window.add(self.summary_frame, stretch='always')
        summary_df = df[['name', 'short_name', 'time_s']]
        summary_df = summary_df.sort_values(by='time_s', ascending=False)
        summary_pt = Table(self.summaryTab, dataframe=summary_df, showtoolbar=True, showstatusbar=True)
        summary_pt.show()
        detailed_df = df[['name', 'short_name', 'time_s', 'variant','C_L1', 'C_L2', 'C_L3', \
            'C_RAM', 'C_max', 'memlevel', 'C_op']]
        detailed_df = detailed_df.sort_values(by='time_s', ascending=False)
        detail_pt = Table(self.detailedSummaryTab, dataframe=detailed_df, showtoolbar=True, showstatusbar=True)
        detail_pt.show()

class SIPlotTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

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
        self.mainFrame = MainFrame(self.oneviewTab.oneview_frame)

    def loadDataSource(self, source):
        self.source = source
        print("DATA source to be loaded", source)
        self.loadedData.add_data(source)
        #parse_ip_siplot(tmpfile.name, "test", 'row', "Testing", chosen_node_set, root=self.siPlotTab)

    def buildTabs(self, parent):
        # 1st level notebook with Workload and Codelet tabs
        self.main_note = ttk.Notebook(parent)
        self.workloadTab = WorkLoadTab(self.main_note)
        self.codeletTab = CodeletTab(self.main_note)
        self.oneviewTab = OneviewTab(self.main_note)
        self.main_note.add(self.oneviewTab, text="Oneview")
        self.main_note.add(self.workloadTab, text="Workload")
        self.main_note.add(self.codeletTab, text="Codelet")
        # Workload and Codelet each have their own 2nd level tabs
        workload_note = ttk.Notebook(self.workloadTab)
        codelet_note = ttk.Notebook(self.codeletTab)
        # Codelet tabs
        self.c_trawlTab = TrawlTab(codelet_note)
        self.c_qplotTab = QPlotTab(codelet_note, QPlotData(self.loadedData))
        self.c_siPlotTab = SIPlotTab(codelet_note)
        codelet_note.add(self.c_trawlTab, text="TRAWL")
        codelet_note.add(self.c_qplotTab, text="QPlot")
        codelet_note.add(self.c_siPlotTab, text="SI Plot")
        codelet_note.pack(fill=tk.BOTH, expand=1)
        # Workload tabs
        self.w_trawlTab = TrawlTab(workload_note)
        self.w_qplotTab = QPlotTab(workload_note, None) # None for data for now - to be updated
        self.w_siPlotTab = SIPlotTab(workload_note)
        workload_note.add(self.w_trawlTab, text="TRAWL")
        workload_note.add(self.w_qplotTab, text="QPlot")
        workload_note.add(self.w_siPlotTab, text="SI Plot")
        workload_note.pack(fill=tk.BOTH, expand=True)
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
