# SPDX-License-Identifier: GPL-3.0-or-later
"""Native preview explanations; no palette or widget behaviour is changed."""
CONTROL_HINTS = {
    'push': 'Botão de comando: clique dispara uma ação apenas na amostra.',
    'toggle': 'Botão alternável: clique liga ou desliga o estado da amostra.',
    'check': 'Checkbox: clique marca ou desmarca uma escolha independente.',
    'radio': 'Opção exclusiva: escolha uma opção do grupo mostrado nesta amostra.',
    'entry': 'Entrada de uma linha: edite e selecione o texto da amostra; não é texto do projeto.',
    'combo': 'Lista de opções: abra e escolha um item da amostra.',
    'spin': 'Valor numérico da amostra, de 0 a 100, passo 1, sem unidade; não representa tamanho em px.',
    'text': 'Entrada de várias linhas: edite, selecione e role o texto da amostra; não altera o projeto.',
    'scale_h': 'Escala horizontal: arraste para ajustar o valor de 0 a 100, sem unidade.',
    'scale_v': 'Escala vertical: arraste para ajustar o valor de 0 a 100, sem unidade.',
    'scroll_h': 'Barra horizontal: setas, trilho e cursor operam o ajuste da amostra; o intervalo depende da página.',
    'scroll_v': 'Barra vertical: setas, trilho e cursor operam o ajuste da amostra; o intervalo depende da página.',
    'arrow': 'Botão de seta isolado: pressione para observar o relevo; não navega no desktop.',
    'progress': 'Indicador de progresso: exibe o valor da amostra; não é medição de uma tarefa em execução.',
    'list': 'Lista: clique para selecionar uma linha; a moldura e a rolagem pertencem ao contêiner.',
    'frame': 'Moldura com conteúdo: compare o encaixe e o relevo; não possui uma ação de clique.',
}


def control_hint(identifier, family):
    if family not in ('gtk2', 'gtk3'):
        raise ValueError('Família sem contrato de dicas nativas: ' + str(family))
    return (family.upper() + ' nativo. ' + CONTROL_HINTS[identifier] +
            ' Ctrl+clique seleciona no laboratório; Ctrl+arraste propõe a posição em px.'
            ' A aparência segue os papéis da paleta da prévia.')


def bind_control_hint(widget, identifier, family):
    """Cover interactive descendants of compound native controls as well."""
    text = control_hint(identifier, family)

    def query(child, _x, _y, _keyboard, tooltip):
        from gi.repository import Gdk
        allocation = widget.get_allocation()
        offset = (0, 0) if child is widget else widget.translate_coordinates(child, 0, 0)
        if offset is None:
            return False
        area = Gdk.Rectangle()
        area.x, area.y = offset
        area.width, area.height = allocation.width, allocation.height
        tooltip.set_text(text)
        # GTK uses widget coordinates for the applicable area. Compound
        # descendants describe the whole control, not just its inner label.
        tooltip.set_tip_area(area)
        if family == 'gtk3':
            from gtk3_hint_position import track_native_tooltip
            track_native_tooltip(widget)
        elif family == 'gtk2':
            from gtk2_hint_position import track_native_tooltip
            track_native_tooltip(widget)
        return True

    def visit(child):
        child.set_tooltip_text(text)
        child.connect('query-tooltip', query)
        if hasattr(child, 'get_children'):
            for nested in child.get_children():
                visit(nested)

    visit(widget)
