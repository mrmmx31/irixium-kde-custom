// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later

// Public Qt adapters owned by this applet: native menu painting, scrollbar
// geometry and the scoped tray-popup wheel route. Native producers, actions
// and layout remain intact.
#include "scrollgeometry.h"
#include "popupwheel.h"
#include <QAction>
#include <QActionEvent>
#include <QApplication>
#include <QCommonStyle>
#include <QHash>
#include <QImage>
#include <QMenu>
#include <QPainter>
#include <QPixmap>
#include <QPointer>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlExtensionPlugin>
#include <QQmlListReference>
#include <QSet>
#include <QStyleOptionMenuItem>
#include <QUuid>
#include <QtQml/qqml.h>

class OwnedMenuStyle : public QCommonStyle {
    Q_OBJECT
public:
    OwnedMenuStyle(QStyle* base, QObject* parent) : m_base(base) {
        setParent(parent);
        setObjectName("domainos-owned-menu-style");
    }
    int pixelMetric(PixelMetric m, const QStyleOption* o = nullptr,
                    const QWidget* w = nullptr) const override {
        return m_base ? m_base->pixelMetric(m, o, w) : QCommonStyle::pixelMetric(m, o, w);
    }
    int styleHint(StyleHint h, const QStyleOption* o = nullptr, const QWidget* w = nullptr,
                  QStyleHintReturn* r = nullptr) const override {
        return m_base ? m_base->styleHint(h, o, w, r) : QCommonStyle::styleHint(h, o, w, r);
    }
    QSize sizeFromContents(ContentsType t, const QStyleOption* o, const QSize& s,
                           const QWidget* w = nullptr) const override {
        return m_base ? m_base->sizeFromContents(t, o, s, w)
                      : QCommonStyle::sizeFromContents(t, o, s, w);
    }
    QRect subElementRect(SubElement e, const QStyleOption* o,
                         const QWidget* w = nullptr) const override {
        return m_base ? m_base->subElementRect(e, o, w) : QCommonStyle::subElementRect(e, o, w);
    }
    QRect subControlRect(ComplexControl c, const QStyleOptionComplex* o, SubControl s,
                         const QWidget* w = nullptr) const override {
        return m_base ? m_base->subControlRect(c, o, s, w)
                      : QCommonStyle::subControlRect(c, o, s, w);
    }
    SubControl hitTestComplexControl(ComplexControl c, const QStyleOptionComplex* o,
                                     const QPoint& p, const QWidget* w = nullptr) const override {
        return m_base ? m_base->hitTestComplexControl(c, o, p, w)
                      : QCommonStyle::hitTestComplexControl(c, o, p, w);
    }
    int layoutSpacing(QSizePolicy::ControlType a, QSizePolicy::ControlType b,
                      Qt::Orientation orientation, const QStyleOption* o = nullptr,
                      const QWidget* w = nullptr) const override {
        return m_base ? m_base->layoutSpacing(a, b, orientation, o, w)
                      : QCommonStyle::layoutSpacing(a, b, orientation, o, w);
    }
    QPixmap standardPixmap(StandardPixmap p, const QStyleOption* o = nullptr,
                           const QWidget* w = nullptr) const override {
        return m_base ? m_base->standardPixmap(p, o, w) : QCommonStyle::standardPixmap(p, o, w);
    }
    QIcon standardIcon(StandardPixmap p, const QStyleOption* o = nullptr,
                       const QWidget* w = nullptr) const override {
        return m_base ? m_base->standardIcon(p, o, w) : QCommonStyle::standardIcon(p, o, w);
    }
    QPixmap generatedIconPixmap(QIcon::Mode mode, const QPixmap& p,
                                const QStyleOption* o) const override {
        return m_base ? m_base->generatedIconPixmap(mode, p, o)
                      : QCommonStyle::generatedIconPixmap(mode, p, o);
    }
    void drawComplexControl(ComplexControl c, const QStyleOptionComplex* o, QPainter* p,
                            const QWidget* w = nullptr) const override {
        if (m_base)
            m_base->drawComplexControl(c, o, p, w);
        else
            QCommonStyle::drawComplexControl(c, o, p, w);
    }
    void polish(QWidget* w) override {
        if (m_base)
            m_base->polish(w);
        else
            QCommonStyle::polish(w);
    }
    void unpolish(QWidget* w) override {
        if (m_base)
            m_base->unpolish(w);
        else
            QCommonStyle::unpolish(w);
    }
    void drawPrimitive(PrimitiveElement e, const QStyleOption* o, QPainter* p,
                       const QWidget* w = nullptr) const override {
        if (e != PE_PanelMenu) {
            if (m_base)
                m_base->drawPrimitive(e, o, p, w);
            else
                QCommonStyle::drawPrimitive(e, o, p, w);
            return;
        }
        const QRect r = o->rect, inner = r.adjusted(1, 1, -1, -1);
        p->save();
        p->fillRect(r, o->palette.window());
        p->setPen(o->palette.light().color());
        p->drawLine(r.topLeft(), r.topRight());
        p->drawLine(r.topLeft(), r.bottomLeft());
        p->setPen(o->palette.shadow().color());
        p->drawLine(r.bottomLeft(), r.bottomRight());
        p->drawLine(r.topRight(), r.bottomRight());
        p->setPen(o->palette.midlight().color());
        p->drawLine(inner.topLeft(), inner.topRight());
        p->drawLine(inner.topLeft(), inner.bottomLeft());
        p->setPen(o->palette.dark().color());
        p->drawLine(inner.bottomLeft(), inner.bottomRight());
        p->drawLine(inner.topRight(), inner.bottomRight());
        p->restore();
    }
    void drawControl(ControlElement e, const QStyleOption* o, QPainter* p,
                     const QWidget* w = nullptr) const override {
        const auto item = qstyleoption_cast<const QStyleOptionMenuItem*>(o);
        if (e != CE_MenuItem || !item) {
            if (m_base)
                m_base->drawControl(e, o, p, w);
            else
                QCommonStyle::drawControl(e, o, p, w);
            return;
        }
        const bool enabled = item->state & State_Enabled,
                   selected = enabled && (item->state & State_Selected);
        const auto group =
            !enabled ? QPalette::Disabled
                     : (item->state & State_Active ? QPalette::Active : QPalette::Inactive);
        const QColor bg = item->palette.color(group,
                                              selected ? QPalette::Highlight : QPalette::Window),
                     fg = item->palette.color(group, selected ? QPalette::HighlightedText
                                                              : QPalette::WindowText);
        const QRect r = item->rect;
        p->save();
        p->fillRect(r, bg);
        p->setPen(fg);
        QFont itemFont = item->font;
        if (item->menuItemType == QStyleOptionMenuItem::DefaultItem)
            itemFont.setBold(true);
        p->setFont(itemFont);
        if (item->menuItemType == QStyleOptionMenuItem::Separator) {
            if (item->text.isEmpty()) {
                const int y = r.center().y();
                p->setPen(item->palette.dark().color());
                p->drawLine(r.left() + 3, y, r.right() - 3, y);
                p->setPen(item->palette.light().color());
                p->drawLine(r.left() + 3, y + 1, r.right() - 3, y + 1);
            } else {
                QFont f = item->font;
                f.setBold(true);
                p->setFont(f);
                const int margin =
                    pixelMetric(PM_MenuHMargin, o, w) + pixelMetric(PM_MenuPanelWidth, o, w);
                p->drawText(r.adjusted(margin, 0, -margin, 0),
                            Qt::AlignVCenter | (item->direction == Qt::RightToLeft ? Qt::AlignRight
                                                                                   : Qt::AlignLeft),
                            item->text);
            }
            p->restore();
            return;
        }
        const bool rtl = item->direction == Qt::RightToLeft,
                   submenu = item->menuItemType == QStyleOptionMenuItem::SubMenu;
        const int margin =
            qMax(2, pixelMetric(PM_MenuHMargin, o, w)) + pixelMetric(PM_MenuPanelWidth, o, w);
        const int iconSize = pixelMetric(PM_SmallIconSize, o, w),
                  checkWidth = item->menuHasCheckableItems ? iconSize : 0;
        const int extent = qMax(item->maxIconWidth, checkWidth), center = r.center().y();
        const QRect logicalIcon(r.left() + margin, center - iconSize / 2, qMax(extent, iconSize),
                                iconSize),
            iconRect = visualRect(item->direction, r, logicalIcon);
        if (!item->icon.isNull())
            item->icon.paint(p, iconRect, Qt::AlignCenter,
                             enabled ? (selected ? QIcon::Active : QIcon::Normal) : QIcon::Disabled,
                             item->checked ? QIcon::On : QIcon::Off);
        if (item->checkType != QStyleOptionMenuItem::NotCheckable) {
            const int side = qMin(iconSize, 12);
            const QRect box = visualRect(item->direction, r,
                                         QRect(logicalIcon.left(), center - side / 2, side, side));
            if (item->icon.isNull()) {
                p->setPen(item->palette.color(group, QPalette::Dark));
                p->drawLine(box.topLeft(), box.topRight());
                p->drawLine(box.topLeft(), box.bottomLeft());
                p->setPen(item->palette.color(group, QPalette::Light));
                p->drawLine(box.bottomLeft(), box.bottomRight());
                p->drawLine(box.topRight(), box.bottomRight());
            }
            p->setPen(fg);
            if (item->checked) {
                // Checked icons keep a cue instead of relying on an optional QIcon::On
                // variant.
                if (!item->icon.isNull()) {
                    p->setPen(item->palette.color(group, QPalette::Highlight));
                    p->drawRect(iconRect.adjusted(0, 0, -1, -1));
                } else if (item->checkType == QStyleOptionMenuItem::Exclusive) {
                    p->setBrush(fg);
                    p->drawEllipse(box.adjusted(3, 3, -3, -3));
                } else {
                    p->drawLine(box.left() + 2, center, box.left() + 5, center + 3);
                    p->drawLine(box.left() + 5, center + 3, box.right() - 2, center - 3);
                }
            }
        }
        const int gap = qMax(2, pixelMetric(PM_MenuHMargin, o, w)),
                  arrowWidth = submenu ? iconSize : 0;
        const int contentLeft = margin + extent + (extent ? gap : 0),
                  contentRight = margin + arrowWidth;
        const QRect logicalText = r.adjusted(contentLeft, 0, -contentRight, 0);
        const auto parts = item->text.split('\t');
        const int shortcutWidth = parts.size() > 1
                                      ? qMax(item->reservedShortcutWidth,
                                             item->fontMetrics.horizontalAdvance(parts.last()))
                                      : 0;
        const QRect labelRect =
            visualRect(item->direction, r,
                       logicalText.adjusted(0, 0, -(shortcutWidth ? shortcutWidth + gap : 0), 0));
        int flags =
            Qt::AlignVCenter | Qt::TextShowMnemonic | (rtl ? Qt::AlignRight : Qt::AlignLeft);
        if (!styleHint(SH_UnderlineShortcut, o, w))
            flags |= Qt::TextHideMnemonic;
        p->setPen(fg);
        p->drawText(labelRect, flags, parts.first());
        if (parts.size() > 1) {
            const QRect shortcutRect =
                visualRect(item->direction, r,
                           QRect(logicalText.right() - shortcutWidth + 1, logicalText.top(),
                                 shortcutWidth, logicalText.height()));
            p->drawText(shortcutRect, Qt::AlignVCenter | (rtl ? Qt::AlignLeft : Qt::AlignRight),
                        parts.last());
        }
        if (submenu) {
            const int x =
                rtl ? r.left() + margin + iconSize / 2 : r.right() - margin - iconSize / 2;
            p->setBrush(fg);
            p->drawPolygon(QPolygon{QPoint(x + (rtl ? 3 : -3), center - 4),
                                    QPoint(x + (rtl ? 3 : -3), center + 4),
                                    QPoint(x + (rtl ? -1 : 1), center)});
        }
        p->restore();
    }

private:
    QPointer<QStyle> m_base;
};

