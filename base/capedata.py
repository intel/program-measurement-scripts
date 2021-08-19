import os
import pickle
from abc import ABC, abstractmethod

import networkx as nx
import pandas as pd

from aggregate_summary import aggregate_runs_df
from metric_names import (ANALYTICS_METRICS, KEY_METRICS, SHORT_NAME_METRICS,
                          SUMMARY_METRICS, MetricName)
from summarize import summary_report_df
import warnings


# Base class for plot data without GUI specific data
# Subclass should override for plot specific data processing.
class CapeData(ABC):
    AllCapeDataItems = []
    DepGraph = nx.DiGraph()

    def __init__(self, df):
        self._df = df
        self.cache_file = None
        CapeData.AllCapeDataItems.append(self)

    
    # Getter of df
    @property
    def df(self):
        return self._df
    
    # # Setter of df (remove so cannot change it)
    # @df.setter
    # def df(self, v):
    #     self._df = v

    cache_dir = None
    # Class variable to remember path to cache data file
    # Set to None to reset
    @classmethod
    def set_cache_dir(cls, data_dir):
        cls.cache_dir = data_dir

    @classmethod
    def clear_dependency_info(cls, self):
        cls.AllCapeDataItems.clear()
        cls.DepGraph = nx.DiGraph()

    def record_dependency(self):
        inSet = set(self.input_args())
        outSet = set(self.output_args())
        for node in self.AllCapeDataItems:
            if node == self:
                continue
            if node.df is not self.df:
                continue
            nodeToItemMetrics = set(node.output_args()) & inSet
            if nodeToItemMetrics and not self.DepGraph.has_edge(node, self):
                self.DepGraph.add_edge(node, self, metrics=nodeToItemMetrics)
            itemToNodeMetrics = set(node.input_args()) & outSet
            if itemToNodeMetrics and not self.DepGraph.has_edge(self, node):
                self.DepGraph.add_edge(self, node, metrics=itemToNodeMetrics)
                
            


    @classmethod
    def invalidate_metrics(cls, metrics, itemPool=None):
        itemPool = cls.AllCapeDataItems if itemPool is None else itemPool
        metricSet = set(metrics)
        invalidateItems = set([item for item in itemPool if set(item.input_args()) & metricSet])
        invalidateItems = invalidateItems | set().union(*[nx.descendants(cls.DepGraph, item) for item in invalidateItems])

        # while updated:
        #     invalidateItems = [item for item in cls.AllCapeDataItems if set(item.input_args()) & metricSet]
        #     newMetricSet = set().union(*[item.output_args() for item in invalidateItems]) | metricSet
        #     updated = not newMetricSet.equals(metricSet)
        #     metricSet = newMetricSet
        # Now we have collected all teams to be invalidated
        for item in invalidateItems:
            # only invalidate cache for now
            # TODO: may want to recompute data in topoligical order
            item.invalidate_cache()
        
        
    def invalidate_cache(self):
        cache_file = self.cache_file 
        if cache_file and os.path.isfile(cache_file):
            os.remove(cache_file)
            self.cache_file = None

    # Subclass could override to read more data
    def try_read_cache(self, filename_prefix):
        cache_file = os.path.join(self.cache_dir, f'{filename_prefix}_dfs.pkl') if self.cache_dir and filename_prefix else None
        if cache_file and os.path.isfile(cache_file):
            with open(cache_file, 'rb') as cache_data:
                data_read = pickle.load(cache_data)
                df = data_read.pop()  # extra the last dataframe which is the df to return
                self.extra_data_to_restore(data_read)
                self.cache_file = cache_file
                return df
        return None

    # Subclass could override to save more data
    def try_write_cache(self, df, filename_prefix):
        cache_file = os.path.join(self.cache_dir, f'{filename_prefix}_dfs.pkl') if self.cache_dir and filename_prefix else None
        if cache_file:
            with open(cache_file, 'wb') as cache_data:
                more_data_to_write = self.extra_data_to_save()
                # df insert at the end so it can be popped by the read call
                pickle.dump(more_data_to_write + [df], cache_data)
                self.cache_file = cache_file
             
    # Subclass override to set the fields give more data
    def extra_data_to_restore(self, more_data):
        pass
    
    # Subclass override to provide more data to be written
    def extra_data_to_save(self):
        return []

    # Should check merge_metrics() in LoadedData class (they should be doing the same thing)
    def compute(self, cache_filename_prefix=None):
        # Copy-in copy-out
        inputs, outputs = self.input_output_args()
        inputs = sorted(inputs)
        outputs = sorted(outputs)

        result_df = self.try_read_cache(cache_filename_prefix)
        if result_df is None:
            copy_df = self.df[KEY_METRICS + [n for n in inputs if n not in KEY_METRICS]].copy() 
            result_df = self.compute_impl(copy_df)
            result_df = result_df[KEY_METRICS + [n for n in outputs if n not in KEY_METRICS]]
            self.try_write_cache(result_df, cache_filename_prefix)

        #result_df = result_df.astype({MetricName.TIMESTAMP: 'int64'})
        # Exclude key metrics not to be overwritten - except when self.df is empty which will be checked below
        existing_outputs = (set(self.df.columns) & set(outputs)) - set(KEY_METRICS)
        if len(existing_outputs) > 0:
            # Drop columns if there is existing columns to be overwritten
            warnings.warn("Trying to override existing columns: {}".format(existing_outputs))
            self.df.drop(columns=existing_outputs, inplace=True, errors='ignore')
        self.df.reset_index(drop=True, inplace=True)
        result_df.reset_index(drop=True, inplace=True)
        if len(self.df) > 0:
            # Not empty self.df case
            merged = pd.merge(left=self.df, right=result_df, how='left', on=KEY_METRICS)
            # Make sure join order is consistent with original self.df order
            assert self.df[MetricName.NAME].equals(merged[MetricName.NAME])

            self.df[MetricName.TIMESTAMP].astype('int64')
            merged[MetricName.TIMESTAMP].astype('int64')
            assert self.df[MetricName.TIMESTAMP].astype('int64').equals(merged[MetricName.TIMESTAMP].astype('int64'))
        else:
            # Empty self.df case, result_df must have all the KEY_METRICS
            assert set(result_df.columns) & set(KEY_METRICS) == set(KEY_METRICS) 
            merged = result_df
        updatedCols = set()
        for col in outputs:
            if col in self.df.columns and self.df[col].equals(merged[col]):
                continue # Update not needed
            try: 
                self.df[col] = merged[col]
            except:
                self.df[col] = None 
            updatedCols.add(col)
        self.record_dependency()
        # Invalidate item if they work on the same df using updatedCols metrics
        self.invalidate_metrics(updatedCols, [item for item in self.AllCapeDataItems if item.df is self.df])
        return self

    @abstractmethod
    # Process data.  Input from df and return results
    # The data processing outside will supply expected columns specified by input_output_args() method
    # On return, only the expected ouptut columns specified by input_output_args() method will be incorporated
    def compute_impl(self, df):
        return df
    
    @abstractmethod
    # Return (expected inputs, expected outputs)
    # This is a contract of the data computation
    # SEE ALSO: compute_impl()
    def input_output_args(self):
        return None, None

    def output_args(self):
        input_args, output_args = self.input_output_args()
        return output_args

    def input_args(self):
        input_args, output_args = self.input_output_args()
        return input_args


