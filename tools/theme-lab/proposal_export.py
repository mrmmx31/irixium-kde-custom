"""Proposal comparison; does not label a generated theme as a live preview."""
import copy
import hashlib
import json
import re


def validate_delta(delta):
    if (not isinstance(delta, dict) or type(delta.get('schema')) is not int or
            delta['schema'] != 1 or delta.get('kind') != 'theme_lab_project_delta'):
        raise ValueError('Contrato de delta de projeto inválido.')
    for key in ('base_model_sha256', 'proposal_model_sha256'):
        if not isinstance(delta.get(key), str) or not re.fullmatch(r'[a-f0-9]{64}', delta[key]):
            raise ValueError('Hash inválido no delta: ' + key)
    changes = delta.get('changes')
    if not isinstance(changes, list) or len(changes) > 10000:
        raise ValueError('Lista de mudanças inválida ou excessiva.')
    for change in changes:
        if not isinstance(change, dict) or change.get('operation') not in ('add', 'remove', 'replace'):
            raise ValueError('Operação inválida no delta.')
        path = change.get('path')
        if (not isinstance(path, list) or not 1 <= len(path) <= 32 or
                any(not (isinstance(key, str) or (type(key) is int and key >= 0)) for key in path)):
            raise ValueError('Caminho de mudança inválido no delta.')
        if change['operation'] in ('add', 'replace') and 'value' not in change:
            raise ValueError('Valor ausente na mudança.')


def model_digest(model):
    return hashlib.sha256(json.dumps(model, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def affected_families(before, after):
    families = sorted(after['recipes'])
    if before.get('color_scheme', '') != after.get('color_scheme', ''):
        return families
    return [family for family in families
            if differences(before['recipes'].get(family), after['recipes'][family])]


def replay_delta(before, delta):
    """Replay only against the exact base; never overwrite a diverged project."""
    if delta.get('base_model_sha256') != model_digest(before):
        raise ValueError('Projeto base divergente; não aplicar a proposta.')
    model = copy.deepcopy(before)
    try:
        for change in delta['changes']:
            path = change['path']
            if not path:
                raise ValueError('A proposta não pode substituir a raiz inteira.')
            parent = model
            for key in path[:-1]:
                parent = parent[key]
            key = path[-1]
            operation = change['operation']
            if operation == 'remove':
                del parent[key]
            elif operation in ('add', 'replace'):
                parent[key] = copy.deepcopy(change['value'])
            else:
                raise ValueError('Operação desconhecida na proposta.')
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError('Mudança não corresponde à estrutura do projeto base.') from error
    if model_digest(model) != delta.get('proposal_model_sha256'):
        raise ValueError('Proposta inconsistente; resultado não corresponde ao hash.')
    return model


def differences(before, after, path=()):
    """Preserve additions/removals explicitly, including null values."""
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            location = path + (key,)
            if key not in before:
                result.append({'path': list(location), 'operation': 'add', 'value': after[key]})
            elif key not in after:
                result.append({'path': list(location), 'operation': 'remove', 'previous': before[key]})
            else:
                result.extend(differences(before[key], after[key], location))
        return result
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        result = []
        for index, (old, new) in enumerate(zip(before, after)):
            result.extend(differences(old, new, path + (index,)))
        return result
    if before != after or type(before) is not type(after):
        return [{'path': list(path), 'operation': 'replace', 'previous': before, 'value': after}]
    return []


def review_text(result):
    comparison = result['comparison']
    lines = ['Exportação — proposta e cena salva', '',
             'Pacote: ' + result['package_directory'],
             'Proposta: ' + comparison['proposal_sha256'],
             'Cena salva: ' + comparison['scene_snapshot_sha256'], '',
             'A comparação usa snapshots salvos. Não comprova pintura da prévia.',
             'Nenhum tema foi instalado; o desktop permanece intacto.', '',
             'Mudanças do projeto:']
    changes = comparison['changes']
    if not changes:
        lines.append('Nenhuma mudança no modelo; consulte as origens externas abaixo.')
    for change in changes:
        path = '/'.join(str(value) for value in change['path'])
        old = json.dumps(change.get('previous'), ensure_ascii=False)
        new = json.dumps(change.get('value'), ensure_ascii=False)
        lines.append(path + ' [' + change['operation'] + ']: ' + old + ' → ' + new)
    lines.extend(['', 'Origens externas da paleta:'])
    for family, audit in comparison['scene_palette_comparison'].items():
        state = {'unknown': 'desconhecida; regenerar', 'changed': 'alterada',
                 'unchanged': 'inalterada'}.get(audit['status'], audit['status'])
        lines.append(family + ': ' + state)
    lines.extend(['', 'Arquivos do pacote:'])
    for family, package in result['artifact_packages'].items():
        if package['status'] == 'no_generated_files':
            lines.append(family + ': sem tradução gerada — ' + str(package.get('reason') or 'adaptador pendente'))
        else:
            lines.append(family + ': ' + package['status'] + '; ' +
                         str(package['payload_files']) + ' novos/alterados; ' +
                         str(package['reused_files']) + ' dependências da base; ' +
                         str(package['removed_files']) + ' removidos.')
    lines.extend(['', 'Um delta exige a base exata; snapshot inclui todos os arquivos da família.',
                  'FILES.json identifica arquivos e hashes. DEPENDENCIES.json registra engines e regras.',
                  'As cores geradas são snapshot de papéis KDE: regenerar após trocar a origem efetiva.'])
    return '\n'.join(lines)
