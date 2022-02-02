/*
   Copyright (C) 2004 - 2022 Université de Versailles Saint-Quentin-en-Yvelines (UVSQ)

   This file is part of MAQAO.

  MAQAO is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public License
   as published by the Free Software Foundation; either version 3
   of the License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */
#include <stdio.h>
#include <stdlib.h>    // qsort, strtol
#include <string.h>    // memset, memcpy, strtok
#include <assert.h>    // assert
#include <time.h>      // clock_gettime, struct timespec
#include <pthread.h>   // pthread_rwlock_{init/rdlock/wrlock/unlock/destroy}

#include <errno.h>
#include <sys/stat.h>    // mkdir (POSIX)
#include <sys/types.h>   // getpid (Linux)
#include <unistd.h>      // getpid (Linux), gethostname (Linux)

#include <omp.h>       // omp_get_thread_num, omp_get_ancestor_thread_num, omp_get_level
#include <omp-tools.h> // OMPT

#include "ompt_tool_addr2line.h" // ompt_tool_addr2line_(init/get/destroy)

// Number of values in ompt_work_t: CF omp-tools.h (which is regularly updated)
#define OMPT_WORK_ENUM_LENGTH 8 // ompt_work_scope

#define MAX_NEST 2 // supported values for omp_get_level() at parallel_begin/end are 0 and 1
#define MAX_NB_PARALLEL_INFO 5000 // max number of parallel regions per nest level
#define NB_SYNC_PER_REG_INIT 10 // max number of sync regions per parallel region
#define NB_WORK_PER_REG_INIT 10 // max number of work regions per parallel region
#define SAMPLES_LEN_INIT 4 // initial allocated size for stats.samples[]

/* MPC team code */
/* Thread data struct */
typedef struct thread_info_s {
   ompt_thread_t type;
   double start;
   double end;
} thread_info_t;
/* MPC team code end */

/*Parallel data struct */
typedef struct {
   double start;
   double sum;
   double min;
   double max;
   unsigned nb_instances;
   unsigned short nb_samples;  // effective number of elements in samples[]
   unsigned short samples_len; // allocated size for samples[]
   double *samples;
} stats_t;

/* Synchronization region (typically implicit/explicit barriers)
 * CF ompt_sync_region_t */
typedef struct {
   const void *codeptr_ra;
   ompt_sync_region_t kind;
   stats_t sync_stats; // sync
   stats_t wait_stats; // sync_wait
} sync_region_t;

/* Set of synchronization regions (impl. as a C++ Vector) */
typedef struct {
   unsigned nb_sync_regions;
   unsigned sync_region_len; // allocated size for sync_region
   sync_region_t *sync_region;
} sync_regions_t;

/* Worksharing region (loop, single, taskloop etc.)
 * CF ompt_work_t */
typedef struct {
   const void *codeptr_ra;
   ompt_work_t kind;
   stats_t work_stats;
} work_region_t;

/* Set of worksharing regions (impl. as a C++ Vector/ */
typedef struct {
   unsigned nb_work_regions;
   unsigned work_region_len;
   work_region_t *work_region;
} work_regions_t;

/* Performance data and sync regions coming from an ancestor thread (single one from sequential code) */
typedef struct {
   unsigned requested_parallelism; // nb of "lines" in sync_stats & wait_stats, 0 = not used
   stats_t stats;
#ifdef PROMPT_SYNC
   sync_regions_t *sync_regions; // sync and sync wait [thread_num]
#endif
#ifdef PROMPT_WORK
   work_regions_t *work_regions; // worksharing regions [thread_num]
#endif
} thread_parallel_info_t;

/* Data related to a "static" parallel region (code location)
 * If a region is nested in another region, data are not duplicated but saved in per_thread */
typedef struct parallel_info {
   pthread_rwlock_t rwlock; // serialize concurrent accesses to next fields
    /* Used only at parallel-begin to force a parinfo being fully initiliazed
     * before it can be reused by another thread */
   // parallel_{begin,end} arguments
   const void *codeptr_ra;
   int flags;

   int level; // omp_get_level()
   struct parallel_info *parent; // reference to info for parent region (NULL if level = 0)

   unsigned nb_ancestor_threads; // number of elements in per_thread[]
   thread_parallel_info_t *per_thread; // data for each ancestor thread
} parallel_info_t;

/* Set of parallel regions at a given level (omp_get_level()) */
typedef struct {
   pthread_rwlock_t rwlock; // serialize concurrent accesses to next fields
   // CAN BE CONCURRENTLY ACCESSED VIA MULTIPLE THREADS IN NESTED PARALLEL REGIONS
   unsigned nb_parallel_info; // number of elements set in parallel_info_array[]
   parallel_info_t parallel_info_array [MAX_NB_PARALLEL_INFO];

   // Inserting before the end of an array of pointer is much faster than in an array of structs
   parallel_info_t *dic [MAX_NB_PARALLEL_INFO];
   parallel_info_t *last_parinfo; // parallel_data->ptr for last parallel-begin
   // END OF VARS TO PROTECT
} parallel_regions_t;

/* Global variables */
parallel_regions_t parallel_regions [MAX_NEST];
struct timespec start_time_ts; // subtract this to subsequent omp_get_time values improves precision of times saved in double variables

/* getenv ("PROMPT_PARALLEL_REGIONS") = "0x123,0x456" implies:
 *  - par_reg_filt = { 0x123, 0x456 }
 *  - par_reg_filt_len = 2 */
void    **par_reg_filt;
unsigned  par_reg_filt_len;

unsigned verbose_level; // atoi (getenv ("PROMPT_VERBOSE"))

unsigned sampling_period; // atoi (getenv ("PROMPT_SAMPLING_PERIOD"))

const char *output_path; // getenv ("PROMPT_OUTPUT_PATH"), "prompt_results" or "prompt_results/<hostname>/<pid>"

#ifdef PROMPT_TASK
// Unique ID for created tasks (assigned by ompt_callback_task_create)
unsigned long task_UID;
pthread_mutex_t task_UID_mutex;
#endif

// Compares two parallel_info from codeptr_ra value, used for bsearch
static int comp_parinfo (const void *key, const void *dat)
{
   const parallel_info_t *key_pi = *((const parallel_info_t **) key);
   const parallel_info_t *dat_pi = *((const parallel_info_t **) dat);
   assert (key_pi != NULL && dat_pi != NULL);

   const void *key_codeptr = key_pi->codeptr_ra;
   const void *dat_codeptr = dat_pi->codeptr_ra;

   if (key_codeptr < dat_codeptr) return -1;
   if (key_codeptr > dat_codeptr) return 1;

   return 0;
}

/* Lookup by codeptr_ra a parallel region at a given level
 * Binary search (log N) should be sufficient for most applications */
static parallel_info_t *lookup_parallel_info (const void *codeptr_ra, int level)
{
   assert (level < MAX_NEST);

   parallel_info_t key_data;
   parallel_info_t *key = &key_data;
   key->codeptr_ra = codeptr_ra;
   key->level = level;

   const parallel_regions_t *pr = &(parallel_regions [level]);

#ifndef NDEBUG
   // Check that pr->dic is already sorted
   parallel_info_t *dic_sorted [MAX_NB_PARALLEL_INFO];
   memcpy (dic_sorted, pr->dic, sizeof pr->dic);
   qsort (dic_sorted, pr->nb_parallel_info, sizeof dic_sorted[0], comp_parinfo);
   unsigned i;
   for (i=0; i < pr->nb_parallel_info; i++)
      assert (dic_sorted[i] == pr->dic[i]);
#endif

   parallel_info_t **found = bsearch (&key, pr->dic, pr->nb_parallel_info,
                                      sizeof pr->dic[0], comp_parinfo);

#ifndef NDEBUG
   if (found == NULL) {
      unsigned i;
      for (i=0; i < pr->nb_parallel_info; i++) {
         assert (pr->parallel_info_array[i].codeptr_ra != codeptr_ra ||
                 pr->parallel_info_array[i].level != level);
      }
      for (i=0; i < pr->nb_parallel_info; i++) {
         assert (pr->dic[i]->codeptr_ra != codeptr_ra ||
                 pr->dic[i]->level != level);
      }
   }
#endif

   return found ? (parallel_info_t *) *found : NULL;
}

/* Insert info for a new parallel region, at a given level */
static parallel_info_t *insert_parallel_info (const void *codeptr_ra, int level)
{
   // This function must be called only for a new couple (codeptr_ra, level)
   assert (lookup_parallel_info (codeptr_ra, level) == NULL);

   parallel_regions_t *pr = &(parallel_regions [level]);

   if (pr->nb_parallel_info == MAX_NB_PARALLEL_INFO) {
      printf ("[PROMPT] Warning: cannot insert more than %d regions per nest-level\n", MAX_NB_PARALLEL_INFO);
      return NULL;
   }

   parallel_info_t *parinfo = pr->parallel_info_array + pr->nb_parallel_info;

   // Lookup for insertion position: pr->dic must always be sorted (bsearch on it)
   unsigned i;
   for (i = 0; i < pr->nb_parallel_info; i++) {
      if (pr->dic[i]->codeptr_ra > codeptr_ra)
         break;
   }

   // Make room for new element (move all elements after insertion position)
   memmove (&(pr->dic[i+1]), &(pr->dic[i]), (pr->nb_parallel_info - i) * sizeof pr->dic[0]);
   pr->dic[i] = parinfo;
#ifndef NDEBUG
   memset (parinfo, 0, sizeof *parinfo);
#endif
   pthread_rwlock_init (&(parinfo->rwlock), NULL);
   parinfo->codeptr_ra = codeptr_ra;
   parinfo->level = level;

   (pr->nb_parallel_info)++;

   return parinfo;
}

static inline void _timespec_sub (const struct timespec *a, const struct timespec *b,
                                  struct timespec *res)
{
   res->tv_sec  = a->tv_sec  - b->tv_sec;
   res->tv_nsec = a->tv_nsec - b->tv_nsec;
   if (res->tv_nsec < 0) {
      res->tv_sec = res->tv_sec - 1;
      res->tv_nsec += 1000 * 1000 * 1000;
   }
}

// TODO: think about using ts instead of double (integer computations)
static inline double __ompt_get_time()
{
   struct timespec ts;

   if (clock_gettime (CLOCK_REALTIME, &ts) != 0) perror ("clock_gettime");

   _timespec_sub (&ts, &start_time_ts, &ts); // makes ts.ts_sec very small

   return ts.tv_sec + ts.tv_nsec * 0.000000001; // precision should be good thanks to small ts.ts_sec
}

/* Callbacks */

/* MPC team code */

