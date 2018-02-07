This document describes how to instrument a new code for analysis.

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

