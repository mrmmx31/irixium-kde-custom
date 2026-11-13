// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <QObject>
#include <QVariantMap>
#include <QStyleOptionSlider>
class NativeScrollGeometry : public QObject {
 Q_OBJECT
public:
 explicit NativeScrollGeometry(QObject *parent = nullptr) : QObject(parent) {}
 Q_INVOKABLE QVariantMap evaluate(const QVariantMap &input) const;
 Q_INVOKABLE QString hitTest(const QVariantMap &input, qreal x, qreal y) const;
private:
 bool option(const QVariantMap &input, QStyleOptionSlider &result) const;
};
