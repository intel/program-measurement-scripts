#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <glob.h>
#include <errno.h>
#include <assert.h>
#include <unistd.h>


#define DISABLE_FILE_STATE0 "/sys/devices/system/cpu/cpu%s/cpuidle/state0/disable"
#define IDLE_FILE_PATTERN "/sys/devices/system/cpu/cpu%s/cpuidle/state[0-5]/disable"

// Print usage and quit
void usage(char* me) {
  fprintf(stderr, "Usage: %s (<cpu#|all>) (ON|OFF) \n", me);
  exit(-1);
}

int main(int argc, char** argv) { 
   char* command; 
   char* command_value;
   char* cpu_glob;
   glob_t results;
   int flags;
   unsigned int i;

   if (argc == 3) {
     if (strcmp(argv[2], "ON") == 0) {
       command_value = "0";   // for not disabling
     } else if  (strcmp(argv[2], "OFF") == 0) {
       command_value = "1";   // for disabling
     } else 
	usage(argv[0]);

     // fall through here for ON and OFF (usage will quit)
     command = argv[2];
     if (strcmp(argv[1], "all") == 0) {
	cpu_glob="*";
     } else {
       int ret;
       char* disable_file;
       ret = asprintf(&disable_file, DISABLE_FILE_STATE0, argv[1]);
       assert (ret > 0);
       if (access (disable_file, F_OK) == -1) {
         fprintf (stderr, "Bad CPU number: %s\n", argv[1]);
	 exit (-1);
       } 
       free(disable_file);
       // after check, we can use argv[1] 
       cpu_glob=argv[1];
     }
   }  else
	usage(argv[0]);
   printf ("set-cpuidle: %s with value %s for CPU %s\n", command, command_value, cpu_glob); 
   flags = 0;
   char* glob_str;
   int ret = asprintf(&glob_str, IDLE_FILE_PATTERN, cpu_glob);
   assert (ret > 0);

   ret = glob(glob_str, flags, NULL, & results);
   if (ret != 0)  {
     fprintf (stderr, "Failed to access cpuidle files: %s\n", glob_str);
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
   free(glob_str);
}

