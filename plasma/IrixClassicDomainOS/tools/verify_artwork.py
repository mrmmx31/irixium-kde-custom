#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check SVG contracts and render real KSvg frames in a private XDG profile."""
import sys

# Set before importing build_artwork from the catalogued component below.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

STYLE = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('/tmp/irix-domainos-style-verification'))
    args=parser.parse_args(); output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    checks={};resources={}
    from build_artwork import PALETTE
    original=json.loads((STYLE/'CLASSIC-BASELINE.json').read_text())
    actual={str(p.relative_to(STYLE.parent/'IrixClassic')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((STYLE.parent/'IrixClassic').rglob('*')) if p.is_file()}
    checks['original_classic_byte_identical']=original==actual
    for path in sorted(STYLE.rglob('*.svg')):
        root=ET.parse(path).getroot();ids=[el.attrib['id'] for el in root.iter() if 'id' in el.attrib]
        assert len(ids)==len(set(ids)),f'Duplicate IDs in {path}'
        for element in root.iter():
            tag=element.tag.rsplit('}',1)[-1]
            assert tag not in ('linearGradient','radialGradient','filter','animate','animateTransform'),(path,tag)
            for key,value in element.attrib.items():
                if key in ('opacity','fill-opacity','stroke-opacity'):assert float(value) in (0,1),(path,key,value)
                if key in ('rx','ry'):assert float(value)==0,(path,key,value)
                if key=='style':
                    for opacity in re.findall(r'(?:^|;)(?:opacity|fill-opacity|stroke-opacity):([^;]+)',value):assert float(opacity) in (0,1),(path,opacity)
        resources[str(path.relative_to(STYLE))]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'unique_ids':True,'no_gradient_filter_or_animation':True}
    checks['all_svg_structural_contracts']=True
    # All HOME/XDG writes go to a temporary fixture; style configuration and
    # desktop APIs are never read or mutated in the real user's profile.
    with tempfile.TemporaryDirectory(prefix='irix-domainos-style-',dir='/tmp') as tmp:
        fixture=Path(tmp)
        for dirname in ('home','data','config','cache','state','runtime'):(fixture/dirname).mkdir(mode=0o700)
        shutil.copytree(STYLE,fixture/'data/plasma/desktoptheme/IrixClassicDomainOS')
        (fixture/'config/plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
        (fixture/'config/kdeglobals').write_text((STYLE/'colors').read_text())
        os.environ.update(HOME=str(fixture/'home'),XDG_DATA_HOME=str(fixture/'data'),XDG_CONFIG_HOME=str(fixture/'config'),XDG_CACHE_HOME=str(fixture/'cache'),XDG_STATE_HOME=str(fixture/'state'),XDG_RUNTIME_DIR=str(fixture/'runtime'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_CONTROLS_STYLE='org.kde.desktop',XDG_CURRENT_DESKTOP='NONE',DBUS_SESSION_BUS_ADDRESS='unix:path='+str(fixture/'no-session-bus'))
        os.environ.pop('WAYLAND_DISPLAY',None);os.environ.pop('DISPLAY',None)
        from PyQt6 import sip
        from PyQt6.QtCore import QObject,QUrl,QTimer,QRectF
        from PyQt6.QtGui import QImage,QPainter,QColor
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
        from PyQt6.QtSvg import QSvgRenderer
        app=QApplication([])
        for path in sorted(STYLE.rglob('*.svg')):
            renderer=QSvgRenderer(str(path));assert renderer.isValid(),path
            resources[str(path.relative_to(STYLE))]['native_qsvg_valid']=True
        clock=QSvgRenderer(str(STYLE/'widgets/clock.svg'))
        face=QImage(64,64,QImage.Format.Format_ARGB32);face.fill(0)
        painter=QPainter(face);clock.render(painter,'ClockFace',QRectF(0,0,64,64));painter.end()
        checks['native_clock_face_blue']=face.pixelColor(32,32).name()==PALETTE['blue']
        checks['native_clock_face_opaque']=face.pixelColor(32,32).alpha()==255
        face.save(str(output/'clock-face.png'))
        engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('artworkRoot',str(STYLE))
        engine.load(QUrl.fromLocalFile(str(STYLE/'tools/ResourcePreview.qml')))
        assert engine.rootObjects(),'Native QML fixture failed to load'
        window=sip.cast(engine.rootObjects()[0],QQuickWindow)
        errors=[]
        def verify():
            try:
                image=window.grabWindow();assert not image.isNull(),'Native screenshot is empty'
                image.save(str(output/'native-style-resources.png'))
                # Pixel-level proof that native KSvg tiles the weave at 1:1,
                # instead of stretching dot spacing when the plate widens.
                checks['native_housing_opaque']=all(image.pixelColor(x,y).alpha()==255 for x in range(1000) for y in range(296))
                checks['native_weave_period_four']=all(image.pixelColor(22+x,24+y)==image.pixelColor(26+x,24+y)==image.pixelColor(22+x,28+y) for x in range(4) for y in range(4))
                checks['native_weave_same_at_two_widths']=all(image.pixelColor(22+x,24+y)==image.pixelColor(154+x,24+y) for x in range(12) for y in range(12))
                checks['native_weave_multiple_fixed_colors']=len({image.pixelColor(22+x,24+y).name() for x in range(8) for y in range(8)})==5
                checks['native_button_relief_changes']=image.pixelColor(24,77)!=image.pixelColor(156,77)
                checks['native_pager_windows_visible']=image.pixelColor(640,40).name()=='#b98976'
                checks['native_pager_active_rim_yellow']=image.pixelColor(800,12).name()==PALETTE['active']
                checks['native_command_rail_rules_distinct']=len({image.pixelColor(30,146+y).name() for y in range(6)})==6
                control=window.findChild(QObject,'nativeSwitch');checks['native_switch_loaded']=control is not None and control.property('checked') is True
                slider=window.findChild(QObject,'nativeSlider');checks['native_slider_loaded']=slider is not None and abs(slider.property('value')-.65)<.001
            except Exception as error:errors.append(str(error))
            finally:app.quit()
        # Fixture-only wait for the renderer; no product timer or action exists.
        QTimer.singleShot(250,verify);app.exec()
        assert not errors,errors
    report={'pass':all(checks.values()),'checks':checks,'resources':resources,'scope':'Real QSvgRenderer resource parse and offscreen KSvg/Plasma controls in an isolated XDG fixture; no real desktop or button action is exercised.','desktop_modified':False,'services_called':False}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'pass':report['pass'],'checks':checks,'output':str(output)},indent=2))
    return 0 if report['pass'] else 1


if __name__=='__main__':sys.exit(main())
