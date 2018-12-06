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
#include "hook.h"


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

typedef struct {
	double start;
//	double stop;
	double ticks;
} TimerData;
TimerData *timer_data;
static int paused; // collection paused?



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
		if (fscanf(input, "%d", &nbClones) != 1) {
                  nbClones = 1;  // failed to read, set to default
                }
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
  init_hook();
	// Pin the main process
//	pin_process(0);
	paused = 0;

	// initialize libraries
	evaluation_init();
	// Create a set of co-running copies of the codelet
	create_clones();

measure_sec_spin_(1);


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
		measure_start_hook();
	}
	return ;
}

// pause only if not paused yet
void measure_may_pause_hook () {
  if (paused) return;
  measure_pause_hook();
}

void measure_pause_()
{
  if (paused) return;
	if( pid != 0) {
		evaluation_stop();
		measure_may_pause_hook();
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
	measure_may_pause_hook();

	// Stop childs
	for (i=1; i<nbClones; i++) {
		kill(pids[i], SIGINT);
	}


	// Print results
    print_results();
    measure_print_data_hook();


	// Close measurement libraries
	evaluation_close();
	measure_stop_hook();

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

void measure_sec_spin_(unsigned long sec) {
  unsigned long t1, t2;
  if (sec < 1)
    return; //too short
  rdtscll(t1);
  sleep(1);
  rdtscll(t2);
  unsigned long freq = t2 - t1;
  sec --;  // already used 1 sec

  unsigned long tt=sec * freq;
  unsigned long tick, tick1;
  rdtscll(tick);
  do {
    rdtscll(tick1);
  } while (tick1 - tick < tt);
}
