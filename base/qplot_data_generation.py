#!/usr/bin/env python
import sys, getopt
import re
import os
import shutil
import csv
import openpyxl

script_path=os.path.realpath(__file__)
script_folder=os.path.dirname(script_path)
qplot_dist_folder=os.path.join(os.path.join(os.path.join(script_folder, ".."), "utils"), "QPlot")
qplot_dist_folder=os.path.realpath(os.path.join(qplot_dist_folder, "dist-7-23-2019"))


def isInt(s):
    try:
        int(s)
        return True
    except:
        return False

def isFloat(s):
    try:
        float(s)
        return True
    except:
        return False

def generate_qplot(inputfile, outputfile, qplot_html):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "QPROF_full"

    renameCpuGenDict={"Skylake Server": "SKYLAKE"}

    with open(inputfile) as f:
        reader = csv.reader(f, delimiter=',')
        rowNum=1
        cpuGenIndex=[]
        for row in reader:
            if rowNum == 1:
                cpuGenIndex=row.index("cpu.generation")
            else:
                renamedName = renameCpuGenDict[row[cpuGenIndex]]
                if renamedName:
                    row[cpuGenIndex]=renamedName
            # Fix data types
            row=[int(d) if isInt(d) else d for d in row]
            row=[float(d) if (isFloat(d) and type(d) == str)  else d for d in row]
            ws.append(row)
            rowNum += 1
    out_dir="/tmp"
    outfile=os.path.join(out_dir,'test.xlsx')
    wb.save(outfile)
    shutil.copytree(qplot_dist_folder, qplot_html)
    os.chdir(qplot_html)
    os.system("nodejs parse.js {}".format(outfile))
    print("QPLOT HTML: {}".format(qplot_html))


    
# Mostly copied from report_summary.py
def main(argv):
    if len(argv) != 6:
        print '\nERROR: Wrong number of arguments!\n'
        print 'Usage:\n  qplot_data_generation.py  -i <inputfile> (optionally) -o <outputfile>'
        sys.exit(2)
    inputfile = []
    outputfile = []
    qplot_html = []
    try:
        opts, args = getopt.getopt(argv, "hi:o:q:")
    except getopt.GetoptError:
        print '\nERROR: Wrong argument(s)!\n'
        print 'Usage:\n  qplot_data_generation.py  -i <inputfile> (optionally) -o <outputfile>'
        sys.exit(2)
    if len(args) != 0:
        print '\nERROR: Wrong argument(s)!\n'
        print 'Usage:\n  qplot_data_generation.py  -i <inputfile> (optionally) -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage:\n  qplot_data_generation.py  -i <inputfile> (optionally) -o <outputfile>'
            sys.exit()
        elif opt == '-i':
            inputfile.append(arg)
            matchobj = re.search(r'(.+?)\.csv', arg)
            if not matchobj:
              print 'inputfile should be a *.csv file'
              sys.exit()
            if matchobj and len(argv) == 2:
              outputfile.append(str(matchobj.group(1)) + '_qplot.xlsx')
        elif opt == '-o':
            outputfile.append(arg)
            matchobj = re.search(r'(.+?)\.xlsx', arg)
            if not matchobj:
              print 'outputfile should be a *.xlsx file'
              sys.exit()
        elif opt == '-q':
            qplot_html.append(arg)

    print 'Inputfile: ', inputfile[0]
    print 'Outputfile: ', outputfile[0]
    generate_qplot(inputfile[0], outputfile[0], qplot_html[0])        
        

if __name__ == "__main__":
    main(sys.argv[1:])
