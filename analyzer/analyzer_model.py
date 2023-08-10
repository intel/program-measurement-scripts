import os
import capelib as cl
import re
from os.path import expanduser
from summarize import compute_speedup
from compute_transitions import compute_end2end_transitions
from summarize import read_raw_data, write_raw_data, write_short_names

import pandas as pd
from capedata import AggregateData, AnalyticsData
#from capedata import ShortNameData as CapeShortNameData
from capedata import MergeShortNameData
from capedata import SummaryData
from capeplot import CapacityData, CapeData, CapePlotColor
from metric_names import ALL_METRICS, KEY_METRICS, NAME_FILE_METRICS, SHORT_NAME_METRICS
from metric_names import MetricName as MN
from metric_names import NonMetricName as NMN
from sat_analysis import do_sat_analysis, SatAnalysisSettings 
from generate_SI import SiData
from pathlib import Path
from capeplot import CapePlot
from capeplot import NodeWithUnitData
from generate_SI import NODE_UNIT_DICT

from utils import Observable
from utils import resource_path as gui_resource_path


class SatAnalysisData(NodeWithUnitData):
  def __init__(self, df):
    super().__init__(df, NODE_UNIT_DICT) 
    self.sat_settings = SatAnalysisSettings(compute_stats=False)

  def compute_impl(self, df):
    # Read the optimal data file
    optimal_data_path = gui_resource_path(os.path.join('clusters', 'LORE-Optimal.csv'))
    optimal_data_df = pd.read_csv(optimal_data_path)
    self.cluster_df, si_df, _ = do_sat_analysis(optimal_data_df, df, self.sat_settings)
    si_df[NMN.SI_TIER_NORMALIZED] = si_df[NMN.SI_TIER_NORMALIZED].astype(float)
    return si_df

  def set_chosen_node_set(self, chosen_node_set):
      super().set_chosen_node_set(chosen_node_set)
      self.sat_settings.set_chosen_node_set(self.chosen_node_set)
      return self

  # Return (expected inputs, expected outputs)
  def input_output_args(self):
    #input_args = SiData.capacities(self.chosen_node_set)+[MN.SHORT_NAME]+ALL_NODE_LIST+[MN.CAP_ALLMAX_GB_P_S] + SW_BIAS_IP
    input_args = self.sat_settings.input_columns()
    output_args = self.sat_settings.output_columns()
    return input_args, output_args


  # Subclass override to set the fields give more data
  def extra_data_to_restore(self, more_data):
    self.cluster_df = more_data.pop()
    assert len(more_data) == 0
    
  # Subclass override to provide more data to be written
  def extra_data_to_save(self):
    return [self.cluster_df]


class PausableObserable(Observable):
    '''Hideable GUI State tracks whether GUI data is hidden and will delay notifcation until exposed.'''
    def __init__(self):
        super().__init__()
        # it is always safe to set this to False 
        self._paused = False
        self.notified = False

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False
        # May trigger notification if being notified before
        if self.notified:
            self.notify_observers()
        
    def notify_observers(self):
        if self._paused:
            print('Delayed notification')
            self.notified = True
            return
        super().notify_observers()
        # Reset to False after handling the notification.
        self.notified = False