/* thread_begin: Callback invoked at the begining of a
 * native thread.
 * [In]  thread_type: Type of native thread
 * [In]  thread_data: Ompt memory record of thread data
 */
void thread_begin (ompt_thread_t type, ompt_data_t *thread_data)
{
   assert( thread_data );

   thread_info_t *thread_infos = malloc (sizeof *thread_infos);

   assert( thread_infos );

   memset( thread_infos, 0, sizeof *thread_infos);

   thread_infos->type = type;
   thread_infos->start = __ompt_get_time();

   /* Save tool data in thread ompt record (ompt_data_t) */
   thread_data->ptr = (void*) thread_infos;

   if (verbose_level >= 1) {
      switch (type) {
      case ompt_thread_initial:
         printf ("[PROMPT] Initial thread starts, rank = %d\n", omp_get_thread_num());
         break;

      case ompt_thread_worker:
         printf ("[PROMPT] Worker thread starts, rank = %d\n", omp_get_thread_num());
         break;

      default:
         {}
      }
   }
}

/* thread_end: Callback invoked at the ending of a native
 * thread.
 * [In]  thread_data: Ompt memory record of thread data
 */
void thread_end (ompt_data_t *thread_data)
{

   thread_info_t* thread_infos = (thread_info_t*) thread_data->ptr;

   thread_infos->end = __ompt_get_time();

   if (verbose_level >= 1) {
      switch (thread_infos->type) {
      case ompt_thread_initial:
         printf ("[PROMPT] Initial thread ends, total time spent = %f, rank = %d\n", thread_infos->end - thread_infos->start, omp_get_thread_num());
         break;

      case ompt_thread_worker:
         printf ("[PROMPT] Worker thread ends, total time spent = %f, rank = %d\n", thread_infos->end - thread_infos->start, omp_get_thread_num());
         break;

      default:
         {}
      }
   }

   free (thread_infos);

   thread_data->ptr = NULL;
}
/*MPC team code end */

static inline int is_target_codeptr (const void *codeptr_ra)
{
   if (par_reg_filt_len == 0) return 1;

   if (codeptr_ra != NULL) {
      unsigned i;
      for (i=0; i<par_reg_filt_len; i++) {
         if (par_reg_filt[i] == codeptr_ra) {
            return 1;
         }
      }
   }

   return 0;
}

static inline void update_stats_begin (stats_t *stats, double start_time)
{
   // Ensure that events are paired (begin and then end)
   assert (stats->start == 0.0); // stats->start is set to 0 by update_stats_end

   stats->start = start_time;
}

static inline int is_pow2 (unsigned x)
{
   assert (x > 0);
   return (x & (x - 1)) == 0;
}

static inline void update_stats_end (stats_t *stats, double end_time)
{
   // Ensure that events are paired (begin and then end)
   assert (stats->start > 0.0); // stats->start is set to 0 by self

   assert (end_time >= stats->start);
   const double duration = end_time - stats->start;
   stats->start = 0.0; // allows to check update_stats_begin() was called first
   stats->sum += duration;

   if (stats->nb_instances == 0) {
      stats->min = duration;
      stats->max = duration;
   }
   else {
      if (duration < stats->min) stats->min = duration;
      if (duration > stats->max) stats->max = duration;
   }

   stats->nb_instances += 1;

   // Save instance duration in samples[]
   if ((sampling_period == 0 && is_pow2 (stats->nb_instances)) || // power of 2
       (sampling_period >  0 && (stats->nb_instances % sampling_period) == 1)) { // for period=10, records 1, 11, 21, etc.
      assert (stats->samples != NULL);

      // If samples[] is full, double its capacity
      if (stats->nb_samples == stats->samples_len) {
         stats->samples = realloc (stats->samples, 2 * stats->samples_len * sizeof stats->samples[0]);
#ifndef NDEBUG
         memset (stats->samples + stats->samples_len, 0, stats->samples_len * sizeof stats->samples[0]);
#endif
         stats->samples_len = 2 * stats->samples_len;
      }

      stats->samples [stats->nb_samples++] = duration;
   }
}

#ifdef PROMPT_SYNC
// Allocate sync regions
static void allocate_sync_regions (thread_parallel_info_t *tpi) {
   const size_t sync_regions_size = tpi->requested_parallelism * sizeof tpi->sync_regions[0];
   tpi->sync_regions = malloc (sync_regions_size);
   unsigned thread_rank;
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      sync_regions_t *sync_regions = &(tpi->sync_regions [thread_rank]);
      sync_regions->nb_sync_regions = 0;
      sync_regions->sync_region_len = NB_SYNC_PER_REG_INIT;
      const size_t sync_region_size = NB_SYNC_PER_REG_INIT * sizeof sync_regions->sync_region[0];
      sync_regions->sync_region = malloc (sync_region_size);
      memset (sync_regions->sync_region, 0, sync_region_size);
   }
}

// Reallocate sync regions to support more threads (increased requested_parallelism)
static void reallocate_sync_regions (thread_parallel_info_t *tpi, unsigned new_requested_parallelism) {
   const size_t sync_region_new_size = new_requested_parallelism * sizeof tpi->sync_regions[0];
   tpi->sync_regions = realloc (tpi->sync_regions, sync_region_new_size);
   unsigned thread_rank;
   for (thread_rank = tpi->requested_parallelism; thread_rank < new_requested_parallelism; thread_rank++) {
      sync_regions_t *sync_regions = &(tpi->sync_regions [thread_rank]);
      sync_regions->nb_sync_regions = 0;
      sync_regions->sync_region_len = NB_SYNC_PER_REG_INIT;
      const size_t sync_region_size = NB_SYNC_PER_REG_INIT * sizeof sync_regions->sync_region[0];
      sync_regions->sync_region = malloc (sync_region_size);
      memset (sync_regions->sync_region, 0, sync_region_size);
   }
}
#endif

#ifdef PROMPT_WORK
// Allocate work regions
static void allocate_work_regions (thread_parallel_info_t *tpi) {
   const size_t work_regions_size = tpi->requested_parallelism * sizeof tpi->work_regions[0];
   tpi->work_regions = malloc (work_regions_size);
   unsigned thread_rank;
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      work_regions_t *work_regions = &(tpi->work_regions [thread_rank]);
      work_regions->nb_work_regions = 0;
      work_regions->work_region_len = NB_WORK_PER_REG_INIT;
      const size_t work_region_size = NB_WORK_PER_REG_INIT * sizeof work_regions->work_region[0];
      work_regions->work_region = malloc (work_region_size);
      memset (work_regions->work_region, 0, work_region_size);
   }
}

// Reallocate work regions to support more threads (increased requested_parallelism)
static void reallocate_work_regions (thread_parallel_info_t *tpi, unsigned new_requested_parallelism) {
   const size_t work_region_new_size = new_requested_parallelism * sizeof tpi->work_regions[0];
   tpi->work_regions = realloc (tpi->work_regions, work_region_new_size);
   unsigned thread_rank;
   for (thread_rank = tpi->requested_parallelism; thread_rank < new_requested_parallelism; thread_rank++) {
      work_regions_t *work_regions = &(tpi->work_regions [thread_rank]);
      work_regions->nb_work_regions = 0;
      work_regions->work_region_len = NB_WORK_PER_REG_INIT;
      const size_t work_region_size = NB_WORK_PER_REG_INIT * sizeof work_regions->work_region[0];
      work_regions->work_region = malloc (work_region_size);
      memset (work_regions->work_region, 0, work_region_size);
   }
}
#endif

static void init_stats (stats_t *stats)
{
   memset (stats, 0, sizeof *stats);
   stats->samples_len = SAMPLES_LEN_INIT;
   stats->samples = malloc (stats->samples_len * sizeof stats->samples[0]);
#ifndef NDEBUG
   memset (stats->samples, 0, stats->samples_len * sizeof stats->samples[0]);
#endif
}

static void init_tpi (thread_parallel_info_t *tpi, unsigned requested_parallelism)
{
   tpi->requested_parallelism = requested_parallelism;
   init_stats (&(tpi->stats));
#ifdef PROMPT_SYNC
   allocate_sync_regions (tpi);
#endif
#ifdef PROMPT_WORK
   allocate_work_regions (tpi);
#endif
}

/* Triggered by ompt_callback_parallel_begin()
 * [In]  encountering_task_data: Encountering task
 * [In]  encountering_task_frame: Frame object that is associated with the encountering task
 * [In]  parallel_data: Ompt memory record of parallel data
 * [In]  requested_parallelism: Indicates the number of threads or teams that the user requested
 * [In]  flags: indicates whether the code for the region is inlined into the app or invoked by the runtime
 and whether the region is a parallel or teams regions.
 * [In] codeptr_ra: relates the implementation of OpenMP region to its source code.
 */
