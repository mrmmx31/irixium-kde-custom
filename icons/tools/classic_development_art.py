# SPDX-License-Identifier: MIT
"""Development tools and configuration identities, without generic code aliases."""
from classic_application_art import page, book
import classic_utility_art


def draw(b,v):
    r,p,c,line=b.rect,b.poly,b.circle,b.path
    if v=='cervisia':return page(b,b.LIGHT)+line('M34 43V20L46 11M34 29L21 23',stroke=b.TEAL,w=3)+c(34,43,4,b.PURPLE)+c(46,11,4,b.GOLD)+c(21,23,4,b.BLUE)
    if v=='kompare':return b.group(page(b,b.LIGHT,line('M1 5H25M1 13H25M1 21H18',stroke=b.RED,w=2)),'translate(-6 8) scale(.8)')+b.group(page(b,b.PAPER,line('M1 5H25M1 13H18M1 21H25',stroke=b.BLUE,w=2)),'translate(23 -4) scale(.8)')+line('M22 43L40 36M35 33L40 36L34 41',stroke=b.GOLD,w=2)
    if v=='meld':return b.group(page(b,b.TEAL),'translate(-9 13) scale(.65)')+b.group(page(b,b.PAPER),'translate(9 0) scale(.75)')+b.group(page(b,b.RED),'translate(32 12) scale(.55)')+line('M14 37L34 27L48 34',stroke=b.GOLD,w=2)
    if v=='kapptemplate':return page(b,b.LIGHT)+r(31,7,22,15,b.BLUE)+p('37,26 47,19 54,24 51,31 56,38 44,45 38,39 31,37',b.PURPLE)
    if v=='kuiviewer':return p('11,16 44,4 54,11 21,25',b.LIGHT)+p('21,25 54,11 54,44 21,57',b.PAPER)+p('25,27 50,17 50,23 25,33',b.PURPLE)+p('26,38 35,34 35,48 26,52',b.MID)+line('M39 35L49 31M39 41L49 37',stroke=b.BLUE,w=2)
    if v=='umbrello':return line('M7 25Q30 -5 56 19L46 29L36 23L26 34L17 28Z',b.BLUE,w=1.4)+line('M31 22V45Q31 57 40 48M31 2V6',stroke=b.GOLD,w=2.5)+line('M17 28Q20 8 31 6Q44 5 46 29',stroke=b.LIGHT,w=1)
    if v=='lazarus':return c(32,28,23,b.BLUE)+p('15,18 22,9 32,16 43,8 51,19 46,42 32,50 18,40',b.GOLD)+c(24,24,3,b.INK)+c(40,24,3,b.INK)+p('27,33 37,33 32,39',b.INK)+line('M24 39L17 37M40 39L47 37',w=1.5)
    if v=='okteta':return p('12,15 42,4 52,10 22,24',b.LIGHT)+p('22,24 52,10 52,45 22,57',b.PAPER)+line('M27 28L34 25V34L27 37V28M39 23L46 20V29L39 32V23M27 42L34 39V48L27 51V42M39 37V46M44 35V44',stroke=b.PURPLE,w=1.5)
    if v=='kcachegrind':return line('M13 16L34 25L48 10M34 25V43',w=2)+p('7,12 17,7 24,13 14,19',b.TEAL)+p('42,8 51,3 58,9 49,15',b.PURPLE)+p('24,25 35,19 44,25 33,32',b.GOLD)+p('24,43 35,37 44,43 33,50',b.BLUE)
    if v=='akonadiconsole':return b.group(b.database(),'translate(-5 -2) scale(.7)')+p('27,29 54,18 54,43 27,55',b.DARK)+line('M33 34L39 37L33 44M42 43L49 40',stroke=b.LIGHT,w=2)
    if v=='translation-category':return book(b,b.PURPLE)+line('M17 16L47 7M41 3L47 7L40 12M45 44L21 53M28 48L21 53L28 56',stroke=b.GOLD,w=3)
    if v=='web-category':return b.group(b.monitor(),'translate(-3 6) scale(.83)')+line('M18 23L12 30L18 33M43 13L50 17L43 23M34 12L24 36',stroke=b.TEAL,w=2.5)
    if v in ('qt5ct','qt6ct'):
        s=p('12,16 40,4 53,12 25,26',b.LIGHT)+p('12,16 25,26 25,51 12,44',b.DARK)+p('25,26 53,12 53,40 25,55',b.TEAL)+c(35,31,8,b.LIGHT)+c(35,31,5,b.TEAL)+line('M40 36L46 40M43 20L51 17M47 19V31',stroke=b.LIGHT,w=2)
        return s+ (line('M46 40H54M46 40V45H53V51H46',stroke=b.PURPLE,w=2) if v=='qt5ct' else line('M54 40H47L46 51H54V45H46',stroke=b.PURPLE,w=2))
    if v=='userinfo':return page(b,b.LIGHT,b.group(b.classic_extensions.symbol(b,'user'),'scale(.35)')+line('M18 6H28M18 13H28M3 30H27',stroke=b.BLUE,w=1.5))
    if v=='vmware-netcfg':return b.group(b.classic_extensions.symbol(b,'network'),'translate(-3 7) scale(.82)')+p('35,15 48,9 56,15 43,22',b.GOLD)+line('M43 22V31',stroke=b.BLUE,w=2)
    if v=='synaptic':return b.group(b.box(),'translate(-8 10) scale(.65)')+b.group(b.box(),'translate(22 -5) scale(.58)')+b.group(b.box(),'translate(29 24) scale(.4)')+line('M19 43L43 15',stroke=b.TEAL,w=2)
    if v=='gnome-software':return p('13,16 41,5 52,12 24,24',b.LIGHT)+p('24,24 52,12 52,44 24,56',b.GOLD)+line('M31 22V11Q31 1 43 9V17',stroke=b.DARK,w=2)+c(39,33,8,b.LIGHT)+line('M35 36L39 25L44 32L39 39Z',b.PURPLE,w=1)
    if v=='thunar-settings':return b.group(classic_utility_art.draw(b,'thunar'),'translate(-4 -3) scale(.83)')+b.group(b.wrench(),'translate(36 31) scale(.4)')
    if v=='lxtask':return b.group(b.classic_extensions.symbol(b,'cpu'),'translate(-5 3) scale(.8)')+b.ellipse(44,35,13,13,b.PAPER)+line('M44 35L50 26',stroke=b.RED,w=2)+line('M35 43H52',stroke=b.TEAL,w=2)
    if v=='xfa':return b.group(b.archive(),'translate(-3 5) scale(.8)')+p('36,27 52,18 59,34 43,44',b.LIGHT)+line('M41 31L51 25M43 36L53 30',stroke=b.BLUE,w=1.5)
    if v=='ktnef':return b.group(b.app('mail'),'translate(-5 9) scale(.75)')+p('36,13 53,5 57,9 40,19 40,40 36,37',b.GOLD)+line('M44 20L52 16M44 27L52 23',stroke=b.BLUE,w=1.5)
    raise ValueError('Unknown development object: '+v)
