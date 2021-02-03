import pandas as pd
import numpy as np  
import math
import sys
from metric_names import MetricName

def remove_prefix(str, prefix):
    return str.lstrip(prefix)

# rhs conversion function
def find_rhs_ops(val):
   if val <=1:
      rhs_node = 1
   else:
      rhs_node = 0
   return rhs_node

# sca ops function : used to compute effect as software negative bias
# The input is vec_ops. so subtracted from 1
def find_sca_ops(val):
   sca_ops_wt = 1
   return sca_ops_wt*(1- val/100)

# fma conversion function : used to compute effect as Positive bias
def find_fma_ops(val):
   fma_ops_wt = 1
   return fma_ops_wt*(val/100)

# scalar conversion factor
def find_sca_factor(val):
   if 'SC=' in str(val):
      vf = 1
   else:
      vf = 0
   return vf

# vector conversion factor
def find_vec_factor(val):
   if 'YMM=' in str(val):
      vf = 1
   elif 'XMM=' in str(val):
      vf = 1
   else:
      vf = 0
   return vf

# clu function
# The array efficiency of inner-most loop is considered
#If array utilization is less that 0.5 accounted to neg bias
def find_clu_factor(clu_score):
   clu_str = str(clu_score)
    # Find the last element in the clu-score value
   clu_str = clu_str.replace(']', '')
   clu_str = clu_str.replace('[', '')
   revSplit_clu = clu_str.rsplit(',', 1)
   clu_val = 0.0
   try:
      clu_val = float(revSplit_clu[1])
   except:
      clu_val = float(revSplit_clu[0])

   if math.isnan(clu_val):
      cf = 0
   elif clu_val < 0.5:
      cf = 1
   else:
      cf = 0
   return cf

# div_ops function
def find_div_ops(div_ops):
    div_wt = 1
    return div_wt*div_ops/100

# cnvt_ops function
def find_cnvt_ops_factor(cnvt_ops):
    cnvt_wt = 1
    return cnvt_wt*cnvt_ops/100

# Recurrence conversion function
def find_recurrence_factor(val):
   if 'TRUE' in str(val):
      rf = 1
   else:
      rf = 0
   return rf

def get_short_name(name):
   return str(name)


def compute_sw_bias(mainDataFrame):

    # init result df
    sw_bias_df = pd.DataFrame()
    # Compute Vector Node
    #addAfterColumn = mainDataFrame.columns.get_loc(MetricName.RATE_FP_GFLOP_P_S) + 1
    #mainDataFrame.insert(addAfterColumn, "VN",
    #mainDataFrame[MetricName.COUNT_OPS_VEC_PCT].apply(find_vec_factor))

    # Compute Scalar Node
    #addAfterColumn = mainDataFrame.columns.get_loc(MetricName.RATE_FP_GFLOP_P_S) + 1
    #mainDataFrame.insert(addAfterColumn, "SN",
    #mainDataFrame[MetricName.COUNT_OPS_VEC_PCT].apply(find_sca_factor))

    # Compute Negative SW Bias
    addAfterColumn = mainDataFrame.columns.get_loc(MetricName.RATE_FP_GFLOP_P_S) + 1
    mainDataFrame.insert(addAfterColumn, "Neg_SW_Bias", (mainDataFrame[MetricName.COUNT_OPS_VEC_PCT].apply(find_sca_ops)
                                                   + mainDataFrame['rhs_op_count'].apply(find_rhs_ops)
                                                   + mainDataFrame['recurrence'].apply(find_recurrence_factor)
                                                   + mainDataFrame[MetricName.COUNT_OPS_CVT_PCT].apply(find_cnvt_ops_factor)
                                                   + mainDataFrame[MetricName.COUNT_OPS_DIV_PCT].apply(find_div_ops)
                                                   + mainDataFrame['clu_scores'].apply(find_clu_factor)))

    # Compute Positive SW Bias
    addAfterColumn = mainDataFrame.columns.get_loc("Neg_SW_Bias") + 1
    mainDataFrame.insert(addAfterColumn, "Pos_SW_Bias", (mainDataFrame[MetricName.COUNT_OPS_FMA_PCT].apply(find_fma_ops)))

    # Compute Net SW Bias
    addAfterColumn = mainDataFrame.columns.get_loc("Pos_SW_Bias") + 1
    mainDataFrame.insert(addAfterColumn, "Net_SW_Bias", (mainDataFrame["Pos_SW_Bias"] - mainDataFrame["Neg_SW_Bias"]))

    # Compute SW_BIAS_VEC
    sw_bias_df['ShortName'] =  mainDataFrame['ShortName'].apply(get_short_name)
    sw_bias_df['Nd_CNVT_OPS'] =  mainDataFrame[MetricName.COUNT_OPS_CVT_PCT].apply(find_cnvt_ops_factor)
    sw_bias_df['Nd_VEC_OPS'] =  mainDataFrame[MetricName.COUNT_OPS_VEC_PCT].apply(find_sca_ops)
    sw_bias_df['Nd_DIV_OPS'] =  mainDataFrame[MetricName.COUNT_OPS_DIV_PCT].apply(find_div_ops)
    sw_bias_df['Nd_FMA_OPS'] =  mainDataFrame[MetricName.COUNT_OPS_FMA_PCT].apply(find_fma_ops)

    sw_bias_df['Nd_clu_score'] =  mainDataFrame['clu_scores'].apply(find_clu_factor)
    sw_bias_df['Nd_Recurrence'] =  mainDataFrame['recurrence'].apply(find_recurrence_factor)
    sw_bias_df['Nd_RHS'] =  mainDataFrame['rhs_op_count'].apply(find_rhs_ops)

    sw_bias_df['Neg_SW_Bias'] =  mainDataFrame['Neg_SW_Bias']
    sw_bias_df['Pos_SW_Bias'] =  mainDataFrame['Pos_SW_Bias']
    sw_bias_df['Net_SW_Bias'] =  mainDataFrame['Net_SW_Bias']

    return sw_bias_df


def main(argv):
    inputfile = []
# csv to read should be first argument
    main_csvToRead = sys.argv[1]
    print("Attempting to read", main_csvToRead)

    # read into pandas
    mainDataFrame = pd.read_csv(main_csvToRead)
    print("Read successful!")

    # save original dataframe
    originalDataFrame = mainDataFrame
    result_df = compute_sw_bias(result_df)
    csv_string = 'sw_bias_sat_results.csv'
    result_df.to_csv(csv_string, index = False, header=True)
if __name__ == "__main__":
    main(sys.argv[1:])
