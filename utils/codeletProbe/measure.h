#ifndef _MEASURE_H_
#define _MEASURE_H_

#if defined(__cplusplus)
extern "C" {
#endif
  
void measure_init_(void);
void measure_start_(void);
void measure_pause_(void);
void measure_stop_(void);
void measure_sec_spin_(unsigned long sec);  

#if defined(__cplusplus)
}
#endif

#endif /* _MEASURE_H_ */
