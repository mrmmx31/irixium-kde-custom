#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Replace this user's panel with DomainOS; restore the saved layout through KDE."""
from __future__ import annotations
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import unquote, urlparse
import uuid

sys.dont_write_bytecode = True
from classic_panel import SCRIPT as INSPECTION_SCRIPT
from install_domainos import check_runtime
from install_suite import roots
from panel_layout import SCRIPT as LAYOUT_SCRIPT
from theme_transaction import Failure, atomic, no_links, snapshot

PLUGIN = 'org.irixclassic.domainos.panel'
GLOBAL_THEME = 'org.magpie.irixclassic.domainos.desktop'
IRIX_GLOBAL_THEMES = ('org.magpie.irixclassic.desktop', 'org.magpie.irixium.desktop')


def effective_preference(config, file, group, key):
    """Read the invoking user's actual KConfig precedence, including defaults."""
    for path in (config/file, config/'kdedefaults'/file):
        no_links(path)
        if path.exists() and path.stat().st_uid != os.getuid():
            raise Failure('Configuração pertence a outro usuário: ' + str(path))
    environment = dict(os.environ, XDG_CONFIG_HOME=str(config))
    directories = environment.get('XDG_CONFIG_DIRS') or '/etc/xdg'
    environment['XDG_CONFIG_DIRS'] = ':'.join(dict.fromkeys([
        str(config/'kdedefaults'), *directories.split(':')]))
    result = subprocess.run(['kreadconfig6', '--file', file, '--group', group,
        '--key', key], env=environment, text=True, capture_output=True, check=True, timeout=10)
    return result.stdout.rstrip('\r\n')


def require_global_choice(config, *, restoring=False):
    current = effective_preference(config, 'kdeglobals', 'KDE', 'LookAndFeelPackage')
    expected = IRIX_GLOBAL_THEMES if restoring else (GLOBAL_THEME,)
    if current not in expected:
        raise Failure('O Tema Global mudou; a transição do painel foi recusada.')
    if not restoring and effective_preference(config, 'plasmarc', 'Theme', 'name') != 'IrixClassicDomainOS':
        raise Failure('O Plasma Style não corresponde ao Tema Global DomainOS.')
