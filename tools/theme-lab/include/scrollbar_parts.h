/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_SCROLLBAR_PARTS_H
#define TL_SCROLLBAR_PARTS_H
#include <stddef.h>
#include <json-c/json.h>
/* Sparse overrides: an unset field inherits the family geometry. Values are
   proposed measurements, never historical defaults or native capabilities. */
#define TL_SCROLL_PART_COUNT 5
#define TL_SCROLL_PARAM_COUNT 3
typedef enum { TL_SCROLL_ARROW, TL_SCROLL_ARROW_BUTTON, TL_SCROLL_TROUGH,
               TL_SCROLL_THUMB, TL_SCROLL_FITTING } TLScrollPart;
#define TL_PART_STATE_COUNT 6
/* Sparse per-state relief: 0 absent, 1 flat, 2 raised, 3 sunken. */
typedef struct {
    unsigned int present;
    int values[TL_SCROLL_PARAM_COUNT];
    unsigned int relief_present;
    int relief[TL_PART_STATE_COUNT];
} TLPartRecipe;
extern const char *const tl_part_state_ids[TL_PART_STATE_COUNT];
int tl_part_relief_set(TLPartRecipe *part,int state,int relief);
int tl_part_relief_validate(const TLPartRecipe *part);
int tl_part_relief_decode(TLPartRecipe *part,json_object *object);
json_object *tl_part_relief_encode(const TLPartRecipe *part);
typedef struct { TLPartRecipe parts[TL_SCROLL_PART_COUNT]; } TLScrollbarParts;
extern const char *const tl_scroll_part_ids[TL_SCROLL_PART_COUNT];
const char *tl_scroll_part_field(TLScrollPart part, int field);
int tl_scroll_parts_set(TLScrollbarParts *parts, TLScrollPart part,
                        int field, int value); /* -1 clears just this override. */
int tl_scroll_parts_any(const TLScrollbarParts *parts);
int tl_scroll_parts_validate(const TLScrollbarParts *parts, char *error, size_t capacity);
int tl_scroll_parts_decode(TLScrollbarParts *parts, json_object *object,
                          char *error, size_t capacity);
json_object *tl_scroll_parts_encode(const TLScrollbarParts *parts);
#endif
