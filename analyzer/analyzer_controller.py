import os
import pickle

class AnalyzerController:
    '''Control part of Analyzer.  It knows about GUI (View) and LoadedData (Model) 
        but do not deal with their details.
        It coordiantes between them.
        E.g. it can say "Look at a certain tab and hightlight specific data points".
        It should set the Model and the notify methods will update GUI automatically.'''
    def __init__(self, gui, loadedData):
        self.gui = gui
        self.setLoadedData(loadedData)
        self.gui.setControl(self)

    # NOTE: This will also be the starting point of setting up the notification mechanism
    def setLoadedData(self, loadedData):
        self.loadedData = loadedData
        self.gui.setLoadedData(self.loadedData)
        
    def loadState(self, input_path):
        with open(os.path.join(input_path, 'loadedData.pkl'), 'rb') as input_file:
            self.setLoadedData(pickle.load(input_file))
            self.loadedData.updated_notify_observers()
            self.loadedData.updated_all_levels_notify_observers()

    def saveState(self, output_path):
        with open(os.path.join(output_path, 'loadedData.pkl'), 'wb') as data_file:
            pickle.dump(self.loadedData, data_file)

    def exportShownDataRawCSV(self, out_path):
        self.loadedData.exportShownDataRawCSV(out_path)

    def loadFile(self, choice, data_dir, source, url):
        if choice == 'Overwrite':
            self.gui.resetTabValues() 
        self.gui.loadUrl(choice, url)
        self.wait_for_work('File loading', lambda: self.loadedData.loadFile(choice, data_dir, source, url))
        #self.loadedData.loadFile(choice, data_dir, source, url)

    # Try to run long running work and cause GUI to tell user to wait
    # This call will cause GUI not accepting user inputs
    # work_function will be invoked as work_function()
    def wait_for_work(self, work_name, work_function):
        self.gui.wait_for_work(work_name, work_function)
        
    # Try to run long running work and cause GUI to tell user work is being done
    # This call will let GUI continue accept user inputs
    # work_function will be invoked as work_function()
    def display_work(self, work_name, work_function):
        self.gui.display_work(work_name, work_function)

    # Auto-change to specific tab
    def change_codelet_tab(self, name):
        self.gui.codeletTab.change_tab(name)
        #self.gui.codeletTab.plot_note.select(idx)
    def maximizeOneview(self):
        self.gui.maximizeOneview()

    def minimizeOneview(self):
        self.gui.minimizeOneview()

    def load_url(self, url):
        self.gui.oneviewTab.set_url(url)
        self.gui.oneviewTab.load_url()
