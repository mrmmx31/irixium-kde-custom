# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 push-button CSS from the shared raster relief/KDE roles.

Foundation only: no installation, widget creation or public adapter declaration.
"""
import hashlib
import json
from pathlib import Path
from gtk2_buttons import geometry
import gtk4_css


def identity(recipe, palette):
    return hashlib.sha256(json.dumps({'geometry':recipe['geometry'],'palette':palette,'rules':recipe['palette']},sort_keys=True).encode()).hexdigest()[:16]


def write_button_css(builder, recipe, palette, destination):
    shadow,padding,font=geometry(recipe)
    art=builder.art
    for role in ('button','button-fg'):
        for key in art.ROLES[role]:
            if key not in palette:
                raise ValueError('GTK4 push missing effective KDE role: '+key)
            art._rgb(palette[key])
    prepared={}
    size=max(1,shadow*2+2)
    for state,index in (('normal',0),('pressed',0),('disabled',2),('backdrop',1)):
        effective=dict(palette)
        for role in ('button','button-fg'):
            effective[art.ROLES[role][0]]=palette[art.ROLES[role][index]]
        pixels=art.bevel(art.blank(size,size,'face'),thickness=shadow,down=state=='pressed')
        face=art.evaluate(art.pixel_plan('button','face'),effective)
        text=effective[art.ROLES['button-fg'][0]]
        prepared[state]=(builder.png(pixels,'button',effective),face,text,
                         {name:builder.png(part,'button',effective) for name,part in art.slices(pixels,shadow).items() if name})
    stamp=identity(recipe,palette)
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False,mode=0o700)
    css=[];assets={};pieces={}
    for state,(png,face,text,parts) in prepared.items():
        path=destination/('push-'+state+'-'+stamp+'.png');path.write_bytes(png);assets[state]=str(path)
        pieces[state]={}
        for name,data in parts.items():
            piece=destination/('push-'+state+'-'+name+'-'+stamp+'.png');piece.write_bytes(data);pieces[state][name]=piece
        css += [f'@define-color lab_push_{state}_face {face};',f'@define-color lab_push_{state}_text {text};']
    selector='button.theme-lab-gtk4-push-'+stamp
    css += gtk4_css.base(selector,shadow,padding,font)
    for state,pseudo in (('normal',''),('pressed',':active'),('backdrop',':backdrop'),('disabled',':disabled')):
        urls=[pieces[state][name].as_uri() for name in gtk4_css.NAMES] if shadow else []
        css += gtk4_css.state(selector,pseudo,shadow,urls,'@lab_push_'+state+'_face','@lab_push_'+state+'_text')
    path=destination/'push.css';path.write_text('\n'.join(css)+'\n',encoding='utf-8')
    return {'css':str(path),'assets':assets,'style_class':'theme-lab-gtk4-push-'+stamp,
            'geometry':{'shadow_px':shadow,'padding_px':padding,'font_px':font},
            'states':['normal','pressed','disabled','backdrop'],
            'final_colors_from_kde_roles':True,'scope':'GTK4 push foundation only'}


def selected_fragment(builder, recipe, palette, state):
    if state not in ('normal','pressed','disabled','backdrop','hover'):
        raise ValueError('GTK4 push state not translated: '+state)
    shadow,padding,font=geometry(recipe)
    asset_state='normal' if state=='hover' else state
    stamp=identity(recipe,palette)
    selector='button.theme-lab-gtk4-push-'+stamp
    pseudo={'normal':'','pressed':':active','disabled':':disabled','backdrop':':backdrop','hover':':hover'}[state]
    art=builder.art
    face_source=art.expression(art.pixel_plan('button','face',inactive=state=='backdrop',disabled=state=='disabled'))
    text_source=art.expression(art.pixel_plan('button','ink',inactive=state=='backdrop',disabled=state=='disabled'))
    urls=['push-'+asset_state+'-'+name+'-'+stamp+'.png' for name in gtk4_css.NAMES] if shadow else []
    lines=['/* GTK4 GtkButton / '+state+'. Selected inspection fragment.',
           ' * Requires the existing push.css and PNG slices from the verified snapshot.',
           ' * Face alias follows '+face_source+'; text alias follows '+text_source+'.',
           ' * Same geometry/layers as the renderer; not a complete theme or installation. */']
    lines+=['@import url("push.css");']
    lines+=gtk4_css.base(selector,shadow,padding,font)
    lines+=gtk4_css.state(selector,pseudo,shadow,urls,
                         '@lab_push_'+asset_state+'_face','@lab_push_'+asset_state+'_text')
    return '\n'.join(lines)+'\n'