void parallel_begin (ompt_data_t *encountering_task_data,
                     const ompt_frame_t *encountering_task_frame,
                     ompt_data_t *parallel_data, unsigned int requested_parallelism,
                     int flags, const void *codeptr_ra)
{
   assert (parallel_data != NULL);

   // Check if filtered out
   if (is_target_codeptr (codeptr_ra) == 0) {
      parallel_data->ptr = NULL;
      return;
   }

   // Get thread rank and level
   const int thread_num = omp_get_thread_num();
   const int level = omp_get_level();

   /* According to the spec, "If attribution to source code is impossible or inappropriate,
    * codeptr_ra may be NULL" => not interested yet with such regions */
   if (codeptr_ra == NULL) {
      printf ("[PROMPT] Warning: entering a parallel region that cannot be related to source code => ignored\n");
      parallel_data->ptr = NULL;

      return;
   }

   // Check that flags are consistent: program XOR runtime, league XOR team
   assert ((flags & ompt_parallel_invoker_program) != (flags & ompt_parallel_invoker_runtime));
   assert ((flags & ompt_parallel_league         ) != (flags & ompt_parallel_team           ));

   // Display parallel_begin parameters
   if (verbose_level >= 1)
      fprintf (stderr, "[PROMPT] {thread #%d at level %d, %f, parallel_begin} (%s, invoked by %s, ra=%p)\n",
               thread_num, level, __ompt_get_time(),
               flags & ompt_parallel_team ? "team" : "league",
               flags & ompt_parallel_invoker_program ? "program" : "runtime",
               codeptr_ra);

   // OMP level is limited to MAX_NEST
   if (level >= MAX_NEST) {
      printf ("[PROMPT] Warning: omp_get_level() returned %d while entering a parallel region: "
              "not yet supported (expects max-active-levels <= %d)\n", level, MAX_NEST);
      parallel_data->ptr = NULL;

      return;
   }

   thread_parallel_info_t *tpi = NULL;
   parallel_regions_t *pr = &(parallel_regions [level]);

   pthread_rwlock_wrlock (&(pr->rwlock)); // serialize parallel info lookup/insertion
   parallel_info_t *parinfo = lookup_parallel_info (codeptr_ra, level);
   if (parinfo == NULL) {
      // First time we see codeptr_ra at the given level

      parinfo = insert_parallel_info (codeptr_ra, level);
      pr->last_parinfo = parinfo;

      // parinfo->{codeptr_ra, level} set by insert_parallel_info => set other fields
      pthread_rwlock_wrlock (&(parinfo->rwlock)); // do not run this after the next line

      pthread_rwlock_unlock (&(pr->rwlock));

      //   Set flags
      parinfo->flags = flags;

      //   Set parent and nb_ancestor_threads
      if (level == 0) { // top-level regions, created by the initial thread (rank = 0)
         parinfo->parent = NULL;
         parinfo->nb_ancestor_threads = 1;
      } else { // nested regions, created by the ancestor thread of the parent region
         parallel_regions_t *parent_pr = &(parallel_regions [level-1]);
         pthread_rwlock_rdlock (&(parent_pr->rwlock));
         parinfo->parent = parent_pr->last_parinfo;
         pthread_rwlock_unlock (&(parent_pr->rwlock));
         assert (parinfo->parent != NULL);
         const thread_parallel_info_t *parent_tpi =
            &(parinfo->parent->per_thread [omp_get_ancestor_thread_num (level-1)]);
         parinfo->nb_ancestor_threads = parent_tpi->requested_parallelism;
      }

      //   Allocate per_thread []
      const size_t per_thread_size = parinfo->nb_ancestor_threads * sizeof parinfo->per_thread[0];
      parinfo->per_thread = malloc (per_thread_size);
      memset (parinfo->per_thread, 0, per_thread_size);

      pthread_rwlock_unlock (&(parinfo->rwlock));

      //   Set per_thread [thread_num] (1 thread_num per parallel_begin() call)
      assert (thread_num < parinfo->nb_ancestor_threads);
      tpi = &(parinfo->per_thread [thread_num]);
      init_tpi (tpi, requested_parallelism);
   }
   else {
      // Already visited (codeptr_ra, level)
      pr->last_parinfo = parinfo;
      pthread_rwlock_unlock (&(pr->rwlock));

      pthread_rwlock_rdlock (&(parinfo->rwlock));

      // Check consistency of info found for the parallel region
      //   codeptr_ra, level, flags
      assert (parinfo->codeptr_ra == codeptr_ra);
      assert (parinfo->level == level);
      assert ((parinfo->flags & ompt_parallel_team  ) == (flags & ompt_parallel_team  ));
      assert ((parinfo->flags & ompt_parallel_league) == (flags & ompt_parallel_league));

      //   level, parent and nb_ancestor_threads
      if (parinfo->parent != NULL) {
         assert (level > 0);
         const thread_parallel_info_t *parent_tpi =
            &(parinfo->parent->per_thread [omp_get_ancestor_thread_num (level-1)]);
         assert (parent_tpi->requested_parallelism <= parinfo->nb_ancestor_threads);
      } else { // parinfo->parent == NULL
         assert (level == 0);
         assert (parinfo->nb_ancestor_threads == 1);
      }

      // Set per_thread [thread_num] (1 thread_num per parallel_begin() call)
      assert (parinfo->per_thread != NULL && thread_num < parinfo->nb_ancestor_threads);
      tpi = &(parinfo->per_thread [thread_num]);

      pthread_rwlock_unlock (&(parinfo->rwlock));

      if (tpi->requested_parallelism == 0) {
         // First visit for a given ancestor thread
         init_tpi (tpi, requested_parallelism);
      } else if (tpi->requested_parallelism < requested_parallelism) {
         // Already visited ancestor thread but parent concurrency has increased
#ifdef PROMPT_SYNC
         reallocate_sync_regions (tpi, requested_parallelism);
#endif
#ifdef PROMPT_WORK
         reallocate_work_regions (tpi, requested_parallelism);
#endif
         tpi->requested_parallelism = requested_parallelism;
      }
   }

   const double begin_time = __ompt_get_time(); // get as late as possible (to exclude tool)
   update_stats_begin (&(tpi->stats), begin_time);

   /* Save tool data in thread ompt record (ompt_data_t) */
   parallel_data->ptr = parinfo;
}

// Triggered by ompt_callback_parallel_end()
void parallel_end (ompt_data_t *parallel_data,
                   ompt_data_t *encountering_task_data,
                   int flags, const void *codeptr_ra)
{
   const double dispatch_time = __ompt_get_time(); // get as soon as possible (to exclude tool)

   assert (parallel_data != NULL);

   // Retrieve info from parallel_data
   parallel_info_t *parinfo = parallel_data->ptr;
   if (parinfo == NULL) return; // case for filtered-out regions

   // Checking that codeptr_ra is not filtered out
   assert (is_target_codeptr (parinfo->codeptr_ra) != 0);

   // Get thread rank and level
   const int level = parinfo->level;
   /* Remark: when compiling with Intel compilers, omp_get_level() returns 2 instead of 1
    * for the inner parallel region (with 2 levels nesting) with OMP_MAX_ACTIVE_LEVELS=1 */
   if (verbose_level >= 1 && omp_get_level() != level) {
      printf ("Warning: level=%d at parallel_begin vs %d at parallel_end."
              "Check OMP_MAX_ACTIVE_LEVELS\n", parinfo->level, omp_get_level());
   }
   const int thread_num = omp_get_ancestor_thread_num (level);

   // Check that flags are consistent: program XOR runtime, league XOR team
   assert ((flags & ompt_parallel_invoker_program) != (flags & ompt_parallel_invoker_runtime));
   assert ((flags & ompt_parallel_league         ) != (flags & ompt_parallel_team           ));

   // Display parallel_end parameters
   if (verbose_level >= 1)
      fprintf (stderr, "[PROMPT] {thread #%d at level %d, %f, parallel_end} (%s, invoked by %s, ra=%p)\n",
               omp_get_thread_num(), omp_get_level(), dispatch_time,
               flags & ompt_parallel_team ? "team" : "league",
               flags & ompt_parallel_invoker_program ? "program" : "runtime",
               codeptr_ra);

   // Check consistency of info found for the parallel region: codeptr_ra, level, flags
   assert (codeptr_ra == NULL || parinfo->codeptr_ra == codeptr_ra);
   assert ((parinfo->flags & ompt_parallel_team  ) == (flags & ompt_parallel_team  ));
   assert ((parinfo->flags & ompt_parallel_league) == (flags & ompt_parallel_league));

   // Get per_thread [thread_num]
   assert (parinfo->per_thread != NULL && thread_num < parinfo->nb_ancestor_threads);
   thread_parallel_info_t *tpi = &(parinfo->per_thread [thread_num]);

   // Update stats for the region itself (only from the current ancestor thread)
   update_stats_end (&(tpi->stats), dispatch_time);

#if defined(PROMPT_SYNC) || (defined(PROMPT_WORK) && !defined(NDEBUG))
   unsigned thread_rank;
#endif

   /* Ends last instance for ignored sync-end events, CF sync_region_common (parallel_data=NULL).
    * Corresponds to implicit barrier at the end of the parallel region */
#ifdef PROMPT_SYNC
   unsigned sync_reg_rank;
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      sync_regions_t *sync_regions = &(tpi->sync_regions [thread_rank]);

      for (sync_reg_rank = 0; sync_reg_rank < sync_regions->nb_sync_regions; sync_reg_rank++) {
         sync_region_t *sync_region = &(sync_regions->sync_region [sync_reg_rank]);

         stats_t *sync_stats = &(sync_region->sync_stats);
         stats_t *wait_stats = &(sync_region->wait_stats);

         if (sync_stats->start > 0.0 || wait_stats->start > 0.0) {
#if(OMPT_SYNC_REGION_ENUM_LENGTH >= 9)
            assert (sync_region->kind == ompt_sync_region_barrier_implicit_parallel ||
                    sync_region->kind == ompt_sync_region_barrier_implicit);
#else
            assert (sync_region->kind == ompt_sync_region_barrier_implicit);
#endif

            if (sync_stats->start > 0.0) update_stats_end (sync_stats, dispatch_time);
            if (wait_stats->start > 0.0) update_stats_end (wait_stats, dispatch_time);
         }
      } // for each sync region
   } // for each thread rank
#endif // PROMPT_SYNC

   // Update stats in worksharing regions (only from the current ancestor thread)
#if defined(PROMPT_WORK) && !defined(NDEBUG)
   unsigned work_reg_rank;
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      work_regions_t *work_regions = &(tpi->work_regions [thread_rank]);

      for (work_reg_rank = 0; work_reg_rank < work_regions->nb_work_regions; work_reg_rank++) {
         work_region_t *work_region = &(work_regions->work_region [work_reg_rank]);
         stats_t *work_stats = &(work_region->work_stats);

         /* All work events should be paired (or never started) */
         assert (work_stats->start == 0.0);
      } // for each sync region
   } // for each thread rank
#endif // PROMPT_WORK && !NDEBUG

   parallel_data->ptr = NULL;
}

