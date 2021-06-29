import pickle
import numpy as np
import sys
import os
# Follow line seems to be needed to get the modules needed
#sys.path.insert(0, 'c:\\Users\\cwong29\\OneDrive - Intel Corporation\\working\\Development\\Cape Analyzer\\master\\cape-experiment-scripts\\base')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'base'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'si_exp'))

import unittest
import pandas as pd
from generate_SI import compute_only
#from sat_analysis import find_clusters
from sat_analysis import do_sat_analysis
from analyzer_model import SatAnalysisData
from metric_names import NonMetricName
from generate_SI import NODE_UNIT_DICT
from generate_SI import SiData
from capeplot import CapacityData
from test_automation import do_sat_analysis as do_sat_analysis_test_automation

class TestGenerateSi(unittest.TestCase):
    def test_demo_may2021_row_norm(self):
        root = os.path.join(os.path.dirname(__file__), 'data', 'generate_SI')
        with open(os.path.join(root, 'demo-may-2021-cluster_df_before.pkl'), 'rb') as infile: cur_cluster_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-run_df_before.pkl'), 'rb') as infile: cur_run_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-cluster_df_row_after.pkl'), 'rb') as infile: output_cluster_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-run_df_row_after.pkl'), 'rb') as infile: output_run_df = pickle.load(infile)
        #new_cluster_df, new_all_df, new_run_df = compute_only(cluster_df, 'matrix', cur_run_df, chosen_node_set = set(node_list))
        SiData(cur_run_df).set_chosen_node_set({'FLOP', 'SB', 'RS', 'L2', 'FE', 'LB', 'L3', 'VR', 'L1', 'RAM', 'LM', 'CU'}).set_norm("row").set_cluster_df(cur_cluster_df).compute()
        self.assertIn('Saturation', cur_run_df.columns)
        self.assertIn('Intensity', cur_run_df.columns)
        self.assertIn('SI', cur_run_df.columns)
        # There will be rounding difference potentially due to order of node as a set so use np.isclose() for comparison rather than using equals()
        self.assertTrue(np.isclose(cur_run_df[['Saturation', 'Intensity', 'SI']], output_run_df[['Saturation', 'Intensity', 'SI']], equal_nan=True).all())
        self.assertTrue(np.isclose(cur_cluster_df[['Saturation', 'Intensity', 'SI']], output_cluster_df[['Saturation', 'Intensity', 'SI']], equal_nan=True).all())

    def test_demo_may2021_matrix_norm(self):
        root = os.path.join(os.path.dirname(__file__), 'data', 'generate_SI')
        #cur_run_df = pd.read_csv(os.path.join(root, 'Test.csv'))
        #node_list=['L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]']
        #cur_run_df[NonMetricName.SI_SAT_NODES]=[node_list]*len(cur_run_df)
        with open(os.path.join(root, 'demo-may-2021-cluster_df_before.pkl'), 'rb') as infile: 
            cur_cluster_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-run_df_before.pkl'), 'rb') as infile: 
            cur_run_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-cluster_df_matrix_after.pkl'), 'rb') as infile: 
            output_cluster_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-run_df_matrix_after.pkl'), 'rb') as infile: 
            output_run_df = pickle.load(infile)
        #new_cluster_df, new_all_df, new_run_df = compute_only(cluster_df, 'matrix', cur_run_df, chosen_node_set = set(node_list))
        SiData(cur_run_df).set_chosen_node_set({'FLOP', 'SB', 'RS', 'L2', 'FE', 'LB', 'L3', 'VR', 'L1', 'RAM', 'LM', 'CU'}).set_norm("matrix").set_cluster_df(cur_cluster_df).compute()
        self.assertIn('Saturation', cur_run_df.columns)
        self.assertIn('Intensity', cur_run_df.columns)
        self.assertIn('SI', cur_run_df.columns)
        # There will be rounding difference potentially due to order of node as a set so use np.isclose() for comparison rather than using equals()
        self.assertTrue(np.isclose(cur_run_df[['Saturation', 'Intensity', 'SI']], output_run_df[['Saturation', 'Intensity', 'SI']], equal_nan=True).all())
        self.assertTrue(np.isclose(cur_cluster_df[['Saturation', 'Intensity', 'SI']], output_cluster_df[['Saturation', 'Intensity', 'SI']], equal_nan=True).all())

