Prompt: OpenMP profiler (using the 'OMPT' / 'OpenMP-tools' callbacks).

Tested with Intel icc.

To compile: make (the icc compiler will be invoked)

To run application:
export OMP_TOOL_LIBRARIES=(path to libprompt_icc.so)
export TARGET_PARALLEL_SECTION=ALL
export PROMPT_VERBOSE=X # optional: 1 (resp. 2) to display info up to par. (resp. sync.) regions
(run application as usual)

'par_regions.csv', 'par_regions_samples.csv', 'sync_regions.csv' and 'sync_regions_samples.csv' files are produced.

If bfd.h is not found, install the binutils-dev package.
If libiberty/demangle.h is not found, install the libiberty-dev package.

=====================================

Remark: PrOMPT metrics are directly derived from the OMPT callbacks defined in the OpenMP 5.1 standard (https://www.openmp.org/wp-content/uploads/OpenMP-API-Specification-5-1.pdf). Please search for omp/ompt names below (for instance "omp_get_level" or "ompt_callback_sync_region") to retrieve exact definition.
Warning: You are supposed to be already familiar to OpenMP concepts ("initial"/"worker"/"ancestor" threads, thread "teams", "fork-join" model etc.) to use PrOMPT.

Output is spread into the 'par_regions.csv' and 'sync_regions.csv' files. Each line of 'par_regions.csv' corresponds to a parallel region while each line of 'sync_regions.csv' corresponds to a "syncronization region" (in general, an implicit or explicit barrier) run by a given thread.

Unreduced timings are provided in 'par_regions_samples.csv' and 'sync_regions_samples.csv' for detailed measurement recording. By default, we will select instances whose numbers are consecutive powers of 2: 1, 2, 4, 8, 16 etc... Therefeore the first, second, fourth, 8th, 16th... instance of the same sync region will be fully recorded. However this choice can be changed by setting PROMPT_SAMPLING_PERIOD to an integer value K. Then every K instance, detailed recording will be carried out. For example, if K = 10, then instance 1, 11, 21, 31 and so on will generate detailed measurement recording.

For both files:
- module_name_offset: name of the executable or .so file + address (offset) in this file. More exactly return address of the outsourced function/region
- sync_time_sum: sum across all instances for the time spent to synchronize threads (implementation + waiting time)
- wait_time_sum: idem sync_time_sum but accounting only waiting time => to get implementation time: subtract wait_time to sync_time
- nb_instances: number of times the parallel/sync region was entered (and then exited)
- fct_name: function name (C++: demangled)
- src_file_line: source file and line

Specific to 'par_regions.csv':
- (one line per binary location and, may be removed, per ancestor thread for nested regions)
- the first data line is special: all fields are empty except for the first one, "ALL", and time_sum which is set to the total application walltime (as seen by PrOMPT, that is timestamp at the beginning of ompt_tool_fina() - timestamp at the end of ompt_tool_init())
- parent_reg_module_name_offset: module_name_offset for the parent parallel region (if any)
- level: nesting level (0 for top-level regions), returned by omp_get_level()
- ancestor_thread_num: rank of the ancestor thread, returned by omp_get_ancestor_thread_num (omp_get_level() - 1) [may be removed]
- invoker: "program" or "runtime" (CF ompt_parallel_invoker_(program/runtime))
- parallel_or_teams:
  - "parallel" = omp parallel construct (CF ompt_parallel_team)
  - "teams"    = omp teams    construct (CF ompt_parallel_league)
- requested_parallelism: (CF ompt_callback_parallel_begin_t/requested_parallelism) number of threads requested (typically via OMP_NUM_THREADS) by the user
- sync_time_sum: sum across all instances, all threads and all sync-regions for sync time (CF above)
- wait_time_sum: idem 'sync_time_sum' for wait time (CF above)
- parallelism_overhead: (100 * 'sync_time_sum') / ('time_sum' * 'requested_parallelism')
- time_{min/max/sum}: min/max/sum across all instances (and, if any, all ancestor threads) for elapsed time

Format of 'par_regions_samples.csv':
- module_name_offset, level, ancestor_thread_num: used to relate with the correct line in 'par_regions.csv' (CF above)
- instance_rank: rank of the instance
- time: time elapsed during the 'instance_rank' instance

Specific to 'sync_regions.csv':
- (one line per binary location, "kind" and concurrent thread, in other words key is 'par_reg_module_name_offset' + 'kind' + 'par_reg_thread_num' + 'thread_num')
- par_reg_module_name_offset: module_name_offset for the related parallel region
- par_reg_thread_num: rank of the ancestor thread (that created the parallel region)
- thread_num: thread rank
- kind: for instance implicit or explicit barrier. CF "Sync/wait breakdown" paragraph below
- sync_time_{sum/min/max}: sum/min/max across all instances for sync time (CF above)
- wait_time_{sum/min/max}: sum/min/max across all instances for wait time (CF above)
- Some lines are added, summing values (sync_time, wait_time and nb_instances) across all threads

Format of 'sync_regions_samples.csv':
- module_name_offset, ancestor_thread_num, thread_num, kind: used to relate with the correct line in 'sync_regions.csv' (CF above)
- instance_rank: rank of the instance
- sync_time: sync time (CF above) during the 'instance_rank' instance
- wait_time: wait time (CF above) during the 'instance_rank' instance

Remarks:
- In embedded parallel regions (level > 0), the number of effective/concurrent threads is greater than the daughter parallel region concurrency: has to be identified by concatenation of 'ancestor_thread_num' and 'thread_num'

Sync/wait breakdown (ompt_sync_region_t + ompt_state_t). Tells where the thread is waiting in:
- barrier (deprecated)
- barrier_implicit (deprecated)
- barrier_explicit: explicit 'barrier' region
- barrier_implementation: barrier "not required by the OpenMP standard but introduced by an OpenMP implementation"
- barrier_implicit_workshare: implicit barrier at the end of a worksharing construct
- barrier_implicit_parallel: implicit barrier at the end of a 'parallel' region
- barrier_teams: barrier at the end of a 'teams' region
- taskgroup: end of a 'taskgroup' construct (not yet tested)
- taskwait: 'taskwait' construct (not yet tested)
- reduction: not sure of how this is processed by recent OMP runtimes