#ifdef PROMPT_SYNC
// Triggered by ompt_callback_{sync_region,sync_region_wait,reduction}()
static void sync_region_common (ompt_sync_region_t kind, ompt_scope_endpoint_t endpoint,
                                ompt_data_t *parallel_data, ompt_data_t *task_data,
                                const void *codeptr_ra, int wait)
{
   // Check kind value
   assert (kind >= 1 && kind <= OMPT_SYNC_REGION_ENUM_LENGTH);

   // ompt_scope_beginend not yet handled
   assert (endpoint == ompt_scope_begin || endpoint == ompt_scope_end);

   const double dispatch_time = __ompt_get_time(); // for endpoint=end, get as soon as possible (to exclude tool)

   /* According to the standard: "For the barrier-end event at the end of a parallel region
    * this argument [parallel_data] is NULL" */
   if (parallel_data == NULL) {
      assert (endpoint == ompt_scope_end);
#if(OMPT_SYNC_REGION_ENUM_LENGTH >= 9)
      assert (kind == ompt_sync_region_barrier_implicit_parallel ||
              kind == ompt_sync_region_barrier_implicit);
#else
      assert (kind == ompt_sync_region_barrier_implicit);
#endif

      if (verbose_level >= 2) {
         // omp_get_level() segfaults when parallel_data=NULL
         fprintf (stderr, "[PROMPT] {thread #%d at level ?, %f, sync_region%s} %s"
                  "(parallel_data=NULL, codeptr_ra=%p) => ignored\n",
                  omp_get_thread_num(), dispatch_time,
                  wait == 1 ? "_wait" : "",
                  endpoint == ompt_scope_begin ? "begin" : "end",
                  codeptr_ra);
      }

      return;
   }

   // Get thread rank and level
   const int thread_num = omp_get_thread_num();
   const int level = omp_get_level();

   if (verbose_level >= 2) {
      const parallel_info_t *const parinfo = parallel_data->ptr;
      fprintf (stderr, "[PROMPT] {thread #%d at level %d, %f, sync_region%s} %s (%p,%p)\n",
               thread_num, level, dispatch_time,
               wait == 1 ? "_wait" : "",
               endpoint == ompt_scope_begin ? "begin" : "end",
               parinfo ? parinfo->codeptr_ra : NULL,
               codeptr_ra);
   }

   // Get info for the related parallel region
   parallel_info_t *parinfo = parallel_data->ptr;
   if (parinfo == NULL) {
      if (par_reg_filt_len == 0)
         printf ("Warning: ignoring a sync-event from a never encountered parallel region. "
                 "That typically corresponds to a \"omp for\" outside any parallel region.\n");
      return;
   }
   if (codeptr_ra == NULL) codeptr_ra = parinfo->codeptr_ra;

   // Excluding sync regions from filtered-out parallel regions
   if (is_target_codeptr (parinfo->codeptr_ra) == 0) return;

   // Get related stats (from the current ancestor thread)
   const int ancestor_thread_num = omp_get_ancestor_thread_num (level-1);
   assert (parinfo->per_thread != NULL && ancestor_thread_num < parinfo->nb_ancestor_threads);
   thread_parallel_info_t *tpi = &(parinfo->per_thread [ancestor_thread_num]);

   sync_region_t *sync_region = NULL;

   // Look for already existing sync region (same kind and codeptr_ra)
   assert (tpi->sync_regions != NULL && thread_num < tpi->requested_parallelism);
   sync_regions_t *const sync_regions = &(tpi->sync_regions [thread_num]);
   unsigned sync_reg_rank;
   for (sync_reg_rank = 0; sync_reg_rank < sync_regions->nb_sync_regions; sync_reg_rank++) {
      sync_region_t *sr = &(sync_regions->sync_region [sync_reg_rank]);
      if (sr->codeptr_ra == codeptr_ra && sr->kind == kind) {
         sync_region = sr;
         break;
      }
   }

   // If new syncronization region, create it
   if (endpoint == ompt_scope_begin && sync_region == NULL) {
      // If sync_regions is full, enlarge it
      if (sync_regions->nb_sync_regions == sync_regions->sync_region_len) {
         const size_t sync_region_size = sync_regions->sync_region_len *
            sizeof sync_regions->sync_region[0];
         sync_regions->sync_region = realloc (sync_regions->sync_region, sync_region_size * 2);
         memset (sync_regions->sync_region + sync_regions->sync_region_len, 0, sync_region_size);
         sync_regions->sync_region_len *= 2;
      }

      sync_region = &(sync_regions->sync_region [sync_regions->nb_sync_regions]);
      sync_regions->nb_sync_regions++;

      // Set all fields: codeptr_ra, kind, sync_stats and wait_stats
      sync_region->codeptr_ra = codeptr_ra;
      sync_region->kind = kind;
      init_stats (&(sync_region->sync_stats));
      init_stats (&(sync_region->wait_stats));
   }

   stats_t *const stats = (wait != 0)
      ? &(sync_region->wait_stats)
      : &(sync_region->sync_stats);

   switch (endpoint) {
   case ompt_scope_begin:
   {
      const double begin_time = __ompt_get_time(); // get as late as possible (to exclude tool)
      update_stats_begin (stats, begin_time);
   }
   break;

   case ompt_scope_end:
      update_stats_end (stats, dispatch_time);
      break;
   }
}

/* _sync_region : Callback used for callbacks that are dispatched when barrier regions,
 * taskwait regions and taskgroup region begin and end and when waiting begins and ends for them.
 * [In]  kind : Indicates the kind of synchronization.
 * [In]  endpoint : indicates that the callback signals the beginning of a scope or the end of a scope.
 * [In]  parallel_data
 * [In]  task_data
 * [In] codeptr_ra: relates the implementation of OpenMP region to its source code.
 */
void sync_region (ompt_sync_region_t kind, ompt_scope_endpoint_t endpoint,
                  ompt_data_t *parallel_data, ompt_data_t *task_data,
                  const void *codeptr_ra)
{
   sync_region_common (kind, endpoint, parallel_data, task_data, codeptr_ra, 0);
}

// CF sync_region
void sync_region_wait (ompt_sync_region_t kind, ompt_scope_endpoint_t endpoint,
                       ompt_data_t *parallel_data, ompt_data_t *task_data,
                       const void *codeptr_ra)
{
   sync_region_common (kind, endpoint, parallel_data, task_data, codeptr_ra, 1);
}
#endif // PROMPT_SYNC

#ifdef PROMPT_WORK
// very similar to sync_common: try to factor code
void work (ompt_work_t wstype, ompt_scope_endpoint_t endpoint,
           ompt_data_t *parallel_data, ompt_data_t *task_data,
           uint64_t count, const void *codeptr_ra)
{
   // Check wstype value
   assert (wstype >= 1 && wstype <= OMPT_WORK_ENUM_LENGTH);

   // ompt_scope_beginend not yet handled
   assert (endpoint == ompt_scope_begin || endpoint == ompt_scope_end);

   const double dispatch_time = __ompt_get_time(); // for endpoint=end, get as soon as possible (to exclude tool)

   // Contrary to ompt_callback_sync_region, parallel_data should never be NULL
   assert (parallel_data != NULL);

   // Get thread rank and level
   const int thread_num = omp_get_thread_num();
   const int level = omp_get_level();

   if (verbose_level >= 2) {
      const parallel_info_t *const parinfo = parallel_data->ptr;
      fprintf (stderr, "[PROMPT] {thread #%d at level %d, %f, worksharing} %s (%p,%p)\n",
               thread_num, level, dispatch_time,
               endpoint == ompt_scope_begin ? "begin" : "end",
               parinfo ? parinfo->codeptr_ra : NULL,
               codeptr_ra);
   }
   
   // Get info for the related parallel region
   parallel_info_t *parinfo = parallel_data->ptr;
   if (parinfo == NULL) {
      if (par_reg_filt_len == 0)
         printf ("Warning: ignoring a work-event from a never encountered parallel region. "
                 "That typically corresponds to a \"omp for\" outside any parallel region.\n");
      return;
   }
   if (codeptr_ra == NULL) codeptr_ra = parinfo->codeptr_ra;

   // Excluding sync regions from filtered-out parallel regions
   if (is_target_codeptr (parinfo->codeptr_ra) == 0) return;

   // Get related stats (from the current ancestor thread)
   const int ancestor_thread_num = omp_get_ancestor_thread_num (level-1);
   assert (parinfo->per_thread != NULL && ancestor_thread_num < parinfo->nb_ancestor_threads);
   thread_parallel_info_t *tpi = &(parinfo->per_thread [ancestor_thread_num]);

   work_region_t *work_region = NULL;

   // Look for already existing work region (same wstype and codeptr_ra)
   assert (tpi->work_regions != NULL && thread_num < tpi->requested_parallelism);
   work_regions_t *const work_regions = &(tpi->work_regions [thread_num]);
   unsigned work_reg_rank;
   for (work_reg_rank = 0; work_reg_rank < work_regions->nb_work_regions; work_reg_rank++) {
      work_region_t *wr = &(work_regions->work_region [work_reg_rank]);
      if (wr->kind == wstype) {
         if (wr->codeptr_ra == codeptr_ra ||
             (endpoint == ompt_scope_end && wr->work_stats.start > 0.0)) {
            work_region = wr;
            break;
         } 
      }
   }

   // If new worksharing region, create it
   if (endpoint == ompt_scope_begin && work_region == NULL) {
      // If work_regions is full, enlarge it
      if (work_regions->nb_work_regions == work_regions->work_region_len) {
         const size_t work_region_size = work_regions->work_region_len *
            sizeof work_regions->work_region[0];
         work_regions->work_region = realloc (work_regions->work_region, work_region_size * 2);
         memset (work_regions->work_region + work_regions->work_region_len, 0, work_region_size);
         work_regions->work_region_len *= 2;
      }

      work_region = &(work_regions->work_region [work_regions->nb_work_regions]);
      work_regions->nb_work_regions++;

      // Set all fields: codeptr_ra, kind, count and work_stats
      work_region->codeptr_ra = codeptr_ra;
      work_region->kind       = wstype;
      init_stats (&(work_region->work_stats));
   }

   assert (work_region != NULL);
   stats_t *const stats = &(work_region->work_stats);

   switch (endpoint) {
   case ompt_scope_begin:
   {
      const double begin_time = __ompt_get_time(); // get as late as possible (to exclude tool)
      update_stats_begin (stats, begin_time);
   }
   break;

   case ompt_scope_end:
      update_stats_end (stats, dispatch_time);
      break;
   }
}
#endif

#ifdef PROMPT_TASK
void implicit_task (ompt_scope_endpoint_t endpoint,
                    ompt_data_t *parallel_data,
                    ompt_data_t *task_data,
                    unsigned int actual_parallelism,
                    unsigned int index,
                    int flags)
{
   assert (endpoint == ompt_scope_begin || endpoint == ompt_scope_end);
   assert (flags == ompt_task_initial || flags == ompt_task_implicit);

   if (endpoint == ompt_scope_begin) {
      pthread_mutex_lock (&task_UID_mutex);
      task_data->value = task_UID++;
      pthread_mutex_unlock (&task_UID_mutex);

      if (verbose_level >= 1) {
         if (flags == ompt_task_initial)
            printf ("[PROMPT] {thread #%d at level %d} Initial task #%lu was generated\n",
                    omp_get_thread_num(), omp_get_level(), task_data->value);
         else // ompt_task_implicit
            printf ("[PROMPT] {thread #%d at level %d} Implicit task #%lu was generated (index %u, %u threads in the parallel/teams region)\n",
                    omp_get_thread_num(), omp_get_level(), task_data->value,
                    index, actual_parallelism);
      }
   } else { // endpoint == ompt_scope_end
      if (verbose_level >= 1) {
         printf ("[PROMPT] {thread #%d at level ?} %s task #%lu was destroyed\n",
                 // omp_get_level segfaults in this context, at least with oneAPI 2021.4...
                 omp_get_thread_num(),
                 flags == ompt_task_initial ? "Initial" : "Implicit",
                 task_data->value);
      }
   }
}

