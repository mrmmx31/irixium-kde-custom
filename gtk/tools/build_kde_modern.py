#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build an independent Irixium-KDE theme from Modern's own CSS and images.

Only the published KDE color-role registry and integer symbolic-mask mechanism
are shared with Classic. Modern's 1277-line source, metrics, CSS bevels, artwork
and plain GTK2 RC are inspected and transformed independently. The source theme
is never modified. Generation does not select a theme or change a profile.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from gtk2_modern_palette import gtk2_rc  # noqa: E402
import adaptive_assets  # noqa: E402
import build_kde_classic as classic  # noqa: E402

SOURCE = HERE.parent/'Irixium'
DESTINATION = HERE.parent/'Irixium-KDE'
ROLE_STATES = classic.ROLE_STATES
STATIC_ROLES = classic.STATIC_ROLES
SYMBOL = re.compile(r'@([a-zA-Z_][a-zA-Z0-9_]*)')
URL = re.compile(r'url\("([^"\n]+\.png)"\)')
COLOR_PROPERTIES = classic.COLOR_PROPERTIES | {'background', 'border-top', 'border-left', 'border-right', 'border-bottom', '-GtkIMHtml-hyperlink-color'}
TONES = {'white_color':255, 'lighterA_color':205, 'lighterB_color':196, 'lighterC_color':185,
         'base_color':193, 'base_colour':193, 'darkerA_color':153, 'darkerB_color':132,
         'darkerC_color':145, 'darkerD_color':96, 'groove_color':106, 'shadowLit_color':85}
SOURCE_ALIASES = set(TONES) | {'black_color','selected_color','entry_red_color','scale_color','disabled_color',
    'link_color','link_hover_color','tooltip_color','active_header_color','backdrop_header_color',
    'rubberband_border_color','rubberband_bg_color','theme_base_color','theme_text_color','theme_bg_color',
    'theme_fg_color','theme_selected_bg_color','theme_selected_fg_color','theme_tooltip_bg_color','theme_tooltip_fg_color'}


def role(name: str, state: int=0) -> str:
    return '@'+(STATIC_ROLES[name] if name in STATIC_ROLES else ROLE_STATES[name][state])


def definitions() -> str:
    values={}
    normal={'window_bg':'#c1c1c1','window_fg':'#000000','view_bg':'#c1c1c1','view_fg':'#000000',
        'selection_bg':'#648bb3','selection_fg':'#ffffff','button_bg':'#c1c1c1','button_fg':'#000000',
        'header_bg':'#c1c1c1','header_fg':'#000000','titlebar_bg':'#c1c1c1','titlebar_fg':'#000000',
        'error':'#ff0000','warning':'#ffff00','success':'#006600','button_hover':'#648bb3','button_focus':'#648bb3'}
    for name,names in ROLE_STATES.items():
        for state,symbol in enumerate(names):
            fallback = normal.get(name, '#606060')
            if state>=2 and name.endswith('_fg'):fallback='#606060'
            if state>=2 and name=='button_bg':fallback='#919191'
            values.setdefault(symbol,fallback)
    values.update({'tooltip_background_breeze':'#d0cfb2','tooltip_text_breeze':'#000000',
        'tooltip_border_breeze':'#555555','link_color_breeze':'#0000cd','link_visited_color_breeze':'#660066'})
    for alias,semantic in classic.ALIASES.items():
        values[alias]=role(semantic,2 if alias.startswith('insensitive_')else 1 if alias=='inactive_selection'else 0)
    return ''.join('@define-color '+name+' '+value+';\n'for name,value in values.items())


def family(selector: str) -> str:
    if 'tooltip' in selector:return 'tooltip'
    leaf=re.split(r'\s+|\s*>\s*',selector.strip())[-1]
    if re.match(r'^(label|image)\b',leaf) and re.search(r'\bbutton\b',selector):return 'button'
    if re.search(r'\b(button|check|radio|slider|arrow|switch)\b',leaf) or re.search(r'\.(?:path-bar-)?button\b',leaf):return 'button'
    if 'headerbar' in selector:return 'header'
    if '.titlebar' in selector:return 'titlebar'
    if re.search(r'\b(menubar|toolbar)\b',selector) and not re.search(r'\bmenuitem\b',selector):return 'header'
    if re.search(r'\b(entry|textview|treeview|iconview|flowbox|list|row|listview|gridview|columnview)\b',selector) or '.view' in selector:
        if 'sidebar' not in selector:return 'view'
    if re.search(r'\b(scrollbar|scale|progressbar|switch|tab)\b',selector):return 'button'
    return 'window'


