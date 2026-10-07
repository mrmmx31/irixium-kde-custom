# SPDX-License-Identifier: MIT
"""Application-specific SGI compositions; preserve unrelated theme artwork."""
import json
from pathlib import Path


def object_art(b, variant):
    r,p,c,line=b.rect,b.poly,b.circle,b.path
    if variant.startswith(('game-','edu-')):
        import classic_game_art
        return classic_game_art.draw(b,variant)
    if variant=='kate-project':
        return p('9,18 43,5 55,12 21,26',b.LIGHT)+p('9,18 21,26 21,52 9,44',b.MID)+p('21,26 55,12 55,41 21,54',b.PAPER)+line('M28 31L48 23M28 40L48 32M28 48L43 42',stroke=b.PURPLE,w=2)+c(26,32,1.4,b.GOLD)+c(26,41,1.4,b.GOLD)
    if variant=='kate-git':
        return p('10,26 37,7 58,26 31,49',b.RED)+p('10,26 31,49 31,56 10,33',b.DARK)+p('31,49 58,26 58,33 31,56',b.MID)+line('M27 19L43 32M33 24V42',stroke=b.LIGHT,w=3)+c(27,19,3,b.LIGHT)+c(43,32,3,b.LIGHT)+c(33,42,3,b.LIGHT)
    if variant=='chrome':
        return c(33,28,23,b.LIGHT)+p('13,16 23,7 43,6 54,17 34,18 25,30',b.RED)+p('54,17 57,34 46,48 28,50 37,33 34,18',b.GOLD)+p('28,50 13,42 10,25 13,16 25,30 37,33',b.TEAL)+c(33,28,10,b.BLUE)+c(30,25,3,b.LIGHT,'none')+line('M17 15Q29 3 43 11',stroke=b.LIGHT,w=1)
    if variant=='vscode':
        # Recognizable folded ribbon, drawn afresh with the SGI muted palette.
        return p('10,23 16,18 47,42 47,10 58,15 58,49 47,54 16,30',b.BLUE)+p('10,42 16,47 47,20 47,10 16,35',b.TEAL)+p('47,10 58,15 58,49 47,54 47,42 51,44 51,22 47,20',b.BLUE)+line('M48 13L55 17V47L48 50',stroke=b.LIGHT,w=1)
    if variant=='idea':
        return p('9,18 18,7 53,12 58,43 43,53 12,46',b.PURPLE)+p('9,18 29,13 39,46 12,46',b.RED)+r(17,17,32,29,b.INK)+line('M23 23V34M20 23H26M20 34H26M34 23H41V31Q41 38 33 36M21 41H33',stroke=b.LIGHT,w=2.1)
    if variant=='education':
        return b.group(b.book(),'translate(0 5) scale(.78)')+p('29,14 47,6 60,14 42,23',b.PURPLE)+p('34,19 44,23 55,18 55,27 45,32 34,27',b.MID)+line('M58 15V35',stroke=b.GOLD,w=2)+c(58,36,2,b.GOLD)
    if variant=='science':
        return p('26,6 39,3 43,7 31,10',b.LIGHT)+p('26,6 31,10 31,26 14,46 14,50 28,57 54,43 54,38 39,22 39,3',b.PAPER)+p('19,43 32,30 46,26 53,39 50,44 28,54 17,48',b.TEAL)+line('M31 11V26M31 27L18 45M32 35L45 29',stroke=b.LIGHT,w=1.2)+c(36,40,3,b.GOLD)+c(29,46,2,b.LIGHT)
    if variant=='system':
        return p('8,17 42,4 55,12 21,26',b.LIGHT)+p('8,17 21,26 21,52 8,44',b.DARK)+p('21,26 55,12 55,40 21,54',b.MID)+p('27,29 48,21 48,36 27,44',b.PURPLE)+line('M27 47L49 38',w=2)+b.group(b.wrench(),'translate(34 20) scale(.45)')
    if variant=='games':
        return p('11,20 33,8 54,20 32,33',b.LIGHT)+p('11,20 32,33 32,55 11,42',b.MID)+p('32,33 54,20 54,42 32,55',b.PAPER)+c(32,20,3,b.PURPLE)+c(21,32,3,b.INK)+c(21,43,3,b.INK)+c(43,32,3,b.RED)+c(43,43,3,b.RED)
    if variant=='arcade':
        return p('16,26 39,15 55,24 32,36',b.LIGHT)+p('16,26 32,36 32,52 16,42',b.DARK)+p('32,36 55,24 55,42 32,55',b.MID)+line('M33 29V12',w=4)+c(33,10,5,b.PURPLE)+c(46,29,3,b.RED)+c(39,34,2,b.GOLD)
    if variant in ('board','strategy'):
        board=p('6,39 36,23 58,35 28,51',b.LIGHT)+p('6,39 28,51 28,56 6,44',b.MID)+p('28,51 58,35 58,40 28,56',b.DARK)
        board+=''.join(p(f'{11+col*8+row*6},{39-col*4+row*3} {19+col*8+row*6},{35-col*4+row*3} {25+col*8+row*6},{38-col*4+row*3} {17+col*8+row*6},{42-col*4+row*3}',b.PURPLE,'none') for row in range(2) for col in range(3) if (row+col)%2==0)
        if variant=='strategy':return board+line('M37 36V8',w=2)+p('38,8 55,14 38,21',b.RED)+p('27,38 37,32 47,38 37,43',b.GOLD)
        return board+line('M33 39L29 31L33 26V19H29V12H34V16H40V12H45V19H41V26L45 33L41 37Z',b.PAPER,w=1.1)
    if variant=='cards':
        return b.group(r(0,0,24,33,b.MID),'matrix(1 -.4 0 1 12 20)')+b.group(r(0,0,24,33,b.LIGHT)+p('12,8 19,17 12,26 5,17',b.RED),'matrix(1 -.4 0 1 25 22)')
    if variant=='children':return b.group(b.box(),'translate(4 -5) scale(.7)')+c(41,28,11,b.GOLD)+c(33,19,4,b.GOLD)+c(49,19,4,b.GOLD)+c(38,27,1.5,b.INK)+c(45,27,1.5,b.INK)+c(41,32,2,b.INK)
    if variant=='logic':
        return p('12,23 30,13 37,17 37,10 49,6 56,12 50,19 58,24 41,34 34,30 28,38 19,34 24,27',b.PURPLE)+p('12,23 24,27 19,34 28,38 34,30 41,34 58,24 58,31 41,42 34,38 28,46 19,42 12,33',b.MID)
    if variant=='languages':return b.group(b.book(),'translate(-2 6) scale(.72)')+b.group(r(0,0,27,33,b.LIGHT)+line('M5 22L11 7L17 22M8 17H14M20 8V19M18 22H23',stroke=b.PURPLE,w=2),'matrix(1 -.3 0 1 31 15)')
    if variant=='mathematics':return p('10,48 33,9 53,34',b.GOLD)+p('22,40 34,20 45,33',b.PAPER)+line('M14 45L18 44M20 37L24 35M25 29L29 27',w=1)+b.group(b.calculator(),'translate(29 21) scale(.43)')
    if variant=='misc-education':return b.group(b.book(),'translate(0 4) scale(.8)')+line('M41 16V45M32 23H54M32 38H54',stroke=b.GOLD,w=3)+c(45,23,4,b.PURPLE)+c(37,38,4,b.TEAL)
    if variant=='texdoctk':return b.group(b.book(),'translate(-2 4) scale(.85)')+line('M28 24H48M38 24V41M43 42H54M43 42V53M43 47H51',stroke=b.PURPLE,w=2)
    if variant=='snx':return b.group(b.classic_extensions.symbol(b,'vpn'),'translate(-2 -3) scale(.85)')+line('M40 35L50 29L55 34M40 44L50 38L55 43',stroke=b.GOLD,w=3)
    import classic_application_art
    try:return classic_application_art.draw(b,variant)
    except ValueError as error:
        if not str(error).startswith('Unknown application object:'):raise
        import classic_utility_art
        try:return classic_utility_art.draw(b,variant)
        except ValueError as error:
            if not str(error).startswith('Unknown utility object:'):raise
            import classic_development_art
            return classic_development_art.draw(b,variant)


