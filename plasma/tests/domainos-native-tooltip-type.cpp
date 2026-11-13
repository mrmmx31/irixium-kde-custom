// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Give the Python test client the exact native StatusNotifier D-Bus interface.
// A QVariant property would export a nested variant, losing ToolTip contents.
#include <QByteArray>
#include <QDBusAbstractAdaptor>
#include <QDBusArgument>
#include <QDBusMetaType>
#include <QDBusObjectPath>
#include <QMetaType>
#include <QVariant>

struct DomainOSFixtureIconPixmap { qint32 width=0,height=0;QByteArray pixels; };
Q_DECLARE_METATYPE(DomainOSFixtureIconPixmap)
QDBusArgument &operator<<(QDBusArgument &argument,const DomainOSFixtureIconPixmap &image) {
    argument.beginStructure();argument<<image.width<<image.height<<image.pixels;argument.endStructure();return argument;
}
const QDBusArgument &operator>>(const QDBusArgument &argument,DomainOSFixtureIconPixmap &image) {
    argument.beginStructure();argument>>image.width>>image.height>>image.pixels;argument.endStructure();return argument;
}
using DomainOSFixtureIconPixmaps=QList<DomainOSFixtureIconPixmap>;
Q_DECLARE_METATYPE(DomainOSFixtureIconPixmaps)
struct DomainOSFixtureTooltip {QString icon;DomainOSFixtureIconPixmaps images;QString title,subtitle;};
Q_DECLARE_METATYPE(DomainOSFixtureTooltip)
QDBusArgument &operator<<(QDBusArgument &argument,const DomainOSFixtureTooltip &tip) {
    argument.beginStructure();argument<<tip.icon<<tip.images<<tip.title<<tip.subtitle;argument.endStructure();return argument;
}
const QDBusArgument &operator>>(const QDBusArgument &argument,DomainOSFixtureTooltip &tip) {
    argument.beginStructure();argument>>tip.icon>>tip.images>>tip.title>>tip.subtitle;argument.endStructure();return argument;
}
class DomainOSFixtureSniAdaptor:public QDBusAbstractAdaptor {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface","org.kde.StatusNotifierItem")
    Q_PROPERTY(QString Category READ category)
    Q_PROPERTY(QString Id READ id)
    Q_PROPERTY(QString Title READ title)
    Q_PROPERTY(QString Status READ status)
    Q_PROPERTY(QString IconName READ iconName)
    Q_PROPERTY(QString AttentionIconName READ attentionIconName)
    Q_PROPERTY(QString OverlayIconName READ overlayIconName)
    Q_PROPERTY(QString IconThemePath READ iconThemePath)
    Q_PROPERTY(uint WindowId READ windowId)
    Q_PROPERTY(bool ItemIsMenu READ itemIsMenu)
    Q_PROPERTY(QDBusObjectPath Menu READ menu)
    Q_PROPERTY(DomainOSFixtureTooltip ToolTip READ tooltip)
public:
    explicit DomainOSFixtureSniAdaptor(QObject *owner,int index):QDBusAbstractAdaptor(owner),m_index(index) {setAutoRelaySignals(true);}
    QString category()const {return parent()->property("Category").toString();}
    QString id()const {return parent()->property("Id").toString();}
    QString title()const {return parent()->property("Title").toString();}
    QString status()const {return parent()->property("Status").toString();}
    QString iconName()const {return parent()->property("IconName").toString();}
    QString attentionIconName()const {return parent()->property("AttentionIconName").toString();}
    QString overlayIconName()const {return parent()->property("OverlayIconName").toString();}
    QString iconThemePath()const {return parent()->property("IconThemePath").toString();}
    uint windowId()const {return parent()->property("WindowId").toUInt();}
    bool itemIsMenu()const {return parent()->property("ItemIsMenu").toBool();}
    QDBusObjectPath menu()const {return QDBusObjectPath("/NO_DBUSMENU");}
    DomainOSFixtureTooltip tooltip()const {return {"utilities-terminal",{},"DomainOS native hint "+QString::number(m_index),"Test-owned StatusNotifierItem"};}
public slots:
    void Activate(int x,int y) {QMetaObject::invokeMethod(parent(),"Activate",Qt::DirectConnection,Q_ARG(int,x),Q_ARG(int,y));}
    void SecondaryActivate(int x,int y) {QMetaObject::invokeMethod(parent(),"SecondaryActivate",Qt::DirectConnection,Q_ARG(int,x),Q_ARG(int,y));}
    void ContextMenu(int x,int y) {QMetaObject::invokeMethod(parent(),"ContextMenu",Qt::DirectConnection,Q_ARG(int,x),Q_ARG(int,y));}
    void Scroll(int delta,const QString &orientation) {QMetaObject::invokeMethod(parent(),"Scroll",Qt::DirectConnection,Q_ARG(int,delta),Q_ARG(QString,orientation));}
    void ProvideXdgActivationToken(const QString &token) {QMetaObject::invokeMethod(parent(),"ProvideXdgActivationToken",Qt::DirectConnection,Q_ARG(QString,token));}
signals:
    void NewStatus(const QString &status);
    void NewIcon();
    void NewAttentionIcon();
    void NewOverlayIcon();
    void NewToolTip();
    void NewTitle();
private:
    int m_index;
};
extern "C" void domainosFixtureAddSniAdaptor(QObject *owner,int index) {
    qDBusRegisterMetaType<DomainOSFixtureIconPixmap>();
    qDBusRegisterMetaType<DomainOSFixtureIconPixmaps>();
    qDBusRegisterMetaType<DomainOSFixtureTooltip>();
    new DomainOSFixtureSniAdaptor(owner,index);
}
#include "domainos-native-tooltip-type.moc"