def selection(selector: str) -> bool:
    return ':selected' in selector or bool(re.search(r'\bselection\b',selector)) or bool(re.search(r'\b(menuitem|modelbutton).*:(hover|active|checked)',selector))


def symbol(name: str, prop: str, selector: str, state: int) -> str:
    group=family(selector)
    face=role(group+'_bg',state)
    fg=role('selection_fg' if selection(selector) else group+'_fg',state)
    if name in ('black_color','theme_fg_color','theme_text_color'):
        return fg if prop=='color'else role(group+'_fg',state)
    if name=='white_color' and prop=='color':return fg
    if name=='disabled_color':return role(group+'_fg',max(2,state)) if prop=='color'else role('borders',max(2,state))
    if name in ('selected_color','scale_color','theme_selected_bg_color'):return role('selection_bg',state)
    if name=='theme_selected_fg_color':return role('selection_fg',state)
    if name in ('theme_bg_color','theme_base_color'):return role('window_bg'if name=='theme_bg_color'else'view_bg',state)
    if name in ('tooltip_color','theme_tooltip_bg_color'):return role('tooltip_bg')
    if name=='theme_tooltip_fg_color':return role('tooltip_fg')
    if name in ('active_header_color','backdrop_header_color'):return role(('titlebar'if group=='titlebar'else'header')+'_bg',state)
    if name=='entry_red_color':return role('selection_bg'if 'switch:checked' in selector else'view_bg',state)
    if name=='link_color':return role('visited'if ':visited'in selector else'link')
    if name=='link_hover_color':return role('button_hover',state)
    if name=='rubberband_border_color':return 'shade('+role('selection_bg',state)+', 0.8)'
    if name=='rubberband_bg_color':return 'alpha('+role('selection_bg',state)+', 0.05)'
    if name in TONES:
        if prop=='background-color' and group in ('view','header','titlebar','tooltip'):
            return face
        return classic.tone(face,TONES[name],193)
    raise ValueError('Unmapped Modern color symbol: '+name)


def color_value(value: str, prop: str, selector: str, state: int) -> str:
    return SYMBOL.sub(lambda match:symbol(match[1],prop,selector,state),value)


def asset_color(asset: str, tag: str, state: int=0) -> str:
    color,*metadata=tag.split(':')
    mark=next((part for part in metadata if part.startswith('ink=')),None)
    rgb=tuple(bytes.fromhex(color[1:]))
    if mark:
        weight=float(mark[4:]);gray=(rgb[0]-133*weight)/(1-weight) if weight<1 else 193
        return 'mix('+classic.tone(role('button_bg',state),round(gray),193)+', '+role('button_fg',2)+', '+format(weight,'.12g')+')'
    if rgb[0]!=rgb[1] or rgb[1]!=rgb[2]:
        if asset.startswith('checkbox_'):weight=(rgb[0]-rgb[1])/255;gray=rgb[1]/(1-weight) if weight<1 else 193;ink='error'
        elif asset.startswith('option_'):weight=(rgb[0]-rgb[2])/255;gray=rgb[2]/(1-weight) if weight<1 else 193;ink='warning'
        else:raise ValueError('Unmapped colored Modern artwork: '+asset+' '+tag)
        return 'mix('+classic.tone(role('button_bg',state),round(gray),193)+', '+role(ink,state)+', '+format(weight,'.12g')+')'
    anchor=193
    return classic.tone(role('button_bg',state),rgb[0],anchor)