/* task_create : Callback used for callbacks that are dispatched when task region or initial tasks are generated.
 * [In]  encountering_task_data
 * [In]  encountering_task_frame
 * [In]  new_task_date
 * [In]  flags : indicates the kind of task (initial, explicit, target) that is generated.
 * [In]  has_dependences : True if the generated task has dependences.
 * [In]  codeptr_ra: relates the implementation of OpenMP region to its source code.
 */

void task_create (ompt_data_t *encountering_task_data, const ompt_frame_t *encountering_task_frame,
                  ompt_data_t *new_task_data, int flags, int has_dependences,
                  const void *codeptr_ra)
{
   assert (new_task_data);
   assert ((flags && ompt_task_initial ) || // deprecated (no more dispatched via task_create)
           (flags && ompt_task_explicit) ||
           (flags && ompt_task_target  ));

   if (flags && ompt_task_initial) return; // deprecated

   pthread_mutex_lock (&task_UID_mutex);
   new_task_data->value = task_UID++;
   pthread_mutex_unlock (&task_UID_mutex);

   if (verbose_level >= 1) {
      printf ("[PROMPT] {thread #%d at level %d} At %p, task #%u created task #%u "
              "(type=%s, %s dependences)\n",
              omp_get_thread_num(), omp_get_level(), codeptr_ra,
              encountering_task_data->value, new_task_data->value,
              flags && ompt_task_explicit ? "explicit" : "target",
              has_dependences ? "with" : "without");
   }
}

void task_schedule (ompt_data_t *prior_task_data,
                    ompt_task_status_t prior_task_status,
                    ompt_data_t *next_task_data)
{
   if (verbose_level >= 1) {
      static const char *task_status_name[] = { NULL, "complete", "yield", "cancel", "detach",
                                                "early_fullfill", "late_fullfill", "switch",
                                                "taskwait_complete" };

      printf ("[PROMPT] {thread #%d at level %d} Schedule from task #%lu (%s) to task #%lu\n",
              omp_get_thread_num(), omp_get_level(), prior_task_data->value,
              task_status_name [prior_task_status], next_task_data->value);
   }
}
#endif // PROMPT_TASK

static void check_set_cb_result (ompt_set_result_t res, const char *cb_name)
{
#ifndef NDEBUG
   char *str = NULL;

   switch (res) {
   case ompt_set_error           : str = "error"           ; break;
   case ompt_set_never           : str = "never"           ; break;
   case ompt_set_impossible      : str = "impossible"      ; break;
   case ompt_set_sometimes       : str = "sometimes"       ; break;
   case ompt_set_sometimes_paired: str = "sometimes_paired"; break;
   default:
      break;
   }

   if (str != NULL)
      fprintf (stderr, "[PROMPT] set %s returned omp_set_%s\n", cb_name, str);
#endif
}

/* ompt_tool_init: Init tool function.
 */
void ompt_tool_init ( ompt_function_lookup_t ompt_lookup_fn, ompt_data_t* tool_data )
{
   assert(ompt_lookup_fn);

   /* NOTE: La fonction d'initialization est la première fonction de l'outil
    *       qui est appellée. La détection d'outil (ompt_start_tool) et l'appel
    *       à cette fonction se fait à l'initialization du runtime OpenMP.
    *
    *       OMPT définit 2 grandes classes de fonctions, les callbacks et les
    *       fonctions point d'entrées. L'outil ne peux y accéder à aucunes
    *       d'elles directement (un outil ne déclanche pas de callbacks et n'a
    *       pas de visibilité sur les fonctions point d'entrées). Pour cela
    *       le runtime OpenMP lui passe une fonction de "recherche" des fonctions
    *       points d'entrées (ompt_lookup_fn). L'outil peux alors récupérer les
    *       adresses des fonctions points d'entrées dont il a besoin et en garder
    *       une collection pour toute la durée d exécution.
    *
    *       Une fonction point d'entrée primordiale est celle permettant
    *       d'enregistrer les callbacks (ompt_set_callback), cad, associer les
    *       fonctions de l'outil aux évènements OMPT. Ces opérations se font
    *       ici, dans la fonction d'initialization de l'outil.
    */

   // Set/check parallel regions filtering
   const char *par_reg_str = getenv ("PROMPT_PARALLEL_REGIONS");
   if (par_reg_str == NULL) {
      printf ("[PROMPT] By default all parallel regions are profiled. Set the PROMPT_PARALLEL_REGIONS environment variable to 0x123,0x456 to profile only some regions (from addresses in the executable)\n");

      par_reg_filt = NULL;
      par_reg_filt_len = 0;
   }
   else {
      unsigned par_reg_filt_max_len = 10;
      par_reg_filt = malloc (par_reg_filt_max_len * sizeof par_reg_filt[0]);
      par_reg_filt_len = 0;

      // Parse (strtok) addresses (comma-separated) in <par_reg_str>
      char *str = strdup (par_reg_str);
      const char *sep = ",";
      const char *tok = strtok (str, sep);
      while (tok != NULL) {
         errno = 0;
         const long addr = strtol (tok, NULL, 16);
         if (errno == 0 && addr != 0) {
            // Resize if necessary
            if (par_reg_filt_len == par_reg_filt_max_len) {
               par_reg_filt_max_len *= 2;
               par_reg_filt = realloc (par_reg_filt, par_reg_filt_max_len * sizeof par_reg_filt[0]);
            }

            par_reg_filt [par_reg_filt_len++] = (void *)(unsigned long) addr;
         }
         tok = strtok (NULL, sep);
      }
      free (str);

      if (par_reg_filt_len == 0) {
         printf ("[PROMPT] Invalid PROMPT_PARALLEL_REGIONS value (%s): expecting 0x123[,0x456...]\n",
                 par_reg_filt);
         return;
      }
   }

   /* Lookup for callback setter entry point */
   ompt_set_callback_t g_set_cb = (ompt_set_callback_t) ompt_lookup_fn ("ompt_set_callback");
   assert (g_set_cb );

   /* Register tool callbacks */
   g_set_cb (ompt_callback_thread_begin, (ompt_callback_t) thread_begin );
   g_set_cb (ompt_callback_thread_end,   (ompt_callback_t) thread_end );

   g_set_cb (ompt_callback_parallel_begin, (ompt_callback_t) parallel_begin );
   g_set_cb (ompt_callback_parallel_end,   (ompt_callback_t) parallel_end );

   ompt_set_result_t res_sync;
#ifdef PROMPT_SYNC
   res_sync = g_set_cb (ompt_callback_sync_region, (ompt_callback_t) sync_region );
   check_set_cb_result (res_sync, "sync_region");
   res_sync = g_set_cb (ompt_callback_reduction,   (ompt_callback_t) sync_region ); // seems not used
   check_set_cb_result (res_sync, "reduction");
   res_sync = g_set_cb (ompt_callback_sync_region_wait, (ompt_callback_t) sync_region_wait );
   check_set_cb_result (res_sync, "sync_region_wait");
#endif

#ifdef PROMPT_WORK // worksharing: ompt_callback_work
   res_sync = g_set_cb (ompt_callback_work, (ompt_callback_t) work);
   check_set_cb_result (res_sync, "work");
#endif

#ifdef PROMPT_TASK
   g_set_cb (ompt_callback_implicit_task, (ompt_callback_t) implicit_task );
   g_set_cb (ompt_callback_task_create  , (ompt_callback_t) task_create   );
   g_set_cb (ompt_callback_task_schedule, (ompt_callback_t) task_schedule );
#endif

   verbose_level = getenv ("PROMPT_VERBOSE") != NULL ? atoi (getenv ("PROMPT_VERBOSE")) : 0;

   // Create the PrOMPT output directory

   // Top-level directory: PROMPT_OUTPUT_PATH or "prompt_results"
   const char *const prompt_output_path = getenv ("PROMPT_OUTPUT_PATH");
   const char *top_path = prompt_output_path != NULL ? prompt_output_path : "prompt_results";
   if (mkdir (top_path, 0755) != 0 && errno != EEXIST) {
      perror ("[PROMPT] Failed to create output directory\n");
      return;
   }

   // Create a node/process hierarchy if PROMPT_SINGLE_PROCESS is not set to "true" or "yes"
   const char *const single_process = getenv ("PROMPT_SINGLE_PROCESS");
   if (single_process == NULL ||
       (strstr (single_process, "yes") == NULL &&
        strstr (single_process, "true") == NULL)) {
      // Node-level directory: top_path/<node name>
      char hostname [128+1];
      const int hostname_ret = gethostname (hostname, sizeof hostname);
      char node_path [strlen (top_path) + strlen (hostname) + 2];
      sprintf (node_path, "%s/%s", top_path, hostname);
      if (hostname_ret != 0 || (mkdir (node_path, 0755) != 0 && errno != EEXIST)) {
         perror ("[PROMPT] Failed to create node-level output directory\n");
         return;
      }

      // Process-level directory: node_path/<process ID>
      char process_path [strlen (node_path) + strlen ("/999999") + 2];
      sprintf (process_path, "%s/%d", node_path, getpid());
      if (mkdir (process_path, 0755) != 0 && errno != EEXIST) {
         perror ("[PROMPT] Failed to create process-level output directory\n");
         return;
      }

      output_path = strdup (process_path);
   }
   else // single-process output
      output_path = top_path;

   sampling_period = (getenv ("PROMPT_SAMPLING_PERIOD") != NULL)
      ? atoi (getenv ("PROMPT_SAMPLING_PERIOD")) : 0;

   // Initialize parallel_regions[]
   unsigned lvl;
   for (lvl=0; lvl<MAX_NEST; lvl++) {
      parallel_regions_t *pr = &(parallel_regions [lvl]);
      pthread_rwlock_init (&(pr->rwlock), NULL);
      memset (pr->parallel_info_array, 0, sizeof pr->parallel_info_array);
      memset (pr->dic, 0, sizeof pr->dic);
      pr->nb_parallel_info = 0;
      pr->last_parinfo = NULL;
   }

#ifdef PROMPT_TASK
   // Initialize mutex to serialize incrementations of task UID
   task_UID = 0;
   pthread_mutex_init (&task_UID_mutex, NULL);
#endif

   // Initialize start_time
   if (clock_gettime (CLOCK_REALTIME, &start_time_ts) != 0) perror ("clock_gettime");

   // Check precision
   struct timespec ts_res;
   if (clock_getres (CLOCK_REALTIME, &ts_res) != 0) perror ("clock_getres");
   printf ("INFO: clock precision is %lu ns\n", ts_res.tv_nsec);
}

