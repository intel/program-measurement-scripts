import os
import pandas as pd
from capeplot import CapeData
from summarize import summary_report_df
from aggregate_summary import aggregate_runs_df
from metric_names import KEY_METRICS, SUMMARY_METRICS, ANALYTICS_METRICS, MetricName

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

    def set_summary_df(self, summaryDf):
        self.summaryDf = summaryDf
        return self
    
    def set_level(self, level):
        self.level = level
        return self
    
    def compute_impl(self, df):
        aggDf, self.mapping = aggregate_runs_df(self.summaryDf.copy(deep=True), 
                                                level=self.level, name_file=self.short_names_path)
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
        if MetricName.SHORT_NAME in df.columns:
            naMask = df[MetricName.SHORT_NAME].isna()
            df.loc[naMask, MetricName.SHORT_NAME] = df.loc[naMask, MetricName.NAME] 
        return df 

    def output_args(self):
        input_args, output_args = self.input_output_args()
        return output_args

class AnalyticsData(MetaData): 
    def __init__(self, df):
        super().__init__(df) 

    def input_output_args(self):
        input_args = []
        output_args = ANALYTICS_METRICS
        return input_args, output_args