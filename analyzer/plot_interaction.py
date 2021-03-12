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
    def __init__(self, tab):
        self.tab = tab
        self.level = self.tab.level
        self.gui = self.tab.data.gui
        self.root = self.tab.data.root
        self.adjusted = False
        self.adjusting = False
        self.guiState.add_observers(self)

    @property
    def textData(self):
        return self.tab.textData

    @property
    def fig(self):
        return self.tab.fig

    @property
    def canvas(self):
        return self.tab.canvas

    @property
    def toolbar(self):
        return self.tab.toolbar

    @property
    def guiState(self):
        return self.gui.loadedData.levelData[self.level].guiState

    @property
    def df(self):
        return self.gui.loadedData.levelData[self.level].df

    def notify(self, data):
        self.updateMarkers()
        self.updateLabels()
        # User could've changed the color of the labels: need to update marker colors

    def setLims(self):
        self.home_xlim = self.cur_xlim = self.textData['ax'].get_xlim()
        self.home_ylim = self.cur_ylim = self.textData['ax'].get_ylim()

    def updateMarkers(self):
        # Hide/Show the markers, labels, and arrows
        for name in self.textData['names']:
            alpha = 1
            if name in self.guiState.hidden: alpha = 0
            self.textData['name:marker'][name].set_alpha(alpha)
            self.textData['name:text'][name].set_alpha(alpha)
            # Unhighlight/highlight points
            if name in self.guiState.highlighted: self.highlight(self.textData['name:marker'][name])
            else: self.unhighlight(self.textData['name:marker'][name])
            # Need to first set all mappings to visible, then remove hidden ones to avoid hiding then showing
            if name in self.textData['name:mapping']: self.textData['name:mapping'][name].set_alpha(1)
        for name in self.textData['name:mapping']:
            if name in self.guiState.hidden: self.textData['name:mapping'][name].set_alpha(0)
        self.canvas.draw()

    def updateLabels(self):
        # Update labels on plot
        current_metrics = self.guiState.labels
        if not current_metrics:
            self.tab.labelTab.resetMetrics()
        for i, text in enumerate(self.textData['texts']):
            label = self.textData['orig_mytext'][i][:-1]
            codeletName = self.textData['names'][i]
            for metric_index, metric in enumerate(current_metrics):
                # Update label menu with currently selected metric
                self.tab.labelTab.metrics[metric_index].set(metric)
                # Append to end of label
                value = self.df.loc[(self.df[NAME]+self.df[TIMESTAMP].astype(str))==codeletName][metric].iloc[0]
                if isinstance(value, int) or isinstance(value, float): 
                    label += ', ' + str(round(value, 2))
                else:
                    label += ', ' + str(value)
            label += ')'
            text.set_text(label)
            self.textData['mytext'][i] = label
        # Update legend for user to see order of metrics in the label
        newTitle = self.textData['orig_legend'][:-1]
        for metric in current_metrics:
            newTitle += ', ' + metric
        newTitle += ')'
        self.textData['legend'].get_title().set_text(newTitle)
        # Adjust labels if already adjusted
        self.canvas.draw()
        if self.adjusted:
            self.adjustText()

    def toggleLabels(self):
        if self.tab.toggle_labels_button['text'] == 'Hide Labels': 
            new_text = 'Show Labels'
            alpha = 0
        else: 
            new_text = 'Hide Labels'
            alpha = 1
        for marker in self.textData['marker:text']:
            if marker.get_alpha(): 
                self.textData['marker:text'][marker].set_alpha(alpha) 
                if self.adjusted: 
                    # possibly called adjustText after a zoom and no arrow is mapped to this label outside of the current axes
                    # TODO: Create "marker:arrow" to simplify this statement
                    if self.textData['marker:text'][marker] in self.textData['text:arrow']: self.textData['text:arrow'][self.textData['marker:text'][marker]].set_visible(alpha)
        self.canvas.draw()
        self.tab.toggle_labels_button['text'] = new_text

    def toggleLabel(self, marker):
        label = self.textData['marker:text'][marker]
        label.set_alpha(not label.get_alpha())
        if label in self.textData['text:arrow']: self.textData[label].set_visible(label.get_alpha())
        self.canvas.draw()

    def highlight(self, marker):
        text = self.textData['marker:text'][marker]
        marker.set_marker('*')
        marker.set_markeredgecolor('k')
        marker.set_markeredgewidth(0.5)
        marker.set_markersize(11)
        text.set_color('r')

    def unhighlight(self, marker):
        text = self.textData['marker:text'][marker]
        marker.set_marker('o')
        marker.set_markeredgecolor(marker.get_markerfacecolor())
        marker.set_markersize(6.0)
        text.set_color('k')
    
    def removePoints(self, names):
        self.guiState.removePoints(names)

    def showPoints(self, names):
        self.guiState.showPoints(names)

    def unhighlightPoints(self, names):
        self.guiState.unhighlightPoints(names)

    def highlightPoints(self, names):
        self.guiState.highlightPoints(names)

    def onClick(self, event):
        #print("(%f, %f)", event.xdata, event.ydata)
        # for child in self.textData['ax'].get_children():
        #     print(child)
        action = self.tab.action_selected.get()
        if action == 'Choose Action': return
        for marker in self.textData['markers']:
            contains, points = marker.contains(event)
            if contains and marker.get_alpha():
                if action == 'Highlight Point': 
                    if marker.get_marker() == 'o': self.highlightPoints([self.textData['marker:name'][marker]])
                    else: self.unhighlightPoints([self.textData['marker:name'][marker]])
                elif action == 'Remove Point': self.removePoints([self.textData['marker:name'][marker]])
                elif action == 'Toggle Label': self.toggleLabel(marker)
                self.canvas.draw()

    def onDraw(self, event):
        if self.adjusted and (self.cur_xlim != self.textData['ax'].get_xlim() or self.cur_ylim != self.textData['ax'].get_ylim()) and \
            (self.home_xlim != self.textData['ax'].get_xlim() or self.home_ylim != self.textData['ax'].get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            print("Ondraw adjusting")
            self.cur_xlim = self.textData['ax'].get_xlim()
            self.cur_ylim = self.textData['ax'].get_ylim()
            self.adjustText()

    def thread_adjustText(self):
        print('Adjusting text...')
        if self.adjusted: # Remove old adjusted texts/arrows and create new texts before calling adjust_text again
            # Store index of hidden texts to update the new texts
            hiddenTexts = []
            highlightedTexts = []
            for i in range(len(self.textData['texts'])):
                if not self.textData['texts'][i].get_alpha(): hiddenTexts.append(i)
                if self.textData['texts'][i].get_color() == 'r': highlightedTexts.append(i)
            # Remove all old texts and arrows
            for child in self.textData['ax'].get_children():
                if isinstance(child, matplotlib.text.Annotation) or (isinstance(child, matplotlib.text.Text) and child.get_text() not in [self.textData['title'], '', self.textData['ax'].get_title()]):
                    child.remove()
            # Create new texts that maintain the current visibility
            self.textData['texts'] = [plt.text(self.textData['xs'][i], self.textData['ys'][i], self.textData['mytext'][i], alpha=1 if i not in hiddenTexts else 0, color='k' if i not in highlightedTexts else 'r') for i in range(len(self.textData['mytext']))]
            # Update marker to text mappings with the new texts
            self.textData['marker:text'] = dict(zip(self.textData['markers'],self.textData['texts']))
            self.textData['name:text'] = dict(zip(self.textData['names'],self.textData['texts']))
        # Only adjust texts that are in the current axes (in case of a zoom)
        to_adjust = []
        for i in range(len(self.textData['texts'])):
            if self.textData['texts'][i].get_alpha() and \
                self.textData['xs'][i] >= self.textData['ax'].get_xlim()[0] and self.textData['xs'][i] <= self.textData['ax'].get_xlim()[1] and \
                self.textData['ys'][i] >= self.textData['ax'].get_ylim()[0] and self.textData['ys'][i] <= self.textData['ax'].get_ylim()[1]:
                to_adjust.append(self.textData['texts'][i])
        adjust_text(to_adjust, ax=self.textData['ax'], arrowprops=dict(arrowstyle="-|>", color='r', alpha=0.5))
        # Map each text to the corresponding arrow
        index = 0
        for child in self.textData['ax'].get_children():
            if isinstance(child, matplotlib.text.Annotation):
                self.textData['text:arrow'][to_adjust[index]] = child # Mapping
                if not to_adjust[index].get_alpha(): child.set_visible(False) # Hide arrows with hidden texts
                index += 1
        self.root.after(0, self.canvas.draw)
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
                plt_sca(self.textData['ax'])
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
    #             otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
    #             otherText = tab.plotInteraction.textData['marker:text'][otherMarker]
    #             self.toggleHighlight(otherMarker, otherText)

    # def drawPlots(self):
    #     for tab in self.tabs:
    #         tab.plotInteraction.canvas.draw()

    #TODO: Possibly unhighlight any other highlighted points or show all points to begin with
    # def A_filter(self, relate, metric, threshold, highlight=True, remove=False, show=False, points=[], getNames=False):
    #     df = self.gui.loadedData.summaryDf
    #     names = []
    #     if metric and metric in df.columns.tolist(): names = [name + timestamp for name,timestamp in zip(df.loc[relate(df[metric], threshold)]['Name'], df.loc[relate(df[metric], threshold)]['Timestamp#'].astype(str))]
    #     names.extend(points)
    #     if getNames: return names
    #     for name in names:
    #         try: 
    #             marker = self.textData['name:marker'][name]
    #             if highlight and marker.get_marker() == 'o': self.highlightPoint(marker)
    #             elif not highlight and marker.get_marker() == '*': self.highlightPoint(marker)
    #             if remove: self.togglePoint(marker, visible=False)
    #             elif show: self.togglePoint(marker, visible=True)
    #         except: pass
    #     self.drawPlots()
    #     return names

    # def togglePoint(self, marker, visible):
    #     for tab in self.tabs:
    #         otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
    #         otherMarker.set_alpha(visible)
    #         tab.plotInteraction.textData['marker:text'][otherMarker].set_alpha(visible)
    #         try: 
    #             for mapping in tab.plotInteraction.textData['name:mapping'][marker.get_label()]:
    #                 mapping.set_alpha(visible)
    #         except: pass
    #         try: tab.plotInteraction.textData['text:arrow'][tab.plotInteraction.textData['marker:text'][otherMarker]].set_visible(visible)
    #         except: pass
    #         name = tab.plotInteraction.textData['marker:name'][otherMarker]
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
    #         row = temp_mappings.loc[(temp_mappings['Before Name']+temp_mappings['Before Timestamp'].astype(str))==name]
    #         while not row.empty:
    #             temp_mappings.drop(row.index, inplace=True)
    #             selected_mappings = selected_mappings.append(row, ignore_index=True)
    #             name = str(row['After Name'].iloc[0]+row['After Timestamp'].iloc[0].astype(str))
    #             all_names.append(name)
    #             row = temp_mappings.loc[(temp_mappings['Before Name']+temp_mappings['Before Timestamp'].astype(str))==name]
    #     return selected_mappings, list(set(all_names))

    # def restoreAnalysisState(self):
    #     self.restoreState(self.gui.loadedData.levels[self.level]['data'])
    #     self.pointSelector.restoreState(self.gui.loadedData.levels[self.level]['data'])

    # def saveState(self):
    #     # Create popup dialog that asks user to select either save selected or save all
    #     self.win = tk.Toplevel()
    #     center(self.win)
    #     self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
    #     self.win.title('Save State')
    #     message = 'Would you like to save data for all of the codelets\nor just for those selected?'
    #     tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
    #     for index, option in enumerate(['Save All', 'Save Selected']):
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
    #     codelet = {'textData' : self.gui.c_customTab.plotInteraction.textData, 'df' : df, 'mapping' : self.gui.loadedData.mapping, \
    #         'summary_dest' : os.path.join(dest, 'summary.xlsx'), 'mapping_dest' : os.path.join(dest, 'mapping.xlsx'), \
    #         'tabs' : self.codelet_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
    #     source = {'textData' : self.gui.s_customTab.plotInteraction.textData, 'df' : srcDf, 'mapping' : self.gui.loadedData.src_mapping, \
    #         'summary_dest' : os.path.join(dest, 'srcSummary.xlsx'), 'mapping_dest' : os.path.join(dest, 'srcMapping.xlsx'), \
    #         'tabs' : self.source_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
    #     app = {'textData' : self.gui.a_customTab.plotInteraction.textData, 'df' : appDf, 'mapping' : self.gui.loadedData.app_mapping, \
    #         'summary_dest' : os.path.join(dest, 'appSummary.xlsx'), 'mapping_dest' : os.path.join(dest, 'appMapping.xlsx'), \
    #         'tabs' : self.application_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
    #     levels = [codelet, source, app]
    #     for level in levels:
    #         # Store hidden/highlighted points for each level
    #         for marker in level['textData']['markers']:
    #             name = level['textData']['marker:name'][marker]
    #             if marker.get_alpha():
    #                 level['data']['visible_names'].append(name)
    #                 if marker.get_marker() == '*': # Highlighted point
    #                     level['data']['highlighted_names'].append(name)
    #             elif self.choice == 'Save All':
    #                 level['data']['hidden_names'].append(name)
    #         # Save either full or selected codelets in dataframes to notify observers upon restoring
    #         if self.choice == 'Save All':
    #             level['df'].to_excel(level['summary_dest'], index=False)
    #             if not level['mapping'].empty: 
    #                 level['mapping'].to_excel(level['mapping_dest'], index=False)
    #         elif self.choice == 'Save Selected':
    #             if not level['mapping'].empty and level['data']['visible_names']:
    #                 selected_mappings, level['data']['visible_names'] = self.getSelectedMappings(level['data']['visible_names'], level['mapping'])
    #                 selected_mappings.to_excel(level['mapping_dest'], index=False)
    #             selected_summary = level['df'].loc[(level['df']['Name']+level['df']['Timestamp#'].astype(str)).isin(level['data']['visible_names'])]
    #             selected_summary.to_excel(level['summary_dest'], index=False)
    #         # variants apply to all levels
    #         level['data']['variants'] = self.gui.c_summaryTab.variants
    #         # Each tab has its own dictionary with it's current plot selections
    #         for tab in level['tabs']:
    #             level['data'][tab.name] = {'x_axis':"{}".format(tab.x_axis), 'y_axis':"{}".format(tab.y_axis), 'x_scale':tab.x_scale, 'y_scale':tab.y_scale}
    #     # Save the all the stored data into a nested dictionary
    #     data = {}
    #     data['Codelet'] = codelet['data']
    #     data['Source'] = source['data']
    #     data['Application'] = app['data']
    #     data_dest = os.path.join(dest, 'data.pkl')
    #     data_file = open(data_dest, 'wb')
    #     pickle.dump(data, data_file)
    #     data_file.close()