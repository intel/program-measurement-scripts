#!/usr/bin/python3

from argparse import ArgumentParser
import pandas as pd
import networkx as nx
import numpy as np

def read_transitions(in_files):
    in_transitions = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in in_files:
        cur_df = pd.read_csv(inputfile, delimiter=',')
        in_transitions = in_transitions.append(cur_df, ignore_index=True)
    return in_transitions

# Get all the sources (nodes without incoming edges)
def get_sources(in_transitions):
    # Perform an outer join with indicator column Exist
    # left_only: Before does not have a match in After (node not pointed to => src)
    # both: Before matches After (intermediate nodes)
    # right_only: After does not have a match in Before (node not pointer to other => dest)
    cmp_transitions = pd.merge(in_transitions[['Before Name','Before Timestamp']], \
        in_transitions[['After Name', 'After Timestamp']], \
            left_on=['Before Name', 'Before Timestamp'], \
                right_on=['After Name', 'After Timestamp'], how='outer', indicator='Exist')
    cmp_transitions = cmp_transitions[cmp_transitions.Exist == 'left_only'].drop_duplicates() 
    return cmp_transitions[['Before Name', 'Before Timestamp']]

# Get all the final dests (nodes without outgoing edges)
def get_dests(in_transitions):
    # Perform an outer join with indicator column Exist
    # left_only: Before does not have a match in After (node not pointed to => src)
    # both: Before matches After (intermediate nodes)
    # right_only: After does not have a match in Before (node not pointer to other => dest)
    cmp_transitions = pd.merge(in_transitions[['Before Name','Before Timestamp']], \
        in_transitions[['After Name', 'After Timestamp']], \
            left_on=['Before Name', 'Before Timestamp'], \
                right_on=['After Name', 'After Timestamp'], how='outer', indicator='Exist')
    cmp_transitions = cmp_transitions[cmp_transitions.Exist == 'right_only'].drop_duplicates() 
    return cmp_transitions[['After Name', 'After Timestamp']]

# Limit transitions to all the sources provided
def limit_sources(in_transitions, srcs):
    return in_transitions.merge(srcs, on=['Before Name', 'Before Timestamp'], how='inner')

# Limit transitions to all the destinations provided
def limit_dests(in_transitions, dests):
    return in_transitions.merge(dests, on=['After Name', 'After Timestamp'], how='inner')

# Add one more hop of transition from in_transtions to cur_transition and return it
def adv_transitions(cur_transitions, in_transitions):
    combined_transitions = cur_transitions.merge(in_transitions, left_on=['After Name', 'After Timestamp'],\
        right_on=['Before Name', 'Before Timestamp'], how='inner')
    # The join will produce "*_x" from cur_transitions and "*_y" from in_transitions
    # Combine the join results for new transitions
    # Difference = Difference_x;Difference_y
    # Before = Before_x
    # After = After_y
    new_transitions = combined_transitions[['Before Name_x', 'Before Timestamp_x', \
        'After Name_y', 'After Timestamp_y']]
    new_transitions = new_transitions.rename(columns={\
        "Before Name_x" : "Before Name", "Before Timestamp_x" : "Before Timestamp", \
            "After Name_y" : "After Name", "After Timestamp_y" : "After Timestamp"})
    new_transitions['Difference'] = combined_transitions['Difference_x'] + ';' + combined_transitions['Difference_y']
    return cur_transitions.append(new_transitions, ignore_index=True).drop_duplicates()

# check whether two transitions are the same
def eq_transitions(trans1, trans2):
    # Perform an outer join with indicator column Exist
    # left_only: rows only in trans1
    # both: Before common rows in both transitions 
    # right_only: rows only in trans2
    cmp_transitions = pd.merge(trans1, trans2, on=list(trans1.columns), how='outer', indicator='Exist')
    mask = cmp_transitions.Exist == 'both'
    # Return True if all True
    return mask.all()

    # Now compute different kinds of transitions
    # Max speedup transitions capturing transitions deliverying max speedup excluding all intermediate ones
