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
import importlib
from pathlib import Path
from metric_names import NonMetricName
import os
# GUI import
from utils import resource_path as gui_resource_path

# For each codelets in current_codelets_runs_df, find their cluster
#   Store the name of the cluster to the SI_CLUSTER_NAME column
#   Also return the a data frame containing by appending all dataframe of the clusters annotated with their names
def find_clusters(current_codelets_runs_df, satThreshold = 0.10, cuSatThreshold = 0.25):
  # Below assumed all the codelets are associated with FE_tier1 cluster.  
  # Real implementation, should put the right cluster name
  current_codelets_runs_df[NonMetricName.SI_CLUSTER_NAME] = 'FE_tier1'

  # Load sample FE_tier1 cluster data.  
  # Real implementation should have found many cluster dataframes and with the name set to its cluster name
  sample_cluster_path = gui_resource_path(os.path.join('clusters', 'FE_tier1.csv'))
  sample_cluster_df = pd.read_csv(sample_cluster_path)
  sample_cluster_df[NonMetricName.SI_CLUSTER_NAME] = 'FE_tier1'

  # Appending all the cluster dataframe into one to return.  
  # GUI will be able to get individual cluster data frame by using the mask all_clusters[NonMetric_Name.SI_CLUSTER_NAME] == 'FE_tier1'
  all_clusters = pd.DataFrame()
  all_clusters = all_clusters.append(sample_cluster_df, ignore_index=True) 
  return all_clusters

# csv to read should be first argument
csvToRead = sys.argv[1]
csvTestSet = sys.argv[2]
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
DO_DEBUG_LOGS = True

CU_NODE_SET={'%frontend', '%lb', '%sb', '%lm', '%rs'}
CU_NODE_DICT={'%frontend':'FE', '%lb':'LB', '%sb':'SB', '%lm':'LM', '%rs':'RS'}

# No Frontend
#CU_NODE_SET={'%lb', '%sb', '%lm', '%rs'}
#CU_NODE_DICT={'%lb':'LB', '%sb':'SB', '%lm':'LM', '%rs':'RS'}

BASIC_NODE_LIST=['L1', 'L2', 'L3', 'FLOP', 'VR', 'RAM']

# memory traffic
trafficToCheck = [ "register_simd_rate_gb/s", "flop_rate_gflop/s", "l1_rate_gb/s", "l2_rate_gb/s", "l3_rate_gb/s", "ram_rate_gb/s" ]
memTrafficToCheck = [ "register_simd_rate_gb/s", "l1_rate_gb/s", "l2_rate_gb/s", "l3_rate_gb/s", "ram_rate_gb/s" ]
archIntensityToCheck = ["SIMD_MEM_Intensity", "FLOP_MEM_Intensity"]


# arith
#percentsToCheck = ["register_simd_rate_gb/s", "%ops[vec]", "%inst[vec]", "%prf", "%sb", "%rs", "%lb", "%rob", "%lm", "%frontend" ]
#percentsToCheck = [ "%sb", "%lm", "%frontend" , "%rs", "%lb"]
percentsToCheck = [ "%sb", "%lm", "%rs", "%lb"]
cuTrafficToCheck = [ "%sb", "%lm", "%lb"]
subNodeTrafficToCheck = [ "%sb", "%lm", "%lb", "%frontend", "%rs"]

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
def findMaxInColumnsToColor(data, main_traffic, cu_traffic, pyxlSheet):
  # get rows that we need to check
  rowsToCheck = data.index.tolist()
  # initialize the dictionary to hold the rows
  initDict(coloured_maxOfColumn, trafficToCheck)
  initDict(coloured_maxOfColumn, percentsToCheck)
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
        coloured_maxOfColumn[column].append(row);
  #endfor

  # percent only colored if above certain threshold
  for column in cu_traffic:
    columnIndex = data.columns.get_loc(column)
    maxValue = data[column].max()

    # only bother if greater than .7
    if maxValue >= 0.5:
      threshold = maxValue * (1 - cuSatThreshold)

      for row in rowsToCheck:
        num = data.iloc[row, columnIndex]

        if num >= threshold:
          coloured_maxOfColumn[column].append(row);
      #endfor
  #endfor
  #check SIMD intensity
  #for row in rowsToCheck:
  # columnIndex = data.columns.get_loc("SIMD_MEM_Intensity")
  #  if data.iloc[row, columnIndex] > 3:
  #    coloured_maxOfColumn["SIMD_MEM_Intensity"].append(row);

