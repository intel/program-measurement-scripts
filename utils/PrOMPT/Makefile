CC=icc
# According to https://github.com/mlpack/mlpack/issues/574, libbfd is an "internal only" library:
# checking PACKAGE and PACKAGE_VERSION is supposed to prevent to use it from other projects
CFLAGS=-O2 -DNDEBUG -fPIC -qopenmp -DPACKAGE -DPACKAGE_VERSION
LDFLAGS=-shared -qopenmp -lbfd -lpthread

OBJS=ompt_start_tool.o ompt_tool_addr2line.o ompt_tool.o

libprompt_$(CC).so: $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

# OMPT_SYNC_REGION_ENUM_LENGTH: set to number of values in ompt_sync_region_t: CF omp-tools.h (which is regularly updated)
ompt_tool.o: ompt_tool.c
	$(CC) -o $@ -c $< $(CFLAGS) -D OMPT_SYNC_REGION_ENUM_LENGTH=10 -D PROMPT_SYNC # -D PROMPT_WORK -D PROMPT_TASK

%.o: %.c
	$(CC) -o $@ -c $< $(CFLAGS)

clean:
	rm -rf libprompt_$(CC).so ${OBJS}
