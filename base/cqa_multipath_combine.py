#!/usr/bin/env python

from __future__ import division
import re
import sys, getopt
import csv
import traceback

def get_num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def main():
  with open ('loops.csv', 'rU') as input_csvfile:
    csvreader = csv.reader(input_csvfile, delimiter=',')
    with open ('loops_avg.csv', 'wb') as output_csvfile:
      csvwriter = csv.writer(output_csvfile)
      csvwriter.writerow(next(csvreader)) # copy header
      input_csvfile.seek(0)
      num_cols = len(next(csvreader))
      avg_data = [0] * num_cols
      num_paths=0

      for input_row in csvreader:
        num_paths+=1
        for index, col in enumerate(input_row):
          if col.replace('.','',1).isdigit() and not isinstance(avg_data[index], str):
            avg_data[index]+=get_num(col)
          else:
            avg_data[index]=col

      for index, col in enumerate(avg_data):
        if  not isinstance(col, str):
          avg_data[index]/=num_paths
      try:
        csvwriter.writerow(avg_data)
      except:
        # skip failures to generate partial reports
        print "WARNING: Unexpected error!"
        traceback.print_exc()

if __name__ == "__main__":
    main()
