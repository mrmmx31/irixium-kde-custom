# SPDX-License-Identifier: GPL-3.0-or-later
CC ?= cc
PKG_CONFIG ?= pkg-config
BUILD ?= build
CPPFLAGS += -Iinclude $(shell $(PKG_CONFIG) --cflags json-c libpng libcrypto)
CFLAGS ?= -O2 -g
CFLAGS += -std=c99 -Wall -Wextra -Werror -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700
LDLIBS += -lXm -lXt -lX11 -ldl $(shell $(PKG_CONFIG) --libs json-c libpng libcrypto xcomposite) -lm
NATIVE_HOST_SOURCES = native-gtk4/focus.c
EDITOR_SOURCES = src/view/control_catalog.c src/editor/view.c src/editor/store.c src/view/ui_menu_hints.c src/view/manual_paint_view.c src/view/manual_paint_recovery.c src/paint/model.c
HISTORY_HEADERS = include/project_history.h include/project_history_store.h include/project_session.h include/project_history_controls.h
EDITOR_HEADERS = include/control_catalog.h include/text_editor.h src/editor/internal.h native-gtk4/canvas_identity.h native-gtk4/focus.h include/manual_paint.h include/manual_paint_view.h include/manual_paint_recovery.h
SOURCES = src/main.c src/controller.c src/controller/owned_processes.c src/controller/generated_preview.c src/controller/project_session.c src/persistence/project_history_store.c src/model/project_history.c src/model/code_search.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c src/model/control_availability.c src/model/gtk2_r584_catalog.c src/view.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c src/view/ui_help.c src/view/ui_export_review.c src/model/help_topics.c src/view/project_history_controls.c src/view/part_relief_editor.c src/preview_event.c src/native_metrics.c src/native_font_motif.c src/font_policy_motif.c src/native_pair_motif.c src/native_parts_motif.c $(EDITOR_SOURCES) $(NATIVE_HOST_SOURCES)
.PHONY: all check check-qt5-scrollbar-xephyr check-qt6-scrollbar-native check-kvantum-recipe check-native-metrics check-controller-spin check-editor check-scroll-parts check-scroll-trough check-trough-pixels check-thumb-pixels check-scroll-thumb check-scroll-fitting check-fitting-pixels check-axis-lock clean native-colors
all: check-samples $(BUILD)/theme-lab gtk4-host
.PHONY: gtk2-pressure
gtk2-pressure: $(BUILD)/libtheme-lab-gtk2-press.so
.PHONY: gtk4-host
gtk4-host: $(BUILD)/libtheme-lab-gtk4-host.so
$(BUILD)/libtheme-lab-gtk4-host.so: native-gtk4/host.c native-gtk4/host.h | $(BUILD)
	$(CC) $(CFLAGS) -fPIC -shared native-gtk4/host.c -lX11 -o "$@"
$(BUILD)/libtheme-lab-gtk2-press.so: native-gtk2/press.c native-gtk2/press.h | $(BUILD)
	$(CC) $(CFLAGS) -Wno-deprecated-declarations -fPIC -shared $(shell $(PKG_CONFIG) --cflags gtk+-2.0) native-gtk2/press.c $(shell $(PKG_CONFIG) --libs gtk+-2.0) -o "$@"
.PHONY: check-font-policy
$(BUILD)/font-policy-test: tests/font_policy_motif_test.c src/font_policy_motif.c include/font_policy_motif.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/font_policy_motif_test.c src/font_policy_motif.c -lXm -lXt -lX11 -o "$@"
check-font-policy: $(BUILD)/font-policy-test
	xvfb-run -a "$<"
.PHONY: check-font-mapping
$(BUILD)/font-mapping-test: tests/font_mapping_motif_test.c src/font_policy_motif.c include/font_policy_motif.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/font_mapping_motif_test.c src/font_policy_motif.c -lXm -lXt -lX11 -o "$@"
check-font-mapping: $(BUILD)/font-mapping-test
	xvfb-run -a /usr/bin/python3 -B tests/test_font_mapping_motif.py "$(abspath $(BUILD))/font-mapping-test"
