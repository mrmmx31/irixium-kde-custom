/* SPDX-License-Identifier: MIT
 * Scoped to the Kate launcher. Registers only its embedded Git icon resource.
 * No Qt link dependency: use the Qt already loaded by the application.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdbool.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include "resources.h"

typedef bool (*register_fn)(int, const unsigned char *, const unsigned char *, const unsigned char *);
static register_fn original;
static pthread_once_t once = PTHREAD_ONCE_INIT;
static void install_resources(void)
{
    original = (register_fn)dlsym(RTLD_NEXT, "_Z21qRegisterResourceDataiPKhS0_S0_");
    if (original)
        original(2, qt_resource_struct, qt_resource_name, qt_resource_data);
}

bool irix_register(int version, const unsigned char *tree,
                   const unsigned char *names, const unsigned char *data)
    __asm__("_Z21qRegisterResourceDataiPKhS0_S0_");
bool irix_register(int version, const unsigned char *tree,
                   const unsigned char *names, const unsigned char *data)
{
    pthread_once(&once, install_resources);
    return original ? original(version, tree, names, data) : false;
}
/* Also support processes without any statically compiled resource initializer. */
__attribute__((constructor)) static void initialize(void)
{
    pthread_once(&once, install_resources);
    /* Do not pass this overlay to programs launched by the GUI. Keep any
       pre-existing user preload entries, which our launcher appends after it. */
    Dl_info self;
    const char *preload = getenv("LD_PRELOAD");
    if (preload && dladdr((void *)initialize, &self) && self.dli_fname) {
        size_t length = strlen(self.dli_fname);
        if (!strncmp(preload, self.dli_fname, length)) {
            if (preload[length] == ':') setenv("LD_PRELOAD", preload + length + 1, 1);
            else if (!preload[length]) unsetenv("LD_PRELOAD");
        }
    }
}
