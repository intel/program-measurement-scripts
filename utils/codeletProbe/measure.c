#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <unistd.h>
#include <sched.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
///* ntel's SEP header to perform per region measurement*/
//#include <sampling.h>
#ifdef HAS_EMON_API
#include <emon_api.h>
#endif
#ifdef HAS_SNIPER_API
#include <sim_api.h>
#endif


// Define rdtscll for x86_64 arch
#ifdef __x86_64__
        #define rdtscll(val) do { \
                        unsigned int __a,__d; \
                        asm volatile("rdtsc" : "=a" (__a), "=d" (__d)); \
                        (val) = ((unsigned long)__a) | (((unsigned long)__d)<<32); \
        } while(0)
#endif

// Define rdtscll for i386 arch
#ifdef __i386__
        #define rdtscll(val) { \
                asm volatile ("rdtsc" : "=A"(val)); \
                }
#endif

static FILE *input;
static FILE *output;
static char *stream = "time.out";
static char *copies = "codelet.copy";
static int  pid = 1;
static int  *pids = NULL;
static int  nbClones = 0;
//#ifdef HAS_EMON_API
//static char *emon_api_stream = "emon_api.out";
//#endif

typedef struct {
	double start;
//	double stop;
	double ticks;
} TimerData;
TimerData *timer_data;
static int paused; // collection paused?


#ifdef HAS_EMON_API
static EMON_HANDLE emon_handle;
static EMON_DATA   emon_data_before, emon_data_after, emon_data_result, emon_data_sum;
#endif

static __inline__ unsigned long long getticks(void)
{
   unsigned long long ret;
   rdtscll(ret);
   return ret;
}

void evaluation_init()
{
	timer_data = (TimerData*)malloc(sizeof(TimerData));
	timer_data->ticks = 0;
}

void evaluation_start()
{
	//evaluationFct start;
	timer_data->start = getticks();
//	// Start SEP measurement	
//	VTResumeSampling();
}

void evaluation_stop()
{
	//evaluationFct stop;
  if (paused) return;
  long long ticks=getticks();
  timer_data->ticks += (ticks-timer_data->start);
  // pause is set from caller (measure_pause_())
//	// Stop SEP measurement	
//	VTPauseSampling();
}

void evaluation_close()
{
	if( timer_data != NULL )
		free(timer_data);
	if(pids != NULL)
		free(pids);
}

void print_results()
{
	output = fopen(stream, "a");
	//	fprintf(output, "%0.6f\n", (double) (timer_data->stop - timer_data->start));
	fprintf(output, "%0.6f\n", (double) (timer_data->ticks));
	fclose(output);
	return;
}

void pin_process(int core)
{
	// Set thread affinity
	cpu_set_t cpuset;
	CPU_ZERO(&cpuset);
	CPU_SET(core, &cpuset);
    sched_setaffinity(0, sizeof(cpu_set_t), &cpuset);
}

void termination_handler(int signum)
{
    exit(0);
}

void create_clones()
{
	int i;
	struct sigaction new_action;

	// read the number of copies
	input = fopen(copies, "r");
	if(input != NULL) {
		fscanf(input, "%d", &nbClones);
		fclose(input);
	}else{
		nbClones = 1;
	}
	// allocate space for created processes
	pids =  (int*)      calloc(nbClones, sizeof(int));

	for (i=1; i<nbClones; i++) {
		pid = fork();
		pids[i] = pid;
		if (pid == 0) {
			pin_process(i);
			// Install signal handler
			new_action.sa_handler = termination_handler;
			sigemptyset (&new_action.sa_mask);
		    new_action.sa_flags = 0;
    		sigaction(SIGINT, &new_action, NULL);
			break;
		}
	}
}

void measure_init_()
{
#ifdef HAS_EMON_API
           EMONConfig ("emon_api_config_file", &emon_handle);

           EMONStart (&emon_handle);
	   emon_data_sum = EMON_DATA_NULL;
#endif
	// Pin the main process
//	pin_process(0);
	paused = 0;

	// initialize libraries
	evaluation_init();
	// Create a set of co-running copies of the codelet
	create_clones();

	return ;
}

void measure_start_()
{
	// Main process starts measurement
	if( pid != 0) {
		// Ensure that co-running processes are started by the kernel
		usleep(500);
		sched_yield();
		paused = 0;
		evaluation_start();
#ifdef HAS_EMON_API
		EMONRead (emon_handle, &emon_data_before);
#endif
#ifdef HAS_SNIPER_API
		SimRoiStart();
#endif
	}
	return ;
}

void measure_pause_emon () {
  if (paused) return;
#ifdef HAS_EMON_API
		EMONRead (emon_handle, &emon_data_after);
		EMONDataCalculate (emon_handle, emon_data_before, emon_data_after, &emon_data_result, "SUBTRACTION");
		EMONDataCalculate (emon_handle, emon_data_result, emon_data_sum, &emon_data_sum, "ADDITION");
#endif
}

void measure_pause_()
{
  if (paused) return;
	if( pid != 0) {
		evaluation_stop();
#ifdef HAS_EMON_API
		measure_pause_emon();
#endif
		paused = 1;
	}
	return ;
}

void measure_stop_()
{
	int i;

	if( pid == 0)
		pause();

	// Stop measurement
	evaluation_stop();
#ifdef HAS_EMON_API
	measure_pause_emon();
	//	EMONRead (emon_handle, &emon_data_after);
#endif

	// Stop childs
	for (i=1; i<nbClones; i++) {
		kill(pids[i], SIGINT);
	}

#ifdef HAS_EMON_API
	//	EMONDataCalculate (emon_handle, emon_data_before, emon_data_after, &emon_data_result, "SUBTRACTION");
#endif

	// Print results
    print_results();
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



	// Close measurement libraries
	evaluation_close();
#ifdef HAS_EMON_API
	EMONStop(&emon_handle);
#endif
#ifdef HAS_SNIPER_API
	SimRoiEnd();
#endif


	return ;
}

void increase_repetitions_(int *value)
{
	int repetitions;

	if (pid != 0) 
		return ;
	repetitions = 1;
//	printf("repe: %d\n", repetitions);
	*value = repetitions;
}

