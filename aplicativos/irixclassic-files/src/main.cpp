// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
// New application entry point. Does NOT register FileManager1 or attach to Dolphin.
#include "core.h"
#include "classicshell.h"
#include "dolphinmainwindow.h"
#include "dolphin_generalsettings.h"
#include <KAboutData>
#include <KCrash>
#include <KIconTheme>
#include <KLocalizedString>
#include <QApplication>
#include <QCommandLineParser>
#include <QDir>
#include <QFileInfo>
#include <QIcon>
#include <QMessageBox>
#include <QStyleFactory>
#include <QTextStream>
#include <unistd.h>
#include <exception>
#include <cstdio>
int main(int argc,char **argv)
{
    if (::geteuid()==0) { fprintf(stderr,"Run IrixClassic Files as a regular user, never with sudo.\n"); return 2; }
    KIconTheme::initTheme();
    QApplication app(argc,argv);
    KAboutData about(QString::fromLatin1(Irix::AppName),QStringLiteral("IrixClassic Files"),QString::fromLatin1(Irix::Version),
                     QStringLiteral("Experimental classic interface based on Dolphin 25.04.3"),KAboutLicense::GPL_V2,
                     QStringLiteral("Dolphin developers; classic integration © 2026 mrmmx31"));
    about.setDesktopFileName(QString::fromLatin1(Irix::DesktopId));
    about.setHomepage(QStringLiteral("https://github.com/mrmmx31/irixium-kde-custom"));
    about.addAuthor(QStringLiteral("mrmmx31"),QStringLiteral("Classic interface and integration"));
    about.addCredit(QStringLiteral("Dolphin contributors"),QStringLiteral("File manager engine; upstream credits retained in source and documentation."));
    KAboutData::setApplicationData(about);
    KLocalizedString::setApplicationDomain("dolphin"); // Retain upstream translations.
    KCrash::initialize();
    app.setWindowIcon(QIcon::fromTheme(QStringLiteral("system-file-manager")));
    QCommandLineParser p; about.setupCommandLine(&p);
    p.addOption({QStringLiteral("new-window"),QStringLiteral("Open a separate IrixClassic Files window.")});
    p.addOption({QStringLiteral("select"),QStringLiteral("Select the supplied items instead of opening them.")});
    p.addOption({QStringLiteral("split"),QStringLiteral("Open the native Dolphin split view.")});
    p.addPositionalArgument(QStringLiteral("locations"),QStringLiteral("Directories or URLs to browse."),QStringLiteral("[locations…]"));
    p.process(app); about.processCommandLine(&p);
    // The generated settings are patched to irixclassic-filesrc in this build.
    auto *settings=GeneralSettings::self();
    settings->setRememberOpenedTabs(false); // No Dolphin session restoration or daemon discovery.
    if (settings->homeUrl().isEmpty()) settings->setHomeUrl(QDir::homePath());
    QList<QUrl> urls;
    for(const auto &arg:p.positionalArguments()) { const auto u=Irix::locationFromText(arg,QUrl::fromLocalFile(QDir::currentPath())); if(u.isValid()&&!u.isEmpty()) urls.append(u); }
    if(urls.isEmpty()) urls.append(QUrl::fromLocalFile(QDir::homePath()));
    const bool split=p.isSet(QStringLiteral("split")); if(split&&urls.size()<2) urls.append(urls.last());
    try {
        auto *window=new DolphinMainWindow;
        if(p.isSet(QStringLiteral("select"))) window->openFiles(urls,split); else window->openDirectories(urls,split);
        new ClassicShell(window);
        window->setSessionAutoSaveEnabled(false); window->resize(900,780); window->show();
        return app.exec();
    } catch(const std::exception &e) { QMessageBox::critical(nullptr,QStringLiteral("IrixClassic Files"),QString::fromUtf8(e.what())); return 1; }
}