// Print parallel regions info to par_regions.csv
static void print_parallel_region (const parallel_info_t *parinfo, unsigned ancestor_thread_num,
                                   FILE *fp, FILE *samples_fp, ompt_tool_addr2line_context_t *a2l_ctxt)
{
   // Get source line info for the parallel region
   resolved_codeptr_t rc;
   ompt_tool_addr2line_get (a2l_ctxt, parinfo->codeptr_ra, &rc);

   // Get stats related to the ancestor thread
   const thread_parallel_info_t *tpi = &(parinfo->per_thread [ancestor_thread_num]);

   // print module_name_offset
   fprintf (fp, "%s:%p,", rc.module_name, rc.module_offset);

   // print parent_reg_module_name_offset
   if (parinfo->parent != NULL) {
      // Get module name and offset for the parent parallel region
      resolved_codeptr_t parent_rc;
      ompt_tool_addr2line_get (a2l_ctxt, parinfo->parent->codeptr_ra, &parent_rc);
      fprintf (fp, "%s:%p,", parent_rc.module_name, parent_rc.module_offset);
   }
   else
      fprintf (fp, "NA,");

   // print level,ancestor_thread_num,invoker,parallel_or_teams,requested_parallelism
   fprintf (fp, "%d,%d,%s,%s,%u,",
            parinfo->level,
            ancestor_thread_num,
            parinfo->flags & ompt_parallel_invoker_program ? "program" : "runtime",
            parinfo->flags & ompt_parallel_team ? "parallel" : "teams",
            tpi->requested_parallelism);

#if defined(PROMPT_SYNC) || defined(PROMPT_WORK)
   unsigned thread_rank;
#endif

#ifdef PROMPT_SYNC
   // print sync_time_sum,wait_time_sum,parallelism_overhead
   int negative_sync_or_wait = 0;
   const char *msg = "[PROMPT] Error: negative (wait/sync)-time for %s:%p => skip. "
      "Please rerun with a PrOMPT library compiled without -DNDEBUG and "
      "report the failed assertion\n";
   double sync_time_sum = 0.0;
   double wait_time_sum = 0.0;

   // Sum sync_time and wait_time (across all threads and sync regions)
   unsigned sync_reg_rank;
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      const sync_regions_t *sync_regions = &(tpi->sync_regions [thread_rank]);

      for (sync_reg_rank = 0; sync_reg_rank < sync_regions->nb_sync_regions; sync_reg_rank++) {
         const sync_region_t *sync_region = &(sync_regions->sync_region [sync_reg_rank]);
         const stats_t *sync_stats = &(sync_region->sync_stats);
         const stats_t *wait_stats = &(sync_region->wait_stats);

         // Accumulate sync_time_sum
         assert (sync_stats->sum >= 0.0);
         if (sync_stats->sum > 0.0)
            sync_time_sum += sync_stats->sum;
         else if (sync_stats->sum < 0.0 && !negative_sync_or_wait) {
            // Only at first occurrence for a given parallel region
            printf (msg, rc.module_name, rc.module_offset);
            negative_sync_or_wait = 1;
         }

         // Accumulate wait_time_sum
         assert (wait_stats->sum >= 0.0);
         if (wait_stats->sum > 0.0)
            wait_time_sum += wait_stats->sum;
         else if (wait_stats->sum < 0.0 && !negative_sync_or_wait) {
            // Only at first occurrence for a given parallel region
            printf (msg, rc.module_name, rc.module_offset);
            negative_sync_or_wait = 1;
         }
      }
   }

   // Print sync_time and wait_time sums
   fprintf (fp, "%.9f,%.9f,%f,",
            sync_time_sum, wait_time_sum,
            (sync_time_sum * 100.0) / (tpi->stats.sum * tpi->requested_parallelism));
#endif

#ifdef PROMPT_WORK
   // print work_time_sum,parallelism_overhead
   double work_time_sum = 0.0;

   // Sum work_time (across all threads and work regions)
   unsigned work_reg_rank;
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      const work_regions_t *work_regions = &(tpi->work_regions [thread_rank]);

      for (work_reg_rank = 0; work_reg_rank < work_regions->nb_work_regions; work_reg_rank++) {
         const work_region_t *work_region = &(work_regions->work_region [work_reg_rank]);
         const stats_t *work_stats = &(work_region->work_stats);

         work_time_sum += work_stats->sum;
      }
   }

   // Print work_time sums
   fprintf (fp, "%.9f,%f,",
            work_time_sum,
            (work_time_sum * 100.0) / (tpi->stats.sum * tpi->requested_parallelism));
#endif

   // print time_sum,time_min,time_max,nb_instances,fct_name,src_file_line
   const char *fct_name = rc.fct_demangled_name ? rc.fct_demangled_name : rc.fct_name;
   fprintf (fp, "%.9f,%.9f,%.9f,%u,\"%s\",%s:%u\n",
            tpi->stats.sum,
            tpi->stats.min,
            tpi->stats.max,
            tpi->stats.nb_instances,
            fct_name ? fct_name : "",
            rc.src_file ? rc.src_file : "",
            rc.src_line);

   // print samples
   unsigned sample_rank;
   unsigned instance_rank = 1;
   for (sample_rank = 0; sample_rank < tpi->stats.nb_samples; sample_rank++) {
      // print module_name_offset
      fprintf (samples_fp, "%s:%p,", rc.module_name, rc.module_offset);

      // print level, ancestor_thread_num
      fprintf (samples_fp, "%d,%d,", parinfo->level, ancestor_thread_num);

      // print instance rank and value
      fprintf (samples_fp, "%u,%.9f\n", instance_rank, tpi->stats.samples [sample_rank]);

      if (sampling_period == 0) instance_rank *= 2;
      else instance_rank += sampling_period;
   }
}

#if defined(PROMPT_SYNC) || defined(PROMPT_WORK)
typedef struct {
   const void *codeptr_ra;
   int kind;
} ptr_kind_pair_t;

typedef struct {
   unsigned nb;
   unsigned len;
   ptr_kind_pair_t *pairs;
} ptr_kind_pairs_t;

static void ptr_kind_pairs_init (ptr_kind_pairs_t *dic)
{
   dic->len = 10;
   dic->nb  = 0;
   dic->pairs = calloc (dic->len, sizeof dic->pairs[0]);
}

// use bsearch/qsort if too slow
static int ptr_kind_pairs_lookup (const ptr_kind_pairs_t *dic, const void *codeptr_ra, int kind)
{
   unsigned i;
   for (i=0; i<dic->nb; i++) {
      const ptr_kind_pair_t *const pair = &(dic->pairs[i]);
      if (pair->codeptr_ra == codeptr_ra && pair->kind == kind)
         return 1;
   }

   return 0;
}

// use bsearch/qsort if too slow
static void ptr_kind_pairs_insert (ptr_kind_pairs_t *dic, const void *codeptr_ra, int kind)
{
   assert (ptr_kind_pairs_lookup (dic, codeptr_ra, kind) == 0);
   if (dic->nb == dic->len) {
      const unsigned new_len = dic->len * 2;
      dic->pairs = realloc (dic->pairs, new_len * sizeof dic->pairs[0]);
      dic->len = new_len;
   }

   dic->pairs [dic->nb].codeptr_ra = codeptr_ra;
   dic->pairs [dic->nb].kind       = kind;
   dic->nb = dic->nb + 1;
}

static void ptr_kind_pairs_destroy (ptr_kind_pairs_t *dic)
{
   free (dic->pairs);
}
#endif

