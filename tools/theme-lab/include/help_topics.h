/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_HELP_TOPICS_H
#define TL_HELP_TOPICS_H
#define TL_HELP_TOPIC_COUNT 10
#define TL_HELP_LEVEL_COUNT 3
const char *tl_help_topic_title(int topic);
const char *tl_help_level_title(int level);
const char *tl_help_topic_text(int topic,int level);
#endif
