from openpyxl.utils.dataframe import dataframe_to_rows
import sys
sys.path.append('.\test_SI')
#from test_SI import compute_and_plot
#from test_SI import test_and_plot_orig
import openpyxl
import openpyxl.chart
import pandas as pd
import numpy as np  
import sys
import re
import importlib
from pathlib import Path
from metric_names import NonMetricName, MetricName, KEY_METRICS
from generate_SI import compute_only
from generate_SI import BASIC_NODE_SET
from generate_SI import NODE_UNIT_DICT
from generate_SI import SiData
from capeplot import CapacityData
from capeplot import NodeWithUnitData
from sw_bias import compute_sw_bias
import os
# GUI import
from utils import resource_path as gui_resource_path

# percent within max in column for color
# TODO unused at the moment
satThreshold = 0.10
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
RUN_SW_BIAS = False

CU_NODE_SET={MetricName.STALL_FE_PCT, MetricName.STALL_LB_PCT, MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_RS_PCT}
CU_NODE_DICT={MetricName.STALL_FE_PCT:'FE [GB/s]', MetricName.STALL_LB_PCT:'LB [GB/s]', MetricName.STALL_SB_PCT:'SB [GB/s]', MetricName.STALL_LM_PCT:'LM [GB/s]', MetricName.STALL_RS_PCT:'RS [GB/s]'}

# No Frontend
#CU_NODE_SET={MetricName.STALL_LB_PCT, MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_RS_PCT}
#CU_NODE_DICT={MetricName.STALL_LB_PCT:'LB', MetricName.STALL_SB_PCT:'SB', MetricName.STALL_LM_PCT:'LM', MetricName.STALL_RS_PCT:'RS'}

# This has to be identical to BASIC_NODE_SET in generate_SI
#BASIC_NODE_LIST=['L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]', 'VR [GB/s]', 'RAM [GB/s]']
BASIC_NODE_LIST=list(BASIC_NODE_SET)

# memory traffic
trafficToCheck = [ MetricName.RATE_REG_SIMD_GB_P_S, MetricName.RATE_FP_GFLOP_P_S, MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S ]
memTrafficToCheck = [ MetricName.RATE_REG_SIMD_GB_P_S, MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S ]
#archIntensityToCheck = ["SIMD_MEM_Intensity", "FLOP_MEM_Intensity"]
archIntensityToCheck = []


ALL_NODE_LIST =  [MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S, MetricName.RATE_REG_SIMD_GB_P_S, MetricName.RATE_FP_GFLOP_P_S,
                            MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT]
# arith

primaryCuTrafficToCheck = [ MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT]
cuTrafficToCheck = [ MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT]
subNodeTrafficToCheck = [ MetricName.STALL_SB_PCT, MetricName.STALL_LM_PCT, MetricName.STALL_LB_PCT, MetricName.STALL_FE_PCT, MetricName.STALL_RS_PCT]


class SatAnalysisData(NodeWithUnitData):
  def __init__(self, df):
    super().__init__(df, NODE_UNIT_DICT) 

  def compute_impl(self, df):
    self.cluster_df, si_df = find_clusters(df, self.chosen_node_set)
    return si_df

  # Return (expected inputs, expected outputs)
  def input_output_args(self):
    input_args = SiData.capacities(self.chosen_node_set)+[MetricName.SHORT_NAME]+ALL_NODE_LIST+[MetricName.CAP_ALLMAX_GB_P_S]
    output_args = [NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES, NonMetricName.SI_SAT_TIER]
    return input_args, output_args


  # Subclass override to set the fields give more data
  def extra_data_to_restore(self, more_data):
    self.cluster_df = more_data.pop()
    assert len(more_data) == 0
    
  # Subclass override to provide more data to be written
  def extra_data_to_save(self):
    return [self.cluster_df]