SCRIPT = INSPECTION_SCRIPT + LAYOUT_SCRIPT + r'''
function domainosPanelSnapshot(panel) {
    var value = panelSnapshot(panel);
    value.widgets.forEach(saved => {
        if (saved.type !== "org.irixclassic.domainos.panel") return;
        var widget = panel.widgetById(saved.id), id = trayId(widget);
        var tray = id > 0 ? desktopById(id) : null;
        if (tray) saved.tray = {id:tray.id,config:configuration(tray,true),widgets:tray.widgets().map(widgetSnapshot)};
        else saved.trayPending = true;
    });
    return value;
}
function tokenPanel(token) {
    return panels().find(p => {
        var initial=p.currentConfigGroup.slice();
        p.currentConfigGroup=["General"];
        var found=p.readConfig("domainosActivationToken", "")===token;
        p.currentConfigGroup=initial;
        return found;
    });
}
function domainosRun(payload) {
    if (payload.action === "inspect") {
        return {ok:true,state:{known:knownWidgetTypes.slice(),panels:panels().map(domainosPanelSnapshot)},
                screens:panels().map(p => ({id:p.id,geometry:screenGeometry(p.screen)}))};
    }
    if (payload.action === "create") {
        var original = panelById(payload.before.id);
        if (!original || !same(stablePanel(panelSnapshot(original)), stablePanel(payload.before)))
            throw new Error("O painel mudou depois da conferência.");
        if (!knownWidgetTypes.includes(payload.plugin)) throw new Error("Instale o applet DomainOS primeiro.");
        if (tokenPanel(payload.token)) throw new Error("Painel desta operação já existe.");
        var created = null;
        try {
            if (payload.savedDomainos) {
                created=panelById(createFromSnapshot(payload.savedDomainos,payload.token).panelId);
                created.currentConfigGroup=["General"];
                created.writeConfig("domainosActivationToken",payload.token);
            } else {
                created = new Panel;
                created.screen = original.screen;
                created.location = "bottom";
                created.alignment = "center";
                created.offset = 0;
                created.height = 109;
                created.lengthMode = "custom";
                created.minimumLength = 971;
                created.maximumLength = 971;
                created.length = 971;
                created.hiding = "none";
                created.floating = true;
                created.currentConfigGroup = ["General"];
                created.writeConfig("domainosActivationToken",payload.token);
                var widget = created.addWidget(payload.plugin);
                if (!widget || widget.type !== payload.plugin) throw new Error("Falha ao criar o applet DomainOS.");
                widget.currentConfigGroup=["General"];
                Object.keys(payload.seedSettings || {}).forEach(key => widget.writeConfig(key,payload.seedSettings[key]));
                if (payload.pins.length) {
                    widget.writeConfig("pinnedApplications",payload.pins);
                }
                widget.reloadConfig();
            }
            return {ok:true,created:domainosPanelSnapshot(created)};
        } catch (error) {
            if (created) created.remove();
            throw error;
        }
    }
    if (payload.action === "resize") {
        var panel=tokenPanel(payload.token);
        if (!panel) throw new Error("Painel desta ativação ausente.");
        panel.minimumLength=payload.width;panel.maximumLength=payload.width;panel.height=payload.height;
        return {ok:true};
    }
    if (payload.action === "seedTray") {
        var active=tokenPanel(payload.token), old=panelById(payload.before.id);
        if (!active || !old || !same(stablePanel(panelSnapshot(old)),stablePanel(payload.before)))
            throw new Error("O painel original mudou; migração da bandeja recusada.");
        if (active.widgets().length!==1 || active.widgets()[0].type!==payload.plugin)
            throw new Error("O painel DomainOS foi reorganizado durante a ativação.");
        layoutPopulateTray(active.widgets()[0],payload.seedTray);
        return {ok:true,created:domainosPanelSnapshot(active)};
    }
    if (payload.action === "commit") {
        var active=tokenPanel(payload.token), old=panelById(payload.before.id);
        if (!active || !old) throw new Error("Os dois painéis esperados precisam existir antes da troca.");
        if (active.widgets().length!==1 || active.widgets()[0].type!==payload.plugin)
            throw new Error("O novo painel foi reorganizado durante a ativação.");
        removePanelChecked(payload.before);
        return {ok:true,created:domainosPanelSnapshot(active)};
    }
    if (payload.action === "rollback") {
        var active=tokenPanel(payload.token);
        if (!panelById(payload.before.id)) throw new Error("Barra anterior ausente; use restaurar.");
        if (active) active.remove();
        return {ok:true};
    }
    if (payload.action === "restore") {
        var active=tokenPanel(payload.token), prior=panelById(payload.before.id);
        if (active && (active.widgets().length!==1 || active.widgets()[0].type!==payload.plugin))
            throw new Error("O painel DomainOS foi reorganizado; restauração recusada.");
        if (prior) {
            if (active) active.remove();
            return {ok:true,original:panelSnapshot(prior)};
        }
        if (panels().some(p => (!active || p.id!==active.id) && p.screen===payload.before.geometry.screen
                              && p.location===payload.before.geometry.location))
            throw new Error("Outro painel passou a ocupar a borda original; restauração recusada.");
        var recovered=null;
        try {
            recovered=panelById(createFromSnapshot(payload.before,payload.restoreToken).panelId);
            if (active) active.remove();
            return {ok:true,original:panelSnapshot(recovered)};
        } catch (error) {
            if (recovered) recovered.remove();
            throw error;
        }
    }
    throw new Error("Operação desconhecida.");
}
'''


def call(payload):
    code = SCRIPT + '\nprint(JSON.stringify(domainosRun(' + json.dumps(payload, ensure_ascii=True) + ')));'
    result = subprocess.run(['gdbus','call','--session','--dest','org.kde.plasmashell',
        '--object-path','/PlasmaShell','--method','org.kde.PlasmaShell.evaluateScript',code],
        text=True,capture_output=True,timeout=30)
    if result.returncode:
        raise Failure(result.stderr.strip() or 'A sessão Plasma não respondeu.')
    values = ast.literal_eval(result.stdout)
    if not isinstance(values,tuple) or len(values)!=1 or not isinstance(values[0],str):
        raise Failure('Resposta inesperada do Plasma.')
    reply = json.loads(values[0])
    if not reply.get('ok'): raise Failure(reply.get('error','Falha na operação Plasma.'))
    return reply


