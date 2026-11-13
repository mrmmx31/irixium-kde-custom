/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_metrics.h"
#include <assert.h>
#include <string.h>
int main(void)
{
    TLNativeMetrics reference = {0}, sample = {0};
    int width = 123, height = 456;
    char text[512], tiny[1];
    reference.width = 240; reference.height = 30; reference.scale_factor = 1;
    sample.width = 120; sample.height = 15; sample.scale_factor = 2;
    assert(!tl_metrics_size_delta(&reference, &sample, &width, &height));
    assert(width == 0 && height == 0); /* unequal logical sizes, equal physical size */
    sample.scale_factor = 1;
    assert(!tl_metrics_size_delta(&reference, &sample, &width, &height));
    assert(width == -120 && height == -15);
    sample.scale_factor = 0; width = 123; height = 456;
    assert(tl_metrics_size_delta(&reference, &sample, &width, &height) == -1);
    assert(width == 123 && height == 456); /* absence is not an equality result */
    sample.scale_factor = 17;
    assert(tl_metrics_size_delta(&reference, &sample, &width, &height) == -1);
    sample.scale_factor = 2; sample.width = 0;
    assert(tl_metrics_size_delta(&reference, &sample, &width, &height) == -1);
    sample.width = 120; sample.minimum_width = sample.minimum_height = -1;
    sample.position_valid = 1; sample.position_x = 16; sample.position_y = 36;
    tl_metrics_format(text, sizeof(text), "Amostra", &sample);
    assert(strstr(text, "toolkit não fornece"));
    assert(strstr(text, "Posição local 16, 36"));
    sample.position_valid = 0; sample.scale_factor = 0;
    tl_metrics_format(text, sizeof(text), "Amostra", &sample);
    assert(strstr(text, "escala não medida"));
    assert(strstr(text, "Posição local não medida"));
    sample.sensitivity_known=1;sample.sensitive=0;
    tl_metrics_format(text,sizeof(text),"Amostra",&sample);
    assert(strstr(text,"Sensibilidade: desabilitado"));
    sample.range.valid=1;sample.range.slider_start=55;sample.range.slider_end=100;
    sample.range.area_x=16;sample.range.area_y=36;sample.range.area_width=120;sample.range.area_height=15;
    tl_metrics_format(text,sizeof(text),"Amostra",&sample);
    assert(strstr(text,"55..100 (45 px lógicos)"));
    assert(strstr(text,"inclui setas"));
    sample.range.valid=0;sample.pieces.mask=1;
    sample.pieces.slider=(TLNativeRect){12,2,30,11};
    tl_metrics_format(text,sizeof(text),"Amostra",&sample);
    assert(strstr(text,"Cursor: 12,2 30 x 11"));
    assert(strstr(text,"Seta inicial: não medida"));
    assert(!strstr(text,"Seta inicial: 0"));
    sample.pieces.source=2;sample.range.valid=1;
    tl_metrics_format(text,sizeof(text),"Amostra",&sample);
    assert(strstr(text,"GTK3 3.24.49 verificado; caixas de margem"));
    assert(!strstr(text,"isolados não medidos"));
    tl_metrics_format(tiny, sizeof(tiny), NULL, &sample); assert(!tiny[0]);
    tl_metrics_format(NULL, 0, NULL, NULL);
    return 0;
}
