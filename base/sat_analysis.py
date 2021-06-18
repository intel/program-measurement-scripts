from capedata import MergeShortNameData
from openpyxl.utils.dataframe import dataframe_to_rows
import sys
sys.path.append('.\test_SI')
#from test_SI import compute_and_plot
#from test_SI import test_and_plot_orig
from metric_names import MetricName
from metric_names import NonMetricName
from sw_bias import compute_sw_bias
import openpyxl
import openpyxl.chart
import pandas as pd
import numpy as np  
import sys
import importlib
import re
from pathlib import Path
from metric_names import KEY_METRICS
from generate_SI import compute_only
from generate_SI import BASIC_NODE_SET
from generate_SI import ALL_NODE_SET
from generate_SI import SiData
from capeplot import CapacityData
from capelib import crossjoin
import os
# GUI import

# percent within max in column for color
# TODO unused at the moment
#@satThreshold = 0.10
cuSatThreshold = 0.25

si_passed = 0
si_failed = 0
no_cluster = 0
unique_sat_node_clusters = []
unique_tiers = []
DO_SUB_CLUSTERING = False
DO_DEBUG_LOGS = False
PRINT_ALL_CLUSTERS = False
PRINT_COLOURED_TIERS = False
RUN_SI = True
RUN_SW_BIAS = True

CU_NODE_SET={MetricName.STALL_FE_PCT, MetricName.STALL_LB_PCT, MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_RS_PCT}
CU_NODE_DICT={MetricName.STALL_FE_PCT:'FE [GW/s]', MetricName.STALL_LB_PCT:'LB [GW/s]', MetricName.STALL_SB_PCT:'SB [GW/s]', MetricName.STALL_LM_PCT:'LM [GW/s]', MetricName.STALL_RS_PCT:'RS [GW/s]'}

# No Frontend
#CU_NODE_SET={MetricName.STALL_LB_PCT, MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_RS_PCT}
#CU_NODE_DICT={MetricName.STALL_LB_PCT:'LB', MetricName.STALL_SB_PCT:'SB', MetricName.STALL_LM_PCT:'LM', MetricName.STALL_RS_PCT:'RS'}

# This has to be identical to BASIC_NODE_SET in generate_SI
#BASIC_NODE_LIST=['L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]', 'VR [GB/s]', 'RAM [GB/s]']
BASIC_NODE_LIST=list(BASIC_NODE_SET)

# memory traffic
trafficToCheck = [ MetricName.RATE_REG_SIMD_GB_P_S, MetricName.RATE_FP_GFLOP_P_S, MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S ]
memTrafficToCheck = [ MetricName.RATE_REG_SIMD_GB_P_S, MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S ]
archIntensityToCheck = ["SIMD_MEM_Intensity", "FLOP_MEM_Intensity"]

#ALL_NODE_LIST =  [ "register_simd_rate_gb/s", "flop_rate_gflop/s", "l1_rate_gb/s", "l2_rate_gb/s", "l3_rate_gb/s", "ram_rate_gb/s",
#                   "%sb", "%lm", "%rs", "%lb"]
ALL_NODE_LIST =  [MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S, MetricName.RATE_REG_SIMD_GB_P_S, MetricName.RATE_FP_GFLOP_P_S,
                            MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT]

# arith
#percentsToCheck = ["register_simd_rate_gb/s", "%ops[vec]", "%inst[vec]", "%prf", "%sb", "%rs", "%lb", "%rob", "%lm", "%frontend" ]
#percentsToCheck = [ "%sb", "%lm", "%frontend" , "%rs", "%lb"]
percentsToCheck = [ MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT]
cuTrafficToCheck = [ MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT]
subNodeTrafficToCheck = [ MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT, MetricName.STALL_FE_PCT, MetricName.STALL_RS_PCT]

SW_BIAS_COLUMNS = ['Nd_CNVT_OPS', 'Nd_VEC_OPS', 'Nd_DIV_OPS', 'Nd_FMA_OPS', 'Nd_ISA_EXT_TYPE', 'Nd_clu_score', 'Nd_Recurrence' , 'Nd_RHS',
                  'Neg_SW_Bias', 'Pos_SW_Bias', 'Net_SW_Bias', NonMetricName.SI_TIER_NORMALIZED]
SW_BIAS_IP = [MetricName.COUNT_OPS_VEC_PCT, MetricName.COUNT_VEC_TYPE_OPS_PCT, MetricName.COUNT_OPS_FMA_PCT,
              MetricName.COUNT_OPS_CVT_PCT, MetricName.COUNT_OPS_DIV_PCT,
              MetricName.SRC_RHS_OP_COUNT, MetricName.SRC_RECURRENCE_B, MetricName.SRC_CLU_SCORE]
OUTPUT_COLUMNS=[NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES, NonMetricName.SI_SAT_TIER] + SW_BIAS_COLUMNS
NEEDED_CLUSTER_DF_COLUMNS = KEY_METRICS+ OUTPUT_COLUMNS + ALL_NODE_LIST + [MetricName.STALL_FE_PCT, MetricName.STALL_RS_PCT]
if RUN_SW_BIAS:
  NEEDED_CLUSTER_DF_COLUMNS = NEEDED_CLUSTER_DF_COLUMNS + SW_BIAS_IP
NEEDED_TEST_DF_COLUMNS = NEEDED_CLUSTER_DF_COLUMNS


# this dict contains columns + rows of those columns that need to be colored
# assumption is that you don't add any more rows else dict becomes out of dat
maxOfColumn = {}
coloured_maxOfColumn = {}

