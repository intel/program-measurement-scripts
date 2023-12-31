import copy
import os
import tkinter as tk
from os.path import expanduser
from tkinter import ttk

import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from metric_names import (ALL_METRICS, CATEGORIZED_METRICS, KEY_METRICS,
                          PLOT_METRICS)
from metric_names import MetricName as MN

from analyzer_model import AnalyzerData
from plot_interaction import PlotInteraction
from utils import Observable, exportCSV, exportXlsx

# Frame that can be hidden and pause associated PasuableObserable object(s)
class HideableTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
    
    # Subclass should override to provide an PausableObservable object this cares about
    def getPausables(self):
        return []

    # This method is called on hiding of this tab
    def hide(self):
        for pausable in self.getPausables():
            pausable.pause()

    # This method is called on exposing of this tab
    def expose(self):
        for pausable in self.getPausables():
            pausable.resume()
    

# globals().update(MetricName.__members__)
class GuiBaseTab(HideableTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.analyzerData = None

    def setAnalyzerData(self, analyzerData):
        assert (analyzerData is not None)
        self.analyzerData = analyzerData
        self.setupAnalyzerData(analyzerData)
        #analyzerData.add_observer(self)

    def setupAnalyzerData(self, analyzerData):
        pass

    def getPausables(self):
        return [self.analyzerData] if self.analyzerData else []

    @property
    def level(self):
        return self.analyzerData.level
        
    @property
    def mappings(self):
        return self.analyzerData.mappings
        
    @property
    def levelData(self):
        return self.analyzerData.levelData

    @property
    def guiState(self):
        return self.levelData.guiState


class AnalyzerTab(GuiBaseTab):
    def __init__(self, parent, analyzerDataClass):
        super().__init__(parent)
        self.analyzerDataClass = analyzerDataClass

    # Do nothing.  Sublcass override to set up notify()
    def setupGuiState(self, guiState):
        pass

    def setupLevelData(self, levelData):
        # GUI tabs listen to levelData
        levelData.add_observer(self)

    def setLevelData(self, levelData):
        self.setAnalyzerData(levelData.guiState.findOrCreateGuiData(self.analyzerDataClass))
        self.setupGuiState(self.guiState)
        self.setupLevelData(self.levelData)
        
    # def setAnalyzerData(self, analyzerData):
    #     super().setAnalyzerData(analyzerData)
    #     #self.level = analyzerData.level
    #     #self.name = analyzerData.name
    #     #self.mappings_path = self.data.loadedData.mappings_path
    #     #self.short_names_path = self.data.short_names_path
    #     return self

class PlotAnalyzerData(AnalyzerData):
    def __init__(self, loadedData, level, name, x_axis, y_axis):
        super().__init__(loadedData, level, name)
        self.scale = "linear"
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.x_scale = 'linear'
        self.y_scale = 'linear'

    def update_axes(self, x_scale, y_scale, x_axis, y_axis, update=True):
        self.update_scale(x_scale, y_scale, update=False)
        if y_axis: self.y_axis = "{}".format(y_axis)
        if x_axis: self.x_axis = "{}".format(x_axis)
        if update: self.updated_notify_observers()

    def update_scale(self, x_scale, y_scale, update=True):
        if x_scale: self.x_scale = x_scale
        if y_scale: self.y_scale = y_scale
        self.scale = self.x_scale + self.y_scale
        if update: self.updated_notify_observers()
    
class PlotTab(AnalyzerTab):
    class PlotUpdater:
        def __init__(self, plotTab):
            self.plotTab = plotTab

        def notify(self, data):
            self.plotTab.try_adjust_plot()
    
    # NOTE: some parameter notes: parent is the GUI level parent (e.g. notebook object of tab) while container is logical level parent (which may skip a few level of GUI parents)
    #       The control object will therefore be retrieved from container rather than parent to avoid extra hoppes of references.
    def __init__(self, parent, container, analyzerDataClass, title='', extra_metrics=[], name=''):
        super().__init__(parent, analyzerDataClass)
        self.title = 'FE_tier1'
        self.container = container
        self.variants = []
        self.current_labels = []
        self.extra_metrics = extra_metrics
        self.window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RIDGE, sashwidth=6, sashpad=3)
        self.window.pack(fill=tk.BOTH, expand=True)
        # Setup Plot Frames
        self.plotFrame = tk.Frame(self.window)
        self.canvasFrame = tk.Frame(self.plotFrame)
        self.chartButtonFrame = tk.Frame(self.plotFrame)
        self.plotFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chartButtonFrame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.canvasFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Plot interacting buttons
        self.plotInteraction = PlotInteraction()
        # self.save_state_button = tk.Button(self.plotFrame3, text='Save State', command=self.plotInteraction.saveState)
        self.adjust_button = tk.Button(self.chartButtonFrame, text='Adjust Text', command=self.adjustText)
        self.toggle_labels_button = tk.Button(self.chartButtonFrame, text='Hide Labels', command=self.toggleLabels)
        self.show_markers_button = tk.Button(self.chartButtonFrame, text='Show Points')
        self.unhighlight_button = tk.Button(self.chartButtonFrame, text='Unhighlight')
        self.tidy_plot_button = tk.Button(self.chartButtonFrame, text='Tighten Plot', command=self.tidy_plot)
        # Notebook of plot specific tabs
        self.tab_note = ttk.Notebook(self.window)
        self.axesTab = AxesTab(self.tab_note, self)
        self.tab_note.add(self.axesTab, text='Axes')
        self.labelTab = LabelTab(self.tab_note)
        self.tab_note.add(self.labelTab, text='Labels')
        #self.plotData = None
        # Update names for plot buttons
        self.show_markers_button['command'] = self.showPoints
        self.unhighlight_button['command'] = self.unhighlightPoints
        # Grid Layout
        self.axesTab.render()
        self.labelTab.render()
        # Grid Layout
        self.tab_note.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.tidy_plot_button.grid(column=5, row=0, sticky=tk.S, pady=2)
        self.unhighlight_button.grid(column=4, row=0, sticky=tk.S, pady=2)
        self.show_markers_button.grid(column=3, row=0, sticky=tk.S, pady=2)
        self.toggle_labels_button.grid(column=2, row=0, sticky=tk.S, pady=2)
        self.adjust_button.grid(column=1, row=0, sticky=tk.S, pady=2)
        self.chartButtonFrame.grid_rowconfigure(0, weight=1)
        self.window.add(self.plotFrame, stretch='always')
        self.window.add(self.tab_note, stretch='never')
        self.plot = None
        self.plotUpdater = PlotTab.PlotUpdater(self)
        self.plot = self.mk_plot()
        self.plot.setupFrames(self.canvasFrame, self.chartButtonFrame, self)

    @property
    def control(self):
        return self.container.control

    def tidy_plot(self):
        self.plot.tidy_plot()
        
    def adjustText(self):
        self.plot.adjustText()
    
    def set_labels(self, metrics):
        self.labelTab.set_labels(metrics)
        
    def set_plot_scale(self, x_scale, y_scale):
        self.axesTab.set_plot_scale(x_scale, y_scale)
    
    def set_plot_axes(self, x_scale, y_scale, x_axis, y_axis):
        self.axesTab.set_plot_axes(x_scale, y_scale, x_axis, y_axis)
    # This call is from outside (e.g. controller)
    def adjust_text(self):
        self.adjustText()
    
    def toggleLabels(self):
        alpha = 1
        if self.toggle_labels_button['text'] == 'Hide Labels':
            self.toggle_labels_button['text'] = 'Show Labels'
            alpha = 0
        else:
            self.toggle_labels_button['text'] = 'Hide Labels'
        self.plot.setLabelAlphas(alpha)

    def showPoints(self):
        self.plot.showPoints()
    
    def unhighlightPoints(self):
        self.plot.unhighlightPoints()

    def setupGuiState(self, guiState):
        super().setupGuiState(guiState)
        # Link up analyer Data to guiState
        guiState.add_observer(self.analyzerData)
    
    def setupAnalyzerData(self, analyzerData):
        super().setupAnalyzerData(analyzerData)
        analyzerData.add_observer(self.plotUpdater)
        #self.labelTab.setAnalyzerData(data)
        #self.plotInteraction.setAnalyzerData(data)

    def setLevelData(self, levelData):
        super().setLevelData(levelData)
        self.labelTab.setLevelData(levelData)
        self.axesTab.setLevelData(levelData)

    # Subclass needs to override this method
    def mk_plot(self):
        raise Exception("Method needs to be overriden to create plots")

    # Subclass needs to override this method. Return self.plot to ease chaining
    def update_plot(self):
        assert self.plot is not None
        return self.plot.setLevelData(self.analyzerData.levelData).setLevel(self.analyzerData.level) \
            .setScale(self.analyzerData.scale).setXaxis(self.analyzerData.x_axis).setYaxis(self.analyzerData.y_axis)\
                .setMapping(self.analyzerData.mappings).setShortNamesPath(self.analyzerData.short_names_path)
    
    # Try to adjust current plot without replotting
    def try_adjust_plot(self):
        if not self.plot: return
        if self.analyzerData.x_axis == self.plot.x_axis and self.analyzerData.y_axis == self.plot.y_axis:
            # Can reuse plot if x- and y- axes are not changed
            self.plot.adjust_plot(self.analyzerData.scale)
        else:
            self.full_plot()
    
    # full fledge plotting of data
    def full_plot(self):
        # Update attributes
        self.df = self.analyzerData.df
        if self.df.empty:
            return

        # if not self.plot:
        #     self.plot = self.mk_plot()
        #     self.plot.setupFrames(self.canvasFrame, self.chartButtonFrame)
        # else:
        #     self.update_plot()
        self.update_plot()

        self.plot.compute_and_plot()
        #self.fig, self.plotData = self.plot.fig, self.plot.plotData
        #self.plotInteraction.setPlotData(self.plotData)

        #self.variants = self.analyzerData.variants
        #self.metrics = metrics

        # Format columns for pandastable compatibility
        # self.df.columns = ["{}".format(i) for i in self.df.columns]
        # self.df.sort_values(by=MN.COVERAGE_PCT, ascending=False, inplace=True)
        # for missing in set(metrics)-set(self.df.columns):
        #     self.df[missing] = np.nan

    def get_metrics(self):
        metrics = copy.deepcopy(self.analyzerData.common_columns_start)
        metrics.extend(self.extra_metrics)
        metrics.extend(self.analyzerData.common_columns_end)
        return metrics

    # Delegate to axestab instead to mimic user action
    def update_axes(self, x_scale, y_scale, x_axis, y_axis):
        self.analyzerData.update_axes(x_scale, y_scale, x_axis, y_axis)
        #self.try_adjust_plot()
        
    def notify(self, data):
        # Metrics to be displayed in the data table are unique for each plot
        #metrics = self.get_metrics()
        #self.after(0, self.full_plot)
        self.full_plot()

    def resetTabValues(self):
        # self.x_scale = self.orig_x_scale
        # self.y_scale = self.orig_y_scale
        # self.x_axis = self.orig_x_axis
        # self.y_axis = self.orig_y_axis
        #self.variants = [self.data.loadedData.default_variant] #TODO: edit this out
        self.variants = []
        self.current_labels = []