# Chosen node set not needed compute_only() will get the nodes to consider from SI_SAT_NODES
# Will return three dataframes: cluster only, cluster+cur_run, cur_run only
# cluster_df, cluster_and_run_df, cur_run_df = compute_only(cluster_df, norm, cur_run_df) 

# For each codelets in current_codelets_runs_df, find their cluster
#   Store the name of the cluster to the SI_CLUSTER_NAME column
#   Also return the a data frame containing by appending all dataframe of the clusters annotated with their names
def find_clusters(current_codelets_runs_df, chosen_node_set, memAlusatThreshold = 0.10, cuSatThreshold = 0.25):
  # Read the optimal data file
  optimal_data_path = gui_resource_path(os.path.join('clusters', 'LORE-Optimal.csv'))
  optimal_data_df = pd.read_csv(optimal_data_path)
  nodes_without_units = {n.split(" ")[0] for n in chosen_node_set} 
  CapacityData(optimal_data_df).set_chosen_node_set(nodes_without_units).compute() 
  # Real implementation should have found many cluster dataframes and with the name set to its cluster name
  all_clusters, all_test_codelets = do_sat_analysis(optimal_data_df, current_codelets_runs_df, chosen_node_set)
    # filter out the unnecessary columns
  all_clusters = all_clusters[[MetricName.NAME, MetricName.TIMESTAMP, NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES, NonMetricName.SI_SAT_TIER] +
                               ALL_NODE_LIST + [MetricName.STALL_FE_PCT, MetricName.STALL_RS_PCT]]
  all_test_codelets=all_test_codelets[KEY_METRICS + [NonMetricName.SI_CLUSTER_NAME, NonMetricName.SI_SAT_NODES, NonMetricName.SI_SAT_TIER] +
                               ALL_NODE_LIST + [MetricName.STALL_FE_PCT, MetricName.STALL_RS_PCT]]


  # GUI will be able to get individual cluster data frame by using the mask all_clusters[NonMetric_Name.SI_CLUSTER_NAME] == 'FE_tier1'
  # return the global cluster and test codelets => to use for plotting
  return all_clusters, all_test_codelets


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
initDict(maxOfColumn, primaryCuTrafficToCheck)
initDict(maxOfColumn, archIntensityToCheck)

column_names = ['short_name', 'peer_codelet_cnt', 'peer codelets ' , 'Tier', 'Sat_Node', 'SI_Result']
result_df = pd.DataFrame(columns=column_names)

################################################################################
# setting up excelsheet to color
################################################################################

################################################################################
# Coloring
################################################################################

opRed = openpyxl.styles.PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
opYellow = openpyxl.styles.PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
opGreen = openpyxl.styles.PatternFill(start_color="008000", end_color="008000", fill_type="solid")
opBlue = openpyxl.styles.PatternFill(start_color="0000FF", end_color="0000FF", fill_type="solid") 
opPurple = openpyxl.styles.PatternFill(start_color="800080", end_color="800080", fill_type="solid")

# loop through max columns, color them
def colorMaxInColumn(data, columnDict, colorToUse, pyxlSheet):
  for key in columnDict.keys():
    columnIndex = data.columns.get_loc(key)
    rowsToColor = columnDict[key]
    # column + 1 because 1-index
    excelColumn = openpyxl.utils.cell.get_column_letter(columnIndex + 1)
    for row in rowsToColor:
      # row + 2 needed because 0 indexed and first row is column names
      excelRow = row + 2
      cellCoord = excelColumn + str(excelRow)
      activeCell = pyxlSheet[cellCoord]
      # color this cell
      activeCell.fill = colorToUse