# Initializes a list of things in a dict as lists
def initDict(maxOfColumn, listOfColumns):
  for i in listOfColumns:
    maxOfColumn[i] = []

# init lists
initDict(maxOfColumn, trafficToCheck)
initDict(maxOfColumn, percentsToCheck)
initDict(maxOfColumn, archIntensityToCheck)

column_names = [MetricName.SHORT_NAME, 'Variant', 'Set', 'peer_codelet_cnt', 'Tier', 'Sat_Node', 'Sat_Range', 'SI_Result', 'Box_Length', 'Box_Ratio', 'SW_bias_CLS_CDLTS',
               'SW_bias_Result', 'SW_bias_box_length', 'SW_bias_box_ratio', 'Intensity', 'Saturation', 'GFlops',
               'neg_bias[CNVT,DIV,clu_score,Rec,RHS]', 'pos_bias[VEC_OPS,ISA_EXT,FMA_OPS]', 'SW_bias']

################################################################################
# setting up excelsheet to color
################################################################################
def load_workbook(tier_book_path):
   if os.path.exists(tier_book_path):
      return openpyxl.load_workbook(tier_book_path)
   return  openpyxl.Workbook()


################################################################################
# Coloring
################################################################################

opRed = openpyxl.styles.PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
opYellow = openpyxl.styles.PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
opGreen = openpyxl.styles.PatternFill(start_color="008000", end_color="008000", fill_type="solid")
opBlue = openpyxl.styles.PatternFill(start_color="0000FF", end_color="0000FF", fill_type="solid")
opPurple = openpyxl.styles.PatternFill(start_color="800080", end_color="800080", fill_type="solid")

def compute_node_thresholds(satSetDF, traffic, cu_traffic, satThreshold, prev_gap):
  traffic_gap = None if prev_gap is None else prev_gap[0]
  cu_gap = None if prev_gap is None else prev_gap[1]
  traffic_max = satSetDF[traffic].max() 
  if traffic_gap is not None:
    trafficThresholds = (traffic_max - traffic_gap).clip(lower=0)
  else:
    trafficThresholds = traffic_max * (1-satThreshold) 
  cu_max = satSetDF[cu_traffic].max()
  cuThresholds = cu_max.copy()
  cuSmallMask = cuThresholds < 50
  cuThresholds[cuSmallMask] = np.nan
  if cu_gap is not None:
    cuThresholds[~cuSmallMask] = (cuThresholds[~cuSmallMask] - cu_gap[~cuSmallMask]).clip(lower=0)
  else:
    cuThresholds[~cuSmallMask] = cuThresholds[~cuSmallMask] * (1-cuSatThreshold)
  # For threshold lower than 50, set it to infinity so no codelets can saturate.
  return pd.concat([trafficThresholds , cuThresholds], axis=0), \
    [traffic_max - trafficThresholds , cu_max - cuThresholds]
  




# def find_all_clusters(satSetDF):
#     #global satThreshold;
#     print ("Memory Node Saturation Threshold : ", satThreshold)
#     print ("Control Node Saturation Threshold : ", cuSatThreshold)

def compute_cluster_names(tiers_sat_nodes_mask, sat_nodes):
  tiered_mask = ~tiers_sat_nodes_mask['Tier'].isna()
  sat_nodes_only=tiers_sat_nodes_mask.loc[tiered_mask, sat_nodes]
  tiers_sat_nodes_mask['satTrafficList']=[[]]*len(tiers_sat_nodes_mask)
  tiers_sat_nodes_mask.loc[tiered_mask, 'satTrafficList'] = sat_nodes_only.apply(lambda x: sorted(sat_nodes_only.columns[x]), axis=1)
  tiers_sat_nodes_mask.loc[tiered_mask, 'Sat_Node'] = tiers_sat_nodes_mask[tiered_mask].apply(lambda x: ", ".join(x['satTrafficList']), axis=1)
  tiers_sat_nodes_mask.loc[tiered_mask, NonMetricName.SI_SAT_TIER] = tiers_sat_nodes_mask.loc[tiered_mask,'Tier'].astype('int32')
  tiers_sat_nodes_mask.loc[tiered_mask, 'Tier'] = tiers_sat_nodes_mask.loc[tiered_mask, NonMetricName.SI_SAT_TIER].astype(str)
  tiers_sat_nodes_mask[NonMetricName.SI_CLUSTER_NAME]=''
  tiers_sat_nodes_mask.loc[tiered_mask, NonMetricName.SI_CLUSTER_NAME]=tiers_sat_nodes_mask[tiered_mask].apply(lambda x: f"{x['Tier']} {x['Sat_Node']}", axis=1)
  tiers_sat_nodes_mask[NonMetricName.SI_SAT_NODES]=[set(BASIC_NODE_LIST)]*len(tiers_sat_nodes_mask) 
  tiers_sat_nodes_mask.loc[tiered_mask, NonMetricName.SI_SAT_NODES]=tiers_sat_nodes_mask[tiered_mask].apply(lambda x: set(BASIC_NODE_LIST) | {CU_NODE_DICT[n] for n in set(x['satTrafficList']) & CU_NODE_SET}, axis=1)