def draw(b,item):
    return b.carpet()+b.group(object_art(b,item['variant']),'translate(3 -1) scale(.86)')


def register(b):
    catalog=json.loads((Path(__file__).resolve().parents[1]/'sources/classic-identities.json').read_text())
    for entry in catalog['icons']:
        names=[entry['name'],*entry.get('aliases',[])]
        for item in b.ITEMS:
            item['aliases']=[n for n in item['aliases'] if n not in names]
        # Existing canonical names keep their aliases and original context.
        existing=next((i for i in b.ITEMS if i['name']==entry['name']),None)
        for n in names:
            other=next((i for i in b.ITEMS if i['name']==n and i is not existing),None)
            if other:
                names += [a for a in other['aliases'] if a not in names]
                b.ITEMS.remove(other)
        if existing:
            existing.update(kind='identity',variant=entry['variant'])
            existing['aliases'] += [n for n in names[1:] if n not in existing['aliases']]
        else:
            b.ITEMS.append(dict(category=entry.get('category','apps'),name=entry['name'],kind='identity',variant=entry['variant'],aliases=names[1:]))
    lookup={n:i for i in b.ITEMS for n in [i['name'],*i['aliases']]}
    for name,target in catalog.get('menu_aliases',{}).items():
        if name in lookup:raise ValueError('Duplicate category alias: '+name)
        b.ITEMS.append(dict(category='categories',name=name,kind='menu_alias',variant=lookup[target]['name'],aliases=[]))
    b.USED.clear();b.USED.update(n for item in b.ITEMS for n in [item['name'],*item['aliases']])
