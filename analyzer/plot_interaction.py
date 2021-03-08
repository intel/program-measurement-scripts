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
        # TODO: Get rid of all places where these tabs are looped through and have loadedData notify observers instead
        self.codelet_tabs = [self.gui.c_siPlotTab, self.gui.c_trawlTab, self.gui.c_qplotTab, self.gui.c_customTab, self.gui.c_summaryTab, self.gui.c_scurveAllTab]
        self.source_tabs = [self.gui.s_trawlTab, self.gui.s_qplotTab, self.gui.s_customTab, self.gui.s_summaryTab]
        self.application_tabs = [self.gui.a_trawlTab, self.gui.a_qplotTab, self.gui.a_customTab, self.gui.a_summaryTab]
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
        self.plotFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.plotFrame3.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.plotFrame2.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tab.window.add(self.plotFrame, stretch='always')
        # Plot interacting buttons
        self.save_state_button = tk.Button(self.plotFrame3, text='Save State', command=self.saveState)
        self.adjust_button = tk.Button(self.plotFrame3, text='Adjust Text', command=self.adjustText)
        self.toggle_labels_button = tk.Button(self.plotFrame3, text='Hide Labels', command=self.toggleLabels)
        self.show_markers_button = tk.Button(self.plotFrame3, text='Show Points', command=self.showMarkers)
        self.unhighlight_button = tk.Button(self.plotFrame3, text='Unhighlight', command=self.unhighlightPoints)
        # self.star_speedups_button = tk.Button(self.plotFrame3, text='Star Speedups', command=self.star_speedups)
        self.action_selected = tk.StringVar(value='Choose Action')
        action_options = ['Choose Action', 'Highlight Point', 'Remove Point', 'Toggle Label']
        self.action_menu = tk.OptionMenu(self.plotFrame3, self.action_selected, *action_options)
        self.action_menu['menu'].insert_separator(1)
        # Plot/toolbar
        self.canvas = FigureCanvasTkAgg(self.fig, self.plotFrame2)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('draw_event', self.onDraw)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame3)
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
        # Notebook of plot specific tabs
        self.tab_note = ttk.Notebook(self.tab.window)
        self.tab_note.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.tab.window.add(self.tab_note, stretch='always')
        self.axesTab = AxesTab(self.tab_note, self.tab, self.tab.name)
        self.tab_note.add(self.axesTab, text='Axes')
        self.labelTab = LabelTab(self.tab_note, self.tab, self.tab.level)
        self.tab_note.add(self.labelTab, text='Labels')
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
        df = self.gui.loadedData.get_df('Codelet').copy(deep=True)
        df.columns = ["{}".format(i) for i in df.columns]
        srcDf = self.gui.loadedData.get_df('Source').copy(deep=True)
        srcDf.columns = ["{}".format(i) for i in srcDf.columns]
        appDf = self.gui.loadedData.get_df('Application').copy(deep=True)
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
            level['data']['variants'] = self.gui.c_summaryTab.variants
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
        # try: dictionary['self.guide_A_state'] = self.gui.c_summaryTab.self.guideTab.aTab.aLabel['text']
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
                #        plt.sca(self.textData['ax'])
                # Do this in mainthread
                plt_sca(self.textData['ax'])
                threading.Thread(target=self.thread_adjustText, name='adjustText Thread').start()