# Find max in traffic columns + perfcent columns, save to maxDict
def findMaxInColumnsToColor(data, main_traffic, cu_traffic):
  # get rows that we need to check
  rowsToCheck = data.index.tolist()
  # initialize the dictionary to hold the rows
  initDict(coloured_maxOfColumn, main_traffic)
  initDict(coloured_maxOfColumn, cu_traffic)
  # column loop setup
  # for each column, find max in that column highlight within some threshold
  # only wanted a few columns, but go ahead and do it for all of them anyways
  for column in main_traffic:
    # init list of blocks to color 
    columnIndex = data.columns.get_loc(column)

    maxValue = data[column].max()
    threshold = maxValue * (1 - satThreshold)

    for row in rowsToCheck:
      num = data.iloc[row, columnIndex]

      if num >= threshold:
        coloured_maxOfColumn[column].append(row)
  #endfor

  # percent only colored if above certain threshold
  for column in cu_traffic:
    columnIndex = data.columns.get_loc(column)
    maxValue = data[column].max()/100

    # only bother if greater than .5
    if maxValue >= 0.5:
      threshold = maxValue * (1 - cuSatThreshold)

      for row in rowsToCheck:
        num = data.iloc[row, columnIndex]/100

        if num >= threshold:
          coloured_maxOfColumn[column].append(row)
      #endfor
  #endfor
  #check SIMD intensity
  #for row in rowsToCheck:
  # columnIndex = data.columns.get_loc("SIMD_MEM_Intensity")
  #  if data.iloc[row, columnIndex] > 3:
  #    coloured_maxOfColumn["SIMD_MEM_Intensity"].append(row)

# Find max in traffic columns + perfcent columns, save to maxDict
def findUniqueTiers(data, satList, tier):
  global unique_sat_node_clusters
  global unique_tiers
  #print ("Calling findUniqueTiers with : ", satList)
  # get rows that we need to check
  sat_string = ''
  if MetricName.RATE_REG_SIMD_GB_P_S in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'vr+'
  if MetricName.RATE_L1_GB_P_S in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'L1+'
  if MetricName.RATE_L2_GB_P_S in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'L2+'
  if MetricName.RATE_L3_GB_P_S in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'L3+'
  if MetricName.RATE_RAM_GB_P_S in satList:
      sat_string = sat_string + 'RAM+'

  if MetricName.RATE_FP_GFLOP_P_S in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'FLOP+'
  if MetricName.STALL_FE_PCT in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'FE+'
  if MetricName.STALL_LM_PCT in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'LM+'
  if MetricName.STALL_SB_PCT in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'SB+'
  if MetricName.STALL_RS_PCT in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'RS+'
  if MetricName.STALL_LB_PCT in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'LB+'

  if 'SIMD_MEM_Intensity' in satList:
      sat_string = sat_string + 'VEC+'

  if tier not in unique_tiers:
      unique_tiers.append(tier)

  if sat_string not in unique_sat_node_clusters:
      unique_sat_node_clusters.append(sat_string)
      target_df = pd.DataFrame(columns=data.columns.tolist())
      #target_df = target_df.append(data.iloc[row])
      #tagetFrames[sat_string] = target_df
  #print (unique_sat_node_clusters)
  #print (unique_tiers)

  for nodes in unique_sat_node_clusters:
    csv_string = nodes + '.csv'
    #tagetFrames[nodes].to_csv(csv_string, index = False, header=True)
# find unique tiers

# init target dataframe dictionary
tagetFrames = {}
# Find max in traffic columns + perfcent columns, save to maxDict
def checkCodeletTier(satdata, testCdltName, traffic, cu_traffic, sat_traffic):
  # get rows that we need to check
  codelet_in_this_tier = False
  index = satdata.index
  condition = satdata[MetricName.SHORT_NAME] == testCdltName
  test_codelet_indx = index[condition]
  row = test_codelet_indx[0]
  #print (rowsToCheck)
  #print (rowsToCheck)
  #satdata.to_csv(testCdltName + '_debug.csv', index = False, header=True)
  short_nameInx = satdata.columns.get_loc(MetricName.SHORT_NAME)
  short_name = satdata.iloc[test_codelet_indx[0], short_nameInx]
  for column in traffic:
    # init list of blocks to color 
    columnIndex = satdata.columns.get_loc(column)
    maxValue = satdata[column].max()
    threshold = maxValue * (1 - satThreshold)
    num = satdata.iloc[row, columnIndex]
    if num > threshold:
      codelet_in_this_tier = True
      sat_traffic.append(column)
      #print(short_name, " in current tier.")
  for column in cu_traffic:
    # init list of blocks to color 
    columnIndex = satdata.columns.get_loc(column)
    maxValue = satdata[column].max()/100
    if maxValue >= 0.5:
      threshold = maxValue * (1 - cuSatThreshold)
      num = satdata.iloc[row, columnIndex]/100
      if num > threshold:
        codelet_in_this_tier = True
        sat_traffic.append(column)
  return codelet_in_this_tier