def session_owner():
    result = subprocess.run(['gdbus','call','--session','--dest','org.freedesktop.DBus',
        '--object-path','/org/freedesktop/DBus','--method','org.freedesktop.DBus.GetConnectionUnixUser',
        'org.kde.plasmashell'], text=True,capture_output=True,timeout=15)
    if result.returncode or result.stdout.strip() != '(uint32 '+str(os.getuid())+',)':
        raise Failure('Use o terminal da própria sessão KDE; o Plasma precisa pertencer ao usuário atual.')


def choose(reply, identifier=None):
    panels=reply['state']['panels']
    if PLUGIN not in reply['state']['known']: raise Failure('Instale o applet DomainOS primeiro, nesta sessão KDE.')
    if any(w['type']==PLUGIN for p in panels for w in p['widgets']):
        raise Failure('DomainOS já está em um painel; nenhuma segunda instância criada.')
    candidates=[p for p in panels if identifier is None or p['id']==identifier]
    if len(candidates)!=1: raise Failure('Escolha o painel com --painel ID quando houver mais de um.')
    before=candidates[0]
    geo=next(s['geometry'] for s in reply['screens'] if s['id']==before['id'])
    if geo['width']<971 or geo['height']<218: raise Failure('Esta tela não comporta o desenho mínimo de 971 × 109.')
    if any(p['id']!=before['id'] and p['geometry']['screen']==before['geometry']['screen']
           and p['geometry']['location']=='bottom' for p in panels):
        raise Failure('A borda inferior já está ocupada por outro painel.')
    return before


def launchers(before):
    result=[]
    for widget in before['widgets']:
        if widget['type'] not in ('org.irixclassic.quicklaunch','org.kde.plasma.quicklaunch'): continue
        values=widget['config']['groups'].get('General',{}).get('entries',{}).get('launcherUrls',[])
        if isinstance(values,str): values=re.split(r'(?<!\\),',values)
        for value in values:
            value=value.replace('\\,',',')
            if value.startswith('applications:'): name=unquote(value[len('applications:'):])
            elif value.startswith('file:'): name=Path(unquote(urlparse(value).path)).name
            else: continue
            if name.endswith('.desktop') and '/' not in name and name not in result: result.append(name)
    return result


TASK_TYPES = {'org.irixclassic.iconbox', 'org.kde.plasma.taskmanager', 'org.kde.plasma.icontasks'}
TASK_SETTINGS = {
    'showOnlyCurrentDesktop': ('tasksOnlyCurrentDesktop', 'bool'),
    'showOnlyCurrentScreen': ('tasksOnlyCurrentScreen', 'bool'),
    'showOnlyCurrentActivity': ('tasksOnlyCurrentActivity', 'bool'),
    'onlyGroupWhenFull': ('tasksOnlyGroupWhenFull', 'bool'),
    'groupingStrategy': ('tasksGroupingMode', 'group'),
    'sortingStrategy': ('tasksSortMode', 'sort'),
    'groupingAppIdBlacklist': ('tasksGroupingAppIdBlacklist', 'list'),
    'groupingLauncherUrlBlacklist': ('tasksGroupingLauncherUrlBlacklist', 'list'),
    'middleClickAction': ('middleClickAction', 'middle'),
    'wheelEnabled': ('wheelEnabled', 'bool'),
    'wheelSkipMinimized': ('wheelSkipMinimized', 'bool'),
    'showToolTips': ('iconboxHintsEnabled', 'bool'),
    'interactiveMute': ('interactiveMute', 'bool'),
    'highlightWindows': ('highlightWindows', 'bool'),
    'unhideOnAttention': ('unhideOnAttention', 'bool'),
    'showOnlyMinimized': ('tasksFilterMode', 'filter'),
}


def config_list(value):
    """WorkspaceScripting returns saved KConfig lists as escaped strings."""
    if value is None or value in ('', 'None'): return []
    if isinstance(value, str):
        values = [entry.replace('\\,', ',').replace('\\\\', '\\')
                  for entry in re.split(r'(?<!\\),', value)]
    elif isinstance(value, list) and all(isinstance(entry, str) for entry in value): values = value[:]
    else: raise Failure('Lista inválida no painel original.')
    return list(dict.fromkeys(values))