def native_icon(source: Path):
    """Rasterize the upstream 17px icon into its native unchanged 16px box.

    GTK3 and GTK4 draw this image through Cairo's bilinear texture path. Doing
    that once before separating color masks prevents partially transparent
    seams when independent symbolic layers are reduced from 17px to 16px.
    No GUI, display or profile is opened. Cairo is a GTK runtime dependency.
    """
    from PIL import Image
    cairo=ctypes.CDLL('libcairo.so.2');pointer=ctypes.c_void_p;integer=ctypes.c_int;double=ctypes.c_double
    def function(name,result,*args):
        value=getattr(cairo,name);value.restype=result;value.argtypes=list(args);return value
    src=function('cairo_image_surface_create_from_png',pointer,ctypes.c_char_p)(str(source).encode())
    dst=function('cairo_image_surface_create',pointer,integer,integer,integer)(0,16,16)
    destroy=function('cairo_surface_destroy',None,pointer);cr=None
    try:
        status=function('cairo_surface_status',integer,pointer)
        if status(src) or status(dst):raise ValueError('Cairo could not rasterize Modern icon: '+str(source))
        cr=function('cairo_create',pointer,pointer)(dst)
        function('cairo_scale',None,pointer,double,double)(cr,16/17,16/17)
        function('cairo_set_source_surface',None,pointer,pointer,double,double)(cr,src,0,0)
        pattern=function('cairo_get_source',pointer,pointer)(cr)
        function('cairo_pattern_set_filter',None,pointer,integer)(pattern,4) # CAIRO_FILTER_BILINEAR
        function('cairo_paint',None,pointer)(cr)
        function('cairo_surface_flush',None,pointer)(dst)
        stride=function('cairo_image_surface_get_stride',integer,pointer)(dst)
        address=function('cairo_image_surface_get_data',pointer,pointer)(dst)
        data=ctypes.string_at(address,stride*16);pixels=[]
        for y in range(16):
            for x in range(16):
                word=int.from_bytes(data[y*stride+x*4:y*stride+x*4+4],sys.byteorder)
                alpha=word>>24;red=(word>>16)&255;green=(word>>8)&255;blue=word&255
                if alpha:
                    red,green,blue=(min(255,(value*255+alpha//2)//alpha)for value in(red,green,blue))
                pixels.append((red,green,blue,alpha))
        image=Image.new('RGBA',(16,16));image.putdata(pixels);return image
    finally:
        if cr:function('cairo_destroy',None,pointer)(cr)
        destroy(dst);destroy(src)


def svg_mask(pixels: list[list],colors: list[str]) -> str:
    """Use integer rectangles, including native edge alpha, without scaling."""
    payload=adaptive_assets._svg(pixels,colors)
    for channel,color in zip(adaptive_assets.CHANNELS,colors):
        alpha=int(next((part[6:]for part in color.split(':')[1:]if part.startswith('alpha=')),'255'))
        if alpha!=255:payload=payload.replace('class="'+channel+'"','class="'+channel+'" fill-opacity="'+format(alpha/255,'.17g')+'"')
    return payload.replace('GPL-3.0-or-later','CC-BY-NC-SA-4.0')


def masks(destination: Path) -> dict:
    from PIL import Image
    destination.mkdir(parents=True,exist_ok=True);result={};files={}
    for source in sorted((SOURCE/'gtk-3.0/assets').glob('*.png')):
        asset=source.stem;original=Image.open(source).convert('RGBA');image=original
        if any(p[3]not in(0,255)for p in image.getdata()):raise ValueError('Modern asset has partial alpha: '+asset)
        icon=asset.startswith(('checkbox_','option_'))
        if icon:
            if image.size!=(17,17):raise ValueError('Unexpected native Modern icon size: '+asset)
            image=native_icon(source)
        original_name=re.sub(r'_(disable|hover)$','',asset)
        normal_source=source.with_name(original_name+'.png')
        normal=(native_icon(normal_source)if icon else Image.open(normal_source).convert('RGBA'))if normal_source.exists()else image
        pixels=[]
        for y in range(image.height):
            row=[]
            for x in range(image.width):
                red,green,blue,alpha=image.getpixel((x,y));tag='#%02x%02x%02x'%(red,green,blue)if alpha else None
                if tag and alpha!=255:tag+=':alpha='+str(alpha)
                old=normal.getpixel((x,y))
                if tag and ('_disable'in asset)and(old[0]!=old[1]or old[1]!=old[2]):tag+=':ink='+format((old[0]-min(old[:3]))/255,'.12g')
                row.append(tag)
            pixels.append(row)
        colors=sorted({p for row in pixels for p in row if p});layers=[]
        for first in range(0,len(colors),3):
            group=colors[first:first+3];filename=asset.replace('_','-')+'-'+str(first//3)+'-symbolic.svg'
            text=svg_mask(pixels,group)
            text='<!-- Derived from TheJollyDuck Irixium artwork; see ../README.upstream.md -->\n'+text
            (destination/filename).write_text(text);files[filename]=hashlib.sha256(text.encode()).hexdigest();layers.append({'file':filename,'colors':group})
        result[asset]={'width':image.width,'height':image.height,'source_size':list(original.size),'sampling':'native Cairo bilinear 17px to unchanged GTK 16px'if icon else'integer original pixels','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'layers':layers}
    manifest={'schema':1,'assets':result,'files':files,'license':'CC-BY-NC-SA-4.0; original upstream README attribution retained'}
    (destination/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest


def image_expression(asset: str,state: int,manifest: dict) -> str:
    item=manifest['assets'][asset];images=[]
    for layer in item['layers']:
        palette=', '.join(channel+' '+asset_color(asset,color,state)for channel,color in zip(adaptive_assets.CHANNELS,layer['colors']))
        images.append('-gtk-recolor(url("adaptive/'+layer['file']+'"), '+palette+')')
    return ', '.join(images)


def transformed(selector: str,properties: dict[str,str],state: int,manifest: dict,version: str,colors_only=False) -> dict:
    output={}
    for prop,value in properties.items():
        if version=='4'and prop.startswith('-Gtk'):continue
        if colors_only and prop not in COLOR_PROPERTIES:continue
        match=URL.fullmatch(value)
        if match:
            asset=Path(match[1]).stem
            if state>=2 and asset.endswith(('_hover','_check','_ind','_non')):
                alternate=re.sub(r'_hover$','',asset)+'_disable'
                if alternate in manifest['assets']:asset=alternate
            expression=image_expression(asset,state,manifest)
            if prop=='-gtk-icon-source':
                # GTK accepts only one icon-source image. Multiple independent
                # symbolic layers use the native background painter instead;
                # The upstream 17px image was rasterized in its native 16px
                # allocation before separating colors; never rescale masks.
                output.update({'-gtk-icon-source':'none','background-image':expression,'background-repeat':'no-repeat','background-position':'center','background-size':'16px 16px'})
            elif prop=='background-image':output[prop]=expression
            else:raise ValueError('Unexpected Modern image property: '+prop)
        elif prop in COLOR_PROPERTIES:output[prop]=color_value(value,prop,selector,state)
        elif not colors_only:output[prop]=value
    return output


def stylesheet(version: str,manifest: dict) -> str:
    rules=classic.rules(SOURCE/'gtk-3.0/gtk.css');output=[]
    for selector,properties in rules:
        for individual in selector.split(','):
            individual=individual.strip().replace('*link','link')
            state=int(':backdrop'in individual)+2*int(':disabled'in individual)
            output.append(classic.render_rule(individual,transformed(individual,properties,state,manifest,version)))
    for state,suffix in((1,':backdrop'),(2,':disabled'),(3,':disabled:backdrop')):
        for selector,properties in rules:
            if selector=='*'or not any(prop in COLOR_PROPERTIES for prop in properties):continue
            for individual in selector.split(','):
                individual=individual.strip().replace('*link','link')
                if ':backdrop'in individual or ':disabled'in individual:continue
                output.append(classic.render_rule(individual+suffix,transformed(individual,properties,state,manifest,version,True)))
    # Modern's source leaves several foregrounds/backgrounds to inherited GTK
    # defaults. Bind these actual nodes explicitly to the corresponding KDE
    # set without changing their original spacing, borders or bevel geometry.
    for state,suffix in((0,''),(1,':backdrop'),(2,':disabled'),(3,':disabled:backdrop')):
        for selector,group in(('window.background','window'),('headerbar','header'),('.titlebar:not(headerbar)','titlebar'),
                               ('menu','window'),('popover > contents','window'),('entry','view'),('textview text','view'),
                               ('list','view'),('listview','view'),('gridview','view'),('columnview','view'),('tooltip','tooltip')):
            output.append(classic.render_rule(selector+suffix,{'color':role(group+'_fg',state),'background-color':role(group+'_bg',state)}))
        for selector in('selection','row:selected','menuitem:hover','menuitem:active','modelbutton:hover','modelbutton:active','button:active','button:checked'):
            output.append(classic.render_rule(selector+suffix,{'color':role('selection_fg',state)}))
    return '/* Generated from TheJollyDuck Irixium CSS; GPL-3.0-or-later. */\n'+definitions()+''.join(output)


def build(destination: Path=DESTINATION, *, theme_name: str='Irixium-KDE') -> dict:
    if theme_name not in ('Irixium-KDE','Irixium-KDE-Reload'):
        raise ValueError('Unknown generated Modern theme name: '+theme_name)
    destination=Path(destination)
    for folder in('gtk-2.0','gtk-3.0','gtk-4.0'):(destination/folder).mkdir(parents=True,exist_ok=True)
    manifest=masks(destination/'common/adaptive')
    for version in('3','4'):
        (destination/'common'/('gtk-'+version+'.css')).write_text(stylesheet(version,manifest))
        (destination/('gtk-'+version+'.0')/'gtk.css').write_text('@import url("../common/gtk-'+version+'.css");\n')
        (destination/('gtk-'+version+'.0')/'gtk-dark.css').write_text('@import url("gtk.css");\n')
    (destination/'gtk-2.0/gtkrc').write_text(gtk2_rc((SOURCE/'gtk-2.0/gtkrc').read_text()))
    (destination/'LICENSE').write_bytes((SOURCE/'LICENSE').read_bytes())
    (destination/'README.upstream.md').write_bytes((SOURCE/'README.md').read_bytes())
    (destination/'README.md').write_text('# Irixium-KDE\n\nGenerated KDE color-role variant of TheJollyDuck’s Irixium. Original Irixium remains unchanged.\nCSS retains the original dimensions and bevels. Check/radio artwork is rasterized with native Cairo bilinear sampling from 17px into the unchanged 16px GTK allocation before color separation; other symbolic artwork retains the source PNG pixels.\nUpstream code is GPL-3.0; upstream images and their derived masks are CC-BY-NC-SA-4.0 as stated in README.upstream.md.\n\nGTK2 uses the original plain RC without an added engine or image dependency. Native runtime RC reparsing is necessary for open GTK2 applications.\nGTK3/4 consume KDE GTK Config’s exported *_breeze names. Automatic reload of already-open GTK4 applications depends on GTK itself; new applications read current colors.\nGTK1.2 is intentionally outside this KDE color-role variant.\n')
    (destination/'index.theme').write_text('[Desktop Entry]\nType=X-GNOME-Metatheme\nName=' + theme_name + '\nComment=Irixium geometry with native KDE colors\nEncoding=UTF-8\n\n[X-GNOME-Metatheme]\nGtkTheme=' + theme_name + '\n')
    receipt={'schema':1,'name':theme_name,'source':{str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(SOURCE.rglob('*'))if p.is_file()},
        'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'dependencies':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()for path in(ROOT/'tools/gtk2_modern_palette.py',HERE/'adaptive_assets.py',HERE/'build_kde_classic.py')},
        'compatibility':['upstream base_colour typo resolves to base_color only in generated theme','GTK4 omits removed -Gtk widget-style properties','upstream *link selector is normalized to link','multicolor check/radio icon-source uses fixed 16px masks of native Cairo sampling without changing its allocation','dark preference imports the same native role stylesheet instead of falling back to Adwaita'],
        'files':{str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(destination.rglob('*'))if p.is_file()and p!=destination/'MANIFEST.json'}}
    (destination/'MANIFEST.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,default=DESTINATION);parser.add_argument('--theme-name',choices=('Irixium-KDE','Irixium-KDE-Reload'),default='Irixium-KDE');args=parser.parse_args()
    receipt=build(args.output_dir,theme_name=args.theme_name);print(f"Built {receipt['name']} / {len(receipt['files'])} files; no profile selected")


if __name__=='__main__':main()
