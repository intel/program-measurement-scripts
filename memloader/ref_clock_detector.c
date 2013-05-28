#include <stdio.h>
#include <time.h>
#include <sys/time.h>

#include "rdtsc.h"

int main (void)
{
	unsigned long long before, after;
        struct timeval tim;
	double t1, t2;

	printf ("Reference clock detection...\n");

	gettimeofday(&tim, NULL);
	t1=tim.tv_sec+(tim.tv_usec/1000000.0);
	t2=t1;


	before = rdtsc ();
	
	while (t2-t1 < 1)
	{
		gettimeofday(&tim, NULL);
		t2=tim.tv_sec+(tim.tv_usec/1000000.0);
	}

	after = rdtsc ();


	printf ("Ref_clock: %lu Hz/s.\n", after - before);

	return 0;

}