include/sample_controls.h: sample_controls.json sample_contract.py
	/usr/bin/python3 -B sample_contract.py
check-samples: include/sample_controls.h
	/usr/bin/python3 -B sample_contract.py --check
$(BUILD)/metrics-comparison-test: tests/metrics_comparison_test.c src/native_metrics.c include/native_metrics.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/metrics_comparison_test.c src/native_metrics.c -o "$@"
check-metrics-comparison: $(BUILD)/metrics-comparison-test
	"$(BUILD)/metrics-comparison-test"
native-colors:
	cmake -S native-build -B "$(BUILD)/native-colors"
	cmake --build "$(BUILD)/native-colors" --parallel 2
$(BUILD):
	mkdir -p "$@"
$(BUILD)/theme-lab: $(SOURCES) $(EDITOR_HEADERS) $(HISTORY_HEADERS) include/code_search.h include/owned_processes.h include/native_font_motif.h include/font_policy_motif.h include/native_pair_motif.h include/native_parts_motif.h include/ui_hints.h include/ui_help.h include/ui_export_review.h include/help_topics.h include/sample_controls.h include/theme_lab.h include/part_relief_editor.h include/scrollbar_parts.h include/control_dimensions.h include/control_availability.h include/gtk2_r584_catalog.h include/controller.h include/generated_preview.h include/preview_event.h include/native_metrics.h Makefile | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) $(SOURCES) $(LDLIBS) -o "$@"
$(BUILD)/model-test: tests/model_test.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c include/theme_lab.h include/part_relief_editor.h include/scrollbar_parts.h include/control_dimensions.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/model_test.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c $(shell $(PKG_CONFIG) --libs json-c) -lm -o "$@"
$(BUILD)/preview-event-test: tests/preview_event_test.c src/preview_event.c include/preview_event.h include/native_metrics.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/preview_event_test.c src/preview_event.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
$(BUILD)/preview-event-file-test: tests/preview_event_file_test.c src/preview_event.c include/preview_event.h include/native_metrics.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/preview_event_file_test.c src/preview_event.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
$(BUILD)/generated-preview-test: tests/generated_preview_test.c src/controller/generated_preview.c include/generated_preview.h src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/generated_preview_test.c src/controller/generated_preview.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c $(shell $(PKG_CONFIG) --libs json-c) -lm -o "$@"
check: $(BUILD)/model-test $(BUILD)/preview-event-test $(BUILD)/code-search-test
	cd "$(CURDIR)/../.." && "$(abspath $(BUILD))/model-test"
	"$(BUILD)/preview-event-test"
	LC_ALL=C.UTF-8 "$(BUILD)/code-search-test"
	/usr/bin/python3 -B tests/test_backend.py
	/usr/bin/python3 -B tests/test_preview_scene.py
	/usr/bin/python3 -B tests/test_qt5_scrollbar_recipe.py
	/usr/bin/python3 -B tests/test_qt6_scrollbar_recipe.py
check-manual-paint-model: $(BUILD)/manual-paint-model-test
	"$(BUILD)/manual-paint-model-test" "$(abspath $(BUILD))/manual-paint-model-test.json"
$(BUILD)/manual-paint-model-test: tests/manual_paint_model_test.c src/paint/model.c include/manual_paint.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/manual_paint_model_test.c src/paint/model.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
.PHONY: check-manual-paint-model
check-qt5-scrollbar-xephyr:
	/usr/bin/python3 -B tests/test_qt5_scrollbar_xephyr.py
check-qt6-scrollbar-native:
	/usr/bin/python3 -B tests/test_qt6_scrollbar_public_native.py
check-kvantum-recipe:
	cd "$(CURDIR)/../.." && /usr/bin/python3 -B -m unittest tools.theme-lab.tests.test_kvantum_recipe -v
