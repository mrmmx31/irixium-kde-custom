# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared GTK4 CSS structure for the renderer and selected-code inspection."""
NAMES=('topleft','topright','bottomleft','bottomright','top','bottom','left','right')
POSITIONS=('left top','right top','left bottom','right bottom','center top','center bottom','left center','right center')


def base(selector, shadow, padding, font):
    return [selector+' {', '  background-image: none; box-shadow: none;',
            '  border-radius: 0; border-style: solid; border-color: transparent;',
            f'  border-width: {shadow}px; border-image: none;',
            '  background-origin: border-box; background-clip: border-box;',
            f'  padding: {padding}px; font-size: {font}px;',
            '  min-width: 0; min-height: 0; transition: none; opacity: 1;', '}']


def state(selector, pseudo, shadow, urls, face, text):
    backgrounds=', '.join('url("'+url+'")' for url in urls) if shadow else 'none'
    lines=[selector+pseudo+' {', f'  background-color: {face}; color: {text};',
           '  background-image: '+backgrounds+';']
    if shadow:
        lengths=[f'{shadow}px {shadow}px']*4+[f'calc(100% - {2*shadow}px) {shadow}px']*2+[f'{shadow}px calc(100% - {2*shadow}px)']*2
        lines+=['  background-position: '+', '.join(POSITIONS)+';',
                '  background-size: '+', '.join(lengths)+';', '  background-repeat: no-repeat;']
    return lines+['}']