# For each codelets in current_codelets_runs_df, find their cluster
#   Store the name of the cluster to the SI_CLUSTER_NAME column
#   Also return the a data frame containing by appending all dataframe of the clusters annotated with their names
def do_sat_analysis(optimal_data_df, testSetDF, chosen_node_set, disable = False):
    short_name=''
    nodes_without_units = {n.split(" ")[0] for n in chosen_node_set} 
    CapacityData(optimal_data_df).set_chosen_node_set(nodes_without_units).compute()
    satSetDF = optimal_data_df

    # If SI Analysis is disabled
    # Creating an empty Dataframe with column names only SI_SAT_NODES and SI_CLUSTER_NAME
    if disable:
      testSetDF[NonMetricName.SI_CLUSTER_NAME] = ''
      testSetDF[NonMetricName.SI_SAT_NODES] = [chosen_node_set]*len(testSetDF)
      all_test_codelets = all_test_codelets.append(testSetDF)
      return all_clusters, all_test_codelets
    #global satThreshold
    global cuSatThreshold
    codelet_tested = 0
    # Commented out following line because it is incorrect.  satThreshold is *not* a constant
    # print ("Memory Node Saturation Threshold : ", satThreshold)
    print ("Control Node Saturation Threshold : ", cuSatThreshold)
    capsToRetain = [MetricName.capWUnit(n) for n in chosen_node_set]+[MetricName.CAP_ALLMAX_GB_P_S]
    #cols = satSetDF.columns.tolist() + list(set(KEY_METRICS) - set(satSetDF.columns.tolist()))+capsToRetain
    cols = set(satSetDF.columns) | set(KEY_METRICS) | set(capsToRetain)

    compute_sw_bias(satSetDF)
    compute_sw_bias(testSetDF)

    mem_traffic = [MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S]
    max_mem_traffic = testSetDF[mem_traffic].max(axis=1)
    mem_traffic_threshold = 0.1 * max_mem_traffic
    check_traffic_mask = testSetDF[memTrafficToCheck].gt(mem_traffic_threshold, axis=0)
    testSetDF.loc[:,'tstcdlt_TrafficToCheck'] = check_traffic_mask.apply(
      lambda x: check_traffic_mask.columns[x].to_list() + [MetricName.RATE_FP_GFLOP_P_S], axis=1)

    satSetDF['Tier'] = None 
    tier = 0
    non_traffic_tiering_metrics = [MetricName.RATE_FP_GFLOP_P_S, MetricName.RATE_REG_SIMD_GB_P_S] + percentsToCheck
    tiering_metrics = mem_traffic + non_traffic_tiering_metrics
    #tiering_table = pd.DataFrame(columns=['Tier']+tiering_metrics)
    tiering_table = pd.DataFrame()
    sat_table = satSetDF[KEY_METRICS].copy()
    # naMask is True for items not tiered yet so need to be considered
    candidate_mask = satSetDF['Tier'].isna()
    gap = None
    while candidate_mask.any():
      curSatSetDF = satSetDF[candidate_mask]
      tier = tier + 1
      satThreshold = 0.1 * tier
      thresholds, this_gap = compute_node_thresholds(curSatSetDF, 
                                                     mem_traffic+[MetricName.RATE_FP_GFLOP_P_S, 
                                                                  MetricName.RATE_REG_SIMD_GB_P_S], 
                                                     percentsToCheck, satThreshold, gap)
                 
      # uncomment following line to try uniform gap
      #gap = this_gap if gap is None else gap
      thresholds['Tier'] = tier
      tiering_table = tiering_table.append(thresholds, ignore_index=True)

      sat_mask = (curSatSetDF[tiering_metrics] > thresholds[tiering_metrics])
      # passMask records the rows in the candidate rows passing the saturation test
      passMask = sat_mask.any(axis=1)
      # update satSetDF in place.  To do this we get the mask to do the update
      # First get a copy of current na mask reflecting this iteration's candidate rows.  
      # The size of this mask is always the same as satSetDF.
      mask_for_satSetDF = candidate_mask.copy()
      # Among the rows with naMask==True, set the True/False value following the pass_mask, 
      # Esseential this operation bring the saturation result back to the overall satSetDF mask,
      # so satSetDF[mask] are the rows passing saturation test.
      mask_for_satSetDF[candidate_mask]=passMask
      satSetDF.loc[mask_for_satSetDF, 'Tier'] = tier

      sat_table.loc[candidate_mask, 'Tier'] = tier
      sat_table.loc[candidate_mask, sat_mask.columns] = sat_mask

      candidate_mask = satSetDF['Tier'].isna()
    all_nodes = set(sat_table)-set(KEY_METRICS+['Tier'])
    compute_cluster_names(sat_table, all_nodes)
    # Since sat_table and satSetDF are in the same index order, so just assign the cluster name column directly
    satSetDF[[NonMetricName.SI_CLUSTER_NAME, 'Sat_Node', 'satTrafficList', NonMetricName.SI_SAT_TIER]] = \
      sat_table[[NonMetricName.SI_CLUSTER_NAME, 'Sat_Node', 'satTrafficList', NonMetricName.SI_SAT_TIER]]

    
    # Now compute the Sat_Range.  Including 'Sat_Node' instead of satTrafficList because list cannob be used in groupby
    # Also reset_index() to bring the cluster name and Sat_Node to column names.  Including Tier and SI_SAT_TIER assuming they are consistent with cluster name which is the primary key
    cluster_info = satSetDF.groupby([NonMetricName.SI_CLUSTER_NAME, 'Sat_Node', 'Tier', NonMetricName.SI_SAT_TIER]).agg({ n: ['min', 'max'] for n in all_nodes}).reset_index()
    # TODO : fix types more cleanly
    cluster_info[NonMetricName.SI_SAT_TIER]=cluster_info[NonMetricName.SI_SAT_TIER].astype('int32')
    cluster_info['Tier']=cluster_info['Tier'].astype(str)
    # Flattern the columns
    cluster_info.columns=[' '.join(col).strip().replace(' ','_') for col in cluster_info.columns.values]
    cluster_info['Sat_Range'] = cluster_info.apply(lambda x: ', '.join([f"{elem}: [{x[elem+'_max']}  {x[elem+'_min']}]" for elem in x['Sat_Node'].split(', ')]), axis=1)

    # Simple counting of codelets in each cluster
    cluster_counts = satSetDF[NonMetricName.SI_CLUSTER_NAME].value_counts()
    # Convert the counts to dataframe to join with cluster_info
    cluster_counts = cluster_counts.to_frame('peer_codelet_cnt').reset_index().rename(columns={'index': NonMetricName.SI_CLUSTER_NAME})
    cluster_info = pd.merge(left=cluster_info, right=cluster_counts, on=NonMetricName.SI_CLUSTER_NAME, how='left')

    # Counting only for tiering
    tiering_table['Training Set Count']=tiering_table.Tier.map(satSetDF.Tier.value_counts())
    # Default values will be overriden when cluster is found

    testSetDF[MetricName.TIMESTAMP] = testSetDF[MetricName.TIMESTAMP].astype({MetricName.TIMESTAMP: 'int64'})
    testSetDF['Variant'] = ''
    # copiedTestSetDF['SI_Result'] = 'No Cluster'
    # copiedTestSetDF[['Box_Length', 'Box_Ratio', 'Intensity', 'Saturation', 'Sat_Node', 'Sat_Range',
    #                  'SW_bias', 'SW_bias_Result', 'SW_bias_box_length', 'SW_bias_box_ratio', 'SW_bias_CLS_CDLTS']] = None

    # Do a cross join so each test codelet will be associated to (the same) tiering table to find tierin parallel (table lookup)
    test_and_tiering = crossjoin(testSetDF, tiering_table, suffixes=("", "_threshold"))
    # Compare against thresholds.  Need to copy out and rename to matching columns to be able to do the big compare operation.
    tiering_threshold_names = [n+"_threshold" for n in tiering_metrics]
    tiering_thresholds = test_and_tiering[tiering_threshold_names]
    tiering_thresholds = tiering_thresholds.rename(columns=dict(zip(tiering_threshold_names, tiering_metrics)))
    tiering_sat_checks = test_and_tiering[tiering_metrics] > tiering_thresholds
    # For traffic compute another mask to ignore small traffic
    small_traffic_thresholds = 0.1 * test_and_tiering[mem_traffic].max(axis=1)
    small_traffic_checks = test_and_tiering[mem_traffic].gt(small_traffic_thresholds, axis=0)

    traffic_sat_checks = tiering_sat_checks[mem_traffic] & small_traffic_checks
    traffic_sat_checks_any = traffic_sat_checks.any(axis=1)
    non_traffic_sat_checks = tiering_sat_checks[non_traffic_tiering_metrics]
    non_traffic_sat_checks_any = non_traffic_sat_checks.any(axis=1)
    test_and_tiering['sat_check'] = traffic_sat_checks_any | non_traffic_sat_checks_any
    tiers = test_and_tiering[KEY_METRICS+['Tier', 'sat_check']].groupby(KEY_METRICS).apply(lambda x: min(x.loc[x['sat_check'],'Tier'], default=np.nan))
    # Join back to get the rows with right tiers only
    test_and_sats = pd.concat([test_and_tiering[KEY_METRICS+['Tier']],traffic_sat_checks, non_traffic_sat_checks], axis=1)
    test_and_sats = pd.merge(left=test_and_sats, right=tiers.to_frame('Tier'), on=KEY_METRICS+['Tier'], how='right')
    compute_cluster_names(test_and_sats, list(traffic_sat_checks.columns)+list(non_traffic_sat_checks.columns))

    # With cluster name, we can merge with cluster_info to get training info associated
    # Note that both test df and cluster info has 'Sat_Node', 'Tier' and 'SI_SAT_TIER' columns, below we join with both cluster name and sat node expecting them to be consistent 
    test_and_sats = pd.merge(left=test_and_sats, right=cluster_info, on=[NonMetricName.SI_CLUSTER_NAME, 'Sat_Node', 'Tier', NonMetricName.SI_SAT_TIER], how='left')
    tiered_mask = ~test_and_sats['Tier'].isna()
    test_and_sats.loc[tiered_mask, NonMetricName.SI_SAT_TIER]=test_and_sats.loc[tiered_mask, NonMetricName.SI_SAT_TIER].astype('int32')
    test_and_sats.loc[tiered_mask,'Tier']=test_and_sats.loc[tiered_mask,'Tier'].astype(str)
    # Set Cluster name to '' for tiny clusters
    test_and_sats.loc[(test_and_sats['peer_codelet_cnt']<2) | (test_and_sats['peer_codelet_cnt'].isna()), NonMetricName.SI_CLUSTER_NAME] = ''
    my_all_test_codelets = pd.merge(left=testSetDF, right=test_and_sats[KEY_METRICS+sorted(set(test_and_sats.columns) -set(testSetDF.columns))], on=KEY_METRICS)
    peer_mask = satSetDF[NonMetricName.SI_CLUSTER_NAME].isin(set(my_all_test_codelets[NonMetricName.SI_CLUSTER_NAME].to_list())-set({''}))
    my_all_clusters = satSetDF[peer_mask]
    # TODO: clean up
    my_all_clusters[NonMetricName.SI_SAT_NODES] = my_all_clusters['satTrafficList'].to_frame().apply(lambda x: set(BASIC_NODE_LIST) | {CU_NODE_DICT[n] for n in set(x['satTrafficList']) & CU_NODE_SET}, axis=1)
    
    test_and_tiering = pd.merge(left=test_and_tiering, right=tiers.to_frame('Tier'), on=KEY_METRICS+['Tier'], how='right')

    copiedTestSetDF = testSetDF.copy()
    copiedTestSetDF[NonMetricName.SI_CLUSTER_NAME] = ''
    copiedTestSetDF[NonMetricName.SI_SAT_NODES] = [set(BASIC_NODE_LIST)]*len(copiedTestSetDF)
    copiedTestSetDF[MetricName.SHORT_NAME]='test-'+copiedTestSetDF[MetricName.SHORT_NAME]

    norm = "row"
    all_test_codelets = my_all_test_codelets
    all_clusters = my_all_clusters


    #all_clusters, my_cluster_and_test_df, testDF = compute_only(all_clusters, norm, testDF, updated_chosen_node_set)
    clustered_test_df = all_test_codelets[all_test_codelets[NonMetricName.SI_CLUSTER_NAME] != '']
    all_clusters, _, clustered_test_df = compute_only(all_clusters, norm, clustered_test_df, 
                                                      set(BASIC_NODE_LIST) |  {CU_NODE_DICT[n] for n in CU_NODE_SET & set(ALL_NODE_LIST)})
    added_columns = set(clustered_test_df.columns)-set(all_test_codelets.columns)
    all_test_codelets = pd.merge(left=all_test_codelets, right=clustered_test_df[KEY_METRICS+sorted(added_columns)], on=KEY_METRICS, how='outer')
    result_df = all_test_codelets[[MetricName.SHORT_NAME, 'peer_codelet_cnt', 'Tier', 'Sat_Node', 'Sat_Range', 'Variant' ]]
    # Compute min and max for S and I for each cluster 
    cluster_groups=all_clusters[[NonMetricName.SI_CLUSTER_NAME, 'Intensity', 'Saturation']].groupby(
      NonMetricName.SI_CLUSTER_NAME).agg({'Intensity': ['min', 'max'], 'Saturation': ['min', 'max']})
    # Flattern the columns
    cluster_groups.columns=[' '.join(col).strip().replace(' ','_') for col in cluster_groups.columns.values]
    cluster_groups['s_length']=round(cluster_groups['Saturation_max']-cluster_groups['Saturation_min'],2)
    cluster_groups['i_length']=round(cluster_groups['Intensity_max']-cluster_groups['Intensity_min'],2)
    cluster_groups['s_ratio']=round(cluster_groups['Saturation_max']/cluster_groups['Saturation_min'],2)
    cluster_groups['i_ratio']=round(cluster_groups['Intensity_max']/cluster_groups['Intensity_min'],2)

    #cluster_groups['Norm_Tier'] = codelet_tier + ((peer_codelet_df['Saturation'] - peer_codelet_df['Saturation'].min())/s_length)
    cluster_groups['Box_Length'] = '{' + cluster_groups['s_length'].astype(str) + ' , ' + cluster_groups['i_length'].astype(str) + '}'
    cluster_groups['Box_Ratio'] = '{' + cluster_groups['s_ratio'].astype(str) + ' , ' + cluster_groups['i_ratio'].astype(str) + '}'
    # Flattern the groupped df
    #cluster_groups = cluster_groups.stack()[['Box_Length', 'Box_Ratio']]
    all_test_codelets=pd.merge(left=all_test_codelets, right=cluster_groups, on=[NonMetricName.SI_CLUSTER_NAME], how='outer')
    all_test_codelets['SW_bias'] = round(all_test_codelets['Net_SW_Bias'], 2)
    all_test_codelets[NonMetricName.SI_TIER_NORMALIZED] = all_test_codelets[NonMetricName.SI_SAT_TIER] + \
      (all_test_codelets['Saturation']-all_test_codelets['Saturation_min']).clip(lower=0)/all_test_codelets['s_length']
    noSatMask = all_test_codelets['Saturation'].isna()
    all_test_codelets.loc[noSatMask,'SI_Result'] = 'No Cluster'
    inBoxMask = (all_test_codelets['Saturation'] >= all_test_codelets['Saturation_min']) & \
      (all_test_codelets['Saturation'] <= all_test_codelets['Saturation_max']) & \
        (all_test_codelets['Intensity'] >= all_test_codelets['Intensity_min']) & \
          (all_test_codelets['Intensity'] <= all_test_codelets['Intensity_max'])
    all_test_codelets.loc[~noSatMask & inBoxMask, 'SI_Result']='Inside Box'
    all_test_codelets.loc[~noSatMask & ~inBoxMask, 'SI_Result']='Outside Box'
    pass_counts = all_test_codelets['SI_Result'].value_counts().reindex(['Inside Box', 'Outside Box'], fill_value=0)
    si_passed = pass_counts['Inside Box']
    si_failed = pass_counts['Outside Box']

    # Also compute normalized tier for training codelets.  
    all_clusters=pd.merge(left=all_clusters, right=cluster_groups, on=[NonMetricName.SI_CLUSTER_NAME], how='outer')
    all_clusters[NonMetricName.SI_TIER_NORMALIZED] = all_clusters[NonMetricName.SI_SAT_TIER] + \
      (all_clusters['Saturation']-all_clusters['Saturation_min'])/all_clusters['s_length']
    result_df['GFlops']=round(all_test_codelets[MetricName.RATE_FP_GFLOP_P_S], 2)
    result_df['Saturation'] = round(all_test_codelets['Saturation'], 2)
    result_df['Intensity'] = round(all_test_codelets['Intensity'], 2)

    result_df['neg_bias[CNVT,DIV,clu_score,Rec,RHS]']=all_test_codelets[['Nd_CNVT_OPS', 'Nd_DIV_OPS', 'Nd_clu_score', 
                                                                         'Nd_Recurrence', 'Nd_RHS']].values.tolist()
    result_df['pos_bias[VEC_OPS,ISA_EXT,FMA_OPS]'] =all_test_codelets[['Nd_VEC_OPS', 'Nd_ISA_EXT_TYPE', 'Nd_FMA_OPS']].values.tolist()
    result_df.to_csv('Result_report.csv', index = True, header=True)
    print ("Total No. of codelets tested : ", codelet_tested)
    print ("Total No. of codelets outside SI box: ", si_passed)
    print ("Total No. of codelets inside SI box: ", si_failed)
    print ("Total No. of codelets without Cluster : ", no_cluster)
    print ("Total No. of Tiers : ", len(result_df['Tier'].unique()))
    print ("Total No. of unique clusters : ", len(result_df['Sat_Node'].unique()))
    stat_data = [{'Mem Threshold (incorrect)' : satThreshold, 'CU Threshold' : cuSatThreshold,
            'Codelets Tested' : codelet_tested, 'Passed' : si_passed, 'Failed' : si_failed,
            'No Cluster' : no_cluster, 'Tier Count' : len(unique_tiers), 'Cluster Count' : len(unique_sat_node_clusters)}]
    stats_df = pd.DataFrame(stat_data)
    my_file = Path("./statistcs.csv")
    if my_file.is_file():
       # file exists
       stats_df.to_csv('statistcs.csv', mode='a', header=False, index=False)
    else :
       stats_df.to_csv('statistcs.csv', mode='w', header=True, index=False)

    # filter out the unnecessary columns
    all_clusters = all_clusters[NEEDED_CLUSTER_DF_COLUMNS]
    # TODO: Fix inconsisent NEEDED CLUSTER and ALL NODE
    all_test_codelets[list(set(NEEDED_CLUSTER_DF_COLUMNS)-set(all_test_codelets.columns))]=np.nan
    all_test_codelets=all_test_codelets[NEEDED_CLUSTER_DF_COLUMNS]
    # GUI will be able to get individual cluster data frame by using the mask all_clusters[NonMetric_Name.SI_CLUSTER_NAME] == 'FE_tier1'
    # return the global cluster and test codelets => to use for plotting
    return all_clusters, all_test_codelets, result_df

    