def setting_value(value, kind):
    if kind == 'list': return config_list(value)
    if kind in ('bool', 'filter'):
        if isinstance(value, bool): parsed = value
        elif isinstance(value, str) and value.lower() in ('true', 'false', '1', '0'):
            parsed = value.lower() in ('true', '1')
        else: raise Failure('Valor booleano inválido no painel original.')
        return ('minimized' if parsed else 'normal') if kind == 'filter' else parsed
    if isinstance(value, bool) or not re.fullmatch(r'[0-9]+', str(value)):
        raise Failure('Opção numérica inválida no painel original.')
    number = int(value)
    if number > {'group': 1, 'sort': 5, 'middle': 5}[kind]:
        raise Failure('Opção do gerenciador original não suportada: '+str(number))
    return number


def seed_preferences(before):
    """Translate compatible explicit choices; new gestures keep approved defaults.

    Multiple task/tray instances cannot silently collapse their independent
    settings. Refuse before creating anything rather than pick one arbitrarily.
    The untouched complete source snapshot remains the restoration authority.
    """
    tasks = [widget for widget in before['widgets'] if widget['type'] in TASK_TYPES]
    trays = [widget for widget in before['widgets'] if widget['type'] in
             ('org.irixclassic.systemtray', 'org.kde.plasma.systemtray')]
    if len(tasks) > 1 or len(trays) > 1:
        raise Failure('O painel tem múltiplos gerenciadores/bandejas com preferências independentes; selecione um painel com uma única instância antes da troca.')
    settings = {}
    if tasks:
        entries = tasks[0]['config']['groups'].get('General', {}).get('entries', {})
        for old, (new, kind) in TASK_SETTINGS.items():
            if old in entries: settings[new] = setting_value(entries[old], kind)
    tray = trays[0].get('tray') if trays else None
    if trays and not tray: raise Failure('Snapshot da bandeja original ausente.')
    if tray:
        entries = tray['config']['groups'].get('General', {}).get('entries', {})
        for old, new in (('shownItems', 'trayVisibleItems'), ('hiddenItems', 'trayHiddenItems')):
            if old in entries: settings[new] = config_list(entries[old])
    return settings, tray


