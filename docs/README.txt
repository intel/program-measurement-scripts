This document describes how to instrument a new code for analysis.

1) Put the source files to a directory (say /path/to/source/<codelet_name>)
2) Ensure the code will be compiled successfully by a "make" command, so a Makefile source also be in /path/to/source.
3) Suppose the compiled binary is called run_kernel.  Check and see run_kernel can be executed.
4) The loop to be analyzed should be inside a function f() eventually called by the main program.

Create codelet.meta with 4 lines:
application name=<App name>
batch name=<Batch name>
code name=<Code name>
codelet name=<codelet_name>

where <Codelet name> is the name of the kernel.  It should be the same as this directory name.  For
<App name>, <Batch name> and <Code name>, those are hierachical information describing the kernel.

<?xml version="1.0" ?>
<codelet>
        <language value=<language of source>/>
        <label name=<codelet_name>/>
        <function name=<loop containing function>/>
        <binary name=<binary>/>
where 
<language of source> describe the source language.
<codelet_name> should be consistent with the path name and the codelet name in codelet.meta.
<loop containing function> is the function where the loop to analyze is located.  In this example, it will be f.
<binary> is the executable name built by the Makefile.  In this example, it is run_kernel.


1)	create a directory structure like the NR-codelets 
a.	Take a look at codelet.meta and codelet.conf to follow its format 
2)	Put your code in the codelet directory with instrument like balanc_3_de program.  ( I will include a sample below).
a.	With the measure_init_(), measure_start_() and measure_end_() around the kernel.
b.	The main function can read “codelet.data” file with “<repetition> <data>” as the format.
i.	<repetition> is an integer about repeating the kernel execution
ii.	<data> specify the input data for the kernels.  For NR codelet, it is an integer specifying array size.  For graph algorithm, it can be data file name.  We can even encode some other things specific to the kernel.
3)	Have your program built in the same way as balanc_3_de – the script and assume a simple make command to build the code you want to analyze.  

I am including an example below for your information:
14   int measure_it;  // not used for this code currently
15   read_infile_from_codelet_data (input_dir, infile_buffer, &repetitions, &measure_it);
16 
17   Graph* graph = new Graph();
18    19   if (!graph->read_file_ggr(infile_buffer, NoEdgeData())) {
20     std::abort();
21   }
22 
23  …
25  
26   measure_init_();
27   measure_start_();
28   for (int i = 0; i < repetitions; i++) {
29     LabelVec* labelVec = new LabelVec(graph->num_nodes, 0);
30     ccPullTopoSync(*graph, *labelVec, *stats); 
31   }
32   measure_stop_();

