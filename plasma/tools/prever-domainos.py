#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render the shared production DomainOS design; no real desktop actions.

Uses its own XDG directories and Qt's software/offscreen renderer by default.
Fixture labels, graph, time, tasks, desktop maps and tray are illustrations.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--interativo',action='store_true')
    args=parser.parse_args()
    output=args.saida.absolute();output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='irix-domainos-design-') as folder:
        private=Path(folder)
        for key,name in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')]:
            path=private/name;path.mkdir(mode=0o700);os.environ[key]=str(path)
        os.environ.update(QT_QUICK_BACKEND='software',QT_QPA_PLATFORMTHEME='generic',
                          DBUS_SESSION_BUS_ADDRESS='unix:path='+str(private/'disabled-bus'),
                          XDG_CURRENT_DESKTOP='NONE')
        if not args.interativo:os.environ['QT_QPA_PLATFORM']='offscreen'
        os.environ.pop('QT_STYLE_OVERRIDE',None)
        from PyQt6 import sip
        from PyQt6.QtCore import QObject,QPointF,QRect,Qt,QUrl,qVersion
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickItem,QQuickWindow
        from PyQt6.QtTest import QTest
        app=QGuiApplication([sys.argv[0]])
        engine=QQmlApplicationEngine();warnings=[]
        engine.warnings.connect(lambda messages:warnings.extend(str(m.toString()) for m in messages))
        engine.load(QUrl.fromLocalFile(str(ROOT/'plasma/tests/DomainOSPreview.qml')))
        if not engine.rootObjects():raise RuntimeError('\n'.join(warnings))
        window=sip.cast(engine.rootObjects()[0],QQuickWindow)
        checks={}
        def require(name,condition):
            checks[name]=bool(condition)
            if not condition:raise AssertionError(name)
        def settle():app.processEvents();window.requestUpdate();QTest.qWait(50);app.processEvents()
        def item(name):
            def visual(node):
                if node.objectName()==name:return node
                for child in node.childItems():
                    found=visual(child)
                    if found is not None:return found
                return None
            obj=visual(window.contentItem())
            if obj is None:obj=window.findChild(QObject,name)
            if obj is None:raise AssertionError('Missing '+name)
            return sip.cast(obj,QQuickItem)
        def capture(name):
            settle();image=window.grabWindow()
            require('capture_'+name,not image.isNull() and image.save(str(output/name)))
            return image
        settle()
        panel=item('domainosPanel')
        normal=capture('DESIGN.png')
        normal.copy(112,296,1942,218).save(str(output/'PANEL.png'))
        require('canonical_1942x218',panel.width()==1942 and panel.height()==218)
        require('seven_iconbox_entries',panel.property('taskCount')==7)
        require('two_illustrative_desktops',panel.property('workspaceCount')==2)
        require('six_tray_icons_in_2x3',panel.property('trayRows')==2 and panel.property('trayColumns')==3)
        require('unconfirmed_functions_are_not_live',panel.property('phase')=='design-awaiting-button-confirmations')
        def center_color(obj):
            point=obj.mapToScene(QPointF(obj.width()/2,obj.height()/2)).toPoint()
            return normal.pixelColor(point).name()
        require('selected_workspace_marker_is_yellow',center_color(item('domainosWorkspaceMarker_Procrastination'))=='#dddd28')
        require('unselected_workspace_marker_remains_neutral',center_color(item('domainosWorkspaceMarker_Work'))=='#607f91')
        selected=item('domainosDeskProcrastination').mapToScene(QPointF(1,10)).toPoint()
        require('selected_workspace_rim_matches_marker',normal.pixelColor(selected).name()=='#dddd28')
        mail=item('domainosMail')
        mail_top=mail.mapToScene(QPointF(mail.width()/2,0)).toPoint()
        def bands(image):
            return [image.pixelColor(mail_top.x(),mail_top.y()+i).name() for i in range(4)]
        require('native_compound_relief_raised',bands(normal)==['#263f4d','#bed0d4','#405c6c','#a2d0e7'])
        geometry={}
        for name in ('domainosInstitutional','domainosIconbox','domainosPager','domainosTray','domainosTrayNavigation','domainosLowerRail'):
            obj=item(name);pos=obj.mapToScene(QPointF(0,0));geometry[name]=[pos.x(),pos.y(),obj.width(),obj.height()]
        buttons=('domainosClock','domainosDate','domainosGraph','domainosMail','domainosIconboxPrevious','domainosIconboxNext',
                 'domainosWorkspace_Work','domainosWorkspace_Procrastination','domainosTrayNext','domainosTrayExpand')
        buttons+=tuple('domainosTask_'+str(i) for i in range(7))
        buttons+=tuple('domainosTray_'+name for name in ('network','speaker','envelope','storage','workstation','indicator'))
        buttons+=tuple('domainosShortcut_'+name for name in ('terminal','preferences','drawer','lock','help'))
        for name in buttons:
            button=item(name);point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint()
            before=(button.x(),button.y(),button.width(),button.height())
            QTest.mousePress(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            settle();require(name+'_pressed',button.property('pressed'))
            held=window.grabWindow()
            origin=button.mapToScene(QPointF(0,0)).toPoint()
            area=QRect(origin.x(),origin.y(),int(button.width()),int(button.height()))
            require(name+'_native_visual_changes_when_held',held.copy(area)!=normal.copy(area))
            if name=='domainosMail':
                capture('PRESSED.png')
                require('native_compound_relief_inverts_when_held',bands(held)==['#263f4d','#6a889a','#a2d0e7','#405c6c'])
            representative={'domainosClock':'PRESSED-CLOCK.png','domainosTask_0':'PRESSED-ICONBOX.png',
                'domainosWorkspace_Procrastination':'PRESSED-PAGER.png','domainosTray_network':'PRESSED-TRAY.png',
                'domainosShortcut_preferences':'PRESSED-SHORTCUT.png','domainosTrayNext':'PRESSED-NAVIGATION.png'}
            if name in representative:capture(representative[name])
            QTest.mouseMove(window,QPointF(20,20).toPoint());settle()
            require(name+'_cancelled_outside',not button.property('pressed'))
            QTest.mouseRelease(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,QPointF(20,20).toPoint());settle()
            require(name+'_geometry_preserved',before==(button.x(),button.y(),button.width(),button.height()))
        cancelled=capture('CANCELLED.png')
        require('normal_restored_after_cancellation',normal==cancelled)
        window.setProperty('drawingScale',0.5);half=capture('HALF-SCALE.png')
        require('half_scale_rigid_layout',panel.width()==971 and panel.height()==109)
        window.setProperty('drawingScale',1)
        require('zero_qml_diagnostics',not warnings)
        sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted((ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/ui').glob('*.qml'))}
        report={'status':'passed','qt':qVersion(),'scope':'production drawing and input feedback; fixture data, no system actions',
                'checks':checks,'geometry':geometry,'source_hashes':sources,'qml_diagnostics':warnings,
                'real_profiles_modified':False,'button_functions_confirmed':False}
        (output/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'status':'passed','checks':len(checks),'output':str(output)}))
        if args.interativo:app.exec()
        else:window.close();app.processEvents()


if __name__=='__main__':main()
