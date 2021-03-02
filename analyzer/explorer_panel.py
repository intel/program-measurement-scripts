# magic for mime type finding for a file
# need to run pip install python-magic-bin (not python-magic)
import magic
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
from abc import ABC, abstractmethod

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
    class DataSource(ABC):
        # Download data file (.raw.csv or .xlsx) at data_url and associated meta files to local_dir
        # TODO: just use data_filename to name meta files to avoid looping data files
        def download_data_and_meta(self, data_url, local_dir):
            dir_url = os.path.dirname(data_url) + '/'
            #dir_url = url_parts[0] + '/' # Get the data directory to download any corresponding files
            #data_filename = url_parts[1]
            data_filename = os.path.basename(data_url)
            short_name = re.sub(r'\.xlsx$|\.raw\.csv$', '', data_filename)
            meta_exts =  ['.mapping.csv', '.analytics.csv', '.names.csv']
            meta_files = [short_name + ext for ext in meta_exts]

            self.get_file(data_url, os.path.join(local_dir, data_filename))
            file_names, timestamps = self.directory_file_names_timestamps(dir_url)
            for file_name in file_names:
                if file_name in meta_files:
                    self.get_file(dir_url + file_name, os.path.join(local_dir, file_name))

        @abstractmethod
        def directory_file_names_timestamps(self, url):
            pass

        @abstractmethod
        def get_file(self, src, dst): 
            pass

        @abstractmethod
        def isdir(self, fullurl): 
            return False

        def isfile(self, fullurl):
            return not self.isdir(fullurl)

        @abstractmethod
        def isValidURL(self, fullurl): 
            return False
        

    class WebServer(DataSource):
        def getContentType (self, url):
            self.page = requests.get(url)
            return self.page.headers['content-type']

        def isValidURL(self, fullurl): 
            try:
                if requests.get(fullurl).status_code == 200:
                    return True
            except:
                pass
            return False

        def directory_file_names(self, url):
            page = requests.get(url)
            tree = html.fromstring(page.content)
            names = []
            link_elements = []
            for link_element in tree.xpath('//tr[position()>3 and position()<last()]'):
                hyperlink = link_element.xpath('td[position()=2]/a')[0]
                names.append(hyperlink.get('href'))
                link_elements.append(link_element)
            names = self.remove_webpages(names)
            return names, link_elements

        def directory_file_names_timestamps(self, url):
            names, link_elements = self.directory_file_names(url)
            raw_timestamps = [link_element.xpath('td[position()=3]/text()')[0] for link_element in link_elements]
            timestamps = [raw_ts[:10] + '_' + raw_ts[11:13] + '-' + raw_ts[14:16] for raw_ts in raw_timestamps]
            return names, timestamps

        def remove_webpages(self, names):
            data_files = [i.split('.xlsx')[0]+'/' for i in names if i.endswith('.xlsx')]
            return [i for i in names if i not in data_files]

        def get_file(self, src, dst): 
            file_data = requests.get(src) 
            open(dst, 'wb').write(file_data.content)

        def isdir(self, fullurl): 
            return fullurl.endswith('/')

            
    class FileSystem(DataSource):
        def getContentType (self, path):
            return magic.from_file(path, mime=True)

        def isValidURL(self, fullurl): 
            return os.path.isfile(os.path.join(fullurl, 'index.html'))
        
        def directory_file_names_timestamps(self, cur_dir):
            names = os.listdir(cur_dir)
            fullnames=[os.path.join(cur_dir, n) for n in names]
            modified_epochs = [os.path.getmtime(fn) for fn in fullnames]
            time_stamps = [datetime.datetime.fromtimestamp(epoch).strftime('%Y-%m-%d_%H-%M') for epoch in modified_epochs]
            return names, time_stamps

        def isdir(self, fullpath): 
            return os.path.isdir(fullpath)

        def isfile(self, fullpath):
            return os.path.isfile(fullpath)

        def get_file(self, src, dst): 
            copyfile(src, dst)
            
    
    class DataTreeNode:
        nextId = 0
        nodeDict = {}
        def __init__(self, name, parent):
            self.name = name
            self.parent = parent
            self.id = DataSourcePanel.DataTreeNode.nextId
            self.children = []
            if parent: parent.children.append(self)
            DataSourcePanel.DataTreeNode.nextId += 1
            DataSourcePanel.DataTreeNode.nodeDict[self.id]=self

        @classmethod
        def lookupNode(cls, id):
            return cls.nodeDict[id]

        def open(self):
            print("node open:", self.name, self.id) 

    class MetaTreeNode(DataTreeNode):
        def __init__(self, name, parent):
            super().__init__(name, parent)

    class RealTreeNode(DataTreeNode):
        def __init__(self, name, parent, virtual_path, real_path, container, data_source):
            super().__init__(name, parent)
            self.virtual_path = virtual_path
            self.real_path = real_path
            self.container = container
            self.data_src = data_source

        def get_root_virtual_path(self):
            if (isinstance(self.parent, DataSourcePanel.RealTreeNode)):
                # If parent is also real node, get root url there
                return self.parent.get_root_virtual_path()
            else:
                # If parent is not real node, the url of this node is the root
                return self.virtual_path
        
    class InternalNode(RealTreeNode):
        def __init__(self, virtual_path, real_path, name, container, parent, 
                     data_source, terminalNodeClass):
            super().__init__(name, parent, virtual_path, real_path, container, data_source)
            # These class objects are used to create object of internal and terminal nodes
            self.terminalNodeClass = terminalNodeClass
            self.internalNodeClass = type(self)

        # Whether to skip next potential child with name
        def skip(self, name):
            #return False
            # Skip meta path
            return os.path.join(self.virtual_path, name) == os.path.join(self.get_root_virtual_path(), "meta")


        # Return names and time_stamps of potential children nodes to visit
        def get_children_names_timestamps(self):
            return self.data_src.directory_file_names_timestamps(self.virtual_path)
            
        # Create an internal node to be added if name tells us this is internal
        def makeInternalNodeOrNone(self, name, time_stamp):
            full_virtual_path = os.path.join(self.virtual_path,  name)
            if self.data_src.isdir(full_virtual_path): 
                full_real_path = re.sub('/$','', os.path.join(self.real_path, name))
                # Use self.internalNodeClass rather than explict class name so this handles subclassing automatically
                return self.internalNodeClass(full_virtual_path, full_real_path, name, self.container, self)
            return None

        # Create an terminal node to be added if name tells us this is terminal
        def makeTerminalNodeOrNone(self, name, time_stamp):
            full_virtual_path = os.path.join(self.virtual_path,  name)
            if self.data_src.isfile(full_virtual_path) and full_virtual_path.endswith(('.raw.csv', '.xlsx')): 
                full_real_path = os.path.join(self.real_path, name, time_stamp, name)
                # Use self.terminalNodeClass rather than explict class name so this handles subclassing automatically
                return self.terminalNodeClass(full_virtual_path, full_real_path, name, self.container, self)
            return None

            

        def open(self):
            print("internal node open:", self.name, self.id) 
            # Directory node
            names, time_stamps = self.get_children_names_timestamps()
            # Show directories and data files (.xlsx or .raw.csv)
            # Iterate internal nodes following revserse order of timestamps
            for time_stamp, name in sorted(zip(time_stamps, names), reverse=True):
                if name in [child.name for child in self.children]:
                    continue  # Skip if already added

                if self.skip(name):
                    continue

                node = self.makeInternalNodeOrNone(name, time_stamp)
                node = node if node else self.makeTerminalNodeOrNone(name, time_stamp)
                if node: self.container.insertNode(self, node)

            
    class TerminalNode(RealTreeNode):
        def __init__(self, virtual_path, real_path, name, container, parent, data_source):
            super().__init__(name, parent, virtual_path, real_path, container, data_source)

        def open(self):
            print("terminal node open:", self.name, self.id, self.real_path)
            self.container.show_options_data(select_fn=self.user_selection, node=self)

        # Normally the real path points to the file to load
        def file_to_load(self):
            return self.real_path

        # def user_selection(self, choice, node):
        #     if self.container.win: self.container.win.destroy()
        #     if choice == 'Cancel': return 

        #     file_to_load = self.file_to_load()
        #     if choice in ['Overwrite', 'Append']: self.get_files(file_to_load)

        #     url = re.sub(r'\.xlsx$|\.raw\.csv$', '', self.virtual_path)
        #     self.container.openLocalFile(choice, os.path.dirname(file_to_load), file_to_load, url)

        def user_selection(self, choice, node=None):
            if self.container.win: self.container.win.destroy()
            if choice == 'Cancel': return 

            file_to_load = self.file_to_load()
            if choice in ['Overwrite', 'Append']: self.get_files(file_to_load)

            #if self.virtual_path.endswith(('.xlsx', 'raw.csv')): url = self.virtual_path[:-5]
            url = re.sub(r'\.xlsx$|\.raw\.csv$', '', self.virtual_path)
            # Set url to None if it does not give a valid webpage
            url = url if self.data_src.isValidURL(url) else None
            self.container.openLocalFile(choice, os.path.dirname(file_to_load), file_to_load, url)


        def get_files(self, file_to_load):
            if not os.path.isfile(file_to_load):
                real_dir = os.path.dirname(file_to_load)
                Path(real_dir).mkdir(parents=True, exist_ok=True)
                print("Downloading Data")
                self.check_meta()
                self.data_src.download_data_and_meta(self.virtual_path, real_dir)

        def check_meta(self):
            root_url = self.get_root_virtual_path()
            meta_url = os.path.join(root_url, 'meta/')
            names, timestamps = self.data_src.directory_file_names_timestamps(os.path.join(root_url, 'meta/'))

            # Get local mapping database max timestamp
            mappings_path = os.path.join(self.container.cape_path, 'mappings.csv')
            all_mappings = pd.read_csv(mappings_path)
            if not 'DataSource' in all_mappings.columns:
                all_mappings['DataSource'] =''
            mask=all_mappings['DataSource']==root_url
            before_max = all_mappings[mask]['Before Timestamp'].max()
            #before_max = all_mappings['Before Timestamp'].max()
            after_max = all_mappings[mask]['After Timestamp'].max()
            #after_max = all_mappings['After Timestamp'].max()
            max_timestamp = before_max if before_max > after_max else after_max
            # Convert nan to -1
            max_timestamp = -1 if pd.isna(max_timestamp) else max_timestamp
            # Check each mapping file and add to database if it has a greater timestamp
            updated = False
            for name in names:
                meta_timestamp = int(name.split('.csv')[0].split('-')[-1])
                # if meta_timestamp > max_timestamp:
                if meta_timestamp > max_timestamp: 
                    # Temporary download, add to database, delete file
                    temp_path = os.path.join(self.container.cape_path, name)
                    self.data_src.get_file(os.path.join(meta_url, name), temp_path)
                    new_mappings = pd.read_csv(temp_path)
                    new_mappings['DataSource']=root_url
                    all_mappings = all_mappings.append(new_mappings).drop_duplicates().reset_index(drop=True)
                    updated = True
                    os.remove(temp_path)
            if updated: all_mappings.to_csv(mappings_path, index=False)


    class RemoteNode(InternalNode):
        def __init__(self, virtual_path, real_path, name, container, parent):
            super().__init__(virtual_path, real_path, name, container, parent, 
                             DataSourcePanel.WebServer(), DataSourcePanel.RemoteDataNode)

        def user_selection(self, choice, node=None):
            if self.container.win: self.container.win.destroy()
            if choice != 'Open Webpage': return 
            # The only choice is to load HTML
            url = self.virtual_path
            # Set url to None if it does not give a valid webpage
            url = None if requests.get(url).status_code != 200 else url
            # choice is 'Open Webpage'
            self.container.openLocalFile(choice, None, None, url)

        # Return names and time_stamps of potential children nodes to visit
        def get_children_names_timestamps(self):
            try:
                names, time_stamps = super().get_children_names_timestamps()
            except:
                # Cannot be browsed as directotry tree.  Consider this HTML content
                self.container.show_options_html(select_fn=self.user_selection)
                names = []
                time_stamps = []
            return names, time_stamps


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

    # This tree should handle cache directory.  The only things to browse are directories.
    # Data will only be loaded under timestamp directories.
    # For cache local directory, virtual_path refers to original path and real_path refers to the cache path
    # - same as other nodes
    class CacheLocalDirNode(InternalNode):
        def __init__(self, virtual_path, real_path, name, container, parent):
            super().__init__(virtual_path, real_path, name, container, parent, 
                             DataSourcePanel.FileSystem(), DataSourcePanel.CacheTimestampDirNode) 
        # Whether to skip next potential child with name
        # Don't skip any directories under cache local directory
        def skip(self, name):
            return False

        # Return names and time_stamps of potential children nodes to visit
        # Override to use real_path
        def get_children_names_timestamps(self):
            return self.data_src.directory_file_names_timestamps(self.real_path)

        # Create an internal node to be added if name tells us this is internal
        def makeInternalNodeOrNone(self, name, time_stamp):
            full_real_path = os.path.join(self.real_path, name)
            if self.data_src.isdir(full_real_path) and not re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', name):
                return self.internalNodeClass(self.virtual_path+'/'+name, full_real_path, name, self.container, self)
            return None

        # Create an terminal node to be added if name tells us this is terminal
        def makeTerminalNodeOrNone(self, name, time_stamp):
            full_real_path = os.path.join(self.real_path, name)
            if self.data_src.isdir(full_real_path) and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}', name): # timestamp directory holding several files to be loaded 
                return self.terminalNodeClass(self.virtual_path, full_real_path, name, self.container, self)
            return None

    # This tree should not visit cache directory
    class NonCacheLocalDirNode(InternalNode):
        def __init__(self, virtual_path, real_path, name, container, parent):
            super().__init__(virtual_path, real_path, name, container, parent, 
                             DataSourcePanel.FileSystem(), DataSourcePanel.NonCacheLocalFileNode)

        # will skip the cape folder
        def skip(self, name):
            full_virtual_path = os.path.join(self.virtual_path,  name)
            return super().skip(name) or os.path.samefile (full_virtual_path, self.container.cape_path)

        # def open(self):
        #     print("noncached dir node open:", self.name, self.id)
        #     names, time_stamps = self.data_src.directory_file_names_timestamps(self.virtual_path)
        #     for d, time_stamp in zip(names, time_stamps):
        #         if d in [child.name for child in self.children]:
        #             continue  # Skip if already added

        #         full_virtual_path = os.path.join(self.virtual_path, d)
        #         if self.skip(full_virtual_path):
        #             continue

        #             #self.fullpath = fullpath
        #         if self.data_src.isdir(full_virtual_path):
        #             real_path = os.path.join(self.real_path, d) 
        #             real_path = re.sub('/$','', real_path)
        #             self.container.insertNode(self, DataSourcePanel.NonCacheLocalDirNode(full_virtual_path, real_path, d, self.container, self))
        #         elif self.data_src.isfile(full_virtual_path) and full_virtual_path.endswith(('.raw.csv', '.xlsx')):
        #             real_path = os.path.join(self.real_path, d, time_stamp, d)
        #             self.container.insertNode(self, DataSourcePanel.NonCacheLocalFileNode(full_virtual_path, real_path, d, self.container, self))

    # Terminal node of the tree supposed to be for loading data and no more expansions

    class CacheTimestampDirNode(TerminalNode):
        def __init__(self, virtual_path, real_path, name, container, parent):
            super().__init__(virtual_path, real_path, name, container, 
                             parent, DataSourcePanel.FileSystem())

        # For timestamp directory, the file to load is the data file contained
        # in this directory.
        def file_to_load(self):
            data_file_name = os.path.basename(os.path.dirname(self.real_path))
            return os.path.join(self.real_path, data_file_name)

        def get_files(self, file_to_load):
            pass  # Nothing to do when browsing cached directory
            
    class NonCacheLocalFileNode(TerminalNode):
        def __init__(self, virtual_path, real_path, name, container, parent):
            super().__init__(virtual_path, real_path, name, container, 
                             parent, DataSourcePanel.FileSystem())

    class RemoteDataNode(TerminalNode):
        def __init__(self, virtual_path, real_path, name, container, parent):
            super().__init__(virtual_path, real_path, name, container, 
                             parent, DataSourcePanel.WebServer())


    def __init__(self, parent, loadDataSrcFn, gui, root):
        ScrolledTreePane.__init__(self, parent)
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.loadDataSrcFn = loadDataSrcFn
        self.gui = gui
        self.root = root
        self.dataSrcNode = DataSourcePanel.MetaTreeNode('Data Source', None)
        self.localNode = DataSourcePanel.MetaTreeNode('Local', self.dataSrcNode)
        self.remoteNode = DataSourcePanel.MetaTreeNode('Remote', self.dataSrcNode)
        self.oneDriveNode = DataSourcePanel.MetaTreeNode('OneDrive', self.dataSrcNode)
        self.insertNode(None, self.dataSrcNode)
        self.insertNode(self.dataSrcNode, self.localNode)
        self.insertNode(self.dataSrcNode, self.remoteNode)
        self.insertNode(self.dataSrcNode, self.oneDriveNode)
        self.opening = False
        self.firstOpen = True
        self.win = None
        self.setupLocalRoots()
        self.setupRemoteRoots()
        self.treeview.bind("<<TreeviewOpen>>", self.handleOpenEvent)

    def show_options_data(self, select_fn, node=None):
        if len(self.gui.loadedData.sources) >= 2: # Currently can only append max 2 files
            self.create_dialog_win('Max Data', 'You have the max number of data files open.\nWould you like to overwrite with the new data?', ['Overwrite', 'Cancel'], select_fn, node)
        elif len(self.gui.loadedData.sources) >= 1: # User has option to append to existing file
            self.create_dialog_win('Existing Data', 'Would you like to append to the existing\ndata or overwrite with the new data?', ['Append', 'Overwrite', 'Cancel'], select_fn, node)
        if not self.gui.loadedData.sources: # Nothing currently loaded so just load the data with no need to warn the user
            select_fn('Overwrite', node)

    def show_options_html(self, select_fn):
        # OV webpage with no xlsx file
        self.create_dialog_win('Missing Data', 'This file is missing the corresponding data file.\nWould you like to clear any existing plots and\nonly load this webpage?', ['Open Webpage', 'Cancel'], select_fn)

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

    def setupLocalRoot(self, nonCachePath, name, localMetaNode):
        if not os.path.isdir(nonCachePath):
            return
        self.insertNode(localMetaNode, DataSourcePanel.NonCacheLocalDirNode(nonCachePath, os.path.join(self.cacheRoot.real_path, name), name, self, localMetaNode) )
        cache_path = os.path.join(self.cacheRoot.real_path, name)
        Path(cache_path).mkdir(parents=True, exist_ok=True)
        self.insertNode(self.cacheRoot, DataSourcePanel.CacheLocalDirNode(nonCachePath, cache_path, name, self, self.cacheRoot))

    # This includes OneDrive sync roots
    def setupLocalRoots(self):
        home_dir=expanduser("~")
        cape_cache_path = os.path.join(home_dir, 'AppData', 'Roaming', 'Cape')
        cache_root_path = os.path.join(cape_cache_path,'Previously Visited')
        if not os.path.isdir(cache_root_path): Path(cache_root_path).mkdir(parents=True, exist_ok=True)
        self.cacheRoot = DataSourcePanel.CacheLocalDirNode(None, cache_root_path , 'Previously Visited', self, self.localNode) 
        self.insertNode(self.localNode, self.cacheRoot)
        
        self.setupLocalRoot(home_dir, 'Home', self.localNode)
        #self.insertNode(self.localNode, DataSourcePanel.NonCacheLocalDirNode(home_dir, self.cape_path, os.path.join(self.cape_path, 'Home'), 'Home', self) )

        cape_onedrive=os.path.join(home_dir, 'Intel Corporation', 'Cape Project - Documents', 'Cape GUI Data', 'data_source')
        cape_onedrive_ext=os.path.join(home_dir, 'Intel Corporation', 'QProf - Shared Documents', 'Cape GUI Data', 'data_source')
        self.setupLocalRoot(cape_onedrive, 'Intel (Internal)', self.oneDriveNode)
        self.setupLocalRoot(cape_onedrive_ext, 'Intel (External)', self.oneDriveNode)
        #self.insertNode(self.localNode, DataSourcePanel.NonCacheLocalDirNode(cape_onedrive, self.cape_path, os.path.join(self.cape_path, 'Intel'), 'Intel', self) )


    def setupRemoteRoot(self, url, name):
        cache_path = os.path.join(self.cacheRoot.real_path, name)
        self.insertNode(self.remoteNode, DataSourcePanel.RemoteNode(url, cache_path, name, self, self.remoteNode))
        Path(cache_path).mkdir(parents=True, exist_ok=True)
        cacheNode = DataSourcePanel.CacheLocalDirNode(url, cache_path, name, self, self.cacheRoot)
        self.insertNode(self.cacheRoot, cacheNode)

    def setupRemoteRoots(self):
        self.setupRemoteRoot('https://vectorization.computer/data/', 'UIUC')
        self.setupRemoteRoot('https://datafront.maqao.exascale-computing.eu/public_html/oneview/', 'UVSQ')
        self.setupRemoteRoot('https://datafront.maqao.exascale-computing.eu/public_html/oneview2020/', 'UVSQ_2020')


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
            self.data_src = DataSourcePanel.FileSystem()

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