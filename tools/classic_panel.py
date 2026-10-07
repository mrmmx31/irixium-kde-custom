#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Migra somente os widgets do painel Classic do usuário, com restauração verificável."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import configparser
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from theme_transaction import Failure, atomic, decode, no_links, snapshot

MAPPING = {
    'org.kde.plasma.kickoff': 'org.irixclassic.applications',
    'org.kde.plasma.quicklaunch': 'org.irixclassic.quicklaunch',
    'org.kde.plasma.taskmanager': 'org.irixclassic.iconbox',
    'org.kde.plasma.systemtray': 'org.irixclassic.systemtray',
    'org.kde.plasma.analogclock': 'org.irixclassic.analogclock',
}
TRAYS = {'org.kde.plasma.systemtray', 'org.irixclassic.systemtray'}

# WorkspaceScripting objects intentionally expose configuration and layout,
# not the QML visual tree. Moving existing widgets through addWidget(widget)
# preserves their IDs and configuration. In particular, an inner tray is a
# QObject child of its wrapper: its widgets must move BEFORE wrapper removal.
# https://invent.kde.org/plasma/plasma-workspace/-/blob/v6.3.6/applets/systemtray/container/systemtraycontainer.cpp
SCRIPT = r'''
var removedIds = [];
function ordered(value) {
    if (Array.isArray(value)) return value.map(ordered);
    if (value && typeof value === "object") {
        var output = {};
        Object.keys(value).sort().forEach(k => output[k] = ordered(value[k]));
        return output;
    }
    return value;
}
function same(a, b) { return JSON.stringify(ordered(a)) === JSON.stringify(ordered(b)); }
function stablePanel(panel) {
    var copy = JSON.parse(JSON.stringify(panel));
    // PanelView::length is m_contentLength, not the window's configured
    // length. New delegates change it; bounds/mode/height remain significant.
    delete copy.geometry.length;
    function trim(widget) {
        delete widget.geometry;
        delete widget.config.entries.PreloadWeight;
        delete widget.config.entries.UserBackgroundHints;
        if (widget.tray) widget.tray.widgets.forEach(trim);
    }
    copy.widgets.forEach(trim);
    return copy;
}
function configuration(object, containment) {
    var initial = object.currentConfigGroup.slice();
    function read(path) {
        object.currentConfigGroup = path;
        var result = {entries: {}, groups: {}};
        object.configKeys.slice().sort().forEach(key => {
            // Native panel layout rewrites IDs here. Order is captured below.
            if (!(containment && path.length === 1 && path[0] === "General" && key === "AppletOrder")) {
                result.entries[key] = object.readConfig(key);
            }
        });
        object.configGroups.slice().sort().forEach(group => {
            // Containment.config starts above each child's Configuration.
            // Widgets are captured separately, including recursive config.
            if (containment && path.length === 0 && group === "Applets") return;
            result.groups[group] = read(path.concat([group]));
        });
        return result;
    }
    try { return read([]); }
    finally { object.currentConfigGroup = initial; }
}
function writeConfiguration(object, tree, skipTrayReference) {
    var initial = object.currentConfigGroup.slice();
    function write(path, node) {
        object.currentConfigGroup = path;
        Object.keys(node.entries).forEach(key => {
            if (skipTrayReference && key === "SystrayContainmentId") return;
            object.writeConfig(key, node.entries[key]);
        });
        Object.keys(node.groups).forEach(group => write(path.concat([group]), node.groups[group]));
    }
    try { write([], tree); }
    finally { object.currentConfigGroup = initial; }
    object.reloadConfig();
}
function trayId(widget) {
    var initial = widget.currentConfigGroup.slice();
    try {
        widget.currentConfigGroup = [];
        var id = Number(widget.readConfig("SystrayContainmentId", 0));
        if (id > 0) return id;
        // Accommodate profiles which stored this reference under General.
        widget.currentConfigGroup = ["General"];
        return Number(widget.readConfig("SystrayContainmentId", 0));
    } finally { widget.currentConfigGroup = initial; }
}
function inner(widget) {
    var id = trayId(widget);
    var containment = id > 0 ? desktopById(id) : null;
    if (!containment) throw new Error("Bandeja interna indisponível: " + id);
    return containment;
}
function isTray(type) {
    return type === "org.kde.plasma.systemtray" || type === "org.irixclassic.systemtray";
}
function widgetSnapshot(widget) {
    var result = {id: widget.id, type: widget.type, config: configuration(widget),
                  shortcut: widget.globalShortcut, background: widget.userBackgroundHints,
                  geometry: widget.geometry};
    if (isTray(widget.type)) {
        var tray = inner(widget);
        result.tray = {id: tray.id, config: configuration(tray, true),
                       widgets: tray.widgets().filter(w => w.id > 0 && !removedIds.includes(w.id)).sort((a,b) => a.id-b.id).map(widgetSnapshot)};
    }
    return result;
}
function panelSnapshot(panel) {
    var initial = panel.currentConfigGroup.slice();
    panel.currentConfigGroup = ["General"];
    var order = String(panel.readConfig("AppletOrder", "")).split(";").map(Number);
    panel.currentConfigGroup = initial;
    // destroy() clears the scripting wrapper immediately, while the native
    // applet remains in its containment until the event loop deletes it.
    var widgets = panel.widgets().filter(w => w.id > 0 && !removedIds.includes(w.id));
    widgets.sort((a,b) => {
        var ai=order.indexOf(a.id), bi=order.indexOf(b.id);
        if (ai >= 0 && bi >= 0) return ai-bi;
        if (ai >= 0) return -1;
        if (bi >= 0) return 1;
        return a.geometry.x-b.geometry.x || a.geometry.y-b.geometry.y || a.id-b.id;
    });
    var result = {id: panel.id, type: panel.type, config: configuration(panel, true), geometry: {},
                  widgets: widgets.map(widgetSnapshot)};
    ["screen", "location", "alignment", "offset", "lengthMode", "length", "minimumLength",
     "maximumLength", "height", "hiding", "floating", "opacity"].forEach(key => result.geometry[key] = panel[key]);
    return result;
}
function inspect() {
    return {known: knownWidgetTypes.slice(), panels: panels().map(panelSnapshot)};
}
function expectedPanel(panel, before, identifiers) {
    var result = panelSnapshot(panel);
    // Panel's visual delegates and AppletOrder are synchronized by Qt.callLater.
    // Return the intended order now; the Python caller independently reads
    // the live panel after this script returns and verifies the native order.
    result.widgets = before.widgets.map(saved => {
        var id = identifiers[saved.id] || saved.id;
        var found = result.widgets.find(w => w.id === id);
        if (!found) throw new Error("Widget esperado ausente: " + id);
        return found;
    });
    return result;
}
function transferTray(source, target, desired) {
    var from = inner(source), to = inner(target);
    if (from.id === to.id) throw new Error("A nova bandeja não possui um containment independente.");
    // A newly constructed native wrapper initially contains default widgets.
    // They belong to this transaction, not to the user's original tray.
    writeConfiguration(to, desired.config, false);
    // reloadConfig may construct the selected default tray widgets. Clear
    // them after reloading, before moving the user's original instances.
    to.widgets().slice().forEach(widget => { removedIds.push(widget.id); widget.remove(); });
    var oldWidgets = from.widgets().filter(w => w.id > 0);
    var expectedIds = desired.widgets.map(widget => widget.id).sort((a,b) => a-b);
    if (!same(oldWidgets.map(widget => widget.id).sort((a,b) => a-b), expectedIds)) {
        throw new Error("Os widgets originais da bandeja mudaram.");
    }
    desired.widgets.forEach((saved, index) => {
        var child = from.widgetById(saved.id);
        to.addWidget(child);
    });
    var ids = to.widgets().filter(w => w.id > 0 && !removedIds.includes(w.id)).map(widget => widget.id).sort((a,b) => a-b);
    if (!same(ids, expectedIds)) throw new Error("Falha ao transferir os widgets da bandeja: " + JSON.stringify(ids) + " / " + JSON.stringify(expectedIds));
}
function recoverTray(source, target, desired) {
    var from = inner(source), to = inner(target);
    // Transfer can fail halfway through. Reunite original children from both
    // containments without destroying either half of the user's tray.
    var wanted = desired.widgets.map(widget => widget.id);
    for (var id of wanted) {
        if (!from.widgetById(id) && !to.widgetById(id)) {
            throw new Error("Widget original da bandeja ausente durante a recuperação: " + id);
        }
    }
    writeConfiguration(to, desired.config, false);
    to.widgets().slice().forEach(widget => {
        if (!wanted.includes(widget.id)) { removedIds.push(widget.id); widget.remove(); }
    });
    desired.widgets.forEach((saved, index) => {
        var child = to.widgetById(saved.id) || from.widgetById(saved.id);
        if (!to.widgetById(saved.id)) to.addWidget(child);
    });
}
function run(payload) {
    if (payload.action === "inspect") return {ok: true, state: inspect()};
    var panel = panelById(payload.before.id);
    if (!panel || !same(stablePanel(panelSnapshot(panel)), stablePanel(payload.before))) {
        return {ok: false, conflict: true, error: "O painel mudou após o diagnóstico; nenhuma alteração feita."};
    }
    // Check every required type and source ID before creating the first widget.
    for (var spec of payload.specs) {
        var original = panel.widgetById(spec.from.id);
        if (!original || original.type !== spec.from.type ||
            !knownWidgetTypes.includes(spec.type) || !knownWidgetTypes.includes(spec.from.type)) {
            return {ok: false, conflict: true, error: "Widget de origem ou pacote de destino indisponível."};
        }
    }
    var replacements = [];
    try {
        for (var spec of payload.specs) {
            var original = panel.widgetById(spec.from.id);
            // Widget.index/geometry setters are no-ops in Plasma 6.3. Passing
            // position to addWidget invokes the native createApplet path and
            // inserts in the existing container's first half, before it.
            var position = original.geometry;
            var replacement = panel.addWidget(spec.type, position.x + position.width/4,
                                               position.y + position.height/2,
                                               position.width, position.height);
            if (!replacement || replacement.type !== spec.type) throw new Error("Falha ao criar " + spec.type);
            var pair = {original: original, replacement: replacement, spec: spec, trayTouched: false};
            replacements.push(pair);
            writeConfiguration(replacement, spec.desired.config, isTray(spec.type));
            replacement.userBackgroundHints = spec.desired.background;
            // Release the existing binding before assigning the same shortcut.
            original.globalShortcut = "";
            replacement.globalShortcut = spec.desired.shortcut;
            if (isTray(spec.type)) {
                pair.trayTouched = true;
                transferTray(original, replacement, spec.desired.tray);
            }
        }
        // All replacements, including tray transfers, are ready before deletion.
        replacements.forEach(pair => { removedIds.push(pair.spec.from.id); pair.original.remove(); });
        var identifiers = {};
        replacements.forEach(pair => identifiers[pair.spec.from.id] = pair.replacement.id);
        var after = expectedPanel(panel, payload.before, identifiers);
        return {ok: true, state: {known: knownWidgetTypes.slice(), panels: [after]}, replacements: replacements.map(pair => ({
            oldId: pair.spec.from.id, newId: pair.replacement.id,
            oldType: pair.spec.from.type, newType: pair.spec.type
        }))};
    } catch (error) {
        var recovery = null;
        try {
            // The script runs synchronously on the shell's GUI thread. Rollback
            // happens before another user action can edit these new widgets.
            replacements.slice().reverse().forEach(pair => {
                var original = panel.widgetById(pair.spec.from.id);
                if (!original || original.id <= 0 || removedIds.includes(pair.spec.from.id)) {
                    var position = pair.replacement.geometry;
                    original = panel.addWidget(pair.spec.from.type, position.x+position.width/4,
                                               position.y+position.height/2,position.width,position.height);
                }
                writeConfiguration(original, pair.spec.from.config, isTray(pair.spec.from.type));
                original.userBackgroundHints = pair.spec.from.background;
                pair.replacement.globalShortcut = "";
                original.globalShortcut = pair.spec.from.shortcut;
                if (pair.trayTouched) recoverTray(pair.replacement, original, pair.spec.from.tray);
                removedIds.push(pair.replacement.id); pair.replacement.remove();
                pair.original = original;
            });
            var identifiers = {};
            replacements.forEach(pair => identifiers[pair.spec.from.id] = pair.original.id);
            recovery = expectedPanel(panel, payload.before, identifiers);
        } catch (rollbackError) { return {ok:false, error:String(error), rollbackError:String(rollbackError), state:inspect()}; }
        return {ok: false, error: String(error), rolledBack: recovery, state: {known:knownWidgetTypes.slice(),panels:[recovery]}};
    }
}
'''