@contextmanager
def locked(directory):
    no_links(directory); directory.mkdir(parents=True,mode=0o700,exist_ok=True)
    no_links(directory/'lock')
    with (directory/'lock').open('a+b') as stream:
        os.chmod(directory/'lock',0o600)
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def save(path, value): atomic(path,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


def latest(directory):
    pointer=directory/'latest'; no_links(pointer)
    if not pointer.is_file(): raise Failure('Não há ativação registrada para restaurar.')
    token=pointer.read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{32}',token): raise Failure('Recibo inválido.')
    path=directory/'backups'/token/'receipt.json'; no_links(path)
    record=json.loads(path.read_text())
    if record.get('format')!=1 or record.get('uid')!=os.getuid() or record.get('token')!=token or record.get('plugin')!=PLUGIN:
        raise Failure('O recibo não pertence a este usuário/applet.')
    if record.get('origin', 'manual') not in ('manual', 'global'):
        raise Failure('Origem da ativação inválida.')
    return path,record


def find_created(reply, token):
    return next((p for p in reply['state']['panels'] if p['config']['groups'].get('General',{}).get('entries',{}).get('domainosActivationToken')==token),None)


def reconcile(path,record,call_fn=call):
    current=call_fn({'action':'inspect'})
    created=find_created(current,record['token'])
    original=next((p for p in current['state']['panels'] if p['id']==record['before']['id']),None)
    if created and original and record.get('status')=='committing':
        for _ in range(8):
            time.sleep(.1)
            current=call_fn({'action':'inspect'})
            created=find_created(current,record['token'])
            original=next((p for p in current['state']['panels'] if p['id']==record['before']['id']),None)
            if not original: break
    if created and not original:
        record.update(status='active',created=created); save(path,record); return True
    if original:
        if created: call_fn(dict(record,action='rollback'))
        record.update(status='restored',restored=original); save(path,record); return False
    record['status']='recovery_needed'; save(path,record)
    raise Failure('Resultado incompleto; execute --restaurar. Backup: '+str(path.parent))


def wait_ready(token):
    end=time.monotonic()+20; adjusted=False
    while time.monotonic()<end:
        created=find_created(call({'action':'inspect'}),token)
        if created and len(created['widgets'])==1:
            widget=created['widgets'][0]; geometry=widget['geometry']
            width=created['geometry']['maximumLength']; height=created['geometry']['height']
            # Panel containment has horizontal gutters even with CanFillArea.
            # Its minimum-sized child can overflow; include both side gutters.
            clipped=geometry['x']+geometry['width']>width
            if geometry['width']>0 and geometry['height']>0 and not adjusted and (geometry['width']<971 or geometry['height']<109 or clipped):
                extra=max(0,971-geometry['width'],geometry['x']+geometry['width']+geometry['x']-width)
                call({'action':'resize','token':token,'width':width+extra,
                      'height':height+max(0,109-geometry['height'])})
                adjusted=True
            elif geometry['width']>=971 and geometry['height']>=109 and not clipped and widget.get('tray'):
                return created
        time.sleep(.15)
    raise Failure('O novo painel não atingiu a geometria/bandeja esperadas; a barra anterior será mantida.')


def verify_seed(created, settings, tray):
    """Refuse destructive commit unless the new native instance kept choices."""
    widget = created['widgets'][0]
    actual = widget['config']['groups'].get('General', {}).get('entries', {})
    kinds = {new: kind for new, kind in TASK_SETTINGS.values()}
    for key, wanted in settings.items():
        if key not in actual: return False
        kind = kinds.get(key, 'list')
        try:
            observed = actual[key] if kind == 'filter' else setting_value(actual[key], kind)
        except Failure: return False
        if observed != wanted: return False
    if not tray: return True
    replacement = widget.get('tray')
    if not replacement or replacement['id'] == tray['id']: return False
    old_ids = {child['id'] for child in tray['widgets']}
    if any(child['id'] in old_ids for child in replacement['widgets']): return False

    def semantic(node):
        if isinstance(node, list): return [semantic(value) for value in node]
        if not isinstance(node, dict): return node
        return {key: semantic(value) for key, value in node.items()
                if key not in ('id', 'geometry', 'AppletOrder', 'PreloadWeight', 'UserBackgroundHints', 'SystrayContainmentId')}
    return semantic(replacement) == semantic(tray)


def wait_seeded(token, settings, tray):
    until = time.monotonic() + 20
    while time.monotonic() < until:
        created = find_created(call({'action': 'inspect'}), token)
        if created and len(created['widgets']) == 1 and verify_seed(created, settings, tray): return created
        time.sleep(.15)
    raise Failure('Preferências do painel/bandeja não foram preservadas na nova instância; barra anterior será mantida.')


def activate(before,config,directory,saved_domainos=None, *, origin='manual'):
    if origin not in ('manual', 'global'): raise Failure('Origem da ativação inválida.')
    if origin == 'global': require_global_choice(config)
    settings, tray = ({}, None) if saved_domainos else seed_preferences(before)
    token=uuid.uuid4().hex; path=directory/'backups'/token/'receipt.json'
    record={'format':1,'uid':os.getuid(),'plugin':PLUGIN,'token':token,'status':'prepared',
        'date':datetime.now(timezone.utc).isoformat(),'before':before,'pins':launchers(before),'origin':origin,
        'seedSettings':settings,
        'layoutFiles':{name:snapshot(config/name) for name in ('plasma-org.kde.plasma.desktop-appletsrc','plasmashellrc')}}
    if tray: record['seedTray']=tray
    if saved_domainos: record['savedDomainos']=saved_domainos
    save(path,record); atomic(directory/'latest',(token+'\n').encode())
    try:
        if origin == 'global': require_global_choice(config)
        call(dict(record,action='create'))
        record['created']=wait_ready(token); save(path,record)
        if tray:
            call(dict(record,action='seedTray'))
        if settings or tray:
            record['created']=wait_seeded(token, settings, tray); save(path,record)
        if origin == 'global': require_global_choice(config)
        record['status']='committing';save(path,record)
        call(dict(record,action='commit'))
        if not reconcile(path,record): raise Failure('A troca não foi concluída; barra anterior preservada.')
    except BaseException as error:
        try: completed=reconcile(path,record)
        except BaseException as recovery:
            record['status']='recovery_needed';save(path,record)
            raise Failure('Confira recuperação com --restaurar. Backup: '+str(path.parent)+'; '+str(recovery)) from error
        if not completed: raise Failure('Ativação cancelada; barra anterior preservada: '+str(error)) from error
    return path,record


def restore(path,record, *, config=None, global_request=False):
    if global_request:
        if record.get('origin', 'manual') != 'global' or config is None:
            raise Failure('A ativação não pertence a uma escolha de Tema Global.')
        require_global_choice(config, restoring=True)
    if not record.get('restoreToken'):
        record['restoreToken']=uuid.uuid4().hex;save(path,record)
    current=call({'action':'inspect'}); active=find_created(current,record['token'])
    if active:
        record['savedDomainos']=active; save(path.parent/'domainos-before-restore.json',active);save(path,record)
    try:
        if global_request: require_global_choice(config, restoring=True)
        result=call(dict(record,action='restore'))
    except BaseException:
        current=call({'action':'inspect'})
        if find_created(current,record['token']): raise
        candidates=[p for p in current['state']['panels'] if p['config']['groups'].get('General',{}).get('entries',{}).get('DomainOSLayoutToken')==record['restoreToken']]
        if len(candidates)!=1: raise
        result={'original':candidates[0]}
    record.update(status='restored',restored=result['original']);save(path,record)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar',action='store_true');parser.add_argument('--restaurar',action='store_true')
    parser.add_argument('--painel',type=int);parser.add_argument('--ponte',action='store_true',help='agir somente sobre o painel já autorizado neste perfil')
    parser.add_argument('--global', dest='global_choice', action='store_true',
                        help='transição vinculada ao Tema Global efetivo deste usuário')
    args=parser.parse_args()
    if os.geteuid()==0: raise Failure('Execute como usuário normal, sem sudo.')
    if not shutil.which('gdbus'): raise Failure('Instale gdbus da distribuição antes de ativar o painel.')
    data,config,state=roots();session_owner();directory=state/'irixium-domainos-panel'
    previous=None; old_path=None
    if (directory/'latest').exists():old_path,previous=latest(directory)
    if args.ponte and not previous: raise Failure('Ative o painel uma vez antes de habilitar a ponte de estilos.')
    if args.restaurar:
        if not previous: raise Failure('Não há ativação registrada para restaurar.')
        if previous['status']=='restored': print('Barra Classic já ativa.');return
        print('Restaurar barra Classic a partir de:',old_path.parent)
        if args.verificar:return
        with locked(directory):restore(old_path,previous, config=config, global_request=args.global_choice)
        print('Barra Classic restaurada. Preferências DomainOS preservadas no recibo.');return
    check_runtime(data)
    if args.global_choice: require_global_choice(config)
    if previous and previous['status'] not in ('restored','active') and not args.verificar:
        with locked(directory):
            if reconcile(old_path,previous):
                print('DomainOS já ativo; operação anterior conferida.');return
    current=call({'action':'inspect'})
    if args.global_choice and not previous and any(w['type']==PLUGIN for p in current['state']['panels'] for w in p['widgets']):
        print('Painel DomainOS já criado pelo layout inicial; nenhum segundo painel ou backup fictício criado.')
        return
    if previous and previous['status']=='active' and find_created(current,previous['token']):
        print('DomainOS já ativo.');return
    identifier=args.painel
    if args.ponte and previous['status']=='restored':identifier=previous['restored']['id']
    before=choose(current,identifier)
    if not (previous and previous.get('savedDomainos')): seed_preferences(before)
    print('DomainOS: substituir painel',before['id'],'por uma barra inferior de 971 × 109.')
    if args.verificar:return
    with locked(directory):
        if previous and previous['status'] not in ('restored',):
            if reconcile(old_path,previous):print('DomainOS já ativo.');return
        path,record=activate(before,config,directory,previous.get('savedDomainos') if previous else None,
                             origin='global' if args.global_choice else 'manual')
    print('DomainOS ativo. Backup somente em arquivo:',path.parent)
    print('Voltar ao Classic: selecione IrixClassic no Plasma Style com a ponte instalada.')
    print('Recuperação manual: python3 tools/activate_domainos.py --restaurar')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:sys.exit('ERRO: '+str(error))
