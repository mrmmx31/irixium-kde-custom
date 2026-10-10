#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt5 entry point for the guarded native Widgets gallery."""
import sys

from qt6_demo import main


if __name__ == '__main__':
    try:
        sys.exit(main(default_qt_major=5))
    except (RuntimeError, OSError, ValueError, ImportError) as error:
        print('Private Qt5 Widgets demo refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
