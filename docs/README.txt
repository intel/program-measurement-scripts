This document describes how to instrument a new code for analysis.  It is assumed steps described in docs/setup.txt have been followed before this document.

A. DEFAULT USAGE

    1) Put the source files to a directory (say /path/to/source/<codelet_name>)
    2) Instrument code to put measurement probes.
    3) Ensure the code will be compiled successfully by a "make" command, so a Makefile source also be in /path/to/source.  Also the script will do "make clean" to clean up object files.
    4) Suppose the compiled binary is called run_kernel.  Check and see run_kernel can be executed.  The loop to be analyzed should be inside a function f() eventually called by the main program.

    I. SETTING UP Code to run
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

    II. INSTRUMENTATION of Code
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

        For C++:

        extern "C" {
            void measure_init_ ();
            void measure_start_ ();
            void measure_stop_ ();
        }

        measure_init_ ();
        measure_start_ ();
        
            f (...);
        
        measure_stop_ ();

        Note for C, the probe function names has trailing underscores ("_").

    III. BUILDING of Code
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

    IV. RUNING of Code
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


B. CUSTOMIZATION of BUILDING (III) and RUNNING (IV) of code

    I. CUSTOMIZATION of Code BUILDING
        This is done by modifying build_codelet() function inside the topmost script.  The default implementation used make to
        build the code.  This could be changed to abitrarily complicated build process.  On the other hand, the 
        contract of this function is simply: $codelet_name is under ${build_folder} on return of the function.

        Note that it is assumed the code to be built will be dynamically linked to the base probe library pointed 
        by ${BASE_PROBE_FOLDER} variable.  When the code is executed, a different probe library (e.g. EMON probe) would be used 
        instead by choosing different ${LD_LIBRARY_PATH}.  The code to built should be able to handle this.
        
    II. CUSTOMIZATION of Code RUNNING
        This is done by modifying parameter_set_decoding(codelet, datasize, repetition, rundir) function 
        inside the topmost script.  Note that we expect $repetition is a mandatory argument to be passed to the code to 
        execute the kernel repeatedly.  As described above, $datasize and $repetition are written to 
        codelet.data by default expecting the program will read that file for these two paramters.  
        
        For program that requires command line argument, the argument should be returned by this function via the echo 
        at the end of this function.  For example, if the code expects command line arguments of the form 
            "-numnodes <M> -numedges <N> -input_file <filename> -rep <R>", 
        then the arguments should be done by doing
            echo "-numnodes $M -numedges $N -input_file $filename -rep $repetition" 
        where the variables $M, $N, and $filename are parsed from the input variable $datasize.  
        They could be encoded as <M>:<N>:<filename> which was stored in name2sizes[] map.
        
        Also, the user can use different methods to pass input arguments for different program by checking the $codelet variable.
        For example,
            if [[ $(basename $codelet) == 'foo' ]]; then
                ...
                echo "-np $NP -n $N -rep $repetition"
            elif [[ $(basename $codelet) == 'bar ]]; then
                ...
                echo "-matrixsize $N -rep $repetition"
            else
                echo ${repetition} ${datasize}" > ./codelet.data
                echo ""
            fi
        So codelet 'foo' will receive $NP, $N and $repetition as command line argument inputs; 
        'bar' will receive $N and $repetition as command line inputs; 
        and for other codelets, the $repetition and $datasize inputs will be stored in ./codelet.data file.

C. Running Multi-Compiler mode
		I. Define get_compilers() function
				In the script, define a get_compilers() function which returns a array of codenames for the compilers. Ex:
				get_compilers () {
					codelet_path="$1"
					# Checking codelet source language
					codelet_lang=$( grep "language value" "$( readlink -f "$codelet_path" )/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
					echo "Codelet Language: ${codelet_lang}" >&2
					if [ $codelet_lang == "Fortran" ] || [ $codelet_lang == "2" ]; then
						compilers="Intel GNU"
					elif [[ $codelet_lang == "CPP" ]]; then
						compilers="Intel GNU LLVM"
					elif [ $codelet_lang == "C" ] || [ $codelet_lang == "1" ]; then
						compilers="Intel GNU LLVM"
					else
						echo "Error: .conf file has invalid language value" >&2
						compilers="default"
					fi
					echo $compilers
				}
	II. Define a build_codelet() function
				Add compiler driver and compiler flag options based on the compiler codename. Also put compiler and its flags into compiler.csv file. Ex:
				build_codelet () {
					codelet_folder=$( readlink -f "$1" )
					codelet_name="$2"
					build_folder=$( readlink -f "$3" )
					curr_compiler="$4"
					declare -gA fortran_compiler
					declare -gA C_compiler
					declare -gA CPP_compiler
					declare -gA fortran_flags
					declare -gA C_flags
					declare -gA CPP_flags

					fortran_compiler[Intel]="ifort"
					fortran_compiler[GNU]="gfortran"

					C_compiler[Intel]="icc"
					C_compiler[GNU]="gcc"
					C_compiler[LLVM]="clang"

					CPP_compiler[Intel]="icpc"
					CPP_compiler[GNU]="g++"
					CPP_compiler[LLVM]="clang++"

					fortran_flags[Intel]="-g -O3 -align array64byte"
					fortran_flags[GNU]="-g -O3"

					C_flags[Intel]="-c -g -std=c99 -O3"
					C_flags[GNU]="-c -g -std=c99 -O3"
					C_flags[LLVM]="-c -g -std=c99 -O3"

					CPP_flags[Intel]="-c -g -std=c++11 -O3"
					CPP_flags[GNU]="-c -g -std=c++11 -O3"
					CPP_flags[LLVM]="-c -g -std=c++11 -O3"

					if [[ $codelet_name == *"sVS"* ]]; then
								 fortran_flags[Intel]+=" -no-vec"
								 fortran_flags[GNU]+=" -fno-tree-vectorize"
								 C_flags[Intel]+=" -no-vec"
								 C_flags[GNU]+=" -fno-tree-vectorize"
								 C_flags[LLVM]+=" -fno-vectorize -fno-slp-vectorize"
								 CPP_flags[Intel]+=" -no-vec"
								 CPP_flags[GNU]+=" -fno-tree-vectorize"
								 CPP_flags[LLVM]+=" -fno-vectorize -fno-slp-vectorize"
					elif [[ $codelet_name == *"se" ]]; then
								 fortran_flags[Intel]+=" -xSSE4.2"
								 fortran_flags[GNU]+=" -msse4.2"
								 C_flags[Intel]+=" -xSSE4.2"
								 C_flags[GNU]+=" -msse4.2"
								 C_flags[LLVM]+=" -msse4.2"
								 CPP_flags[Intel]+=" -xSSE4.2"
								 CPP_flags[GNU]+=" -msse4.2"
								 CPP_flags[LLVM]+=" -msse4.2"
					fi

					codelet_lang=$( grep "language value" "$( readlink -f "$codelet_folder" )/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
					if [ $codelet_lang == "Fortran" ] || [ $codelet_lang == "2" ]; then
						curr_compiler_driver=${fortran_compiler[${curr_compiler}]}
						for flag in ${fortran_flags[${curr_compiler}]}; do
							curr_compiler_flags+=${flag}
							curr_compiler_flags+=" "
						done
						make_vars=(CF=${curr_compiler_driver} FFLAGS="${curr_compiler_flags}")
					elif [[ $codelet_lang == "CPP" ]]; then
						curr_compiler_driver=${CPP_compiler[${curr_compiler}]}
						for flag in ${CPP_flags[${curr_compiler}]}; do
							curr_compiler_flags+=${flag}
							curr_compiler_flags+=" "
						done
						make_vars=(CXX=${curr_compiler_driver} CXXFLAGS="${curr_compiler_flags}")
					elif [ $codelet_lang == "C" ] || [ $codelet_lang == "1" ]; then
						curr_compiler_driver=${C_compiler[${curr_compiler}]}
						for flag in ${C_flags[${curr_compiler}]}; do
							curr_compiler_flags+=${flag}
							curr_compiler_flags+=" "
						done
						make_vars=(CC=${curr_compiler_driver} CFLAGS="${curr_compiler_flags}")
					else
						echo "Error: Cannot find compiler (${curr_compiler}) for the specified language (${codelet_lang})"
						exit -1
					fi
					echo MAKE CONFIG: ${make_vars}

					echo mkdir "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
					mkdir "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" &> /dev/null

					# Simple codelet compilation
					binary_name=$( grep "binary name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
					echo -e "Binary name \t'$binary_name'"
					# ensured it is at the same level as codelet_folder so that relative paths in Makefile is preserved it will be moved to the build_folder
					# after generating original
					build_tmp_folder=$(mktemp -d --tmpdir=${codelet_folder}/..)


					echo "Generating codelet '$codelet_folder/$codelet_name'..."

					echo "Compiler information using -v flags"
					${curr_compiler_driver} -v

					build_files=$(find ${codelet_folder} -maxdepth 1 -type f -o -type l)
					cp ${build_files} ${build_tmp_folder}

					cd ${build_tmp_folder}
					if [[ "$ENABLE_SEP" == "1" ]]; then
						echo make "${make_vars[@]}" clean ENABLE_SEP=sep ${emon_api_flags} all
						make "${make_vars[@]}" clean ENABLE_SEP=sep ${emon_api_flags} all
					else
						echo make "${make_vars[@]}" LIBPATH="${BASE_PROBE_FOLDER}" clean all
						make "${make_vars[@]}" LIBPATH="${BASE_PROBE_FOLDER}" clean all
					fi

					# &> /dev/null
					res=$?

					if [[ "$res" != "0" ]]; then
						echo "ERROR! Make did not succeed."
						exit -1
					fi

					mv "$binary_name" "$codelet_name"
					res=$?

					if [[ "$res" != "0" ]]; then
						echo "ERROR! Move did not succeed."
						exit -1
					fi

					if [[ -e "codelet.o" ]]; then
						cp "codelet.o" "$codelet_folder/$CLS_RES_FOLDER/"
					fi

					# Should be safe because $binary_name was already renamed to $codelet_name
					make clean &> /dev/null

					#add Compiler to compiler.csv
					echo -e "compiler,compiler_flags\n${curr_compiler_driver},${curr_compiler_flags}" > ${build_tmp_folder}/compiler.csv

					echo "Codelet generation was successful."
					mv ${build_tmp_folder} "${build_folder}"

					cp ${build_folder}/"$codelet_name" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
					res=$?
					if [[ "$res" != "0" ]]; then
						echo "ERROR! Copy of binary to binary folder failed"
						exit -1
					fi
				}