# Find max in traffic columns + perfcent columns, save to maxDict
def findPeerCodelets(data, traffic, cu_traffic, satList, short_name):
  # get rows that we need to check
  initDict(maxOfColumn, satList)
  rowsToCheck = data.index.tolist()
  target_df = pd.DataFrame(columns=data.columns.tolist())
  csv_string = short_name + '_peer_codelet.csv'

  # To Remove the codelets that saturates nodes not in satList
  NodesNotInSatList = set(ALL_NODE_LIST) - set(satList)
  rowsToCheckForSaturation = []
  for row in rowsToCheck:
    codelet_in_non_sat_grp = False
    for column in NodesNotInSatList:
      columnIndex = data.columns.get_loc(column)
      maxValue = data[column].max()
      if column in cu_traffic:
          maxValue = maxValue/100
          if maxValue >= 0.5:
              threshold = maxValue * (1 - cuSatThreshold)
              num = data.iloc[row, columnIndex]/100
              if num > threshold:
                 codelet_in_non_sat_grp = True
      else:
          threshold = maxValue * (1 - satThreshold)
          num = data.iloc[row, columnIndex]
          if num > threshold:
            codelet_in_non_sat_grp = True
    if codelet_in_non_sat_grp is False:
      rowsToCheckForSaturation.append(row)
  for row in rowsToCheckForSaturation:
    for column in satList:
      # init list of blocks to color 
      columnIndex = data.columns.get_loc(column)
      maxValue = data[column].max()
      if column in cu_traffic:
          maxValue = maxValue/100
          if maxValue >= 0.5:
              threshold = maxValue * (1 - cuSatThreshold)
              num = data.iloc[row, columnIndex]/100
              if num > threshold:
                 maxOfColumn[column].append(row)
      else:
          threshold = maxValue * (1 - satThreshold)
          num = data.iloc[row, columnIndex]
          if num > threshold:
            maxOfColumn[column].append(row)
    #end columnfor
  #end rowfor
  codelet_list = maxOfColumn[column]
  for column in satList:
      codelet_list = list(set(codelet_list) & set(maxOfColumn[column]))
  for row in codelet_list:
      target_df = target_df.append(data.iloc[row], ignore_index=True)
  #target_df.to_csv(csv_string, index = False, header=True)
  return target_df