$(BUILD)/native-metrics-view: tests/native_metrics_view.c tests/ui_help_flow.c tests/dynamic_hints.c src/view.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c src/view/ui_help.c src/view/ui_export_review.c src/model/help_topics.c src/view/project_history_controls.c src/view/part_relief_editor.c src/model.c src/model/code_search.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c src/model/control_availability.c src/model/gtk2_r584_catalog.c src/native_metrics.c src/native_font_motif.c src/font_policy_motif.c src/native_pair_motif.c src/native_parts_motif.c $(EDITOR_SOURCES) $(NATIVE_HOST_SOURCES) $(EDITOR_HEADERS) include/control_availability.h include/gtk2_r584_catalog.h include/native_font_motif.h include/font_policy_motif.h include/native_pair_motif.h include/native_parts_motif.h include/ui_hints.h include/ui_help.h include/ui_export_review.h include/help_topics.h include/sample_controls.h include/theme_lab.h include/part_relief_editor.h include/scrollbar_parts.h include/control_dimensions.h include/native_metrics.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/native_metrics_view.c tests/ui_help_flow.c tests/dynamic_hints.c src/view.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c src/view/ui_help.c src/view/ui_export_review.c src/model/help_topics.c src/view/project_history_controls.c src/view/part_relief_editor.c src/model.c src/model/code_search.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c src/model/control_availability.c src/model/gtk2_r584_catalog.c src/native_metrics.c src/native_font_motif.c src/font_policy_motif.c src/native_pair_motif.c src/native_parts_motif.c $(EDITOR_SOURCES) $(NATIVE_HOST_SOURCES) $(LDLIBS) -o "$@"
check-native-metrics: $(BUILD)/native-metrics-view
	xvfb-run -a "$(BUILD)/native-metrics-view"
	xvfb-run -a /usr/bin/python3 -B tests/test_native_metrics.py
$(BUILD)/controller-spin-probe: tests/controller_spin_probe.c tests/import_exec_gate.c $(filter-out src/main.c,$(SOURCES)) $(EDITOR_HEADERS) $(HISTORY_HEADERS) include/owned_processes.h include/native_font_motif.h include/font_policy_motif.h include/native_pair_motif.h include/native_parts_motif.h include/ui_hints.h include/ui_help.h include/ui_export_review.h include/help_topics.h include/sample_controls.h include/theme_lab.h include/part_relief_editor.h include/scrollbar_parts.h include/control_dimensions.h include/native_metrics.h Makefile | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/controller_spin_probe.c tests/import_exec_gate.c $(filter-out src/main.c,$(SOURCES)) -Wl,--wrap=tl_view_set_anchor -Wl,--wrap=execv -Wl,--wrap=tl_view_create -Wl,--wrap=tl_part_editor_update -Wl,--wrap=tl_part_editor_capture $(LDLIBS) -o "$@"
check-journal-capacity: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --journal-capacity

check-quit-recovery: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --quit-recovery

check-controller-spin: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe"
$(BUILD)/editor-store-probe: tests/editor_store_probe.c src/editor/store.c $(EDITOR_HEADERS) | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/editor_store_probe.c src/editor/store.c -Wl,--wrap=fsync $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
check-editor: $(BUILD)/controller-spin-probe $(BUILD)/editor-store-probe
	/usr/bin/python3 -B tests/test_editor_store.py "$(abspath $(BUILD))/editor-store-probe"
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --editor
clean:
	rm -f "$(BUILD)/theme-lab" "$(BUILD)/model-test" "$(BUILD)/preview-event-test" "$(BUILD)/code-search-test" "$(BUILD)/native-metrics-view" "$(BUILD)/controller-spin-probe"

$(BUILD)/code-search-test: tests/code_search_test.c src/model/code_search.c include/code_search.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/code_search_test.c src/model/code_search.c -o "$@"

check-scroll-parts: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --piece

check-scroll-trough: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --piece-trough

check-trough-pixels: native-colors
	/usr/bin/python3 -B tests/test_trough_native.py

check-thumb-pixels: native-colors
	/usr/bin/python3 -B tests/test_trough_native.py --thumb

check-scroll-thumb: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --piece-thumb

check-scroll-fitting: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --piece-fitting

check-fitting-pixels: native-colors
	/usr/bin/python3 -B tests/test_trough_native.py --fitting

