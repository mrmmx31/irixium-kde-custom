# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
# Included only in the prepared, private Dolphin source tree.
set(CMAKE_AUTOMOC ON)
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)
set(bundle "${CMAKE_BINARY_DIR}/irixclassic-bundle")
# Unique SONAMEs prevent accidental replacement of the system Dolphin libraries.
set_target_properties(dolphinprivate PROPERTIES OUTPUT_NAME irixclassic-files-private
    LIBRARY_OUTPUT_DIRECTORY "${bundle}/lib" BUILD_RPATH_USE_ORIGIN TRUE
    BUILD_WITH_INSTALL_RPATH TRUE INSTALL_RPATH_USE_LINK_PATH FALSE INSTALL_RPATH "$ORIGIN")
set_target_properties(dolphinvcs PROPERTIES OUTPUT_NAME irixclassic-files-vcs
    LIBRARY_OUTPUT_DIRECTORY "${bundle}/lib" BUILD_RPATH_USE_ORIGIN TRUE
    BUILD_WITH_INSTALL_RPATH TRUE INSTALL_RPATH_USE_LINK_PATH FALSE INSTALL_RPATH "$ORIGIN")
add_library(irixclassic-ui STATIC core.cpp core.h shelf.cpp shelf.h preview.cpp preview.h classicshell.cpp classicshell.h)
# Dolphin disables exceptions; the new UI throws a contract error caught by main.
kde_target_enable_exceptions(irixclassic-ui PUBLIC)
target_include_directories(irixclassic-ui PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}" "${CMAKE_SOURCE_DIR}/src" "${CMAKE_BINARY_DIR}/src")
target_link_libraries(irixclassic-ui PUBLIC dolphinstatic Qt6::Widgets KF6::CoreAddons KF6::I18n KF6::KIOWidgets)
add_executable(irixclassic-files main.cpp)
target_link_libraries(irixclassic-files PRIVATE irixclassic-ui KF6::Crash)
set_target_properties(irixclassic-files PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${bundle}/bin"
    BUILD_RPATH_USE_ORIGIN TRUE BUILD_RPATH "$ORIGIN/../lib" BUILD_WITH_INSTALL_RPATH TRUE INSTALL_RPATH_USE_LINK_PATH FALSE INSTALL_RPATH "$ORIGIN/../lib")
add_executable(irixclassic-preview-worker previewworker.cpp)
target_link_libraries(irixclassic-preview-worker PRIVATE Qt6::Gui)
set_target_properties(irixclassic-preview-worker PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${bundle}/bin")
add_custom_target(irixclassic-bundle DEPENDS irixclassic-files irixclassic-preview-worker)
option(IRIXCLASSIC_BUILD_TESTS "Build the isolated tests for IrixClassic Files" ON)
if(IRIXCLASSIC_BUILD_TESTS)
    find_package(Qt6 REQUIRED COMPONENTS Test)
    enable_testing()
    add_executable(irixclassic-coretest ../irixclassic-tests/tst_core.cpp core.cpp)
    target_include_directories(irixclassic-coretest PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
    target_link_libraries(irixclassic-coretest PRIVATE Qt6::Test Qt6::Widgets)
    add_test(NAME irixclassic-core COMMAND irixclassic-coretest)
    add_executable(irixclassic-apptest ../irixclassic-tests/tst_application.cpp)
    target_link_libraries(irixclassic-apptest PRIVATE irixclassic-ui Qt6::Test)
    add_dependencies(irixclassic-apptest irixclassic-preview-worker)
    set_target_properties(irixclassic-apptest PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${bundle}/bin" BUILD_RPATH_USE_ORIGIN TRUE BUILD_RPATH "$ORIGIN/../lib" BUILD_WITH_INSTALL_RPATH TRUE INSTALL_RPATH_USE_LINK_PATH FALSE INSTALL_RPATH "$ORIGIN/../lib")
    add_test(NAME irixclassic-application COMMAND irixclassic-apptest)
    set_tests_properties(irixclassic-application PROPERTIES TIMEOUT 60 ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
    add_custom_target(irixclassic-tests DEPENDS irixclassic-coretest irixclassic-apptest)
endif()
# Deliberately no install() rules. Never run cmake --install on the upstream tree.
