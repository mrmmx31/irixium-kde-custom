# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure shared layout contract; toolkit rendering remains independent."""
CONTROLS = ('push', 'toggle', 'check', 'radio', 'entry', 'combo', 'spin', 'text', 'scale_h', 'scale_v', 'scroll_h', 'scroll_v', 'arrow', 'progress', 'list', 'frame')
CATEGORIES = (0,0,0,0,1,1,1,1,2,2,2,2,2,2,3,4)

def integer(value, minimum, maximum, field):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{field}: inteiro entre {minimum} e {maximum} esperado.')
    return value


def scene(model, family='gtk3'):
    """Pure layout specification; never imports GI or mutates a project."""
    if family not in ('gtk2', 'gtk3', 'gtk4', 'qt5', 'qt6', 'kvantum', 'plasma'):
        raise ValueError('Família não suportada pelo contrato de montagem.')
    recipes = model.get('recipes') if isinstance(model, dict) else None
    recipe = recipes.get(family) if isinstance(recipes, dict) else None
    if not isinstance(recipe, dict):
        raise ValueError('Receita da família ausente.')
    categories = integer(recipe.get('visible_categories', 31), 0, 31, 'visible_categories')
    controls = integer(recipe.get('visible_controls', 65535), 0, 65535, 'visible_controls')
    selected = integer(recipe.get('selected_control', 0), 0, 15, 'selected_control')
    state = integer(recipe.get('edit_state', 0), 0, 3, 'edit_state')
    positions = recipe.get('positions', [[16 + (i % 4)*160, 16 + (i // 4)*80] for i in range(16)])
    if not isinstance(positions, list) or len(positions) != len(CONTROLS):
        raise ValueError('positions deve conter 16 pares de coordenadas.')
    sizes = recipe.get('sizes', [[0, 0] for _ in CONTROLS])
    if not isinstance(sizes, list) or len(sizes) != len(CONTROLS):
        raise ValueError('sizes deve conter 16 pares de dimensões.')
    anchors = recipe.get('length_anchor', [0]*len(CONTROLS))
    if (not isinstance(anchors,list) or len(anchors)!=len(CONTROLS) or
            any(type(v) is not int or v not in (0,1) or (v and i not in (10,11)) for i,v in enumerate(anchors))):
        raise ValueError('length_anchor inválida; extremidade somente nas barras.')
    result = []
    for index, (identifier, category, pair) in enumerate(zip(CONTROLS, CATEGORIES, positions)):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('Cada posição deve conter somente x e y.')
        x = integer(pair[0], 0, 2048, f'positions[{index}].x')
        y = integer(pair[1], 0, 2048, f'positions[{index}].y')
        dimensions = sizes[index]
        if not isinstance(dimensions, list) or len(dimensions) != 2:
            raise ValueError('Cada tamanho deve conter largura e altura.')
        width = integer(dimensions[0], 0, 2048, f'sizes[{index}].width')
        height = integer(dimensions[1], 0, 2048, f'sizes[{index}].height')
        if not (categories & (1 << category) and controls & (1 << index)):
            continue
        result.append({'id': identifier, 'index': index, 'category': category,
                       'x': x, 'y': y, 'width': width, 'height': height, 'selected': index == selected,
                       'forced_state': state if index == selected else 0, 'length_anchor': anchors[index]})
    return result

