#include "hook.h"

#ifdef HAS_SNIPER_API
#include <sim_api.h>
#endif

void init_hook() {
}

void measure_start_hook() {
#ifdef HAS_SNIPER_API
		SimRoiStart();
#endif
}

void measure_pause_hook() {
}
void measure_print_data_hook() {
}

void measure_stop_hook() {
#ifdef HAS_SNIPER_API
	SimRoiEnd();
#endif
}