class SummaryGenerationData(CapeData):
    def __init__(self, df):
        super().__init__(df) 
        self.mapping = None
        self.short_names_path = None

    def set_short_names_path(self, short_names_path):
        self.short_names_path = short_names_path
        return self

    def input_output_args(self):
        input_args = []
        output_args = SUMMARY_METRICS
        return input_args, output_args

    # Subclass override to set the fields give more data
    def extra_data_to_restore(self, more_data):
        assert len(more_data) >= 1
        self.mapping, = more_data
        
    # Subclass override to provide more data to be written
    def extra_data_to_save(self):
        return [ self.mapping ]
    
class SummaryData(SummaryGenerationData): 
    def __init__(self, df):
        super().__init__(df) 
        self.sources = []
    
    def set_sources(self, sources):
        self.sources = sources
        return self

    def compute_impl(self, df):
        in_files = self.sources
        exts = [ os.path.splitext(src)[1] for src in in_files ]
        in_files_format = [ 'csv' if ext == '.csv' else 'xlsx' for ext in exts ]

        # in_files_format = [None] * len(sources)
        # for index, source in enumerate(sources):
        #     in_files_format[index] = 'csv' if os.path.splitext(source)[1] == '.csv' else 'xlsx'
        user_op_file = None
        request_no_cqa = False
        request_use_cpi = False
        request_skip_energy = False
        request_skip_stalls = False

        # Codelet summary
        # mapping not used 
        df, self.mapping = summary_report_df(in_files, in_files_format, user_op_file, request_no_cqa, request_use_cpi, 
                                             request_skip_energy, request_skip_stalls, self.short_names_path, False, True, None)
        
        return df 

