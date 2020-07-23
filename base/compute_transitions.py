#!/usr/bin/python3

from argparse import ArgumentParser
import pandas as pd

def read_transitions(in_files):
    in_transitions = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in inputfiles:
        cur_df = pd.read_csv(inputfile, delimiter=',')
        in_transitions = in_transitions.append(cur_df, ignore_index=True)
    return in_transitions

    # Now compute different kinds of transitions
    # End-to-end transitions capturing very beginning to very end transitions excluding all intermediate ones
def compute_end2end_transitions(in_transitions):
    pass

    # Collect all n-steps transitions (if n = Inf, this will compute a transitive clousure - all transitions inferable)
def compute_nsteps_transitions(in_transitions, nsteps):
    pass
    
    # Collect all transitions with a specific "Difference"
def select_transitions_by_difference(in_transitions, difference):
    pass


if __name__ == '__main__':
    parser = ArgumentParser(description='Compute transition given input codelet mapping file.')
    parser.add_argument('-i', nargs='+', help='the input mapping csv file', required=True, dest='in_files')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output mapping csv file (default out.csv)', \
        dest='out_file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--end-to-end', action='store_true', help='compute end-to-end transitions', dest='end_to_end')
    group.add_argument('--nsteps', nargs='?', type=int, help='number of steps', dest='nsteps')
    group.add_argument('--difference', nargs='?', help='select transition for difference', dest='difference')
    args = parser.parse_args()
    
    transitions = read_transitions(args.in_files)
    if args.end_to_end:
        out_transitions = compute_end2end_transitions(transitions)
    elif args.nsteps:
        out_transitions = compute_nsteps_transitions(transitions, args.nsteps)
    else:
        out_transitions = select_transitions_by_difference(transitions, args.difference)

    out_transitions.to_csv(args.out_file, index=False)