# Find max in traffic columns + perfcent columns, save to maxDict
def findNextTierInColumns(data, traffic, cu_traffic):
  # get rows that we need to check
  rowsToCheck = data.index.tolist()
  target_df = pd.DataFrame(columns=data.columns.tolist())
  csv_string = 'next_tier.csv'
  for row in rowsToCheck:
    row_add_to_next_tier = True
    for column in traffic:
      # init list of blocks to color 
      columnIndex = data.columns.get_loc(column)
      maxValue = data[column].max()
      threshold = maxValue * (1 - satThreshold)
      try:
         num = data.iloc[row, columnIndex]
      except:
         print ("Cannot access row : ", row, "column : ", column)
         print ("Rows to check : ", rowsToCheck)
      if num > threshold:
        row_add_to_next_tier = False
    for column in cu_traffic:
      # init list of blocks to color
      # only bother if greater than .7
      columnIndex = data.columns.get_loc(column)
      maxValue = data[column].max()
      if maxValue >= 50:
          threshold = maxValue * (1 - cuSatThreshold)
          try:
             num = data.iloc[row, columnIndex]
          except:
             print ("Cannot access row : ", row, "column : ", column)
          if num > threshold:
             row_add_to_next_tier = False
    if row_add_to_next_tier == True:
      target_df = target_df.append(data.iloc[row], ignore_index=True)
    #end columnfor
  #end rowfor
  #target_df.to_csv(csv_string, index = False, header=True)
  return target_df

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
    global result_df
    global si_passed
    global si_failed
    global no_cluster
    chosen_node_set = set(BASIC_NODE_LIST)
    node_chck =  any(elem in satTrafficList  for elem in subNodeTrafficToCheck)
    if not node_chck :
        sub_nodes = []
        for column in subNodeTrafficToCheck:
          columnIndex = testDF.columns.get_loc(column)
          cu_val = testDF.iloc[0, columnIndex]
          if cu_val >= 50:
             sub_nodes.append(column)
        print (sub_nodes)
        print ("calling createSubcluster :", short_name)
        sub_cluster_df = createSubcluster(peer_codelet_df, sub_nodes, short_name)
        sub_clstr_cdlt_count = sub_cluster_df.shape[0]
        if sub_clstr_cdlt_count >= 3:
            outputfile = short_name + 'SUB_Tier_'+str(codelet_tier) + "_SI.csv"
            norm = "row"
            title = "SI"
            target_df = pd.DataFrame()
            #print ("calling SI Compute with nodes :", chosen_node_set)
            compute_and_plot('XFORM', sub_cluster_df, outputfile, norm, title, chosen_node_set, target_df)
            peer_dfs = [sub_cluster_df,testDF]
            final_df = concat_ordered_columns(peer_dfs)
            if DO_DEBUG_LOGS:
               final_df.to_csv(short_name+'_sub_cluster_report.csv', index = True, header=True)
            result = test_and_plot_orig('ORIG', final_df, outputfile, norm, title, chosen_node_set, target_df, short_name)
            #print ("Sub_Cluster Result is : ", result)
            if result == True :
                print (short_name, "Passed the Sub_Cluster SI Test =>")
                si_passed +=1
                findUniqueTiers(sub_cluster_df, satTrafficList, codelet_tier)
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_nodes, 'SI_Result' : 'Outside Box',
                            'Saturation' : final_df.loc[final_df['short_name'] == short_name, 'Saturation'].item(), 'Intensity' : final_df.loc[final_df['short_name'] == short_name, 'Intensity'].item()}, 
                ignore_index = True) 
            else:
                print (short_name, "Failed the Sub_ClusterSI Test =>")
                si_failed +=1
                findUniqueTiers(sub_cluster_df, satTrafficList, codelet_tier)
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_nodes, 'SI_Result' : 'Inside Box',
                            'Saturation' : final_df.loc[final_df['short_name'] == short_name, 'Saturation'].item(), 'Intensity' : final_df.loc[final_df['short_name'] == short_name, 'Intensity'].item()},
                ignore_index = True)
        else:
            print (short_name, "Not enough codelets in the Sub_ClusterSI Test =>")
            no_cluster+=1
            findUniqueTiers(sub_cluster_df, satTrafficList, codelet_tier)
            result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                        'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_nodes, 'SI_Result' : 'No Sub Cluster'},  
            ignore_index = True)
    else :
        print (short_name, "How to do Sub_Cluster SI Test ??=>")
        si_failed+=1

