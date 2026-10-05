#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Original file or optional patch in a temporary copy, never installed by this probe."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from arrow_runtime import run_quick

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true');p.add_argument('--original',action='store_true')
    p.add_argument('--estilo',choices=('Fusion','Breeze','kvantum'),default='kvantum')
    p.add_argument('--offscreen',action='store_true');p.add_argument('--qml-file',type=Path)
    p.add_argument('--capturas',type=Path);a=p.parse_args(argv)
    result,code=run_quick('file' if a.original else 'temporary_fix',a.estilo,
        manual=not a.testar,qml_file=a.qml_file,offscreen=a.offscreen,captures=a.capturas)
    print(json.dumps(result,ensure_ascii=False,indent=2));return code

if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as exc:print('Dependência Qt ausente:',exc,file=sys.stderr);sys.exit(77)
    except (OSError,ValueError,RuntimeError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
