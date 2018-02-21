This document describes how to instrument a new code for analysis.

1) Put the source files to a directory (say /path/to/source/<codelet_name>)
2) Ensure the code will be compiled successfully by a "make" command, so a Makefile source also be in /path/to/source.  Also the script will do "make clean" to clean up object files.
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

Probe insertion just before and after the kernel call:

For Fortran:

CALL measure_init()
CALL measure_start()
 
        CALL f (...)
 
 CALL measure_stop()
 
For C:

measure_init_ ();
measure_start_ ();
 
    f (...);
 
measure_stop_ ();

Note for C, the probe function names has trailing underscores ("_").

Update the Makefile to provide hook for script to link probe library by 
1) adding a line LIBS=-lmeasure
2) inserting "$(LIBS) -L$(LIBPATH)" in the command building the binary.  

For example:
LIBS=-lmeasure
...
$(EXEC): cmodule.o codelet.o cutil.o getticks.o driver.o
        $(CF) -o $@ $^ $(LDFLAGS)  $(LIBS) -L$(LIBPATH)


Test this by running
make LIBPATH=/path/to/script-directory/utils/codeletProbe

Test and run binary 
cat time.out

There should be a number being the cycle count for executing the loop.


The script will generate an input file for the program to read
“codelet.data”.  The format is a single line with "<repetition> <data>”
where
<repetition> is a integer - it will be the number of repetition to be done to run the kernel (f() in this case).  The script will make use of this repetition to ensure the kernel is executed long enough.
<data> is a string - the program is expected to be able to parse/ignore it to instruct the program about data loading/algorithm choosing/etc.

Below is a typical example of the code 



   // read "codelet.data" file for repetition and data file name
   read_infile_from_codelet_data (input_dir, infile_buffer, &repetitions, &measure_it);
 
   Graph* graph = new Graph();
   if (!graph->read_file_ggr(infile_buffer, NoEdgeData())) {
     std::abort();
   }
 
  …
  
   measure_init_();
   measure_start_();
   for (int i = 0; i < repetitions; i++) {
        f();
   }
   measure_stop_();

Update the script so it can locate the code
Remember the codelet is located under /path/to/source/<codelet_name>

Add, to the script, 
fill_codelet_maps <prefix> <default datasizes>
where <prefix> is the path to the parent directory of the codelet directory.  In this example, it would be /path/to.  
<default datasizes> will be some default data size to run the code.  It can be overriden by setting name2sizes[<codelet_name>]=... .




