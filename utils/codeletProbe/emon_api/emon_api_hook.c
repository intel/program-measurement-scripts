#include "hook.h"


///* Intel's SEP header to perform per region measurement*/
//#include <sampling.h>
#ifdef HAS_EMON_API
#include <emon_api.h>
#endif

//#ifdef HAS_EMON_API
//static char *emon_api_stream = "emon_api.out";
//#endif

#ifdef HAS_EMON_API
static EMON_HANDLE emon_handle;
static EMON_DATA   emon_data_before, emon_data_after, emon_data_result, emon_data_sum;
#endif

void init_hook() {
#ifdef HAS_EMON_API
           EMONConfig ("emon_api_config_file", &emon_handle);

           EMONStart (&emon_handle);
	   emon_data_sum = EMON_DATA_NULL;
#endif
}

void measure_start_hook() {
#ifdef HAS_EMON_API
		EMONRead (emon_handle, &emon_data_before);
#endif
}

void measure_pause_hook() {
#ifdef HAS_EMON_API
		EMONRead (emon_handle, &emon_data_after);
		EMONDataCalculate (emon_handle, emon_data_before, emon_data_after, &emon_data_result, "SUBTRACTION");
		EMONDataCalculate (emon_handle, emon_data_result, emon_data_sum, &emon_data_sum, "ADDITION");
#endif
}

void measure_print_data_hook() {
#ifdef HAS_EMON_API
	// open file to redirect to
//	int emon_api_fd = open (emon_api_stream, O_WRONLY | O_CREAT| O_APPEND, S_IRUSR|S_IWUSR);
//	if (emon_api_fd < 0) {
//		fprintf(stderr, "Error open file for EMON output!\n");
//		return;
//	}

	// redirect stdout to file
//	int save_stdout = dup (1);
//	fflush(stdout);
//	int rst = dup2(emon_api_fd,1);
//	if (rst < 0) {
//		fprintf(stderr, "Error redirecting EMON output to stderr!\n");
//		return;
//	}
	
	EMONDataPrint (emon_data_sum);
	// redirect back to stdout
//	fflush(stdout);
//	rst = dup2(save_stdout, 1);
//	if (rst < 0) {
//		fprintf(stderr, "Error redirecting back stdout!\n");
//		return;
//	}
//	close(emon_api_fd);
#endif

}

void measure_stop_hook() {
#ifdef HAS_EMON_API
	EMONStop(&emon_handle);
#endif

}
