# SPDX-License-Identifier: MIT
"""Additional original Indigo Magic inspired artwork and reviewed audit names."""
import json
import math
from pathlib import Path


def symbol(b, kind):
    """64-unit silhouettes shared by devices, actions, application and file art."""
    r,p,c,line=b.rect,b.poly,b.circle,b.path
    if kind.startswith('wifi-'):
        state=kind[5:].split('-')[0]; level=int(state) if state.isdigit() else 0
        s=c(32,49,3,b.TEAL)
        for index,(y,spread) in enumerate(((43,5),(36,11),(29,17),(22,23),(15,28)),1):
            if math.ceil(level/20)>=index or not state.isdigit():
                s+=line(f'M{32-spread} {y+7}Q32 {y-8} {32+spread} {y+7}',stroke=b.BLUE,w=3)
        if state=='off':s+=line('M12 12L53 54',stroke=b.RED,w=4)
        if state=='acquiring':s+=b.group(b.mark('help'),'translate(42 39) scale(.7)')
        if state=='hotspot':s+=b.group(b.mark('plus'),'translate(42 39) scale(.7)')
        if 'locked' in kind:s+=b.group(b.mark('lock'),'translate(43 43) scale(.8)')
        return s
    if kind.startswith('wired-'):
        s=b.status('network-online')
        if any(v in kind for v in ('off','disconnect','unavailable')):s+=b.group(b.mark('error'),'translate(40 40)')
        elif 'acquiring' in kind:s+=b.group(b.mark('help'),'translate(40 40)')
        elif 'activated' in kind:s+=b.group(b.mark('check'),'translate(40 40)')
        return s
    if kind.startswith('mobile-'):
        level=int(kind.split('-')[1]);s=b.group(symbol(b,'phone'),'translate(-7 0) scale(.85)')
        for i in range(math.ceil(level/20)):s+=r(38+i*4,43-i*5,3,10+i*5,b.BLUE,'none')
        if 'locked' in kind:s+=b.group(b.mark('lock'),'translate(44 45) scale(.7)')
        return s
    if kind.startswith('mic-'):
        state=kind[4:];level={'muted':0,'low':1,'medium':2,'high':3}[state]
        s=r(24,6,16,29,b.PAPER)+r(27,9,10,20,b.MID)+line('M18 23V31Q18 43 32 43Q46 43 46 31V23M32 43V55M22 55H42',w=3)
        for i in range(level):s+=r(48+i*4,30-i*6,2,10+i*6,b.BLUE,'none')
        if not level:s+=line('M11 11L52 52',stroke=b.RED,w=4)
        return s
    if kind in ('bell','bell-off'):
        s=line('M12 45L17 39V25Q17 12 32 12Q47 12 47 25V39L52 45Z',b.PAPER,w=2)+c(32,9,3,b.GOLD)+c(32,50,5,b.GOLD)
        if kind=='bell-off':s+=line('M10 8L55 55',stroke=b.RED,w=4)
        return s
    if kind.startswith('bluetooth'):
        s=line('M30 5L46 19L20 43M30 5V57L46 43L20 19',stroke=b.BLUE,w=4)
        if kind.endswith('off'):s+=line('M9 9L55 55',stroke=b.RED,w=4)
        if kind.split('-')[1:2]==['active']:s+=c(53,10 if 'locked' in kind else 49,5,b.TEAL)
        if 'locked' in kind:s+=b.group(b.mark('lock'),'translate(43 43) scale(.8)')
        return s
    if kind=='battery-missing':return b.status('battery-0')+b.group(b.mark('error'),'translate(24 21) scale(1.2)')
    if kind=='battery':return b.status('battery-60')
    if kind=='user':return c(32,18,10,b.PAPER)+line('M13 55V43Q13 30 32 30Q51 30 51 43V55Z',b.MID,w=2)
    if kind=='users':return b.group(symbol(b,'user'),'translate(-2 4) scale(.8)')+b.group(symbol(b,'user'),'translate(21 -1) scale(.7)')
    if kind=='keyboard':return p('5,24 44,8 59,30 20,49',b.MID)+''.join(p(f'{x},{y} {x+4},{y-2} {x+7},{y+3} {x+3},{y+5}',b.LIGHT,w=.7) for x,y in [(12+i*7,27-i*3+j*6) for i in range(5) for j in range(3)])
    if kind=='mouse':return b.ellipse(32,31,14,21,b.MID)+line('M32 10V30M18 27H46M32 10Q21 1 10 6',w=2)+r(30,16,4,8,b.LIGHT)
    if kind in ('cpu','memory'):
        s=r(15,15,34,34,b.MID)+r(22,22,20,20,b.PURPLE)
        for a in (20,28,36,44):s+=line(f'M{a} 9V15M{a} 49V55M9 {a}H15M49 {a}H55',w=3)
        if kind=='memory':s+=r(24,24,5,16,b.LIGHT)+r(35,24,5,16,b.LIGHT)
        return s
    if kind=='phone':return r(20,5,26,53,b.MID)+r(23,11,20,36,b.BLUE)+c(33,52,2,b.LIGHT)
    if kind=='chat':return line('M7 12H48V40H25L13 52V40H7Z',b.PAPER,w=2)+line('M14 22H40M14 29H34',stroke=b.PURPLE,w=3)
    if kind=='rss':return c(13,49,4,b.GOLD)+line('M9 29Q33 29 33 53M9 10Q52 10 52 53',stroke=b.GOLD,w=6)
    if kind=='download':return b.arrow('down')+line('M9 48V58H55V48',w=3)
    if kind=='upload':return b.arrow('up')+line('M9 48V58H55V48',w=3)
    if kind in ('shield','vpn'):
        s=p('10,12 32,5 54,12 50,39 32,59 14,39',b.BLUE)+p('14,15 32,9 32,53 18,37',b.LIGHT)
        if kind=='vpn':s+=b.group(b.mark('lock'),'translate(22 22) scale(1.1)')
        return s
    if kind=='key':return c(19,21,12,b.GOLD)+c(19,21,5,b.PAPER)+line('M27 29L52 54M39 41L45 35M47 49L53 43',stroke=b.GOLD,w=6)
    if kind=='font':return line('M12 52L30 10H36L53 52M19 37H46',stroke=b.PURPLE,w=5)
    if kind=='book':return b.book()
    if kind=='game':return r(8,17,48,29,b.MID)+line('M18 23V39M10 31H26',w=4)+c(45,27,4,b.PURPLE)+c(38,37,4,b.RED)
    if kind=='math':return line('M8 21H26M17 12V30M39 17L53 31M53 17L39 31M8 45H26M39 43H54M39 51H54',stroke=b.BLUE,w=3)
    if kind=='science':return line('M25 5H39M28 5V22L11 51Q9 58 18 58H47Q55 58 52 51L36 22V5',b.LIGHT,w=2)+p('21,35 43,35 52,52 49,55 15,55 13,51',b.TEAL)+c(30,44,3,b.GOLD)
    if kind=='map':return p('5,16 22,7 41,14 58,5 58,48 41,57 22,50 5,59',b.PAPER)+line('M22 7V50M41 14V57M10 37L28 25L37 38L51 21',stroke=b.TEAL,w=3)
    if kind=='pin':return line('M32 58L14 28C1 -4 63 -4 50 28Z',b.RED,w=2)+c(32,20,8,b.LIGHT)
    if kind=='cloud':return line('M13 48C-2 45 0 24 15 24C17 4 45 4 47 24C64 24 63 48 49 48Z',b.LIGHT,w=2)
    if kind=='sun':return c(32,32,13,b.GOLD)+''.join(line(f'M32 5V13',stroke=b.GOLD,w=3) if i==0 else b.group(line('M32 5V13',stroke=b.GOLD,w=3),f'rotate({i*45} 32 32)') for i in range(8))
    if kind=='weather':return symbol(b,'sun')+b.group(symbol(b,'cloud'),'translate(5 20) scale(.8)')
    if kind=='scanner':return p('8,30 41,14 57,25 24,42',b.LIGHT)+p('8,30 24,42 24,52 8,41',b.DARK)+p('24,42 57,25 57,39 24,52',b.MID)+p('13,25 43,9 49,13 20,28',b.BLUE)
    if kind=='bug':return b.ellipse(32,34,13,19,b.TEAL)+c(32,13,7,b.PURPLE)+line('M19 25L8 16M19 35H7M19 45L8 54M45 25L56 16M45 35H57M45 45L56 54M32 20V51',w=2)
    if kind=='window':return r(7,9,49,44,b.PAPER)+r(7,9,49,8,b.PURPLE)+r(11,22,16,26,b.LIGHT)+r(31,22,21,26,b.LIGHT)
    if kind.startswith('window-'):
        s=symbol(b,'window');v=kind[7:]
        glyph={'minimize':line('M22 40H42',w=4),'maximize':r(20,24,26,22,'none',sw=2),'restore':r(19,28,20,17,'none',sw=2)+r(25,23,20,17,'none',sw=2),'above':b.group(b.arrow('up'),'translate(15 18) scale(.55)'), 'below':b.group(b.arrow('down'),'translate(15 18) scale(.55)'),'shade':line('M15 25H49',w=3)}.get(v)
        return s+(glyph or b.group(b.mark('star'),'translate(26 26)'))
    if kind=='workspace':return ''.join(r(x,y,20,17,b.PURPLE if x==8 and y==9 else b.PAPER) for x in (8,36) for y in (9,35))
    if kind=='clipboard':return b.action('paste')
    if kind=='spreadsheet':
        return r(9,9,46,46,b.PAPER)+r(9,9,46,10,b.TEAL)+line('M9 30H55M9 42H55M24 19V55M39 19V55',w=1.5)+r(26,33,10,6,b.GOLD,'none')
    if kind=='presentation':
        return r(8,9,48,36,b.PAPER)+r(8,9,48,8,b.PURPLE)+line('M32 45V56M20 57H44',w=3)+r(15,31,7,8,b.BLUE)+r(27,25,7,14,b.TEAL)+r(39,21,7,18,b.GOLD)
    if kind=='eye':return line('M5 32Q32 3 59 32Q32 61 5 32Z',b.LIGHT)+c(32,32,11,b.BLUE)+c(32,32,4,b.INK)
    if kind=='filter':return p('6,8 58,8 38,32 38,51 26,58 26,32',b.PAPER)
    if kind=='tag':return p('6,13 32,13 58,39 39,58 6,25',b.GOLD)+c(16,22,3,b.PAPER)
    if kind=='airplane':return p('28,5 36,5 38,25 58,38 58,44 37,37 36,51 45,57 45,61 32,57 19,61 19,57 28,51 27,37 6,44 6,38 26,25',b.PAPER)
    if kind=='sleep':return b.monitor()+line('M32 13H47L32 28H47M46 4H57L46 15H57',stroke=b.PURPLE,w=3)
    if kind=='zoom':return b.group(b.mark('search'),'translate(5 5) scale(2.6)')
    if kind=='sort':return b.arrow('down')+line('M8 12H22M8 19H18M8 26H14',w=2)
    if kind=='chart':return r(9,35,11,20,b.BLUE)+r(26,24,11,31,b.TEAL)+r(43,10,11,45,b.PURPLE)
    if kind=='split':return b.action('split')
    if kind=='eject':return p('9,39 32,10 55,39',b.PAPER)+r(10,46,44,8,b.MID)
    if kind=='shuffle':return line('M7 15H18L43 49H57M7 49H18L43 15H57',stroke=b.BLUE,w=3)+p('49,8 59,15 49,22',b.PAPER)+p('49,42 59,49 49,56',b.PAPER)
    if kind=='face':return c(32,32,24,b.GOLD)+c(23,25,3,b.INK)+c(41,25,3,b.INK)+line('M19 38Q32 54 45 38',w=2)
    if kind=='qr':return ''.join(r(x,y,12,12,b.INK) for x,y in ((8,8),(44,8),(8,44)))+''.join(r(x,y,5,5,b.INK) for x,y in ((27,8),(27,21),(8,27),(40,27),(53,27),(27,40),(40,40),(53,53)))
    if kind=='network':return b.status('network-online')
    if kind=='settings':return b.wrench()
    raise ValueError('Unknown original symbol: '+kind)


def draw(b, item):
    s=symbol(b,item['variant'])
    if item['kind']=='app_ext':return b.carpet()+b.group(s,'translate(4 -1) scale(.85)')
    if item['kind']=='paper_ext':
        sheets=b.shadow()+''.join(b.group(b.rect(0,0,25,33,colour),f'matrix(1 -.5 0 1 {x} {y})')
                                  for x,y,colour in ((14,19,b.MID),(17,20,b.LIGHT),(20,21,b.PAPER)))
        return sheets+b.group(s,'matrix(.27 -.135 0 .27 23 27)')
    return s


def register(b):
    catalog=json.loads((Path(__file__).resolve().parents[1]/'sources/classic-audit-coverage.json').read_text())
    for item in catalog['artwork']:
        b.add(item['category'],item['name'],item['kind'],item['variant'])
    lookup={i['name']:i for i in b.ITEMS}
    for name,target in catalog['aliases'].items():
        if name in b.USED:
            raise ValueError('Audit alias duplicates existing artwork: '+name)
        b.USED.add(name)
        lookup[target]['aliases'].append(name)
