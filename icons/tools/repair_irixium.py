#!/usr/bin/env python3
"""Audit by default; optionally build a conservative, independent Irixium-Fixed.
Never modifies the source or the KDE configuration. Python >= 3.10.
SPDX-License-Identifier: MIT
"""
from __future__ import annotations
import argparse
import configparser
import os
import re
import shutil
import sys
from pathlib import Path
from icon_common import (CONTEXTS, IMAGE_EXT, audit, directory_names, parse_index,
                         png_size, safe_target, walk_files, write_report)


def build_fixed(source: Path, dest: Path, normalize_png: bool=False) -> dict:
    source=source.expanduser().resolve(strict=True)
    dest=dest.expanduser().absolute()
    # is_relative_to is inclusive: source and destination may not overlap.
    resolved=dest.resolve()
    if resolved.is_relative_to(source) or source.is_relative_to(resolved):
        raise ValueError('Origem e destino não podem se sobrepor.')
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f'Destino já existe, não sobrescrito: {dest}')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',dest.name):
        raise ValueError('Nome da pasta do tema: use somente letras ASCII, números, _ e -.')
    before=audit(source)
    cp=parse_index(source/'index.theme')
    invalid={i['path'] for i in before['issues'] if i['code'] in
             ('unsafe-or-broken-link','directory-symlink','invalid-image','unsafe-directory')}
    copied=[]; skipped=[]; resized=[]
    try:
        dest.mkdir(parents=True,exist_ok=False)
        for file,dirlink in walk_files(source):
            rel=file.relative_to(source)
            if rel.as_posix() in invalid or dirlink or (file.is_symlink() and not safe_target(file,source)):
                skipped.append(rel.as_posix()); continue
            if file.name == 'icon-theme.cache':
                skipped.append(rel.as_posix()); continue
            # Index and manifest are produced below, never copied over running output.
            if rel.as_posix() == 'index.theme':continue
            target=dest/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            # Dereference safe INTERNAL file links; outputs are self-contained.
            shutil.copyfile(file,target)
            copied.append(rel.as_posix())
        present={p.parent.relative_to(dest).as_posix() for p in dest.rglob('*')
                 if p.is_file() and p.suffix.lower() in IMAGE_EXT}
        declared=directory_names(cp)
        ordered=[d for d in declared if d in present]+sorted(present-set(declared))
        new=configparser.ConfigParser(interpolation=None)
        new.optionxform=str
        new['Icon Theme']=dict(cp['Icon Theme'])
        header=new['Icon Theme']
        header['Name']='Irixium — Fixed (local)'
        for key in list(header):
            if key.startswith('Name['):del header[key]
        header['Name[pt_BR]']='Irixium — Corrigido (local)'
        # Preserve other explicit parents; the known Irixium snapshot yields breeze,hicolor.
        parents=[x.strip() for x in header.get('Inherits','').split(',') if x.strip() and x.strip()!='hicolor']
        if 'breeze' not in parents:parents.append('breeze')
        header['Inherits']=','.join(dict.fromkeys(parents+['hicolor']))
        header['Directories']=','.join(ordered)
        header.pop('ScaledDirectories',None) # all actual dirs remain in Directories
        for group in ('Desktop','Toolbar','MainToolbar','Panel','Dialog','Small'):
            key=group+'Sizes';default=header.get(group+'Default')
            if key in header:
                nums={int(x) for x in header[key].split(',') if x.strip()}
                if default:nums.add(int(default))
                if group!='Small' and any(d.startswith('24x24/') for d in ordered):nums.add(24)
                header[key]=','.join(str(n) for n in sorted(nums))
        for directory in ordered:
            if directory in cp:
                new[directory]=dict(cp[directory])
            else:
                match=re.fullmatch(r'(\d+)x\1(?:@(\d+))?/(.+)',directory)
                if not match:
                    raise ValueError(f'Diretório sem metadados inferíveis: {directory}; ajuste manualmente.')
                size,scale,category=match.groups()
                new[directory]={'Size':size,'Scale':scale or '1','Type':'Fixed',
                                'Context':CONTEXTS.get(category,'Applications')}
            section=new[directory]
            kinds={p.suffix.lower() for p in (dest/directory).iterdir() if p.is_file()}
            if section.get('Type')=='Scalable' and '.svg' not in kinds:
                section['Type']='Fixed'
                for key in ('MinSize','MaxSize','Threshold'):section.pop(key,None)
        # Keep Scale != 1 in ScaledDirectories as specified by freedesktop.
        scaled=[d for d in ordered if int(new[d].get('Scale','1'))!=1]
        header['Directories']=','.join(d for d in ordered if d not in scaled)
        if scaled:header['ScaledDirectories']=','.join(scaled)
        # Opt-in correction of actual canvas mismatch; no automatic optical cropping.
        if normalize_png:
            try:from PIL import Image
            except ImportError as exc:raise RuntimeError('--normalize-png exige Pillow/python3-pil.') from exc
            for directory in ordered:
                section=new[directory]
                if section.get('Type','Threshold')!='Fixed':continue
                size=int(section['Size'])*int(section.get('Scale','1'))
                if not 1<=size<=2048:raise ValueError(f'Dimensão insegura/não suportada: {size}')
                for p in (dest/directory).glob('*.png'):
                    w,h=png_size(p)
                    if section.get('Context')=='Animations':continue
                    if (w,h)==(size,size):continue
                    with Image.open(p) as original:
                        rgba=original.convert('RGBA')
                        ratio=min(size/w,size/h)
                        target=(max(1,round(w*ratio)),max(1,round(h*ratio)))
                        method=Image.Resampling.NEAREST if ratio>=1 else Image.Resampling.LANCZOS
                        rgba=rgba.resize(target,method)
                        canvas=Image.new('RGBA',(size,size),(0,0,0,0))
                        canvas.alpha_composite(rgba,((size-target[0])//2,(size-target[1])//2))
                        canvas.save(p)
                    resized.append(p.relative_to(dest).as_posix())
        with (dest/'index.theme').open('w',encoding='utf-8') as stream:
            new.write(stream,space_around_delimiters=False)
        after=audit(dest)
        report={'source':str(source),'destination':str(dest),'before':before,'after':after,
                'copied_files':len(copied),'skipped_files':skipped,'normalized_png':resized,
                'notes':['Origem não alterada. Sem mudança nas configurações do KDE.',
                         'Arquivos corrompidos/links inseguros omitidos; nomes ausentes usam fallback.',
                         'Sem normalização solicitada, a arte copiada conserva seus bytes.',
                         'Uma imagem pequena não ganha detalhes ao ampliar; revisão visual ainda é necessária.']}
        write_report(report,dest/'IRIXIUM-FIX-REPORT.json')
        (dest/'IRIXIUM-FIX-NOTICE.txt').write_text(
            'Cópia local corrigida. Arte e direitos permanecem dos respectivos autores.\n'
            'Este procedimento não atribui licença nova à arte de terceiros.\n'
            'Consulte IRIXIUM-FIX-REPORT.json. Não publicar a cópia sem esclarecer a licença original.\n',encoding='utf-8')
        return report
    except Exception:
        # Do not erase content automatically. The caller sees the partial path.
        print(f'Falha ao construir {dest}. Não aplique uma cópia parcial.',file=sys.stderr)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path,help='Pasta Irixium que contém index.theme.')
    parser.add_argument('--build',type=Path,help='Novo destino, por exemplo ~/.local/share/icons/Irixium-Fixed.')
    parser.add_argument('--normalize-png',action='store_true',help='Somente na cópia: corrigir telas PNG de dimensão errada; requer Pillow.')
    parser.add_argument('--report',type=Path,help='Salvar relatório adicional em arquivo novo.')
    args=parser.parse_args()
    try:
        if args.report and args.report.expanduser().resolve().is_relative_to(args.source.expanduser().resolve()):
            raise ValueError('Salve o relatório fora da origem para mantê-la inalterada.')
        if args.normalize_png and not args.build:raise ValueError('--normalize-png requer --build.')
        if args.report and (args.report.exists() or args.report.is_symlink()):
            raise FileExistsError('Relatório já existe; escolha outro nome.')
        report=build_fixed(args.source,args.build,args.normalize_png) if args.build else audit(args.source)
        print(write_report(report,args.report))
        return 1 if (report['after']['errors'] if args.build else report['errors']) else 0
    except Exception as exc:parser.exit(2,f'Erro: {exc}\n')


if __name__=='__main__':sys.exit(main())
