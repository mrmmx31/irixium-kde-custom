# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt5/Qt6 gallery explanations; uses native tips without palette overrides."""


def _install_tooltip_positioner(widget_type):
    """Move native Qt tooltip windows outside their owning control."""
    from pathlib import Path
    import sys

    try:
        from tooltip_position import outside_control
    except ModuleNotFoundError as error:
        if error.name != 'tooltip_position':
            raise
        for parent in Path(__file__).resolve().parents:
            module_dir = parent / 'tools/theme-lab'
            if (module_dir / 'tooltip_position.py').is_file():
                sys.path.insert(0, str(module_dir))
                break
        from tooltip_position import outside_control

    if widget_type.__module__.startswith('PyQt6'):
        from PyQt6.QtCore import QEvent, QObject, QPoint, QTimer
        from PyQt6.QtWidgets import QApplication, QToolTip
    else:
        from PyQt5.QtCore import QEvent, QObject, QPoint, QTimer
        from PyQt5.QtWidgets import QApplication, QToolTip

    app = QApplication.instance()
    if getattr(app, '_domainos_tooltip_positioner', None):
        return

    class TooltipPositioner(QObject):
        tooltip_event = getattr(getattr(QEvent, 'Type', QEvent), 'ToolTip')
        mouse_move_event = getattr(getattr(QEvent, 'Type', QEvent), 'MouseMove')
        show_event = getattr(getattr(QEvent, 'Type', QEvent), 'Show')
        hide_event = getattr(getattr(QEvent, 'Type', QEvent), 'Hide')

        def __init__(self):
            super().__init__(app)
            self.owner_rect = None
            self.owner_screen = None
            self.owner_widget = None
            self.position_timers = set()

        def remember_owner(self, widget):
            area = widget.frameGeometry()
            self.owner_widget = widget
            self.owner_rect = (area.x(), area.y(), area.width(), area.height())
            self.owner_screen = QApplication.screenAt(area.center())

        def position_tip(self, tip, owner_rect, owner_screen, attempt=0):
            if not tip.isVisible():
                if attempt < 10:
                    self.schedule_position(tip, owner_rect, owner_screen, attempt + 1)
                return
            tip_rect = tip.frameGeometry()
            if (tip_rect.width() <= 0 or tip_rect.height() <= 0) and attempt < 3:
                self.schedule_position(tip, owner_rect, owner_screen, attempt + 1)
                return
            if tip_rect.width() <= 0 or tip_rect.height() <= 0:
                return
            overlaps = not (tip_rect.right() < owner_rect[0] or
                            tip_rect.x() > owner_rect[0] + owner_rect[2] or
                            tip_rect.bottom() < owner_rect[1] or
                            tip_rect.y() > owner_rect[1] + owner_rect[3])
            if not overlaps:
                return
            screen = owner_screen or QApplication.primaryScreen()
            if screen is None:
                QToolTip.hideText()
                return
            position = outside_control(owner_rect,
                                       (tip_rect.width(), tip_rect.height()),
                                       screen.availableGeometry().getRect())
            if position is None:
                QToolTip.hideText()
            else:
                tip.move(*position)

        def schedule_position(self, tip, owner_rect, owner_screen, attempt):
            timer = QTimer(self)
            timer.setSingleShot(True)
            self.position_timers.add(timer)

            def reposition():
                try:
                    self.position_tip(tip, owner_rect, owner_screen, attempt)
                finally:
                    self.position_timers.discard(timer)
                    timer.deleteLater()

            timer.timeout.connect(reposition)
            timer.start(0)

        def eventFilter(self, watched, event):
            is_menu = hasattr(watched, 'inherits') and watched.inherits('QMenu')
            if is_menu:
                if event.type() == self.show_event:
                    # QMenu tooltips are raised by Qt's menu controller; its
                    # ToolTip event is not consistently sent through the
                    # application event filter. Track the actual menu surface
                    # on show/motion so the later QTipLabel can avoid every row.
                    self.remember_owner(watched)
                elif event.type() == self.mouse_move_event:
                    point = (event.position().toPoint() if hasattr(event, 'position')
                             else event.pos())
                    action = watched.actionAt(point)
                    if action is not None and action.toolTip():
                        self.remember_owner(watched)
                elif event.type() == self.hide_event and self.owner_widget is watched:
                    self.owner_widget = None
                    self.owner_rect = None
                    self.owner_screen = None
                elif event.type() == self.tooltip_event:
                    action = watched.activeAction()
                    if action and action.toolTip():
                        self.remember_owner(watched)
            elif event.type() == self.tooltip_event and isinstance(watched, widget_type) and watched.toolTip():
                origin = watched.mapToGlobal(QPoint(0, 0))
                self.owner_widget = watched
                self.owner_rect = (origin.x(), origin.y(), watched.width(), watched.height())
                self.owner_screen = QApplication.screenAt(
                    watched.mapToGlobal(QPoint(watched.width() // 2, watched.height() // 2)))
            elif (event.type() == self.show_event and
                  hasattr(watched, 'inherits') and watched.inherits('QTipLabel') and
                  self.owner_rect):
                owner_rect = self.owner_rect
                owner_screen = self.owner_screen
                self.owner_widget = None
                self.owner_rect = None
                self.owner_screen = None
                # At the QTipLabel Show event, Qt has assigned its final size
                # and default position but has not painted the first frame yet.
                # Move synchronously so a menu hint never flashes over a row.
                self.position_tip(watched, owner_rect, owner_screen)
            return False

    positioner = TooltipPositioner()
    app.installEventFilter(positioner)
    app._domainos_tooltip_positioner = positioner


def _install_submenu_help_strip(window, status_widget):
    """Use the gallery's status line for delayed submenu-parent help.

    Qt can close the parent QMenu surface while opening its child menu, which
    prevents the ordinary QAction tooltip from being painted reliably. The
    help text stays in the gallery window instead of following the pointer.
    """
    if getattr(window, '_domainos_submenu_help_strip', None):
        return
    if status_widget is None:
        return
    if window.__class__.__module__.startswith('PyQt6'):
        from PyQt6.QtCore import QEvent, QObject, QTimer
        from PyQt6.QtGui import QCursor
        from PyQt6.QtWidgets import QApplication, QToolTip
    else:
        from PyQt5.QtCore import QEvent, QObject, QTimer
        from PyQt5.QtGui import QCursor
        from PyQt5.QtWidgets import QApplication, QToolTip

    event_types = getattr(QEvent, 'Type', QEvent)
    mouse_move = event_types.MouseMove
    tooltip_event = event_types.ToolTip
    leave_event = event_types.Leave
    hide_event = event_types.Hide
    app = QApplication.instance()

    class SubmenuHelpStrip(QObject):
        def __init__(self):
            super().__init__(window)
            self.pending_owner = None
            self.pending_action = None
            self.previous_text = None
            self.visible_text = None
            self.delay = QTimer(self)
            self.delay.setSingleShot(True)
            self.delay.setInterval(500)
            self.delay.timeout.connect(self.show_pending)
            self.expiry = QTimer(self)
            self.expiry.setSingleShot(True)
            self.expiry.setInterval(2400)
            self.expiry.timeout.connect(self.restore_status)

        def eventFilter(self, watched, event):
            if not hasattr(watched, 'inherits') or not watched.inherits('QMenu'):
                return False
            if event.type() == mouse_move:
                point = (event.position().toPoint() if hasattr(event, 'position')
                         else event.pos())
                action = watched.actionAt(point)
                if action is not None and action.menu() is not None:
                    self.schedule(watched, action)
                else:
                    self.cancel_pending()
            elif event.type() == tooltip_event:
                point = watched.mapFromGlobal(QCursor.pos())
                action = watched.actionAt(point) or watched.activeAction()
                if action is not None and action.menu() is not None:
                    QToolTip.hideText()
                    return True
            elif event.type() in (leave_event, hide_event):
                if not self.submenu_visible():
                    self.cancel_pending()
            return False

        def schedule(self, owner, action):
            if self.pending_owner is owner and self.pending_action is action:
                return
            self.cancel_pending()
            self.pending_owner, self.pending_action = owner, action
            self.delay.start()

        def submenu_visible(self):
            action = self.pending_action
            child = action.menu() if action is not None else None
            return child is not None and child.isVisible()

        def show_pending(self):
            owner, action = self.pending_owner, self.pending_action
            if owner is None or action is None or not owner.isVisible():
                return
            point = owner.mapFromGlobal(QCursor.pos())
            still_over = owner.actionAt(point) is action
            if not still_over and not self.submenu_visible():
                self.cancel_pending()
                return
            text = action.statusTip() or action.toolTip()
            if not text:
                return
            self.restore_status()
            self.previous_text = status_widget.text()
            self.visible_text = text
            status_widget.setText(text)
            self.expiry.start()

        def restore_status(self):
            self.expiry.stop()
            if (self.visible_text is not None and
                    status_widget.text() == self.visible_text and
                    self.previous_text is not None):
                status_widget.setText(self.previous_text)
            self.visible_text = None
            self.previous_text = None

        def cancel_pending(self):
            self.delay.stop()
            self.pending_owner = None
            self.pending_action = None
            self.restore_status()

    helper = SubmenuHelpStrip()
    app.installEventFilter(helper)
    window._domainos_submenu_help_strip = helper


def widget_hint(widget):
    if widget.inherits('QAbstractSpinBox'):
        return ('Valor da amostra, sem unidade: mínimo %s, máximo %s, passo %s. '
                'Use as setas ou edite o campo; isso não modifica medidas do tema em px.' %
                (widget.minimum(), widget.maximum(), widget.singleStep()))
    if widget.inherits('QScrollBar'):
        axis = 'horizontal' if int(widget.orientation().value if hasattr(widget.orientation(), 'value')
                                   else widget.orientation()) == 1 else 'vertical'
        return 'Barra %s: setas, trilho e cursor deslocam o conteúdo nativo da amostra.' % axis
    if widget.inherits('QSlider'):
        return ('Escala da amostra, sem unidade: de %s a %s, passo %s. '
                'Arraste o cursor; o indicador de progresso acompanha este valor.' %
                (widget.minimum(), widget.maximum(), widget.singleStep()))
    if widget.inherits('QProgressBar'):
        return 'Indicador do valor da escala na amostra; não mede uma tarefa em execução.'
    if widget.inherits('QComboBox'):
        return 'Abra a lista e escolha uma opção da amostra; isso não troca o tema do desktop.'
    if widget.inherits('QRadioButton'):
        return 'Opção exclusiva do grupo nativo. Clique para observar seleção e relevo.'
    if widget.inherits('QCheckBox'):
        return 'Escolha independente da amostra: marque ou desmarque para observar o estado nativo.'
    if widget.inherits('QAbstractButton'):
        if widget.isCheckable():
            return 'Botão alternável: clique para ligar ou desligar o estado da amostra.'
        return 'Botão nativo da amostra: mantenha pressionado para observar o relevo e solte para acionar.'
    if widget.inherits('QLineEdit'):
        parent=widget.parentWidget()
        if parent and parent.inherits('QAbstractSpinBox'):
            return widget_hint(parent)
        return 'Entrada de uma linha: selecione ou edite o texto da amostra; Undo/Redo e clipboard são nativos.'
    if widget.inherits('QTextEdit') or widget.inherits('QPlainTextEdit'):
        return 'Editor de várias linhas: selecione, edite e role o texto; Undo/Redo e clipboard são nativos.'
    if widget.inherits('QHeaderView'):
        return 'Cabeçalho nativo: clique para ordenar quando habilitado; arraste a divisória para ajustar a coluna.'
    if widget.inherits('QAbstractItemView'):
        return 'Tabela/lista nativa: selecione itens, edite células permitidas e use as barras para percorrer o conteúdo.'
    if widget.inherits('QTabBar'):
        return 'Escolha a página de controles da amostra; as páginas mantêm seus valores.'
    if widget.inherits('QTabWidget'):
        return 'Abas de controles nativos: escolha uma página; seus valores permanecem independentes.'
    if widget.inherits('QScrollArea'):
        return 'Conteúdo rolável nativo: percorra os botões usando as barras sem alterar o layout do tema.'
    return None


def add_gallery_hints(window, widget_type, action_type, status_widget=None):
    _install_tooltip_positioner(widget_type)
    count=0
    for widget in window.findChildren(widget_type):
        if widget.inherits('QMenu'):
            widget.setToolTipsVisible(True)
        text=widget_hint(widget)
        if text:
            if not widget.toolTip(): widget.setToolTip(text)
            count+=1
    actions=window.findChildren(action_type)
    for action in actions:
        if action.isSeparator(): continue
        if not action.toolTip() or action.toolTip()==action.text().replace('&',''):
            action.setToolTip('Ação do menu nativo da amostra: '+action.text().replace('&','')+'.')
        if action.menu() is not None and not action.statusTip():
            action.setStatusTip(action.toolTip())
    if status_widget is not None:
        _install_submenu_help_strip(window, status_widget)
    return {'widgets':count,'actions':sum(not a.isSeparator() for a in actions),
            'submenu_help_strip':status_widget is not None,
            'scope':'native Qt hints assigned; timing/geometry and theme translation need separate proof'}


def add_dialog_hints(dialog, widget_type, action_type):
    coverage=add_gallery_hints(dialog,widget_type,action_type)
    file_dialog=dialog.inherits('QFileDialog')
    names={
        'fileNameEdit':'Nome do arquivo no ambiente privado: digite ou selecione um arquivo existente. A galeria registra apenas o resultado, sem ler seu conteúdo.',
        'fileTypeCombo':'Filtro de tipos de arquivo: limita a lista visível; não altera os arquivos.',
        'lookInCombo':'Pasta atual do ambiente privado: escolha onde procurar o arquivo.',
        'backButton':'Volta à pasta anterior no histórico deste seletor privado.',
        'forwardButton':'Avança no histórico de pastas deste seletor privado.',
        'toParentButton':'Mostra a pasta acima da pasta atual no ambiente privado.',
        'listModeButton':'Apresenta os arquivos em lista neste seletor.',
        'detailModeButton':'Apresenta os arquivos com detalhes neste seletor.',
        'newFolderButton':'Cria uma pasta no ambiente privado; não modifica o perfil pessoal.',
    }
    for widget in dialog.findChildren(widget_type):
        if file_dialog and widget.objectName() in names:
            widget.setToolTip(names[widget.objectName()])
        if widget.inherits('QDialogButtonBox'):
            for button in widget.buttons():
                role=widget.buttonRole(button)
                value=role.value if hasattr(role,'value') else int(role)
                if value==0:
                    button.setToolTip('Confirma a seleção do arquivo privado; a galeria não abre nem modifica seu conteúdo.'
                                      if file_dialog else 'Fecha esta explicação e retorna à galeria, sem modificar o tema.')
                elif value==1:
                    button.setToolTip('Cancela este seletor e retorna à galeria sem selecionar um arquivo.')
    return coverage