#ifdef PROMPT_SYNC
// Print sync region info to sync_regions.csv
static void print_sync_region (const parallel_info_t *parinfo, unsigned ancestor_thread_num,
                               const void *codeptr_ra, ompt_sync_region_t kind,
                               FILE *fp, FILE *samples_fp, ompt_tool_addr2line_context_t *a2l_ctxt)
{
   const char *ompt_sync_region_name[] = { NULL, "barrier", "barrier_implicit", "barrier_explicit",
                                           "barrier_implem", "taskwait", "taskgroup", "reduction",
                                           "barrier_implicit_workshare", "barrier_implicit_parallel",
                                           "teams" };

   // Get stats related to the ancestor thread
   const thread_parallel_info_t *tpi = &(parinfo->per_thread [ancestor_thread_num]);

   unsigned thread_rank;

   // Create a flattened view for events having codeptr_ra
   unsigned nb_threads = 0;
   struct { const sync_region_t *reg; unsigned rank; } regs [tpi->requested_parallelism];
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      const sync_regions_t *sync_regions = &(tpi->sync_regions [thread_rank]);

      unsigned sync_reg_rank;
      for (sync_reg_rank = 0; sync_reg_rank < sync_regions->nb_sync_regions; sync_reg_rank++) {
         const sync_region_t *sync_region = &(sync_regions->sync_region [sync_reg_rank]);

         if (sync_region->codeptr_ra == codeptr_ra && sync_region->kind == kind) {
            regs [nb_threads].reg = sync_region;
            regs [nb_threads].rank = thread_rank;
            nb_threads++;
         }
      }
   }

   // Warn in case of partial threads coverage
   if (nb_threads < tpi->requested_parallelism) {
      printf ("Warning: only %u threads (out of %u) have encoutered the %p sync-region\n",
              nb_threads, tpi->requested_parallelism, codeptr_ra);
   }

   // Get source line info for the parallel region
   resolved_codeptr_t par_rc;
   ompt_tool_addr2line_get (a2l_ctxt, parinfo->codeptr_ra, &par_rc);

   // Get source line info for the sync region and demangled name for the related function
   resolved_codeptr_t rc;
   ompt_tool_addr2line_get (a2l_ctxt, codeptr_ra, &rc);
   const char *fct_name = rc.fct_demangled_name ? rc.fct_demangled_name : rc.fct_name;

   // AT = All/Across Threads
   double sync_sum_AT = 0.0;
   double sync_min_AT = 0.0;
   double sync_max_AT = 0.0;
   double wait_sum_AT = 0.0;
   double wait_min_AT = 0.0;
   double wait_max_AT = 0.0;
   unsigned nb_instances_sum_AT = 0;

   // Print stats for each thread and sum them to print them later
   for (thread_rank = 0; thread_rank < nb_threads; thread_rank++) {
      const sync_region_t *sync_region = regs [thread_rank].reg;
      const stats_t *sync_stats = &(sync_region->sync_stats);
      const stats_t *wait_stats = &(sync_region->wait_stats);

      // print module_name_offset,par_reg_module_name_offset,par_reg_thread_num,thread_num,kind
      fprintf (fp, "%s:%p,%s:%p,%d,%d,%s,",
               rc.module_name, rc.module_offset,
               par_rc.module_name, par_rc.module_offset, ancestor_thread_num,
               regs [thread_rank].rank, ompt_sync_region_name [sync_region->kind]);

      // print sync_time_(sum/min/max)
      fprintf (fp, "%.9f,%.9f,%.9f,",
               sync_stats->sum,
               sync_stats->min,
               sync_stats->max);

      // update sum/min/max (sync)
      sync_sum_AT += sync_stats->sum;
      if (thread_rank == 0 || sync_stats->min < sync_min_AT)
         sync_min_AT = sync_stats->min;
      if (thread_rank == 0 || sync_stats->max > sync_max_AT)
         sync_max_AT = sync_stats->max;

      // print wait_time_(sum/min/max)
      fprintf (fp, "%.9f,%.9f,%.9f,",
               wait_stats->sum,
               wait_stats->min,
               wait_stats->max);

      // update sum/min/max (wait)
      wait_sum_AT += wait_stats->sum;
      if (thread_rank == 0 || wait_stats->min < wait_min_AT)
         wait_min_AT = wait_stats->min;
      if (thread_rank == 0 || wait_stats->max > wait_max_AT)
         wait_max_AT = wait_stats->max;

      // print nb_instances,fct_name,src_file_line
      fprintf (fp, "%u,\"%s\",%s:%u\n",
               sync_stats->nb_instances, fct_name ? fct_name : "",
               rc.src_file ? rc.src_file : "", rc.src_line);

      // update nb_instances (sum)
      nb_instances_sum_AT += sync_stats->nb_instances;

      // print samples
      if (sync_stats->nb_instances == wait_stats->nb_instances)
         assert (sync_stats->nb_samples == wait_stats->nb_samples);
      else if (wait_stats->nb_instances == 0)
         printf ("[PROMPT] Warning: no wait events for the %p sync-region (thread #%u)\n",
                 codeptr_ra, thread_rank);
      else // wait_stats->nb_instances > 0 && sync_stats->nb_instances != wait_stats->nb_instances
         printf ("[PROMPT] Warning: unpaired sync-wait events for the %p sync-region (thread #%u)\n",
                 codeptr_ra, thread_rank);

      unsigned sample_rank;
      unsigned instance_rank = (sampling_period == 0) ? 1 : sampling_period;
      for (sample_rank = 0; sample_rank < sync_stats->nb_samples; sample_rank++) {
         // print module_name_offset
         fprintf (samples_fp, "%s:%p,", rc.module_name, rc.module_offset);

         // print par_reg_thread_num,thread_num,kind
         fprintf (samples_fp, "%d,%d,%s,", ancestor_thread_num, regs [thread_rank].rank,
                  ompt_sync_region_name [sync_region->kind]);

         // print instance rank, sync_time
         fprintf (samples_fp, "%u,%.9f,", instance_rank,
                  sync_stats->samples [sample_rank]);

         // print wait_time
         if (sync_stats->nb_instances == wait_stats->nb_instances) {
            // paired sync-wait events
            fprintf (samples_fp, "%.9f\n", wait_stats->samples [sample_rank]);
         } else {
            // no wait events (observed for kind=reduction) or unpaired sync-wait events
            fprintf (samples_fp, "0\n");
         }

         if (sampling_period == 0) instance_rank *= 2;
         else instance_rank += sampling_period;
      }
   } // for each thread rank

   // Across-threads summary
   // print module_name_offset,par_reg_module_name_offset,par_reg_thread_num,thread_num,kind
   fprintf (fp, "%s:%p,%s:%p,%d,ALL,%s,",
            rc.module_name, rc.module_offset,
            par_rc.module_name, par_rc.module_offset, ancestor_thread_num,
            ompt_sync_region_name [regs[0].reg->kind]);

   // print sync_time_(sum/min/max)
   fprintf (fp, "%.9f,%.9f,%.9f,", sync_sum_AT, sync_min_AT, sync_max_AT);

   // print wait_time_(sum/min/wax)
   fprintf (fp, "%.9f,%.9f,%.9f,", wait_sum_AT, wait_min_AT, wait_max_AT);

   // nb_instances,fct_name,src_file_line
   fprintf (fp, "%u,\"%s\",%s:%u\n",
            nb_instances_sum_AT, fct_name ? fct_name : "",
            rc.src_file ? rc.src_file : "", rc.src_line);
}
#endif

#ifdef PROMPT_WORK
// Print sync region info to sync_regions.csv
static void print_work_region (const parallel_info_t *parinfo, unsigned ancestor_thread_num,
                               const void *codeptr_ra, ompt_work_t wstype,
                               FILE *fp, FILE *samples_fp, ompt_tool_addr2line_context_t *a2l_ctxt)
{
   const char *ompt_work_name[] = { NULL, "loop", "sections", "single_executor", "single_other",
                                    "workshare", "distribute", "taskloop", "scope" };

   // Get stats related to the ancestor thread
   const thread_parallel_info_t *tpi = &(parinfo->per_thread [ancestor_thread_num]);

   unsigned thread_rank;

   // Create a flattened view for events having codeptr_ra
   unsigned nb_threads = 0;
   struct { const work_region_t *reg; unsigned rank; } regs [tpi->requested_parallelism];
   for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
      const work_regions_t *work_regions = &(tpi->work_regions [thread_rank]);

      unsigned work_reg_rank;
      for (work_reg_rank = 0; work_reg_rank < work_regions->nb_work_regions; work_reg_rank++) {
         const work_region_t *work_region = &(work_regions->work_region [work_reg_rank]);

         if (work_region->codeptr_ra == codeptr_ra && work_region->kind == wstype) {
            regs [nb_threads].reg = work_region;
            regs [nb_threads].rank = thread_rank;
            nb_threads++;
         }
      }
   }

   // Warn in case of partial threads coverage (except for single sections)
   if (wstype != ompt_work_single_executor && wstype != ompt_work_single_other &&
       nb_threads < tpi->requested_parallelism) {
      printf ("Warning: only %u threads (out of %u) have encoutered the %p work-region\n",
              nb_threads, tpi->requested_parallelism, codeptr_ra);
   }

   // Get source line info for the parallel region
   resolved_codeptr_t par_rc;
   ompt_tool_addr2line_get (a2l_ctxt, parinfo->codeptr_ra, &par_rc);

   // Get source line info for the work region and demangled name for the related function
   resolved_codeptr_t rc;
   ompt_tool_addr2line_get (a2l_ctxt, codeptr_ra, &rc);
   const char *fct_name = rc.fct_demangled_name ? rc.fct_demangled_name : rc.fct_name;

   // AT = All/Across Threads
   double work_sum_AT = 0.0;
   double work_min_AT = 0.0;
   double work_max_AT = 0.0;
   unsigned nb_instances_sum_AT = 0;

   // Print stats for each thread and sum them to print them later
   for (thread_rank = 0; thread_rank < nb_threads; thread_rank++) {
      const work_region_t *work_region = regs [thread_rank].reg;
      const stats_t *work_stats = &(work_region->work_stats);

      // print module_name_offset,par_reg_module_name_offset,par_reg_thread_num,thread_num,kind
      fprintf (fp, "%s:%p,%s:%p,%d,%d,%s,",
               rc.module_name, rc.module_offset,
               par_rc.module_name, par_rc.module_offset, ancestor_thread_num,
               regs [thread_rank].rank, ompt_work_name [work_region->kind]);

      // print work_time_(sum/min/max)
      fprintf (fp, "%.9f,%.9f,%.9f,",
               work_stats->sum,
               work_stats->min,
               work_stats->max);

      // update sum/min/max (work)
      work_sum_AT += work_stats->sum;
      if (thread_rank == 0 || work_stats->min < work_min_AT)
         work_min_AT = work_stats->min;
      if (thread_rank == 0 || work_stats->max > work_max_AT)
         work_max_AT = work_stats->max;

      // print nb_instances,fct_name,src_file_line
      fprintf (fp, "%u,\"%s\",%s:%u\n",
               work_stats->nb_instances, fct_name ? fct_name : "",
               rc.src_file ? rc.src_file : "", rc.src_line);

      // update nb_instances (sum)
      nb_instances_sum_AT += work_stats->nb_instances;

      // print samples
      unsigned sample_rank;
      unsigned instance_rank = (sampling_period == 0) ? 1 : sampling_period;
      for (sample_rank = 0; sample_rank < work_stats->nb_samples; sample_rank++) {
         // print module_name_offset
         fprintf (samples_fp, "%s:%p,", rc.module_name, rc.module_offset);

         // print par_reg_thread_num,thread_num,kind
         fprintf (samples_fp, "%d,%d,%s,", ancestor_thread_num, regs [thread_rank].rank,
                  ompt_work_name [work_region->kind]);

         // print instance rank, work_time
         fprintf (samples_fp, "%u,%.9f\n", instance_rank,
                  work_stats->samples [sample_rank]);

         if (sampling_period == 0) instance_rank *= 2;
         else instance_rank += sampling_period;
      }
   } // for each thread rank

   // Across-threads summary
   // print module_name_offset,par_reg_module_name_offset,par_reg_thread_num,thread_num,kind
   fprintf (fp, "%s:%p,%s:%p,%d,ALL,%s,",
            rc.module_name, rc.module_offset,
            par_rc.module_name, par_rc.module_offset, ancestor_thread_num,
            ompt_work_name [regs[0].reg->kind]);

   // print work_time_(sum/min/max)
   fprintf (fp, "%.9f,%.9f,%.9f,", work_sum_AT, work_min_AT, work_max_AT);

   // nb_instances,fct_name,src_file_line
   fprintf (fp, "%u,\"%s\",%s:%u\n",
            nb_instances_sum_AT, fct_name ? fct_name : "",
            rc.src_file ? rc.src_file : "", rc.src_line);
}
#endif // PROMPT_WORK

static void free_parallel_regions ()
{
   unsigned lvl, i, anc_thr_rank;

   // For each OMP nest level
   for (lvl=0; lvl<MAX_NEST; lvl++) {
      parallel_regions_t *pr = &(parallel_regions [lvl]);

      // For each parallel region
      for (i=0; i < pr->nb_parallel_info; i++) {
         parallel_info_t *parinfo = &(pr->parallel_info_array[i]);

#ifdef PROMPT_SYNC
         for (anc_thr_rank = 0; anc_thr_rank < parinfo->nb_ancestor_threads; anc_thr_rank++)
            free (parinfo->per_thread [anc_thr_rank].sync_regions);
#endif
#ifdef PROMPT_WORK
         for (anc_thr_rank = 0; anc_thr_rank < parinfo->nb_ancestor_threads; anc_thr_rank++)
            free (parinfo->per_thread [anc_thr_rank].work_regions);
#endif
         free (parinfo->per_thread);
         pthread_rwlock_destroy (&(parinfo->rwlock));
      } // for each parallel region

      pthread_rwlock_destroy (&(pr->rwlock));
   } // for each OMP nest level
}

