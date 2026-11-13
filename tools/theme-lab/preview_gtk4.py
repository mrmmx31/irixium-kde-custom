#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 push preview. No theme installation or personal profile edits."""
import argparse
import os
from pathlib import Path
import sys
import backend


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('project','snapshot','events-dir'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--root',type=Path,default=backend.ROOT)
    parser.add_argument('--kdeglobals',type=Path)
    parser.add_argument('--preview-instance')
    parser.add_argument('--private-toggle-session',action='store_true')
    parser.add_argument('--private-check-session',action='store_true')
    parser.add_argument('--private-scrollbar-session',action='store_true')
    parser.add_argument('--runtime-toggle-active',type=int,choices=(0,1))
    parser.add_argument('--runtime-check-active',type=int,choices=(0,1))
    parser.add_argument('--embed-window',type=lambda value:int(value,0))
    parser.add_argument('--host-pid',type=int)
    parser.add_argument('--host-bridge',type=Path)
    parser.add_argument('--host-session-root',type=Path,
                        help='Permite somente GTK4 XEmbed ou captura offscreen na sessão privada do Theme Lab em ~/tempia.')
    parser.add_argument('--capture-control',type=int)
    parser.add_argument('--capture-state',type=int,default=0)
    parser.add_argument('--capture-length',type=int,default=0)
    parser.add_argument('--capture-thickness',type=int,default=0)
    parser.add_argument('--capture-value',type=int,default=25)
    parser.add_argument('--capture-page-size',type=int,default=25)
    parser.add_argument('--capture-part',choices=(
        'whole','arrow','arrow_button','trough','thumb','fitting'),default='whole')
    parser.add_argument('--capture-direction',choices=(
        'auto','left','right','up','down'),default='auto')
    parser.add_argument('--capture-output',type=Path)
    args=parser.parse_args(argv)
    if args.capture_control==1:args.private_toggle_session=True
    elif args.capture_control==2:args.private_check_session=True
    elif args.capture_control in (10,11):args.private_scrollbar_session=True
    if args.runtime_toggle_active is not None and not args.private_toggle_session:
        parser.error('Toggle restoration requires explicit toggle capability')
    if args.runtime_check_active is not None and not args.private_check_session:
        parser.error('Checkbox restoration requires explicit check capability')
    if args.private_scrollbar_session and (args.private_toggle_session or args.private_check_session):
        parser.error('Scrollbar and button preview sessions are mutually exclusive')
    root=args.root.resolve()
    if args.host_session_root is not None and os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE')!='bwrap':
        guards=backend.embedded_user_preview_guard(
            root,args.project,args.snapshot,args.events_dir,args.host_session_root,
            args.embed_window,family='gtk4',capture_mode=args.capture_control is not None,
            capture_output=args.capture_output)
    else:
        guards=backend.private_namespace(root)  # Before any GTK init.
    if args.embed_window is not None:
        from scene_contract import integer
        integer(args.embed_window,1,0xffffffff,'embed_window')
    if bool(args.embed_window)!=bool(args.host_pid and args.host_bridge):
        parser.error('Embedding requires canvas, host PID and host bridge together')
    if ((args.capture_control is None)!=(args.capture_output is None) or
            not 0<=args.capture_state<=4):
        parser.error('GTK4 capture requires a control, output, and state 0..4')
    if args.capture_control is not None:
        if args.capture_control not in (0,1,2,10,11):
            parser.error('GTK4 capture is unavailable for this untranslated control')
        if args.capture_control in (1,2) and args.private_scrollbar_session:
            parser.error('Button capture conflicts with the scrollbar session')
        if args.capture_control in (10,11) and not args.private_scrollbar_session:
            parser.error('Scrollbar capture requires the native scrollbar session')
        if args.capture_control==1 and not args.private_toggle_session:
            parser.error('Toggle capture requires its private native session')
        if args.capture_control==2 and not args.private_check_session:
            parser.error('Check capture requires its private native session')
        if args.capture_length and not 15<=args.capture_length<=2048:
            parser.error('GTK4 private length must be natural or 15..2048 px')
        if args.capture_thickness and not 1<=args.capture_thickness<=512:
            parser.error('GTK4 private thickness must be natural or 1..512 px')
        if not 1<=args.capture_page_size<=100 or not 0<=args.capture_value<=100-args.capture_page_size:
            parser.error('GTK4 private range is 0..100 and value must fit before page end')
        if args.capture_control not in (10,11) and any((
                args.capture_length,args.capture_thickness,args.capture_value!=25,
                args.capture_page_size!=25,args.capture_part!='whole',
                args.capture_direction!='auto')):
            parser.error('GTK4 geometry/range/part/direction requires a scrollbar')
        if args.capture_control==10 and args.capture_direction not in ('auto','left','right'):
            parser.error('GTK4 horizontal scrollbar accepts auto/left/right only')
        if args.capture_control==11 and args.capture_direction not in ('auto','up','down'):
            parser.error('GTK4 vertical scrollbar accepts auto/up/down only')
    from gtk4_worker import Worker
    return Worker(args,guards).run()


def entrypoint(argv=None):
    """Report an expected private-session refusal without a Python traceback."""
    try:
        return main(argv)
    except backend.Unavailable as error:
        print('Prévia GTK4 indisponível: '+str(error),file=sys.stderr,flush=True)
        return 2


if __name__=='__main__':sys.exit(entrypoint())
