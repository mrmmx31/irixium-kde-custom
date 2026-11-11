CC ?= cc
CPPFLAGS += -Iinclude $(shell pkg-config --cflags json-c)
CFLAGS ?= -O2 -g
CFLAGS += -std=c99 -Wall -Wextra -Werror -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700
LDLIBS += -lXm -lXt -lX11 $(shell pkg-config --libs json-c libcrypto)
SOURCES = src/main.c src/model.c src/controller.c src/view.c src/editor.c
all: build/work-board
build/work-board: $(SOURCES) include/board.h include/view.h include/editor.h
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SOURCES) -o $@ $(LDLIBS)
check: build/work-board
	python3 -B tests/test_store.py
check-native: build/work-board
	python3 -B tests/test_native.py
check-editing: build/work-board
	python3 -B tests/test_editing.py
clean:
	rm -rf build
.PHONY: all check check-native check-editing clean
