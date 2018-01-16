/*******************************************************************
********************************************************************
*
*	Intel Corporation, C 2008
*	author: Luis Fernando Recalde (luis.f.recalde@intel.com)
*
*	setmsr.c is a program used to read MSR values, write MSR values,
*	and toggle bits in an MSR.
*
*	version 1.0: Jan. 24, '08
*	three functionalities available, few error checks
*
*********************************************************************
*********************************************************************/

#include <inttypes.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <limits.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/sysinfo.h>

int64_t read_msr(char * msrDevPName, off_t msrNum, int64_t msrValue);
int64_t write_msr(char * msrDevPName, off_t msrNum, int64_t msrValue);

int main(int argc, const char *argv[], const char *envv[])
{
        int cpuNum;  /* Do it for all CPUs */
        int i;

        off_t msrNum;
        char msrDevPName[PATH_MAX];
        int64_t msrValue = 0;

        cpuNum = get_nprocs();

        if (argc < 2 || argc > 5) {
                printf("\nUSAGE:\t\t\t\tMSR v1.0\n");
                printf("./setmsr 0x1A0\t\t\t:read MSR value from all CPUs\n");
                printf("./setmsr 0x1A0 0x0123456789\t:write MSR value on all CPUs\n");
                printf("./setmsr 0x1A0 19 23\t\t:set MSR 0x1a0 to value 0x19 only on CPU 23\n\n");
                return 0;
        }

        char *endptr;
        msrNum = strtol(argv[1], &endptr, 16);

        if (argc == 2) {
		// read msr value from all CPUs
                // usage:  ./msr.exe 0x1A0
                for (i = 0; i < cpuNum; i++) {
                        snprintf(msrDevPName,sizeof(msrDevPName)-1,"/dev/cpu/%d/msr",i);
			msrValue = read_msr(msrDevPName, msrNum, msrValue);
                        // printf("CPU %d: MSR 0x%0X = 0x%0" PRIX64 "\n",i,msrNum,msrValue);
                        printf("CPU %d: MSR 0x%0" PRIXMAX " = 0x%0" PRIX64 "\n",i,msrNum,msrValue);
                }
        }
        else if (argc == 3) {
		// write msr value to all CPUs
                // usage:  ./msr.exe 0x1A0 0x0123456789
	        msrValue = strtoll(argv[2], &endptr, 16);

                for (i = 0; i < cpuNum; i++) {
	                snprintf(msrDevPName,sizeof(msrDevPName)-1,"/dev/cpu/%d/msr",i);
			msrValue = write_msr(msrDevPName, msrNum, msrValue);
	                printf("CPU %d: MSR 0x%0" PRIXMAX " = 0x%0" PRIX64 "\n",i,msrNum,msrValue);
		}
        }
        else if (argc == 4) {
		char *endptr;
		int cpu = atoi(argv[3]);
	        msrValue = strtoll(argv[2], NULL,  16);
	        snprintf(msrDevPName,sizeof(msrDevPName)-1,"/dev/cpu/%d/msr",cpu);
		msrValue = write_msr(msrDevPName, msrNum, msrValue);
		}
        else {
		// set msr bit to 0 or 1 on all CPUs
                // usage:  ./msr.exe 0x1A0 13 1
		int bit = atoi(argv[2]);
		int bitValue = atoi(argv[3]);

		if (bit < 0 || bit > 63) {
			printf("ERROR: bit must be between 0 and 63 only!\n");
                        return -1;
		}
                for (i = 0; i < cpuNum; i++) {
                        snprintf(msrDevPName,sizeof(msrDevPName)-1,"/dev/cpu/%d/msr",i);
			msrValue = read_msr(msrDevPName, msrNum, msrValue);
			if (bitValue == 1) {
		                /* change bit to 1 */
		                msrValue |= (1<<bit);
				msrValue = write_msr(msrDevPName, msrNum, msrValue);

			}
			else if (bitValue == 0) {
                                /* change bit to 0 */
                                msrValue &= ~(1<<bit);
				msrValue = write_msr(msrDevPName, msrNum, msrValue);
			}
			else {
				printf("ERROR: bit must be set to 0 or 1 only!\n");
				return -1;
			}
                        //printf("CPU %d: MSR 0x%0X = 0x%0llX\n",i,msrNum,msrValue);
                        printf("CPU %d: MSR 0x%0" PRIXMAX " = 0x%0" PRIX64 "\n",i,msrNum,msrValue);
                }
        }
        return 0;
}


int64_t read_msr(char * msrDevPName, off_t msrNum, int64_t msrValue) {

        int fh;
        off_t fpos;
        ssize_t countBy;

	if ((fh= open(msrDevPName,O_RDWR))<0) {
		fprintf(stderr,"open(\"%s\",...) failed\n",msrDevPName);
		exit(__LINE__);
	}
//	else
//		fprintf(stderr,"\nopen(\"%s\",...) successful\n",msrDevPName);
        if ((fpos= lseek(fh,msrNum,SEEK_SET)),0) {
                perror("lseek() failed"); exit(__LINE__);
        }
//	else
//		fprintf(stderr,"lseek(%d==0x%0X) successful\n",msrNum,msrNum);
        if ((countBy= read(fh,&msrValue,sizeof(msrValue)))<0) {
                perror("read() failed");
                exit(__LINE__);
        }
        else if (countBy!=sizeof(msrValue)) {
                fprintf(stderr,"attempt to read(8-bytes) got %zd bytes\n",countBy);
                exit(__LINE__);
        }
	return msrValue;
}


int64_t write_msr(char * msrDevPName, off_t msrNum, int64_t msrValue) {

        int fh;
        off_t fpos;
        ssize_t countBy;

	if ((fh= open(msrDevPName,O_RDWR))<0) {
                fprintf(stderr,"open(\"%s\",...) failed\n",msrDevPName);
                exit(__LINE__);
        }
        if ((fpos= lseek(fh,msrNum,SEEK_SET)),0) {
                perror("lseek() failed"); exit(__LINE__);
        }
        if ((countBy= write(fh,&msrValue,sizeof(msrValue)))<0) {
                perror("write() failed");
                exit(__LINE__);
        }
        else if (countBy!=sizeof(msrValue)) {
                fprintf(stderr,"attempt to write(8-bytes) got %zd bytes\n",countBy);
                exit(__LINE__);
        }
        if ((countBy= read(fh,&msrValue,sizeof(msrValue)))<0) {
                perror("read() failed");
                exit(__LINE__);
        }
        else if (countBy!=sizeof(msrValue)) {
                fprintf(stderr,"attempt to read(8-bytes) got %zd bytes\n",countBy);
                exit(__LINE__);
        }
	return msrValue;
}

