// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#include "core.h"
#include "classicshell.h"
#include "shelf.h"
#include "preview.h"
#include "dolphinmainwindow.h"
#include "dolphinviewcontainer.h"
#include "views/dolphinview.h"
#include <KAboutData>
#include <KActionCollection>
#include <KStandardAction>
#include <KLocalizedString>
#include <QApplication>
#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <QImage>
#include <QJsonDocument>
#include <QProcess>
#include <QTemporaryDir>
#include <QtTest>
class AppTest : public QObject {
    Q_OBJECT
private Q_SLOTS:
    void shelfDoesNotDeleteOriginal() {
        QTemporaryDir dir;QFile f(dir.path()+"/document.txt");QVERIFY(f.open(QIODevice::WriteOnly));f.write("safe");f.close();
        Shelf shelf;shelf.setLocation(QUrl::fromLocalFile(dir.path()));shelf.addReferences({QUrl::fromLocalFile(f.fileName())});QCOMPARE(shelf.count(),1);
        shelf.item(0)->setSelected(true);shelf.removeReferences();QCOMPARE(shelf.count(),0);QVERIFY(QFile::exists(f.fileName()));
        Shelf loaded;loaded.setLocation(QUrl::fromLocalFile(dir.path()));QCOMPARE(loaded.count(),0);
    }
    void shelfPerDirectory() {
        QTemporaryDir a,b;Shelf s;s.setLocation(QUrl::fromLocalFile(a.path()));s.addReferences({QUrl::fromLocalFile(a.path())});QCOMPARE(s.count(),1);
        s.setLocation(QUrl::fromLocalFile(b.path()));QCOMPARE(s.count(),0);s.setLocation(QUrl::fromLocalFile(a.path()));QCOMPARE(s.count(),1);
    }
    void previewTextAndImage() {
        QTemporaryDir dir;QFile f(dir.path()+"/text.html");QVERIFY(f.open(QIODevice::WriteOnly));f.write("<script>do_not_execute()</script>");f.close();
        ContentViewer viewer;viewer.showUrl(QUrl::fromLocalFile(f.fileName()));QTRY_COMPARE_WITH_TIMEOUT(viewer.currentKind(),QString("text"),5000);
        QImage image(24,24,QImage::Format_RGB32);image.fill(Qt::red);QVERIFY(image.save(dir.path()+"/image.png"));
        viewer.showUrl(QUrl::fromLocalFile(dir.path()+"/image.png"));QTRY_COMPARE_WITH_TIMEOUT(viewer.currentKind(),QString("image"),5000);
        viewer.showUrl(QUrl("https://example.test/image.png"));QCOMPARE(viewer.currentKind(),QString("empty"));
    }
    void binaryAndOversize() {
        QTemporaryDir dir;QFile f(dir.path()+"/binary.bin");QVERIFY(f.open(QIODevice::WriteOnly));f.write(QByteArray(30,'\0'));f.close();
        ContentViewer v;v.showUrl(QUrl::fromLocalFile(f.fileName()));QTRY_COMPARE_WITH_TIMEOUT(v.currentKind(),QString("unsupported"),5000);
        QVERIFY(f.open(QIODevice::ReadWrite));QVERIFY(f.resize(17*1024*1024));f.close();v.showUrl(QUrl::fromLocalFile(f.fileName()));QTRY_COMPARE_WITH_TIMEOUT(v.currentKind(),QString("unsupported"),5000);
    }
    void initialFileSelection() {
        QTemporaryDir dir; QFile file(dir.path()+"/selected.txt");
        QVERIFY(file.open(QIODevice::WriteOnly)); file.write("preview from --select\n"); file.close();
        auto *window=new DolphinMainWindow;
        window->openFiles({QUrl::fromLocalFile(file.fileName())},false);
        auto *shell=new ClassicShell(window); window->show();
        auto *view=window->activeViewContainer()->view();
        QTRY_COMPARE_WITH_TIMEOUT(view->selectedItemsCount(),1,15000);
        QTRY_COMPARE_WITH_TIMEOUT(shell->viewer()->currentKind(),QString("text"),5000);
        window->close(); delete window;
    }
    void nativeCopyMoveAndSelection() {
        QTemporaryDir source, destination, moved;
        QFile file(source.path()+"/Documento com acentos ação.txt");
        QVERIFY(file.open(QIODevice::WriteOnly)); file.write("conteudo artificial\n"); file.close();
        auto *window=new DolphinMainWindow;
        window->openDirectories({QUrl::fromLocalFile(source.path())},false);
        auto *shell=new ClassicShell(window); window->resize(900,780); window->show();
        auto *view=window->activeViewContainer()->view();
        QTRY_COMPARE_WITH_TIMEOUT(view->itemsCount(),1,15000);
        view->selectAll();
        QTRY_COMPARE_WITH_TIMEOUT(view->selectedItemsCount(),1,5000);
        QTRY_COMPARE_WITH_TIMEOUT(shell->viewer()->currentKind(),QString("text"),5000);
        shell->pinSelection(); QCOMPARE(shell->shelf()->count(),1);
        const auto selection=view->selectedItems();
        view->copySelectedItems(selection,QUrl::fromLocalFile(destination.path()));
        const auto copy=destination.path()+"/"+QFileInfo(file.fileName()).fileName();
        QTRY_VERIFY_WITH_TIMEOUT(QFile::exists(copy),15000);
        QFile copied(copy); QVERIFY(copied.open(QIODevice::ReadOnly)); QCOMPARE(copied.readAll(),QByteArray("conteudo artificial\n")); copied.close();
        QVERIFY(QFile::exists(file.fileName()));
        view->moveSelectedItems(selection,QUrl::fromLocalFile(moved.path()));
        QTRY_VERIFY_WITH_TIMEOUT(QFile::exists(moved.path()+"/"+QFileInfo(file.fileName()).fileName()),15000);
        QTRY_VERIFY_WITH_TIMEOUT(!QFile::exists(file.fileName()),5000);
        QVERIFY(QFile::exists(copy));
        window->actionCollection()->action("split_view")->trigger();
        QTRY_VERIFY(window->isSplitViewEnabledInCurrentTab());
        window->close(); delete window;
    }
    void dolphinViewAndIsolation() {
        QTemporaryDir dir;QVERIFY(QDir().mkdir(dir.path()+"/child"));
        QFile f(dir.path()+"/Unicode space.txt");QVERIFY(f.open(QIODevice::WriteOnly));f.write("fixture");f.close();
        auto *window=new DolphinMainWindow;window->openDirectories({QUrl::fromLocalFile(dir.path())},false);auto *shell=new ClassicShell(window);window->show();
        QVERIFY(window->activeViewContainer());auto *view=window->activeViewContainer()->view();
        QTRY_VERIFY_WITH_TIMEOUT(view->itemsCount()>=2,15000);
        for(const auto &name:{"edit_copy","edit_paste","renamefile","movetotrash","deletefile","edit_undo","new_tab","split_view"}) QVERIFY2(window->actionCollection()->action(QString::fromLatin1(name)),name);
        QVERIFY(window->actionCollection()->action(KStandardAction::name(KStandardAction::Redisplay)));
        view->setViewMode(DolphinView::DetailsView);view->setHiddenFilesShown(true);
        shell->navigate(QUrl::fromLocalFile(dir.path()+"/child"));QTRY_COMPARE_WITH_TIMEOUT(view->url(),QUrl::fromLocalFile(dir.path()+"/child"),5000);
        window->close();delete window;QCoreApplication::processEvents();
        QVERIFY(!QFile::exists(dir.path()+"/.directory"));QVERIFY(!QFile::exists(dir.path()+"/child/.directory"));
        QVERIFY(!QFile::exists(QDir::homePath()+"/.config/dolphinrc"));
    }
};
int main(int argc,char **argv) {
    // Isolation is established BEFORE Qt/KConfig are constructed.
    QTemporaryDir home;if(!home.isValid())return 2;
    qputenv("HOME",home.path().toUtf8());qputenv("XDG_CONFIG_HOME",(home.path()+"/.config").toUtf8());
    qputenv("XDG_DATA_HOME",(home.path()+"/.local/share").toUtf8());qputenv("XDG_CACHE_HOME",(home.path()+"/.cache").toUtf8());
    QApplication app(argc,argv);KAboutData about(QString::fromLatin1(Irix::AppName),"IrixClassic tests",Irix::Version);KAboutData::setApplicationData(about);
    KLocalizedString::setApplicationDomain("dolphin");
    AppTest test;return QTest::qExec(&test,argc,argv);
}
#include "tst_application.moc"