class LoadedData(Observable):
        
    class PerLevelData(PausableObserable):
        def __init__(self, loadedData, level):
            super().__init__()
            self.level = level
            self.loadedData = loadedData
            #self._df = pd.DataFrame(columns=KEY_METRICS)
            self._dfs = []
            self._shortnameDataItems = []
            self._capacityDataItems = []
            self._satAnalysisDataItems = []
            self._siDataItems = [] 
            # Put this here but may move it out.
            self.guiState = PerLevelGuiState(self, level)

        # Also pause for guiState
        def pause(self):
            super().pause()
            self.guiState.pause()

        # Also resume for guiState
        def resume(self):
            super().resume()
            self.guiState.resume()
            

        @classmethod
        def update_list(cls, lst, data, append):
            if not append:
                lst.clear()
            lst.append(data)
            return data
            
        class LevelShortNameData(MergeShortNameData):
            def __init__(self, df, levelData):
                super().__init__(df) 
                self.levelData = levelData
                
            @property
            def merge_df(self):
                return self.levelData.short_names_df 
            
        def setup_df(self, df, append, short_names_path):
            df = self.update_list(self._dfs, df, append)
            #self.update_list(self._shortnameDataItems, CapeShortNameData(df).set_filename(short_names_path).compute(), append)
            self.update_list(self._shortnameDataItems, LoadedData.PerLevelData.LevelShortNameData(df, self).compute(), append)
            self.update_list(self._capacityDataItems, CapacityData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'capacity-{self.level}'), append)
            satAnalysisData = self.update_list(self._satAnalysisDataItems, SatAnalysisData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'sat_analysis-{self.level}'), append)

            cluster_df = satAnalysisData.cluster_df
            CapacityData(cluster_df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'cluster-{self.level}') 
            self.update_list(self._siDataItems, SiData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).set_norm("row").set_cluster_df(cluster_df).compute(f'si-{self.level}'), append)
            initial_color_map = self.df[KEY_METRICS]
            initial_color_map['Color'] = None
            initial_color_map['Label'] = ''
            initial_color_map['Alphas'] = ''
            self.guiState.set_color_map(initial_color_map, notify=False)
            self.updated_notify_observers()
            
        @property
        def common_columns_start(self):
            return self.loadedData.common_columns_start
        
        @property
        def common_columns_end(self):
            return self.loadedData.common_columns_end

        @property
        def source_title(self):
            return self.loadedData.source_title

        @property
        def short_names_path(self):
            return self.loadedData.short_names_path
        
        @property
        def short_names_df(self):
            return pd.merge(left=self.loadedData.short_names_df, right=self.df[KEY_METRICS], on=KEY_METRICS, how='right')
            #return self.loadedData.short_names_df

        @property
        def mapping_df(self):
            before = pd.merge(left=self.df[KEY_METRICS], right=self.loadedData.mappings_df, left_on=KEY_METRICS, right_on=['Before Name', 'Before Timestamp'], 
                            how='inner').drop(columns=KEY_METRICS)
            return pd.merge(left=self.df[KEY_METRICS], right=before, left_on=KEY_METRICS, right_on=['After Name', 'After Timestamp'], 
                                how='inner').drop(columns=KEY_METRICS)
        
        @property
        def df(self):
            if len(self._dfs) == 0:
                return pd.DataFrame()
            return pd.concat(self._dfs, ignore_index=True)

        @property
        def capacityDataItems(self):
            return self._capacityDataItems

        @property
        def satAnalysisDataItems(self):
            return self._satAnalysisDataItems

        @property
        def siDataItems(self):
            return self._siDataItems

        def clear_df(self):
            self._dfs.clear()
            self._capacityDataItems.clear()
            self._satAnalysisDataItems.clear()
            self._siDataItems.clear()
            self.guiState.reset_state()
        
        def resetStates(self):
            self.clear_df()
            #for col in KEY_METRICS:
            #    self.df[col] = None

        @property
        def color_map(self):
            return self.guiState.get_color_map()

        def update_colors(self, df):
            self.guiState.set_color_map(df[KEY_METRICS+['Label', 'Color']])

        def update_mapping(self):
            self.updated_notify_observers()

        def update_short_names(self):
            for item in self._shortnameDataItems:
                # Will reread short name files (should have been updated)
                item.compute() 
            # self.guiState.set_color_map(self.short_names_df[KEY_METRICS+['Label', 'Color']])
            self.updated_notify_observers()
            
        def merge_metrics(self, df, metrics):
            #metrics.extend(KEY_METRICS)
            for target_df in self._dfs:
                cl.import_dataframe_columns(target_df, df, metrics)


            # Incorporated following implementation in capelib.py already but keep it here for reference
            # # as there is some minor difference still.  Will delete later when code is stablized.
            # merged = pd.merge(left=target_df, right=df[metrics], on=KEY_METRICS, how='left')
            # target_df.sort_values(by=NAME, inplace=True)
            # target_df.reset_index(drop=True, inplace=True)
            # merged.sort_values(by=NAME, inplace=True)
            # merged.reset_index(drop=True, inplace=True)
            # for metric in metrics:
            #     if metric + "_y" in merged.columns and metric + "_x" in merged.columns:
            #         merged[metric] = merged[metric + "_y"].fillna(merged[metric + "_x"])
            #     if metric not in KEY_METRICS: target_df[metric] = merged[metric]
        def exportShownDataRawCSV(self, outfilename, sources):
            raw_df = pd.DataFrame()  # empty df as start and keep appending in loop next
            for src in sources:
                raw_df = raw_df.append(read_raw_data(src), ignore_index=True)
            # TODO: Need to filter out hidden rows.
            hidden=self.guiState.get_hidden_mask(raw_df)
            raw_df = raw_df[~hidden]
            write_raw_data(outfilename, raw_df)
            sname_df = pd.merge(left=self.df[KEY_METRICS+SHORT_NAME_METRICS], right=raw_df[KEY_METRICS], on=KEY_METRICS, how='right')
            # write short name files if short name not the same as Name
            if not sname_df[MN.NAME].equals(sname_df[MN.SHORT_NAME]):
                # remove extension twice to remove ".raw.csv" extension
                basic_path= os.path.splitext(os.path.splitext(outfilename)[0])[0]
                out_shortname = basic_path + ".names.csv"
                write_short_names(out_shortname, sname_df)


    def updated_all_levels_notify_observers(self):
        for level in self.allLevels:
            self.levelData[level].updated_notify_observers()

    def clear(self):
        self.sources = []
        self.analytics = pd.DataFrame()
        self.names = pd.DataFrame()
        for level in self.levelData:
            self.levelData[level].clear_df()

    def setUrl(self, url):
        if url: 
            self.urls = [url]

    def appendUrl(self, url):
        if url: 
            self.urls.append(url)
    
    def setSource(self, source):
        self.sources = [source]
    
    def appendSource(self, source):
        self.sources.append(source)

    def loadFile(self, choice, data_dir, source, url):
        if choice == 'Open Webpage':
            self.clear()
            self.setUrl(url)
        elif choice == 'Overwrite':
            self.clear()
            self.setUrl(url)
            self.setSource(source)
            self.add_data(self.sources, data_dir, append=False)
        elif choice == 'Append':
            self.appendUrl(url)
            self.appendSource(source)
            self.add_data(self.sources, data_dir, append=True)

        
        
    #CHOSEN_NODE_SET = set(['L1','L2','L3','RAM','FLOP','VR','FE'])
    # Need to get all nodes as SatAnalysis will try to add any nodes in ALL_NODE_SET
    CHOSEN_NODE_SET = CapacityData.ALL_NODE_SET
    def __init__(self):
        super().__init__()
        self.allLevels = ['Codelet',  'Source', 'Application']
        self.levelData = { lvl : LoadedData.PerLevelData(self, lvl) for lvl in self.allLevels }
        self.data_items=[]
        self.sources=[]
        self.common_columns_start = [MN.NAME, MN.SHORT_NAME, MN.COVERAGE_PCT, MN.TIME_APP_S, MN.TIME_LOOP_S, MN.CAP_FP_GFLOP_P_S, 
                                     MN.COUNT_OPS_FMA_PCT, MN.COUNT_INSTS_FMA_PCT, MN.VARIANT, MN.MEM_LEVEL]
        self.common_columns_end = [MN.RATE_INST_GI_P_S, MN.TIMESTAMP, 'Color']
        self.src_mapping = pd.DataFrame()
        self.app_mapping = pd.DataFrame()
        self.analytics = pd.DataFrame()
        self.names = pd.DataFrame()
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.short_names_path = os.path.join(self.cape_path, 'short_names.csv')
        self.mappings_path = os.path.join(self.cape_path, 'mappings.csv')
        self.analysis_results_path = os.path.join(self.cape_path, 'Analysis Results')
        self.check_cape_paths()
        self.resetStates()
        self.data = {}
        self.restore = False
        self.removedIntermediates = False
        self.transitions = 'disabled'
        self.urls = []
        self.short_names_df = pd.read_csv(self.short_names_path)
        self.mappings_df = pd.read_csv(self.mappings_path)

    def get_df(self, level):
        return self.levelData[level].df

    def get_mapping(self, level):
        return self.levelData[level].mapping

    def setFilter(self, level, metric, minimum, maximum, names, variants):
        self.levelData[level].guiState.setFilter(metric, minimum, maximum, names, variants)

    def updateLabels(self, metrics, level):
        self.levelData[level].updateLabels(metrics)

    def update_colors(self, df, level):
        self.levelData[level].update_colors(df)

    def remove_mapping(self, level, toRemove):
        # Remove from local database
        self.mappings_df = self.mappings_df.drop(self.mappings_df[(self.mappings_df['Before Name'] == toRemove['Before Name'].iloc[0]) & \
                                                                  (self.mappings_df['Before Timestamp'] == toRemove['Before Timestamp'].iloc[0]) & \
                                                                  (self.mappings_df['After Name'] == toRemove['After Name'].iloc[0]) & \
                                                                  (self.mappings_df['After Timestamp'] == toRemove['After Timestamp'].iloc[0])].index)
        self.mappings_df.to_csv(self.mappings_path, index=False)
        # Notify observers
        self.levelData[level].update_mapping()

    def add_mapping(self, level, toAdd):
        # Add to local database
        self.mappings_df = pd.concat([self.mappings_df, toAdd]).drop_duplicates(['Before Timestamp', 'Before Name', 'After Timestamp', 'After Name']).reset_index(drop=True)
        self.mappings_df.to_csv(self.mappings_path, index=False)
        # Notify observers
        self.levelData[level].update_mapping()

    def update_short_names(self, new_short_names, level):
        # Update local database
        new_df = pd.concat([self.short_names_df, new_short_names]).drop_duplicates(KEY_METRICS, keep='last').reset_index(drop=True)
        if new_df[KEY_METRICS+SHORT_NAME_METRICS].sort_values(by=KEY_METRICS, ignore_index=True).fillna('').equals(
            self.short_names_df[KEY_METRICS+SHORT_NAME_METRICS].sort_values(by=KEY_METRICS, ignore_index=True).fillna('')):
            return  # No change
        self.short_names_df = new_df
        self.short_names_df.to_csv(self.short_names_path, index=False)
        # Notify observers
        self.levelData[level].update_short_names()
    
    def check_cape_paths(self):
        if not os.path.isfile(self.short_names_path):
            Path(self.cape_path).mkdir(parents=True, exist_ok=True)
            #open(self.short_names_path, 'wb') 
            pd.DataFrame(columns=KEY_METRICS+NAME_FILE_METRICS+ ['Label']).to_csv(self.short_names_path, index=False)
        if not os.path.isfile(self.mappings_path):
            open(self.mappings_path, 'wb')
            pd.DataFrame(columns=['Before Name', 'Before Timestamp', 'After Name', 'After Timestamp', 'Before Variant', 'After Variant', 
                                  MN.SPEEDUP_TIME_LOOP_S, MN.SPEEDUP_TIME_APP_S, MN.SPEEDUP_RATE_FP_GFLOP_P_S, 'Difference']).to_csv(self.mappings_path, index=False)
        if not os.path.isdir(self.analysis_results_path):
            Path(self.analysis_results_path).mkdir(parents=True, exist_ok=True)

    def meta_filename(self, ext):
        data_dir = self.data_dir
        # data_dir is timestamped directory /path/to/datafile/<timestamp>
        # so dropped <timesampt> will get back datafile 
        datafile = os.path.basename(os.path.dirname(data_dir))
        return os.path.join(data_dir, re.sub(r'\.xlsx$|\.raw\.csv$', '', datafile)+ext)
        
    def set_meta_data(self):
        data_dir = self.data_dir
        if not data_dir:
            return
        datafile = os.path.basename(os.path.dirname(data_dir))
        shortnamefile = self.meta_filename('.names.csv')
        names = pd.read_csv(shortnamefile) if os.path.isfile(shortnamefile) else pd.DataFrame(columns=KEY_METRICS + NAME_FILE_METRICS)
        # Only add entries not already in self.short_names_df
        if not set(names.columns).issuperset(set(KEY_METRICS+NAME_FILE_METRICS)):
            # Skip if shortname file not compatible
            return
        merged = pd.merge(left=self.short_names_df, right=names, on=KEY_METRICS, how='outer')
        updated = False
        for n in NAME_FILE_METRICS:
            need_update = merged[n+'_x'].isna()  
            merged.loc[need_update, n+'_x'] = merged.loc[need_update, n+'_y']
            updated = updated | need_update

        if updated.any():
            # For key metrics, move them as is
            for n in KEY_METRICS:
                self.short_names_df[n] = merged[n]
            # For short name metrics, move the merged metrics *_x to db
            for n in NAME_FILE_METRICS:
                self.short_names_df[n] = merged[n+'_x']
            self.short_names_df.to_csv(self.short_names_path, index=False)

    # TODO: remove this property
    @property
    def summaryDf(self):
        return self.get_df('Codelet')

    def resetStates(self):
        # Track points/labels that have been hidden/highlighted by the user
        self.c_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.s_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        self.a_plot_state = {'hidden_names' : [], 'highlighted_names' : []}
        for level in self.allLevels:
            self.levelData[level].resetStates()

    def exportShownDataRawCSV(self, outfilename):
        # Will only export codelet level data
        self.levelData['Codelet'].exportShownDataRawCSV(outfilename, self.sources)
    
    def add_data(self, sources, data_dir='', append=False):
        self.restore = False
        if not append: self.resetStates() # Clear hidden/highlighted points from previous plots (Do we want to do this if appending data?)        
        # NOTE: sources is a list of loaded file and the last one is to be loaded
        # data_dir is the data directory of the last one which is to be loaded
        self.sources = sources
        # Get data file name and timestamp for plot title
        self.source_title = sources[0].split('\\')[-4:-3][0] + ":" + sources[0].split('\\')[-3:-2][0] + ':' + sources[0].split('\\')[-2:-1][0]
        last_source = sources[-1]  # Get the last source to be loaded
        self.data_dir = data_dir

        # Add meta data from the timestamp directory.  Will read short names to global database
        self.set_meta_data()

        # Get path to short name database
        short_names_path = self.short_names_path if os.path.isfile(self.short_names_path) else None

        CapeData.set_cache_dir(self.data_dir)

        dfs = { n : pd.DataFrame(columns = KEY_METRICS) for n in self.allLevels }
        summaryDf = dfs['Codelet']
        srcDf = dfs['Source']
        appDf = dfs['Application']
        SummaryData(summaryDf).set_sources([last_source]).set_short_names_path(short_names_path).compute('summary-Codelet')
        AnalyticsData(summaryDf).set_filename(self.meta_filename('.analytics.csv')).compute()
        AggregateData(srcDf).set_summary_df(summaryDf).set_level('src').set_short_names_path(short_names_path).set_short_names_df(self.short_names_df).compute('summary-Source')
        AggregateData(appDf).set_summary_df(summaryDf).set_level('app').set_short_names_path(short_names_path).set_short_names_df(self.short_names_df).compute('summary-Application')
        # Fill the extra columns in summary but not aggregated by None
        for extra in summaryDf.columns:
            if extra not in srcDf.columns: srcDf[extra] = None
            if extra not in appDf.columns: appDf[extra] = None
        
        for level in self.levelData:
            df = dfs[level]
            self.levelData[level].setup_df(df, append, short_names_path)
            # df[MetricName.CAP_FP_GFLOP_P_S] = df[RATE_FP_GFLOP_P_S]

            # levelData.capacityData = CapacityData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'capacity-{level}')
            # levelData.satAnalysisData = SatAnalysisData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'sat_analysis-{level}')

            # cluster_df = levelData.satAnalysisData.cluster_df
            # CapacityData(cluster_df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET).compute(f'cluster-{level}') 
            # levelData.siData = SiData(df).set_chosen_node_set(LoadedData.CHOSEN_NODE_SET)\
            #     .set_norm("row").set_cluster_df(cluster_df).compute(f'si-{level}')

            # cl.append_dataframe_rows(self.get_df(level), df)
            # Add mappings to levelData for each level
            # self.loadMapping(level)

        # TODO: Append other levels?
        self.names = summaryDf[KEY_METRICS+NAME_FILE_METRICS]

        # Add diagnostic variables from analyticsDf
        #self.common_columns_end = [RATE_INST_GI_P_S, TIMESTAMP, 'Color']

        self.updated_notify_observers()


    @staticmethod
    def append_df(df, append_df):
        merged = df.append(append_df, ignore_index=True)
        cl.replace_dataframe_content(df, merged)
    
    def add_saved_data(self, levels=[]):
        gui.oneviewTab.removePages()
        gui.loaded_url = None
        self.resetStates()
        self.levels = {'Codelet' : levels[0], 'Source' : levels[1], 'Application' : levels[2]}
        self.summaryDf = self.levels['Codelet']['summary']
        self.srcDf = self.levels['Source']['summary']
        self.appDf = self.levels['Application']['summary']
        self.mapping = self.levels['Codelet']['mapping']
        self.src_mapping = self.levels['Source']['mapping']
        self.app_mapping = self.levels['Application']['mapping']
        self.analytics = pd.DataFrame()
        self.sources = []
        self.restore = True
        # Notify the data for all the plots with the saved data 
        for level in self.levels:
            for observer in self.observers:
                if observer.name in self.levels[level]['data']:
                    observer.notify(self, x_axis=self.levels[level]['data'][observer.name]['x_axis'], y_axis=self.levels[level]['data'][observer.name]['y_axis'], \
                        scale=self.levels[level]['data'][observer.name]['x_scale'] + self.levels[level]['data'][observer.name]['y_scale'], level=level, mappings=self.levels[level]['mapping'])

    def add_speedup(self, mappings, df):
        if mappings.empty or df.empty:
            return
        speedup_time = []
        speedup_apptime = []
        speedup_gflop = []
        for i in df.index:
            row = mappings.loc[(mappings['Before Name']==df['Name'][i]) & (mappings['Before Timestamp']==df['Timestamp#'][i])]
            speedup_time.append(row[SPEEDUP_TIME_LOOP_S].iloc[0] if not row.empty else 1)
            speedup_apptime.append(row[SPEEDUP_TIME_APP_S].iloc[0] if not row.empty else 1)
            speedup_gflop.append(row[SPEEDUP_RATE_FP_GFLOP_P_S].iloc[0] if not row.empty else 1)
        speedup_metric = [(speedup_time, SPEEDUP_TIME_LOOP_S), (speedup_apptime, SPEEDUP_TIME_APP_S), (speedup_gflop, SPEEDUP_RATE_FP_GFLOP_P_S)]
        for pair in speedup_metric:
            df[pair[1]] = pair[0]

    def get_speedups(self, level, mappings):
        mappings = compute_speedup(self.get_df(level), mappings)
        return mappings
    
    def get_end2end(self, mappings, metric=MN.SPEEDUP_RATE_FP_GFLOP_P_S):
        newMappings = compute_end2end_transitions(mappings, metric)
        newMappings['Before Timestamp'] = newMappings['Before Timestamp'].astype(int)
        newMappings['After Timestamp'] = newMappings['After Timestamp'].astype(int)
        self.add_speedup(newMappings, self.summaryDf)
        return newMappings
    
    # def cancelAction(self):
    #     # If user quits the window we set a default before/after order
    #     self.source_order = list(self.summaryDf['Timestamp#'].unique())
    #     self.win.destroy()

    # def orderAction(self, button, ts):
    #     self.source_order.append(ts)
    #     button.destroy()
    #     if len(self.source_order) == len(self.sources):
    #         self.win.destroy()

    # def get_order(self):
    #     self.win = tk.Toplevel()
    #     center(self.win)
    #     self.win.protocol("WM_DELETE_WINDOW", self.cancelAction)
    #     self.win.title('Order Data')
    #     message = 'Select the order of data files from oldest to newest'
    #     tk.Label(self.win, text=message).grid(row=0, columnspan=3, padx=15, pady=10)
    #     # Need to link the datafile name with the timestamp
    #     for index, source in enumerate(self.sources):
    #         expr_summ_df = pd.read_excel(source, sheet_name='Experiment_Summary')
    #         ts_row = expr_summ_df[expr_summ_df.iloc[:,0]=='Timestamp']
    #         ts_string = ts_row.iloc[0,1]
    #         date_time_obj = datetime.strptime(ts_string, '%Y-%m-%d %H:%M:%S')
    #         ts = int(date_time_obj.timestamp())
    #         path, source_file = os.path.split(source)
    #         b = tk.Button(self.win, text=source_file.split('.')[0])
    #         b['command'] = lambda b=b, ts=ts : self.orderAction(b, ts) 
    #         b.grid(row=index+1, column=1, padx=20, pady=10)
    #     root.wait_window(self.win)

    def loadMapping(self, level):
        df = self.get_df(level)
        before = pd.merge(left=df[KEY_METRICS], right=self.mappings_df, left_on=KEY_METRICS, right_on=['Before Name', 'Before Timestamp'], 
                          how='inner').drop(columns=KEY_METRICS)
        mappings = pd.merge(left=df[KEY_METRICS], right=before, left_on=KEY_METRICS, right_on=['After Name', 'After Timestamp'], 
                            how='inner').drop(columns=KEY_METRICS)
        if not mappings.empty:
            # Add variants from summary to mappings
            mappings = self.addMappingVariants(level, mappings)
            self.get_speedups(level, mappings)
        # self.add_speedup(self.mapping, self.get_df('Codelet'))
        self.levelData[level].mapping = mappings

    def addMappingVariants(self, level, mappings):
        df = self.get_df(level)  
        mappings.drop(columns=['Before Variant', 'After Variant'], inplace=True, errors='ignore')
        mappings = pd.merge(mappings, df[KEY_METRICS + [MN.VARIANT]], \
            left_on=['Before Name', 'Before Timestamp'], right_on=KEY_METRICS, \
            how='inner').drop(columns=KEY_METRICS).rename(columns={MN.VARIANT:'Before Variant'})
        mappings = pd.merge(mappings, df[KEY_METRICS + [MN.VARIANT]], \
            left_on=['After Name', 'After Timestamp'], right_on=KEY_METRICS,  \
            how='inner').drop(columns=KEY_METRICS).rename(columns={MN.VARIANT:'After Variant'})
        return mappings

    # def createMappings(self, df):
    #     mappings = pd.DataFrame()
    #     df['map_name'] = df['Name'].map(lambda x: x.split(' ')[1].split(',')[-1].split('_')[-1])
    #     before = df.loc[df['Timestamp#'] == self.source_order[0]]
    #     after = df.loc[df['Timestamp#'] == self.source_order[1]]
    #     for index in before.index:
    #         match = after.loc[after['map_name'] == before['map_name'][index]].reset_index(drop=True) 
    #         if not match.empty:
    #             match = match.iloc[[0]]
    #             match['Before Timestamp'] = before['Timestamp#'][index]
    #             match['Before Name'] = before['Name'][index]
    #             match['before_short_name'] = before['Short Name'][index]
    #             match['After Timestamp'] = match['Timestamp#']
    #             match['After Name'] = match['Name']
    #             match['after_short_name'] = match['Short Name']
    #             match = match[['Before Timestamp', 'Before Name', 'before_short_name', 'After Timestamp', 'After Name', 'after_short_name']]
    #             mappings = mappings.append(match, ignore_index=True)
    #     if not mappings.empty:
    #         mappings = self.get_speedups(mappings)
    #         self.all_mappings = self.all_mappings.append(mappings, ignore_index=True)
    #         self.all_mappings.to_csv(self.mappings_path, index=False)
    #     return mappings

    # def addShortNames(self, level):
    #     all_short_names = pd.read_csv(self.short_names_path)
    #     self.merge_metrics(all_short_names, [SHORT_NAME, 'Color'], level)

    def merge_metrics(self, df, metrics, level):
        # Add metrics computed in plot functions to master dataframe
        self.levelData[level].merge_metrics(df, metrics)



