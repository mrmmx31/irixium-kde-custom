#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK3 hover/press in controlled backdrop, using real pointer input."""
from pathlib import Path
import sys
from test_arrow_relief_native import module,worker,ROOT
if __name__=='__main__':
    if '--worker' in sys.argv:raise SystemExit(worker(states=('hover',),hover_backdrop=True))
    runner=module(ROOT/'tools/theme-lab/tests/test_trough_native.py','hover_context_runner')
    raise SystemExit(runner.main(script=Path(__file__),prefix='.qa-theme-lab-arrow-hover-backdrop-'))
