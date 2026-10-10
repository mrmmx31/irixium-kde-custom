// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QWindow>

// Qt 6.8.2/XCB grabs a Popup.Window's owner, but does not forward Wheel.
// This adapter is explicitly bound to one tray popup; it implements no action.
class NativePopupWheelForwarder : public QObject {
    Q_OBJECT
    Q_PROPERTY(QWindow* ownerWindow READ ownerWindow WRITE setOwnerWindow NOTIFY ownerWindowChanged)
    Q_PROPERTY(QWindow* popupWindow READ popupWindow WRITE setPopupWindow NOTIFY popupWindowChanged)
    Q_PROPERTY(bool enabled READ enabled WRITE setEnabled NOTIFY enabledChanged)
    Q_PROPERTY(bool supported READ supported CONSTANT)
public:
    explicit NativePopupWheelForwarder(QObject* parent = nullptr);
    ~NativePopupWheelForwarder() override;
    QWindow* ownerWindow() const { return m_owner; }
    QWindow* popupWindow() const { return m_popup; }
    bool enabled() const { return m_enabled; }
    bool supported() const { return m_supported; }
    void setOwnerWindow(QWindow* window);
    void setPopupWindow(QWindow* window);
    void setEnabled(bool enabled);
signals:
    void ownerWindowChanged();
    void popupWindowChanged();
    void enabledChanged();
protected:
    bool eventFilter(QObject* receiver, QEvent* event) override;
private:
    void updateFilter();
    QPointer<QWindow> m_owner, m_popup, m_watched;
    QMetaObject::Connection m_ownerDestroyed, m_popupDestroyed;
    bool m_enabled = false, m_forwarding = false;
    const bool m_supported;
};
