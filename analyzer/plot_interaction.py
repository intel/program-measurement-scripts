import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import sys
import threading
from pathlib import Path
import pickle
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from adjustText import adjust_text
import copy
from metric_names import MetricName
from explorer_panel import center
from tkinter import ttk
from metric_names import MetricName
from metric_names import NonMetricName, KEY_METRICS
globals().update(MetricName.__members__)

# Extracted from sca(ax) from 3.2.2
def plt_sca(ax):
    """ 
    Set the current Axes instance to *ax*.

    The current Figure is updated to the parent of *ax*.
    """
    managers = plt._pylab_helpers.Gcf.get_all_fig_managers()
    for m in managers:
        if ax in m.canvas.figure.axes:
            plt._pylab_helpers.Gcf.set_active(m)
            m.canvas.figure.sca(ax)
            return
    raise ValueError("Axes instance argument was not found in a figure")

class PlotInteraction():
    def __init__(self):
        self.adjusted = False
        self.adjusting = False
        self.data = None
        self.level = None
        self.plotData = None

    def setAnalyzerData(self, analyzerData):
        self.analyzerData = analyzerData
        self.level = analyzerData.level

    def setPlotData(self, plotData):
        self.plotData = plotData

    @property
    def canvas(self):
        return self.plotData.canvas

    @property
    def toolbar(self):
        return self.plotData.toolbar

    @property
    def guiState(self):
        return self.analyzerData.levelData.guiState

    @property
    def df(self):
        return self.analyzerData.levelData.df

    def onClick(self, event):
        #print("(%f, %f)", event.xdata, event.ydata)
        # for child in self.plotData.ax.get_children():
        #     print(child)
        action = self.guiState.action_selected
        if action == 'Select Point':
            selected = self.plotData.getSelected(event)
            self.guiState.selectPoints(selected)
            return
        if action == 'Choose Action': return
        for marker in self.plotData.markers:
            contains, points = marker.contains(event)
            if contains and marker.get_alpha():
                name = self.plotData.marker_name[marker]
                if action == 'Highlight Point': 
                    if marker.get_marker() == 'o': self.guiState.highlightPoints([name])
                    else: self.guiState.unhighlightPoints([name])
                elif action == 'Remove Point':
                    self.guiState.removePoints([name]) 
                elif action == 'Toggle Label': 
                    alpha = not self.plotData.name_text[name].get_alpha()
                    self.guiState.toggleLabel(name, alpha)

    def onDraw(self, event):
        if self.adjusted and (self.cur_xlim != self.plotData.ax.get_xlim() or self.cur_ylim != self.plotData.ax.get_ylim()) and \
            (self.home_xlim != self.plotData.ax.get_xlim() or self.home_ylim != self.plotData.ax.get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            print("Ondraw adjusting")
            self.cur_xlim = self.plotData.ax.get_xlim()
            self.cur_ylim = self.plotData.ax.get_ylim()
            self.adjustText()

    def setLims(self):
        self.home_xlim = self.cur_xlim = self.plotData.ax.get_xlim()
        self.home_ylim = self.cur_ylim = self.plotData.ax.get_ylim()
    
    def checkAdjusted(self):
        if self.adjusted:
            self.adjustText()

    def thread_adjustText(self):
        print('Adjusting text...')
        if self.adjusted: # Remove old adjusted texts/arrows and create new texts before calling adjust_text again
            # Store index of hidden texts to update the new texts
            hiddenTexts = []
            highlightedTexts = []
            for i in range(len(self.plotData.texts)):
                if not self.plotData.texts[i].get_alpha(): hiddenTexts.append(i)
                if self.plotData.texts[i].get_color() == 'r': highlightedTexts.append(i)
            # Remove all old texts and arrows
            for child in self.plotData.ax.get_children():
                if isinstance(child, matplotlib.text.Annotation) or (isinstance(child, matplotlib.text.Text) and child.get_text() not in [self.plotData.title, '', self.plotData.ax.get_title()]):
                    child.remove()
            # Create new texts that maintain the current visibility
            self.plotData.texts = [plt.text(self.plotData.xs[i], self.plotData.ys[i], self.plotData.mytext[i], alpha=1 if i not in hiddenTexts else 0, color='k' if i not in highlightedTexts else 'r') for i in range(len(self.plotData.mytext))]
            # Update marker to text mappings with the new texts
            self.plotData.marker_text = dict(zip(self.plotData.markers,self.plotData.texts))
            self.plotData.name_text = dict(zip(self.plotData.names,self.plotData.texts))
        # Only adjust texts that are in the current axes (in case of a zoom)
        to_adjust = []
        for i in range(len(self.plotData.texts)):
            if self.plotData.texts[i].get_alpha() and \
                self.plotData.xs[i] >= self.plotData.ax.get_xlim()[0] and self.plotData.xs[i] <= self.plotData.ax.get_xlim()[1] and \
                self.plotData.ys[i] >= self.plotData.ax.get_ylim()[0] and self.plotData.ys[i] <= self.plotData.ax.get_ylim()[1]:
                to_adjust.append(self.plotData.texts[i])
        adjust_text(to_adjust, ax=self.plotData.ax, arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        # Map each text to the corresponding arrow
        index = 0
        for child in self.plotData.ax.get_children():
            if isinstance(child, matplotlib.text.Annotation):
                self.plotData.text_arrow[to_adjust[index]] = child # Mapping
                if not to_adjust[index].get_alpha(): child.set_visible(False) # Hide arrows with hidden texts
                index += 1
        #self.root.after(0, self.canvas.draw)
        # TODO: WARNING global variable used here. May want to get it from GUI componenet.
        self.canvas.get_tk_widget().after(0, self.canvas.draw)
        self.adjusted = True
        self.adjusting = False
        print('Done Adjust text')
    
    def adjustText(self):
        if not self.adjusting: 
            self.adjusting = True
            if sys.platform == 'darwin':
                self.thread_adjustText()
            else: 
                # Do this in mainthread
                plt_sca(self.plotData.ax)
                threading.Thread(target=self.thread_adjustText, name='adjustText Thread').start()

    # Outdated methods to reference when refactoring GuideTab

    # def toggleHighlight(self, marker, otherText=None):
    #     if marker.get_marker() == 'o':
    #         marker.set_marker('*')
    #         marker.set_markeredgecolor('k')
    #         marker.set_markeredgewidth(0.5)
    #         marker.set_markersize(11)
    #         if otherText:
    #             otherText.set_color('r')
    #     elif marker.get_marker() == '*':
    #         marker.set_marker('o')
    #         marker.set_markeredgecolor(marker.get_markerfacecolor())
    #         marker.set_markersize(6.0)
    #         if otherText:
    #             otherText.set_color('k')

    # def highlightPoint(self, marker):
    #     for tab in self.tabs:
    #         if tab.name != 'Scurve' and tab.name != 'Scurve_all':
    #             otherMarker = tab.plotInteraction.plotData.name_marker[self.plotData.marker_name[marker]]
    #             otherText = tab.plotInteraction.plotData.marker_text[otherMarker]
    #             self.toggleHighlight(otherMarker, otherText)

    # def drawPlots(self):
    #     for tab in self.tabs:
    #         tab.plotInteraction.canvas.draw()

    #TODO: Possibly unhighlight any other highlighted points or show all points to begin with
    # def A_filter(self, relate, metric, threshold, highlight=True, remove=False, show=False, points=[], getNames=False):
    #     df = self.gui.loadedData.summaryDf
    #     names = []
    #     if metric and metric in df.columns.tolist(): names = [name + timestamp for name,timestamp in zip(df.loc[relate(df[metric], threshold)]['Name, df.loc[relate(df[metric], threshold)]['Timestamp#.astype(str))]
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

    # def togglePoint(self, marker, visible):
    #     for tab in self.tabs:
    #         otherMarker = tab.plotInteraction.plotData.name_marker[self.plotData.marker_name[marker]]
    #         otherMarker.set_alpha(visible)
    #         tab.plotInteraction.plotData.marker_text[otherMarker].set_alpha(visible)
    #         try: 
    #             for mapping in tab.plotInteraction.plotData.name_mapping[marker.get_label()]:
    #                 mapping.set_alpha(visible)
    #         except: pass
    #         try: tab.plotInteraction.plotData.text_arrow[tab.plotInteraction.plotData.marker_text[otherMarker]].set_visible(visible)
    #         except: pass
    #         name = tab.plotInteraction.plotData.marker_name[otherMarker]
    #         index = tab.plotInteraction.pointSelector.names.index(name)
    #         tab.plotInteraction.pointSelector.vars[index].set(visible)

    # def cancelAction(self):
    #     self.choice = 'cancel'
    #     self.win.destroy()

    # def selectAction(self, option):
    #     self.choice = option
    #     self.win.destroy()

    # def getSelectedMappings(self, names, mappings):
    #     if mappings.empty or not names: return
    #     selected_mappings = pd.DataFrame()
    #     temp_mappings = mappings.copy(deep=True)
    #     all_names = copy.deepcopy(names)
    #     for name in names:
    #         row = temp_mappings.loc[(temp_mappings['Before Name+temp_mappings['Before Timestamp.astype(str))==name]
    #         while not row.empty:
    #             temp_mappings.drop(row.index, inplace=True)
    #             selected_mappings = selected_mappings.append(row, ignore_index=True)
    #             name = str(row['After Name.iloc[0]+row['After Timestamp.iloc[0].astype(str))
    #             all_names.append(name)
    #             row = temp_mappings.loc[(temp_mappings['Before Name+temp_mappings['Before Timestamp.astype(str))==name]
    #     return selected_mappings, list(set(all_names))

    # def restoreAnalysisState(self):
    #     self.restoreState(self.gui.loadedData.levels[self.level]['data)
    #     self.pointSelector.restoreState(self.gui.loadedData.levels[self.level]['data)

    # def saveState(self):
    #     # Create popup dialog that asks user to select either save selected or save all
    #     self.win = tk.Toplevel()
    #     center(self.win)
    #     self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
    #     self.win.title('Save State')
    #     message = 'Would you like to save data for all of the codelets\nor just for those selected?'
    #     tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
    #     for index, option in enumerate(['Save All', 'Save Selected):
    #         b = tk.Button(self.win, text=option, command= lambda metric=option : self.selectAction(metric))
    #         b.grid(row=index+1, column=1, padx=20, pady=10)
    #     self.root.wait_window(self.win)
    #     if self.choice == 'cancel': return        
    #     # Ask user to name the directory for this state to be saved
    #     dest_name = tk.simpledialog.askstring('Analysis Result', 'Provide a name for this analysis result')
    #     if not dest_name: return
    #     dest = os.path.join(self.gui.loadedData.analysis_results_path, dest_name)
    #     if not os.path.isdir(dest):
    #         Path(dest).mkdir(parents=True, exist_ok=True)
    #     # Store data for all levels
    #     df = self.gui.loadedData.get_df('Codelet').copy(deep=True)
    #     df.columns = ["{}".format(i) for i in df.columns]
    #     srcDf = self.gui.loadedData.get_df('Source').copy(deep=True)
    #     srcDf.columns = ["{}".format(i) for i in srcDf.columns]
    #     appDf = self.gui.loadedData.get_df('Application').copy(deep=True)
    #     appDf.columns = ["{}".format(i) for i in appDf.columns]
    #     codelet = {'plotData' : self.gui.c_customTab.plotInteraction.plotData, 'df' : df, 'mapping' : self.gui.loadedData.mapping, \
    #         'summary_dest' : os.path.join(dest, 'summary.xlsx'), 'mapping_dest' : os.path.join(dest, 'mapping.xlsx'), \
    #         'tabs' : self.codelet_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
    #     source = {'plotData' : self.gui.s_customTab.plotInteraction.plotData, 'df' : srcDf, 'mapping' : self.gui.loadedData.src_mapping, \
    #         'summary_dest' : os.path.join(dest, 'srcSummary.xlsx'), 'mapping_dest' : os.path.join(dest, 'srcMapping.xlsx'), \
    #         'tabs' : self.source_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
    #     app = {'plotData' : self.gui.a_customTab.plotInteraction.plotData, 'df' : appDf, 'mapping' : self.gui.loadedData.app_mapping, \
    #         'summary_dest' : os.path.join(dest, 'appSummary.xlsx'), 'mapping_dest' : os.path.join(dest, 'appMapping.xlsx'), \
    #         'tabs' : self.application_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
    #     levels = [codelet, source, app]
    #     for level in levels:
    #         # Store hidden/highlighted points for each level
    #         for marker in level['plotData['markers:
    #             name = level['plotData['marker_name[marker]
    #             if marker.get_alpha():
    #                 level['data['visible_names.append(name)
    #                 if marker.get_marker() == '*': # Highlighted point
    #                     level['data['highlighted_names.append(name)
    #             elif self.choice == 'Save All':
    #                 level['data['hidden_names.append(name)
    #         # Save either full or selected codelets in dataframes to notify observers upon restoring
    #         if self.choice == 'Save All':
    #             level['df.to_excel(level['summary_dest, index=False)
    #             if not level['mapping.empty: 
    #                 level['mapping.to_excel(level['mapping_dest, index=False)
    #         elif self.choice == 'Save Selected':
    #             if not level['mapping.empty and level['data['visible_names:
    #                 selected_mappings, level['data['visible_names = self.getSelectedMappings(level['data['visible_names, level['mapping)
    #                 selected_mappings.to_excel(level['mapping_dest, index=False)
    #             selected_summary = level['df.loc[(level['df['Name+level['df['Timestamp#.astype(str)).isin(level['data['visible_names)]
    #             selected_summary.to_excel(level['summary_dest, index=False)
    #         # variants apply to all levels
    #         level['data['variants = self.gui.c_summaryTab.variants
    #         # Each tab has its own dictionary with it's current plot selections
    #         for tab in level['tabs:
    #             level['data[tab.name] = {'x_axis':"{}".format(tab.x_axis), 'y_axis':"{}".format(tab.y_axis), 'x_scale':tab.x_scale, 'y_scale':tab.y_scale}
    #     # Save the all the stored data into a nested dictionary
    #     data = {}
    #     data['Codelet = codelet['data
    #     data['Source = source['data
    #     data['Application = app['data
    #     data_dest = os.path.join(dest, 'data.pkl')
    #     data_file = open(data_dest, 'wb')
    #     pickle.dump(data, data_file)
    #     data_file.close()