class AxesTab(tk.Frame):
    @staticmethod
    def custom_axes(parent, var, gui):
        menubutton = tk.Menubutton(parent, textvariable=var, indicatoron=True,
                           borderwidth=2, relief="raised", highlightthickness=2)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        # TRAWL
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='TRAWL', menu=menu)
        for metric in [SPEEDUP_VEC, SPEEDUP_DL1, MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S, VARIANT]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # QPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='QPlot', menu=menu)
        for metric in [MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_L3_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S, MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S]:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # SIPlot
        menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='SIPlot', menu=menu)
        for metric in ['Saturation', 'Intensity']:
            menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Speedups (If mappings):
        # if not parent.tab.mappings.empty:
        #     menu = tk.Menu(main_menu, tearoff=False)
        #     main_menu.add_cascade(label='Speedups', menu=menu)
        #     for metric in [SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']:
        #         menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Diagnostic Variables
        # if gui.loadedData.analytic_columns and set(gui.loadedData.analytic_columns).issubset(gui.loadedData.summaryDf.columns):
        #     menu = tk.Menu(main_menu, tearoff=False)
        #     main_menu.add_cascade(label='Diagnostics', menu=menu)
        #     for metric in gui.loadedData.analytic_columns:
        #         menu.add_radiobutton(value=metric, label=metric, variable=var)
        # Summary categories/metrics
        summary_menu = tk.Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label='Summary', menu=summary_menu)
        metrics = [[COVERAGE_PCT, TIME_APP_S, TIME_LOOP_S],
                    [NUM_CORES, DATA_SET, PREFETCHERS, REPETITIONS],
                    [E_PKG_J, E_DRAM_J, E_PKGDRAM_J], 
                    [P_PKG_W, P_DRAM_W, P_PKGDRAM_W],
                    [COUNT_INSTS_GI, RATE_INST_GI_P_S],
                    [RATE_L1_GB_P_S, RATE_L2_GB_P_S, RATE_L3_GB_P_S, RATE_RAM_GB_P_S, RATE_FP_GFLOP_P_S, RATE_INST_GI_P_S, RATE_REG_ADDR_GB_P_S, RATE_REG_DATA_GB_P_S, RATE_REG_SIMD_GB_P_S, RATE_REG_GB_P_S],
                    [COUNT_OPS_VEC_PCT, COUNT_OPS_FMA_PCT, COUNT_OPS_DIV_PCT, COUNT_OPS_SQRT_PCT, COUNT_OPS_RSQRT_PCT, COUNT_OPS_RCP_PCT],
                    [COUNT_INSTS_VEC_PCT, COUNT_INSTS_FMA_PCT, COUNT_INSTS_DIV_PCT, COUNT_INSTS_SQRT_PCT, COUNT_INSTS_RSQRT_PCT, COUNT_INSTS_RCP_PCT],
                    gui.loadedData.summaryDf.columns.tolist()]
        # TODO: Get all other metrics not in a pre-defined category and put in Misc instead of All
        categories = ['Time/Coverage', 'Experiment Settings', 'Energy', 'Power', 'Instructions', 'Rates', r'%ops', r'%inst', 'All']
        for index, category in enumerate(categories):
            menu = tk.Menu(summary_menu, tearoff=False)
            summary_menu.add_cascade(label=category, menu=menu)
            for metric in metrics[index]:
                if metric in gui.loadedData.summaryDf.columns:
                    menu.add_radiobutton(value=metric, label=metric, variable=var)
        return menubutton

    def __init__(self, parent, tab, plotType):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.plotType = plotType
        # Axes metric options
        metric_label = tk.Label(self, text='Metrics:')
        self.y_selected = tk.StringVar(value='Choose Y Axis Metric')
        self.x_selected = tk.StringVar(value='Choose X Axis Metric')
        x_options = ['Choose X Axis Metric', MetricName.CAP_FP_GFLOP_P_S, RATE_INST_GI_P_S]
        if self.plotType == 'Custom' or self.plotType == 'Scurve':
            x_menu = AxesTab.custom_axes(self, self.x_selected, self.tab.data.gui)
            y_menu = AxesTab.custom_axes(self, self.y_selected, self.tab.data.gui)
        else:  
            if self.plotType == 'QPlot':
                y_options = ['Choose Y Axis Metric', MetricName.CAP_L1_GB_P_S, MetricName.CAP_L2_GB_P_S, MetricName.CAP_L3_GB_P_S, MetricName.CAP_RAM_GB_P_S, MetricName.CAP_MEMMAX_GB_P_S]
            elif self.plotType == 'TRAWL':
                y_options = ['Choose Y Axis Metric', SPEEDUP_VEC, SPEEDUP_DL1]
            elif self.plotType == 'Summary':
                x_options.append(RECIP_TIME_LOOP_MHZ)
                y_options = ['Choose Y Axis Metric', COVERAGE_PCT, TIME_LOOP_S, TIME_APP_S, RECIP_TIME_LOOP_MHZ]
            else:
                x_options = ['Choose X Axis Metric']
                y_options = ['Choose Y Axis Metric']
            y_menu = tk.OptionMenu(self, self.y_selected, *y_options)
            x_menu = tk.OptionMenu(self, self.x_selected, *x_options)
            y_menu['menu'].insert_separator(1)
            x_menu['menu'].insert_separator(1)
        # Axes scale options
        scale_label = tk.Label(self, text='Scales:')
        self.yscale_selected = tk.StringVar(value='Choose Y Axis Scale')
        self.xscale_selected = tk.StringVar(value='Choose X Axis Scale')
        yscale_options = ['Choose Y Axis Scale', 'Linear', 'Log']
        xscale_options = ['Choose X Axis Scale', 'Linear', 'Log']
        yscale_menu = tk.OptionMenu(self, self.yscale_selected, *yscale_options)
        xscale_menu = tk.OptionMenu(self, self.xscale_selected, *xscale_options)
        yscale_menu['menu'].insert_separator(1)
        xscale_menu['menu'].insert_separator(1)
        # Update button to replot
        update = tk.Button(self, text='Update', command=self.update_axes)
        # Tab grid
        metric_label.grid(row=0, column=0, padx=5, sticky=tk.W)
        scale_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        x_menu.grid(row=1, column=0, padx=5, sticky=tk.W)
        y_menu.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        xscale_menu.grid(row=1, column=1, padx=5, sticky=tk.W)
        yscale_menu.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        update.grid(row=3, column=0, padx=5, sticky=tk.NW)
    
    def update_axes(self):
        # Get user selected metrics
        if self.x_selected.get() != 'Choose X Axis Metric':
            self.tab.x_axis = self.x_selected.get()
        if self.y_selected.get() != 'Choose Y Axis Metric':
            self.tab.y_axis = self.y_selected.get()
        # Get user selected scales
        if self.xscale_selected.get() != 'Choose X Axis Scale':
            self.tab.x_scale = self.xscale_selected.get().lower()
        if self.yscale_selected.get() != 'Choose Y Axis Scale':
            self.tab.y_scale = self.yscale_selected.get().lower()
        # Save current plot states
        self.tab.plotInteraction.save_plot_state()
        # Set user selected metrics/scales if they have changed at least one
        if self.x_selected.get() != 'Choose X Axis Metric' or self.y_selected.get() != 'Choose Y Axis Metric' or self.xscale_selected.get() != 'Choose X Axis Scale' or self.yscale_selected.get() != 'Choose Y Axis Scale':
            self.tab.data.scale = self.tab.x_scale + self.tab.y_scale
            self.tab.data.y_axis = "{}".format(self.tab.y_axis)
            self.tab.data.x_axis = "{}".format(self.tab.x_axis)
            self.tab.data.notify(self.tab.data.gui.loadedData)

