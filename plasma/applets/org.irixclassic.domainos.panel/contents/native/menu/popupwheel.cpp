// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
#include "popupwheel.h"
#include <QCoreApplication>
#include <QGuiApplication>
#include <QThread>
#include <QWheelEvent>
#include <QtCore/qscopeguard.h>
#include <cmath>

NativePopupWheelForwarder::NativePopupWheelForwarder(QObject* parent)
    : QObject(parent), m_supported(QGuiApplication::platformName() == QStringLiteral("xcb")
                                  && QString::fromLatin1(qVersion()) == QStringLiteral("6.8.2")) {}

NativePopupWheelForwarder::~NativePopupWheelForwarder() {
    if (m_watched)
        m_watched->removeEventFilter(this);
}

void NativePopupWheelForwarder::updateFilter() {
    if (m_watched)
        m_watched->removeEventFilter(this);
    m_watched.clear();
    if (m_supported && m_enabled && m_owner && m_popup && m_owner != m_popup
        && thread() == m_owner->thread() && thread() == m_popup->thread()) {
        m_watched = m_owner;
        m_watched->installEventFilter(this);
    }
}

void NativePopupWheelForwarder::setOwnerWindow(QWindow* window) {
    if (m_owner == window)
        return;
    disconnect(m_ownerDestroyed);
    m_owner = window;
    if (window)
        m_ownerDestroyed = connect(window, &QObject::destroyed, this, [this] {
            m_owner.clear();
            updateFilter();
            emit ownerWindowChanged();
        });
    updateFilter();
    emit ownerWindowChanged();
}

void NativePopupWheelForwarder::setPopupWindow(QWindow* window) {
    if (m_popup == window)
        return;
    disconnect(m_popupDestroyed);
    m_popup = window;
    if (window)
        m_popupDestroyed = connect(window, &QObject::destroyed, this, [this] {
            m_popup.clear();
            updateFilter();
            emit popupWindowChanged();
        });
    updateFilter();
    emit popupWindowChanged();
}

void NativePopupWheelForwarder::setEnabled(bool enabled) {
    if (m_enabled == enabled)
        return;
    m_enabled = enabled;
    updateFilter();
    emit enabledChanged();
}

bool NativePopupWheelForwarder::eventFilter(QObject* receiver, QEvent* event) {
    if (event->type() != QEvent::Wheel || !event->spontaneous() || m_forwarding
        || !m_supported || !m_enabled || receiver != m_owner || !m_owner || !m_popup
        || m_owner == m_popup || QThread::currentThread() != thread()
        || !m_popup->isVisible() || m_popup->type() != Qt::Popup
        || m_popup->transientParent() != m_owner)
        return false;

    auto* wheel = static_cast<QWheelEvent*>(event);
    // Smooth-scroll updates take a different internal Popup.Window route.
    // Retain Qt's original handling until that route has its own native proof.
    if (wheel->phase() != Qt::NoScrollPhase)
        return false;
    const QPointF global = wheel->globalPosition();
    if (!std::isfinite(global.x()) || !std::isfinite(global.y()))
        return false;
    const QPointF local = m_popup->mapFromGlobal(global);
    if (!QRectF(QPointF(0, 0), QSizeF(m_popup->size())).contains(local)
        || QGuiApplication::topLevelAt(global.toPoint()) != m_popup)
        return false;

    QWheelEvent translated(local, global, wheel->pixelDelta(), wheel->angleDelta(),
                           wheel->buttons(), wheel->modifiers(), wheel->phase(),
                           wheel->inverted(), wheel->source(), wheel->pointingDevice());
    translated.setTimestamp(wheel->timestamp());
    translated.setAccepted(wheel->isAccepted());
    m_forwarding = true;
    // Native callbacks may close the popup or destroy this adapter synchronously.
    // No member or target is accessed after dispatch without checking its lifetime.
    const QPointer<NativePopupWheelForwarder> self(this);
    const auto reset = qScopeGuard([self] {
        if (self)
            self->m_forwarding = false;
    });
    QCoreApplication::sendEvent(m_popup, &translated);
    wheel->setAccepted(translated.isAccepted());
    // A native compact can ignore Wheel to allow its popup's ScrollView to scroll.
    // It must never fall through to the owner's Iconbox or receive a second copy.
    return true;
}
