# SPDX-License-Identifier: MIT
"""Distinct physical objects and application motifs in the SGI palette."""


def page(b, colour=None, body=''):
    colour=colour or b.PAPER
    return (b.poly('12,13 41,3 50,9 50,43 22,54',colour)+
            b.poly('12,13 22,18 22,54 12,47',b.MID)+
            b.poly('41,3 41,13 50,9',b.LIGHT)+b.group(body,'matrix(.75 -.25 0 .75 25 23)'))


def picture(b, style):
    border=b.LIGHT if style=='polaroid' else b.MID
    scene=b.rect(4,4,31,23,b.BLUE)+b.poly('5,26 15,14 21,20 27,10 35,23 35,27',b.TEAL)+b.circle(12,10,3,b.GOLD)
    body=b.rect(0,0,39,36,border)+scene
    if style=='film':body+=''.join(b.rect(x,29,4,3,b.DARK,'none') for x in (5,12,19,26))
    return b.group(body,'matrix(1 -.25 0 1 12 16)')+b.poly('12,16 12,52 17,55 17,19',b.DARK)


def book(b, colour, motif=''):
    return b.poly('15,11 37,3 48,9 26,18',b.LIGHT)+b.poly('15,11 26,18 26,54 15,47',b.DARK)+b.poly('26,18 48,9 48,43 26,54',colour)+b.group(motif,'matrix(.7 -.3 0 .7 29 26)')


