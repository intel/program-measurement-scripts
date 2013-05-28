CC=icc

all:
	${CC} load_procedure.c -c -O3 -Wall -Wextra -funroll-loops -cl-unsafe-math-optimizations
	${CC} -vec-report load_procedure.c -c -O3 -Wall -Wextra -funroll-loops -S -ftree-vectorizer-verbose=9 -cl-unsafe-math-optimizations -v
	${CC} *.o memloader.c -o Memloader -O3 -Wall -Wextra
	${CC} -o Ref_clock_detector ref_clock_detector.c -O3 -Wall -Wextra

clean:
	rm -f Memloader *.o
