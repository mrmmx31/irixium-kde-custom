# SPDX-License-Identifier: MIT
"""Game pieces and learning instruments, drawn as individual SGI objects."""
from classic_application_art import page, book


def draw(b,v):
    r,p,c,line=b.rect,b.poly,b.circle,b.path
    if v.startswith('edu-'):return education(b,v[4:])
    name=v[5:]
    def grid(colour=b.GOLD,rows=4,cols=4):
        return b.group(r(0,0,40,36,colour)+''.join(line(f'M{x} 0V36',stroke=b.DARK,w=.8) for x in range(0,41,40//cols))+''.join(line(f'M0 {y}H40',stroke=b.DARK,w=.8) for y in range(0,37,36//rows)),'matrix(1 -.25 0 .8 12 19)')
    def dice(x=19,y=10,colour=b.LIGHT):return b.group(p('1,12 17,3 32,11 17,21',colour)+p('1,12 17,21 17,38 1,29',b.MID)+p('17,21 32,11 32,29 17,38',colour)+c(17,12,2,b.PURPLE)+c(9,22,2,b.INK)+c(24,22,2,b.RED),'translate(%s %s)'%(x,y))
    if name in ('gnugo48','kigo'):
        return grid(rows=5,cols=5)+c(25,30,7,b.INK)+c(42,25 if name=='kigo' else 35,7,b.LIGHT)+ (c(36,40,5,b.INK) if name=='kigo' else line('M16 14L22 8L28 14',stroke=b.RED,w=2))
    if name=='bovo':return grid(b.PAPER)+line('M17 26L25 31M25 24L17 33M31 20L39 25M39 18L31 27',stroke=b.RED,w=2.5)+c(39,35,5,b.BLUE)
    if name=='kfourinline':return p('12,13 47,1 55,7 20,22',b.LIGHT)+p('20,22 55,7 55,44 20,57',b.BLUE)+''.join(c(x,y-(x-26)*.38,3,b.RED if i<3 else b.GOLD) for i,(x,y) in enumerate(((26,28),(36,28),(46,28),(26,38),(36,38),(46,38),(26,48),(36,48),(46,48))))
    if name=='knights':return grid(b.PAPER,rows=3,cols=3)+line('M24 42L29 32L24 24L27 12L35 6L47 17L40 23L35 20L35 34L43 40Z',b.LIGHT,w=1.5)+c(35,13,1.5,b.INK)
    if name=='kreversi':return grid(b.TEAL)+c(25,30,9,b.INK)+c(43,35,8,b.LIGHT)+c(28,29,2,b.PAPER)
    if name=='ksquares':return grid(b.PAPER)+''.join(c(x,y-(x-14)*.25,1.5,b.INK) for x in (16,28,40,52) for y in (23,35,47))+line('M16 35L40 29L40 41L28 44',stroke=b.PURPLE,w=3)
    if name in ('kajongg','kmahjongg','kshisen'):
        s=b.group(r(0,0,22,31,b.MID),'matrix(1 -.3 0 1 11 21)')+b.group(r(0,0,22,31,b.LIGHT),'matrix(1 -.3 0 1 26 18)')
        if name=='kmahjongg':return s+line('M32 26L43 22M34 30L41 28M37 26V42M30 36L44 31',stroke=b.RED,w=2)
        if name=='kshisen':return s+''.join(line(f'M{x} {y}V{y+12}',stroke=b.TEAL,w=2) for x,y in ((31,25),(36,24),(42,22)))+line('M31 31L42 27',stroke=b.TEAL,w=2)
        return s+c(36,31,5,b.PURPLE)+c(36,43,4,b.TEAL)+r(11,7,21,10,b.GOLD)+line('M15 11H28',w=1.3)
    if name in ('kiriki','kjumpingcube'):return dice()+dice(4,25,b.GOLD) if name=='kiriki' else grid(b.PURPLE,rows=3,cols=3)+dice(18,0)
    if name in ('kpat','lskat'):
        s=b.group(r(0,0,24,33,b.LIGHT)+p('12,5 18,15 12,24 6,15',b.RED),'matrix(1 -.3 0 1 11 20)')
        return s+b.group(r(0,0,24,33,b.PAPER)+(c(12,14,5,b.INK)+p('12,5 19,17 5,17',b.INK) if name=='lskat' else line('M6 10C2 0 20 0 18 10L12 22Z',b.RED)),'matrix(1 -.3 0 1 30 17)')
    if name in ('kmines','kblackbox','killbots'):
        if name=='kmines':return grid(b.MID)+c(31,27,12,b.INK)+''.join(b.group(line('M31 9V16',w=3),f'rotate({i*45} 31 27)') for i in range(8))+c(27,22,3,b.LIGHT)
        if name=='kblackbox':return b.box()+line('M8 17L34 40L57 17',stroke=b.RED,w=2)+c(8,17,3,b.RED)
        return r(21,13,26,21,b.MID)+r(24,37,20,15,b.PURPLE)+c(27,22,3,b.RED)+c(40,22,3,b.GOLD)+line('M21 41L11 32M44 41L54 29M27 52V59M41 52V59M33 13V5',w=3)
    if name=='bomber':return p('9,22 26,19 36,9 42,11 37,21 56,24 57,30 39,31 31,41 24,40 29,31 10,28',b.BLUE)+c(41,47,6,b.INK)+line('M39 39L41 42',stroke=b.GOLD,w=2)
    if name=='granatier':return b.ellipse(33,34,14,20,b.TEAL)+r(28,9,12,8,b.MID)+line('M31 9L44 4L50 12L45 20M24 23H44M20 35H47M23 46H44M29 18V52M39 18V52',w=1.5)
    if name=='kgoldrunner':return r(13,8,8,45,b.MID)+r(42,8,8,45,b.MID)+''.join(line(f'M20 {y}H42',stroke=b.GOLD,w=2) for y in (14,23,32,41,50))+p('11,44 28,34 41,42 24,53',b.GOLD)
    if name=='kapman':return line('M53 12L31 30L54 46A24 24 0 1 1 53 12Z',b.GOLD,w=1.5)+c(34,14,2,b.INK)+c(56,29,3,b.PAPER)
    if name in ('kblocks','fifteenpuzzle','klickety','ksame'):
        if name=='kblocks':return ''.join(b.group(b.box(),f'translate({x} {y}) scale(.33)') for x,y in ((10,18),(23,12),(36,6),(23,27),(36,21)))
        if name=='fifteenpuzzle':return grid(b.PAPER,rows=3,cols=3)+''.join(p(f'{x},{y} {x+9},{y-2} {x+9},{y+6} {x},{y+8}',b.PURPLE if i%2 else b.GOLD) for i,(x,y) in enumerate(((13,20),(26,17),(39,14),(13,30),(26,27),(39,24),(13,40),(26,37))))
        if name=='klickety':return grid(b.BLUE)+''.join(r(x,y,8,8,colour) for x,y,colour in ((15,20,b.RED),(23,20,b.RED),(31,20,b.GOLD),(15,29,b.RED),(23,29,b.PURPLE),(31,29,b.PURPLE)))
        return ''.join(c(x,y,7,colour) for x,y,colour in ((19,18,b.RED),(34,18,b.RED),(49,18,b.PURPLE),(19,35,b.GOLD),(34,35,b.PURPLE),(49,35,b.PURPLE)))+line('M15 51L38 43',stroke=b.GOLD,w=3)
    if name in ('kbounce','kbreakout','kollision','klines'):
        if name=='kbounce':return grid(b.BLUE)+c(24,27,7,b.RED)+c(44,37,7,b.GOLD)+line('M34 15V45',stroke=b.LIGHT,w=3)
        if name=='kbreakout':return ''.join(r(x,y,12,6,b.RED if y==9 else b.GOLD) for x in (9,24,39) for y in (9,19))+r(24,47,26,6,b.BLUE)+c(29,35,5,b.LIGHT)
        if name=='kollision':return c(23,24,14,b.RED)+c(43,36,11,b.BLUE)+line('M39 13L33 23M53 20L44 26M51 48L43 45',stroke=b.GOLD,w=2)
        return grid(b.PAPER)+''.join(c(x,y,5,colour) for x,y,colour in ((17,25,b.RED),(26,22,b.RED),(35,19,b.RED),(44,16,b.RED),(44,33,b.BLUE),(26,39,b.GOLD)))
    if name=='kdiamond':return p('32,5 51,19 32,44 13,19',b.PURPLE)+line('M13 19H51M24 10L25 19L32 44L39 19L40 10',stroke=b.LIGHT,w=1)+p('8,37 18,30 25,37 16,48',b.TEAL)
    if name=='katomic':return ''.join(line(f'M32 28L{x} {y}',stroke=b.DARK,w=3)+c(x,y,8,colour) for x,y,colour in ((14,14,b.BLUE),(48,15,b.RED),(47,43,b.GOLD),(14,43,b.TEAL)))+c(32,28,11,b.PURPLE)
    if name=='knetwalk':return grid(b.PAPER,rows=3,cols=3)+line('M18 23V40H42V19H52',stroke=b.TEAL,w=4)+c(18,23,4,b.GOLD)+c(52,19,4,b.BLUE)
    if name=='knavalbattle':return p('6,36 56,27 44,46 19,50',b.MID)+r(23,17,22,14,b.PAPER)+r(31,9,8,10,b.DARK)+line('M8 53Q18 46 28 53Q38 46 51 51',stroke=b.BLUE,w=3)
    if name=='konquest':return c(23,23,16,b.BLUE)+b.ellipse(23,23,23,7,'none',b.GOLD,2)+c(49,42,7,b.RED)+line('M40 22L51 10',stroke=b.LIGHT,w=2)
    if name=='ksirk':return p('10,18 31,6 53,20 45,45 22,53 5,36',b.TEAL)+line('M29 46V10',w=2)+p('30,10 53,15 31,25',b.RED)+c(17,33,5,b.GOLD)
    if name in ('ksnakeduel','kspaceduel'):
        if name=='ksnakeduel':return line('M11 12H45V24H22V39H50V49H36',stroke=b.TEAL,w=9)+line('M12 49H22V31H8',stroke=b.RED,w=7)+c(38,49,2,b.LIGHT)
        return p('8,31 29,20 19,43',b.BLUE)+p('37,14 59,31 34,35',b.RED)+line('M28 31L38 27',stroke=b.GOLD,w=3)
    if name=='kolf':return b.ellipse(30,43,24,10,b.TEAL)+b.ellipse(28,42,6,3,b.INK)+line('M36 42V6',w=2)+p('37,6 53,12 37,22',b.RED)+c(13,35,4,b.LIGHT)
    if name=='ktuberling':return b.ellipse(32,30,20,25,b.GOLD)+c(25,24,5,b.LIGHT)+c(40,24,5,b.LIGHT)+c(25,25,2,b.INK)+c(40,25,2,b.INK)+line('M25 41Q33 48 42 39',w=2)+c(32,32,4,b.RED)
    if name=='kturtle':return b.ellipse(32,30,18,15,b.TEAL)+c(51,30,7,b.GOLD)+line('M19 17L13 9M19 42L13 49M40 17L45 9M40 43L45 50M24 21L39 21L44 32L34 41L20 32Z',stroke=b.DARK,w=2)
    if name=='kubrick':return ''.join(b.group(b.box(),f'translate({x} {y}) scale(.32)') for x,y in ((7,15),(19,9),(31,3),(7,29),(19,23),(31,17),(7,43),(19,37),(31,31)))
    if name=='palapeli':return b.group(b.classic_identity.object_art(b,'logic'),'translate(-8 3) scale(.75)')+b.group(b.classic_identity.object_art(b,'logic'),'translate(24 19) scale(.55)')
    if name=='ksudoku':return grid(b.LIGHT,rows=3,cols=3)+line('M18 22V29M29 18H34L29 26H34M40 14H46L41 24M19 38H24V45H19V38M31 32V40',stroke=b.PURPLE,w=1.5)
    if name=='picmi':return grid(b.LIGHT,rows=5,cols=5)+''.join(r(x,y,6,6,b.PURPLE,'none') for x,y in ((23,17),(31,17),(15,25),(23,25),(31,25),(39,25),(23,33),(31,33)))
    if name=='skladnik':return grid(b.MID,rows=3,cols=3)+b.group(b.box(),'translate(1 -6) scale(.55)')+b.group(b.box(),'translate(26 17) scale(.38)')
    if name=='blinken':return c(31,27,24,b.DARK)+p('31,27 10,18 15,8 31,4',b.BLUE)+p('31,27 31,4 48,10 54,25',b.RED)+p('31,27 54,25 46,44 31,50',b.GOLD)+p('31,27 31,50 13,42 10,18',b.TEAL)+c(31,27,7,b.DARK)
    if name=='khangman':return line('M13 51H45M19 51V6H43V14',stroke=b.GOLD,w=3)+c(43,21,6,b.PAPER)+line('M43 27V42M35 32H51M43 42L36 51M43 42L50 51',w=2)
    raise ValueError('Unknown game object: '+name)


def education(b,name):
    r,p,c,line=b.rect,b.poly,b.circle,b.path
    if name=='kalgebra':return page(b,b.LIGHT,line('M2 23L13 2L24 23M7 15H19M3 30H23',stroke=b.PURPLE,w=2.3))
    if name=='kbruch':return page(b,b.LIGHT,line('M4 4H23M14 4V12M4 18H24M5 26H22M5 26V32H23',stroke=b.BLUE,w=2))+c(49,35,9,b.GOLD)
    if name=='kmplot':return p('10,18 45,4 55,12 20,27',b.LIGHT)+p('20,27 55,12 55,46 20,58',b.PAPER)+line('M25 31V50L49 40M25 46Q35 10 49 33',stroke=b.PURPLE,w=2)
    if name=='kig':return p('13,45 28,8 52,36',b.LIGHT)+c(28,8,4,b.RED)+c(13,45,4,b.BLUE)+c(52,36,4,b.TEAL)+line('M28 8L32 41',stroke=b.PURPLE,w=1.8)
    if name=='cantor':return book(b,b.BLUE,line('M3 1H23L5 13L23 26H3',stroke=b.LIGHT,w=3))+line('M34 49L54 18',stroke=b.GOLD,w=3)
    if name=='kalzium':return ''.join(p(f'{x},{y} {x+10},{y-4} {x+10},{y+9} {x},{y+13}',colour) for x,y,colour in ((9,16,b.BLUE),(22,11,b.PURPLE),(35,6,b.GOLD),(9,32,b.TEAL),(22,27,b.RED),(35,22,b.PAPER)))+line('M13 22L17 20M26 17L30 15M39 12L43 10',stroke=b.LIGHT,w=1.3)
    if name=='step':return line('M15 9H52M23 9L41 39M46 9L22 40',stroke=b.DARK,w=2)+c(41,39,8,b.PURPLE)+c(22,40,8,b.GOLD)+line('M12 53H50',stroke=b.BLUE,w=2)
    if name=='kanagram':return book(b,b.PURPLE,line('M2 21L10 2L18 21M5 14H15',stroke=b.LIGHT,w=2))+p('37,35 55,27 55,46 37,54',b.GOLD)+line('M42 36V47M42 36H49V41H42M42 41H50V46H42',w=1.5)
    if name=='klettres':return book(b,b.TEAL,line('M1 19L9 2L17 19M4 13H14',stroke=b.LIGHT,w=2))+c(47,38,10,b.GOLD)+line('M47 31V45M41 34H53',stroke=b.PURPLE,w=2)
    if name=='kiten':return page(b,b.LIGHT,line('M2 5H28M15 2V25M3 12H26M6 17L24 27M24 16L5 27',stroke=b.RED,w=2))+p('35,39 56,31 56,50 35,58',b.PAPER)
    if name=='parley':return b.group(b.book(),'translate(-5 7) scale(.75)')+line('M29 12H56V32H42L35 42V32H29Z',b.PAPER,stroke=b.BLUE,w=1.5)+line('M35 18H51M35 24H47',stroke=b.PURPLE,w=2)
    if name=='wordquiz':return page(b,b.LIGHT,line('M2 20L10 2L18 20M5 13H15',stroke=b.PURPLE,w=2))+p('36,29 56,22 56,48 36,55',b.GOLD)+line('M43 31Q53 27 50 36L45 42M45 47V48',w=2)
    if name=='artikulate':return b.group(b.classic_extensions.symbol(b,'chat'),'translate(-4 1) scale(.72)')+b.group(b.speaker(),'translate(28 20) scale(.5)')
    if name=='ktouch':return b.group(b.classic_extensions.symbol(b,'keyboard'),'translate(-2 5) scale(.82)')+p('25,26 24,9 29,7 33,21 35,12 40,11 42,23 47,18 51,20 48,35 38,45',b.PAPER)
    raise ValueError('Unknown learning object: '+name)
