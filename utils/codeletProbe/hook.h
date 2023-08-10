#ifndef _HOOK_H_
#define _HOOK_H_

void init_hook(void);
void measure_start_hook(void);
// this hook is called only when collection is not paused.and about to pause
void measure_pause_hook(void);
void measure_print_data_hook(void);
void measure_stop_hook(void);
#endif /* _HOOK_H_ */
