#ifndef LOAD_PROCEDURE_H
#define LOAD_PROCEDURE_H

#define NB_BYTES_PER_BATCH 4096

double load (char* array, unsigned int array_size, double delay, unsigned long long* total_iters, unsigned long long* total_batches, int silent, char* not_interrupted, unsigned int nb_doubles_per_batch, unsigned long long reference_clock);

#define RDTSC_INDUCED_UNCERTAINTY 17

#define MAX_MONOTONIC_CHANGES_IN_A_ROW 24
#define PROGRESSION_RAMP_UP 4

#define NO_CHANGE_TOLERANCE 1


#endif
