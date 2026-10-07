#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Copy a pinned, Debian-patched Dolphin tree and apply the isolated app overlay.

No edits in the caller's checkout/upstream. No system installation or git writes.
Changes use unique anchors. An unexpected base is rejected, not forced.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.0-alpha1'
DEBIAN_VERSION='4:25.04.3-1+deb13u1'

class Failure(RuntimeError): pass

def sha(data): return hashlib.sha256(data).hexdigest()
def replace_one(text,old,new):
    if text.count(old)!=1: raise Failure('Upstream anchor absent or ambiguous: '+old[:100])
    return text.replace(old,new,1)

def replace_body(text,signature,new_body):
    if text.count(signature)!=1: raise Failure('Function signature absent or ambiguous: '+signature)
    start=text.index(signature)+len(signature)
    begin=text.find('{',start)
    if begin<0: raise Failure('Function has no body')
    # Lexer for C++ braces, strings, characters and comments. No regex body matching.
    i=begin; depth=0; mode='code'
    while i<len(text):
        c=text[i]; nxt=text[i:i+2]
        if mode=='line':
            if c=='\n': mode='code'
        elif mode=='comment':
            if nxt=='*/': mode='code';i+=1
        elif mode in ('string','char'):
            if c=='\\': i+=1
            elif c==('"' if mode=='string' else "'"): mode='code'
        else:
            if nxt=='//':mode='line';i+=1
            elif nxt=='/*':mode='comment';i+=1
            elif c=='"':mode='string'
            elif c=="'":mode='char'
            elif c=='{':depth+=1
            elif c=='}':
                depth-=1
                if depth==0:return text[:begin]+'{\n'+new_body.rstrip()+'\n}'+text[i+1:]
        i+=1
    raise Failure('Unterminated function body')

def transform_viewproperties(text):
    text=replace_one(text,'const char ViewPropertiesFileName[] = ".directory";',
                     'const char ViewPropertiesFileName[] = "view.properties";')
    text=replace_body(text,'ViewPropertySettings *ViewProperties::loadProperties(const QString &folderPath) const',r"""    // Private view-properties files only. Never read/write directory xattrs.
    const QString path = folderPath + QDir::separator() + ViewPropertiesFileName;
    return new ViewPropertySettings(KSharedConfig::openConfig(path, KConfig::SimpleConfig));""")
    text=replace_one(text,'    m_node = loadProperties(m_filePath);',r"""    // Override upstream's per-directory destination, including HOME locations.
    // Keep special-view decisions but store ALL view preferences in this app.
    const QString privateKey = useGlobalViewProps ? QStringLiteral("global")
        : QStringLiteral("folders/") + QString::fromLatin1(QCryptographicHash::hash(
              url.adjusted(QUrl::NormalizePathSegments | QUrl::RemovePassword).toEncoded(),
              QCryptographicHash::Sha256).toHex());
    m_filePath = destinationDir(privateKey);
    m_node = loadProperties(m_filePath);""")
    text=replace_body(text,'void ViewProperties::save()',r"""    if (!QDir().mkpath(m_filePath)) {
        qCWarning(DolphinDebug) << "Cannot create private view-properties directory";
        return;
    }
    m_node->setVersion(CurrentViewPropertiesVersion);
    if (m_node->save()) m_changedProps = false;""")
    if 'setAttribute(metaDataKey' in text or 'metaData.setAttribute' in text:raise Failure('Unexpected xattr writer remained')
    return text

def transform_xml(text):
    tree=ET.fromstring(text)
    if tree.tag!='gui' or tree.get('name')!='dolphin':raise Failure('Unexpected XMLGUI root')
    tree.set('name','irixclassic-files')
    bar=tree.find('MenuBar')
    if bar is None:raise Failure('Missing native menu bar')
    for name,title in [('file','Actions'),('edit','Selected'),('tools','Options')]:
        menu=bar.find(f"Menu[@name='{name}']")
        if menu is None:raise Failure('Missing native menu '+name)
        label=menu.find('text')
        if label is None:label=ET.Element('text',{'context':'@title:menu'});menu.insert(0,label)
        label.text=title
    # Native sort action owns its menu. Move that existing action to the bar.
    view=bar.find("Menu[@name='view']")
    sort=view.find("Action[@name='sort']") if view is not None else None
    if sort is None:raise Failure('Native sort action not found')
    view.remove(sort);bar.insert(2,sort)
    ET.indent(tree,space='    ')
    return '<?xml version="1.0"?>\n<!DOCTYPE gui SYSTEM "kpartgui.dtd">\n'+ET.tostring(tree,encoding='unicode')+'\n'