check-axis-lock: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --axis-lock

.PHONY: check-motif-internals check-metrics-comparison
$(BUILD)/motif-version-mismatch.so: tests/motif_version_mismatch.c | $(BUILD)
	$(CC) $(CFLAGS) -shared -fPIC "$<" -o "$@"
check-motif-internals: $(BUILD)/native-metrics-view $(BUILD)/motif-version-mismatch.so
	xvfb-run -a "$(BUILD)/native-metrics-view"
	xvfb-run -a env TL_TEST_UNSUPPORTED_MOTIF=1 LD_PRELOAD="$(abspath $(BUILD))/motif-version-mismatch.so" "$(BUILD)/native-metrics-view"

.PHONY: check-native-comparison
check-native-comparison: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --comparison

$(BUILD)/part-states-test: tests/part_states_test.c src/model/scrollbar_parts.c src/model/part_states.c include/scrollbar_parts.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/part_states_test.c src/model/scrollbar_parts.c src/model/part_states.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
.PHONY: check-part-states
check-part-states: $(BUILD)/part-states-test
	"$(BUILD)/part-states-test"

.PHONY: check-state-relief-css
check-state-relief-css:
	xvfb-run -a /usr/bin/python3 -B tests/test_state_relief_css.py

.PHONY: check-arrow-relief-pixels
check-arrow-relief-pixels: native-colors
	/usr/bin/python3 -B tests/test_arrow_relief_native.py

$(BUILD)/part-relief-editor-test: tests/part_relief_editor_test.c src/view/part_relief_editor.c src/model/part_states.c include/part_relief_editor.h include/scrollbar_parts.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/part_relief_editor_test.c src/view/part_relief_editor.c src/model/part_states.c -lXm -lXt -lX11 $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
.PHONY: check-part-relief-editor
check-part-relief-editor: $(BUILD)/part-relief-editor-test
	xvfb-run -a "$(BUILD)/part-relief-editor-test"

.PHONY: check-relief-controller
check-relief-controller: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --relief
check-arrow-context-pixels:
	/usr/bin/python3 -B tests/test_arrow_relief_context_native.py
check-arrow-hover-pixels:
	/usr/bin/python3 -B tests/test_arrow_relief_hover_native.py
	/usr/bin/python3 -B tests/test_arrow_relief_hover_backdrop_native.py

.PHONY: check-thumb-relief-controller
check-thumb-relief-controller: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --thumb-relief

.PHONY: check-fitting-state-paint
check-fitting-state-paint:
	/usr/bin/python3 -B tests/test_fitting_states_native.py

.PHONY: check-fitting-relief-controller
check-fitting-relief-controller: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --fitting-relief

.PHONY: check-preview-readiness
check-preview-readiness: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --preview-readiness

$(BUILD)/project-history-test: tests/project_history_test.c src/model/project_history.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c include/project_history.h include/theme_lab.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/project_history_test.c src/model/project_history.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
.PHONY: check-project-history
check-project-history: $(BUILD)/project-history-test
	"$(BUILD)/project-history-test"

$(BUILD)/project-history-store-test: tests/project_history_store_test.c src/persistence/project_history_store.c src/model/project_history.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c include/project_history_store.h include/project_history.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/project_history_store_test.c src/persistence/project_history_store.c src/model/project_history.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
.PHONY: check-project-history-store
check-project-history-store: $(BUILD)/project-history-store-test
	"$(BUILD)/project-history-store-test"

HISTORY_SOURCES = src/controller/project_session.c src/persistence/project_history_store.c src/model/project_history.c src/model.c src/model/scrollbar_parts.c src/model/part_states.c src/model/control_dimensions.c
$(BUILD)/project-session-test: tests/project_session_test.c $(HISTORY_SOURCES) include/project_session.h include/project_history_store.h include/project_history.h include/theme_lab.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/project_session_test.c $(HISTORY_SOURCES) $(shell $(PKG_CONFIG) --libs json-c) -o "$@"
.PHONY: check-project-session
check-project-session: $(BUILD)/project-session-test
	"$(BUILD)/project-session-test"