def draw(b,v):
    r,p,c,line=b.rect,b.poly,b.circle,b.path
    # Graphics: retain the visual cue of the original application, with real objects.
    if v=='eom':return picture(b,'polaroid')+b.group(b.classic_extensions.symbol(b,'eye'),'translate(25 28) scale(.44)')
    if v=='gpicview':return picture(b,'film')+line('M16 20L21 18',stroke=b.LIGHT,w=1)
    if v=='lximage':return picture(b,'polaroid')+p('36,39 53,32 57,42 40,49',b.PAPER)+c(47,40,3,b.GOLD)
    if v=='imagemagick':return p('17,43 46,32 56,42 27,52',b.PURPLE)+p('24,38 34,6 49,37',b.BLUE)+c(36,22,3,b.GOLD)+line('M13 36L51 9',stroke=b.GOLD,w=3)+line('M49 6V13M45 10H54',stroke=b.LIGHT,w=2)
    if v=='kontrast':return c(34,26,20,b.TEAL)+p('34,6 34,46 19,39 14,26 19,13',b.INK)+line('M23 40L33 12H36L47 40M28 30H41',stroke=b.LIGHT,w=3)
    if v=='lo-draw':return page(b,b.GOLD,r(1,4,11,13,b.LIGHT)+c(23,11,6,b.PAPER)+p('8,25 19,11 29,25',b.LIGHT))
    if v=='icon-editor':return p('9,19 44,6 55,14 20,28',b.LIGHT)+p('9,19 20,28 20,50 9,42',b.DARK)+p('20,28 55,14 55,39 20,54',b.PAPER)+''.join(p(f'{26+i*6},{30-i*2+j*5} {31+i*6},{28-i*2+j*5} {31+i*6},{32-i*2+j*5} {26+i*6},{34-i*2+j*5}',b.PURPLE if (i+j)%2 else b.BLUE) for i in range(4) for j in range(3))+line('M16 45L48 19',stroke=b.GOLD,w=3)
    if v=='gimp':return b.ellipse(33,29,22,15,b.MID)+p('15,22 13,11 26,20',b.MID)+c(24,23,6,b.LIGHT)+c(39,20,7,b.LIGHT)+c(25,24,2,b.INK)+c(40,21,2,b.INK)+c(48,30,6,b.DARK)+line('M25 42L53 15',stroke=b.GOLD,w=4)
    if v=='krita':return c(29,25,19,b.PURPLE)+p('29,6 46,16 29,25',b.BLUE)+p('29,25 46,16 46,35',b.RED)+line('M17 48L48 8',stroke=b.GOLD,w=5)+p('16,48 11,54 23,50',b.MID)
    # Readers and office suites.
    pdf=line('M3 24Q17 4 14 1Q4 -6 11 12Q23 30 28 19Q32 9 3 24',stroke=b.LIGHT,w=2)
    if v=='adobe':return page(b,b.RED,pdf)
    if v=='atril':return page(b,b.LIGHT,line('M3 24Q17 4 14 1Q4 -6 11 12Q23 30 28 19Q32 9 3 24',stroke=b.RED,w=2)+line('M3 31H26',stroke=b.BLUE,w=2))
    if v=='calibre':return b.group(book(b,b.GOLD),'translate(-10 3) scale(.85)')+b.group(book(b,b.TEAL),'translate(6 -2) scale(.86)')+b.group(book(b,b.BLUE),'translate(23 9) scale(.72)')
    if v=='ebook-viewer':return book(b,b.GOLD)+b.group(b.mark('search'),'translate(32 30) scale(1.25)')
    if v=='ebook-editor':return b.group(b.book(),'translate(-4 6) scale(.85)')+line('M30 42L52 12',stroke=b.GOLD,w=4)+p('30,42 26,49 33,45',b.INK)
    if v=='lrf-reader':return p('15,13 40,4 50,11 25,21',b.LIGHT)+p('15,13 25,21 25,53 15,46',b.DARK)+p('25,21 50,11 50,44 25,55',b.MID)+p('29,25 46,19 46,39 29,46',b.PAPER)+line('M32 29L42 25M32 35L42 31M32 41L40 38',w=1.5)
    if v=='qpdfview':return page(b,b.LIGHT,line('M2 4H26M2 10H26M2 16H14',stroke=b.MID,w=2))+b.group(b.mark('search'),'translate(32 31) scale(1.25)')
    if v=='xpdf':return page(b,b.DARK,line('M2 1L28 27M28 1L2 27',stroke=b.RED,w=4)+line('M2 33H25',stroke=b.LIGHT,w=2))
    if v=='lokalize':return page(b,b.LIGHT,line('M2 24L10 4L18 24M6 16H14',stroke=b.PURPLE,w=2))+b.group(page(b,b.PAPER,line('M3 6H27M15 6V26M5 13Q10 25 24 27M22 12Q18 24 4 28',stroke=b.TEAL,w=2)),'translate(23 10) scale(.6)')
    if v=='abiword':return page(b,b.LIGHT,line('M0 3H26M0 10H26M0 17H20',stroke=b.BLUE,w=2))+p('36,39 48,10 54,13 42,42',b.GOLD)+p('36,39 35,48 42,42',b.DARK)
    if v=='lo-writer':return page(b,b.BLUE,line('M1 4H25M1 11H25M1 18H25M1 25H18',stroke=b.LIGHT,w=2))
    if v=='lo-calc':return page(b,b.TEAL,r(1,1,28,27,b.LIGHT)+line('M1 10H29M1 19H29M10 1V28M20 1V28',stroke=b.TEAL,w=1.5))
    if v=='lo-impress':return page(b,b.RED,r(1,2,27,20,b.LIGHT)+line('M15 22V31M6 32H24',stroke=b.LIGHT,w=2)+r(5,12,4,7,b.BLUE)+r(12,7,4,12,b.TEAL)+r(20,4,4,15,b.GOLD))
    if v=='lo-math':return page(b,b.PURPLE,line('M2 14L8 22L17 3H29M22 15H28M25 12V18',stroke=b.LIGHT,w=2.5))
    if v=='kontact':return b.group(b.book(),'translate(-5 6) scale(.72)')+p('28,30 54,18 54,40 28,52',b.LIGHT)+line('M28 30L40 35L54 18',w=1.3)+b.group(b.calendar() if hasattr(b,'calendar') else b.app('calendar'),'translate(38 7) scale(.34)')
    if v=='addressbook':return book(b,b.GOLD,b.group(b.classic_extensions.symbol(b,'user'),'scale(.4)'))+''.join(r(14,y,7,3,b.MID) for y in (20,29,38))
    if v=='merkuro-contacts':return book(b,b.TEAL,b.group(b.classic_extensions.symbol(b,'users'),'scale(.4)'))+c(45,10,6,b.GOLD)+line('M45 1V4M45 16V19M36 10H39M51 10H54',stroke=b.GOLD,w=1.5)
    if v=='merkuro-calendar':return b.group(b.app('calendar'),'translate(-1 -3) scale(.83)')+c(46,37,9,b.GOLD)+line('M46 24V28M46 46V50M33 37H37M55 37H59',stroke=b.GOLD,w=1.5)
    if v=='sieveeditor':return p('9,18 45,5 57,15 21,30',b.LIGHT)+p('21,30 57,15 42,38 42,50 33,54 33,41',b.MID)+line('M26 20L36 23L48 12',w=1.5)
    if v=='contact-theme':return page(b,b.LIGHT,b.group(b.classic_extensions.symbol(b,'user'),'scale(.35)')+r(20,8,9,4,b.PURPLE,'none')+r(20,17,9,3,b.MID,'none'))+b.group(b.wrench(),'translate(37 27) scale(.36)')
    if v=='contact-print':return b.group(b.printer(),'translate(-1 14) scale(.68)')+b.group(page(b,b.LIGHT,b.group(b.classic_extensions.symbol(b,'user'),'scale(.35)')),'translate(24 -2) scale(.62)')
    if v=='mail-theme':return b.group(b.app('mail'),'translate(-3 7) scale(.75)')+b.group(b.wrench(),'translate(36 19) scale(.4)')
    # Text editors: recognizable physical cues instead of a shared pencil.
    if v=='kate':return b.group(b.book(),'translate(-4 3) scale(.78)')+line('M22 45L49 7',stroke=b.GOLD,w=5)+p('22,45 17,54 26,49',b.INK)
    if v=='kwrite':return page(b,b.LIGHT,line('M2 4H26M2 11H26M2 18H26M2 25H18',w=1.5))
    if v=='gedit':return page(b,b.LIGHT,line('M1 10H27M1 17H27M1 24H18',stroke=b.BLUE,w=1))+''.join(c(x,10-(x-12)*.35,2,b.MID) for x in (12,19,26,33,40))+line('M32 47L52 14',stroke=b.RED,w=4)
    if v=='mousepad':return page(b,b.LIGHT)+p('16,16 40,7 45,12 21,21',b.BLUE)+line('M23 44L50 13',stroke=b.GOLD,w=5)+p('23,44 19,52 27,48',b.DARK)
    if v=='featherpad':return page(b,b.LIGHT)+line('M24 46Q21 17 51 7Q53 26 24 46Z',b.PAPER,stroke=b.PURPLE,w=1.3)+line('M22 53L47 14',stroke=b.GOLD,w=2)
    if v=='feathernotes':return p('13,17 40,6 52,12 25,24',b.GOLD)+p('25,24 52,12 52,36 25,48',b.GOLD)+line('M28 30L44 23M28 37L40 32',w=1.5)+line('M37 51Q33 27 57 19Q59 36 37 51Z',b.PAPER,stroke=b.PURPLE,w=1.2)
    if v=='cherrytree':return line('M34 11V46M34 19L21 26M34 30L47 38M34 41L22 47',stroke=b.DARK,w=3)+c(34,9,6,b.RED)+c(20,26,6,b.RED)+c(47,37,6,b.RED)+c(21,47,6,b.RED)+p('31,6 43,4 35,11',b.TEAL)
    if v=='notepadqq':return page(b,b.LIGHT,line('M2 6L10 12L2 18M27 6L19 12L27 18M16 2L12 25',stroke=b.TEAL,w=2))
    if v=='pluma':return page(b,b.PAPER)+line('M23 48Q20 20 49 7Q50 27 23 48Z',b.BLUE,w=1.3)+line('M20 53L43 17',stroke=b.LIGHT,w=1.5)
    if v=='xfw':return p('9,17 44,4 55,12 20,25',b.LIGHT)+p('20,25 55,12 55,44 20,56',b.PAPER)+line('M26 29L31 44L36 29L42 43L49 21',stroke=b.PURPLE,w=2)
    if v=='xfi':return page(b,b.LIGHT)+p('31,36 53,14 57,19 35,41',b.RED)+p('31,36 28,44 35,41',b.INK)
    raise ValueError('Unknown application object: '+v)
