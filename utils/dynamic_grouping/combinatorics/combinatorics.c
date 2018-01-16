#include <stdio.h>
#include <stdlib.h>

void generate_dynamic_groups (int nb_of_groups, int* cur_groups, int rank);

int main (int argc, char** argv)
{
	int nb_of_groups = 3;
	int cur_groups[256];

	if (argc != 2) return -1;

	nb_of_groups = atoi (argv[1]);

	generate_dynamic_groups (nb_of_groups, cur_groups, 0);

	return 0;
}

void generate_dynamic_groups (int nb_of_groups, int* cur_groups, int rank)
{
	int i;	

	for (i = 0; i < 2; i++)
	{
		cur_groups[rank] = i;
		if (rank != (nb_of_groups - 1)) generate_dynamic_groups (nb_of_groups, cur_groups, rank + 1);
		else
		{
			int j;
			int printed_something = 0;

			for (j = 0; j < nb_of_groups; j++)
			{
				if (cur_groups[j] != 0)
				{
					printf( "%d", j + 1);
					if (j != (nb_of_groups - 1)) printf (" ");
					printed_something = 1;
				}
			}
			if (printed_something) printf ("\n");
		}
	}
}