# Some leftover routines not removed but unused.
# Find max in traffic columns + perfcent columns, save to maxDict
def createSubcluster(data, subSatList, short_name):
  # get rows that we need to check
  rowsToCheck = data.index.tolist()
  initDict(maxOfColumn, subNodeTrafficToCheck)
  target_df = pd.DataFrame(columns=data.columns.tolist())
  csv_string = short_name + '_sub_cluster.csv'
  #print (data)
  if not subSatList:
      for row in rowsToCheck:
        #print (row)
        #print ("No sub sat nodes")
        for column in subNodeTrafficToCheck:
          columnIndex = data.columns.get_loc(column)
          # init list of blocks to color 
          num = data.iloc[row, columnIndex]
          if num <= 50:
              maxOfColumn[column].append(row)
  else:
      for row in rowsToCheck:
        #print (row)
        #print (subSatList)
        for column in subNodeTrafficToCheck and subSatList:
          # init list of blocks to color 
          columnIndex = data.columns.get_loc(column)
          num = data.iloc[row, columnIndex]
          if num >= 50:
              maxOfColumn[column].append(row)
    #end columnfor
  #end rowfor
  codelet_list = maxOfColumn[column]
  if not subSatList:
      for column in cuTrafficToCheck:
          codelet_list = list(set(codelet_list) & set(maxOfColumn[column]))
      for row in codelet_list:
          target_df = target_df.append(data.iloc[row], ignore_index=True)
  else :
      codelet_list = maxOfColumn[subSatList[0]]
      for column in cuTrafficToCheck and subSatList:
          codelet_list = list(set(codelet_list) & set(maxOfColumn[column]))
      for row in codelet_list:
          target_df = target_df.append(data.iloc[row], ignore_index=True)
  return target_df