def find_cluster(satSetDF, testDF, short_name, codelet_tier, all_clusters, all_test_codelets):
    global result_df
    global si_passed
    global si_failed
    global no_cluster
    global satThreshold
    peer_cdlt_count = 0
    dfs = [satSetDF,testDF]
    full_df = concat_ordered_columns(dfs)
    #full_df.to_csv(short_name + '_debug.csv', index = False, header=True)
    satTrafficList = []
    codelet_tier = codelet_tier + 1
    max_mem_traffic = testDF[[MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S, MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S]].max(axis=1)
    satThreshold = 0.1*codelet_tier
    mem_traffic_threshold = 0.1 * max_mem_traffic.item()
    tstcdlt_TrafficToCheck = []
    tstcdlt_TrafficToCheck.append(MetricName.RATE_FP_GFLOP_P_S)
    for column in memTrafficToCheck:
       columnIndex = testDF.columns.get_loc(column)
       val = testDF.iloc[0, columnIndex]
       if (val > mem_traffic_threshold):
          tstcdlt_TrafficToCheck.append(column)
    check_codlet_in_this_tier = checkCodeletTier(full_df, short_name, tstcdlt_TrafficToCheck, primaryCuTrafficToCheck, satTrafficList)

    if PRINT_COLOURED_TIERS:
       tier_book_path = short_name + "_tier.xlsx"
       tier_book = load_workbook(tier_book_path);
       highlightSheet = tier_book.create_sheet(short_name + "_" + str(codelet_tier), 0)
       sheet_title = short_name + "_" + str(codelet_tier) + "_" + "Highlights"
       for r in dataframe_to_rows(full_df, index=False, header=True):
          highlightSheet.append(r)
       findMaxInColumnsToColor(full_df, trafficToCheck, percentsToCheck)
       colorMaxInColumn(full_df, coloured_maxOfColumn, opBlue, highlightSheet)
       tier_book.save(tier_book_path)
    # Moved this out of if check so else part also have chosen_node_set defined.
    chosen_node_set = set(BASIC_NODE_LIST)
    if check_codlet_in_this_tier == True:
        #print (satTrafficList)
        peer_codelet_df = findPeerCodelets(satSetDF, trafficToCheck, primaryCuTrafficToCheck, satTrafficList, short_name)
        peer_cdlt_count = peer_codelet_df.shape[0]
        sat_rng_string = ''
        for elem in satTrafficList:
            sat_rng_string += elem
            sat_rng_string += ": ["
            sat_rng_string += str(peer_codelet_df[elem].max())
            sat_rng_string += "  "
            sat_rng_string += str(peer_codelet_df[elem].min())
            sat_rng_string += "], "
        if peer_cdlt_count >= 3:
            for elem in satTrafficList:
                if elem in CU_NODE_SET:
                    #print (CU_NODE_DICT[elem])
                    chosen_node_set.add(CU_NODE_DICT[elem])
            outputfile = short_name + 'Tier_'+str(codelet_tier) + "_SI.csv"
            norm = "row"
            title = "SI"
            target_df = pd.DataFrame()
            #print ("calling SI Compute with nodes :", chosen_node_set)
            #compute_and_plot('XFORM', peer_codelet_df, outputfile, norm, title, chosen_node_set, target_df)
            #satTrafficString = ''
            #for i, elem in enumerate(satTrafficList): 
            #  if i != len(satTrafficList) - 1: satTrafficString += str(elem) + ', '
            #  else: satTrafficString += str(elem)
            satTrafficString = ", ".join(map(str, satTrafficList))

            testDF[NonMetricName.SI_CLUSTER_NAME] = str(codelet_tier) + ' ' + satTrafficString
            testDF[NonMetricName.SI_SAT_NODES] = [chosen_node_set]*len(testDF)
            testDF[NonMetricName.SI_SAT_TIER] = codelet_tier
            peer_codelet_df[NonMetricName.SI_CLUSTER_NAME] = str(codelet_tier) + ' ' + satTrafficString
            peer_codelet_df[NonMetricName.SI_SAT_NODES] = [chosen_node_set]*len(peer_codelet_df)
            peer_codelet_df[NonMetricName.SI_SAT_TIER] = codelet_tier
            my_cluster_df, my_cluster_and_test_df, my_test_df = compute_only(peer_codelet_df, norm, testDF, chosen_node_set)
            all_test_codelets = all_test_codelets.append(my_test_df)
            # cluster_name = str(codelet_tier) + str(satTrafficList)
            cluster_name = str(codelet_tier) + ' ' + satTrafficString
            my_cluster_df[NonMetricName.SI_CLUSTER_NAME] = cluster_name
            peer_dfs = [peer_codelet_df,testDF]
            final_df = concat_ordered_columns(peer_dfs)
            if all_clusters.empty or cluster_name not in all_clusters[NonMetricName.SI_CLUSTER_NAME].values:
                all_clusters = all_clusters.append(my_cluster_df)
            if DO_DEBUG_LOGS:
                filename=short_name[-9:]
                re.sub('[^\w\-_\. ]', '_', filename)
                final_df.to_csv(filename + '_report.csv', index = True, header=True)
            #result = test_and_plot_orig('ORIG', final_df, outputfile, norm, title, chosen_node_set, target_df, short_name)
            result =True
            if result == True :
                print (short_name, "Passed the SI Test =>")
                si_passed +=1
                findUniqueTiers(peer_codelet_df, satTrafficList, codelet_tier)
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                   'Tier' : 'Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Range' : sat_rng_string, 'SI_Result' : 'Outside Box',
                   'Saturation' : final_df.loc[final_df['ShortName'] == short_name, 'Saturation'].item(), 'Intensity' : final_df.loc[final_df['ShortName'] == short_name, 'Intensity'].item()},  
                ignore_index = True) 
                if DO_SUB_CLUSTERING:
                   do_sub_clustering(peer_codelet_df, testDF, short_name, codelet_tier, satTrafficList)
            else:
                print (short_name, "Failed the SI Test =>")
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                            'Tier' : 'Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Range' : sat_rng_string, 'SI_Result' : 'Inside Box',
                            'Saturation' : final_df.loc[final_df['ShortName'] == short_name, 'Saturation'].item(), 'Intensity' : final_df.loc[final_df['ShortName'] == short_name, 'Intensity'].item()},  
                ignore_index = True)
                if DO_SUB_CLUSTERING:
                   do_sub_clustering(peer_codelet_df, testDF, short_name, codelet_tier, satTrafficList)
            if DO_DEBUG_LOGS:
                filename=short_name[-9:]
                re.sub('[^\w\-_\. ]', '_', filename)
                final_df.to_csv(filename+'_report.csv', index = True, header=True)
        else:
            # empty tuple more friendly to group by operations
            testDF[NonMetricName.SI_CLUSTER_NAME] = ''
            testDF[NonMetricName.SI_SAT_NODES] = [chosen_node_set]*len(testDF)
            all_test_codelets = all_test_codelets.append(testDF)
            print (short_name, "No Cluster for the SI Test =>")
            no_cluster+=1
            findUniqueTiers(peer_codelet_df, satTrafficList, codelet_tier)
            result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                        'Tier' : 'Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Range' : sat_rng_string, 'SI_Result' : 'No Cluster'},  
            ignore_index = True) 
    else:
        next_tier_df = findNextTierInColumns(satSetDF, trafficToCheck, primaryCuTrafficToCheck)
        #print ("next tier codelet count : ", next_tier_df.shape[0])
        if next_tier_df.shape[0] > 5 :
            all_clusters, all_test_codelets = find_cluster(next_tier_df, testDF, short_name, codelet_tier, all_clusters, all_test_codelets)
        else :
            # empty tuple more friendly to group by operations
            testDF[NonMetricName.SI_CLUSTER_NAME] = ''
            testDF[NonMetricName.SI_SAT_NODES] = [chosen_node_set]*len(testDF)
            all_test_codelets = all_test_codelets.append(testDF)
            print (short_name, "Last Tier: No Cluster for the SI Test =>")
            result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                        'Tier' : 'LastTier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'SI_Result' : 'No Cluster'},  
            ignore_index = True) 
    return all_clusters, all_test_codelets

