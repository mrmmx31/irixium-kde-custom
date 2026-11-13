#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Theme absolute launcher icons using guarded, reversible per-user overrides."""
import argparse
import configparser
import os
from pathlib import Path
import subprocess
import sys
import json
from theme_transaction import Transaction, Change, snapshot, decode, edit_ini, Failure, atomic, no_links
from install_suite import roots

# Explicit identities: do not guess icons for arbitrary third-party launchers.
MAPPING = {
    'tdeiconedit.desktop':'tdeiconedit',
    'agenda-cientifica-agenda-cientifica.desktop':'agenda-cientifica',
    'tesourariamc-TesourariasMC.desktop':'tesourarias-mc',
    'WPrefs.desktop':'WPrefs', 'dbeaver-ce.desktop':'database',
    'grdesktop.desktop':'sgi-app-network', 'python3.13.desktop':'applications-development',
    'timidity.desktop':'multimedia-volume-control',
    'android-studio_android-studio.desktop':'android-studio',
    'powershell_powershell.desktop':'powershell',
    'teams-for-linux_teams-for-linux.desktop':'sgi-app-chat',
    'Intellij Idea.desktop':'idea',
    'io.snapcraft.SessionAgent.desktop':'system-software-install',
    'vim.desktop':'accessories-text-editor',
    'texdoctk.desktop':'texdoctk', 'snxgui.desktop':'snxgui',
}

# Only these published generic names may be replaced in existing local entries.
# Personal icon choices outside these exact defaults are preserved.
GENERIC_DEFAULTS = {
    'tdeiconedit.desktop': ('applications-graphics','tdeiconedit'),
    'calibre-lrfviewer.desktop': ('calibre-viewer','calibre-lrfviewer'),
    'org.kde.contactthemeeditor.desktop': ('kaddressbook','contact-theme-editor'),
    'org.kde.contactprintthemeeditor.desktop': ('kaddressbook','contact-print-theme-editor'),
    'org.kde.headerthemeeditor.desktop': ('kmail','mail-header-theme-editor'),
    'pluma.desktop': ('accessories-text-editor','pluma'),
    'android-studio_android-studio.desktop': ('applications-development', 'android-studio'),
    'WPrefs.desktop': ('preferences-system', 'WPrefs'),
    'agenda-cientifica-agenda-cientifica.desktop': ('office-calendar', 'agenda-cientifica'),
    'powershell_powershell.desktop': ('utilities-terminal', 'powershell'),
    'mate-terminal.desktop': ('utilities-terminal', 'mate-terminal'),
    'qterminal.desktop': ('utilities-terminal', 'qterminal'),
    'qt5ct.desktop': ('preferences-desktop-theme','qt5ct'),
    'qt6ct.desktop': ('preferences-desktop-theme','qt6ct'),
    'thunar-settings.desktop': ('org.xfce.thunar','thunar-settings'),
    'lxtask.desktop': ('utilities-system-monitor','lxtask'),
    'qterminal-drop.desktop': ('utilities-terminal', 'qterminal-drop'),
    'debian-xterm.desktop': ('mini.xterm', 'xterm'),
    'debian-uxterm.desktop': ('mini.xterm', 'uxterm'),
    'mintstick-kde.desktop': ('system-run', 'mintstick-writer'),
    'mintstick-format-kde.desktop': ('system-run', 'mintstick-format'),
    'mate-font-viewer.desktop': ('preferences-desktop-font', 'mate-font-viewer'),
    'mate-calc.desktop': ('accessories-calculator', 'mate-calculator'),
    'gucharmap.desktop': ('accessories-character-map', 'gucharmap'),
    'org.kde.kcharselect.desktop': ('accessories-character-map', 'kcharselect'),
    'org.kde.plasma.emojier.desktop': ('preferences-desktop-emoticons', 'plasma-emojier'),
    'org.kde.drkonqi.coredump.gui.desktop': ('tools-report-bug', 'crashed-processes-viewer'),
    'pcmanfm.desktop': ('system-file-manager', 'pcmanfm'),
    'thunar-bulk-rename.desktop': ('org.xfce.thunar', 'thunar-bulk-rename'),
    'tesourariamc-TesourariasMC.desktop': ('applications-office', 'tesourarias-mc'),
}
MAPPING.update({name: pair[1] for name,pair in GENERIC_DEFAULTS.items()})


