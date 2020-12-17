import sys
import os
# Follow line seems to be needed to get the modules needed
#sys.path.insert(0, 'c:\\Users\\cwong29\\OneDrive - Intel Corporation\\working\\Development\\Cape Analyzer\\master\\cape-experiment-scripts\\base')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'base'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

import unittest
import pandas as pd
from generate_SI import compute_only
from sat_analysis import find_clusters
from metric_names import NonMetricName

class TestGenerateSi(unittest.TestCase):
    def test_compute_norm_row(self):
        root = os.path.join(os.path.dirname(__file__), 'data', 'generate_SI')
        cur_run_df = pd.read_csv(os.path.join(root, 'Test.csv'))
        cur_run_df[NonMetricName.SI_SAT_NODES]=[['L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]']]*len(cur_run_df)
        cluster_df = pd.read_csv(os.path.join(root, 'LORE-Optimal.csv'))
        new_cluster_df, new_all_df, new_run_df = compute_only(cluster_df, 'row', cur_run_df)
        self.assertIn('Saturation', new_all_df.columns)
        self.assertIn('Intensity', new_all_df.columns)
        self.assertTrue(new_cluster_df.append(new_run_df).equals(new_all_df))
        # Should add more to check values

    def test_compute_norm_matrix(self):
        root = os.path.join(os.path.dirname(__file__), 'data', 'generate_SI')
        cur_run_df = pd.read_csv(os.path.join(root, 'Test.csv'))
        cur_run_df[NonMetricName.SI_SAT_NODES]=[['L1 [GB/s]', 'L2 [GB/s]', 'L3 [GB/s]', 'FLOP [GFlop/s]']]*len(cur_run_df)
        cluster_df = pd.read_csv(os.path.join(root, 'LORE-Optimal.csv'))
        new_cluster_df, new_all_df, new_run_df = compute_only(cluster_df, 'matrix', cur_run_df)
        self.assertIn('Saturation', new_all_df.columns)
        self.assertIn('Intensity', new_all_df.columns)
        self.assertTrue(new_cluster_df.append(new_run_df).equals(new_all_df))
        # Should add more to check values

class TestSiAnalysis(unittest.TestCase):
    def test_repeated_calls_df (self):
        root = os.path.join(os.path.dirname(__file__), 'data', 'sat_analysis')
        cur_run_df = pd.read_csv(os.path.join(root, 'empty_cluster_case.csv'))
        cluster_df1, si_df1 = find_clusters(cur_run_df)
        # Run again to get the results
        cluster_df2, si_df2 = find_clusters(cur_run_df)
        self.assertFalse(cluster_df1.empty)
        self.assertFalse(cluster_df2.empty)
        self.assertTrue(cluster_df1.equals(cluster_df2))
        self.assertTrue(si_df1.equals(si_df2))

if __name__ == '__main__':
    unittest.main()