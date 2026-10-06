#!/usr/bin/env python3
"""Audit an icon theme without changing it. SPDX-License-Identifier: MIT"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from icon_common import audit, write_report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('theme', type=Path)
    parser.add_argument('--report', type=Path)
    args=parser.parse_args()
    try:
        if args.report and args.report.expanduser().resolve().is_relative_to(args.theme.expanduser().resolve()):
            raise ValueError('Salve o relatório fora do tema auditado.')
        report=audit(args.theme)
        print(write_report(report,args.report))
        return 1 if report['errors'] else 0
    except Exception as exc:
        parser.exit(2,f'Erro: {exc}\n')


if __name__=='__main__':sys.exit(main())
