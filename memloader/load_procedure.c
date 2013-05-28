#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "load_procedure.h"
#include "rdtsc.h"


double load (char* array, unsigned int array_size, double delay, unsigned long long* total_iters, unsigned long long* total_batches, int silent, char* not_interrupted, unsigned int nb_doubles_per_batch, unsigned long long reference_clock)
{
	(void) silent;

	unsigned int aim = delay;

	double* d_array = (double*) array;

	unsigned int d_array_size = array_size / sizeof (double);
	double* address_not_to_exceed = d_array + d_array_size;

	double res = 0;
	unsigned long long ref_time_stamp, tmp_time_stamp;
	const int i_max = nb_doubles_per_batch;

	int monotonic_changes_in_a_row = 0;

	
	ref_time_stamp = rdtsc ();
	
	while (*not_interrupted)
	{
		double* tmp_d_array = d_array;
		double local_average;

		unsigned long long total_batches_before = *total_batches;
		unsigned long long total_batches_after;
		unsigned long long time_ref = rdtsc ();
		unsigned long long time_tmp;

		const unsigned int passable_treshold = (aim - RDTSC_INDUCED_UNCERTAINTY) * (aim > RDTSC_INDUCED_UNCERTAINTY);

		while (tmp_d_array < address_not_to_exceed && *not_interrupted)
		{
			int i;
			unsigned long long diff;

			for (i = 0; i < i_max; i++)
			{
				res += (tmp_d_array[i]);
				(*total_iters)++;
			}

			(*total_batches)++;

			tmp_d_array += i_max;

			while ( (diff = ((tmp_time_stamp = rdtsc ()) - ref_time_stamp)) < passable_treshold);
			ref_time_stamp = tmp_time_stamp;

			if (diff < aim)
			{
				res = (res + 1) / res;
			}
		}

		time_tmp = rdtsc ();
		total_batches_after = *total_batches;
		local_average = (time_tmp - time_ref) / ((double)total_batches_after - total_batches_before);

		if (!silent)
		{
			double actual_bw = (   reference_clock * (nb_doubles_per_batch * sizeof (double))  ) / local_average;
			printf ("Local BW: %.2lf GB/s\t(%.2lf MB/s)\tLocal ACBB: %.2lf. [aim was %d]\n", actual_bw / (1024 * 1024 * 1024), actual_bw / (1024 * 1024), local_average, aim);
		}


		if (local_average >= (delay - NO_CHANGE_TOLERANCE) && local_average <= (delay + NO_CHANGE_TOLERANCE));
		else if (local_average > delay)
		{
			if (aim > 0)
			{
				if (monotonic_changes_in_a_row > 0) monotonic_changes_in_a_row = 0;
				else if (monotonic_changes_in_a_row > (-1 * MAX_MONOTONIC_CHANGES_IN_A_ROW)) monotonic_changes_in_a_row--;
				aim -= 1 << (-1 * (monotonic_changes_in_a_row / PROGRESSION_RAMP_UP));
				//printf ("Minus: %d.\n", 1 << (-1 * monotonic_changes_in_a_row));
				aim = aim * ((signed)aim > 0);
			}
		}
		else
		{
			if (aim < 1000000)
			{
				if (monotonic_changes_in_a_row < 0) monotonic_changes_in_a_row = 0;
				else if (monotonic_changes_in_a_row < MAX_MONOTONIC_CHANGES_IN_A_ROW) monotonic_changes_in_a_row++;
				aim += 1 << (monotonic_changes_in_a_row / PROGRESSION_RAMP_UP);
				//printf ("Plus: %d.\n", 1 << monotonic_changes_in_a_row);
			}
		}
	}

	return res;
}
