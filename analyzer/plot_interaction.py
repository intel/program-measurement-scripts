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
from meta_tabs import ChecklistBox
from explorer_panel import center
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
    def __init__(self, tab, df, fig, textData, level, gui, root):
        self.tab = tab
        self.df = df
        self.fig = fig
        self.textData = textData
        self.level = level
        self.gui = gui
        self.root = root
        self.adjusted = False
        self.adjusting = False
        self.cur_xlim = self.home_xlim = self.textData['ax'].get_xlim()
        self.cur_ylim = self.home_ylim = self.textData['ax'].get_ylim()
        # Create lists of tabs that need to be synchronized according to the level and update the plot with the saved state
        # self.codelet_tabs = [self.gui.c_siPlotTab, self.gui.c_trawlTab, self.gui.c_qplotTab, self.gui.c_customTab, self.gui.summaryTab, self.gui.c_scurveTab, self.gui.c_scurveAllTab]
        self.codelet_tabs = [self.gui.c_siPlotTab, self.gui.c_trawlTab, self.gui.c_qplotTab, self.gui.c_customTab, self.gui.summaryTab, self.gui.c_scurveAllTab]
        self.source_tabs = [self.gui.s_trawlTab, self.gui.s_qplotTab, self.gui.s_customTab]
        self.application_tabs = [self.gui.a_trawlTab, self.gui.a_qplotTab, self.gui.a_customTab]
        if self.level == 'Codelet': 
            self.tabs = self.codelet_tabs
            self.stateDictionary = self.gui.loadedData.c_plot_state
            self.restoreState(self.stateDictionary)
        elif self.level == 'Source': 
            self.tabs = self.source_tabs
            self.stateDictionary = self.gui.loadedData.s_plot_state
            self.restoreState(self.stateDictionary)
        elif self.level == 'Application': 
            self.tabs = self.application_tabs
            self.stateDictionary = self.gui.loadedData.a_plot_state
            self.restoreState(self.stateDictionary)
        # Setup Frames
        self.plotFrame = tk.Frame(self.tab.window)
        self.plotFrame2 = tk.Frame(self.plotFrame)
        self.plotFrame3 = tk.Frame(self.plotFrame)
        self.tab.window.add(self.plotFrame, stretch='always')
        self.plotFrame3.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.plotFrame2.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Plot interacting buttons
        self.save_state_button = tk.Button(self.plotFrame3, text='Save State', command=self.saveState)
        self.adjust_button = tk.Button(self.plotFrame3, text='Adjust Text', command=self.adjustText)
        self.toggle_labels_button = tk.Button(self.plotFrame3, text='Hide Labels', command=self.toggleLabels)
        self.show_markers_button = tk.Button(self.plotFrame3, text='Show Points', command=self.showMarkers)
        self.unhighlight_button = tk.Button(self.plotFrame3, text='Unhighlight', command=self.unhighlightPoints)
        #self.star_speedups_button = tk.Button(self.plotFrame3, text='Star Speedups', command=self.star_speedups)
        self.action_selected = tk.StringVar(value='Choose Action')
        action_options = ['Choose Action', 'Highlight Point', 'Remove Point', 'Toggle Label']
        self.action_menu = tk.OptionMenu(self.plotFrame3, self.action_selected, *action_options)
        self.action_menu['menu'].insert_separator(1)
        # Plot/toolbar
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame2)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('draw_event', self.onDraw)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame3)
        # Point selection table
        options=[]
        for i in range(len(self.df[SHORT_NAME])):
            options.append('[' + self.df[SHORT_NAME][i] + '] ' + self.df[NAME][i] + ' [' + str(self.df[TIMESTAMP][i]) + ']')
        self.pointSelector = ChecklistBox(self.plotFrame2, options, options, self, listType='pointSelector', short_names=self.df[SHORT_NAME].tolist(), names=self.df[NAME].tolist(), timestamps=self.df[TIMESTAMP].tolist(), bd=1, relief="sunken", background="white")
        self.pointSelector.restoreState(self.stateDictionary)
        # Check if we are loading an analysis result and restore if so
        if self.gui.loadedData.restore: self.restoreAnalysisState()
        # Grid Layout
        self.toolbar.grid(column=7, row=0, sticky=tk.S)
        self.action_menu.grid(column=5, row=0, sticky=tk.S)
        self.unhighlight_button.grid(column=4, row=0, sticky=tk.S, pady=2)
        self.show_markers_button.grid(column=3, row=0, sticky=tk.S, pady=2)
        self.toggle_labels_button.grid(column=2, row=0, sticky=tk.S, pady=2)
        self.adjust_button.grid(column=1, row=0, sticky=tk.S, pady=2)
        self.save_state_button.grid(column=0, row=0, sticky=tk.S, pady=2)
        self.plotFrame3.grid_rowconfigure(0, weight=1)
        self.pointSelector.pack(side=tk.RIGHT, anchor=tk.N, fill=tk.Y)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, anchor=tk.N, padx=10)
        self.toolbar.update()
        self.canvas.draw()

    def restoreAnalysisState(self):
        self.restoreState(self.gui.loadedData.levels[self.level]['data'])
        self.pointSelector.restoreState(self.gui.loadedData.levels[self.level]['data'])

    def cancelAction(self):
        self.choice = 'cancel'
        self.win.destroy()

    def selectAction(self, option):
        self.choice = option
        self.win.destroy()

    def saveState(self):
        # Create popup dialog that asks user to select either save selected or save all
        self.win = tk.Toplevel()
        center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
        self.win.title('Save State')
        message = 'Would you like to save data for all of the codelets\nor just for those selected?'
        tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
        for index, option in enumerate(['Save All', 'Save Selected']):
            b = tk.Button(self.win, text=option, command= lambda metric=option : self.selectAction(metric))
            b.grid(row=index+1, column=1, padx=20, pady=10)
        self.root.wait_window(self.win)
        if self.choice == 'cancel': return        
        # Ask user to name the directory for this state to be saved
        dest_name = tk.simpledialog.askstring('Analysis Result', 'Provide a name for this analysis result')
        if not dest_name: return
        dest = os.path.join(self.gui.loadedData.analysis_results_path, dest_name)
        if not os.path.isdir(dest):
            Path(dest).mkdir(parents=True, exist_ok=True)
        # Store data for all levels
        df = self.gui.loadedData.summaryDf.copy(deep=True)
        df.columns = ["{}".format(i) for i in df.columns]
        srcDf = self.gui.loadedData.srcDf.copy(deep=True)
        srcDf.columns = ["{}".format(i) for i in srcDf.columns]
        appDf = self.gui.loadedData.appDf.copy(deep=True)
        appDf.columns = ["{}".format(i) for i in appDf.columns]
        codelet = {'textData' : self.gui.c_customTab.plotInteraction.textData, 'df' : df, 'mapping' : self.gui.loadedData.mapping, \
            'summary_dest' : os.path.join(dest, 'summary.xlsx'), 'mapping_dest' : os.path.join(dest, 'mapping.xlsx'), \
            'tabs' : self.codelet_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
        source = {'textData' : self.gui.s_customTab.plotInteraction.textData, 'df' : srcDf, 'mapping' : self.gui.loadedData.src_mapping, \
            'summary_dest' : os.path.join(dest, 'srcSummary.xlsx'), 'mapping_dest' : os.path.join(dest, 'srcMapping.xlsx'), \
            'tabs' : self.source_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
        app = {'textData' : self.gui.a_customTab.plotInteraction.textData, 'df' : appDf, 'mapping' : self.gui.loadedData.app_mapping, \
            'summary_dest' : os.path.join(dest, 'appSummary.xlsx'), 'mapping_dest' : os.path.join(dest, 'appMapping.xlsx'), \
            'tabs' : self.application_tabs, 'data' : {'visible_names' : [], 'hidden_names' : [], 'highlighted_names' : []}}
        levels = [codelet, source, app]
        for level in levels:
            # Store hidden/highlighted points for each level
            for marker in level['textData']['markers']:
                name = level['textData']['marker:name'][marker]
                if marker.get_alpha():
                    level['data']['visible_names'].append(name)
                    if marker.get_marker() == '*': # Highlighted point
                        level['data']['highlighted_names'].append(name)
                elif self.choice == 'Save All':
                    level['data']['hidden_names'].append(name)
            # Save either full or selected codelets in dataframes to notify observers upon restoring
            if self.choice == 'Save All':
                level['df'].to_excel(level['summary_dest'], index=False)
                if not level['mapping'].empty: 
                    level['mapping'].to_excel(level['mapping_dest'], index=False)
            elif self.choice == 'Save Selected':
                if not level['mapping'].empty and level['data']['visible_names']:
                    selected_mappings, level['data']['visible_names'] = self.getSelectedMappings(level['data']['visible_names'], level['mapping'])
                    selected_mappings.to_excel(level['mapping_dest'], index=False)
                selected_summary = level['df'].loc[(level['df']['Name']+level['df']['Timestamp#'].astype(str)).isin(level['data']['visible_names'])]
                selected_summary.to_excel(level['summary_dest'], index=False)
            # variants apply to all levels
            level['data']['variants'] = self.gui.summaryTab.variants
            # Each tab has its own dictionary with it's current plot selections
            for tab in level['tabs']:
                level['data'][tab.name] = {'x_axis':"{}".format(tab.x_axis), 'y_axis':"{}".format(tab.y_axis), 'x_scale':tab.x_scale, 'y_scale':tab.y_scale}
        # Save the all the stored data into a nested dictionary
        data = {}
        data['Codelet'] = codelet['data']
        data['Source'] = source['data']
        data['Application'] = app['data']
        data_dest = os.path.join(dest, 'data.pkl')
        data_file = open(data_dest, 'wb')
        pickle.dump(data, data_file)
        data_file.close()

    #TODO: Possibly unhighlight any other highlighted points or show all points to begin with
    def A_filter(self, relate, metric, threshold, highlight=True, remove=False, show=False, points=[], getNames=False):
        df = self.gui.loadedData.summaryDf
        names = []
        if metric and metric in df.columns.tolist(): names = [name + timestamp for name,timestamp in zip(df.loc[relate(df[metric], threshold)]['Name'], df.loc[relate(df[metric], threshold)]['Timestamp#'].astype(str))]
        names.extend(points)
        if getNames: return names
        for name in names:
            try: 
                marker = self.textData['name:marker'][name]
                if highlight and marker.get_marker() == 'o': self.highlightPoint(marker)
                elif not highlight and marker.get_marker() == '*': self.highlightPoint(marker)
                if remove: self.togglePoint(marker, visible=False)
                elif show: self.togglePoint(marker, visible=True)
            except: pass
        self.drawPlots()
        return names

    def save_plot_state(self):
        # Get names of this tabs current hidden/highlighted data points
        if self.level == 'Codelet': dictionary = self.gui.loadedData.c_plot_state
        elif self.level == 'Source': dictionary = self.gui.loadedData.s_plot_state
        elif self.level == 'Application': dictionary = self.gui.loadedData.a_plot_state
        dictionary['hidden_names'] = []
        dictionary['highlighted_names'] = []
        # try: dictionary['self.guide_A_state'] = self.gui.summaryTab.self.guideTab.aTab.aLabel['text']
        # except: pass
        for marker in self.textData['markers']:
            if not marker.get_alpha():
                dictionary['hidden_names'].append(marker.get_label())
            if marker.get_marker() == '*':
                dictionary['highlighted_names'].append(marker.get_label())

    def restoreState(self, dictionary):
        for name in dictionary['hidden_names']:
            try:
                self.textData['name:marker'][name].set_alpha(0)
                self.textData['name:text'][name].set_alpha(0)
            except:
                pass
        self.filterArrows(dictionary['hidden_names'])
        for name in dictionary['highlighted_names']:
            try: 
                if self.textData['name:marker'][name].get_marker() != '*': self.highlight(self.textData['name:marker'][name], self.textData['name:text'][name])
            except: pass
        
    def filterArrows(self, names):
        if self.tab.mappings.empty or not names: return
        transitions = pd.DataFrame()
        for name in names:
            row = self.tab.mappings.loc[(self.tab.mappings['Before Name']+self.tab.mappings['Before Timestamp'].astype(str))==name]
            while not row.empty:
                try: self.togglePoint(self.textData['name:marker'][name], visible=False)
                except: pass
                transitions = transitions.append(row, ignore_index=True)
                name = str(row['After Name'].iloc[0]+row['After Timestamp'].iloc[0].astype(str))
                row = self.tab.mappings.loc[(self.tab.mappings['Before Name']+self.tab.mappings['Before Timestamp'].astype(str))==name]

    def getSelectedMappings(self, names, mappings):
        if mappings.empty or not names: return
        selected_mappings = pd.DataFrame()
        temp_mappings = mappings.copy(deep=True)
        all_names = copy.deepcopy(names)
        for name in names:
            row = temp_mappings.loc[(temp_mappings['Before Name']+temp_mappings['Before Timestamp'].astype(str))==name]
            while not row.empty:
                temp_mappings.drop(row.index, inplace=True)
                selected_mappings = selected_mappings.append(row, ignore_index=True)
                name = str(row['After Name'].iloc[0]+row['After Timestamp'].iloc[0].astype(str))
                all_names.append(name)
                row = temp_mappings.loc[(temp_mappings['Before Name']+temp_mappings['Before Timestamp'].astype(str))==name]
        return selected_mappings, list(set(all_names))

    def toggleLabels(self):
        if self.toggle_labels_button['text'] == 'Hide Labels':
            print("Hiding Labels")
            for text in self.textData['texts']:
                text.set_alpha(0)
                if self.adjusted:
                    # possibly called adjustText after a zoom and no arrow is mapped to this label outside of the current axes
                    try: self.textData['text:arrow'][text].set_visible(False)
                    except: pass
            self.canvas.draw()
            self.toggle_labels_button['text'] = 'Show Labels'
        elif self.toggle_labels_button['text'] == 'Show Labels':
            print("Showing Labels")
            for marker in self.textData['marker:text']:
                if marker.get_alpha(): 
                    self.textData['marker:text'][marker].set_alpha(1) 
                    if self.adjusted: 
                        try: self.textData['text:arrow'][self.textData['marker:text'][marker]].set_visible(True)
                        except: pass
            self.canvas.draw()
            self.toggle_labels_button['text'] = 'Hide Labels'

    def toggleLabel(self, marker):
        label = self.textData['marker:text'][marker]
        if label.get_alpha():
            label.set_alpha(0)
            try: self.textData['text:arrow'][label].set_visible(False)
            except: pass 
        else:
            label.set_alpha(1)
            try: self.textData['text:arrow'][label].set_visible(True)
            except: pass 
        self.canvas.draw()

    def showMarkers(self):
        print("Showing markers")
        for tab in self.tabs:
            for marker in tab.plotInteraction.textData['markers']:
                marker.set_alpha(1)
                if tab.plotInteraction.textData['mappings']: 
                    for i in range(len(tab.plotInteraction.textData['mappings'])): 
                        tab.plotInteraction.textData['mappings'][i].set_alpha(1) 
                if tab.plotInteraction.toggle_labels_button['text'] == 'Hide Labels': # Know we need to show the labels/arrows as well
                    tab.plotInteraction.textData['marker:text'][marker].set_alpha(1)
                    if tab.plotInteraction.adjusted:
                        try: tab.plotInteraction.textData['text:arrow'][tab.plotInteraction.textData['marker:text'][marker]].set_visible(True)
                        except: pass
            for var in tab.plotInteraction.pointSelector.vars:
                var.set(1)
            tab.plotInteraction.canvas.draw()

    def onClick(self, event):
        #print("(%f, %f)", event.xdata, event.ydata)
        # for child in self.textData['ax'].get_children():
        #     print(child)
        if self.action_selected.get() == 'Choose Action':
            pass
        elif self.action_selected.get() == 'Highlight Point':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.highlightPoint(marker)
                    self.drawPlots()
                    return
        elif self.action_selected.get() == 'Remove Point':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.togglePoint(marker, visible=False)
                    self.drawPlots()
                    return
        elif self.action_selected.get() == 'Toggle Label':
            for marker in self.textData['markers']:
                contains, points = marker.contains(event)
                if contains and marker.get_alpha():
                    self.toggleLabel(marker)
                    return

    def togglePoint(self, marker, visible):
        # TODO: Fix so that binned scurve doesn't get invoked in togglePoint
        for tab in self.tabs:
            otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
            otherMarker.set_alpha(visible)
            tab.plotInteraction.textData['marker:text'][otherMarker].set_alpha(visible)
            try: 
                for mapping in tab.plotInteraction.textData['name:mapping'][marker.get_label()]:
                    mapping.set_alpha(visible)
            except: pass
            try: tab.plotInteraction.textData['text:arrow'][tab.plotInteraction.textData['marker:text'][otherMarker]].set_visible(visible)
            except: pass
            name = tab.plotInteraction.textData['marker:name'][otherMarker]
            index = tab.plotInteraction.pointSelector.names.index(name)
            tab.plotInteraction.pointSelector.vars[index].set(visible)

    def highlight(self, marker, otherText=None):
        if marker.get_marker() == 'o':
            marker.set_marker('*')
            marker.set_markeredgecolor('k')
            marker.set_markeredgewidth(0.5)
            marker.set_markersize(11)
            if otherText:
                otherText.set_color('r')
        elif marker.get_marker() == '*':
            marker.set_marker('o')
            marker.set_markeredgecolor(marker.get_markerfacecolor())
            marker.set_markersize(6.0)
            if otherText:
                otherText.set_color('k')
    
    def highlightPoint(self, marker):
        for tab in self.tabs:
            if tab.name != 'Scurve' and tab.name != 'Scurve_all':
                otherMarker = tab.plotInteraction.textData['name:marker'][self.textData['marker:name'][marker]]
                otherText = tab.plotInteraction.textData['marker:text'][otherMarker]
                self.highlight(otherMarker, otherText)

    def unhighlightPoints(self):
        for tab in self.tabs:
            for marker in tab.plotInteraction.textData['markers']:
                text = tab.plotInteraction.textData['marker:text'][marker]
                if marker.get_marker() == '*':
                    marker.set_marker('o')
                    marker.set_markeredgecolor(marker.get_markerfacecolor())
                    marker.set_markersize(6.0)
                    text.set_color('k')
        self.drawPlots()
    
    def drawPlots(self):
        for tab in self.tabs:
            tab.plotInteraction.canvas.draw()

    def onDraw(self, event):
        if self.adjusted and (self.cur_xlim != self.textData['ax'].get_xlim() or self.cur_ylim != self.textData['ax'].get_ylim()) and \
            (self.home_xlim != self.textData['ax'].get_xlim() or self.home_ylim != self.textData['ax'].get_ylim()) and \
            self.toolbar.mode != 'pan/zoom': 
            print("Ondraw adjusting")
            self.cur_xlim = self.textData['ax'].get_xlim()
            self.cur_ylim = self.textData['ax'].get_ylim()
            self.adjustText()

    def thread_adjustText(self):
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
    
    def adjustText(self):
        if not self.adjusting: 
            self.adjusting = True
            if sys.platform == 'darwin':
                self.thread_adjustText()
            else: 
                #        plt.sca(self.textData['ax'])
                # Do this in mainthread
                plt_sca(self.textData['ax'])
                threading.Thread(target=self.thread_adjustText, name='adjustText Thread').start()