import os
import pickle
from metric_names import MetricName as MN
from metric_names import NonMetricName, KEY_METRICS, CATEGORIZED_METRICS, PLOT_METRICS
globals().update(MN.__members__)

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

        
    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't save gui as they are GUI components
        if 'gui' in state:
            del state['gui']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore observers to []
        self.gui = []

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
    def change_level_tab(self, name):
        self.gui.change_level_tab(name)

    def change_current_level_plot_tab(self, name):
        self.gui.change_current_level_plot_tab(name)
        #self.gui.codeletTab.plot_note.select(idx)

    def maximizeOneview(self):
        self.gui.maximizeOneview()

    def minimizeOneview(self):
        self.gui.minimizeOneview()

    def load_url(self, url):
        self.gui.oneviewTab.set_url(url)
        self.gui.oneviewTab.load_url()

    def remove_points(self, operator, metric, threshold, level):
        df = self.loadedData.levelData[level].df
        # TODO: Only enable the state diagram once data is loaded so this doesn't error on an empty df
        df = df.loc[operator(df[metric].astype(str), str(threshold))]
        names = (df[NAME] + df[TIMESTAMP].astype(str)).tolist()
        self.loadedData.levelData[level].guiState.removePoints(names)

    # Following few functions applies to current tab (level and plot)
    def set_plot_scale(self, x_scale, y_scale):
        #scale = x_scale + y_scale
        self.gui.set_plot_scale(x_scale, y_scale)

    def set_plot_axes(self, x_scale, y_scale, x_axis, y_axis):
        self.gui.set_plot_axes(x_scale, y_scale, x_axis, y_axis)

    def set_labels(self, metrics):
        self.gui.set_labels(metrics)
        #self.loadedData.levelData[level].guiState.setLabels(metrics)


    #TODO: Possibly unhighlight any other highlighted points or show all points to begin with
    # def A_filter(self, relate, metric, threshold, level):
    #     df = self.gui.loadedData.summaryDf
    #     names = []
    #     if metric and metric in df.columns.tolist(): names = [name + timestamp for name,timestamp in zip(df.loc[relate(df[metric], threshold)][NAME], df.loc[relate(df[metric], threshold)][TIMESTAMP].astype(str))]
    #     names.extend(points)
    #     if getNames: return names
    #     for name in names:
    #         try: 
    #             marker = self.plotData.name_marker[name]
    #             if highlight and marker.get_marker() == 'o': self.highlightPoint(marker)
    #             elif not highlight and marker.get_marker() == '*': self.highlightPoint(marker)
    #             if remove: self.togglePoint(marker, visible=False)
    #             elif show: self.togglePoint(marker, visible=True)
    #         except: pass
    #     self.drawPlots()
    #     return names