# Find max in traffic columns + perfcent columns, save to maxDict
def findUniqueTiers(data, satList, tier):
  global unique_sat_node_clusters
  global unique_tiers
  #print ("Calling findUniqueTiers with : ", satList)
  # get rows that we need to check
  sat_string = ''
  if 'register_simd_rate_gb/s' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'vr+'
  if 'l1_rate_gb/s' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'L1+'
  if 'l2_rate_gb/s' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'L2+'
  if 'l3_rate_gb/s' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'L3+'
  if 'ram_rate_gb/s' in satList:
      sat_string = sat_string + 'RAM+'

  if 'flop_rate_gflop/s' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'FLOP+'
  if '%frontend' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'FE+'
  if '%lm' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'LM+'
  if '%sb' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'SB+'
  if 'rs' in satList:
      sat_string = sat_string + 'tier_' + str(tier) + 'RS+'
  if '%lb' in satList:
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
  condition = satdata["short_name"] == testCdltName
  test_codelet_indx = index[condition]
  row = test_codelet_indx[0]
  #print (rowsToCheck)
  #print (rowsToCheck)
  #satdata.to_csv(testCdltName + '_debug.csv', index = False, header=True)
  short_nameInx = satdata.columns.get_loc('short_name')
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
    maxValue = satdata[column].max()
    threshold = maxValue * (1 - satThreshold)
    num = satdata.iloc[row, columnIndex]
    if num > threshold and threshold > 0.5:
      codelet_in_this_tier = True
      #print(short_name, " in current tier.")
      sat_traffic.append(column)
  #if codelet_in_this_tier == False:
    #print(short_name, " not in current tier.")
  return codelet_in_this_tier

# Find max in traffic columns + perfcent columns, save to maxDict
def findPeerCodelets(data, traffic, cu_traffic, satList, short_name):
  # get rows that we need to check
  initDict(maxOfColumn, satList)
  rowsToCheck = data.index.tolist()
  target_df = pd.DataFrame(columns=data.columns.tolist())
  csv_string = short_name + '_peer_codelet.csv'
  for row in rowsToCheck:
    for column in satList:
      # init list of blocks to color 
      columnIndex = data.columns.get_loc(column)
      maxValue = data[column].max()
      if column in cu_traffic:
          if maxValue >= 0.5:
              threshold = maxValue * (1 - cuSatThreshold)
              num = data.iloc[row, columnIndex]
              if num > threshold:
                 maxOfColumn[column].append(row);
      else:
          threshold = maxValue * (1 - satThreshold)
          num = data.iloc[row, columnIndex]
          if num > threshold:
            maxOfColumn[column].append(row);
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
          if num <= 0.5:
              maxOfColumn[column].append(row);
  else:
      for row in rowsToCheck:
        #print (row)
        #print (subSatList)
        for column in subNodeTrafficToCheck and subSatList:
          # init list of blocks to color 
          columnIndex = data.columns.get_loc(column)
          num = data.iloc[row, columnIndex]
          if num >= 0.5:
              maxOfColumn[column].append(row);
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
      if maxValue >= 0.7:
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
          if cu_val >= 0.5:
             sub_nodes.append(column)
        print (sub_nodes)
        print ("calling createSubcluster :", short_name)
        sub_cluster_df = createSubcluster(peer_codelet_df, sub_nodes, short_name)
        sub_clstr_cdlt_count = sub_cluster_df.shape[0]
        if sub_clstr_cdlt_count >= 2:
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
                            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_nodes, 'SI_Result' : 'Pass'},  
                ignore_index = True) 
            else:
                print (short_name, "Failed the Sub_ClusterSI Test =>")
                si_failed +=1
                findUniqueTiers(sub_cluster_df, satTrafficList, codelet_tier)
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : sub_clstr_cdlt_count,
                            'Tier' : 'SUB_Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Sub_Node' : sub_nodes, 'SI_Result' : 'Fail'},  
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