.PHONY: check-project-history-controller
check-project-history-controller: $(BUILD)/controller-spin-probe
	/usr/bin/python3 -B tests/test_controller_spin.py "$(abspath $(BUILD))/controller-spin-probe" --project-history

$(BUILD)/ui-hints-native: tests/ui_hints_native.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c include/ui_hints.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/ui_hints_native.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c -lXm -lXt -lX11 -o "$@"
.PHONY: check-ui-hints
check-ui-hints: $(BUILD)/ui-hints-native $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 xvfb-run -a "$<"
	LC_ALL=C.UTF-8 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/native-metrics-view"

.PHONY: check-ui-help
check-ui-help: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 TL_HELP_ONLY=1 xvfb-run -a "$<"

.PHONY: check-paint-hints
check-paint-hints: $(BUILD)/native-metrics-view
	TMPDIR="$(HOME)/tempia/domainos-theme-work" LC_ALL=C.UTF-8 TL_PAINT_HINTS_ONLY=1 xvfb-run -a -s '-screen 0 1600x900x24' "$<"

.PHONY: check-paint-reference-copy
check-paint-reference-copy: $(BUILD)/native-metrics-view
	TMPDIR="$(HOME)/tempia/domainos-theme-work" LC_ALL=C.UTF-8 TL_PAINT_REFERENCE_ONLY=1 xvfb-run -a -s '-screen 0 1600x900x24' "$<"

.PHONY: check-control-availability
check-control-availability:
	TMPDIR="$(HOME)/tempia/domainos-theme-work" /usr/bin/python3 -B tests/test_control_availability_contract.py

.PHONY: check-gtk2-r584-catalog check-paint-sample-role
$(BUILD)/gtk2-r584-catalog-test: tests/gtk2_r584_catalog_test.c src/model/gtk2_r584_catalog.c include/gtk2_r584_catalog.h include/theme_lab.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/gtk2_r584_catalog_test.c src/model/gtk2_r584_catalog.c $(shell $(PKG_CONFIG) --libs json-c libcrypto) -o "$@"
check-gtk2-r584-catalog: $(BUILD)/gtk2-r584-catalog-test
	"$<" "$(CURDIR)/tests/fixtures/gtk2-r584" "$(CURDIR)/../../docs/review/I167-GTK2-USER-PALETTE-UPDATE-20261028-R584.json" "$(HOME)/.local/share/irixium/gtk2-palette/fe95ddd38ef6f61a941d420f6d3d33f376b4d34032c3fc2cf9cad77834710755/manifest.json"
check-paint-sample-role:
	/usr/bin/python3 -B tests/test_paint_sample_role_contract.py

.PHONY: check-paint-control-catalog
check-paint-control-catalog: $(BUILD)/native-metrics-view
	TMPDIR="$(HOME)/tempia/domainos-theme-work" LC_ALL=C.UTF-8 TL_PAINT_CATALOG_ONLY=1 xvfb-run -a -s '-screen 0 1650x900x24' "$<"

.PHONY: check-paint-r584
check-paint-r584: $(BUILD)/native-metrics-view
	TMPDIR="$(HOME)/tempia/domainos-theme-work" LC_ALL=C.UTF-8 TL_PAINT_R584_ONLY=1 xvfb-run -a -s '-screen 0 1650x900x24' "$<"

.PHONY: check-paint-selection
check-paint-selection: $(BUILD)/native-metrics-view
	TMPDIR="$(HOME)/tempia/domainos-theme-work" LC_ALL=C.UTF-8 TL_PAINT_SELECTION_ONLY=1 xvfb-run -a -s '-screen 0 1650x900x24' "$<"

.PHONY: check-export-review
check-export-review: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 TL_EXPORT_REVIEW_ONLY=1 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/native-metrics-view"

.PHONY: check-file-dialog-hints
check-file-dialog-hints: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/native-metrics-view" --file-dialog

.PHONY: check-file-dialog-hover
check-file-dialog-hover: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 TL_FILE_HINTS_ONLY=1 TL_FILE_HOVER=1 xvfb-run -a "$<"

