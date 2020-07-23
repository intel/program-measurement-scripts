
#!/usr/bin/python3

from argparse import ArgumentParser
import pandas as pd

# TODO: refactor to capelib for this util
def read_csvfiles_as_df(inputfiles):
    in_data = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in inputfiles:
        cur_df = pd.read_csv(inputfile, delimiter=',')
        in_data = in_data.append(cur_df, ignore_index=True)
    return in_data

def read_csvfiles_as_lists(inputfiles):
    in_data = []
    for inputfile in inputfiles:
        cur_df = pd.read_csv(inputfile, delimiter=',')
        in_data.append(cur_df)
    return in_data

def assign_clusters(in_rows, clusters):
    # TODO: Add implementation to add the "cluster" column
    return in_rows

if __name__ == '__main__':
    parser = ArgumentParser(description='Assign clusters for codelets.')
    parser.add_argument('-i', nargs='+', help='the input summary csv files', required=True, dest='in_files')
    parser.add_argument('-c', nargs='+', help='the cluster csv files', required=True, dest='cluster_files')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output summary csv file with cluster column (default out.csv)', \
        dest='out_file')
    args = parser.parse_args()


    in_summary = read_csvfiles_as_df(args.in_files)
    clusters = read_csvfiles_as_list(args.cluster_files)
    out_rows = assign_clusters(in_summary, clusters)
    out_rows.to_csv(args.out_file, index=False)