class AggregateData(SummaryGenerationData): 
    def __init__(self, df):
        super().__init__(df) 
        self.summaryDf = None
        self.level = None
        self.short_names_df = None

    def set_summary_df(self, summaryDf):
        self.summaryDf = summaryDf
        return self
    
    def set_level(self, level):
        self.level = level
        return self

    def set_short_names_df(self, short_names_df):
        self.short_names_df = short_names_df
        return self
    
    def compute_impl(self, df):
        aggDf, self.mapping = aggregate_runs_df(self.summaryDf.copy(deep=True), 
                                                level=self.level, short_name_df=self.short_names_df)
        return aggDf

    def input_output_args(self):
        input_args, output_args = super().input_output_args()
        output_args = [out for out in output_args if out != MetricName.SRC_NAME]
        return input_args, output_args

class MetaData(CapeData): 
    def __init__(self, df):
        super().__init__(df) 
        self.filename = None
    
    def set_filename(self, filename):
        self.filename = filename
        return self
        
    def compute_impl(self, df):
        if not os.path.isfile(self.filename):
            return pd.DataFrame(columns=KEY_METRICS + self.output_args())
        data = pd.read_csv(self.filename)
        df = pd.merge(left=df, right=data, on=KEY_METRICS, how='left')
        # Use reindex function to add extra columns if needed
        df = df.reindex(columns=df.columns.tolist() + self.output_args())
        return df 

class MergeDataFrameData(CapeData):
    def __init__(self, df):
        super().__init__(df) 

    # Subclass override to provide data frame
    @property
    @abstractmethod
    def merge_df(self):
        return None 

    def compute_impl(self, df):
        if self.merge_df is None:
            return pd.DataFrame(columns=KEY_METRICS + self.output_args())
        df = pd.merge(left=df, right=self.merge_df, on=KEY_METRICS, how='left')
        return df 
    


class AnalyticsData(MetaData): 
    def __init__(self, df):
        super().__init__(df) 

    def input_output_args(self):
        input_args = []
        output_args = ANALYTICS_METRICS
        return input_args, output_args

class ShortNameData:
    def fix_up(self, df):
        naMask = df[MetricName.SHORT_NAME].isna()
        df.loc[naMask, MetricName.SHORT_NAME] = df.loc[naMask, MetricName.NAME] 
        return df
        

# Attempt to use multiple inheritance to separate handling of data source and data kind
class MetaShortNameData(MetaData, ShortNameData): 
    def __init__(self, df):
        super().__init__(df) 

    def compute_impl(self, df):
        df = super().compute_impl(df)
        return self.fix_up(df) 

    def input_output_args(self):
        input_args = []
        output_args = SHORT_NAME_METRICS
        return input_args, output_args

class MergeShortNameData(MergeDataFrameData, ShortNameData): 
    def __init__(self, df):
        super().__init__(df) 

    def compute_impl(self, df):
        df = super().compute_impl(df)
        return self.fix_up(df)

    # Subclass should still need to override merge_df(self) to provide data frame 

    def input_output_args(self):
        input_args = []
        output_args = SHORT_NAME_METRICS
        return input_args, output_args