def find_cluster(satSetDF, testDF, short_name, codelet_tier):
    global result_df
    global si_passed
    global si_failed
    global no_cluster
    peer_cdlt_count = 0
    dfs = [satSetDF,testDF]
    full_df = concat_ordered_columns(dfs)
    #full_df.to_csv(short_name + '_debug.csv', index = False, header=True)
    satTrafficList = []
    codelet_tier = codelet_tier + 1;
    max_mem_traffic = testDF[["l1_rate_gb/s", "l2_rate_gb/s", "l3_rate_gb/s", "ram_rate_gb/s"]].max(axis=1)
    mem_traffic_threshold = 0.1 * max_mem_traffic.item()
    tstcdlt_TrafficToCheck = []
    tstcdlt_TrafficToCheck.append("flop_rate_gflop/s")
    for column in memTrafficToCheck:
       columnIndex = testDF.columns.get_loc(column)
       val = testDF.iloc[0, columnIndex]
       if (val > mem_traffic_threshold):
          tstcdlt_TrafficToCheck.append(column)
    check_codlet_in_this_tier = checkCodeletTier(full_df, short_name, tstcdlt_TrafficToCheck, percentsToCheck, satTrafficList)

    tier_book = openpyxl.Workbook();
    highlightSheet = tier_book.active
    highlightSheet.title = "Highlights"
    findMaxInColumnsToColor(full_df, tstcdlt_TrafficToCheck, percentsToCheck, highlightSheet)
    colorMaxInColumn(full_df, maxOfColumn, opBlue, highlightSheet)
    #tier_book.save("tier.xlsx")
    if check_codlet_in_this_tier == True:
        #print (satTrafficList)
        peer_codelet_df = findPeerCodelets(satSetDF, trafficToCheck, percentsToCheck, satTrafficList, short_name)
        peer_cdlt_count = peer_codelet_df.shape[0]
        chosen_node_set = set(BASIC_NODE_LIST)
        sat_rng_string = ''
        for elem in satTrafficList:
            sat_rng_string += elem
            sat_rng_string += ": ["
            sat_rng_string += str(peer_codelet_df[elem].max())
            sat_rng_string += "  "
            sat_rng_string += str(peer_codelet_df[elem].min())
            sat_rng_string += "], "
        if peer_cdlt_count >= 2:
            for elem in satTrafficList:
                if elem in CU_NODE_SET:
                    #print (CU_NODE_DICT[elem])
                    chosen_node_set.add(CU_NODE_DICT[elem])
            outputfile = short_name + 'Tier_'+str(codelet_tier) + "_SI.csv"
            norm = "row"
            title = "SI"
            target_df = pd.DataFrame()
            #print ("calling SI Compute with nodes :", chosen_node_set)
            compute_and_plot('XFORM', peer_codelet_df, outputfile, norm, title, chosen_node_set, target_df)
            peer_dfs = [peer_codelet_df,testDF]
            final_df = concat_ordered_columns(peer_dfs)
            if DO_DEBUG_LOGS:
                final_df.to_csv(short_name+'_report.csv', index = True, header=True)
            result = test_and_plot_orig('ORIG', final_df, outputfile, norm, title, chosen_node_set, target_df, short_name)
            if result == True :
                print (short_name, "Passed the SI Test =>")
                si_passed +=1
                findUniqueTiers(peer_codelet_df, satTrafficList, codelet_tier)
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                            'Tier' : 'Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Range' : sat_rng_string, 'SI_Result' : 'Pass'},  
                ignore_index = True) 
            else:
                print (short_name, "Failed the SI Test =>")
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                            'Tier' : 'Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Range' : sat_rng_string, 'SI_Result' : 'Fail'},  
                ignore_index = True)
                if DO_SUB_CLUSTERING:
                   do_sub_clustering(peer_codelet_df, testDF, short_name, codelet_tier, satTrafficList)
        else:
            print (short_name, "No Cluster for the SI Test =>")
            no_cluster+=1
            findUniqueTiers(peer_codelet_df, satTrafficList, codelet_tier)
            result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                        'Tier' : 'Tier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'Sat_Range' : sat_rng_string, 'SI_Result' : 'No Cluster'},  
            ignore_index = True) 
    else:
        next_tier_df = findNextTierInColumns(satSetDF, trafficToCheck, percentsToCheck)
        #print ("next tier codelet count : ", next_tier_df.shape[0])
        if next_tier_df.shape[0] > 5 :
            find_cluster(next_tier_df, testDF, short_name, codelet_tier)
        else :
                print (short_name, "Last Tier: No Cluster for the SI Test =>")
                result_df = result_df.append({'short_name' : short_name, 'peer_codelet_cnt' : peer_cdlt_count,
                            'Tier' : 'LastTier_'+str(codelet_tier), 'Sat_Node' : satTrafficList, 'SI_Result' : 'No Cluster'},  
                ignore_index = True) 

