import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from argparse import ArgumentParser
#from idlelib.TreeWidget import ScrolledCanvas, FileTreeItem, TreeNode
import pathlib
import os
from os.path import expanduser
from summarize import summary_report
from generate_QPlot import parse_ip as parse_ip_qplot
from generate_SI import parse_ip as parse_ip_siplot
import tempfile
import pkg_resources.py2_warn

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
        def __init__(self, name):
            super().__init__(name)

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
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteTreeNode('uvsq'))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteTreeNode('uiuc'))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteTreeNode('uta'))

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

class ApplicationTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class OneviewTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)        
        # May want to explore solution to embed Chrome in GUI
        # https://stackoverflow.com/questions/46571448/tkinter-and-a-html-file

class TrawlTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class QPlotTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class SIPlotTab(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

class AnalyzerGui(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

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

    def loadDataSource(self, source):
        print("DATA source to be loaded", source)
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
        summary_report(in_files, tmpfile.name, in_file_format, user_op_file, request_no_cqa, \
            request_use_cpi, request_skip_energy, request_skip_stalls, request_succinct, None)
        chosen_node_set = set(['L1','L2','L3','RAM','FLOP'])
        parse_ip_qplot(tmpfile.name, "test", "scalar", "Testing", chosen_node_set, False, gui=True, analyzer_gui=self)
        #parse_ip_siplot(tmpfile.name, "test", 'row', "Testing", chosen_node_set, root=self.siPlotTab)

    def buildTabs(self, parent):
        # 1st level notebook with Workload and Codelet tabs
        main_note = ttk.Notebook(parent)
        self.workloadTab = WorkLoadTab(main_note)
        self.codeletTab = CodeletTab(main_note)
        self.oneviewTab = OneviewTab(main_note)
        main_note.add(self.workloadTab, text="Workload")
        main_note.add(self.codeletTab, text="Codelet")
        main_note.add(self.oneviewTab, text="Oneview")
        # Workload and Codelet each have their own 2nd level tabs
        workload_note = ttk.Notebook(self.workloadTab)
        codelet_note = ttk.Notebook(self.codeletTab)
        # Codelet tabs
        self.c_summaryTab = SummaryTab(codelet_note)
        self.c_trawlTab = TrawlTab(codelet_note)
        self.c_qplotTab = QPlotTab(codelet_note)
        self.c_siPlotTab = SIPlotTab(codelet_note)
        codelet_note.add(self.c_trawlTab, text="TRAWL")
        codelet_note.add(self.c_qplotTab, text="QPlot")
        codelet_note.add(self.c_siPlotTab, text="SI Plot")
        codelet_note.pack(fill=tk.BOTH, expand=1)
        # QPlot tab has paned window with summary table and qplot
        self.c_qplot_window = tk.PanedWindow(self.c_qplotTab, orient=tk.VERTICAL, sashrelief=tk.RIDGE, sashwidth=6,
                                                sashpad=3)
        self.c_qplot_window.pack(fill=tk.BOTH,expand=True)
        # Workload tabs
        self.w_summaryTab = SummaryTab(workload_note)
        self.w_trawlTab = TrawlTab(workload_note)
        self.w_qplotTab = QPlotTab(workload_note)
        self.w_siPlotTab = SIPlotTab(workload_note)
        workload_note.add(self.w_trawlTab, text="TRAWL")
        workload_note.add(self.w_qplotTab, text="QPlot")
        workload_note.add(self.w_siPlotTab, text="SI Plot")
        workload_note.pack(fill=tk.BOTH, expand=True)
        return main_note


def on_closing(root):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.quit()
        root.destroy()

if __name__ == '__main__':
    parser = ArgumentParser(description='Cape Analyzer')
    root = tk.Tk()
    root.title("Cape Analyzer")
    # Set opening window to half user's screen wxh
    width  = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry('%sx%s' % (int(width/1.2), int(height/1.2)))
    #root.geometry(f'{width}x{height}')

    gui = AnalyzerGui(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()