class PerLevelGuiState(PausableObserable):
    def __init__(self, levelData, level):
        super().__init__()
        self.level = level
        self.levelData = levelData
        # Should have size <= 3
        self.labels = []
        self.hidden = []
        self.highlighted = []
        self.selected = []
        self.label_visibility = {}
        # For data filtering
        # The following variants and filter metric set up a mask to select data point
        self.selectedVariants = []
        self.filterMetric = None
        self.filterMinThreshold = 0
        self.filterMaxThreshold = 0
        self.hidden_mask = []

        # Currently selected plot interaction action
        self.selectPoint = True
        self.showHiddenPointInTable = False
        self.action_selected = 'Choose Action'

        # The final mask used to select data points
        self.selectedDataPoints = []

        # A map from color to color name for plotting
        self.color_map = pd.DataFrame(columns=KEY_METRICS + ['Label', 'Color'])

        # Cape paths
        self.cape_path = os.path.join(expanduser('~'), 'AppData', 'Roaming', 'Cape')
        self.short_names_path = os.path.join(self.cape_path, 'short_names.csv')
        self.mappings_path = os.path.join(self.cape_path, 'mappings.csv')
        # Column order for data table display.  All except KEY_METRICS.
        self.nonKeyColumnOrder = [m for m in ALL_METRICS if m not in KEY_METRICS] 
        self.guiDataDict = {}

    def setSelectPoint(self, value):
        self.selectPoint = value
    
    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't save observers as they are GUI components
        del state['observers']
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore observers to []
        self.observers = []

    def findOrCreateGuiData(self, guiDataClass):
        if guiDataClass not in self.guiDataDict:
            self.guiDataDict[guiDataClass] = guiDataClass(self.levelData, self.level)
        return self.guiDataDict[guiDataClass]
    
    def moveColumnsFirst(self, columns):
        columns = [column for column in columns if column in self.columnOrder]
        if columns:
            self.nonKeyColumnOrder = columns+[m for m in self.nonKeyColumnOrder if m not in columns]
            self.updated_notify_observers()
        
    @property
    def columnOrder(self):
        # Make SHORT_NAME just after KEY_METRICS
        return KEY_METRICS + [MN.SHORT_NAME] + [c for c in self.nonKeyColumnOrder if c != MN.SHORT_NAME]

    # Only do this for non-hidden points
    def setLabelAlphas(self, names, alpha, notify=True):
        for name in set(names)-set(self.hidden):
            self.label_visibility[name] = alpha
        if notify:
            self.updated_notify_observers()

    def toggleLabelData(self, nameTimestampDf, notify=True):
        for name in self.get_encoded_names(nameTimestampDf).tolist():
            self.toggleLabel(name, notify=False)
        if notify:
            self.updated_notify_observers()

    def toggleLabel(self, name, notify=True):
        if name not in self.label_visibility:
            self.label_visibility[name] = 0
        self.setLabelAlpha(name, int(not self.label_visibility[name]), notify)
    
    def setLabelAlpha(self, name, alpha, notify=True):
        self.label_visibility[name] = alpha
        if notify:
            self.updated_notify_observers()

    def set_color_map(self, color_map_df, notify=True):
        if 'Label' not in color_map_df: color_map_df['Label'] = ''
        naMask = color_map_df['Color'].isna()
        # needed .value possibly due to a Pandas bug
        # See:https://stackoverflow.com/questions/24188729/pandas-adding-a-series-to-a-dataframe-causes-nan-values-to-appear
        color_map_df.loc[naMask,'Color']=pd.Series([CapePlotColor.DEFAULT_COLOR]*len(color_map_df[naMask])).values
        #color_map_df.fillna({'Color': CapePlotColor.DEFAULT_COLOR}, inplace=True)
        self.color_map = color_map_df
        if notify:
            self.updated_notify_observers()

    def get_color_map(self):
        return self.color_map
    
    # Write methods to update the fields and then call 
    # self.loadedData.levelData[level].updated() to notify all observers
    def reset_labels(self):
        self.labels = []
        self.updated_notify_observers()

    def setFilterMask(self, hidden_mask):
        self.hidden_mask = hidden_mask
        df = self.levelData.df[hidden_mask]
        self.hidden = list(dict.fromkeys((df[MN.NAME]+df[MN.TIMESTAMP].astype(str)).tolist()))
        self.showLabels()
        self.hideLabels(self.hidden)
        self.updated_notify_observers()

    def setFilter(self, metric, minimum, maximum, names, variants):
        self.filterMetric = metric
        self.filterMinThreshold = minimum
        self.filterMaxThreshold = maximum
        self.selectedVariants = variants
        self.hidden = names
        # Add codelet names outside of filtered range to hidden names
        hidden_mask = [val in names for val in (self.levelData.df[MN.NAME]+self.levelData.df[MN.TIMESTAMP].astype(str))]
        if metric:
            hidden_mask |= self.levelData.df[metric] < minimum
            hidden_mask |= self.levelData.df[metric] > maximum
        self.setFilterMask(hidden_mask)

    def removePoints(self, names):
        self.hidden.extend(names)
        self.hidden = list(dict.fromkeys(self.hidden))
        for name in names:
            self.label_visibility[name] = 0
        self.updated_notify_observers()

    # remove data with provided name and timestamp info
    def removeData(self, nameTimestampDf):
        self.removePoints(self.get_encoded_names(nameTimestampDf).tolist())

    def highlightData(self, nameTimestampDf):
        self.highlightPoints(self.get_encoded_names(nameTimestampDf).tolist())

    def unhighlightData(self, nameTimestampDf):
        self.unhighlightPoints(self.get_encoded_names(nameTimestampDf).tolist())

    def selectPoints(self, names):
        self.selected = names
        self.updated_notify_observers()

    def showPoints(self, names):
        self.hidden = [name for name in self.hidden if name not in names]
        for name in names:
            self.label_visibility[name] = 1
        self.updated_notify_observers()

    def isHidden(self, name):
        return name in self.hidden

    def hideLabels(self, names):
        for name in names:
            self.label_visibility[name] = 0

    def showLabels(self):
        for name in self.label_visibility:
            self.label_visibility[name] = 1
    
    def labelVisbility(self, name):
        alpha = 1
        if name in self.label_visibility:
            alpha = self.label_visibility[name]
        return alpha

    def highlightPoints(self, names):
        self.highlighted.extend(names)
        self.highlighted = list(dict.fromkeys(self.highlighted))
        self.updated_notify_observers()

    def unhighlightPoints(self, names):
        self.highlighted = [name for name in self.highlighted if name not in names]
        self.updated_notify_observers()

    def setLabels(self, metrics):
        self.labels = metrics
        self.updated_notify_observers()

    def reset_state(self):
        self.hidden = []
        self.highlighted = []

    def get_encoded_names(self, df):
        return df[MN.NAME] + df[MN.TIMESTAMP].astype(str)

    def get_hidden_mask(self, df):
        return self.get_encoded_names(df).isin(self.hidden)

    def get_highlighted_mask(self, df):
        return self.get_encoded_names(df).isin(self.highlighted)

    def get_selected_mask(self, df):
        return self.get_encoded_names(df).isin(self.selected)
        

    # Plot interaction objects for each plot at this level will be notified to avoid a complete redraw

