# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure semantic color adaptation of the reviewed canonical Classic artwork.

Only the caller's generated copy changes. Window, button, view, selection,
tooltip and glyph roles come from the native KDE GtkConfig export. Startup
Base/AlternateBase/Shadow come separately from the native Qt platform palette.
The caller owns file paths, session notifications, journaling and rollback.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from kvantum_palette_config import adapt_config

SOURCE_SVG_SHA256 = '73329f86299faa81d6953f5807623cb446f958154b72e75ed9ab5219554cba3d'
SOURCE_CONFIG_SHA256 = 'd3a08e95dc09adbbeea569fdb72fe27dd547c758927a4bda411ecd29c399b08e'

# Family identity is part of the color contract. This is not a global hex map.
MODES = {}
def _families(mode, names):
    for name in names.split():
        if name in MODES: raise ValueError('Duplicate family '+name)
        MODES[name] = mode
_families('window', 'ic-menupanel ic-window ic-tool ic-common ic-group ic-tabframe ic-menu ic-menubaritem ic-menuitem ic-tab ic-toolbar ic-grip ic-splitgrip ic-slidergrip ic-notebook ic-notebookbase ic-notebookpage ic-section-frame ic-divider-panel ic-divider-grip ic-resize-mark ic-sizegrip ic-finish-toolbar header-separator dial dial-handle dial-notches')
_families('button', 'ic-button ic-command ic-palettebutton ic-toolbarbutton ic-option ic-spin ic-thumb ic-slidercursor ic-groove ic-scroll-groove ic-scroll-thumb ic-scroll-grip ic-range-thumb ic-range-mark ic-meter-track ic-optionmark')
_families('input', 'ic-input ic-entry')
_families('inset', 'ic-inset')
_families('view', 'ic-view')
_families('fill', 'ic-meter-fill ic-progress')
_families('range', 'ic-range-track')
_families('selection', 'ic-item ic-row-panel')
_families('menurow', 'ic-menurow ic-menutitle')
_families('header', 'ic-bar ic-menustrip ic-column-panel ic-dock-strip')
_families('tooltip', 'ic-hint-panel')
_families('legacy-check', 'ic-check ic-radio')
_families('check', 'ic-checkmark')
_families('radio', 'ic-radiomark')
_families('glyph-button', 'ic-arrow ic-spinmark ic-finish-spinmark ic-column-mark')
_families('glyph-title', 'ic-mdi-mark')
_families('glyph-view', 'ic-branch-mark')
_families('glyph-window', 'ic-tab-close ic-tab-left ic-tab-right ic-tabmark')
_families('tree', 'ic-tree')
_families('menuindicator', 'ic-menuindicator')
_families('focus', 'ic-focus ic-button-default ic-command-default dial-focus')
_families('scrollarrow', 'ic-scrollarrow')
_families('title', 'ic-mdi-title')
FAMILIES = sorted(MODES, key=len, reverse=True)
STATES = ('normal','focused','pressed','toggled','disabled','toggledFocused','toggledPressed')
ROLE = {
 'window': ('theme_bg_color_breeze','theme_unfocused_bg_color_breeze','insensitive_bg_color_breeze','insensitive_unfocused_bg_color_breeze'),
 'title-fg': ('theme_titlebar_foreground_breeze','theme_titlebar_foreground_backdrop_breeze','theme_titlebar_foreground_insensitive_breeze','theme_titlebar_foreground_insensitive_backdrop_breeze'),
 'window-fg': ('theme_fg_color_breeze','theme_unfocused_fg_color_breeze','insensitive_fg_color_breeze','insensitive_unfocused_fg_color_breeze'),
 'button': ('theme_button_background_normal_breeze','theme_button_background_backdrop_breeze','theme_button_background_insensitive_breeze','theme_button_background_backdrop_insensitive_breeze'),
 'button-fg': ('theme_button_foreground_normal_breeze','theme_button_foreground_backdrop_breeze','theme_button_foreground_insensitive_breeze','theme_button_foreground_backdrop_insensitive_breeze'),
 'view': ('theme_base_color_breeze','theme_unfocused_base_color_breeze','insensitive_base_color_breeze','theme_unfocused_view_bg_color_breeze'),
 'view-fg': ('theme_text_color_breeze','theme_unfocused_text_color_breeze','insensitive_base_fg_color_breeze','theme_unfocused_view_text_color_breeze'),
 'selection': ('theme_selected_bg_color_breeze','theme_unfocused_selected_bg_color_breeze','insensitive_selected_bg_color_breeze','insensitive_unfocused_selected_bg_color_breeze'),
 'selection-fg': ('theme_selected_fg_color_breeze','theme_unfocused_selected_fg_color_breeze','insensitive_selected_fg_color_breeze','insensitive_unfocused_selected_fg_color_breeze'),
 'header': ('theme_header_background_breeze','theme_header_background_backdrop_breeze','theme_header_background_backdrop_breeze','theme_header_background_backdrop_breeze'),
 'error': ('error_color_breeze','error_color_backdrop_breeze','error_color_insensitive_breeze','error_color_insensitive_backdrop_breeze'),
 'link': ('link_color_breeze',)*4,
 'tooltip': ('tooltip_background_breeze',)*4,
 'tooltip-fg': ('tooltip_text_breeze',)*4,
 'focus': ('theme_button_decoration_focus_breeze','theme_button_decoration_focus_backdrop_breeze','theme_button_decoration_focus_insensitive_breeze','theme_button_decoration_focus_backdrop_insensitive_breeze'),
}
# Populated once from the reviewed canonical source, not from caller input.
KNOWN_COLORS = {'dial': ('#4c4c4c', '#c1c1c1', '#e1e1e1'), 'dial-focus': ('#000000',), 'dial-handle': ('#4c4c4c', '#737373', '#999999', '#cccccc', '#e1e1e1'), 'dial-notches': ('#4c4c4c',), 'header-separator': ('#4c4c4c', '#c1c1c1', '#e1e1e1'), 'ic-arrow': ('#4c4c4c', '#858585', '#919191', '#ececec'), 'ic-bar': ('#919191', '#c1c1c1', '#ececec'), 'ic-branch-mark': ('#000000', '#858585'), 'ic-button': ('#252525', '#4c4c4c', '#737373', '#858585', '#999999', '#cccccc', '#e1e1e1'), 'ic-button-default': ('#000000',), 'ic-check': ('#000000', '#606060', '#858585', '#919191', '#999999', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-checkmark': ('#606060', '#660000', '#919191', '#999999', '#b3b3b3', '#c1c1c1', '#cc0000', '#cccccc', '#dfdfdf', '#e1e1e1'), 'ic-column-mark': ('#000000', '#858585'), 'ic-column-panel': ('#4c4c4c', '#737373', '#8c8c8c', '#919191', '#aaaaaa', '#b1b1b1', '#b3b3b3', '#bcbcbc', '#c1c1c1', '#cccccc', '#d7d7d7', '#e1e1e1'), 'ic-command': ('#252525', '#4c4c4c', '#737373', '#858585', '#919191', '#999999', '#cccccc', '#e1e1e1'), 'ic-command-default': ('#000000',), 'ic-common': ('#606060', '#919191', '#b1b1b1', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-divider-grip': ('#4c4c4c', '#858585', '#cccccc', '#e1e1e1'), 'ic-divider-panel': ('#4c4c4c', '#8c8c8c', '#b1b1b1', '#c1c1c1', '#d1d1d1', '#e1e1e1'), 'ic-dock-strip': ('#4c4c4c', '#737373', '#8c8c8c', '#aaaaaa', '#b1b1b1', '#bcbcbc', '#c1c1c1', '#cccccc', '#e1e1e1'), 'ic-entry': ('#606060', '#919191', '#b1b1b1', '#b6b6aa', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-finish-spinmark': ('#4c4c4c', '#858585', '#cccccc', '#ececec'), 'ic-finish-toolbar': ('#606060', '#919191', '#ececec'), 'ic-focus': ('#000000',), 'ic-grip': ('#606060', '#ececec'), 'ic-groove': ('#606060', '#919191', '#999999', '#dfdfdf', '#ececec'), 'ic-group': ('#606060', '#919191', '#b1b1b1', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-hint-panel': ('#4c4c4c', '#737373', '#8c8c8c', '#aaaaaa', '#b1b1b1', '#bcbcbc', '#c1c1c1', '#cccccc', '#e1e1e1'), 'ic-input': ('#000000', '#2f2f2f', '#606060', '#858585', '#919191', '#a0a0a0', '#b6b6aa', '#c1c1c1', '#cccccc', '#dfdfdf', '#ececec'), 'ic-inset': ('#2f2f2f', '#606060', '#858585', '#919191', '#a0a0a0', '#c1c1c1', '#cccccc', '#dfdfdf', '#ececec'), 'ic-item': ('#9ebfbf',), 'ic-mdi-mark': ('#000000', '#858585', '#e1e1e1'), 'ic-mdi-title': ('#999999', '#a39f83'), 'ic-menu': ('#606060', '#919191', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-menubaritem': ('#606060', '#919191', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-menuindicator': ('#606060', '#858585', '#919191', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-menuitem': ('#606060', '#919191', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-menupanel': ('#606060', '#919191', '#c1c1c1', '#ececec'), 'ic-menurow': ('#606060', '#919191', '#b3b3b3', '#dfdfdf', '#ececec'), 'ic-menustrip': ('#606060', '#919191', '#c1c1c1', '#ececec'), 'ic-menutitle': ('#606060', '#919191', '#b3b3b3', '#dfdfdf', '#ececec'), 'ic-meter-fill': ('#4c4c4c', '#719e9e', '#737373', '#8c8c8c', '#8eaaaa', '#aaaaaa', '#b1b1b1', '#bcbcbc', '#cccccc', '#e1e1e1'), 'ic-meter-track': ('#4c4c4c', '#737373', '#8c8c8c', '#999999', '#aaaaaa', '#b1b1b1', '#bcbcbc', '#cccccc', '#e1e1e1'), 'ic-notebook': ('#606060', '#919191', '#a7a7a7', '#b8b8b8', '#c1c1c1', '#ececec'), 'ic-notebookbase': ('#c1c1c1',), 'ic-notebookpage': ('#606060', '#919191', '#c1c1c1', '#cccccc', '#ececec'), 'ic-option': ('#252525', '#4c4c4c', '#737373', '#858585', '#919191', '#999999', '#a0a0a0', '#cccccc', '#dfdfdf', '#e1e1e1'), 'ic-optionmark': ('#4c4c4c', '#606060', '#858585', '#999999', '#cccccc', '#ececec'), 'ic-palettebutton': ('#4c4c4c', '#737373', '#858585', '#919191', '#999999', '#cccccc', '#e1e1e1'), 'ic-progress': ('#606060', '#919191', '#9ebfbf', '#dfdfdf', '#ececec'), 'ic-radio': ('#000000', '#606060', '#858585', '#c1c1c1', '#ececec'), 'ic-radiomark': ('#000066', '#0000cc', '#737373', '#919191', '#999999', '#b3b3b3', '#c1c1c1', '#cccccc', '#dfdfdf', '#e1e1e1'), 'ic-range-mark': ('#4c4c4c', '#858585', '#cccccc', '#e1e1e1'), 'ic-range-thumb': ('#4c4c4c', '#737373', '#8c8c8c', '#999999', '#aaaaaa', '#b1b1b1', '#bcbcbc', '#cccccc', '#e1e1e1'), 'ic-range-track': ('#4c4c4c', '#719e9e', '#737373', '#8c8c8c', '#999999', '#aaaaaa', '#b1b1b1', '#bcbcbc', '#cccccc', '#e1e1e1'), 'ic-resize-mark': ('#4c4c4c', '#858585', '#cccccc', '#e1e1e1'), 'ic-row-panel': ('#9ebfbf', '#b3c3c3', '#d7e0dc'), 'ic-scroll-grip': ('#000000', '#858585', '#cccccc', '#e1e1e1'), 'ic-scroll-groove': ('#000000', '#4c4c4c', '#737373', '#999999', '#cccccc'), 'ic-scroll-thumb': ('#000000', '#4c4c4c', '#737373', '#858585', '#999999', '#b3b3b3', '#cccccc', '#e1e1e1'), 'ic-scrollarrow': ('#4c4c4c', '#737373', '#858585', '#8c8c8c', '#999999', '#b3b3b3', '#cccccc', '#e1e1e1'), 'ic-section-frame': ('#919191', '#e1e1e1'), 'ic-sizegrip': ('#606060',), 'ic-slidercursor': ('#252525', '#4c4c4c', '#858585', '#999999', '#e1e1e1'), 'ic-slidergrip': ('#606060', '#ececec'), 'ic-spin': ('#4c4c4c', '#737373', '#919191', '#999999', '#a0a0a0', '#cccccc', '#dfdfdf', '#e1e1e1'), 'ic-spinmark': ('#4c4c4c', '#858585', '#cccccc', '#ececec'), 'ic-splitgrip': ('#606060', '#ececec'), 'ic-tab': ('#606060', '#919191', '#a7a7a7', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-tab-close': ('#000000',), 'ic-tab-left': ('#4c4c4c', '#858585'), 'ic-tab-right': ('#4c4c4c', '#858585'), 'ic-tabframe': ('#606060', '#919191', '#b1b1b1', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-tabmark': ('#000000', '#606060', '#858585', '#ececec'), 'ic-thumb': ('#252525', '#4c4c4c', '#858585', '#999999', '#e1e1e1'), 'ic-tool': ('#606060', '#919191', '#c1c1c1', '#dfdfdf', '#ececec'), 'ic-toolbar': ('#606060', '#919191', '#ececec'), 'ic-toolbarbutton': ('#4c4c4c', '#737373', '#919191', '#999999', '#cccccc', '#e1e1e1'), 'ic-tree': ('#000000', '#858585', '#efefef'), 'ic-view': ('#606060', '#919191', '#b1b1b1', '#c1c1c1', '#dfdfdf', '#ececec', '#efefef'), 'ic-window': ('#c1c1c1',)}
SUFFIX_TOKENS = frozenset('bottom bottomleft bottomright checked close disabled down focused handle horizontal inactive left leftjunct maximize minimize minus normal plus pressed restore right rightjunct separator shade tear tearoff tick toggled toggledFocused toggledPressed top topleft topright tristate unchecked up vertical'.split())
EXPECTED_GEOMETRY_SHA256 = '498488c5e62247e42b85c0b072c1e210bdfa18663eca769f71b9b7ad1f5dfb91'
_HEX = re.compile(r'#[0-9a-fA-F]{6}\Z')
_GROUP = re.compile(r'(<g\b[^>]*\bid="([^"]+)"[^>]*>)(.*?)(</g>)', re.S)
_RECT = re.compile(r'<rect\b[^>]*/>')
_FILL = re.compile(r'\bfill="(#[0-9a-fA-F]{6})"')


def family(identifier):
    value = identifier
    for context in ('menu-','item-','floating-'):
        if value.startswith(context): value=value[len(context):]; break
    found = next((prefix for prefix in FAMILIES if value == prefix or value.startswith(prefix+'-')), None)
    if found is None: raise ValueError('Unknown SVG family: '+identifier)
    # Alias contexts have a limited, explicit role; do not classify an
    # unrelated new menu-/item-/floating- control by stripping its name.
    if identifier.startswith('floating-') and found != 'ic-notebook': raise ValueError('Unknown floating alias')
    if identifier.startswith('item-') and found != 'ic-checkmark': raise ValueError('Unknown item alias')
    if identifier.startswith('menu-') and found not in ('ic-check','ic-radio','ic-checkmark','ic-radiomark'): raise ValueError('Unknown menu alias')
    suffix = value[len(found):].strip('-')
    if suffix and any(token not in SUFFIX_TOKENS for token in suffix.split('-')):
        raise ValueError('Unknown SVG family suffix: '+identifier)
    if sum(token in STATES for token in suffix.split('-')) > 1:
        raise ValueError('Ambiguous SVG state: '+identifier)
    return found


def flags(identifier):
    tokens=identifier.split('-')
    state=next((token for token in tokens if token in STATES),'normal')
    return state, 'inactive' in tokens, state=='disabled'


def role(kind, identifier):
    _state,inactive,disabled=flags(identifier)
    return ROLE[kind][(2 if disabled else 0)+(1 if inactive else 0)]


def gray_tone(kind, identifier, color, anchor):
    rgb=tuple(int(color[n:n+2],16) for n in (1,3,5))
    if rgb[0] != rgb[1] or rgb[1] != rgb[2]: raise ValueError('Unclassified colored surface '+identifier+' '+color)
    value=rgb[0]
    ratio=(anchor-value)/anchor if value < anchor else (value-anchor)/(255-anchor)
    return {'role':role(kind,identifier),'mix':ratio,'endpoint':'#000000' if value<anchor else '#ffffff'}


def foreground(kind, identifier, color):
    # Preserve the glyph's original gray/emboss tone relative to its text role.
    # In particular, gray arrows are not globally turned into black text.
    anchor=119 if flags(identifier)[2] else 0
    return gray_tone(kind+'-fg',identifier,color,anchor)


def scroll_mask(identifier):
    state,_,disabled=flags(identifier)
    direction=next((token for token in identifier.split('-') if token in ('up','down','left','right')),None)
    if direction is None: raise ValueError('Scrollarrow direction absent')
    rows=('00010000','00011000','00011000','00111100','00111100','01111110','01111110','11111111','11111111')
    points={(5+x,4+y) for y,row in enumerate(rows) for x,bit in enumerate(row) if bit=='1'}
    if direction in ('down','right'):points={(17-x,17-y) for x,y in points}
    if direction in ('left','right'):points={(y,x) for x,y in points}
    return points


def plan(identifier, attrs):
    color=attrs['fill'].lower();stem=family(identifier);mode=MODES[stem]
    if color not in KNOWN_COLORS.get(stem,()): raise ValueError('Unknown family color: '+identifier+' '+color)
    state,inactive,disabled=flags(identifier)
    if mode == 'focus':return {'role':role('focus',identifier),'mix':0,'endpoint':'#000000'}
    if mode == 'scrollarrow':
        pixels={(x,y) for y in range(int(attrs['y']),int(attrs['y'])+int(attrs['height'])) for x in range(int(attrs['x']),int(attrs['x'])+int(attrs['width']))}
        mask=scroll_mask(identifier)
        glyph_color='#858585' if disabled else '#4c4c4c'
        if color==glyph_color and pixels & mask:
            if not pixels <= mask: raise ValueError('Rect crosses glyph/bevel roles: '+identifier)
            return foreground('button',identifier,color)
        return gray_tone('button',identifier,color,153)
    if mode.startswith('glyph-'):
        kind=mode[len('glyph-'):]
        if stem=='ic-arrow' and 'separator' in identifier:
            return gray_tone('window',identifier,color,193)
        if stem=='ic-tabmark' and 'tear' in identifier:
            return gray_tone('window',identifier,color,193)
        return foreground(kind,identifier,color)
    if mode in ('check','radio','legacy-check'):
        if color in ('#cc0000','#660000') and mode=='check':
            return {'role':role('error',identifier),'mix':0 if color=='#cc0000' else .5,'endpoint':'#000000'}
        if color in ('#0000cc','#000066') and mode=='radio':
            return {'role':role('link',identifier),'mix':0 if color=='#0000cc' else .5,'endpoint':'#000000'}
        if color=='#000000' or (disabled and color=='#858585'):
            return foreground('button',identifier,color)
        return gray_tone('button',identifier,color,153)
    if mode in ('input','view'):
        if color==('#b6b6aa' if mode=='input' else '#efefef'):
            return {'role':role('view',identifier),'mix':0,'endpoint':'#000000'}
        if mode=='input' and state=='focused' and color=='#000000':
            return {'role':role('focus',identifier),'mix':0,'endpoint':'#000000'}
        return gray_tone('window',identifier,color,193)
    if mode=='inset':return gray_tone('window',identifier,color,193)
    if mode=='tree':
        if color=='#efefef':return {'role':role('view',identifier),'mix':0,'endpoint':'#000000'}
        return foreground('view',identifier,color)
    if mode in ('fill','range'):
        if color in ('#719e9e','#8eaaaa','#9ebfbf'):
            return {'role':role('selection',identifier),'mix':0,'endpoint':'#000000'}
        return gray_tone('button' if mode=='range' or stem=='ic-meter-fill' else 'window',identifier,color,153 if mode=='range' or stem=='ic-meter-fill' else 193)
    if mode=='selection':
        if color=='#d7e0dc':return {'role':role('selection',identifier),'mix':.6,'endpointRole':role('view',identifier)}
        return {'role':'theme_unfocused_selected_bg_color_breeze' if color=='#b3c3c3' else role('selection',identifier),'mix':0,'endpoint':'#000000'}
    if mode=='menurow':
        return gray_tone('selection',identifier,color,179 if state=='pressed' else 223)
    if mode=='menuindicator':
        if 'separator' in identifier or 'tearoff' in identifier:return gray_tone('window',identifier,color,193)
        return foreground('selection' if state in ('focused','pressed','toggled') else 'window',identifier,color)
    if mode=='title':
        return {'role':'theme_titlebar_background_backdrop_breeze' if inactive or state=='normal' else 'theme_titlebar_background_breeze','mix':0,'endpoint':'#000000'}
    anchors={'window':193,'button':153,'header':193,'tooltip':193}
    if mode not in anchors:raise ValueError('Unclassified SVG mode: '+mode)
    return gray_tone(mode,identifier,color,anchors[mode])


def evaluate(value, palette):
    def rgb(name):
        color=palette.get(name)
        if not isinstance(color,str) or not _HEX.fullmatch(color):raise ValueError('Native color role missing: '+name)
        return tuple(int(color[n:n+2],16) for n in (1,3,5))
    source=rgb(value['role'])
    endpoint=rgb(value['endpointRole']) if 'endpointRole' in value else tuple(int(value['endpoint'][n:n+2],16) for n in (1,3,5))
    ratio=value['mix']
    if not 0 <= ratio <= 1:raise ValueError('Invalid color mixture')
    return '#%02x%02x%02x' % tuple(round(a*(1-ratio)+b*ratio) for a,b in zip(source,endpoint))


def geometry(svg):
    root=ET.fromstring(svg)
    if root.tag != '{http://www.w3.org/2000/svg}svg':raise ValueError('SVG namespace absent')
    if b'<!' in svg:raise ValueError('SVG DTD/entity/comment unsupported')
    ids=set();structure=[]
    allowed={'svg': {'version','width','height','viewBox','shape-rendering'}, 'title':set(), 'desc':set(), 'g': {'id','transform'}, 'rect': {'x','y','width','height','fill','fill-opacity'}}
    for node in root.iter():
        if node.tag not in ('{http://www.w3.org/2000/svg}svg','{http://www.w3.org/2000/svg}title','{http://www.w3.org/2000/svg}desc','{http://www.w3.org/2000/svg}g','{http://www.w3.org/2000/svg}rect'):raise ValueError('Unclassified SVG primitive '+node.tag)
        name=node.tag.rsplit('}',1)[-1]
        if set(node.attrib)-allowed[name]:raise ValueError('Unsupported SVG attribute on '+name)
        if name=='rect':
            for metric in ('x','y','width','height'):
                if not re.fullmatch(r'[0-9]+',node.get(metric,'')) or not 0<=int(node.get(metric))<=4096:raise ValueError('Invalid rectangle metric')
            if int(node.get('width'))==0 or int(node.get('height'))==0:raise ValueError('Empty rectangle')
            if node.get('fill-opacity') not in (None,'0'):raise ValueError('Unknown rectangle opacity')
        if node.get('id'):
            if node.get('id') in ids:raise ValueError('Duplicate SVG id')
            ids.add(node.get('id'))
        structure.append((node.tag,{key:value for key,value in node.attrib.items() if key!='fill'},node.text if node.tag.endswith(('title','desc')) else None))
    return structure


def render(svg:bytes, kvconfig:bytes, palette:dict, *, native_qt_palette:dict):
    """Return SVG bytes, config bytes and receipt; never write or set a palette."""
    if not isinstance(svg,bytes) or len(svg)>8*1024*1024:raise ValueError('Invalid Classic SVG bytes')
    if not isinstance(kvconfig,bytes):raise ValueError('Invalid Classic configuration bytes')
    if hashlib.sha256(svg).hexdigest()!=SOURCE_SVG_SHA256 or hashlib.sha256(kvconfig).hexdigest()!=SOURCE_CONFIG_SHA256:
        raise ValueError('Unrecognized Classic source revision; semantic audit required')
    before=geometry(svg)
    identity=hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if EXPECTED_GEOMETRY_SHA256 and identity!=EXPECTED_GEOMETRY_SHA256:raise ValueError('Canonical Classic geometry was not reviewed')
    text=svg.decode('utf-8');groups=Counter();roles=Counter();count=0;bounds=0;glyphs=0
    def recolor_group(group):
        nonlocal count,bounds,glyphs
        opening,identifier,contents,closing=group.groups();family(identifier);groups[family(identifier)]+=1
        def recolor_rect(rect):
            nonlocal count,bounds,glyphs
            raw=rect.group(0);attrs=ET.fromstring(raw).attrib
            if attrs.get('fill-opacity')=='0':bounds+=1;return raw
            if 'fill' not in attrs or not _HEX.fullmatch(attrs['fill']):raise ValueError('Unclassified rectangle paint '+identifier)
            value=plan(identifier,attrs);color=evaluate(value,palette);roles[value['role']]+=1
            if 'endpointRole' in value:roles[value['endpointRole']]+=1
            if MODES[family(identifier)]=='scrollarrow' and value['role']==role('button-fg',identifier):glyphs+=1
            count+=1
            return _FILL.sub(lambda m:'fill="'+color+'"',raw,count=1)
        return opening+_RECT.sub(recolor_rect,contents)+closing
    output=_GROUP.sub(recolor_group,text).encode('utf-8')
    if len(groups)==0 or sum(groups.values()) != len(ET.fromstring(svg).findall('{*}g')):raise ValueError('Unsupported nested/unmatched SVG groups')
    all_rects=ET.fromstring(svg).findall('.//{*}rect')
    if count+bounds!=len(all_rects):raise ValueError('SVG paint outside classified groups')
    if geometry(output)!=before:raise ValueError('Geometry changed during recolor')
    config,config_report=adapt_config(kvconfig, native_qt_palette=native_qt_palette)
    return output,config,{'groups':sum(groups.values()),'opaqueRects':count,'transparentBoundsPreserved':bounds,'scrollGlyphRects':glyphs,'families':dict(groups),'roles':dict(roles),'config':config_report,'geometryUnchanged':True,'sourceSvgSha256':hashlib.sha256(svg).hexdigest(),'svgSha256':hashlib.sha256(output).hexdigest()}
