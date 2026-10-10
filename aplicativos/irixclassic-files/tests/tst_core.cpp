// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#include "core.h"
#include <QFile>
#include <QTemporaryDir>
#include <QtTest>
class CoreTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void absolutePath() { QCOMPARE(Irix::locationFromText("/tmp/a b",{}),QUrl::fromLocalFile("/tmp/a b")); }
    void relativePath() { QCOMPARE(Irix::locationFromText("child",QUrl::fromLocalFile("/tmp/root")),QUrl::fromLocalFile("/tmp/root/child")); }
    void remotePath() { QCOMPARE(Irix::locationFromText("child",QUrl("sftp://example.test/a")),QUrl("sftp://example.test/a/child")); }
    void emptyPath() { QVERIFY(Irix::locationFromText("  ",{}).isEmpty()); }
    void unicodePath() { QCOMPARE(Irix::locationFromText(QString::fromUtf8("/tmp/ação"),{}).toLocalFile(),QString::fromUtf8("/tmp/ação")); }
    void parents() { const auto p=Irix::ancestors(QUrl::fromLocalFile("/tmp/a b"));QCOMPARE(p.size(),3);QCOMPARE(p.first().toLocalFile(),QString("/"));QCOMPARE(p.last().toLocalFile(),QString("/tmp/a b")); }
    void hiddenPassword() { QVERIFY(!Irix::displayedLocation(QUrl("sftp://user:secret@example.test/a")).contains("secret")); }
    void privateKey() { QCOMPARE(Irix::shelfKey(QUrl("sftp://u:a@h/p")),Irix::shelfKey(QUrl("sftp://u:b@h/p")));QCOMPARE(Irix::shelfKey(QUrl("file:///a")).size(),64); }
    void localOnlyShelf() { QVERIFY(!Irix::shelfReferenceAllowed(QUrl("https://example.test/a")));QTemporaryDir d;QVERIFY(Irix::shelfReferenceAllowed(QUrl::fromLocalFile(d.path())));QVERIFY(!Irix::shelfReferenceAllowed(QUrl::fromLocalFile(d.path()+"/absent"))); }
};
QTEST_GUILESS_MAIN(CoreTest)
#include "tst_core.moc"
