# SPDX-License-Identifier: GPL-3.0-or-later
cmake_minimum_required(VERSION 3.16)
project(ThemeLabNativeColors LANGUAGES CXX)
find_package(Qt6 REQUIRED COMPONENTS Core Gui)
# The distribution's all-component KF6Config CMake package also requires Qml
# development files. This reader uses only the installed C++ Core/ColorScheme
# APIs, so find those headers/libraries without loading unrelated Qml targets.
find_path(KF6_CONFIG_CORE_INCLUDE KSharedConfig PATH_SUFFIXES KF6/KConfigCore)
find_path(KF6_CONFIG_VERSION_INCLUDE kconfig_version.h PATH_SUFFIXES KF6/KConfig)
find_path(KF6_COLOR_SCHEME_INCLUDE KColorScheme PATH_SUFFIXES KF6/KColorScheme)
find_library(KF6_CONFIG_CORE_LIBRARY KF6ConfigCore)
find_library(KF6_COLOR_SCHEME_LIBRARY KF6ColorScheme)
foreach(dependency KF6_CONFIG_CORE_INCLUDE KF6_CONFIG_VERSION_INCLUDE KF6_COLOR_SCHEME_INCLUDE KF6_CONFIG_CORE_LIBRARY KF6_COLOR_SCHEME_LIBRARY)
  if(NOT ${dependency})
    message(FATAL_ERROR "Missing native KDE dependency: ${dependency}")
  endif()
endforeach()
add_executable(theme-lab-colors ../src/native_colors.cpp)
target_compile_features(theme-lab-colors PRIVATE cxx_std_17)
target_compile_options(theme-lab-colors PRIVATE -Wall -Wextra -Werror)
target_include_directories(theme-lab-colors PRIVATE ${KF6_CONFIG_CORE_INCLUDE} ${KF6_CONFIG_VERSION_INCLUDE} ${KF6_COLOR_SCHEME_INCLUDE})
target_link_libraries(theme-lab-colors PRIVATE Qt6::Core Qt6::Gui ${KF6_CONFIG_CORE_LIBRARY} ${KF6_COLOR_SCHEME_LIBRARY})
set(THEME_LAB_COLOR_OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/../build" CACHE PATH "Private native helper output")
set_target_properties(theme-lab-colors PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${THEME_LAB_COLOR_OUTPUT}")