class GuiStateMonitoringTab(AnalyzerTab):
    def __init__(self, parent, analyzerData):
        super().__init__(parent, analyzerData)
    # Override so not to monitor levelData
    def setupLevelData(self, levelData):
        pass

    # Monitor gui state changes instead
    def setupGuiState(self, guiState):
        guiState.add_observer(self)

class AxesTabData(AnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Axes')
        self.axes = AxesTab.DUMMY_AXES.copy()
        self.scales = AxesTab.DUMMY_SCALES.copy()

    def setAxis(self, idx, value):
        self.axes[idx] = value

    def setScale(self, idx, value): 
        self.scales[idx] = value

    def getAxes(self):
        return self.axes
    
    def getScales(self):
        return self.scales

class AxesTab(AnalyzerTab):
    DUMMY_AXES = ['Choose X Axis Metric', 'Choose Y Axis Metric']
    DUMMY_SCALES = ['Choose X Axis Scale', 'Choose Y Axis Scale']
    X_IDX = 0
    Y_IDX = 1
    @staticmethod
    def all_metric_menu(parent, var, group=False):
        menubutton = tk.Menubutton(parent, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        main_menu.add_radiobutton(value=var.get(), label=var.get(), variable=var)
        main_menu.insert_separator(1)
        if group: 
            single_menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label='Single', menu=single_menu)
            group_menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label='Group', menu=group_menu)
            AxesTab.single_metric_menu(var, single_menu)
            AxesTab.group_metric_menu(var, group_menu)
        else: 
            AxesTab.single_metric_menu(var, main_menu)
        return menubutton

    @staticmethod
    def single_metric_menu(var, main_menu):
        # TRAWL/QPlot/SIPlot metrics
        for category, metrics in PLOT_METRICS.items():
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label=category, menu=menu)
            for metric in metrics:
                menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='All', menu=summary_menu)
        for category, metrics in CATEGORIZED_METRICS.items():
            menu = tk.Menu(summary_menu, tearoff=False)
            summary_menu.add_cascade(label=category, menu=menu)
            for metric in metrics:
                menu.add_radiobutton(value=metric, label=metric, variable=var)

    @staticmethod
    def group_metric_menu(var, main_menu):
        # TRAWL/QPlot/SIPlot metrics
        for category in PLOT_METRICS:
            main_menu.add_radiobutton(value=category, label=category, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='All', menu=summary_menu)
        for category in CATEGORIZED_METRICS:
            summary_menu.add_radiobutton(value=category, label=category, variable=var)

    def __init__(self, parent, tab):
        super().__init__(parent, AxesTabData)
        self.parent = parent
        self.tab = tab
        # Axes metric options
        self.metric_label = tk.Label(self, text='Metrics:')
        self.axes = [self.mkAxisVar(i) for i in range(len(AxesTab.DUMMY_AXES))]
        self.axis_menus = [AxesTab.all_metric_menu(self, a) for a in self.axes]
        # Axes scale options
        self.scale_label = tk.Label(self, text='Scales:')
        self.scales = [self.mkScaleVar(i) for i in range(len(AxesTab.DUMMY_SCALES))]
        self.scale_menus = [tk.OptionMenu(self, s, *([s.get()] + ['Linear', 'Log'])) for s in self.scales]
        for menu in self.scale_menus: menu['menu'].insert_separator(1)
        # Update button to replot
        self.update = tk.Button(self, text='Update', command=self.update_axes)

    def mkAxisVar(self, idx):
        axis = tk.StringVar(value=AxesTab.DUMMY_AXES[idx])
        axis.trace('w', lambda *args: self.axisChanged(idx))
        return axis

    def axisChanged(self, idx):
        self.analyzerData.setAxis(idx, self.axes[idx].get())

    def mkScaleVar(self, idx):
        scale = tk.StringVar(value=AxesTab.DUMMY_SCALES[idx])
        scale.trace('w', lambda *args: self.scaleChanged(idx))
        return scale

    def scaleChanged(self, idx):
        self.analyzerData.setScale(idx, self.scales[idx].get())

    def setupAnalyzerData(self, analyzerData):
        self.setAxes(analyzerData.getAxes())
        self.setScales(analyzerData.getScales())

    def setAxes(self, axes):
        for i, axis in enumerate(axes):
            self.axes[i].set(axis)

    def setScales(self, scales):
        for i, scale in enumerate(scales):
            self.scales[i].set(scale)

    def render(self):
        # Tab grid
        self.metric_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        self.scale_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.axis_menus[0].grid(row=1, column=0, padx=5, sticky=tk.W)
        self.axis_menus[1].grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.scale_menus[0].grid(row=1, column=1, padx=5, sticky=tk.W)
        self.scale_menus[1].grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.update.grid(row=3, column=0, padx=5, sticky=tk.NW)
    
    # Function call to force this tab to set to the provided value and trigger GUI updates
    # This mimics user choose the setting and press the Update button.
    def set_plot_axes(self, x_scale, y_scale, x_axis, y_axis):
        if x_axis: self.axes[self.X_IDX].set(x_axis)
        if y_axis: self.axes[self.Y_IDX].set(y_axis)
        self.set_plot_scale(x_scale, y_scale)

    def set_plot_scale(self, x_scale, y_scale):
        if x_scale: self.scales[self.X_IDX].set(x_scale)
        if y_scale: self.scales[self.Y_IDX].set(y_scale)
        self.update_axes()
    
    def update_axes(self):
        x_axis = None
        y_axis = None
        x_scale = ''
        y_scale = ''
        # Get user selected metrics
        if self.axes[self.X_IDX].get() not in AxesTab.DUMMY_AXES:
            x_axis = self.axes[self.X_IDX].get()
        if self.axes[self.Y_IDX].get() not in AxesTab.DUMMY_AXES:
            y_axis = self.axes[self.Y_IDX].get()
        # Get user selected scales
        if self.scales[self.X_IDX].get() not in AxesTab.DUMMY_SCALES:
            x_scale = self.scales[self.X_IDX].get().lower()
        if self.scales[self.Y_IDX].get() not in AxesTab.DUMMY_SCALES:
            y_scale = self.scales[self.Y_IDX].get().lower()
        # Set user selected metrics/scales to the analyzerData if at least one changed
        if x_scale or y_scale or x_axis or y_axis:
            self.tab.update_axes(x_scale, y_scale, x_axis, y_axis)

    # Override so not to monitor levelData
    def setupLevelData(self, levelData):
        pass

    def setupAnalyzerData(self, analyzerData):
        super().setupAnalyzerData(analyzerData)
        analyzerData.add_observer(self)

    def setupGuiState(self, guiState):
        pass

    def notify(self, data):
        pass
        # if self.current_metrics != self.guiState.labels:
        #     self.resetMetrics()
        #     if self.guiState.labels: self.setMetrics(self.guiState.labels)

