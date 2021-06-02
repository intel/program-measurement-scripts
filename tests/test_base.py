import pickle
import numpy as np
import sys
import os
# Follow line seems to be needed to get the modules needed
#sys.path.insert(0, 'c:\\Users\\cwong29\\OneDrive - Intel Corporation\\working\\Development\\Cape Analyzer\\master\\cape-experiment-scripts\\base')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'base'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

import unittest
import pandas as pd
from generate_SI import compute_only
#from sat_analysis import find_clusters
from sat_analysis import do_sat_analysis
from sat_analysis import SatAnalysisData
from metric_names import NonMetricName
from generate_SI import NODE_UNIT_DICT
from generate_SI import SiData
from capeplot import CapacityData

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
        print(f'Elapsed Time = {end-start} sec')
        new_columns = {'Nd_ISA_EXT_TYPE', 'Nd_RHS', 'SiSatNodes', 'Neg_SW_Bias', 'Nd_Recurrence', 
                       'Pos_SW_Bias', 'Nd_clu_score', 'Nd_CNVT_OPS', 'Nd_FMA_OPS', 'Nd_VEC_OPS', 
                       'Normalized_Tier', 'SiClusterName', 'Net_SW_Bias', 'SiTier', 'Nd_DIV_OPS'}
        self.assertTrue(set(new_columns).issubset(set(cur_df.columns)))
        # Compare everything for strict equality
        self.assertTrue(cur_df[set(new_columns)-{'Normalized_Tier'}].equals(output_df[set(new_columns)-{'Normalized_Tier'}]))
        # Somehow the normalized Tier has rounding difference.
        self.assertTrue(np.isclose(cur_df['Normalized_Tier'], output_df['Normalized_Tier']).all())


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