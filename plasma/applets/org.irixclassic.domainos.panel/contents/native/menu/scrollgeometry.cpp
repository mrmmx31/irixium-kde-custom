// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
#include "scrollgeometry.h"
#include <QApplication>
#include <QStyle>
#include <QThread>
#include <cmath>
#include <limits>
namespace {
QVariantMap rectangle(const QRect &r) { return {{"x",r.x()},{"y",r.y()},{"width",r.width()},{"height",r.height()}}; }
QStyle *style() { auto *app=qobject_cast<QApplication*>(QCoreApplication::instance()); return app ? app->style() : nullptr; }
}
bool NativeScrollGeometry::option(const QVariantMap &input, QStyleOptionSlider &opt) const {
 if (!style() || QThread::currentThread()!=QCoreApplication::instance()->thread()) return false;
 for (const char *key : {"width","height","minimum","maximum","value","paintMargins","textureWidth","textureHeight"}) {
  const double v=input.value(key,0).toDouble();
  if (!std::isfinite(v) || std::abs(v)>std::numeric_limits<int>::max()/2) return false;
 }
 const bool horizontal=input.value("horizontal").toBool();
 const int width=int(input.value("width").toDouble()),height=int(input.value("height").toDouble());
 const int textureWidth=input.value("textureWidth").toInt(),textureHeight=input.value("textureHeight").toInt(),margin=input.value("paintMargins").toInt();
 if (width<=0 || height<=0 || margin<0) return false;
 // These are logical coordinates. DPR changes the backing image, not the
 // QStyleOption rect (qqc2-desktop-style6.13.0 initStyleOption/updatePolish).
 opt.rect=QRect(margin,0,(textureWidth>0?textureWidth:width)-2*margin,textureHeight>0?textureHeight:height);
 if (opt.rect.isEmpty()) return false;
 opt.minimum=qMax(0,input.value("minimum").toInt());
 opt.maximum=qMax(0,input.value("maximum").toInt());
 opt.pageStep=qMax(0,horizontal?width:height);
 opt.orientation=horizontal?Qt::Horizontal:Qt::Vertical;
 // Desktop's horizontal ScrollBar explicitly prevents mirroring.
 opt.direction=input.value("mirrored").toBool()&&!horizontal?Qt::RightToLeft:Qt::LeftToRight;
 opt.sliderPosition=opt.sliderValue=input.value("value").toInt();
 opt.subControls=QStyle::SC_All;
 opt.activeSubControls=QStyle::SC_None;
 opt.upsideDown=false;
 opt.state=QStyle::State_Active|QStyle::State_Raised;
 if (input.value("enabled",true).toBool()) opt.state|=QStyle::State_Enabled;
 if (horizontal) opt.state|=QStyle::State_Horizontal;
 opt.palette=QApplication::palette();
 return true;
}
QVariantMap NativeScrollGeometry::evaluate(const QVariantMap &input) const {
 QStyleOptionSlider opt;
 if (!option(input,opt)) return {{"valid",false},{"reason","invalid_shape_or_no_native_application_style"}};
 auto *s=style();
 const QRect up=s->subControlRect(QStyle::CC_ScrollBar,&opt,QStyle::SC_ScrollBarSubLine),down=s->subControlRect(QStyle::CC_ScrollBar,&opt,QStyle::SC_ScrollBarAddLine),handle=s->subControlRect(QStyle::CC_ScrollBar,&opt,QStyle::SC_ScrollBarSlider),groove=s->subControlRect(QStyle::CC_ScrollBar,&opt,QStyle::SC_ScrollBarGroove);
 const bool valid=!up.isEmpty()&&!down.isEmpty()&&!handle.isEmpty()&&!groove.isEmpty()&&opt.rect.contains(up)&&opt.rect.contains(down)&&opt.rect.contains(handle)&&opt.rect.contains(groove);
 return {{"valid",valid},{"reason",valid?"":"missing_required_subcontrol_or_outside_shape"},{"style",s->metaObject()->className()},{"up",rectangle(up)},{"down",rectangle(down)},{"handle",rectangle(handle)},{"groove",rectangle(groove)},{"addPage",rectangle(s->subControlRect(QStyle::CC_ScrollBar,&opt,QStyle::SC_ScrollBarAddPage))},{"subPage",rectangle(s->subControlRect(QStyle::CC_ScrollBar,&opt,QStyle::SC_ScrollBarSubPage))}};
}
QString NativeScrollGeometry::hitTest(const QVariantMap &input,qreal x,qreal y) const {
 QStyleOptionSlider opt;
 if (!option(input,opt)||!std::isfinite(x)||!std::isfinite(y)
     ||std::abs(x)>std::numeric_limits<int>::max()/2
     ||std::abs(y)>std::numeric_limits<int>::max()/2) return "none";
 switch(style()->hitTestComplexControl(QStyle::CC_ScrollBar,&opt,QPoint(int(x),int(y)))) {
 case QStyle::SC_ScrollBarSubLine:return "up";
 case QStyle::SC_ScrollBarAddLine:return "down";
 case QStyle::SC_ScrollBarSlider:return "handle";
 case QStyle::SC_ScrollBarSubPage:return "upPage";
 case QStyle::SC_ScrollBarAddPage:return "downPage";
 default:return "none";
 }
}
