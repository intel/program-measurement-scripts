#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include "omp-tools.h" // OMPT

void ompt_tool_init ( ompt_function_lookup_t ompt_lookup_fn, ompt_data_t* tool_data );
void ompt_tool_fina ( ompt_data_t* tool_data );

/* ompt_initialize: Tool initialize routine.
 * [In]  ompt_lookup_fn: Query function to lookup for ompt entry points.
 * [In]  initial_device_num: device num (heterogeneous node).
 * [In]  tool_data: global storage of the tool.
 * [Out] integer: Boolean behaviour, true or false.
 */
static int ompt_initialize ( ompt_function_lookup_t ompt_lookup_fn,
                             int initial_device_num,
                             ompt_data_t* tool_data ) {

   int ret = 0;

   if( ompt_lookup_fn ) {
      /* Call intialization sub-routine */
      ompt_tool_init( ompt_lookup_fn, tool_data );
      ret = 1;
   }

   return ret;
}

/* ompt_finalize: Tool finalize routine.
 * [In]  tool_data: global storage of the tool.
 */
static void ompt_finalize ( ompt_data_t* tool_data ) {

   /* Call finalization sub-routine */
   ompt_tool_fina( tool_data );
}

static char *omp_version_string (unsigned ver)
{
   assert (ver >= 201611); // OMPT was introduced along with OpenMP 5.0 Preview 1 (2016 Nov.)

   switch (ver) {
   case 202011: return "5.1";
   case 201811: return "5.0";
   case 201611: return "5.0 Preview 1";
   }

   assert (ver > 202011);

   return "> 5.1";
}

/* ompt_start_tool: Routine called by Omp runtime to determine if a tool has
 * provided initialize and finalize routines.
 * [In]  omp_version: OpenMP runtime supported version.
 * [In]  runtime_version: OpenMP implementation runtime version.
 * [Out] tool_result: Structure contening tool initialize and finalize routines.
 */
ompt_start_tool_result_t*
ompt_start_tool ( unsigned int omp_version,
                  const char *runtime_version ) {
   printf ("[PROMPT] Tool compiled with _OPENMP=%d (%s)\n",
           _OPENMP, omp_version_string ((unsigned) _OPENMP));
   printf ("[PROMPT] OpenMP runtime is [%s] with API %d (%s) support\n",
           runtime_version, omp_version, omp_version_string (omp_version));
   if ((unsigned) _OPENMP < omp_version) {
      printf ("[PROMPT] Warning: PrOMPT was compiled with an OpenMP version older than runtime's: some applications may not be correctly profiled\n");
   }

   // need of persistent memory (static or malloc)
   static ompt_start_tool_result_t tool_res = { ompt_initialize, ompt_finalize, ompt_data_none };

   return &tool_res;
}
