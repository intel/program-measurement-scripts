import tkinter as tk
import os
import sys
from pathlib import Path
import pickle
import pandas as pd
import copy
from metric_names import MetricName
from explorer_panel import center
from tkinter import ttk
from metric_names import MetricName
from metric_names import NonMetricName, KEY_METRICS
globals().update(MetricName.__members__)


class PlotInteraction():
    def __init__(self):
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