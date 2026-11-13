# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GtkToggleButton relief foundation, not a public renderer yet.

Selection is orthogonal to native pointer ACTIVE. Prospective press relief
uses the established GTK2 adaptation contract; historical fidelity is separate.
"""
from pathlib import Path
from gtk2_buttons import geometry
from gtk4_buttons import identity
import gtk4_css


def depressed(checked, pressed, disabled=False):
    if any(type(value) is not bool for value in (checked,pressed,disabled)):
        raise ValueError('GTK4 toggle selection/press must be boolean')
    return checked if disabled else checked != pressed


def state_selectors(variant, pressed_values=None, extra=''):
    for checked in (False,True):
        for pressed in (pressed_values if pressed_values is not None else
                        (False,) if variant=='disabled' else (False,True)):
            pseudo=':checked' if checked else ':not(:checked)'
            if variant=='disabled':pseudo+=':disabled'
            else:
                pseudo+=(':active' if pressed else ':not(:active)')+':not(:disabled)'
                if variant=='backdrop':pseudo+=':backdrop'
            yield pseudo+extra, depressed(checked,pressed,variant=='disabled')


def write_toggle_css(builder, recipe, palette, destination, push_receipt):
    shadow,padding,font=geometry(recipe)
    stamp=identity(recipe,palette)
    if push_receipt.get('style_class')!='theme-lab-gtk4-push-'+stamp:
        raise ValueError('GTK4 toggle/base snapshot identity mismatch')
    base=Path(push_receipt['css'])
    if not base.is_absolute() or not base.is_file() or base.is_symlink():
        raise ValueError('GTK4 toggle requires existing generated push.css')
    art=builder.art;prepared={}
    for variant,index in (('normal',0),('backdrop',1),('disabled',2)):
        effective=dict(palette)
        for role in ('button','button-fg'):
            for key in art.ROLES[role]:art._rgb(palette[key])
            effective[art.ROLES[role][0]]=palette[art.ROLES[role][index]]
        for down in (False,True):
            extent=max(1,shadow*2+2)
            pixels=art.bevel(art.blank(extent,extent,'face'),thickness=shadow,down=down)
            prepared[variant,down]={name:builder.png(part,'button',effective)
                                    for name,part in art.slices(pixels,shadow).items() if name}
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False,mode=0o700)
    paths={}
    for (variant,down),parts in prepared.items():
        paths[variant,down]={}
        for name,data in parts.items():
            path=destination/('toggle-'+variant+('-down-' if down else '-up-')+name+'-'+stamp+'.png')
            path.write_bytes(data);paths[variant,down][name]=path
    selector='button.theme-lab-gtk4-toggle-'+stamp
    css=['@import url("'+base.as_uri()+'");']+gtk4_css.base(selector,shadow,padding,font)
    for variant in ('normal','backdrop','disabled'):
        for pseudo,down in state_selectors(variant):
            urls=[paths[variant,down][name].as_uri() for name in gtk4_css.NAMES] if shadow else []
            css+=gtk4_css.state(selector,pseudo,shadow,urls,
                '@lab_push_'+variant+'_face','@lab_push_'+variant+'_text')
    path=destination/'toggle.css';path.write_text('\n'.join(css)+'\n',encoding='utf-8')
    return {'css':str(path),'style_class':'theme-lab-gtk4-toggle-'+stamp,
            'base_css':str(base),'selected_relief':'checked XOR pointer ACTIVE; disabled retains checked',
            'palette_source':'Aliases from existing verified push snapshot',
            'scope':'Private foundation; session/controller/public routing pending',
            'public_support_announced':False,'historical_fidelity_claimed':False}


def selected_fragment(builder, recipe, palette, state):
    if state not in ('normal','pressed','disabled','backdrop','hover'):
        raise ValueError('GTK4 toggle state not translated: '+state)
    shadow,padding,font=geometry(recipe);stamp=identity(recipe,palette)
    variant=state if state in ('disabled','backdrop') else 'normal'
    selector='button.theme-lab-gtk4-toggle-'+stamp
    face=builder.art.expression(builder.art.pixel_plan('button','face',
        inactive=state=='backdrop',disabled=state=='disabled'))
    text=builder.art.expression(builder.art.pixel_plan('button','ink',
        inactive=state=='backdrop',disabled=state=='disabled'))
    lines=['/* GTK4 GtkToggleButton / '+state+'. Selected inspection fragment.',
           ' * Selection remains native; relief uses checked XOR pointer ACTIVE.',
           ' * Requires existing toggle.css, its push.css dependency and verified PNG slices.',
           ' * Face alias follows '+face+'; text alias follows '+text+'.',
           ' * Keep this fragment beside toggle.css; do not replace the imported file. */',
           '@import url("toggle.css");']+gtk4_css.base(selector,shadow,padding,font)
    for pseudo,down in state_selectors(variant,(state=='pressed',),':hover' if state=='hover' else ''):
        urls=['toggle-'+variant+('-down-' if down else '-up-')+name+'-'+stamp+'.png'
              for name in gtk4_css.NAMES] if shadow else []
        lines+=gtk4_css.state(selector,pseudo,shadow,urls,
                             '@lab_push_'+variant+'_face','@lab_push_'+variant+'_text')
    return '\n'.join(lines)+'\n'
