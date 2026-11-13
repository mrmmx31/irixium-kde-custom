/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_UI_EXPORT_REVIEW_H
#define TL_UI_EXPORT_REVIEW_H
#include <Xm/Xm.h>
typedef struct TLExportReview TLExportReview;
TLExportReview *tl_export_review_create(Widget shell);
Widget tl_export_review_dialog(TLExportReview *review);
void tl_export_review_open(TLExportReview *review,const char *text);
void tl_export_review_destroy(TLExportReview *review);
#endif