class OwnMenuScope : public QObject {
    Q_OBJECT
    Q_PROPERTY(QPalette palette READ palette WRITE setPalette NOTIFY paletteChanged)
    Q_PROPERTY(QVariantMap stats READ stats NOTIFY statsChanged)
public:
    explicit OwnMenuScope(QObject* parent = nullptr)
        : QObject(parent), m_effectivePalette(explicitPalette(m_palette)) {}
    ~OwnMenuScope() override { release(); }
    QPalette palette() const { return m_palette; }
    void setPalette(const QPalette& p) {
        if (p == m_palette && p.resolveMask() == m_palette.resolveMask())
            return;
        m_palette = p;
        m_effectivePalette = explicitPalette(p);
        QPointer<OwnMenuScope> safe = this;
        emit paletteChanged();
        if (!safe)
            return;
        const auto entries = m_entries;
        for (const auto& entry : entries) {
            if (!safe)
                return;
            if (entry.menu && entry.menu->style() == entry.owned)
                entry.menu->setPalette(m_effectivePalette);
        }
    }
    QVariantMap stats() const {
        return {{"attached", m_entries.size()},
                {"scans", m_scans},
                {"queued", m_queued},
                {"firstPaints", m_firstPaints},
                {"incorrectFirstPaints", m_badFirstPaints},
                {"active", bool(m_root)},
                {"markerName", m_marker ? m_marker->objectName() : QString()},
                {"error", m_error}};
    }
    Q_INVOKABLE bool prepare(QObject* provider) {
        if (!provider) {
            m_error = "missing provider";
            emit statsChanged();
            return false;
        }
        if (m_provider == provider && m_root) {
            return scan();
        }
        QPointer<OwnMenuScope> safeScope = this;
        QPointer<QObject> safeProvider = provider;
        release();
        if (!safeScope || !safeProvider)
            return false;
        QPointer<QQmlEngine> engine = qmlEngine(provider);
        QQmlListReference content(provider, "content");
        if (!engine || !content.isValid() || !content.canCount() || !content.canAt()) {
            m_error = "provider has no QML menu content";
            emit statsChanged();
            return false;
        }
        QQmlComponent component(engine);
        component.setData("import org.kde.plasma.extras as Extras; Extras.MenuItem "
                          "{ visible:false; text: \"Own scope marker\" }",
                          QUrl());
        QObject* marker = component.create(qmlContext(provider));
        if (!marker) {
            m_error = component.errorString();
            emit statsChanged();
            return false;
        }
        QPointer<QObject> safeMarker = marker;
        if (!safeProvider || !engine) {
            marker->deleteLater();
            return false;
        }
        QQmlEngine::setObjectOwnership(marker, QQmlEngine::CppOwnership);
        marker->setObjectName("domainos-own-scope-" +
                              QUuid::createUuid().toString(QUuid::WithoutBraces));
        marker->setParent(provider);
        if (!safeScope || !safeProvider || !safeMarker || !engine) {
            if (safeMarker)
                safeMarker->deleteLater();
            return false;
        }
        auto jsProvider = engine->newQObject(provider), jsMarker = engine->newQObject(marker);
        auto add = jsProvider.property("addMenuItem");
        if (!add.isCallable() || add.callWithInstance(jsProvider, {jsMarker}).isError()) {
            marker->deleteLater();
            m_error = "marker insertion failed";
            emit statsChanged();
            return false;
        }
        if (!safeProvider || !safeMarker || !engine) {
            if (safeMarker)
                safeMarker->deleteLater();
            return false;
        }
        auto action = qobject_cast<QAction*>(marker->property("action").value<QObject*>());
        QList<QMenu*> candidates;
        if (action)
            for (auto object : action->associatedObjects())
                if (auto menu = qobject_cast<QMenu*>(object))
                    candidates.append(menu);
        if (candidates.size() != 1) {
            marker->deleteLater();
            m_error = "marker does not identify exactly one native root";
            emit statsChanged();
            return false;
        }
        auto root = candidates.first();
        if (auto owner = s_owners.value(root); owner && owner != this) {
            marker->deleteLater();
            m_error = "native root already has another menu scope";
            emit statsChanged();
            return false;
        }
        bool markerPresent = false;
        for (qsizetype i = 0; i < content.count(); ++i) {
            auto item = content.at(i);
            if (item == marker)
                markerPresent = true;
            if (!item || item->property("section").toBool())
                continue;
            auto a = qobject_cast<QAction*>(item->property("action").value<QObject*>());
            if (a && !a->associatedObjects().isEmpty() && !root->actions().contains(a)) {
                marker->deleteLater();
                m_error = "root differs from provider content";
                emit statsChanged();
                return false;
            }
        }
        if (!markerPresent) {
            marker->deleteLater();
            m_error = "marker missing from provider content";
            emit statsChanged();
            return false;
        }
        m_provider = provider;
        m_engine = engine;
        m_marker = marker;
        m_root = root;
        m_error.clear();
        m_providerConnection = connect(provider, &QObject::destroyed, this, [this] { release(); });
        return scan();
    }
    Q_INVOKABLE QObject* rootMenu() const { return m_root; }
    Q_INVOKABLE void release() {
        if (m_releasing)
            return;
        m_releasing = true;
        m_pending = false;
        ++m_generation;
        disconnect(m_providerConnection);
        for (const auto& connections : m_actionConnections)
            for (const auto& connection : connections)
                disconnect(connection);
        m_actionConnections.clear();
        QPointer<OwnMenuScope> safeScope = this;
        const auto entries = m_entries;
        m_entries.clear();
        for (const auto& entry : entries) {
            restore(entry);
            if (!safeScope)
                return;
        }
        auto marker = m_marker, provider = m_provider;
        QPointer<QQmlEngine> engine = m_engine;
        m_root = nullptr;
        m_marker = nullptr;
        m_provider = nullptr;
        if (marker) {
            if (provider && engine) {
                auto js = engine->newQObject(provider);
                auto remove = js.property("removeMenuItem");
                if (remove.isCallable())
                    remove.callWithInstance(js, {engine->newQObject(marker)});
            }
            if (marker)
                marker->deleteLater();
        }
        m_engine = nullptr;
        m_releasing = false;
        emit statsChanged();
    }
signals:
    void paletteChanged();
    void statsChanged();

protected:
    bool eventFilter(QObject* object, QEvent* event) override {
        if (m_releasing)
            return false;
        if (event->type() == QEvent::Paint) {
            auto menu = qobject_cast<QMenu*>(object);
            if (menu && !m_painted.contains(menu)) {
                m_painted.insert(menu);
                ++m_firstPaints;
                bool correct = false;
                for (const auto& entry : m_entries)
                    if (entry.menu == menu)
                        correct = menu->style() == entry.owned &&
                                  sameBrushes(menu->palette(), m_effectivePalette);
                if (!correct)
                    ++m_badFirstPaints;
            }
            return false;
        }
        if (event->type() == QEvent::ActionAdded || event->type() == QEvent::ActionChanged ||
            event->type() == QEvent::ActionRemoved)
            scheduleScan();
        if (event->type() == QEvent::Show) {
            m_painted.remove(qobject_cast<QMenu*>(object));
            if (!m_mutating)
                scan();
        }
        return false;
    }

private:
    struct Entry {
        QPointer<QMenu> menu;
        QPointer<QStyle> original;
        QPointer<OwnedMenuStyle> owned;
        QPalette palette;
        bool explicitStyle = false, explicitPalette = false;
        QMetaObject::Connection destroyed;
    };
    void restore(const Entry& entry) {
        QPointer<QMenu> menu = entry.menu;
        disconnect(entry.destroyed);
        if (menu) {
            menu->removeEventFilter(this);
            if (s_owners.value(menu) == this)
                s_owners.remove(menu);
            const bool ownsStyle = menu->style() == entry.owned;
            const bool ownsPalette =
                sameBrushes(menu->palette(), m_effectivePalette) &&
                menu->palette().resolveMask() == m_effectivePalette.resolveMask();
            if (ownsStyle) {
                menu->setStyle(entry.explicitStyle ? entry.original.data() : nullptr);
                if (menu && ownsPalette)
                    menu->setPalette(entry.explicitPalette ? entry.palette : QPalette());
            }
        }
        if (entry.owned)
            entry.owned->deleteLater();
    }
    void scheduleScan() {
        if (m_pending || m_releasing || !m_root)
            return;
        m_pending = true;
        ++m_queued;
        QPointer<OwnMenuScope> safe = this;
        const int generation = m_generation;
        QMetaObject::invokeMethod(
            this,
            [safe, generation] {
                if (!safe || safe->m_generation != generation)
                    return;
                safe->m_pending = false;
                safe->scan();
            },
            Qt::QueuedConnection);
    }
    bool attach(QMenu* menu) {
        for (const auto& entry : m_entries)
            if (entry.menu == menu)
                return true;
        if (auto owner = s_owners.value(menu); owner && owner != this) {
            m_error = "submenu already has another menu scope";
            return false;
        }
        Entry entry{menu,
                    menu->style(),
                    new OwnedMenuStyle(menu->style(), this),
                    menu->palette(),
                    menu->testAttribute(Qt::WA_SetStyle),
                    menu->testAttribute(Qt::WA_SetPalette),
                    {}};
        entry.destroyed = connect(menu, &QObject::destroyed, this, [this, menu] {
            s_owners.remove(menu);
            m_painted.remove(menu);
            scheduleScan();
        });
        m_entries.append(entry);
        s_owners.insert(menu, this);
        menu->installEventFilter(this);
        QPointer<OwnMenuScope> safeScope = this;
        QPointer<QMenu> safe = menu;
        menu->setStyle(entry.owned);
        if (!safeScope)
            return false;
        if (!safe)
            return true;
        // Kvantum may set WindowText during its first, deferred widget polish.
        // Finish that native setup before applying this menu's explicit KDE brushes.
        safe->ensurePolished();
        if (!safeScope)
            return false;
        if (!safe)
            return true;
        safe->setPalette(m_effectivePalette);
        return bool(safeScope);
    }
    bool scan() {
        if (!m_root || m_mutating || m_releasing)
            return bool(m_root);
        QPointer<OwnMenuScope> safeScope = this;
        m_mutating = true;
        ++m_scans;
        QSet<QMenu*> reachable;
        QSet<QAction*> reachableActions;
        QList<QPointer<QMenu>> pending{m_root};
        bool valid = true;
        while (!pending.isEmpty()) {
            QPointer<QMenu> menu = pending.takeLast();
            if (!menu || reachable.contains(menu))
                continue;
            if (reachable.size() >= 512) {
                m_error = "menu graph exceeds 512 native menus";
                valid = false;
                break;
            }
            reachable.insert(menu);
            const bool attached = attach(menu);
            if (!safeScope)
                return false;
            if (!attached) {
                valid = false;
                break;
            }
            if (!menu)
                continue;
            QList<QPointer<QAction>> actions;
            for (auto action : menu->actions())
                actions.append(action);
            for (const auto& action : actions) {
                if (!action)
                    continue;
                if (reachableActions.size() >= 8192) {
                    m_error = "menu graph exceeds 8192 native actions";
                    valid = false;
                    break;
                }
                reachableActions.insert(action);
                if (!m_actionConnections.contains(action)) {
                    auto raw = action.data();
                    m_actionConnections.insert(
                        raw, {connect(raw, &QAction::changed, this, [this] { scheduleScan(); }),
                              connect(raw, &QObject::destroyed, this, [this, raw] {
                                  m_actionConnections.remove(raw);
                                  scheduleScan();
                              })});
                }
                if (action && action->menu())
                    pending.append(action->menu());
            }
            if (!valid)
                break;
        }
        for (qsizetype i = m_entries.size() - 1; i >= 0; --i) {
            const auto entry = m_entries[i];
            if (entry.menu && reachable.contains(entry.menu))
                continue;
            m_entries.removeAt(i);
            restore(entry);
            if (!safeScope)
                return false;
        }

        for (auto i = m_actionConnections.begin(); i != m_actionConnections.end();) {
            if (reachableActions.contains(i.key())) {
                ++i;
                continue;
            }
            for (const auto& connection : i.value())
                disconnect(connection);
            i = m_actionConnections.erase(i);
        }
        m_mutating = false;
        if (!valid) {
            release();
            return false;
        }
        emit statsChanged();
        return true;
    }
    static QPalette explicitPalette(const QPalette& native) {
        QPalette result = native;
        // A native palette can carry values with resolveMask == 0. QWidget would
        // otherwise inherit those roles from Kvantum. Keep the property unchanged
        // and make only this local widget palette explicit, in every color group.
        for (int group = 0; group < 3; ++group)
            for (int role = 0; role < QPalette::NColorRoles; ++role) {
                if (role == QPalette::NoRole)
                    continue;
                result.setBrush(
                    QPalette::ColorGroup(group), QPalette::ColorRole(role),
                    native.brush(QPalette::ColorGroup(group), QPalette::ColorRole(role)));
            }
        return result;
    }
    static bool sameBrushes(const QPalette& first, const QPalette& second) {
        // Resolution provenance/currentColorGroup do not change the brushes used
        // by the menu painter. NoRole is reserved, not a paintable Qt color role.
        for (int group = 0; group < 3; ++group)
            for (int role = 0; role < QPalette::NColorRoles; ++role) {
                if (role == QPalette::NoRole)
                    continue;
                if (first.brush(QPalette::ColorGroup(group), QPalette::ColorRole(role)) !=
                    second.brush(QPalette::ColorGroup(group), QPalette::ColorRole(role)))
                    return false;
            }
        return true;
    }
    QPalette m_palette;
    QPalette m_effectivePalette;
    QPointer<QObject> m_provider, m_marker;
    QPointer<QQmlEngine> m_engine;
    QPointer<QMenu> m_root;
    inline static QHash<QMenu*, QPointer<OwnMenuScope>> s_owners;
    QList<Entry> m_entries;
    QSet<QMenu*> m_painted;
    QHash<QAction*, QList<QMetaObject::Connection>> m_actionConnections;
    QMetaObject::Connection m_providerConnection;
    bool m_pending = false, m_releasing = false, m_mutating = false;
    int m_scans = 0, m_queued = 0, m_firstPaints = 0, m_badFirstPaints = 0, m_generation = 0;
    QString m_error;
};
class NativeMenuPlugin : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char* uri) override {
        qmlRegisterType<OwnMenuScope>(uri, 1, 0, "OwnMenuScope");
        qmlRegisterType<NativeScrollGeometry>(uri, 1, 0, "NativeScrollGeometry");
        qmlRegisterType<NativePopupWheelForwarder>(uri, 1, 0, "NativePopupWheelForwarder");
    }
};
#include "plugin.moc"
