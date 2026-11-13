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
        from PyQt6.QtGui import QGuiApplication,QImage,QPainter,QFont,QFontInfo
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickItem,QQuickWindow
        from PyQt6.QtTest import QTest
        from PyQt6.QtSvg import QSvgRenderer
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
        require('reference_fixture_has_no_live_runtime',panel.property('phase')=='design-reference')
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
        require('native_instrument_reference_relief_raised',bands(normal)==['#a3d0e6']*4)
        geometry={}
        for name in ('domainosInstitutional','domainosIconbox','domainosPager','domainosTray','domainosTrayNavigation','domainosLowerRail'):
            obj=item(name);pos=obj.mapToScene(QPointF(0,0));geometry[name]=[pos.x(),pos.y(),obj.width(),obj.height()]
        instruments=[item(name) for name in ('domainosClock','domainosDate','domainosGraph','domainosMail')]
        left=item('domainosInstitutional')
        require('left_and_right_modules_have_equal_width',left.width()==sum(item(name).width() for name in ('domainosPager','domainosTray','domainosTrayNavigation')))
        require('four_instruments_same_rectangle',len({(obj.width(),obj.height()) for obj in instruments})==1)
        require('instrument_row_starts_inside_cyan_chassis',
                left.x()+instruments[0].x()==item('domainosLeftCyanBorder').x()+item('domainosLeftCyanBorder').width())
        require('instrument_row_reaches_iconbox_without_extra_frame',
                left.x()+instruments[-1].x()+instruments[-1].width()==item('domainosIconbox').x())
        require('instrument_row_equal_gaps',len({b.x()-a.x()-a.width() for a,b in zip(instruments,instruments[1:])})==1)
        require('instrument_frames_touch_like_reference',all(a.x()+a.width()==b.x() for a,b in zip(instruments,instruments[1:])))
        require('instrument_row_reaches_metal_without_extra_frame',
                all(left.y()+obj.y()+obj.height()==item('domainosLowerRail').y() for obj in instruments))
        require('instrument_buttons_use_reference_simple_profile',all(obj.property('bevelThickness')==4
                and obj.property('simpleRelief') and obj.property('bevelLight').name()=='#a3d0e6'
                and obj.property('bevelDark').name()=='#194b63' for obj in instruments))
        require('tray_and_arrows_keep_compound_profile',all(item(name).property('bevelThickness')==4 for name in ('domainosTray_network','domainosTrayNext','domainosIconboxPrevious')))
        box=item('domainosIconbox'); previous=item('domainosIconboxPrevious'); next_button=item('domainosIconboxNext')
        tasks=[item('domainosTask_'+str(i)) for i in range(7)]
        require('narrower_iconbox_keeps_all_seven_without_overlap',previous.x()+previous.width()<=tasks[0].x() and all(a.x()+a.width()<=b.x() for a,b in zip(tasks,tasks[1:])) and tasks[-1].x()+tasks[-1].width()<=next_button.x() and next_button.x()+next_button.width()<=box.width())
        require('iconbox_task_group_has_equal_arrow_clearances',
                tasks[0].x()-previous.x()-previous.width()==next_button.x()-tasks[-1].x()-tasks[-1].width())
        require('iconbox_task_group_centered_horizontally',
                tasks[0].x()+tasks[-1].x()+tasks[-1].width()==box.width())
        require('iconbox_controls_centered_vertically',
                all(obj.y()*2+obj.height()==box.height() for obj in tasks+[previous,next_button,item('domainosIconboxWell')]))
        pager=item('domainosPager'); desks=[item('domainosDeskWork'),item('domainosDeskProcrastination')]
        require('pager_cards_equal_and_centered',
                desks[0].width()==desks[1].width() and desks[0].x()==pager.width()-desks[1].x()-desks[1].width()
                and all(obj.y()*2+obj.height()==pager.height() for obj in desks))
        for name,count in [('Work',3),('Procrastination',5)]:
            desk_map=item('domainosWorkspaceMap_'+name)
            samples=[item('domainosWorkspaceSample_'+name+'_'+str(i)) for i in range(count)]
            require('pager_'+name+'_samples_stay_inside_map',
                    desk_map.clip() and all(obj.x()>=2 and obj.y()>=2 and obj.x()+obj.width()<=desk_map.width()
                                           and obj.y()+obj.height()<=desk_map.height()-2 for obj in samples))
        navigation=item('domainosTrayNavigation'); navigation_buttons=[item('domainosTrayNext'),item('domainosTrayExpand')]
        require('navigation_controls_centered_as_group',
                all(obj.x()*2+obj.width()==navigation.width() for obj in navigation_buttons)
                and navigation_buttons[0].y()==navigation.height()-navigation_buttons[-1].y()-navigation_buttons[-1].height())
        tray=item('domainosTray'); well=item('domainosTrayWell')
        first=item('domainosTray_network'); last=item('domainosTray_indicator')
        require('tray_well_centered_horizontally',well.x()*2+well.width()==tray.width())
        require('tray_well_centered_vertically',well.y()*2+well.height()==tray.height())
        require('tray_grid_equal_left_right_clearance',first.x()-well.x()==well.x()+well.width()-last.x()-last.width())
        require('tray_grid_equal_top_bottom_clearance',first.y()-well.y()==well.y()+well.height()-last.y()-last.height())
        require('tray_grid_clear_of_inner_frame',min(first.x()-well.x(),first.y()-well.y())>4)
        rail=item('domainosLowerRail'); indicator=item('domainosRightIndicator')
        require('metal_rail_matches_reference_height',rail.height()==52)
        lip=item('domainosCyanLip'); foot_shadow=item('domainosCyanFootShadow')
        require('cyan_foot_is_part_of_chassis',rail.y()+rail.height()==lip.y()
                and lip.y()+lip.height()==foot_shadow.y() and foot_shadow.y()+foot_shadow.height()==218)
        # The 2px mounting shadow extends above/left of the centered 17x12 rim.
        require('indicator_rim_centered_on_command_rail',indicator.y()+4+24/2==rail.height()/2)
        require('indicator_reference_right_clearance',rail.width()-indicator.x()-indicator.width()==52)
        require('indicator_reference_blue',str(indicator.property('face').name())=='#78a0d5')
        identity=item('domainosIdentity')
        require('identity_simple_raised_metal_plate',identity.property('simpleRelief') and identity.property('bevelThickness')==4
                and identity.property('bevelLight').name()=='#c4d5ed' and identity.property('bevelDark').name()=='#3e536e')
        identity_top=identity.mapToScene(QPointF(identity.width()/2,0)).toPoint()
        identity_bottom=identity.mapToScene(QPointF(identity.width()/2,identity.height()-1)).toPoint()
        require('identity_original_highlight_and_shadow_orientation',normal.pixelColor(identity_top).name()=='#c4d5ed' and normal.pixelColor(identity_bottom).name()=='#3e536e')
        buttons=('domainosApplicationsDrawer','domainosIdentity','domainosClock','domainosDate','domainosGraph','domainosMail','domainosIconboxPrevious','domainosIconboxNext',
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
                require('native_instrument_reference_relief_inverts_when_held',bands(held)==['#194b63']*4)
            representative={'domainosClock':'PRESSED-CLOCK.png','domainosTask_0':'PRESSED-ICONBOX.png',
                'domainosWorkspace_Procrastination':'PRESSED-PAGER.png','domainosTray_network':'PRESSED-TRAY.png',
                'domainosApplicationsDrawer':'PRESSED-APPLICATIONS.png',
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
        # Observe rendered pixels at the actual desktop size. Checking only the
        # 1942px fixture missed the disappearance of highlights and fine weave.
        top=mail.mapToScene(QPointF(mail.width()/2,0)).toPoint()
        require('half_scale_instrument_keeps_two_pixel_reference_top',
                [half.pixelColor(top.x(),top.y()+y).name() for y in range(2)]==['#a3d0e6']*2)
        seams=[]
        for button in instruments[1:]:
            point=button.mapToScene(QPointF(0,button.height()/2)).toPoint()
            seams.append([half.pixelColor(point.x()+x,point.y()).name() for x in range(-2,2)])
        require('half_scale_instrument_faces_separated_by_four_pixel_relief',
                all(colors==['#194b63','#194b63','#a3d0e6','#a3d0e6'] for colors in seams))
        for button in instruments:
            bottom=button.mapToScene(QPointF(button.width()/2,button.height())).toPoint()
            require(button.objectName()+'_half_scale_single_bottom_frame',
                    [half.pixelColor(bottom.x(),bottom.y()+y).name() for y in (-2,-1,0,1)]
                    ==['#194b63','#194b63','#c4d5ed','#c4d5ed'])
        right=mail.mapToScene(QPointF(mail.width(),mail.height()/2)).toPoint()
        require('half_scale_instrument_group_single_right_frame',
                [half.pixelColor(right.x()+x,right.y()).name() for x in (-2,-1,0,1)]
                ==['#194b63','#194b63','#a3d0e6','#a3d0e6'])
        for name in ('domainosIconbox','domainosPager','domainosTray','domainosTrayNavigation'):
            obj=item(name);point=obj.mapToScene(QPointF(obj.width()/2,0)).toPoint()
            require(name+'_half_scale_top_matches_original_sequence',
                    [half.pixelColor(point.x(),point.y()+y).name() for y in range(-4,2)]
                    ==['#c5e8e6','#c5e8e6','#7acac5','#7acac5','#a3d0e6','#a3d0e6'])
            require(name+'_half_scale_top_and_bottom_have_single_frame',
                    [half.pixelColor(point.x(),point.y()+y).name() for y in range(2)]==['#a3d0e6']*2
                    and [half.pixelColor(point.x(),point.y()+int(obj.height()/2)-2+y).name() for y in range(2)]==['#194b63']*2)
        clock_face=item('domainosClockFace');clock_hands=item('domainosClockHands');clock=instruments[0]
        require('clock_face_and_hands_have_same_center',
                clock_face.x()+clock_face.width()/2==clock_hands.x()==clock.width()/2
                and clock_face.y()+clock_face.height()/2==clock_hands.y()==clock.height()/2)
        date_face=item('domainosDateFace')
        require('date_face_preserves_original_aspect_with_pixel_rounding',abs(date_face.width()/2-date_face.height()/2*60/35)<=1)
        date_origin=instruments[1].mapToScene(QPointF(0,0)).toPoint()
        glyphs=[(x,y) for x in range(int(instruments[1].width()/2)) for y in range(int(instruments[1].height()/2))
                if half.pixelColor(date_origin.x()+x,date_origin.y()+y).name()=='#ffffff']
        xs,ys=zip(*glyphs)
        date_text_bounds=[min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1]
        geometry['date_white_text_at_half_scale']=date_text_bounds
        # The bundled Courier strike is an explicit alternative, not the
        # original Swiss742. Its native ink measures 52x27 for these two lines.
        require('date_bitmap_lettering_scales_uniformly_and_is_centered',
                abs(date_text_bounds[2]-round(52*75/59))<=1 and abs(date_text_bounds[3]-round(27*75/59))<=1
                and abs(date_text_bounds[0]+date_text_bounds[2]/2-instruments[1].width()/4)<=1)
        date_label=item('domainosDateLettering');date_font=date_label.property('font')
        require('date_text_declares_unsmoothed_bitmap_content',not date_label.property('smooth'))
        require('date_font_strategy_keeps_platform_default',date_font.styleStrategy()==QFont.StyleStrategy.PreferDefault)
        blue='#3297c7';white='#ffffff'
        inside=date_face.mapToScene(QPointF(0,0)).toPoint()
        require('date_ink_has_only_binary_white_and_blue_pixels',
                all(half.pixelColor(inside.x()+x,inside.y()+y).name() in (blue,white)
                    for x in range(1,int(date_face.width()/2)-1) for y in range(1,int(date_face.height()/2)-1)))
        drawer=item('domainosApplicationsDrawer')
        require('applications_drawer_uses_existing_empty_slot',drawer.x()==587 and drawer.width()==118 and drawer.height()==52)
        date_info=QFontInfo(date_font)
        geometry['date_font']={'requested':date_font.family(),'resolved':date_info.family(),
                              'pixel_size':date_info.pixelSize(),'exact_strike':date_info.exactMatch()}
        require('bundled_x11_date_strike_loaded_without_outline_fallback',
                date_font.family()==date_info.family()=='Adobe Courier'
                and date_info.pixelSize()==14 and date_info.exactMatch())
        require('enlarged_date_drawing_keeps_clearance_from_button_relief',
                date_face.width()<=instruments[1].width()-8 and date_face.height()<=instruments[1].height()-8)
        def painted_image(node,filename):
            source=node.property('assetSource') or node.property('source')
            if isinstance(source,QUrl) and source.toString().endswith(filename):return node
            for child in node.childItems():
                found=painted_image(child,filename)
                if found is not None:return found
            return None
        for button,filename,aspect in [(instruments[2],'graph-reference.svg',60/35),(mail,'mail.svg',56/27)]:
            graphic=painted_image(button,filename)
            # A PreserveAspectFit canvas may have spare space. Check the image
            # actually painted by Qt rather than treating its canvas as ink.
            width=graphic.property('paintedWidth');height=graphic.property('paintedHeight')
            geometry[filename+'_painted_size_at_half_scale']=[width/2,height/2]
            require(filename+'_painted_face_preserves_original_aspect',abs(width-height*aspect)<0.01)
            require(filename+'_painted_face_keeps_button_relief_clear',width<=button.width()-8 and height<=button.height()-8)
        for name,expected in [('graph-reference.svg',(60,35)),('mail.svg',(56,27))]:
            renderer=QSvgRenderer(str(ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/images'/name))
            face=QImage(renderer.defaultSize(),QImage.Format.Format_ARGB32);face.fill(Qt.GlobalColor.transparent)
            painter=QPainter(face);renderer.render(painter);painter.end()
            require(name+'_native_face_matches_measured_reference',
                    (face.width(),face.height())==expected
                    and all(face.pixelColor(x,y).alpha()==255 for x in range(face.width()) for y in range(face.height())))
        renderer=QSvgRenderer(str(ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/images/clock-face.svg'))
        face=QImage(renderer.defaultSize(),QImage.Format.Format_ARGB32);face.fill(Qt.GlobalColor.transparent)
        painter=QPainter(face);renderer.render(painter);painter.end()
        ticks={(x,y) for x in range(face.width()) for y in range(face.height())
               if face.pixelColor(x,y).alpha()==255 and face.pixelColor(x,y).name()=='#ffffff'}
        tick_pixels=len(ticks);components=0
        while ticks:
            pending=[ticks.pop()];components+=1
            while pending:
                x,y=pending.pop()
                for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if neighbor in ticks:ticks.remove(neighbor);pending.append(neighbor)
        require('clock_has_four_small_cardinal_marks_like_reference',components==4 and tick_pixels==8)
        navigation=item('domainosTrayNext').mapToScene(QPointF(item('domainosTrayNext').width()/2,0)).toPoint()
        require('half_scale_navigation_keeps_compound_top',
                [half.pixelColor(navigation.x(),navigation.y()+i).name() for i in range(2)]==['#c5e8e6','#7acac5'])
        start=mail.mapToScene(QPointF(8,8)).toPoint()
        weave=[[half.pixelColor(start.x()+x,start.y()+y).name() for x in range(4)] for y in range(4)]
        require('half_scale_instrument_face_has_reference_weave',
                {color for row in weave for color in row}=={'#194b63','#a3d0e6'})
        require('half_scale_weave_keeps_single_pixel_alternation',
                all(weave[y][x]!=weave[y][x+1] for y in range(4) for x in range(3))
                and all(weave[y][x]!=weave[y+1][x] for y in range(3) for x in range(4)))
        rail=item('domainosLowerRail')
        start=rail.mapToScene(QPointF(300,16)).toPoint()
        rail_pixels=[[half.pixelColor(start.x()+x,start.y()+y).name() for x in range(6)] for y in range(6)]
        require('half_scale_rail_has_two_reference_colors',
                {color for row in rail_pixels for color in row}=={'#3e536e','#c4d5ed'})
        require('half_scale_rail_keeps_three_row_period',
                all(rail_pixels[y]==rail_pixels[y+3] for y in range(3)) and len({tuple(row) for row in rail_pixels})==3)
        empty=item('domainosRailLeft')
        begin=empty.mapToScene(QPointF(20,0)).toPoint()
        row_types=[]
        for y in range(2,int(empty.height()/2)-2):
            colors={half.pixelColor(begin.x()+x,begin.y()+y).name() for x in range(8)}
            row_types.append('light' if colors=={'#c4d5ed'} else 'dark' if colors=={'#3e536e'} else 'checker')
        starts=[i for i in range(len(row_types)-2) if row_types[i:i+3]==['light','checker','dark']]
        require('half_scale_rail_exactly_four_central_grooves',len(starts)==4 and all(b-a==3 for a,b in zip(starts,starts[1:])))
        require('half_scale_rail_has_checker_above_and_below_grooves',row_types[:starts[0]-1]==['checker']*(starts[0]-1)
                and row_types[starts[-1]+4:]==['checker']*(len(row_types)-starts[-1]-4))
        require('half_scale_rail_checker_margins_match_original',starts[0]-1==4 and len(row_types)-starts[-1]-4==4)
        foot_origin=lip.mapToScene(QPointF(200,0)).toPoint()
        require('half_scale_cyan_foot_matches_reference',
                [half.pixelColor(foot_origin.x(),foot_origin.y()+y).name() for y in range(4)]
                ==['#7acac5','#7acac5','#406b68','#406b68'])
        edge=item('domainosRightCyanBorder').mapToScene(QPointF(0,0)).toPoint()
        require('half_scale_right_cyan_and_shadow_are_continuous',
                all([half.pixelColor(edge.x()+x,edge.y()+y).name() for x in range(4)]
                    ==['#7acac5','#7acac5','#406b68','#406b68'] for y in range(105)))
        require('half_scale_right_band_preserves_inner_frame',
                [half.pixelColor(edge.x()+x,edge.y()+10).name() for x in range(-2,0)]==['#194b63']*2
                and [half.pixelColor(edge.x()+x,edge.y()+90).name() for x in range(-2,0)]==['#3e536e']*2)
        chassis_top=item('domainosTopChassisLight').mapToScene(QPointF(400,0)).toPoint()
        require('half_scale_top_border_matches_reference',
                [half.pixelColor(chassis_top.x(),chassis_top.y()+y).name() for y in range(4)]
                ==['#c5e8e6','#c5e8e6','#7acac5','#7acac5'])
        chassis_left=item('domainosLeftChassisLight').mapToScene(QPointF(0,40)).toPoint()
        require('half_scale_left_border_matches_complete_reference',
                [half.pixelColor(chassis_left.x()+x,chassis_left.y()+y).name() for x in range(4) for y in (0,70)]
                ==['#c5e8e6']*4+['#7acac5']*4)
        # The emblem must stay inside its metal plate after reducing its margins.
        plate=item('domainosIdentity'); plate_origin=plate.mapToScene(QPointF(0,0)).toPoint()
        require('half_scale_emblem_preserves_top_and_bottom_relief',
                all(half.pixelColor(plate_origin.x()+x,plate_origin.y()+y).name()=='#c4d5ed'
                    for x in range(128) for y in range(2) if x<126)
                and all(half.pixelColor(plate_origin.x()+x,plate_origin.y()+y).name()=='#3e536e'
                    for x in range(2,128) for y in (24,25)))
        emblem_margin=[[half.pixelColor(plate_origin.x()+x,plate_origin.y()+y).name()
                        for x in range(2,126)] for y in (2,23)]
        require('half_scale_emblem_has_clear_weave_above_and_below',
                all(set(row)=={'#3e536e','#c4d5ed'}
                    and all(a!=b for a,b in zip(row,row[1:])) for row in emblem_margin))
        lens_origin=indicator.mapToScene(QPointF(0,0)).toPoint()
        lens=[[half.pixelColor(lens_origin.x()+x,lens_origin.y()+y).name() for x in range(19)] for y in range(14)]
        require('half_scale_indicator_blue_lens_13_by_7',sum(color=='#78a0d5' for row in lens for color in row)==13*7)
        require('half_scale_indicator_mounting_recess_is_visible',
                lens[0]==['#3e536e']*19 and lens[1][:18]==['#3e536e']*18
                and all(row[:2]==['#3e536e']*2 for row in lens[2:13])
                and lens[1][18]=='#c4d5ed' and lens[13][:2]==['#3e536e','#c4d5ed'])
        require('half_scale_indicator_original_light_rim',lens[2][2:]==['#c4d5ed']*17
                and all(row[2:]==['#c4d5ed']*17 for row in lens[-2:]))
        require('half_scale_indicator_inner_shadow',all(lens[y][16]=='#3e536e' for y in range(3,12))
                and lens[11][3:17]==['#3e536e']*14)
        point=mail.mapToScene(QPointF(mail.width()/2,mail.height()/2)).toPoint()
        QTest.mousePress(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
        held=capture('HALF-SCALE-PRESSED.png')
        require('half_scale_pressed_inverts_reference_instrument_top',
                [held.pixelColor(top.x(),top.y()+y).name() for y in range(2)]==['#194b63']*2)
        QTest.mouseMove(window,QPointF(20,20).toPoint())
        QTest.mouseRelease(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,QPointF(20,20).toPoint())
        require('half_scale_cancel_restores_every_pixel',capture('HALF-SCALE-CANCELLED.png')==half)
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