def plan(data, desktop, application_roots):
    effective={}
    for folder in application_roots:
        if not folder.is_dir():continue
        for p in sorted(folder.glob('*.desktop')):effective.setdefault(p.name,p)
    sources=[(p,data/'applications'/name) for name,p in effective.items() if name in MAPPING]
    sources += [(desktop/name,desktop/name) for name in MAPPING if (desktop/name).is_file()]
    changes=[]
    for source,dest in sources:
        if dest.is_symlink():raise Failure('Atalho local simbólico recusado: '+str(dest))
        contents=source.read_bytes()
        if source.name=='snxgui.desktop':
            import re
            text=contents.decode('utf-8-sig')
            blocks=re.split(r'(?m)^\[Desktop Entry\]\s*\n',text)
            if len(blocks)>2:
                if blocks[0].strip() or len({part.strip() for part in blocks[1:]})!=1:
                    raise Failure('Grupos SNX conflitantes; atalho preservado para revisão.')
                contents=('[Desktop Entry]\n'+blocks[1].strip()+'\n').encode()
        cp=configparser.ConfigParser(interpolation=None,strict=False)
        cp.read_string(contents.decode('utf-8-sig'))
        icon=cp.get('Desktop Entry','Icon',fallback='')
        migrate_idea=source.name=='Intellij Idea.desktop' and icon=='applications-development'
        empty_tex=source.name=='texdoctk.desktop' and not icon
        generic=source.name in GENERIC_DEFAULTS and icon==GENERIC_DEFAULTS[source.name][0]
        if not icon.startswith(('/','~')) and not migrate_idea and not empty_tex and not generic:continue
        target=MAPPING[source.name]
        if not any((data/'icons/IrixClassic-SGI'/f).is_file()
                   for f in ('scalable/apps/'+target+'.svg','scalable/categories/'+target+'.svg')):
            raise Failure('Ícone de destino não instalado: '+target)
        updated=edit_ini(contents,'Desktop Entry',{'Icon':target})
        prior=snapshot(dest)
        changes.append(Change(dest,updated,0,prior.get('mode',0o644),prior))
    return changes


def mime_changes(data):
    """Repair only the known local shell-script icon override, preserving globs."""
    import xml.etree.ElementTree as ET
    import html
    path=data/'mime/packages/application-x-shellscript.xml'
    if not path.is_file():return []
    prior=snapshot(path);contents=decode(prior)
    tree=ET.fromstring(contents)
    text=contents.decode('utf-8')
    for entry in tree:
        if entry.get('type')!='application/x-shellscript':continue
        for child in entry:
            value=child.get('name','')
            if child.tag.split('}')[-1]=='icon' and value.startswith(('/','~')):
                old='name="'+html.escape(value,quote=True)+'"'
                if old not in text:raise Failure('Formato do ícone MIME precisa de revisão.')
                text=text.replace(old,'name="text-x-script"',1)
    return [] if text.encode()==contents else [Change(path,text.encode(),0,prior['mode'],prior)]


def restore_history(tx,dry=False):
    """Undo all our installed layers, newest first, preserving later user edits."""
    receipts=[]
    for path in (tx.state/'backups').glob('*/receipt.json'):
        no_links(path)
        record=json.loads(path.read_text())
        if record['status']=='installed':receipts.append(path)
        elif record['status'] in ('prepared','restoring','recovery_needed'):
            raise Failure('Há adaptação interrompida; preserve o backup antes de restaurar.')
    for path in sorted(receipts,key=lambda p:p.stat().st_mtime_ns,reverse=True):
        if dry:
            print('Backup a restaurar: '+str(path.parent));continue
        atomic(tx.state/'latest',(path.parent.name+'\n').encode())
        tx.restore()
    if not receipts:print('Nenhuma adaptação ativa para restaurar.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar',action='store_true')
    parser.add_argument('--restaurar',action='store_true')
    args=parser.parse_args()
    if os.geteuid()==0:raise Failure('Execute sem sudo.')
    data,config,state=roots()
    # Read the user's configured desktop location; never repurpose HOME.
    dirs=configparser.ConfigParser()
    desktop=Path.home()/'Desktop'
    settings=config/'user-dirs.dirs'
    if settings.exists():
        import re
        match=re.search(r'^XDG_DESKTOP_DIR="([^"]+)"',settings.read_text(),re.M)
        if match:desktop=Path(match[1].replace('$HOME',str(Path.home())))
    if not desktop.is_relative_to(Path.home()):raise Failure('Área de trabalho fora do perfil do usuário.')
    allowed={data/'applications'/n for n in MAPPING}|{desktop/n for n in MAPPING}
    allowed.add(data/'mime/packages/application-x-shellscript.xml')
    def refuse_shared(entries):
        raise Failure('Arquivos compartilhados nunca são permitidos nesta operação.')
    tx=Transaction(state/'irix-classic-launchers',refuse_shared,lambda path,phase:path in allowed and phase==0)
    if args.restaurar:
        with tx.locked():restore_history(tx,dry=args.verificar)
    else:
        directories=[data/'applications']+[Path(p)/'applications' for p in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')]
        # Exported launchers can appear in menus even if this shell omits their XDG root.
        directories += [Path('/var/lib/flatpak/exports/share/applications'),Path('/var/lib/snapd/desktop/applications')]
        changes=plan(data,desktop,directories)+mime_changes(data)
        with tx.locked():tx.install(changes,dry=args.verificar)
    if not args.verificar:
        mime_tool=__import__('shutil').which('update-mime-database')
        if mime_tool and (data/'mime/packages').is_dir():subprocess.run([mime_tool,str(data/'mime')],check=True)
        tool=__import__('shutil').which('kbuildsycoca6')
        if tool:subprocess.run([tool,'--noincremental'],check=True)


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:sys.exit('ERRO: '+str(e))