def do_sat_analysis(satSetDF,testSetDF):
    short_name=''
    # Creating an empty Dataframe with column names only
    #print("Empty Dataframe ", dfObj, sep='\n')
    codelet_tested = 0;
    print ("Memory Node Saturation Threshold : ", satThreshold)
    print ("Control Node Saturation Threshold : ", cuSatThreshold)
    for i, row in testSetDF.iterrows():
        l_df = satSetDF
        testDF = pd.DataFrame(columns=satSetDF.columns.tolist())
        short_name = row['short_name']
        short_name = 'test-' + short_name
        row['short_name'] = short_name
        testDF = testDF.append(row, ignore_index=False)[satSetDF.columns.tolist()]
        codelet_tested += 1;
        find_cluster(satSetDF, testDF, short_name, 0)
        #print ("codelet_tested = ", codelet_tested, " Passed = ", si_passed, " Failed = ", si_failed, " No Cluster = ", no_cluster)
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


def main(argv):
    inputfile = []
    global satThreshold
    global cuSatThreshold
  # if 3 arg specified, assumes 3rd is threshold replacement
    #print("No of sys args : ", len(sys.argv))
    if (len(sys.argv) >= 5):
      satThreshold = float(sys.argv[3])
      cuSatThreshold = float(sys.argv[4])

    print("Attempting to read", csvToRead)

    # read into pandas
    mainDataFrame = pd.read_csv(csvToRead)
    TestSetDF = pd.read_csv(csvTestSet)

    print("Read successful!")

    # save original dataframe
    originalDataFrame = mainDataFrame

    # SIMD_RATE divided by max traffic column for memory
    addAfterColumn = mainDataFrame.columns.get_loc("ram_rate_gb/s") + 1
    mainDataFrame.insert(addAfterColumn, "SIMD_MEM_Intensity",
      mainDataFrame["register_simd_rate_gb/s"] / mainDataFrame[["l1_rate_gb/s", "l2_rate_gb/s", "l3_rate_gb/s", "ram_rate_gb/s"]].max(axis=1))

    # FLOP_RATE divided by max traffic column for memory
    addAfterColumn = mainDataFrame.columns.get_loc("flop_rate_gflop/s") + 1
    mainDataFrame.insert(addAfterColumn, "FLOP_MEM_Intensity",
    mainDataFrame["flop_rate_gflop/s"] / mainDataFrame[["l1_rate_gb/s", "l2_rate_gb/s", "l3_rate_gb/s", "ram_rate_gb/s"]].max(axis=1)/8)

    do_sat_analysis(mainDataFrame, TestSetDF)


if __name__ == "__main__":
    main(sys.argv[1:])
