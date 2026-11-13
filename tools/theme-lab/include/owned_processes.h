/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_OWNED_PROCESSES_H
#define TL_OWNED_PROCESSES_H
#include <stddef.h>
#include <sys/types.h>
/* Only unreaped direct children, each created as leader of its own group.
 * Never pass a historical PID or reap a leader before this call. */
int tl_owned_processes_shutdown(const pid_t *leaders, size_t count);
/* Nonblocking completion: 0 running, 1 reaped, -1 error. Kill remaining owned
 * group members while the exited leader still prevents PID reuse. */
int tl_owned_process_poll(pid_t leader, int *status);
#endif
