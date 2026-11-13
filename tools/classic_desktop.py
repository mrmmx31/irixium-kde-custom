#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Adiciona gr_osview e habilita o pager, somente na sessão KDE do próprio usuário."""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from theme_transaction import Failure, atomic, snapshot

PAGER = 'org.kde.plasma.pager'
GROSVIEW = 'org.irixclassic.grosview'
VD_INTERFACE = 'org.kde.KWin.VirtualDesktopManager'
VD_PATH = '/VirtualDesktopManager'

SCRIPT = r'''
function widgetData(w) {
    return {id: w.id, type: w.type, geometry: w.geometry};
}
function inspect() {
    return {known: knownWidgetTypes.filter(t => t === 'org.kde.plasma.pager' || t === 'org.irixclassic.grosview'),
            desktops: desktops().filter(d => d.screen >= 0).map(d => ({
                id: d.id, screen: d.screen, widgets: d.widgets().map(widgetData)
            })),
            panels: panels().map(p => ({id: p.id, screen: p.screen,
                widgets: p.widgets().map(widgetData)}))};
}
function removeCreated(created) {
    var errors = [];
    created.slice().reverse().forEach(saved => {
        try {
            if (!Number.isInteger(saved.containment) || !Number.isInteger(saved.id) ||
                    saved.id <= 0 || saved.containment <= 0 ||
                    ['org.kde.plasma.pager', 'org.irixclassic.grosview'].indexOf(saved.type) < 0) {
                throw new Error('Identificação do widget recém-criado inválida.');
            }
            var c = desktopById(saved.containment) || panelById(saved.containment);
            var w = c ? c.widgetById(saved.id) : null;
            if (w && w.type !== saved.type) throw new Error('O widget mudou; remoção recusada.');
            if (w) w.remove();
        } catch (e) { errors.push(String(e)); }
    });
    return errors;
}
function run(a) {
    var created = [];
    try {
        if (a.action === 'inspect') return {ok: true, state: inspect()};
        if (a.action === 'rollback') {
            var errors = removeCreated(a.created);
            return {ok: errors.length === 0, rollback_errors: errors, state: inspect()};
        }
        if (a.pager) {
            var ps = panels().filter(p => p.screen === a.screen);
            if (ps.length !== 1) throw new Error('Escolha uma tela com um único painel para adicionar o pager.');
            var panel = ps[0];
            if (!panel.widgets().some(w => w.type === 'org.kde.plasma.pager')) {
                var ws = panel.widgets();
                var right = ws.find(w => w.type === 'org.irixclassic.systemtray' || w.type === 'org.kde.plasma.systemtray');
                var g = right ? right.geometry : (ws.length ? ws[ws.length - 1].geometry : {x: 0, y: 0, height: 64});
                var pager = panel.addWidget('org.kde.plasma.pager', g.x, g.y, 112, Math.max(32, g.height));
                if (!pager || pager.id <= 0) throw new Error('Não foi possível adicionar o pager.');
                created.push({containment: panel.id, id: pager.id, type: pager.type});
            }
        }
        if (a.grosview) {
            if (knownWidgetTypes.indexOf('org.irixclassic.grosview') < 0) throw new Error('Instale a suíte atualizada antes de adicionar gr_osview.');
            var desktop = desktopForScreen(a.screen);
            if (!desktop) throw new Error('Desktop não encontrado nesta tela/atividade.');
            if (!desktop.widgets().some(w => w.type === 'org.irixclassic.grosview')) {
                var geo = screenGeometry(a.screen);
                var width = Math.min(280, geo.width - 32);
                var height = Math.min(220, geo.height - 32);
                if (width < 200 || height < 160) throw new Error('Tela pequena demais para este monitor.');
                // Coordinates are local to the containment, not global screen coordinates.
                // Native addWidget supplies geometry; Widget.geometry's setter is a no-op in Plasma 6.3.
                var monitor = desktop.addWidget('org.irixclassic.grosview', geo.width - width - 16, 16, width, height);
                if (!monitor || monitor.id <= 0) throw new Error('Não foi possível adicionar gr_osview.');
                created.push({containment: desktop.id, id: monitor.id, type: monitor.type});
            }
        }
        return {ok: true, created: created, state: inspect()};
    } catch (e) {
        var rollbackErrors = removeCreated(created);
        return {ok: false, error: String(e), created: created,
                rollback_errors: rollbackErrors, state: inspect()};
    }
}
'''


def plasma(payload):
    script = SCRIPT + '\nprint(JSON.stringify(run(' + json.dumps(payload) + ')));'
    result = subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.kde.plasmashell',
        '--object-path', '/PlasmaShell', '--method', 'org.kde.PlasmaShell.evaluateScript', script],
        capture_output=True, text=True, timeout=30, check=True)
    value = ast.literal_eval(result.stdout)
    if not isinstance(value, tuple) or len(value) != 1:
        raise Failure('Resposta inesperada do Plasma.')
    return json.loads(value[0])


def desktop_state():
    result = subprocess.run(['busctl', '--user', '--json=short', 'get-property', 'org.kde.KWin',
                             VD_PATH, VD_INTERFACE, 'desktops'],
                            capture_output=True, text=True, timeout=15, check=True)
    value = json.loads(result.stdout)
    desks = value.get('data')
    if (not isinstance(desks, list) or not desks or
            any(not isinstance(d, list) or len(d) != 3 for d in desks)):
        raise Failure('Lista de áreas de trabalho inesperada.')
    return desks


