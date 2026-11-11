# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt5 entry point for the shared QScrollBar recipe renderer."""
from qt6_scrollbar_recipe import STATES, contract
from qt6_scrollbar_recipe import generate as _generate, verify as _verify


def generate(root, folder, model, project_hash, kdeglobals):
    return _generate(root, folder, model, project_hash, kdeglobals, family='qt5')


def verify(root, receipt, model):
    return _verify(root, receipt, model, family='qt5')
