// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QWidget>
#include <QUrl>
class QLabel;
class QPlainTextEdit;
class QStackedWidget;
class QProcess;
class QTimer;
class ContentViewer final : public QWidget {
    Q_OBJECT
public:
    explicit ContentViewer(QWidget *parent = nullptr);
    ~ContentViewer() override;
    void showUrl(const QUrl &url);
    void clear(const QString &message = {});
    QString currentKind() const { return m_kind; }
Q_SIGNALS:
    void previewReady(const QString &kind);
private:
    void stop();
    void displayResult(const QByteArray &data);
    QStackedWidget *m_stack;
    QLabel *m_message;
    QLabel *m_image;
    QPlainTextEdit *m_text;
    QProcess *m_process = nullptr;
    QTimer *m_timeout;
    QString m_kind = QStringLiteral("empty");
    quint64 m_request = 0;
};