.PHONY: check-editor-menu-hover
check-editor-menu-hover: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 TL_EDITOR_HOVER=1 TL_EDITOR_MOUSE=1 TL_EDITOR_LIVE_PALETTE=1 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/native-metrics-view" --file-dialog

.PHONY: check-history-hint-hover
check-history-hint-hover: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 TL_HISTORY_HOVER=1 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/native-metrics-view"

.PHONY: check-foreign-control-hints
check-foreign-control-hints:
	T07_PRIVATE_PROBE=1 NO_AT_BRIDGE=1 LC_ALL=C.UTF-8 xvfb-run -a /usr/bin/python3 -B tests/probe_control_hints.py --family gtk2
	T07_PRIVATE_PROBE=1 NO_AT_BRIDGE=1 LC_ALL=C.UTF-8 xvfb-run -a /usr/bin/python3 -B tests/probe_control_hints.py --family gtk3

.PHONY: check-gtk3-hint-hover check-gtk2-hint-hover
check-gtk3-hint-hover:
	T07_PRIVATE_PROBE=1 NO_AT_BRIDGE=1 GTK_MODULES='' LC_ALL=C.UTF-8 xvfb-run -a -s '-screen 0 940x700x24' /usr/bin/python3 -B tests/probe_gtk_hint_hover.py --family gtk3
check-gtk2-hint-hover:
	T07_PRIVATE_PROBE=1 NO_AT_BRIDGE=1 GTK_MODULES='' LC_ALL=C.UTF-8 xvfb-run -a -s '-screen 0 940x700x24' /usr/bin/python3 -B tests/probe_gtk_hint_hover.py --family gtk2

.PHONY: check-tooltip-position
check-tooltip-position:
	/usr/bin/python3 -B tests/test_tooltip_position.py

.PHONY: check-qt-gallery-hint-helper
check-qt-gallery-hint-helper:
	T07_PRIVATE_PROBE=1 LC_ALL=C.UTF-8 xvfb-run -a /usr/bin/python3 -B tests/probe_qt_gallery_hints.py --major 5
	T07_PRIVATE_PROBE=1 LC_ALL=C.UTF-8 xvfb-run -a /usr/bin/python3 -B tests/probe_qt_gallery_hints.py --major 6

$(BUILD)/help-topics-test: tests/help_topics_test.c src/model/help_topics.c include/help_topics.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/help_topics_test.c src/model/help_topics.c -o "$@"
.PHONY: check-help-topics
check-help-topics: $(BUILD)/help-topics-test
	"$<"

.PHONY: check-dynamic-hints
check-dynamic-hints: $(BUILD)/native-metrics-view
	LC_ALL=C.UTF-8 TL_DYNAMIC_HINTS=1 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/native-metrics-view"

$(BUILD)/spin-hint-hover: tests/spin_hint_hover.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c include/ui_hints.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/spin_hint_hover.c src/view/ui_hints.c src/view/ui_spin_hints.c src/view/ui_disabled_hints.c -lXm -lXt -lX11 -o "$@"
.PHONY: check-spin-hint-hover
check-spin-hint-hover: $(BUILD)/spin-hint-hover
	LC_ALL=C.UTF-8 TL_SPIN_HINT_HOVER=1 xvfb-run -a /usr/bin/python3 -B tests/test_ui_hint_palettes.py "$(abspath $(BUILD))/spin-hint-hover"

.PHONY: check-gtk3-control-palette-native
check-gtk3-control-palette-native:
	NO_AT_BRIDGE=1 LC_ALL=C.UTF-8 xvfb-run -a -s '-screen 0 640x480x24' /usr/bin/python3 -B tests/test_gtk3_control_palette_native.py

$(BUILD)/owned-processes-test: tests/owned_processes_test.c src/controller/owned_processes.c include/owned_processes.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) tests/owned_processes_test.c src/controller/owned_processes.c -o "$@"

.PHONY: check-owned-processes
check-owned-processes: $(BUILD)/owned-processes-test
	"$(BUILD)/owned-processes-test"