def compute_maxspeedup_transitions(in_transitions, speedup_name="Speedup[FLOP Rate (GFLOP/s)]", dests=None):
    # Some mockup speedup code only for debugging purpose (commented out)
    #rng = np.random.RandomState(seed=5)
    #numRows = in_transitions.shape[0]
    #in_transitions[speedup_name]=rng.randint(1,11, size=(numRows,1))

    # For shortest path algorithm applied to max speedup, compute log(1/speedup) = -log(speedup)
    # then shortest path => minimize -log(speedup) => maximize log(speedup) => maximize speedup
    # Also, additive -log(speedup) <==> multiplicative speedup
    # Fix the erroneous speedups before proceeding
    # For Inf => Use a big floating point (e.g. 1e9)
    # For nan => Use 1
    BIG_SPEEDUP = 1e9
    in_transitions.loc[in_transitions[speedup_name].isnull(), speedup_name] = 1
    in_transitions.loc[~np.isfinite(in_transitions[speedup_name]), speedup_name] = BIG_SPEEDUP

    in_transitions['Before']=list(zip(in_transitions['Before Name'], in_transitions['Before Timestamp']))
    in_transitions['After']=list(zip(in_transitions['After Name'], in_transitions['After Timestamp']))
    # All speedup columns except the chosen one
    other_speedup_columns = [s for s in in_transitions.columns if s.startswith('Speedup[') and s != speedup_name]
    in_transitions['log_inv_speedup'] = -np.log(in_transitions[speedup_name])
    G = nx.from_pandas_edgelist(in_transitions, 'Before', 'After', \
        [speedup_name, 'log_inv_speedup', 'Difference']+other_speedup_columns, create_using=nx.DiGraph())

    # Some drawing code for debugging purpose as well.
    #pos = nx.planar_layout(G)
    #nx.draw_networkx(G,pos)
    #labels = nx.get_edge_attributes(G, 'log_inv_speedup')
    #nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    # Convert to graph and then compute all pair longest path with log (speedup), then convert back
    # finally limit outgoing edges from sources only
    path_predecessors, path_lengths = nx.floyd_warshall_predecessor_and_distance(G, weight = 'log_inv_speedup')
    srcs = get_sources(in_transitions)
    srcs['Src']=list(zip(srcs['Before Name'], srcs['Before Timestamp']))
    if dests is not None:
        dests['Dest']=list(zip(dests['After Name'], dests['After Timestamp']))

    soln_src_names = []
    soln_src_timestamps = []
    soln_dest_names = []
    soln_dest_timestamps = []
    soln_dest_speedups = []
    soln_diffs = []
    # This will be a list of array - each row is for codelet
    soln_other_speedups = []
    for src in list(srcs['Src']):
        dest_lengths = path_lengths[src]
        if dests is not None:
            dest_lengths = {k:dest_lengths[k] for k in dests['Dest']}
        min_dest, min_inv_speedup = min(dest_lengths.items(), key=lambda x: x[1])
        min_dest_name, min_dest_timestamp = min_dest
        src_name, src_timestamp = src
        soln_src_names.append(src_name)
        soln_src_timestamps.append(src_timestamp)
        soln_dest_names.append(min_dest_name)
        soln_dest_timestamps.append(min_dest_timestamp)
        # min inv speedup is the max 1/inv speedup
        soln_dest_speedups.append(np.exp(-min_inv_speedup))
        soln_path = nx.reconstruct_path(src, min_dest, path_predecessors)
        # Need to reconstruct the Difference by going along the path
        soln_diff = ''
        # This will be a list of list - each element is a row of speedups
        all_speedups = []
        for bf, af in zip(soln_path[:-1], soln_path[1:]):
            soln_diff += (G[bf][af]['Difference']+';')
            all_speedups.append([G[bf][af].get(key) for key in other_speedup_columns])
        soln_other_speedups.append(np.array(all_speedups).prod(axis=0))
        # remove last ';'
        soln_diffs.append(soln_diff[:-1])
    results = pd.DataFrame({'Before Name': soln_src_names, 'Before Timestamp': soln_src_timestamps, \
        'After Name': soln_dest_names, 'After Timestamp': soln_dest_timestamps, 'Difference' : soln_diffs, \
            speedup_name : soln_dest_speedups })
    soln_other_speedups_df = pd.DataFrame(data=np.array(soln_other_speedups), columns=other_speedup_columns)
    return pd.concat([results, soln_other_speedups_df], axis=1)

    # End-to-end transitions capturing very beginning to very end transitions excluding all intermediate ones
