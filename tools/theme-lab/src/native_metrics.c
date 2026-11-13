/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_metrics.h"
#include <stdio.h>
int tl_metrics_size_delta(const TLNativeMetrics *reference,
                         const TLNativeMetrics *sample, int *width, int *height)
{
    if (!reference || !sample || !width || !height ||
        reference->width < 1 || reference->width > 65535 ||
        reference->height < 1 || reference->height > 65535 ||
        sample->width < 1 || sample->width > 65535 ||
        sample->height < 1 || sample->height > 65535 ||
        reference->scale_factor < 1 || reference->scale_factor > 16 ||
        sample->scale_factor < 1 || sample->scale_factor > 16) return -1;
    *width = sample->width * sample->scale_factor - reference->width * reference->scale_factor;
    *height = sample->height * sample->scale_factor - reference->height * reference->scale_factor;
    return 0;
}
static void piece_format(char *out,size_t capacity,const char *name,int known,const TLNativeRect *rect)
{
    if(!known)(void)snprintf(out,capacity,"%s: não medida",name);
    else (void)snprintf(out,capacity,"%s: %d,%d %d x %d",name,rect->x,rect->y,rect->width,rect->height);
}
void tl_metrics_format(char *text, size_t capacity, const char *origin,
                       const TLNativeMetrics *metrics)
{
    char scale[48], minimum[64], position[96], range[400];
    if (!text || !capacity) return;
    if (!origin) origin = "Controle";
    if (!metrics || metrics->width < 1 || metrics->height < 1) {
        (void)snprintf(text, capacity, "%s: aguardando medida nativa", origin);
        return;
    }
    if (metrics->scale_factor < 1 || metrics->scale_factor > 16)
        (void)snprintf(scale, sizeof(scale), "escala não medida");
    else (void)snprintf(scale, sizeof(scale), "escala %d", metrics->scale_factor);
    if (metrics->minimum_width < 0 || metrics->minimum_height < 0)
        (void)snprintf(minimum, sizeof(minimum), "Mínimo: toolkit não fornece");
    else (void)snprintf(minimum, sizeof(minimum), "Mínimo %d x %d",
                       metrics->minimum_width, metrics->minimum_height);
    if (metrics->position_valid)
        (void)snprintf(position, sizeof(position), "Posição local %d, %d",
                       metrics->position_x, metrics->position_y);
    else (void)snprintf(position, sizeof(position), "Posição local não medida");
    const char *font = metrics->font.kind == TL_FONT_NONE ? "sem texto próprio" :
        metrics->font.kind == TL_FONT_MEASURED ? metrics->font.description : "não medida";
    const char *sensitive = !metrics->sensitivity_known ? "não medida" :
        metrics->sensitive ? "habilitado" : "desabilitado";
    if(metrics->pieces.mask) {
        const TLNativePieces *p=&metrics->pieces;
        char slider[80],track[80],first[80],last[80];
        const char *source=p->source==1 ? "Motif 2.3.8 interno" :
            p->source==2 ? "GTK3 3.24.49 verificado; caixas de margem" : "Fonte não identificada";
        piece_format(slider,sizeof(slider),"Cursor",p->mask&1,&p->slider);
        piece_format(track,sizeof(track),"Trilho/área cursor",p->mask&2,&p->track);
        piece_format(first,sizeof(first),"Seta inicial",p->mask&4,&p->arrows[0]);
        piece_format(last,sizeof(last),"Seta final",p->mask&8,&p->arrows[1]);
        (void)snprintf(range,sizeof(range),
            "%s; caixas locais (não silhuetas)\n%s\n%s\n%s\n%s",source,slider,track,first,last);
    } else if (metrics->range.valid)
        (void)snprintf(range,sizeof(range),
            "Cursor (caixa de margem): intervalo %d..%d (%d px lógicos)\nÁrea GtkRange %d,%d: %d x %d (inclui setas)\nCoordenadas da janela GTK; seta/trilho isolados não medidos.",
            metrics->range.slider_start,metrics->range.slider_end,
            metrics->range.slider_end-metrics->range.slider_start,
            metrics->range.area_x,metrics->range.area_y,
            metrics->range.area_width,metrics->range.area_height);
    else (void)snprintf(range,sizeof(range),"Peças internas: não medidas");
    (void)snprintf(text, capacity,
        "%s: %d x %d; %s\n%s; preferido %d x %d\n%s\nFonte: %s\nSensibilidade: %s\n%s",
        origin, metrics->width, metrics->height, scale, minimum,
        metrics->natural_width, metrics->natural_height, position, font, sensitive,range);
}