class LabelTab(tk.Frame):
    def __init__(self, parent, tab, level):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.tab = tab
        self.loadedData = self.tab.data.gui.loadedData
        self.metric1 = tk.StringVar(value='Metric 1')
        self.metric2 = tk.StringVar(value='Metric 2')
        self.metric3 = tk.StringVar(value='Metric 3')
        self.menu1 = AxesTab.custom_axes(self, self.metric1, self.tab.data.gui)
        self.menu2 = AxesTab.custom_axes(self, self.metric2, self.tab.data.gui)
        self.menu3 = AxesTab.custom_axes(self, self.metric3, self.tab.data.gui)
        self.updateButton = tk.Button(self, text='Update', command=self.updateLabels)
        self.resetButton = tk.Button(self, text='Reset', command=self.reset)
        # Grid layout 
        self.menu1.grid(row=0, column=0, padx = 10, pady=10, sticky=tk.NW)
        self.menu2.grid(row=0, column=1, pady=10, sticky=tk.NW)
        self.menu3.grid(row=0, column=2, padx = 10, pady=10, sticky=tk.NW)
        self.updateButton.grid(row=1, column=0, padx=10, sticky=tk.NW)
        self.resetButton.grid(row=1, column=1, sticky=tk.NW)

    def resetMetrics(self):
        self.metric1.set('Metric 1')
        self.metric2.set('Metric 2')
        self.metric3.set('Metric 3')
        # self.loadedData.levelData[level].reset_labels()

    def reset(self):
        self.resetMetrics()
        for tab in self.tab.plotInteraction.tabs:
            if tab.name != 'Scurve':
                textData = tab.plotInteraction.textData
                tab.current_labels = []
                for i, text in enumerate(textData['texts']):
                    text.set_text(textData['orig_mytext'][i])
                    textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
                    textData['legend'].get_title().set_text(textData['orig_legend'])
                tab.plotInteraction.canvas.draw()
                # Adjust labels if already adjusted
                if tab.plotInteraction.adjusted:
                    tab.plotInteraction.adjustText()

    def updateLabels(self):
        current_metrics = []
        if self.metric1.get() != 'Metric 1': current_metrics.append(self.metric1.get())
        if self.metric2.get() != 'Metric 2': current_metrics.append(self.metric2.get())
        if self.metric3.get() != 'Metric 3': current_metrics.append(self.metric3.get())
        current_metrics = [metric for metric in current_metrics if metric in self.tab.plotInteraction.df.columns.tolist()]
        if not current_metrics: return # User hasn't selected any label metrics
        for tab in self.tab.plotInteraction.tabs:
            if tab.name != 'Scurve':
                tab.current_labels = current_metrics
                textData = tab.plotInteraction.textData

                # TODO: Update the rest of the plots at the same level with the new checked variants
                # for tab in self.parent.tab.plotInteraction.tabs:
                #     for i, cb in enumerate(self.cbs):
                #         tab.labelTab.checkListBox.vars[i].set(self.vars[i].get())
                #     tab.current_labels = self.parent.tab.current_labels

                # If nothing selected, revert labels and legend back to original
                if not tab.current_labels:
                    for i, text in enumerate(textData['texts']):
                        text.set_text(textData['orig_mytext'][i])
                        textData['mytext'] = copy.deepcopy(textData['orig_mytext'])
                        textData['legend'].get_title().set_text(textData['orig_legend'])
                else: 
                    # Update existing plot texts by adding user specified metrics
                    df = tab.plotInteraction.df
                    for i, text in enumerate(textData['texts']):
                        toAdd = textData['orig_mytext'][i][:-1]
                        for choice in tab.current_labels:
                            codeletName = textData['names'][i]
                            # TODO: Clean this up so it's on the edges and not the data points
                            if choice in [SPEEDUP_TIME_LOOP_S, SPEEDUP_TIME_APP_S, SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']:
                                tempDf = pd.DataFrame()
                                if not tab.mappings.empty: # Mapping
                                    tempDf = tab.mappings.loc[(tab.mappings['Before Name']+tab.mappings['Before Timestamp'].astype(str))==codeletName]
                                if tempDf.empty: 
                                    if choice == 'Difference': 
                                        tempDf = tab.mappings.loc[(tab.mappings['After Name']+tab.mappings['After Timestamp'].astype(str))==codeletName]
                                        if tempDf.empty:
                                            value = 'Same'
                                    else: value = 1
                                else: value = tempDf[choice].iloc[0]
                            else:
                                value = df.loc[(df[NAME]+df[TIMESTAMP].astype(str))==codeletName][choice].iloc[0]
                            if isinstance(value, int) or isinstance(value, float):
                                toAdd += ', ' + str(round(value, 2))
                            else:
                                toAdd += ', ' + str(value)
                        toAdd += ')'
                        text.set_text(toAdd)
                        textData['mytext'][i] = toAdd
                    # Update legend for user to see order of metrics in the label
                    newTitle = textData['orig_legend'][:-1]
                    for choice in tab.current_labels:
                        newTitle += ', ' + choice
                    newTitle += ')'
                    textData['legend'].get_title().set_text(newTitle)
                tab.plotInteraction.canvas.draw()
                # Adjust labels if already adjusted
                if tab.plotInteraction.adjusted:
                    tab.plotInteraction.adjustText()

class ChecklistBox(tk.Frame):
    def __init__(self, parent, choices, hidden, tab, short_names=[], names=[], timestamps=[], **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent=parent
        self.tab=tab
        scrollbar = tk.Scrollbar(self)
        scrollbar_x = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        checklist = tk.Text(self, width=40)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        checklist.pack(fill=tk.Y, expand=True)
        self.vars = []
        self.names = []
        self.cbs = []
        bg = self.cget("background")
        for index, choice in enumerate(choices):
            var = tk.IntVar(value=1)
            self.vars.append(var)
            if short_names and names and timestamps:
                name = names[index] + str(timestamps[index])
                self.names.append(name)
                if name in hidden:
                    var.set(0)
            cb = tk.Checkbutton(self, var=var, text=choice,
                                onvalue=1, offvalue=0,
                                anchor="w", width=100, background=bg,
                                relief="flat", highlightthickness=0
            )
            self.cbs.append(cb)
            checklist.window_create("end", window=cb)
            checklist.insert("end", "\n")
        checklist.config(yscrollcommand=scrollbar.set)
        checklist.config(xscrollcommand=scrollbar_x.set)
        scrollbar.config(command=checklist.yview)
        scrollbar_x.config(command=checklist.xview)
        checklist.configure(state="disabled")

    def restoreState(self, dictionary):
        for name in dictionary['hidden_names']:
            try: 
                index = self.names.index(name)
                self.vars[index].set(0)
            except: pass

    def updatePlot(self):
        hidden_names = []
        for index, var in enumerate(self.vars):
            # selected = var.get()
            # selected_value = 1 if selected else 0
            if not var.get(): hidden_names.append(self.names[index])
            # marker = tab.plotInteraction.textData['name:marker'][name]
            # marker.set_alpha(selected_value)
            # text = tab.plotInteraction.textData['marker:text'][marker]
            # text.set_alpha(selected_value) 
            # if text in tab.plotInteraction.textData['text:arrow']: tab.plotInteraction.textData['text:arrow'][text].set_visible(selected)
            # try: 
            #     for mapping in tab.plotInteraction.textData['name:mapping'][name]:
            #         mapping.set_alpha(selected_value)
            # except: pass
        return hidden_names
        # tab.plotInteraction.canvas.draw()

    def updatePlot1(self):
        for tab in self.tab.tabs:
            for index, var in enumerate(self.vars):
                selected = var.get()
                selected_value = 1 if selected else 0
                name = self.names[index]
                tab.plotInteraction.pointSelector.vars[index].set(selected_value)
                marker = tab.plotInteraction.textData['name:marker'][name]
                marker.set_alpha(selected_value)
                text = tab.plotInteraction.textData['marker:text'][marker]
                text.set_alpha(selected_value) 
                try: tab.plotInteraction.textData['text:arrow'][text].set_visible(selected)
                except: pass
                try: 
                    for mapping in tab.plotInteraction.textData['name:mapping'][name]:
                        mapping.set_alpha(selected_value)
                except: pass
            tab.plotInteraction.canvas.draw()

    def getCheckedItems(self):
        values = []
        for i, cb in enumerate(self.cbs):
            value =  self.vars[i].get()
            if value:
                values.append(cb['text'])
        return values

    def showAllVariants(self):
        for i, cb in enumerate(self.cbs):
            self.vars[i].set(1)
        self.updateVariants()
    
    def showOrig(self):
        for i, cb in enumerate(self.cbs):
            if cb['text'] == self.tab.data.gui.loadedData.default_variant: self.vars[i].set(1)
            else: self.vars[i].set(0)
        self.updateVariants()

    def updateVariants(self):
        self.parent.tab.variants = self.getCheckedItems()
        # Update the rest of the plots at the same level with the new checked variants
        for tab in self.parent.tab.plotInteraction.tabs:
            for i, cb in enumerate(self.cbs):
                tab.variantTab.checkListBox.vars[i].set(self.vars[i].get())
            tab.variants = self.parent.tab.variants
        self.parent.tab.plotInteraction.save_plot_state()
        # Get new mappings from database to update plots
        self.all_mappings = pd.read_csv(self.tab.data.gui.loadedData.mappings_path)
        # self.mapping = MappingsTab.restoreCustom(self.tab.data.gui.loadedData.summaryDf.loc[self.tab.data.gui.loadedData.summaryDf[VARIANT].isin(self.parent.tab.variants)], self.all_mappings)
        for tab in self.parent.tab.plotInteraction.tabs:
            if tab.name == 'SIPlot': tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, cluster=tab.cluster, title=tab.title, mappings=self.mapping)
            else: tab.data.notify(self.tab.data.gui.loadedData, variants=tab.variants, x_axis="{}".format(tab.x_axis), y_axis="{}".format(tab.y_axis), scale=tab.x_scale+tab.y_scale, update=True, level=tab.level, mappings=self.mapping)

    def set_all(self, val):
        for var in self.vars: var.set(val)