def concat_ordered_columns(frames):
    columns_ordered = []
    for frame in frames:
        columns_ordered.extend(x for x in frame.columns if x not in columns_ordered)
    final_df = pd.concat(frames, ignore_index=True)
    return final_df[columns_ordered]

def do_sub_clustering(peer_codelet_df, testDF, short_name, codelet_tier, satTrafficList):
    # global si_passed
    # global si_failed
    global no_cluster
    sub_cls_df = pd.DataFrame()
    chosen_node_set = set(BASIC_NODE_LIST)
    node_chck =  any(elem in satTrafficList  for elem in subNodeTrafficToCheck)
    if not node_chck :
        sub_nodes = []
        for column in subNodeTrafficToCheck:
          columnIndex = testDF.columns.get_loc(column)
          cu_val = testDF.iloc[0, columnIndex]/100
          if cu_val >= 0.3:
             sub_nodes.append(column)
        #print (sub_nodes)
        print ("calling createSubcluster :", short_name)
        if not sub_nodes:
           sub_node_string = "No CU Saturation in sub clustering"
        else:
           sub_node_string = str(sub_nodes) + "has 50% or more activity in sub clustering"
        sub_cluster_df = createSubcluster(peer_codelet_df, sub_nodes, short_name)
        sub_clstr_cdlt_count = sub_cluster_df.shape[0]
        if sub_clstr_cdlt_count >= 3:
            outputfile = short_name + 'SUB_Tier_'+str(codelet_tier) + "_SI.csv"
            norm = "row"
            title = "SI"
            target_df = pd.DataFrame()
            #print ("calling SI Compute with nodes :", chosen_node_set)
            #sw_bias_df = compute_sw_bias(sub_cluster_df)
            compute_and_plot('XFORM', sub_cluster_df, outputfile, norm, title, chosen_node_set, target_df)
            peer_dfs = [sub_cluster_df,testDF]
            final_df = concat_ordered_columns(peer_dfs)
            result = test_and_plot_orig('ORIG', final_df, outputfile, norm, title, chosen_node_set, target_df, short_name)
            if DO_DEBUG_LOGS:
               final_df.to_csv(short_name+'_sub_cluster_report.csv', index = True, header=True)
            #print ("Sub_Cluster Result is : ", result)
            if result == True :
                print (short_name, "Passed the Sub_Cluster SI Test =>")
                si_passed +=1
                findUniqueTiers(satTrafficList, codelet_tier)
                #result_df = result_df.append({'ShortName' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                #            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_node_string, 'SI_Result' : 'Outside Box',
                #            'GFlops' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, MetricName.RATE_FP_GFLOP_P_S].item(),
                #            'Saturation' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Saturation'].item(),
                #            'Intensity' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Intensity'].item()}, 
                #ignore_index = True)
                sub_cls_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_node_string, 'SI_Result' : 'Outside Box',
                            'GFlops' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, MetricName.RATE_FP_GFLOP_P_S].item(),
                            'Saturation' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Saturation'].item(),
                            'Intensity' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Intensity'].item()})
            else:
                print (short_name, "Failed the Sub_ClusterSI Test =>")
                si_failed +=1
                findUniqueTiers(satTrafficList, codelet_tier)
                #result_df = result_df.append({'ShortName' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                #            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_node_string, 'SI_Result' : 'Inside Box',
                #            'GFlops' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, MetricName.RATE_FP_GFLOP_P_S].item(),
                #            'Saturation' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Saturation'].item(),
                #            'Intensity' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Intensity'].item()},
                #ignore_index = True)
                sub_cls_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_node_string, 'SI_Result' : 'Inside Box',
                            'GFlops' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, MetricName.RATE_FP_GFLOP_P_S].item(),
                            'Saturation' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Saturation'].item(),
                            'Intensity' : final_df.loc[final_df[MetricName.SHORT_NAME] == short_name, 'Intensity'].item()})
        else:
            print (short_name, "Not enough codelets in the Sub_ClusterSI Test =>")
            no_cluster+=1
            findUniqueTiers(satTrafficList, codelet_tier)
            #result_df = result_df.append({'ShortName' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
            #           'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_node_string, 'SI_Result' : 'No Sub Cluster'})
            sub_cls_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                        'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_node_string, 'SI_Result' : 'No Sub Cluster'})
    else :
        print (short_name, "How to do Sub_Cluster SI Test ??=>")
        sub_cls_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : 0,
                   'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : 'N/A', 'SI_Result' : 'No Sub Cluster'})
        si_failed+=1
    return sub_cls_df