class TestSiAnalysis(unittest.TestCase):
    def test_demo_may2021(self):
        chosen_node_set = {'LB', 'CU', 'VR', 'FLOP', 'L1', 'FE', 'RS', 'L2', 'L3', 'LM', 'SB', 'RAM'}
        root = os.path.join(os.path.dirname(__file__), 'data', 'sat_analysis')
        with open(os.path.join(root, 'demo-may-2021-df_before.pkl'), 'rb') as infile:
            cur_df = pickle.load(infile)
        with open(os.path.join(root, 'demo-may-2021-df_after.pkl'), 'rb') as infile:
            output_df = pickle.load(infile)
        import time
        start = time.time()
        SatAnalysisData(cur_df).set_chosen_node_set(chosen_node_set).compute()
        end = time.time()
        # Before tuning, elapased times are : 
        #       83.6s, 92.7s, 80.9s, 78.4s,    79.1s : median = 80.9s
        # After removing redundant swbias calculation
        #       56.6s, 61.7s, 61.6s, 64.376s,  61.4s : median = 61.6s
        # AFter simplifying tiering calls
        #       6.4s,  9.1s,  7.9s,  8.9s,     9.1s  : median = 8.9s
        # More code vectorized
        #       5.0s,  4.4s,  4.5s,  4.7s,     4.8s  : median = 4.7s
        # Moved SI calculation out (vectorized)
        #       3.1s,  2.5s,  2.5s,  2.4s,     2.6s  : median = 2.6s
        # Finished removing the data point iterating loop
        #       1.6s,  1.2s,  1.2s,  1.2s,     1.2s, : median = 1.2s
        print(f'Elapsed Time = {end-start} sec')
        new_columns = {'Nd_ISA_EXT_TYPE', 'Nd_RHS', 'SiSatNodes', 'Neg_SW_Bias', 'Nd_Recurrence', 
                       'Pos_SW_Bias', 'Nd_clu_score', 'Nd_CNVT_OPS', 'Nd_FMA_OPS', 'Nd_VEC_OPS', 
                       'Normalized_Tier', 'SiClusterName', 'Net_SW_Bias', 'SiTier', 'Nd_DIV_OPS'}
        self.assertTrue(set(new_columns).issubset(set(cur_df.columns)))
        # Compare everything for strict equality
        self.assertTrue((cur_df[set(new_columns)-{'Normalized_Tier', NonMetricName.SI_SAT_NODES}]==(output_df[set(new_columns)-{'Normalized_Tier', NonMetricName.SI_SAT_NODES}])).all().all())
        # for sat nodes only expect match for cases with clusters
        cluster_found_mask= cur_df[NonMetricName.SI_CLUSTER_NAME] != ''
        self.assertTrue(cur_df.loc[cluster_found_mask, NonMetricName.SI_SAT_NODES].equals(output_df.loc[cluster_found_mask, NonMetricName.SI_SAT_NODES]))
        # Somehow the normalized Tier has rounding difference.
        naMask = cur_df['Normalized_Tier'].isna()
        self.assertTrue(np.isclose(cur_df.loc[~naMask,'Normalized_Tier'], output_df.loc[~naMask,'Normalized_Tier'], atol=0.02).all())

    def test_automation_standalone (self):
        root = os.path.join(os.path.dirname(__file__), 'data', 'sat_analysis')
        with open(os.path.join(root, 'test_automation-mainDataFrame.pkl'), 'rb') as infile: 
            input_mainDataFrame = pickle.load(infile)
        with open(os.path.join(root, 'test_automation-TestSetDF.pkl'), 'rb') as infile: 
            input_TestSetDF = pickle.load(infile)
        with open(os.path.join(root, 'test_automation-results.pkl'), 'rb') as infile: 
            expected_results = pickle.load(infile)
        results = do_sat_analysis_test_automation(input_mainDataFrame, input_TestSetDF)
        self.assertTrue(results.equals(expected_results))


    def test_repeated_calls_df (self):
        chosen_node_set = CapacityData.ALL_NODE_SET
        chosen_node_set_w_unit = {"{} {}".format(n, NODE_UNIT_DICT[n]) for n in chosen_node_set}
        root = os.path.join(os.path.dirname(__file__), 'data', 'sat_analysis')
        cur_run_df = pd.read_csv(os.path.join(root, 'empty_cluster_case.csv'))
        cluster_df1, si_df1 = do_sat_analysis(cur_run_df, chosen_node_set_w_unit)
        cluster_df2, si_df2 = do_sat_analysis(cur_run_df, chosen_node_set_w_unit)
        #cluster_df1, si_df1 = find_clusters(cur_run_df)
        # Run again to get the results
        #cluster_df2, si_df2 = find_clusters(cur_run_df)
        self.assertFalse(cluster_df1.empty)
        self.assertFalse(cluster_df2.empty)
        #self.assertTrue(cluster_df1.equals(cluster_df2))
        #self.assertTrue(si_df1.equals(si_df2))

if __name__ == '__main__':
    unittest.main()