def compute_end2end_transitions(in_transitions, speedup_name="Speedup[FLOP Rate (GFLOP/s)]"):
    dests = get_dests(in_transitions)
    return compute_maxspeedup_transitions(in_transitions, speedup_name, dests)
    # srcs = get_sources(in_transitions)
    # cur_transitions = limit_sources(in_transitions, srcs)
    # while True:
    #     prv_transitions = cur_transitions
    #     cur_transitions = adv_transitions(cur_transitions, in_transitions)
    #     if eq_transitions(prv_transitions, cur_transitions):
    #         break
    # cur_transitions = limit_sources(cur_transitions, srcs)
    # cur_transitions = limit_dests(cur_transitions, dests)
    # return cur_transitions

    # Collect all n-steps transitions (if n = Inf, this will compute a transitive clousure - all transitions inferable)
def compute_nsteps_transitions(in_transitions, nsteps):
    srcs = get_sources(in_transitions)
    cur_transitions = limit_sources(in_transitions, srcs)
    for i in range(nsteps):
        prv_transitions = cur_transitions
        cur_transitions = adv_transitions(cur_transitions, in_transitions)
    cmp_transitions = pd.merge(cur_transitions, prv_transitions, on=list(cur_transitions.columns), \
        how='left', indicator='Exist')
    # Retain only rows not presense in both (should be the new rows in cur_transitions)
    cmp_transitions = cmp_transitions[cmp_transitions.Exist != 'both']
    cmp_transitions.drop('Exist', axis=1, inplace=True)
    return cmp_transitions
    
    # Collect all transitions with a specific "Difference"
def select_transitions_by_difference(in_transitions, difference):
    return in_transitions[in_transitions['Difference'].isin(difference)]


if __name__ == '__main__':
    parser = ArgumentParser(description='Compute transition given input codelet mapping file.')
    parser.add_argument('-i', nargs='+', help='the input mapping csv file (with speedups)', required=True, dest='in_files')
    parser.add_argument('-s', nargs='?', default='Speedup[FLOP Rate (GFLOP/s)]', \
        help='Speedup metric to use (default Speedup[FLOP Rate (GFLOP/s)])', dest='speedup_name')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output mapping csv file (default out.csv)', \
        dest='out_file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--end-to-end', action='store_true', help='compute end-to-end transitions', dest='end_to_end')
    group.add_argument('--max-speedup', action='store_true', help='compute transitions for max speedup', dest='max_speedup')
    group.add_argument('--nsteps', nargs='?', type=int, help='number of steps', dest='nsteps')
    group.add_argument('--difference', nargs='+', help='select transition for difference', dest='difference')
    args = parser.parse_args()
    
    transitions = read_transitions(args.in_files)
    if args.end_to_end:
        out_transitions = compute_end2end_transitions(transitions, args.speedup_name)
    elif args.max_speedup:
        out_transitions = compute_maxspeedup_transitions(transitions, args.speedup_name)
    elif args.nsteps:
        out_transitions = compute_nsteps_transitions(transitions, args.nsteps)
    else:
        out_transitions = select_transitions_by_difference(transitions, args.difference)

    out_transitions.to_csv(args.out_file, index=False)