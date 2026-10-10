# SPDX-License-Identifier: GPL-3.0-or-later
CC ?= cc
PKG_CONFIG ?= pkg-config
BUILD ?= build
CPPFLAGS += -Iinclude $(shell $(PKG_CONFIG) --cflags json-c libpng libcrypto)
CFLAGS ?= -O2 -g
CFLAGS += -std=c99 -Wall -Wextra -Werror -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700
LDLIBS += -lXm -lXt -lX11 $(shell $(PKG_CONFIG) --libs json-c libpng libcrypto) -lm
SOURCES = src/main.c src/controller.c src/model.c src/view.c src/preview_event.c
.PHONY: all check clean native-colors
all: $(BUILD)/theme-lab
native-colors:
	cmake -S native-build -B "$(BUILD)/native-colors"
	cmake --build "$(BUILD)/native-colors" --parallel 2
$(BUILD):
	mkdir -p "$@"
$(BUILD)/theme-lab: $(SOURCES) include/theme_lab.h include/controller.h include/preview_event.h Makefile | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) $(SOURCES) $(LDLIBS) -o "$@"
$(BUILD)/model-test: tests/model_test.c src/model.c include/theme_lab.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/model_test.c src/model.c $(shell $(PKG_CONFIG) --libs json-c) -lm -o "$@"
$(BUILD)/preview-event-test: tests/preview_event_test.c src/preview_event.c include/preview_event.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/preview_event_test.c src/preview_event.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
check: $(BUILD)/model-test $(BUILD)/preview-event-test
	cd "$(CURDIR)/../.." && "$(abspath $(BUILD))/model-test"
	"$(BUILD)/preview-event-test"
	/usr/bin/python3 -B tests/test_backend.py
	/usr/bin/python3 -B tests/test_preview_scene.py
clean:
	rm -f "$(BUILD)/theme-lab" "$(BUILD)/model-test" "$(BUILD)/preview-event-test"