def ensure_desktops(before, call=None):
    """The native pager hides with one desktop. Add one only in that case."""
    if len(before) >= 2:
        return None
    if len(before) != 1:
        raise Failure('O KWin não forneceu uma área de trabalho válida.')
    if call is None:
        def call(position, name):
            subprocess.run(['busctl', '--user', 'call', 'org.kde.KWin', VD_PATH,
                VD_INTERFACE, 'createDesktop', 'us', str(position), name],
                capture_output=True, text=True, timeout=15, check=True)
    call(1, 'Desktop 2')
    return 'Desktop 2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pager', action='store_true', help='mostrar o pager; criar segunda área apenas se houver uma')
    parser.add_argument('--grosview', action='store_true', help='adicionar uma única instância no canto superior direito')
    parser.add_argument('--tela', type=int, default=0)
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--saida', type=Path, help='relatório público opcional, sem configurações privadas')
    args = parser.parse_args()
    if not args.pager and not args.grosview:
        parser.error('informe --pager, --grosview ou ambos')
    if args.tela < 0:
        parser.error('a tela deve ser um número não negativo')
    from reload_decoration import check_session
    check_session()
    from install_suite import roots
    _, config, state = roots()
    before = plasma({'action': 'inspect'})
    if not before.get('ok'):
        raise Failure(before.get('error', 'Plasma indisponível.'))
    native_before = desktop_state() if args.pager else None
    report = {'uid': os.getuid(), 'screen': args.tela, 'before': before['state'],
              'virtual_desktops_before': native_before, 'status': 'planned'}
    if not args.verificar:
        receipt = state/'irixclassic-desktop'/uuid.uuid4().hex/'receipt.json'
        # Exact private backup stays in this user's state directory, never in --saida.
        record = {'status': 'prepared', 'before': dict(report),
                  'kwinrc_before': snapshot(config/'kwinrc')}
        atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
        report['created_widgets'] = []
        desktop_creation_attempted = False
        add_response_received = False
        try:
            result = plasma({'action': 'add', 'screen': args.tela, 'pager': args.pager, 'grosview': args.grosview})
            add_response_received = True
            report['created_widgets'] = result.get('created', [])
            if not result.get('ok'):
                raise Failure(result.get('error', 'Não foi possível adicionar os widgets.'))
            if args.pager:
                desktop_creation_attempted = len(native_before) == 1
                report['created_virtual_desktop'] = ensure_desktops(native_before)
                native_after = desktop_state()
                if native_after[:len(native_before)] != native_before or len(native_after) < 2:
                    raise Failure('O KWin não confirmou as áreas de trabalho esperadas.')
                report['virtual_desktops_after'] = native_after
            after = plasma({'action': 'inspect'})
            if not after.get('ok'):
                raise Failure(after.get('error', 'Não foi possível conferir os widgets.'))
            report['after'] = after['state']
            report['status'] = 'applied'
            record.update(status='applied', result=report, kwinrc_after=snapshot(config/'kwinrc'))
            atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
        except BaseException as exc:
            errors = []
            if not add_response_received:
                errors.append('Plasma não devolveu os IDs; confira os widgets antes de repetir a operação.')
            if report['created_widgets']:
                try:
                    rollback = plasma({'action': 'rollback', 'created': report['created_widgets']})
                    if not rollback.get('ok'):
                        errors.extend(rollback.get('rollback_errors') or [rollback.get('error', 'Remoção dos novos widgets não confirmada.')])
                    report['after_widget_recovery'] = rollback.get('state')
                except BaseException as rollback_error:
                    errors.append('Widgets: '+str(rollback_error))
            if args.pager:
                # A newly created desktop may already contain a window. Never remove it automatically.
                report['desktop_creation_attempted'] = desktop_creation_attempted
                try:
                    report['virtual_desktops_after_failure'] = desktop_state()
                except BaseException as state_error:
                    report['virtual_desktops_after_failure'] = None
                    report['virtual_desktop_query_error'] = str(state_error)
                report['virtual_desktop_recovery'] = 'Nenhuma área removida; confira a lista preservada no registro.'
            report['status'] = 'failed'
            record.update(status='recovery_needed' if errors else 'failed', result=report,
                          error=type(exc).__name__+': '+str(exc), recovery_errors=errors)
            try:
                record['kwinrc_after_failure'] = snapshot(config/'kwinrc')
                atomic(receipt, (json.dumps(record, indent=2)+'\n').encode())
            except BaseException as journal_error:
                errors.append('Registro: '+str(journal_error))
            detail = '; recuperação incompleta: '+'; '.join(errors) if errors else ''
            raise Failure('Falha ao preparar widgets: '+str(exc)+detail+
                          '. Nenhuma área de trabalho foi removida. Backup: '+str(receipt.parent)) from exc
        print('Backup e registro somente deste usuário: '+str(receipt.parent))
    if args.saida:
        atomic(args.saida, (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode(), mode=0o644)
        print('Resultado para compartilhar: '+str(args.saida))
    print('Verificação concluída.' if args.verificar else 'Widgets e áreas de trabalho preparados nesta sessão.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit('ERRO: '+str(exc))
