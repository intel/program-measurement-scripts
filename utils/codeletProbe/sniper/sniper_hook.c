#include "hook.h"

#ifdef HAS_SNIPER_API
#include <sim_api.h>
#endif

void init_hook(void) {
}

void measure_start_hook(void) {
#ifdef HAS_SNIPER_API
		SimRoiStart();
#endif
}

void measure_pause_hook(void) {
}
void measure_print_data_hook(void) {
}

void measure_stop_hook(void) {
#ifdef HAS_SNIPER_API
	SimRoiEnd();
#endif
}