class AnalyzerData(PausableObserable):
    def __init__(self, levelData, level, name):
        super().__init__()
        self.levelData = levelData
    #    self.mappings = pd.DataFrame()
        self.level = level
        self.name = name
        #self.gui = gui
        #self.root = root
        # Watch for updates in loaded data
        #levelData.loadedData.add_observer(self)
        #levelData.add_observer(self)

    # Make df a property that refer to the right dataframe
    @property
    def df(self):
        # Get correct dataframe
        return self.levelData.df

    def __getstate__(self):
        state = self.__dict__.copy()
        # Don't save observers as they are GUI components
        del state['observers']
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore observers to []
        self.observers = []

    # @property
    # def guiState(self):
    #     return self.loadedData.levelData[self.level].guiState

    @property
    def mappings(self):
        return self.levelData.mapping_df

    @property
    def variants(self):
        return self.levelData.guiState.selectedVariants

    @property
    def common_columns_start(self):
        return self.levelData.common_columns_start

    @property
    def common_columns_end(self):
        return self.levelData.common_columns_end

    @property
    def short_names_path(self):
        return self.levelData.short_names_path

    @property
    def guiState(self):
        return self.levelData.guiState

    @property
    def columnOrder(self):
        return self.levelData.guiState.columnOrder

    # Move need to move this to controller class (Plot interaction?)
    def moveColumnsFirst(self, columns):
        self.levelData.guiState.moveColumnsFirst(columns)

    def setFilter(self, metric, minimum, maximum, names, variants):
        self.levelData.guiState.setFilter(metric, minimum, maximum, names, variants)

    @property
    def capacityDataItems(self):
        return self.levelData.capacityDataItems

    @property
    def siDataItems(self):
        return self.levelData.siDataItems
        
    @property
    def satAnalysisDataItems(self):
        return self.levelData.satAnalysisDataItems

    def notify(self, loadedData):
        print(f"{self.name} Notified from ", loadedData)
        self.updated_notify_observers()

        
    def merge_metrics(self, df, metrics):
        self.levelData.merge_metrics(df, metrics)

