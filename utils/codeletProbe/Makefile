CC=gcc
CFLAGS=-O3 -Wall
LDFLAGS=-ldl -rdynamic 
SEP_INCLUDE=-I/opt/intel/sep/include
EMON_INCLUDE=-I/opt/intel/sep/sepdk/include
SNIPER_INCLUDE=-I/nfs/site/proj/alac/software/Sniper/private/sniper/dcg_sniper-sniper-conf/include
SEP_LIBS=/opt/intel/sep/bin64/libprog_api.so /opt/intel/sep/bin64/libabstract.so /opt/intel/sep/bin64/libsampling_utils.so

ifneq ("$(wildcard /opt/intel/sep/sepdk/include/emon_api.h)","")
TARGETS=libmeasure.a libmeasure_emon_api.a
else
TARGETS=libmeasure.a
endif

ifneq ("$(wildcard /opt/intel/sep/sepdk/include/emon_api.h)","")
TARGETS:=$(TARGETS) libmeasure_sniper_api.a
endif

all: $(TARGETS)

libmeasure.a: measure.c
	$(CC) $(CFLAGS) -c -g measure.c
	ar -r libmeasure.a measure.o 
	rm measure.o


libmeasure_emon_api.a: measure.c
	$(CC) $(CFLAGS) $(EMON_INCLUDE) -DHAS_EMON_API -c -g measure.c
	ar -r libmeasure_emon_api.a measure.o 
	rm measure.o

libmeasure_sniper_api.a: measure.c
	$(CC) $(CFLAGS) $(SNIPER_INCLUDE) -DHAS_SNIPER_API -c -g measure.c
	ar -r libmeasure_sniper_api.a measure.o 
	rm measure.o

clean:
	rm -f *.o *.a

distclean: clean
	rm -f *.a test

