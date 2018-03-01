CC=gcc
CFLAGS=-O3 -Wall -fPIC -I.
LDFLAGS=-ldl -rdynamic 
SEP_HEADER=/opt/intel/sep/include
SEP_INCLUDE=-I$(SEP_HEADER)
EMON_API_HEADER=/opt/intel/sep/sepdk/include
EMON_API_LIB=/opt/intel/sep/bin64
EMON_API_INCLUDE=-I$(EMON_API_HEADER)
SNIPER_HEADER=/nfs/site/proj/alac/software/Sniper/private/sniper/dcg_sniper-sniper-conf/include
SNIPER_INCLUDE=-I$(SNIPER_HEADER)
SEP_LIBS=/opt/intel/sep/bin64/libprog_api.so /opt/intel/sep/bin64/libabstract.so /opt/intel/sep/bin64/libsampling_utils.so

ifneq ("$(wildcard $(EMON_API_HEADER)/emon_api.h)","")
TARGETS=./libmeasure.so emon_api/libmeasure.so
else
TARGETS=./libmeasure.so
endif

ifneq ("$(wildcard $(SNIPER_HEADER)/sim_api.h)","")
TARGETS:=$(TARGETS) sniper/libmeasure.so
endif

all: $(TARGETS)

#libmeasure.a: measure.c
#	$(CC) $(CFLAGS) -c -g measure.c
#	ar -r libmeasure.a measure.o 
#	rm measure.o

measure.o: measure.c
	$(CC) $(CFLAGS) -c -g $^ -o $@

emon_api/emon_api_hook.o: emon_api/emon_api_hook.c
	$(CC) $(CFLAGS) $(EMON_API_INCLUDE) -DHAS_EMON_API -c -g $^ -o $@ -L/opt/intel/sep/bin64 -lprog_api

sniper/emon_api_hook.o: sniper/sniper_hook.c
	$(CC) $(CFLAGS) $(SNIPER_INCLUDE) -DHAS_SNIPER_API -c -g $^ -o $@

libmeasure.so.1: measure.o base/empty_hook.o
	ld -shared -soname $(notdir $@) -o $(dir $@)/libmeasure.so.1.0 $^
	ldconfig -n $(dir $@)

sniper/libmeasure.so.1: measure.o sniper/sniper_hook.o
	ld -shared -soname $(notdir $@) -o $(dir $@)/libmeasure.so.1.0 $^
	ldconfig -n $(dir $@)

emon_api/libmeasure.so.1: measure.o emon_api/emon_api_hook.o
	ld -shared -soname $(notdir $@) -o $(dir $@)/libmeasure.so.1.0 $^ -L$(EMON_API_LIB) -lprog_api
	ldconfig -n $(dir $@)


libmeasure.so: libmeasure.so.1
	ln -s $< $@


emon_api/libmeasure.so: emon_api/libmeasure.so.1
	ln -s $< $@

sniper/libmeasure.so: sniper/libmeasure.so.1
	ln -s $< $@

clean:
	rm -f *.o *.so */*.so *.so.* */*.so.*

distclean: clean
	rm -f *.a test