def do_sat_analysis(satSetDF, testSetDF, chosen_node_set):
    all_clusters = pd.DataFrame()
    all_test_codelets = pd.DataFrame()
    short_name=''
    # Creating an empty Dataframe with column names only
    #print("Empty Dataframe ", dfObj, sep='\n')
    global satThreshold
    global cuSatThreshold
    codelet_tested = 0
    print ("Memory Node Saturation Threshold : ", satThreshold)
    print ("Control Node Saturation Threshold : ", cuSatThreshold)
    capsToRetain = [MetricName.capWUnit(n) for n in chosen_node_set]+[MetricName.CAP_ALLMAX_GB_P_S]
    #cols = satSetDF.columns.tolist() + list(set(KEY_METRICS) - set(satSetDF.columns.tolist()))+capsToRetain
    cols = set(satSetDF.columns) | set(KEY_METRICS) | set(capsToRetain)
    for i, row in testSetDF.iterrows():
        l_df = satSetDF
        testDF = pd.DataFrame(columns=cols)
        short_name = row[MetricName.SHORT_NAME]
        short_name = 'test-' + short_name
        row[MetricName.SHORT_NAME] = short_name
        testDF = testDF.append(row, ignore_index=False)[cols]
        testDF = testDF.astype({MetricName.TIMESTAMP: 'int64'})
        codelet_tested += 1
		    #find the saturation clusters
        all_clusters, all_test_codelets = find_cluster(satSetDF, testDF, short_name, 0, all_clusters, all_test_codelets)
        if RUN_SW_BIAS:
            sw_bias_df = compute_sw_bias(testDF)
            testDF = pd.merge(testDF, sw_bias_df)
            if DO_DEBUG_LOGS:
               filename=short_name[-9:]
               re.sub('[^\w\-_\. ]', '_', filename)
               testDF.to_csv(filename + '_sw_bias.csv', index = True, header=True)
    result_df.to_csv('Result_report.csv', index = True, header=True)
    print ("Total No. of codelets tested : ", codelet_tested)
    print ("Total No. of codelets Passed SI : ", si_passed)
    print ("Total No. of codelets Failed SI : ", si_failed)
    print ("Total No. of codelets without Cluster : ", no_cluster)
    print ("Total No. of Tiers : ", len(unique_tiers))
    print ("Total No. of unique clusters : ", len(unique_sat_node_clusters))
    stat_data = [{'Mem Threshold' : satThreshold, 'CU Threshold' : cuSatThreshold,
            'Codelets Tested' : codelet_tested, 'Passed' : si_passed, 'Failed' : si_failed,
            'No Cluster' : no_cluster, 'Tier Count' : len(unique_tiers), 'Cluster Count' : len(unique_sat_node_clusters)}]
    stats_df = pd.DataFrame(stat_data)
    my_file = Path("./statistcs.csv")
    if my_file.is_file():
       # file exists
       stats_df.to_csv('statistcs.csv', mode='a', header=False, index=False)
    else :
       stats_df.to_csv('statistcs.csv', mode='w', header=True, index=False)
    return all_clusters, all_test_codelets


def main(argv):
    inputfile = []
    # if 3 arg specified, assumes 3rd is threshold replacement
    # print("No of sys args : ", len(sys.argv))

    test_data_path = sys.argv[2]
    #optimal_data_path = gui_resource_path(os.path.join('clusters', 'tier1_L1.csv'))
    test_data_df = pd.read_csv(test_data_path)

    print("Read test data successful!")

    find_clusters(test_data_df, BASIC_NODE_SET)


if __name__ == "__main__":
    # csv to read should be first argument
    main(sys.argv[1:])
