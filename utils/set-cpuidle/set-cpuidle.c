#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <glob.h>
#include <errno.h>


#define IDLE_FILE_PATTERN "/sys/devices/system/cpu/cpu?/cpuidle/state[0-5]/disable"

// Print usage and quit
void usage(char* me) {
  fprintf(stderr, "Usage: %s (ON|OFF)\n", me);
  exit(-1);
}

int main(int argc, char** argv) { 
   char* command; 
   char* command_value;
   glob_t results;
   int flags;
   unsigned int i;

   if (argc == 2) {
     if (strcmp(argv[1], "ON") == 0) {
       command_value = "0";   // for not disabling
     } else if  (strcmp(argv[1], "OFF") == 0) {
       command_value = "1";   // for disabling
     } else 
	usage(argv[0]);
     // fall through here for ON and OFF (usage will quit)
     command = argv[1];
   }  else
	usage(argv[0]);
   printf ("set-cpuidle: %s with value %s\n", command, command_value); 
   flags = 0;
   int ret = glob(IDLE_FILE_PATTERN, flags, NULL, & results);
   if (ret != 0)  {
     fprintf (stderr, "Failed to access cpuidle files: %s\n", IDLE_FILE_PATTERN);
     exit(-1);
   }
   // ready to set the value

   for (i = 0; i < results.gl_pathc; i++) {
        char* filename=results.gl_pathv[i];
#ifdef DEBUG
	printf("Writing %s to %s\n", command_value, filename);
#endif
        FILE* fp=fopen(filename, "w");
        if (fp != NULL) {
          fprintf(fp, "%s\n", command_value);
          fclose(fp);
        } else {
          fprintf(stderr, "Error writing to %s\n", filename);
        }
   }
   globfree(& results);
}