def find_swbias_cluster(satSetDF, testDF, swbias_threshold):
    mask = satSetDF[NonMetricName.SI_SW_BIAS] >= swbias_threshold
    if testDF.iloc[0]['Net_SW_Bias'] >= swbias_threshold:
         return satSetDF[mask]
    else:
         return satSetDF[~mask]

def do_swbias_clustering(peer_codelet_df, testDF, satTrafficList):
    #sw_bias_df = compute_sw_bias(peer_codelet_df)
    #peer_codelet_swBias_df = pd.merge(peer_codelet_df, sw_bias_df)

    # sw_bias_df = compute_sw_bias(testDF)
     # get SW bias Vector
    neg_bias_vec =[testDF['Nd_CNVT_OPS'].item(), testDF['Nd_DIV_OPS'].item(), testDF['Nd_clu_score'].item(),
                   testDF['Nd_Recurrence'].item(), testDF['Nd_RHS'].item()] 
    pos_bias_vec =[testDF['Nd_VEC_OPS'].item(), testDF['Nd_ISA_EXT_TYPE'].item(), testDF['Nd_FMA_OPS'].item()]

    # test_swBias_df = pd.merge(testDF, sw_bias_df)
    swbias_cluster_df = find_swbias_cluster(peer_codelet_df, testDF, 0)
    cdlt_count = swbias_cluster_df.shape[0]
    chosen_node_set = set(BASIC_NODE_LIST)
    short_name = str(testDF.iloc[0][MetricName.SHORT_NAME])
    if cdlt_count >= 3:
        for elem in satTrafficList:
            if elem in CU_NODE_SET:
                #print (CU_NODE_DICT[elem])
                chosen_node_set.add(CU_NODE_DICT[elem])
        outputfile = short_name + '_sw_bias_'+ "_SI.csv"
        norm = "row"
        title = "SI"
        target_df = pd.DataFrame()
        #compute_and_plot('XFORM', swbias_cluster_df, outputfile, norm, title, chosen_node_set, target_df)
        my_cluster_df, my_cluster_and_test_df, my_test_df = compute_only(swbias_cluster_df, norm, testDF, chosen_node_set)
        peer_dfs = [swbias_cluster_df,testDF]
        final_df = concat_ordered_columns(peer_dfs)
        final_df.to_csv(outputfile, index = False, header=True)
        #bias_result = test_and_plot_orig('ORIG', final_df, outputfile, norm, title, chosen_node_set, target_df, short_name)
        bias_result = True
        s_length = swbias_cluster_df['Saturation'].max() - swbias_cluster_df['Saturation'].min()
        i_length = swbias_cluster_df['Intensity'].max() - swbias_cluster_df['Intensity'].min()
        box_length = '{' + str(round(s_length, 2)) + ' , ' + str(round(i_length, 2)) + '}'

        s_ratio = swbias_cluster_df['Saturation'].max() / swbias_cluster_df['Saturation'].min()
        i_ratio = swbias_cluster_df['Intensity'].max() / swbias_cluster_df['Intensity'].min()
        box_ratio = '{' + str(round(s_length, 2)) + ' , ' + str(round(i_length, 2)) + '}'

        if bias_result == True :
            print (short_name, " swbias cluster Outside the SI Box =>")
            result_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : cdlt_count,'SI_Result' : 'Outside Box',
                        'Box_Length' : box_length, 'Box_Ratio' : box_ratio, 'Neg_SW_bias_Vec' : str(neg_bias_vec), 'Pos_SW_bias_Vec' : str(pos_bias_vec)}, index=[0])
        else:
            print (short_name, " swbias cluster Inside the SI Box =>")
            result_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : cdlt_count,'SI_Result' : 'Inside Box',
                        'Box_Length' : box_length, 'Box_Ratio' : box_ratio, 'Neg_SW_bias_Vec' : str(neg_bias_vec), 'Pos_SW_bias_Vec' : str(pos_bias_vec)}, index=[0])
    else:
        print (short_name, " swbias cluster not present =>")
        result_df = pd.DataFrame({MetricName.SHORT_NAME : short_name, 'peer_codelet_cnt' : 0,'SI_Result' : 'No Cluster',
        'Box_Length' : 0, 'Box_Ratio' : 0, 'Neg_SW_bias_Vec' : str(neg_bias_vec), 'Pos_SW_bias_Vec' : str(pos_bias_vec)}, index=[0])
    return result_df



