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
        def edge_bands(renderer, identifier):
            bounds=renderer.boundsOnElement(identifier)
            result=QImage(round(bounds.width()),round(bounds.height()),QImage.Format.Format_ARGB32)
            result.fill(0)
            painter=QPainter(result)
            renderer.render(painter,identifier,QRectF(0,0,result.width(),result.height()))
            painter.end()
            colors=[result.pixelColor(result.width()//2,y).name() for y in range(result.height())]
            assert all(result.pixelColor(x,y).alpha()==255 for x in range(result.width()) for y in range(result.height())),identifier
            return colors
        button=QSvgRenderer(str(STYLE/'widgets/button.svg'))
        raised_top=[PALETTE['highlight'],PALETTE['turquoise'],PALETTE['shadow'],PALETTE['pale']]
        raised_bottom=[PALETTE['face'],PALETTE['pale'],PALETTE['shadow'],PALETTE['rim']]
        checks['native_raised_relief_four_distinct_one_pixel_bands']=edge_bands(button,'normal-top')==raised_top and edge_bands(button,'normal-bottom')==raised_bottom and len(set(raised_top))==len(set(raised_bottom))==4
        checks['native_pressed_relief_is_reversed_bands']=edge_bands(button,'pressed-top')==list(reversed(raised_bottom)) and edge_bands(button,'pressed-bottom')==list(reversed(raised_top))
        instrument=QSvgRenderer(str(STYLE/'widgets/instrument.svg'))
        frame=QSvgRenderer(str(STYLE/'widgets/frame.svg'))
        checks['native_instrument_and_well_share_compound_relief']=edge_bands(instrument,'normal-top')==raised_top and edge_bands(frame,'plain-top')==list(reversed(raised_bottom))
        checks['native_relief_keeps_four_pixel_margin_contract']=all(element.attrib['width']=='4' and element.attrib['height']=='4' for filename in ('button','instrument','panel-background','frame','pager','iconbox','command-rail') for element in ET.parse(STYLE/'widgets'/f'{filename}.svg').getroot().iter() if element.attrib.get('id','').endswith(('hint-top-margin','hint-bottom-margin','hint-left-margin','hint-right-margin')))
        clock=QSvgRenderer(str(STYLE/'widgets/clock.svg'))
        face=QImage(64,64,QImage.Format.Format_ARGB32);face.fill(0)
        painter=QPainter(face);clock.render(painter,'ClockFace',QRectF(0,0,64,64));painter.end()
        checks['native_clock_face_blue']=face.pixelColor(32,32).name()==PALETTE['blue']
        checks['native_clock_face_opaque']=face.pixelColor(32,32).alpha()==255
        face.save(str(output/'clock-face.png'))
        rail=QSvgRenderer(str(STYLE/'widgets/command-rail.svg'))
        checks['native_command_rail_simple_two_tone_rim']=edge_bands(rail,'top')==['#c4d5ed']*4 and edge_bands(rail,'bottom')==['#3e536e']*4
        checks['native_command_rail_vertical_tile_hint_absent']=not rail.elementExists('hint-tile-center')
        def rail_rows(image,x,y,width,height):
            rows=[]
            for dy in range(height):
                colors={image.pixelColor(x+dx,y+dy).name() for dx in range(width)}
                # KSvg rasterizes a stretched center: checker cells may gain
                # interpolated colors at fractional scales. Count the solid
                # highlights/shadows separately from nonuniform checker rows.
                rows.append('L' if colors=={'#c4d5ed'} else 'D' if colors=={'#3e536e'} else 'C' if len(colors)>1 else '?')
            return ''.join(rows)
        def compact_rows(rows):
            return ''.join(value for i,value in enumerate(rows) if i==0 or value!=rows[i-1])
        rail_source=QImage(24,24,QImage.Format.Format_ARGB32);rail_source.fill(0)
        painter=QPainter(rail_source);rail.render(painter,'center',QRectF(0,0,24,24));painter.end()
        source_rows=rail_rows(rail_source,0,0,24,24)
        checks['native_command_rail_source_has_four_central_grooves']=source_rows=='CCCCCD'+('LCD'*4)+'LCCCCC'
        checks['native_command_rail_source_matches_sr104_two_colors']={rail_source.pixelColor(x,y).name() for x in range(24) for y in range(24)}=={'#3e536e','#c4d5ed'}
        checks['native_command_rail_source_checker_margins_alternate']=all(rail_source.pixelColor(x,y)!=rail_source.pixelColor(x+1,y) and rail_source.pixelColor(x,y)!=rail_source.pixelColor(x,y+1) for x in range(20) for y in (0,1,2,19,20,21))
        rail_source.save(str(output/'command-rail-source-center.png'))
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
                checks['native_weave_period_two']=all(image.pixelColor(22+x,24+y)==image.pixelColor(24+x,24+y)==image.pixelColor(22+x,26+y) for x in range(2) for y in range(2))
                checks['native_weave_same_at_two_widths']=all(image.pixelColor(22+x,24+y)==image.pixelColor(154+x,24+y) for x in range(12) for y in range(12))
                checks['native_weave_matches_sr104_two_colors']={image.pixelColor(22+x,24+y).name() for x in range(8) for y in range(8)}=={'#194b63','#a3d0e6'}
                checks['native_weave_alternates_each_pixel']=all(image.pixelColor(22+x,24+y)!=image.pixelColor(23+x,24+y) and image.pixelColor(22+x,24+y)!=image.pixelColor(22+x,25+y) for x in range(6) for y in range(6))
                checks['native_button_relief_changes']=image.pixelColor(24,77)!=image.pixelColor(156,77)
                checks['native_pager_windows_visible']=image.pixelColor(640,40).name()=='#b98976'
                checks['native_pager_active_rim_yellow']=image.pixelColor(800,12).name()==PALETTE['active']
                rail_native=rail_rows(image,16,140,276,24)
                rail_tall=rail_rows(image,316,140,276,32)
                checks['native_command_rail_has_four_grooves_at_two_heights']=compact_rows(rail_native)==compact_rows(rail_tall)=='CDLCDLCDLCDLCDLC'
                checks['native_command_rail_grooves_keep_checker_margins']=rail_native.startswith('CCCCC') and rail_native.endswith('CCCCC') and rail_tall.startswith('CCCCC') and rail_tall.endswith('CCCCC')
                control=window.findChild(QObject,'nativeSwitch');checks['native_switch_loaded']=control is not None and control.property('checked') is True
                slider=window.findChild(QObject,'nativeSlider');checks['native_slider_loaded']=slider is not None and abs(slider.property('value')-.65)<.001
            except Exception as error:errors.append(str(error))
            finally:app.quit()
        # Fixture-only wait for the renderer; no product timer or action exists.
        QTimer.singleShot(250,verify);app.exec()
        assert not errors,errors
    report={'pass':all(checks.values()),'checks':checks,'resources':resources,'scope':'Real QSvgRenderer resource parse and offscreen KSvg/Plasma controls in an isolated XDG fixture; no real desktop or button action is exercised.','command_rail_native_limit':'Default KSvg center stretching preserves four grooves but stretches checker spacing horizontally and introduces interpolated colors at fractional scales. Physical checker frequency is supplied by the production panel QML; this SVG fallback does not claim that frequency at arbitrary sizes.','desktop_modified':False,'services_called':False}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'pass':report['pass'],'checks':checks,'output':str(output)},indent=2))
    return 0 if report['pass'] else 1


if __name__=='__main__':sys.exit(main())
