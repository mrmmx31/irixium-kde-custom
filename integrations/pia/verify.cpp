// SPDX-License-Identifier: MIT
// Optional diagnostic, compiled against the target Qt. Not required to install.
#include <QtCore/QCoreApplication>
#include <QtCore/QFile>
#include <QtGui/QImage>
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    if (argc < 2) return 1;
    if (argc > 2 && !dlopen(argv[2], RTLD_NOW | RTLD_GLOBAL)) {
        fprintf(stderr, "%s\n", dlerror()); return 2;
    }
    const char *sets[] = {"dark-no-outline-margins", "light-no-outline-margins",
                         "colored-no-outline-margins", "classic-margins"};
    const char *states[] = {"alert", "down", "connected", "disconnecting", "connecting", "snoozed"};
    int count = 0;
    for (auto set : sets) for (auto state : states) {
        QFile actual(QString(":/img/tray/square-%1-%2.png").arg(set, state));
        QFile expected(QString("%1/%2.png").arg(argv[1], state));
        if (!actual.open(QIODevice::ReadOnly) || !expected.open(QIODevice::ReadOnly)) return 3;
        auto data = actual.readAll();
        if (data != expected.readAll() || QImage::fromData(data).isNull()) return 4;
        count++;
    }
    const char *preload = getenv("LD_PRELOAD");
    if (preload && QString::fromLocal8Bit(preload).contains("libirix-pia-tray.so")) return 5;
    printf("%d resource paths verified; overlay removed from child-process environment.\n", count);
    return 0;
}