def print_coloured_tiers(short_name, codelet_tier, full_df):
    tier_book_path = short_name + "_tier.xlsx"
    tier_book = load_workbook(tier_book_path);
    highlightSheet = tier_book.create_sheet(short_name + "_" + str(codelet_tier), 0)
    sheet_title = short_name + "_" + str(codelet_tier) + "_" + "Highlights"
        # import all rows into xlsx package
    for r in dataframe_to_rows(full_df, index=False, header=True):
        highlightSheet.append(r)
    findMaxInColumnsToColor(full_df, trafficToCheck, percentsToCheck)
    colorMaxInColumn(full_df, coloured_maxOfColumn, opBlue, highlightSheet)
    tier_book.save(tier_book_path)


def main(argv):
    # csv to read should be first argument
    csvToRead = sys.argv[1]
    csvTestSet = sys.argv[2]
    inputfile = []
    #global satThreshold
    global cuSatThreshold
    sys.setrecursionlimit(10**9) 
  # if 3 arg specified, assumes 3rd is threshold replacement
    #print("No of sys args : ", len(sys.argv))
    if (len(sys.argv) >= 5):
      satThreshold = float(sys.argv[3])
      cuSatThreshold = float(sys.argv[4])

    print("Attempting to read", csvToRead)

    # read into pandas
    mainDataFrame = pd.read_csv(csvToRead)
    TestSetDF = pd.read_csv(csvTestSet)
    grouped = TestSetDF.groupby(MetricName.VARIANT)
    mask = (TestSetDF['Set'] == 'BENEFITTING') & (TestSetDF['Variant'] == 'ORIG')
    #mask = (TestSetDF['Set'] == 'BENEFITTING')

    print("Read successful!")

    # save original dataframe
    originalDataFrame = mainDataFrame

    # SIMD_RATE divided by max traffic column for memory
    addAfterColumn = mainDataFrame.columns.get_loc(MetricName.RATE_RAM_GB_P_S) + 1
    mainDataFrame.insert(addAfterColumn, "SIMD_MEM_Intensity",
      mainDataFrame[MetricName.RATE_REG_SIMD_GB_P_S] / mainDataFrame[[MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S]].max(axis=1))

    # FLOP_RATE divided by max traffic column for memory
    addAfterColumn = mainDataFrame.columns.get_loc(MetricName.RATE_FP_GFLOP_P_S) + 1
    mainDataFrame.insert(addAfterColumn, "FLOP_MEM_Intensity",
    mainDataFrame[MetricName.RATE_FP_GFLOP_P_S] / mainDataFrame[[MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S]].max(axis=1)/8)
    if RUN_SI:
      #do_sat_analysis(mainDataFrame, TestSetDF[mask])
      nodes_without_units = {n.split(" ")[0] for n in ALL_NODE_SET} 
      CapacityData(TestSetDF).set_chosen_node_set(nodes_without_units).compute()
      results = do_sat_analysis(mainDataFrame, TestSetDF, ALL_NODE_SET)
    # if PRINT_ALL_CLUSTERS:
    #   find_all_clusters(mainDataFrame)


if __name__ == "__main__":
    # csv to read should be first argument
    main(sys.argv[1:])
