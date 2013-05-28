#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "load_procedure.h"
#include "rdtsc.h"

char not_interrupted = 1;

void handler (int a)
{
	(void) a;
	not_interrupted = 0;
}

int main (int argc, char** argv)
{
	unsigned int array_size = 40960000;
	char* array;
	double delay;
	unsigned int nb_doubles_per_batch = 80;
	int silent = 1;
	unsigned int bw;
	unsigned long long reference_clock = 3300000000;

	unsigned long long total_iters = 0, total_batches = 0;
	unsigned long long ref_time_stamp, after_time_stamp;

	double average_cycles, average_cycles_between_batches;
	double actual_bw;

	if (argc < 2)
	{
		printf ("%s <bandwidth in MB/s> [reference clock (in Hz) [silent (0/1) [array size (in bytes) [doubles per batch]]]]\n", argv[0]);
		return -1;
	}

	bw = atoi (argv[1]);
	printf ("Target bandwidth: %u MB/s (%.2lf GB/s).\n", bw, (double)bw/1024);

	if (argc >= 3)
	{
		reference_clock = atol (argv[2]);
	}
	printf ("Reference clock: %llu.\n", reference_clock);

	if (argc >= 4)
	{
		silent = atoi (argv[3]);
	}
	printf ("Silent mode: %d.\n", silent);

	if (argc >= 5)
	{
		array_size = atoi (argv[4]);
		if ( (array_size <= 0) || (array_size % sizeof (double) != 0) )
		{
			printf ("Error: the array size needs to be a strictly positive multiple of %lu (%d).\n", sizeof (double), array_size);
			return -1;
		}
	}
	printf ("Array size: %u bytes.\n", array_size); 

	if (argc >= 6)
	{
		nb_doubles_per_batch = atoi (argv[5]);
	}
	printf ("Number of doubles per batch: %u.\n", nb_doubles_per_batch);


	delay = reference_clock / (   ((double)bw * 1024 * 1024) / (nb_doubles_per_batch * sizeof(double))   );


	printf ("Computed delay: %.2lf.\n", delay);


	array = malloc (array_size);
	if (array == NULL)
	{
		printf ("Could not allocate an array of size %u.\n", array_size);
		return -1;
	}
	memset (array, 0, array_size);


	signal (SIGINT, handler);


	printf ("Memloader: Aiming to load %u doubles every % .2lf reference cycles, from an array of %u bytes.\n", nb_doubles_per_batch, delay, array_size);


	// CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL
	ref_time_stamp = rdtsc ();
	load (array, array_size, delay, &total_iters, &total_batches, silent, &not_interrupted, nb_doubles_per_batch, reference_clock);
	after_time_stamp = rdtsc ();
	// CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL CALL


	average_cycles = (after_time_stamp - ref_time_stamp) / (double)total_iters;
	average_cycles_between_batches = (after_time_stamp - ref_time_stamp) / (double)total_batches;
	actual_bw = (reference_clock / average_cycles_between_batches) * (nb_doubles_per_batch * sizeof (double));

	printf ("Global average for loading a double:\t%.2lf.\n", average_cycles);
	printf ("Global average between %.2luB batches:\t%.2lf.\n", nb_doubles_per_batch * sizeof (double), average_cycles_between_batches);
	printf ("Global average bandwidth:\t%.2lf GB/s,\t%.2lf MB/s,\t%.2lf KB/s,\t%.2lf B/s.\n", actual_bw / (1024 * 1024 * 1024), actual_bw / (1024 * 1024), actual_bw / (1024), actual_bw);


	free (array);
	return 0;
}