def script(payload):
    return SCRIPT + '\nprint(JSON.stringify(run(' + json.dumps(payload, ensure_ascii=True) + ')));'


def plasma(payload):
    result = subprocess.run([
        'gdbus', 'call', '--session', '--dest', 'org.kde.plasmashell',
        '--object-path', '/PlasmaShell', '--method', 'org.kde.PlasmaShell.evaluateScript',
        script(payload)], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise Failure(result.stderr.strip() or 'A consulta ao Plasma falhou.')
    values = ast.literal_eval(result.stdout)
    if not isinstance(values, tuple) or len(values) != 1 or not isinstance(values[0], str):
        raise Failure('Resposta inesperada do Plasma.')
    return json.loads(values[0])


def selected_style(config):
    # Plasma's kdedefaults layer is per-user and must remain a read-only fallback.
    candidates = [config/'plasmarc', config/'kdedefaults/plasmarc']
    candidates.extend(Path(p)/'plasmarc' for p in os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg').split(':') if p)
    for path in dict.fromkeys(candidates):
        parser = configparser.ConfigParser(interpolation=None); parser.optionxform = str
        parser.read(path)
        if parser.has_option('Theme', 'name'):
            return parser.get('Theme', 'name')
    return 'default'


def diagnose(call=plasma):
    result = call({'action': 'inspect'})
    if not result.get('ok'):
        raise Failure(result.get('error', 'Falha ao consultar o Plasma.'))
    state = result['state']
    if len(state['panels']) != 1:
        raise Failure('A migração exige um único painel existente; nenhum layout foi alterado.')
    return state


def plan(panel):
    specs = []
    for widget in panel['widgets']:
        if widget['type'] not in MAPPING:
            continue
        desired = json.loads(json.dumps(widget))
        if widget['type'] == 'org.kde.plasma.taskmanager':
            general = desired['config']['groups'].setdefault('General', {'entries': {}, 'groups': {}})
            # readConfig without a typed default returns stored KConfig strings.
            # Keep that representation for the native postcondition comparison.
            general['entries'].update(maxStripes='1', forceStripes='true')
        specs.append({'from': widget, 'type': MAPPING[widget['type']], 'desired': desired})
    return specs


def projected(panel, specs):
    """Planned result before new IDs exist; original IDs remain placeholders."""
    result = json.loads(json.dumps(panel))
    by_id = {spec['from']['id']: spec for spec in specs}
    for index, widget in enumerate(result['widgets']):
        if widget['id'] in by_id:
            spec = by_id[widget['id']]
            result['widgets'][index] = dict(spec['desired'], type=spec['type'])
    return result


def reverse_specs(record, current):
    """Accept only the recorded replacement IDs and the five known type pairs."""
    by_id = {w['id']: w for w in current['widgets']}
    originals = {w['id']: w for w in record['before']['widgets']}
    specs, seen = [], set()
    for replacement in record['replacements']:
        old_type, new_type = replacement['oldType'], replacement['newType']
        old_id, new_id = replacement['oldId'], replacement['newId']
        if (old_id in seen or MAPPING.get(old_type) != new_type or
                old_id not in originals or originals[old_id]['type'] != old_type or
                new_id not in by_id or by_id[new_id]['type'] != new_type):
            raise Failure('Identificadores do recibo não correspondem a esta migração.')
        seen.add(old_id)
        specs.append({'from': by_id[new_id], 'type': old_type, 'desired': originals[old_id]})
    expected = {spec['from']['id'] for spec in record['specs']}
    if seen != expected:
        raise Failure('O recibo não registra todos os widgets substituídos.')
    return specs


def semantic(panel):
    """Compare UI configuration while allowing native replacement instance IDs."""
    result = stable(panel)
    for widget in result['widgets']:
        if widget['type'] in MAPPING or widget['type'] in MAPPING.values():
            widget.pop('id')
        if widget['type'] in TRAYS:
            for node in walk_config(widget['config']):
                node['entries'].pop('SystrayContainmentId', None)
            widget['tray'].pop('id')
            # Inner widgets are moved, not replaced: their IDs remain significant.
    return result


def stable(panel):
    """Drop automatic layout geometry and native preload cache counters."""
    result = json.loads(json.dumps(panel))
    result['geometry'].pop('length', None)
    def trim(widget):
        widget.pop('geometry', None)
        widget['config']['entries'].pop('PreloadWeight', None)
        # The property captures this value. Its setter materializes an absent
        # KConfig entry even when setting the same standard/default hint.
        widget['config']['entries'].pop('UserBackgroundHints', None)
        if 'tray' in widget:
            for child in widget['tray']['widgets']:
                trim(child)
    for widget in result['widgets']:
        trim(widget)
    return result


def walk_config(tree):
    yield tree
    for child in tree['groups'].values():
        yield from walk_config(child)


def save(receipt, record):
    atomic(receipt, (json.dumps(record, ensure_ascii=False, indent=2)+'\n').encode())


@contextmanager
def locked(state):
    no_links(state); state.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = state/'lock'; no_links(path)
    with path.open('a+b') as stream:
        os.chmod(path, 0o600)
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Failure('Outra migração do painel está em andamento.') from exc
        yield


def latest(state):
    pointer = state/'latest'; no_links(pointer)
    if not pointer.exists():
        return None
    token = pointer.read_text().strip()
    if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
        raise Failure('Referência de recibo inválida.')
    receipt = state/'backups'/token/'receipt.json'; no_links(receipt)
    return receipt


def apply(config, state, *, call=plasma, dry=False):
    if selected_style(config) != 'IrixClassic':
        raise Failure('Selecione o Plasma Style IrixClassic no usuário atual antes da migração.')
    live = diagnose(call); panel = live['panels'][0]; specs = plan(panel)
    missing = sorted(set(MAPPING.values()) - set(live['known']))
    if missing:
        raise Failure('Widgets Classic ausentes: '+', '.join(missing)+'. Instale a suíte primeiro.')
    if not specs:
        print('O painel já utiliza os widgets Classic; nenhuma alteração feita.')
        return None
    print('Painel:', panel['id'], '| altura preservada:', panel['geometry']['height'], '| widgets:', len(specs))
    for spec in specs:
        print('  '+spec['from']['type']+' → '+spec['type'])
    if dry:
        return None
    with locked(state):
        previous = latest(state)
        if previous:
            status = json.loads(previous.read_text()).get('status')
            if status in ('prepared', 'restoring', 'recovery_needed'):
                raise Failure('Há uma migração interrompida. Examine o recibo antes de continuar: '+str(previous))
        token = uuid.uuid4().hex
        receipt = state/'backups'/token/'receipt.json'
        record = {'format': 1, 'uid': os.getuid(), 'status': 'prepared',
                  'config_path': str(config/'plasma-org.kde.plasma.desktop-appletsrc'),
                  'config_before': snapshot(config/'plasma-org.kde.plasma.desktop-appletsrc'),
                  'before': panel, 'planned_after': projected(panel, specs), 'specs': specs}
        save(receipt, record); atomic(state/'latest', (token+'\n').encode())
        try:
            result = call({'action': 'replace', 'before': panel, 'specs': specs})
            if not result.get('ok'):
                record['error'] = result.get('error')
                record['status'] = 'recovery_needed'
                if result.get('conflict'):
                    record['status'] = 'not_applied'
                elif result.get('rolledBack'):
                    checked = diagnose(call)['panels'][0]
                    record['rolled_back'] = checked
                    if semantic(checked) == semantic(panel):
                        record['status'] = 'rolled_back'
                record['failure'] = result; save(receipt, record)
                raise Failure(result.get('error', 'Migração recusada.'))
            after = result['state']['panels'][0]
            record['after'] = after; record['replacements'] = result['replacements']
            save(receipt, record)
            if semantic(after) != semantic(record['planned_after']):
                raise Failure('O painel resultante não preservou a configuração planejada.')
            checked = diagnose(call)['panels'][0]
            if stable(checked) != stable(after):
                raise Failure('O painel mudou durante a conferência. O recibo conserva os estados para recuperação.')
            record['status'] = 'applied'; record['config_after'] = snapshot(Path(record['config_path']))
            save(receipt, record)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            if record['status'] == 'prepared':
                record['status'] = 'recovery_needed'; record['error'] = str(exc); save(receipt, record)
                # A rejected postcondition is a failed transaction too. Undo
                # only when its authoritative after-state still matches live.
                if 'after' in record:
                    try:
                        current = diagnose(call)['panels'][0]
                        if stable(current) != stable(record['after']):
                            raise Failure('O painel mudou antes da reversão; alterações posteriores preservadas.')
                        undo = call({'action': 'replace', 'before': current,
                                     'specs': reverse_specs(record, current)})
                        if not undo.get('ok') or semantic(undo['state']['panels'][0]) != semantic(panel):
                            raise Failure('A reversão automática exige recuperação pelo recibo.')
                        record['status'] = 'rolled_back'; record['rolled_back'] = undo['state']['panels'][0]
                        save(receipt, record)
                    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as rollback:
                        record['rollback_error'] = str(rollback); save(receipt, record)
            raise
    print('Painel atualizado. Recibo: '+str(receipt))
    return receipt


def restore(config, state, *, call=plasma, dry=False):
    receipt = latest(state)
    if receipt is None:
        raise Failure('Nenhuma migração do painel registrada.')
    record = json.loads(receipt.read_text())
    if record.get('format') != 1 or record.get('uid') != os.getuid() or record.get('config_path') != str(config/'plasma-org.kde.plasma.desktop-appletsrc'):
        raise Failure('Recibo não pertence ao perfil atual.')
    decode(record['config_before'])  # Check the full original snapshot's hash.
    if record['status'] == 'restored':
        print('Painel já restaurado.'); return receipt
    if record['status'] in ('rolled_back', 'not_applied'):
        print('A migração não ficou aplicada; nenhuma alteração feita.'); return receipt
    if record['status'] not in ('applied', 'recovery_needed', 'prepared'):
        raise Failure('Recibo incompleto: restauração automática recusada para não substituir alterações desconhecidas. Backup: '+str(receipt))
    live = diagnose(call); current = live['panels'][0]
    if 'after' not in record:
        if stable(current) == stable(record['before']):
            if not dry:
                record['status'] = 'rolled_back'; save(receipt, record)
            print('O painel original está intacto; nenhuma restauração necessária.'); return receipt
        # If the D-Bus reply was lost, recover IDs only from a fully proven
        # planned result; partial or unrelated states remain untouched.
        if semantic(current) != semantic(record['planned_after']):
            raise Failure('Resultado da operação interrompida desconhecido; painel preservado. Backup: '+str(receipt))
        record['after'] = current
        new_by_position = dict(zip((w['id'] for w in record['before']['widgets']), current['widgets']))
        record['replacements'] = [{'oldId': spec['from']['id'], 'newId': new_by_position[spec['from']['id']]['id'],
                                   'oldType': spec['from']['type'], 'newType': spec['type']} for spec in record['specs']]
    if stable(current) != stable(record['after']):
        raise Failure('O painel mudou após a migração; restauração recusada para preservar alterações individuais.')
    specs = reverse_specs(record, current)
    if set(spec['type'] for spec in specs) - set(live['known']):
        raise Failure('Widgets originais indisponíveis. Nenhum widget foi removido.')
    if dry:
        print('Restauração disponível para o painel '+str(current['id'])+'.'); return receipt
    with locked(state):
        record['status'] = 'restoring'; save(receipt, record)
        try:
            result = call({'action': 'replace', 'before': current, 'specs': specs})
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            record['status'] = 'recovery_needed'; record['restore_error'] = str(exc); save(receipt, record)
            raise
        if not result.get('ok'):
            checked = diagnose(call)['panels'][0]
            record['status'] = 'applied' if stable(checked) == stable(current) or result.get('conflict') else 'recovery_needed'
            record['restore_failure'] = result; save(receipt, record)
            raise Failure(result.get('error', 'Falha na restauração.'))
        restored = result['state']['panels'][0]
        if semantic(restored) != semantic(record['before']):
            record['status'] = 'recovery_needed'; record['restore_failure'] = result; save(receipt, record)
            raise Failure('A restauração não reproduziu a configuração original.')
        checked = diagnose(call)['panels'][0]
        if stable(checked) != stable(restored):
            record['status'] = 'recovery_needed'; record['restored'] = restored; save(receipt, record)
            raise Failure('O painel mudou durante a conferência da restauração; consulte o recibo.')
        record['status'] = 'restored'; record['restored'] = restored; save(receipt, record)
    print('Widgets e configuração originais restaurados no mesmo painel.')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true', help='diagnóstico sem alterar arquivos ou widgets')
    parser.add_argument('--restaurar', action='store_true', help='restaurar a última migração deste perfil')
    args = parser.parse_args()
    from reload_decoration import check_session
    from install_suite import roots
    check_session()
    _, config, state = roots()
    state = state/'irixclassic-panel'
    if args.restaurar:
        restore(config, state, dry=args.verificar)
    else:
        apply(config, state, dry=args.verificar)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(f'ERRO: {exc}')
