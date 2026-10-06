#!/usr/bin/env python3
"""Install a parallel icon theme; do not change the active theme.
Python >= 3.10, standard library. SPDX-License-Identifier: MIT
"""
from __future__ import annotations
import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from icon_common import audit


def install(source: Path, icons_root: Path) -> Path:
    source=source.expanduser().resolve(strict=True)
    if not re.fullmatch(r'[A-Za-z0-9_-]+',source.name):
        raise ValueError('Nome interno inválido para a pasta do tema.')
    icons_root=icons_root.expanduser().resolve()
    dest=icons_root/source.name
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f'O tema já existe; nada sobrescrito: {dest}')
    if dest.is_relative_to(source) or source.is_relative_to(dest):
        raise ValueError('Instalação não pode se sobrepor à origem.')
    report=audit(source)
    if report['errors']:
        raise ValueError(f'Tema tem {report["errors"]} erro(s); execute validate_theme.py antes de instalar.')
    icons_root.mkdir(parents=True,exist_ok=True)
    # Audit rejected external links and symlinked directories.
    shutil.copytree(source,dest,symlinks=False)
    return dest


def main():
    default=Path(__file__).resolve().parents[1]/'themes/IrixClassic-SGI'
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme',type=Path,default=default)
    parser.add_argument('--icons-root',type=Path,default=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'icons')
    args=parser.parse_args()
    try:
        dest=install(args.theme,args.icons_root)
        print(f'Instalado: {dest}\nO tema ativo NÃO foi alterado.\nAbra Configurações do Sistema, procure Ícones e selecione o novo tema.')
    except Exception as exc:parser.exit(1,f'Erro: {exc}\n')


if __name__=='__main__':main()