def prepare(source:Path,destination:Path,overlay:Path=ROOT):
    source=source.resolve();destination=destination.absolute()
    if destination.exists():raise Failure('Destination exists; choose a new prepared-tree directory')
    if source==destination or source in destination.parents:raise Failure('Destination cannot be inside the source')
    if not (source/'debian/changelog').is_file():raise Failure('Use the Debian source, not an unpatched upstream checkout')
    first=(source/'debian/changelog').read_text().splitlines()[0]
    if not first.startswith('dolphin ('+DEBIAN_VERSION+') '):raise Failure('Expected Debian source '+DEBIAN_VERSION+', got '+first)
    cm=(source/'CMakeLists.txt').read_text()
    for part in ('VERSION_MAJOR "25"','VERSION_MINOR "04"','VERSION_MICRO "3"'):
        if part not in cm:raise Failure('Unexpected upstream version')
    series=source/'debian/patches/series'
    required=[]
    if series.exists():required=[l.split()[0] for l in series.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')]
    applied_file=source/'.pc/applied-patches'
    applied=applied_file.read_text().splitlines() if applied_file.exists() else []
    if any(p not in applied for p in required):raise Failure('Debian patches are not all applied. Extract with dpkg-source -x first.')
    if (source/'.git').exists():raise Failure('Expected an extracted Debian source tree, without .git')
    # Source symlinks are refused rather than silently dereferenced outside tree.
    for p in source.rglob('*'):
        if p.is_symlink():raise Failure('Unexpected source symlink: '+str(p.relative_to(source)))
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.irix-prepare-',dir=destination.parent) as tmp:
        work=Path(tmp)/'source';shutil.copytree(source,work)
        before={p.relative_to(work).as_posix():sha(p.read_bytes()) for p in (work/'src').rglob('*') if p.is_file()}
        # All generated setting classes point at the private app rc.
        replaced=0
        for p in (work/'src').rglob('*'):
            if p.is_file() and p.suffix in ('.cpp','.h','.kcfg','.kcfgc'):
                text=p.read_text()
                if 'dolphinrc' in text:
                    replaced+=text.count('dolphinrc');p.write_text(text.replace('dolphinrc','irixclassic-filesrc'))
        if replaced==0:raise Failure('No Dolphin config anchors found')
        p=work/'src/dolphinmainwindow.cpp';text=p.read_text()
        text=replace_one(text,'setComponentName(QStringLiteral("dolphin"), QGuiApplication::applicationDisplayName());',
                              'setComponentName(QStringLiteral("irixclassic-files"), QGuiApplication::applicationDisplayName());')
        text=replace_one(text,'setObjectName(QStringLiteral("Dolphin#"));','setObjectName(QStringLiteral("IrixClassicFiles#"));')
        p.write_text(text)
        p=work/'src/dolphin.qrc';text=p.read_text()
        text=replace_one(text,'prefix="/kxmlgui5/dolphin"','prefix="/kxmlgui5/irixclassic-files"')
        text=replace_one(text,'<file>dolphinui.rc</file>','<file alias="irixclassic-filesui.rc">dolphinui.rc</file>');p.write_text(text)
        p=work/'src/dolphinui.rc';p.write_text(transform_xml(p.read_text()))
        p=work/'src/views/viewproperties.cpp';p.write_text(transform_viewproperties(p.read_text()))
        p=work/'src/dolphinbookmarkhandler.cpp';text=p.read_text()
        first='    QString bookmarksFile = QStandardPaths::locate(QStandardPaths::GenericDataLocation, QStringLiteral("kfile/bookmarks.xml"));'
        last='    m_bookmarkManager = std::make_unique<KBookmarkManager>(bookmarksFile);'
        if text.count(first)!=1 or text.count(last)!=1:raise Failure('Bookmark storage anchors changed')
        begin=text.index(first);end=text.index(last,begin)
        text=text[:begin]+'''    // Bookmarks belong to this variant, not kfile/bookmarks.xml or Dolphin.
    const QString directory = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(directory);
    const QString bookmarksFile = directory + QStringLiteral("/bookmarks.xml");
'''+text[end:]
        p.write_text(text)
        p=work/'src/global.cpp';text=p.read_text()
        text=replace_one(text,'#include <KService>','#include <KService>\n#include <KShell>')
        text=replace_one(text,'QString command = QStringLiteral("dolphin --new-window");',
            'QString command = KShell::quoteArg(QCoreApplication::applicationFilePath()) + QStringLiteral(" --new-window");')
        # Generated D-Bus C++ interface name stays unchanged, but lookup NEVER
        # attaches to running system Dolphin services.
        text=replace_one(text,'const QString pattern = QStringLiteral("org.kde.dolphin-");',
            'const QString pattern = QStringLiteral("io.github.mrmmx31.irixclassic.files-");')
        p.write_text(text)
        p=work/'src/CMakeLists.txt';p.write_text(p.read_text()+'\n# IrixClassic Files: additional private target, never upstream install.\nadd_subdirectory(irixclassic)\n')
        p=work/'CMakeLists.txt';text=p.read_text()
        text=replace_one(text,'add_subdirectory(src)', 'enable_testing()\nadd_subdirectory(src)');p.write_text(text)
        shutil.copytree(overlay/'src',work/'src/irixclassic')
        (work/'src/irixclassic-tests').mkdir()
        for p in (overlay/'tests').glob('tst_*.cpp'):shutil.copy2(p,work/'src/irixclassic-tests'/p.name)
        changes=[]
        for p in (work/'src').rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(work).as_posix();after=sha(p.read_bytes())
            if before.get(rel)!=after:changes.append({'path':rel,'before':before.get(rel),'after':after})
        record={'version':VERSION,'debian_source':DEBIAN_VERSION,'debian_patches':applied,'changes':changes,
                'top_level_cmake_sha256':sha((work/'CMakeLists.txt').read_bytes()),
                'notice':'No system installation. Native compilation/tests are a separate step.'}
        (work/'IRIXCLASSIC-PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n')
        work.rename(destination)
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--origem',type=Path,required=True);p.add_argument('--destino',type=Path,required=True)
    a=p.parse_args();record=prepare(a.origem,a.destino);print(json.dumps(record,indent=2));return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (Failure,OSError,UnicodeError,ET.ParseError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
