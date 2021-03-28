import os
import pickle

class AnalyzerController:
    '''Control part of Analyzer.  It knows about GUI (View) and LoadedData (Model) 
        but do not deal with their details.
        It coordiantes between them.
        E.g. it can say "Look at a certain tab and hightlight specifici data points".
        It should set the Model and the notify methods will update GUI automatically.'''
    def __init__(self, gui, loadedData):
        self.gui = gui
        self.setLoadedData(loadedData)
        self.gui.setControl(self)

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
        self.loadedData.loadFile(choice, data_dir, source, url)