#include "platform.h"
#include "devices.h"
#include "storage.h"
#include "app.h"
int main(void) {
    platform_init();
    settings_defaults(&settings);
    devices_init();
    storage_init();
    app_init();
    for (;;)
        app_step();
}