class LabelTabData(AnalyzerData):
    def __init__(self, loadedData, level):
        super().__init__(loadedData, level, 'Label')
        self.metrics = LabelTab.DUMMY_METRICS.copy()

    def setMetric(self, idx, value):
        self.metrics[idx] = value

    def getMetrics(self):
        return self.metrics
       

class LabelTab(GuiStateMonitoringTab):
    DUMMY_METRICS = ['Metric 1', 'Metric 2', 'Metric 3']
    def __init__(self, parent):
        super().__init__(parent, LabelTabData)
        self.metrics = [self.mkStringVar(i) for i in range(len(LabelTab.DUMMY_METRICS))]
        self.menus = [AxesTab.all_metric_menu(self, m) for m in self.metrics]
        self.updateButton = tk.Button(self, text='Update', command=self.updateLabels)
        self.resetButton = tk.Button(self, text='Reset', command=self.reset)

    def mkStringVar(self, idx):
        metric = tk.StringVar(value=LabelTab.DUMMY_METRICS[idx])
        metric.trace('w', lambda *args: self.varChanged(idx))
        return metric

    def varChanged(self, idx):
        self.analyzerData.setMetric(idx, self.metrics[idx].get())
        
    @property
    def df(self):
        return self.levelData.df

    @property
    def current_metrics(self):
        return [metric.get() for metric in self.metrics if metric.get() not in LabelTab.DUMMY_METRICS]

    def setupAnalyzerData(self, analyzerData):
        self.setMetrics(analyzerData.getMetrics())

    def notify(self, data):
        if self.current_metrics != self.guiState.labels:
            self.resetMetrics()
            if self.guiState.labels: self.setMetrics(self.guiState.labels)

    def setMetrics(self, metrics):
        for i, metric in enumerate(metrics):
            self.metrics[i].set(metric)

    def render(self):
        self.menus[0].grid(row=0, column=0, padx = 10, pady=10, sticky=tk.NW)
        self.menus[1].grid(row=0, column=1, pady=10, sticky=tk.NW)
        self.menus[2].grid(row=0, column=2, padx = 10, pady=10, sticky=tk.NW)
        self.updateButton.grid(row=1, column=0, padx=10, sticky=tk.NW)
        self.resetButton.grid(row=1, column=1, sticky=tk.NW)

    def resetMetrics(self):
        for metric, label in zip(self.metrics, LabelTab.DUMMY_METRICS):
            metric.set(label)

    def reset(self):
        self.guiState.reset_labels()

    # This method mimic user select the metrics and press Update button
    def set_labels(self, metrics):
        self.resetMetrics()
        self.setMetrics(metrics)
        self.updateLabels()

    def updateLabels(self):
        new_metrics = [metric for metric in self.current_metrics if metric in self.df.columns.tolist()]
        if not new_metrics: 
            self.reset()
        else:
            self.guiState.setLabels(new_metrics)
