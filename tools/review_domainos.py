#!/usr/bin/env python3
"""Open the two DomainOS review boards without modifying the desktop theme."""
import argparse
import os
from pathlib import Path
import stat
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    app = root / 'skills/retro-ui-review/scripts/review_board.py'
    command = [sys.executable, '-B', str(app),
               '--data', str(root / 'docs/review/project-checklist.json'),
               '--data', str(root / 'docs/review/visual-checklist.json'),
               '--title', 'DomainOS — pranchetas de avaliação']
    if args.validate:
        command.append('--validate')
    else:
        if args.output is None:
            directory = Path('/tmp') / ('domainos-review-' + str(os.getuid()))
            try:
                directory.mkdir(mode=0o700)
            except FileExistsError:
                info = directory.lstat()
                if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                        or stat.S_IMODE(info.st_mode) != 0o700):
                    parser.error('Pasta temporária existente não é privada deste usuário.')
            output = directory / 'respostas.json'
        else:
            output = args.output.absolute()
        command += ['--output', str(output)]
    os.execv(sys.executable, command)


if __name__ == '__main__':
    main()
