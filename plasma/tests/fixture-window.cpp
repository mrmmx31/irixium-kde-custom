/* SPDX-License-Identifier: GPL-2.0-or-later */
// Disposable test window for the private KWin/Xvfb task-manager fixture.
// Pass --desktop-id equal to the generated .desktop filename without its
// .desktop suffix, e.g. org.irixclassic.fixture.editor. No real app is opened.
// Use --window-title; QApplication reserves and consumes the standard --title.
#include <QApplication>
#include <QCommandLineOption>
#include <QCommandLineParser>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QRegularExpression>
#include <QTextStream>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    QCommandLineParser parser;
    parser.setApplicationDescription(QStringLiteral("Disposable IRIX Classic task test window; exits within 60 seconds."));
    parser.addHelpOption();
    const QCommandLineOption desktopIdOption(
        QStringLiteral("desktop-id"),
        QStringLiteral("Generated desktop filename without the .desktop suffix."),
        QStringLiteral("id"));
    const QCommandLineOption titleOption(
        QStringLiteral("window-title"),
        QStringLiteral("Stable window title for the task model."),
        QStringLiteral("title"), QStringLiteral("IRIX Classic fixture"));
    parser.addOption(desktopIdOption);
    parser.addOption(titleOption);
    parser.process(app);

    const QString desktopId = parser.value(desktopIdOption);
    const QString title = parser.value(titleOption);
    const QRegularExpression validId(QStringLiteral("^[A-Za-z0-9][A-Za-z0-9_.-]*$"));
    if (!parser.isSet(desktopIdOption) || !validId.match(desktopId).hasMatch()
        || desktopId.endsWith(QStringLiteral(".desktop")) || title.isEmpty()) {
        QTextStream(stderr) << "--desktop-id requires an identifier without .desktop; --window-title cannot be empty.\n";
        return 2;
    }
    QApplication::setApplicationName(desktopId);
    QApplication::setDesktopFileName(desktopId);

    QWidget window;
    window.setObjectName(QStringLiteral("irixClassicFixtureWindow"));
    window.setWindowTitle(title);
    window.setFixedSize(320, 180);
    auto *layout = new QVBoxLayout(&window);
    auto *heading = new QLabel(title, &window);
    heading->setObjectName(QStringLiteral("fixtureTitle"));
    layout->addWidget(heading);
    auto *identifier = new QLabel(desktopId, &window);
    identifier->setObjectName(QStringLiteral("fixtureDesktopId"));
    identifier->setWordWrap(true);
    layout->addWidget(identifier);
    layout->addStretch();

    // The lifetime guard belongs only to this standalone test executable.
    QTimer::singleShot(60000, &app, &QCoreApplication::quit);
    window.show();
    QTimer::singleShot(0, &window, [&window, desktopId, title]() {
        const QJsonObject ready {
            {QStringLiteral("ready"), true},
            {QStringLiteral("win_id"), QStringLiteral("0x") + QString::number(qulonglong(window.winId()), 16)},
            {QStringLiteral("pid"), QCoreApplication::applicationPid()},
            {QStringLiteral("desktop_id"), desktopId},
            {QStringLiteral("title"), title}
        };
        QTextStream output(stdout);
        output << QJsonDocument(ready).toJson(QJsonDocument::Compact) << '\n';
        output.flush();
    });
    return app.exec();
}
