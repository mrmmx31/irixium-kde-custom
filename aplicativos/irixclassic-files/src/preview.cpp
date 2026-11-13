// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#include "preview.h"
#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QPlainTextEdit>
#include <QProcess>
#include <QProcessEnvironment>
#include <QPixmap>
#include <QScrollArea>
#include <QStackedWidget>
#include <QTimer>
#include <QVBoxLayout>

ContentViewer::ContentViewer(QWidget *parent) : QWidget(parent)
{
    setObjectName(QStringLiteral("IrixContentViewer"));
    setAccessibleName(tr("Content Viewer: read-only preview"));
    auto *layout = new QVBoxLayout(this); layout->setContentsMargins(0,0,0,0);
    m_stack = new QStackedWidget(this); layout->addWidget(m_stack);
    m_message = new QLabel(tr("Select one file to preview its contents."), this);
    m_message->setTextFormat(Qt::PlainText); m_message->setWordWrap(true); m_message->setAlignment(Qt::AlignCenter);
    m_stack->addWidget(m_message);
    m_text = new QPlainTextEdit(this); m_text->setReadOnly(true); m_text->setLineWrapMode(QPlainTextEdit::NoWrap);
    m_stack->addWidget(m_text);
    auto *scroll = new QScrollArea(this); scroll->setWidgetResizable(true);
    m_image = new QLabel; m_image->setAlignment(Qt::AlignCenter); scroll->setWidget(m_image);
    auto pal = m_image->palette(); pal.setColor(QPalette::Window, QColor("#5f5f5f"));
    m_image->setPalette(pal); m_image->setAutoFillBackground(true);
    scroll->setPalette(pal); scroll->viewport()->setPalette(pal); m_stack->addWidget(scroll);
    m_timeout = new QTimer(this); m_timeout->setSingleShot(true);
    connect(m_timeout, &QTimer::timeout, this, [this] { clear(tr("Preview exceeded the 3-second limit.")); });
    setMinimumHeight(72);
}
ContentViewer::~ContentViewer() { stop(); }
void ContentViewer::stop()
{
    ++m_request; m_timeout->stop();
    if (m_process) {
        auto *old = m_process; m_process = nullptr;
        old->disconnect(this); old->kill();
        if (old->state() == QProcess::NotRunning) old->deleteLater();
        else connect(old, qOverload<int,QProcess::ExitStatus>(&QProcess::finished), old, &QObject::deleteLater);
    }
}
void ContentViewer::clear(const QString &message)
{
    stop(); m_kind = QStringLiteral("empty"); m_image->clear(); m_text->clear();
    m_message->setText(message.isEmpty() ? tr("Select one file to preview its contents.") : message);
    m_stack->setCurrentIndex(0); Q_EMIT previewReady(m_kind);
}
void ContentViewer::showUrl(const QUrl &url)
{
    clear();
    if (url.isEmpty()) return;
    if (!url.isLocalFile()) { clear(tr("Remote preview is disabled in this version. No download was started.")); return; }
    const auto helper = QCoreApplication::applicationDirPath() + QStringLiteral("/irixclassic-preview-worker");
    if (!QFileInfo(helper).isExecutable()) { clear(tr("Preview helper not found beside the application.")); return; }
    m_message->setText(tr("Loading preview…"));
    const auto ticket = m_request;
    auto *p = new QProcess(this); m_process = p;
    // The decoder is a separate, cancellable process; never a shell command.
    p->setProgram(helper); p->setArguments({url.toLocalFile()});
    auto env = QProcessEnvironment::systemEnvironment(); env.insert(QStringLiteral("QT_QPA_PLATFORM"), QStringLiteral("offscreen"));
    p->setProcessEnvironment(env); p->setProcessChannelMode(QProcess::SeparateChannels);
    connect(p, &QProcess::readyReadStandardOutput, this, [this,p,ticket] {
        if (ticket != m_request) return;
        if (p->bytesAvailable() > 12*1024*1024) clear(tr("Preview response is too large."));
    });
    connect(p, &QProcess::readyReadStandardError, this, [p] { p->readAllStandardError(); });
    connect(p, &QProcess::errorOccurred, this, [this,ticket](QProcess::ProcessError) {
        if (ticket == m_request) clear(tr("Preview helper could not complete the request."));
    });
    connect(p, qOverload<int,QProcess::ExitStatus>(&QProcess::finished), this, [this,p,ticket](int code,QProcess::ExitStatus status) {
        if (ticket != m_request) return;
        m_timeout->stop(); m_process = nullptr;
        const auto output = p->readAllStandardOutput(); p->deleteLater();
        if (status != QProcess::NormalExit || code != 0 || output.size() > 12*1024*1024) { clear(tr("Unsupported, damaged or oversized file.")); return; }
        displayResult(output);
    });
    m_timeout->start(3000); p->start();
}
void ContentViewer::displayResult(const QByteArray &data)
{
    const auto doc = QJsonDocument::fromJson(data); const auto o = doc.object();
    m_kind = o.value("kind").toString();
    if (m_kind == QStringLiteral("text")) {
        m_text->setPlainText(o.value("text").toString()); m_stack->setCurrentIndex(1);
    } else if (m_kind == QStringLiteral("image")) {
        QPixmap pix;
        const auto bytes = QByteArray::fromBase64(o.value("png").toString().toLatin1());
        if (bytes.size() > 8*1024*1024 || !pix.loadFromData(bytes, "PNG")) { clear(tr("Invalid preview image.")); return; }
        m_image->setPixmap(pix); m_stack->setCurrentIndex(2);
    } else {
        m_kind = QStringLiteral("unsupported"); m_message->setText(o.value("message").toString(tr("Preview unavailable."))); m_stack->setCurrentIndex(0);
    }
    Q_EMIT previewReady(m_kind);
}