/* ompt_tool_fina: Finalize tool function.
 */
void ompt_tool_fina (ompt_data_t* tool_data)
{
   // Get end time (to subtract with start_time_ts and then get global walltime)
   struct timespec end_time_ts;
   if (clock_gettime (CLOCK_REALTIME, &end_time_ts) != 0) perror ("clock_gettime");

   /* NOTE: La fonction de finalization est la dernière fonction appellée
    *       par l'outil, la norme OpenMP impose qu'elle soit appellée après
    *       le dernier evènement OMPT. C'est donc ici que le traitement
    *       des données collectées pendant l'exécution est généralement fait.
    */

   // Free parallel regions filter
   free (par_reg_filt);
   par_reg_filt = NULL;
   par_reg_filt_len = 0;

   char par_regions_filename [strlen (output_path) + strlen ("/par_regions.csv") + 1];
   sprintf (par_regions_filename, "%s/par_regions.csv", output_path);
   char par_reg_smp_filename [strlen (output_path) + strlen ("/par_regions_samples.csv") + 1];
   sprintf (par_reg_smp_filename, "%s/par_regions_samples.csv", output_path);

   printf ("[PROMPT] Writing results to %s and %s\n", par_regions_filename, par_reg_smp_filename);

   // Parallel regions (walltime + total sync/wait-time): open file + print headers
   FILE *par_regions_fp = fopen (par_regions_filename, "w");
   if (par_regions_fp == NULL) {
      free_parallel_regions ();
      return;
   }

   fprintf (par_regions_fp, "module_name_offset,parent_reg_module_name_offset,");
   fprintf (par_regions_fp, "level,ancestor_thread_num,invoker,");
   fprintf (par_regions_fp, "parallel_or_teams,requested_parallelism,");
#ifdef PROMPT_SYNC
   fprintf (par_regions_fp, "sync_time_sum,wait_time_sum,parallelism_overhead,");
#endif
#ifdef PROMPT_WORK
   fprintf (par_regions_fp, "work_time_sum,parallelism_work_efficiency,");
#endif
   fprintf (par_regions_fp, "time_sum,time_min,time_max,nb_instances,fct_name,src_file_line\n");

   // Parallel regions samples: open file + print headers
   FILE *par_regions_samples_fp = fopen (par_reg_smp_filename, "w");
   if (par_regions_samples_fp == NULL) {
      free_parallel_regions ();
      return;
   }

   fprintf (par_regions_samples_fp, "module_name_offset,level,ancestor_thread_num,");
   fprintf (par_regions_samples_fp, "instance_rank,time\n");

#ifdef PROMPT_SYNC
   char sync_regions_filename [strlen (output_path) + strlen ("/sync_regions.csv") + 1];
   sprintf (sync_regions_filename, "%s/sync_regions.csv", output_path);
   char sync_reg_smp_filename [strlen (output_path) + strlen ("/sync_regions_samples.csv") + 1];
   sprintf (sync_reg_smp_filename, "%s/sync_regions_samples.csv", output_path);

   printf ("[PROMPT] Writing results to %s and %s\n", sync_regions_filename, sync_reg_smp_filename);

   // Syncronization regions (per-thread walltime): open file + print headers
   FILE *sync_regions_fp = fopen (sync_regions_filename, "w");
   if (sync_regions_fp == NULL) {
      free_parallel_regions ();
      return;
   }

   fprintf (sync_regions_fp, "module_name_offset,par_reg_module_name_offset,");
   fprintf (sync_regions_fp, "par_reg_thread_num,thread_num,kind,");
   fprintf (sync_regions_fp, "sync_time_sum,sync_time_min,sync_time_max,");
   fprintf (sync_regions_fp, "wait_time_sum,wait_time_min,wait_time_max,");
   fprintf (sync_regions_fp, "nb_instances,fct_name,src_file_line\n");

   // Syncronization regions samples: open file + print headers
   FILE *sync_regions_samples_fp = fopen (sync_reg_smp_filename, "w");
   if (sync_regions_samples_fp == NULL) {
      free_parallel_regions ();
      return;
   }

   fprintf (sync_regions_samples_fp, "module_name_offset,");
   fprintf (sync_regions_samples_fp, "par_reg_thread_num,thread_num,kind,");
   fprintf (sync_regions_samples_fp, "instance_rank,sync_time,wait_time\n");
#endif

#ifdef PROMPT_WORK
   char work_regions_filename [strlen (output_path) + strlen ("/work_regions.csv") + 1];
   sprintf (work_regions_filename, "%s/work_regions.csv", output_path);
   char work_reg_smp_filename [strlen (output_path) + strlen ("/work_regions_samples.csv") + 1];
   sprintf (work_reg_smp_filename, "%s/work_regions_samples.csv", output_path);

   printf ("[PROMPT] Writing results to %s and %s\n", work_regions_filename, work_reg_smp_filename);

   // Workronization regions (per-thread walltime): open file + print headers
   FILE *work_regions_fp = fopen (work_regions_filename, "w");
   if (work_regions_fp == NULL) {
      free_parallel_regions ();
      return;
   }

   fprintf (work_regions_fp, "module_name_offset,par_reg_module_name_offset,");
   fprintf (work_regions_fp, "par_reg_thread_num,thread_num,kind,");
   fprintf (work_regions_fp, "work_time_sum,work_time_min,work_time_max,");
   fprintf (work_regions_fp, "nb_instances,fct_name,src_file_line\n");

   // Worksharing regions samples: open file + print headers
   FILE *work_regions_samples_fp = fopen (work_reg_smp_filename, "w");
   if (work_regions_samples_fp == NULL) {
      free_parallel_regions ();
      return;
   }

   fprintf (work_regions_samples_fp, "module_name_offset,");
   fprintf (work_regions_samples_fp, "par_reg_thread_num,thread_num,kind,");
   fprintf (work_regions_samples_fp, "instance_rank,work_time\n");
#endif

   //   Print array content
   struct timespec walltime_ts;
   _timespec_sub (&end_time_ts, &start_time_ts, &walltime_ts);
   const double walltime = walltime_ts.tv_sec + walltime_ts.tv_nsec * 0.000000001;
   fprintf (par_regions_fp, "ALL,,,,,,,"); // CF header: 7 fields
#ifdef PROMPT_SYNC
   fprintf (par_regions_fp, ",,,"); // CF header: 3 fields
#endif
#ifdef PROMPT_WORK
   fprintf (par_regions_fp, ",,"); // CF header: 2 fields
#endif
   fprintf (par_regions_fp, "%f\n", walltime); // don't care about fields after walltime

   // Prepare context to get source line info
   ompt_tool_addr2line_context_t a2l_ctxt;
   ompt_tool_addr2line_init (&a2l_ctxt);

   unsigned lvl, i, anc_thr_rank;
   // For each OMP nest level
   for (lvl=0; lvl<MAX_NEST; lvl++) {
      const parallel_regions_t *pr = &(parallel_regions [lvl]);

      // For each parallel region
      for (i=0; i < pr->nb_parallel_info; i++) {
         const parallel_info_t *parinfo = &(pr->parallel_info_array[i]);
         assert (parinfo->per_thread != NULL);

         // For each ancestor thread (single one at top-level)
         for (anc_thr_rank = 0; anc_thr_rank < parinfo->nb_ancestor_threads; anc_thr_rank++) {
            const thread_parallel_info_t *tpi = &(parinfo->per_thread [anc_thr_rank]);

            // Process only enabled stats
            if (tpi->requested_parallelism > 0) {
               print_parallel_region (parinfo, anc_thr_rank,
                                      par_regions_fp, par_regions_samples_fp,
                                      &a2l_ctxt);

#ifdef PROMPT_SYNC
               const sync_regions_t *th0_sync_regions = &(tpi->sync_regions[0]);
               unsigned sync_reg_rank;
               for (sync_reg_rank = 0; sync_reg_rank < th0_sync_regions->nb_sync_regions; sync_reg_rank++) {
                  const sync_region_t *th0_sync_region = &(th0_sync_regions->sync_region [sync_reg_rank]);
                  print_sync_region (parinfo, anc_thr_rank, th0_sync_region->codeptr_ra, th0_sync_region->kind, sync_regions_fp, sync_regions_samples_fp, &a2l_ctxt);
               }
#endif

#ifdef PROMPT_WORK
               ptr_kind_pairs_t dic;
               ptr_kind_pairs_init (&dic);

               unsigned thread_rank, work_reg_rank;
               for (thread_rank = 0; thread_rank < tpi->requested_parallelism; thread_rank++) {
                  const work_regions_t *work_regions = &(tpi->work_regions [thread_rank]);

                  for (work_reg_rank = 0; work_reg_rank < work_regions->nb_work_regions; work_reg_rank++) {
                     const work_region_t *wr = &(work_regions->work_region [work_reg_rank]);
                     if (ptr_kind_pairs_lookup (&dic, wr->codeptr_ra, wr->kind) == 0) {
                        print_work_region (parinfo, anc_thr_rank, wr->codeptr_ra, wr->kind, work_regions_fp, work_regions_samples_fp, &a2l_ctxt);
                        ptr_kind_pairs_insert (&dic, wr->codeptr_ra, wr->kind);
                     }
                  }
               }

               ptr_kind_pairs_destroy (&dic);
#endif
            }
         } // for each ancestor thread
      } // for each parallel region
   } // for each OMP nest level

   // Free memory allocated for the context used to retrieve source line info
   ompt_tool_addr2line_destroy (&a2l_ctxt);

   // Close files
   fclose (par_regions_fp);
   fclose (par_regions_samples_fp);
#ifdef PROMPT_SYNC
   fclose (sync_regions_fp);
   fclose (sync_regions_samples_fp);
#endif
#ifdef PROMPT_WORK
   fclose (work_regions_fp);
   fclose (work_regions_samples_fp);
#endif

   /* Notify other tools that dump is finished, useful when PrOMPT invokation is non-blocking,
    * for instance via jobscript submission */
   char done_filename [strlen (output_path) + strlen ("/prompt_done") + 1];
   sprintf (done_filename, "%s/prompt_done", output_path);
   FILE *done_fp = fopen (done_filename, "w");
   if (done_fp != NULL)
      fclose (done_fp);
   else
      printf ("[PROMPT] Warning: cannot create %s to notify dump completion\n", done_filename);

#ifdef PROMPT_TASK
   pthread_mutex_destroy (&task_UID_mutex);
#endif

   free_parallel_regions ();
}
