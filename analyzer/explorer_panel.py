import tkinter as tk
from tkinter import ttk
import os
from os.path import expanduser
import requests
from lxml import html
import pandas as pd
import re
import pickle
from pathlib import Path
from utils import center
import datetime
from shutil import copyfile

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
        def __init__(self, path, name, container, time_stamp=None):
            super().__init__(name)
            self.container = container
            self.path = path
            self.time_stamp = time_stamp

    class RemoteNode(RemoteTreeNode):
        def __init__(self, url, cape_path, path, name, container, time_stamp=None):
            super().__init__(path, name, container, time_stamp)
            self.cape_path = cape_path
            self.mappings_path = os.path.join(self.cape_path, 'mappings.csv')
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

        def user_selection(self, choice, node=None):
            if self.container.win: self.container.win.destroy()
            if choice == 'Cancel': return 
            elif choice in ['Overwrite', 'Append']: self.get_files()
            url = None
            if self.url.endswith('.xlsx'): url = self.url[:-5]
            elif choice == 'Open Webpage': url = self.url
            self.container.openLocalFile(choice, os.path.dirname(self.path), self.path, url)
        
        def get_files(self):
            #TODO: Look into combining this when opening LocalDir
            if not os.path.isfile(self.path): # Then we need to download the data from the server
                os.makedirs(os.path.dirname(self.path))
                self.download_data()

        def download_data(self):
            print("Downloading Data")
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
                    # Add new mappings data to database
                    if file_name == self.name + '.mapping.csv':
                        pass
                        # new_mappings = pd.read_csv(os.path.join(local_dir, file_name))
                        # all_mappings = pd.read_csv(self.mappings_path)
                        # all_mappings = all_mappings.append(new_mappings).drop_duplicates().reset_index(drop=True)
                        # all_mappings.to_csv(self.mappings_path, index=False)

        def open_directory(self):
            names, link_element = self.directory_file_names(self.page)
            # Show directories and data files (.xlsx or .raw.csv)
            for name in names:
                # Check if there exists a meta directory
                if name == 'meta/': #TODO: Only check this once a user has decided to load a file
                    self.check_meta()
                if (name.endswith('/') or name.endswith('.raw.csv') or name.endswith('.xlsx')) and name not in self.children:
                    self.children.append(name)
                    full_url = self.url + name
                    short_name = name.split('.raw.csv')[0] if name.endswith('.raw.csv') else name.split('.xlsx')[0]
                    if name.endswith('.raw.csv') or name.endswith('.xlsx'): 
                        time_stamp = link_element.xpath('td[position()=3]/text()')[0][:10] + '_' + link_element.xpath('td[position()=3]/text()')[0][11:13] + '-' + link_element.xpath('td[position()=3]/text()')[0][14:16]
                        full_path = os.path.join(self.path, short_name, time_stamp, name)
                    elif name.endswith('/'): full_path = os.path.join(self.path, name[:-1])
                    self.container.insertNode(self, DataSourcePanel.RemoteNode(full_url, self.cape_path, full_path, short_name, self.container))

        def check_meta(self):
            meta_url = self.url + 'meta/'
            meta_page = requests.get(meta_url)
            names, link_element = self.directory_file_names(meta_page)
            # Get local mapping database max timestamp
            all_mappings = pd.read_csv(self.mappings_path)
            before_max = all_mappings['Before Timestamp'].max()
            after_max = all_mappings['After Timestamp'].max()
            max_timestamp = before_max if before_max > after_max else after_max
            # Check each mapping file and add to database if it has a greater timestamp
            for name in names:
                meta_timestamp = int(name.split('.csv')[0].split('-')[-1])
                # if meta_timestamp > max_timestamp:
                if meta_timestamp > -1: #TODO: Use local database max corresponding to root
                    # Temporary download, add to database, delete file
                    file_data = requests.get(meta_url + name)
                    temp_path = os.path.join(self.cape_path, name)
                    open(temp_path, 'wb').write(file_data.content)
                    new_mappings = pd.read_csv(temp_path)
                    all_mappings = pd.read_csv(self.mappings_path)
                    all_mappings = all_mappings.append(new_mappings).drop_duplicates().reset_index(drop=True)
                    all_mappings.to_csv(self.mappings_path, index=False)
                    os.remove(temp_path)

        def directory_file_names(self, page):
            tree = html.fromstring(page.content)
            names = []
            for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                hyperlink = link_element.xpath('td[position()=2]/a')[0]
                names.append(hyperlink.get('href'))
            names = self.remove_webpages(names)
            return names, link_element

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
        def __init__(self, path, name, container, select_fn):
            self.user_selection = select_fn
            super().__init__(path, name, container)

        def open(self):
            print("file node open:", self.name, self.id)
            self.container.show_options(file_type='data', select_fn=self.user_selection)
        

    class LocalDirNode(LocalTreeNode):
        def __init__(self, path, name, container):
            super().__init__(path, name+'/', container)
            self.children = []
            self.url = ''

        def user_selection(self, choice, node=None):
            if self.container.win: self.container.win.destroy()
            if choice == 'Cancel': return 
            if not node: # Then the user has selected a timestamp directory and we find the data file
                for data in os.listdir(self.path):
                    if (data.endswith('.xlsx') and not data.endswith('summary.xlsx')) or data.endswith('.raw.csv'):
                        source_path = os.path.join(self.path, data)
                        break
            else: # The user has selected a noncache data file
                # Check if we need to create cache directory and copy source file
                if not os.path.isfile(node.cache_path):
                    os.makedirs(os.path.dirname(node.cache_path))
                    copyfile(node.path, node.cache_path)
                source_path = node.cache_path
                self.path = os.path.split(source_path)[0]
            # Recreate URL from local directory structure if UVSQ file (.xlsx)
            if source_path.endswith('.xlsx'): self.create_url()
            self.container.openLocalFile(choice, self.path, source_path, self.url if source_path.endswith('.xlsx') else None)
        
        def create_url(self):
            self.url = 'https://datafront.maqao.exascale-computing.eu/public_html/oneview'
            dirs = []
            path, name = os.path.split(os.path.dirname(self.path)) # dir_path is self.path
            while (name != 'UVSQ') and (name != 'UVSQ_2020'):
                dirs.append(name)
                path, name = os.path.split(path)
            dirs.reverse()
            if name == 'UVSQ_2020':
                self.url = 'https://datafront.maqao.exascale-computing.eu/public_html/oneview2020'
            for name in dirs:
                self.url += '/' + name

    def __init__(self, parent, loadDataSrcFn, gui, root):
        ScrolledTreePane.__init__(self, parent)
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.loadDataSrcFn = loadDataSrcFn
        self.gui = gui
        self.root = root
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

    def show_options(self, file_type, select_fn, node=None):
        if file_type == 'html': # OV webpage with no xlsx file
            self.create_dialog_win('Missing Data', 'This file is missing the corresponding data file.\nWould you like to clear any existing plots and\nonly load this webpage?', ['Open Webpage', 'Cancel'], select_fn)
        elif file_type == 'data':
            if len(self.gui.loadedData.sources) >= 2: # Currently can only append max 2 files
                self.create_dialog_win('Max Data', 'You have the max number of data files open.\nWould you like to overwrite with the new data?', ['Overwrite', 'Cancel'], select_fn, node)
            elif len(self.gui.loadedData.sources) >= 1: # User has option to append to existing file
                self.create_dialog_win('Existing Data', 'Would you like to append to the existing\ndata or overwrite with the new data?', ['Append', 'Overwrite', 'Cancel'], select_fn, node)
            if not self.gui.loadedData.sources: # Nothing currently loaded so just load the data with no need to warn the user
                select_fn('Overwrite', node)

    def create_dialog_win(self, title, message, options, select_fn, node=None):
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", lambda option='Cancel' : select_fn(option))
        self.win.title(title)
        tk.Label(self.win, text=message).grid(row=0, columnspan=len(options), padx=15, pady=10)
        for i, option in enumerate(options):
            tk.Button(self.win, text=option, command=lambda choice=option:select_fn(choice, node)).grid(row=1, column=i, pady=10)
        self.root.wait_window(self.win)

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
        self.insertNode(self.localNode, DataSourcePanel.NonCacheLocalDirNode(home_dir, self.cape_path, os.path.join(self.cape_path, 'Home'), 'Home', self) )
        cape_onedrive=os.path.join(home_dir, 'Intel Corporation', 'Cape Project - Documents', 'Cape GUI Data', 'data_source')
        if os.path.isdir(cape_onedrive):
            self.insertNode(self.localNode, DataSourcePanel.NonCacheLocalDirNode(cape_onedrive, self.cape_path, os.path.join(self.cape_path, 'Intel'), 'Intel', self) )
        cape_cache_path= os.path.join(home_dir, 'AppData', 'Roaming', 'Cape')
        if not os.path.isdir(cape_cache_path): Path(cape_cache_path).mkdir(parents=True, exist_ok=True)
        self.insertNode(self.localNode, DataSourcePanel.CacheLocalDirNode(cape_cache_path, 'Previously Visited', self) )

    def setupRemoteRoots(self):
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://datafront.maqao.exascale-computing.eu/public_html/oneview/', 
                                                                    self.cape_path, os.path.join(self.cape_path, 'UVSQ'), 'UVSQ', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://datafront.maqao.exascale-computing.eu/public_html/oneview2020/', 
                                                                    self.cape_path, os.path.join(self.cape_path, 'UVSQ_2020'), 'UVSQ_2020', self))
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode('https://vectorization.computer/data/', 
                                                                    self.cape_path, os.path.join(self.cape_path, 'UIUC'), 'UIUC', self))

    # This tree should handle cache directory
    class CacheLocalDirNode(LocalDirNode):
        def __init__(self, path, name, container):
            super().__init__(path, name, container)

        def open(self):
            print("dir node open:", self.name, self.id)
            if re.match('\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', self.name): # timestamp directory holding several files to be loaded
                self.container.show_options(file_type='data', select_fn=self.user_selection)
            else:
                for d in os.listdir(self.path):
                    if d not in self.children:
                        self.children.append(d)
                        self.fullpath= os.path.join(self.path, d)
                        if os.path.isdir(self.fullpath):
                            self.container.insertNode(self, DataSourcePanel.CacheLocalDirNode(self.fullpath, d, self.container))
                        elif os.path.isfile(self.fullpath) and (self.fullpath.endswith('.raw.csv') or self.fullpath.endswith('.xlsx')):
                            self.container.insertNode(self, DataSourcePanel.LocalFileNode(self.fullpath, d, self.container, self.user_selection))

    # This tree should not visit cache directory
    class NonCacheLocalDirNode(LocalDirNode):
        def __init__(self, path, cape_path, cache_path, name, container):
            super().__init__(path, name, container)
            self.cache_path = cache_path
            self.cape_path = cape_path

        def open(self):
            print("noncached dir node open:", self.name, self.id)
            for d in os.listdir(self.path):
                fullpath = os.path.join(self.path, d)
                if d not in self.children and not os.path.samefile (fullpath, self.cape_path):
                    self.children.append(d)
                    #self.fullpath = fullpath
                    if os.path.isdir(fullpath):
                        self.container.insertNode(self, DataSourcePanel.NonCacheLocalDirNode(fullpath, self.cape_path, 
                                                                                             os.path.join(self.cache_path, d), d, self.container))
                    elif os.path.isfile(fullpath) and (fullpath.endswith('.raw.csv') or fullpath.endswith('.xlsx')):
                        short_name = d.split('.raw.csv')[0] if d.endswith('.raw.csv') else d.split('.xlsx')[0]
                        modified_epoch = os.path.getmtime(fullpath)
                        time_stamp = datetime.datetime.fromtimestamp(modified_epoch).strftime('%Y-%m-%d_%H-%M')
                        cache_path = os.path.join(self.cache_path, short_name, time_stamp, d)
                        self.container.insertNode(self, DataSourcePanel.NonCacheLocalFileNode(fullpath, cache_path, d, self.container, self.user_selection))

    class NonCacheLocalFileNode(LocalTreeNode):
        def __init__(self, path, cache_path, name, container, select_fn):
            self.user_selection = select_fn
            super().__init__(path, name, container)
            self.cache_path = cache_path

        def open(self):
            print("noncache file node open:", self.name, self.id, self.cache_path)
            self.container.show_options(file_type='data', select_fn=self.user_selection, node=self)

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
        def __init__(self, path, name, container, df=pd.DataFrame(), srcDf=pd.DataFrame(), appDf=pd.DataFrame(), \
            mapping=pd.DataFrame(), srcMapping=pd.DataFrame(), appMapping=pd.DataFrame(), \
            analytics=pd.DataFrame(), data={}):
            super().__init__(path, name, container)

        def open(self):
            print("file node open:", self.name, self.id) 

    class LocalDirNode(LocalTreeNode):
        def __init__(self, path, name, container):
            super().__init__(path, name+'/', container)
            self.children = []
            self.analysis_result = False
            self.df = pd.DataFrame()
            self.srcDf = pd.DataFrame()
            self.appDf = pd.DataFrame()
            self.mapping = pd.DataFrame()
            self.srcMapping = pd.DataFrame()
            self.appMapping = pd.DataFrame()
            self.analytics = pd.DataFrame()
            self.data = {}

        def open(self):
            print("dir node open:", self.name, self.id) 
            for d in os.listdir(self.path):
                if d not in self.children:
                    self.children.append(d)
                    fullpath = os.path.join(self.path, d)
                    # Just display directory names 
                    if os.path.isdir(fullpath):
                        self.analysis_result = False
                        self.container.insertNode(self, AnalysisResultsPanel.LocalDirNode(fullpath, d, self.container))
                    # Load analysis results directory
                    else:
                        self.analysis_result = True
                        if d == 'summary.xlsx': self.df = pd.read_excel(os.path.join(self.path, d))
                        if d == 'srcSummary.xlsx': self.srcDf = pd.read_excel(os.path.join(self.path, d))
                        if d == 'appSummary.xlsx': self.appDf = pd.read_excel(os.path.join(self.path, d))
                        if d == 'mapping.xlsx': self.mapping = pd.read_excel(os.path.join(self.path, d))
                        if d == 'srcMapping.xlsx': self.srcMapping = pd.read_excel(os.path.join(self.path, d))
                        if d == 'appMapping.xlsx': self.appMapping = pd.read_excel(os.path.join(self.path, d))
                        if d == 'data.pkl': 
                            data_file = open(os.path.join(self.path, d), 'rb')
                            self.data = pickle.load(data_file)
                            data_file.close()

            if self.analysis_result:
                codelet = {'summary':self.df, 'mapping':self.mapping, 'data':self.data['Codelet']}
                source = {'summary':self.srcDf, 'mapping':self.srcMapping, 'data':self.data['Source']}
                app = {'summary':self.appDf, 'mapping':self.appMapping, 'data':self.data['Application']}
                self.levels = [codelet, source, app]
                self.container.openLocalFile(self.levels)

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

    def openLocalFile(self, levels=[]):
        self.loadSavedStateFn(levels)

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
    def __init__(self, parent, loadDataSrcFn, loadSavedStateFn, gui, root):
        tk.PanedWindow.__init__(self, parent, orient="horizontal")
        top = DataSourcePanel(self, loadDataSrcFn, gui, root)
        top.pack(side = tk.LEFT, expand=True)
        bot = AnalysisResultsPanel(self, loadSavedStateFn)
        bot.pack(side = tk.LEFT, expand=True)
        self.add(top, stretch='always')
        self.add(bot, stretch='always')
        self.pack(fill=tk.BOTH,expand=True)
        self.configure(sashrelief=tk.RAISED)