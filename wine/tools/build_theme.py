#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate original Wine styling from the repository's Classic GTK artwork."""
import hashlib
import io
import json
from pathlib import Path
import struct
from PIL import Image
from resources import theme_pe

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'wine/IrixClassic/package'
ART = ROOT/'gtk/IrixClassic/common/assets'
COLORS = {
    'Scrollbar':'193 193 193', 'Background':'70 94 102',
    'ActiveTitle':'181 177 139', 'InactiveTitle':'145 145 145',
    'Menu':'193 193 193', 'Window':'239 239 239', 'WindowFrame':'32 32 32',
    'MenuText':'0 0 0', 'WindowText':'0 0 0', 'TitleText':'0 0 0',
    'ActiveBorder':'193 193 193', 'InactiveBorder':'193 193 193',
    'AppWorkspace':'158 191 191', 'Hilight':'158 191 191', 'HilightText':'0 0 0',
    'ButtonFace':'193 193 193', 'ButtonShadow':'96 96 96', 'GrayText':'119 119 119',
    'ButtonText':'0 0 0', 'InactiveTitleText':'0 0 0', 'ButtonHilight':'236 236 236',
    'ButtonDkShadow':'32 32 32', 'ButtonLight':'204 204 204',
    'InfoText':'0 0 0', 'InfoWindow':'193 193 193', 'ButtonAlternateFace':'153 153 153',
    'HotTrackingColor':'0 0 170', 'GradientActiveTitle':'181 177 139',
    'GradientInactiveTitle':'145 145 145', 'MenuHilight':'158 191 191', 'MenuBar':'193 193 193',
}
PROPERTY_NAMES = {
    'ActiveTitle':'ActiveCaption','InactiveTitle':'InactiveCaption',
    'TitleText':'CaptionText','Hilight':'Highlight','HilightText':'HighlightText',
    'ButtonFace':'BtnFace','ButtonShadow':'BtnShadow','ButtonText':'BtnText',
    'ButtonHilight':'BtnHighlight','ButtonDkShadow':'DkShadow3D','ButtonLight':'Light3D',
    'InfoWindow':'InfoBk','HotTrackingColor':'HotTracking',
    'GradientActiveTitle':'GradientActiveCaption','GradientInactiveTitle':'GradientInactiveCaption',
    'InactiveTitleText':'InactiveCaptionText',
}


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    resources = [('PACKTHEM_VERSION',1,struct.pack('<H',3)),
                 ('COLORNAMES',1,'Classic\0\0'.encode('utf-16le')),
                 ('SIZENAMES',1,'NormalSize\0\0'.encode('utf-16le')),
                 ('FILERESNAMES',1,'CLASSIC_INI\0\0'.encode('utf-16le'))]
    origin = {}
    text = ['; Original IRIX Classic Wine adaptation. GPL-3.0-or-later.',
            '; No font override: applications retain their own fonts and size.',
            '[SysMetrics]']
    text += [PROPERTY_NAMES.get(key,key)+'='+value for key,value in COLORS.items()
             if key != 'ButtonAlternateFace']
    text += ['FlatMenus=False', '', '[globals]', 'TextColor=0 0 0',
             'TextShadowType=None', 'ContentMargins=4,4,3,3']
    added = set()

    def asset(name):
        name = {'tab-disabled':'tab-normal'}.get(name,name)
        token = name.upper().replace('-','_')+'_BMP'
        if token not in added:
            image = Image.open(ART/(name+'.png')).convert('RGBA')
            # Use opaque Classic backing; no dependence on alpha heuristics or magenta keys.
            background = Image.new('RGBA',image.size,(193,193,193,255))
            background.alpha_composite(image)
            stream = io.BytesIO(); background.convert('RGB').save(stream,format='BMP')
            resources.append((2,token,stream.getvalue()[14:]))
            added.add(token)
            origin[str((ART/(name+'.png')).relative_to(ROOT))] = hashlib.sha256((ART/(name+'.png')).read_bytes()).hexdigest()
        return token[:-4]+'.bmp'

    def section(name, image=None, margins=3, true_size=False, color=None, extra=()):
        text.extend(['', '['+name+']', 'TextColor='+('119 119 119' if 'DISABLED' in name.upper() else '0 0 0')])
        if image:
            text.extend(['BgType=ImageFile', 'ImageFile='+asset(image), 'ImageCount=1',
                         'SizingType='+('TrueSize' if true_size else 'Stretch'),
                         f'SizingMargins={margins},{margins},{margins},{margins}',
                         'ContentMargins=5,5,4,4', 'Transparent=False', 'MirrorImage=True'])
        else:
            text.extend(['BgType=BorderFill','BorderSize=1','BorderColor=96 96 96',
                         'FillColor='+(color or '193 193 193')])
        text.extend(extra)

    def states(part, art, mapping=None, margins=3):
        section(part,art+'-normal',margins)
        for state, suffix in (mapping or {'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','DISABLED':'disabled','FOCUSED':'focused'}).items():
            section(part+'('+state+')',art+'-'+suffix,margins)

    states('Button.PushButton','command',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','DISABLED':'disabled','DEFAULTED':'focused','DEFAULTED_ANIMATING':'focused'})
    for control, values in [('CheckBox',['UNCHECKED','CHECKED','MIXED']),('RadioButton',['UNCHECKED','CHECKED'])]:
        family='check' if control=='CheckBox' else 'radio'
        section('Button.'+control,family+'-off',0,True)
        for value, name in zip(values,['off','on','mixed']):
            for state in ['NORMAL','HOT','PRESSED','DISABLED']:
                section('Button.'+control+'('+value+state+')',family+'-'+name+('-disabled' if state=='DISABLED' else ''),0,True)
    section('Button.GroupBox','section-normal',2,extra=['ContentMargins=8,8,14,8'])
    section('Button.GroupBox(DISABLED)','section-disabled',2)
    states('Edit.EditText','input',{'NORMAL':'normal','HOT':'normal','SELECTED':'focused','DISABLED':'disabled','FOCUSED':'focused','READONLY':'normal','ASSIST':'normal'})
    for p in ['Border','Border_NoScroll','Border_HScroll','Border_VScroll','Border_HVScroll']:
        states('Edit.'+p,'input',{'NORMAL':'normal','HOT':'normal','FOCUSED':'focused','DISABLED':'disabled'})
    for p in ['DropDownButton','DropDownButtonRight','DropDownButtonLeft']:
        states('ComboBox.'+p,'stepper-down',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','DISABLED':'disabled'},2)
    for p in ['Border','ReadOnly','Background','TransparentBackground']:
        states('ComboBox.'+p,'input',{'NORMAL':'normal','HOT':'normal','FOCUSED':'focused','PRESSED':'pressed','DISABLED':'disabled'})
    section('ListBox','input-normal',3)
    for p in ['Border','Border_HScroll','Border_VScroll','Border_HVScroll','Border_NoScroll']:
        section('ListBox.'+p,'input-normal',3)
    section('ListView',color='239 239 239')
    section('TreeView',color='239 239 239')
    section('TreeView.Glyph','stepper-right-normal',0,True)
    section('TreeView.Glyph(CLOSED)','stepper-right-normal',0,True)
    section('TreeView.Glyph(OPENED)','stepper-down-normal',0,True)
    states('ScrollBar.ThumbBtnHorz','scroll-grip-h',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','DISABLED':'disabled'},2)
    states('ScrollBar.ThumbBtnVert','scroll-grip-v',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','DISABLED':'disabled'},2)
    for p in ['LowerTrackHorz','UpperTrackHorz','LowerTrackVert','UpperTrackVert','SizeBox']:
        section('ScrollBar.'+p,'scroll-trough-normal',1)
    section('ScrollBar.ArrowBtn','stepper-up-normal',2)
    for direction in ['UP','DOWN','LEFT','RIGHT']:
        for state,suffix in [('NORMAL','normal'),('HOT','normal'),('PRESSED','pressed'),('DISABLED','disabled')]:
            section('ScrollBar.ArrowBtn('+direction+state+')','stepper-'+direction.lower()+'-'+suffix,2)
    for p in ['TabItem','TabItemLeftEdge','TabItemRightEdge','TabItemBothEdge','TopTabItem','TopTabItemLeftEdge','TopTabItemRightEdge','TopTabItemBothEdge']:
        states('Tab.'+p,'tab',{'NORMAL':'normal','HOT':'normal','SELECTED':'toggled','DISABLED':'disabled','FOCUSED':'focused'})
    section('Tab.Pane','section-normal',2)
    section('Tab.Body',color='193 193 193')
    for p in ['Bar','BarVert']:
        section('Progress.'+p,'meter-track-normal',2)
    for p in ['Chunk','ChunkVert','Fill','FillVert']:
        section('Progress.'+p,'meter-fill-normal',1)
    for p in ['Track','TrackVert']:
        section('TrackBar.'+p,'range-track-normal',1)
    for p in ['Thumb','ThumbBottom','ThumbTop','ThumbVert','ThumbLeft','ThumbRight']:
        states('TrackBar.'+p,'palettebutton',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','FOCUSED':'focused','DISABLED':'disabled'},2)
    states('ToolBar.Button','command',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed','DISABLED':'disabled','CHECKED':'pressed','HOTCHECKED':'pressed'})
    states('Header.HeaderItem','column',{'NORMAL':'normal','HOT':'normal','PRESSED':'pressed'})
    section('Menu',color='193 193 193')
    section('Menu.PopupBackground','menupanel-normal',2)
    for p in ['MenuItem','BarItem','PopupItem']:
        section('Menu.'+p,color='193 193 193')
        for state in ['HOT','PUSHED','NORMALHOT']:
            section('Menu.'+p+'('+state+')','menurow-focused',2)
        section('Menu.'+p+'(DISABLED)',color='193 193 193')
    section('Status.Pane','input-normal',2)
    section('Status.GripperPane','input-normal',2)
    section('ToolTip.Standard','menupanel-normal',2)
    section('Window.Dialog',color='193 193 193')
    section('Window.Caption',color=COLORS['ActiveTitle'])
    section('Window.Caption(INACTIVE)',color=COLORS['InactiveTitle'])
    ini='\r\n'.join(text)+'\r\n'
    # Keep repository text in LF; the embedded Wine resource remains CRLF.
    (OUTPUT/'classic.ini').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='')
    resources.append(('TEXTFILE','CLASSIC_INI',ini.encode('utf-16le')))
    description='[Documentation]\r\nDisplayName=IRIX Classic\r\nTooltip=Original Classic artwork for Wine\r\nAuthor=mrmmx31\r\n'
    resources.append(('TEXTFILE','THEMES_INI',description.encode('utf-16le')))
    data=theme_pe(resources)
    (OUTPUT/'IrixClassic.msstyles').write_bytes(data)
    portable='[Theme]\r\nDisplayName=IRIX Classic\r\n\r\n[Control Panel\\Colors]\r\n'
    portable+='\r\n'.join(key+'='+value for key,value in COLORS.items())+'\r\n'
    (OUTPUT/'IrixClassic.theme').write_bytes(b'\xff\xfe'+portable.encode('utf-16le'))
    (OUTPUT/'ORIGEM.json').write_text(json.dumps({'license':'GPL-3.0-or-later',
        'kind':'original_wine_visual_style','author':'mrmmx31','version':'0.1.0',
        'artwork_sources':origin,'msstyles_sha256':hashlib.sha256(data).hexdigest(),
        'fonts':'Inherited from the prefix/application; no system font override.',
        'references':['https://github.com/wine-mirror/wine/blob/wine-10.0/dlls/uxtheme/msstyles.c',
                      'https://learn.microsoft.com/en-us/windows/win32/controls/themesfileformat-overview']},indent=2)+'\n')
    print(OUTPUT/'IrixClassic.msstyles',len(data),'bytes',len(added),'original Classic bitmaps')


if __name__=='__main__':
    build()
