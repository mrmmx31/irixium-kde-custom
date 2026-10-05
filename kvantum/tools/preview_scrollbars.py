#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Interactive Qt 6 scrollbar gallery; only temporary Kvantum configuration."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tema', choices=('IrixClassic', 'Irixium'), default='IrixClassic')
    p.add_argument('--capturas', type=Path, help='Generate actual Qt PNGs, offscreen, then exit.')
    p.add_argument('--testar', action='store_true', help='Exercise native QScrollBar events offscreen.')
    args = p.parse_args(argv)
    binding = next((name for name in ('PyQt6', 'PySide6') if importlib.util.find_spec(name)), None)
    if binding is None:
        print('Qt 6 ausente: instale os bindings por seu fluxo habitual. Nenhuma dependência foi instalada.', file=sys.stderr)
        return 77
    source = Path(__file__).resolve().parent.parent / args.tema
    if not all((source / (args.tema + '.' + ext)).is_file() for ext in ('svg', 'kvconfig')):
        print('Tema não encontrado: ' + args.tema, file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix='irix-scrollbars-') as tmp:
        config = Path(tmp)
        dest = config / 'Kvantum' / args.tema
        dest.mkdir(parents=True)
        for ext in ('svg', 'kvconfig'):
            shutil.copyfile(source / (args.tema + '.' + ext), dest / (args.tema + '.' + ext))
        (config / 'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=' + args.tema + '\n')
        os.environ['XDG_CONFIG_HOME'] = str(config)
        os.environ['QT_STYLE_OVERRIDE'] = 'kvantum'
        if args.capturas or args.testar:
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        if binding == 'PyQt6':
            from PyQt6 import QtWidgets as W, QtCore as C, QtGui as G, QtTest as T
        else:
            from PySide6 import QtWidgets as W, QtCore as C, QtGui as G, QtTest as T
        app = W.QApplication([sys.argv[0]])
        app.setApplicationName('IrixScrollbarPreview')
        style = W.QStyleFactory.create('kvantum')
        if style is None:
            print('Kvantum Qt 6 ausente: não será usado Fusion como substituto.', file=sys.stderr)
            return 77
        app.setStyle(style)
        font = G.QFont('Nimbus Sans'); font.setPixelSize(14); app.setFont(font)

        class Bar(W.QScrollBar):
            def option(self):
                opt = W.QStyleOptionSlider(); self.initStyleOption(opt); return opt
            def subrect(self, sub):
                return self.style().subControlRect(W.QStyle.ComplexControl.CC_ScrollBar, self.option(), sub, self)

        window = W.QWidget(); window.setWindowTitle(args.tema + ' — barras de rolagem')
        layout = W.QVBoxLayout(window)
        layout.addWidget(W.QLabel('Galeria Qt real. A configuração da sessão e a decoração não são alteradas.'))
        grid = W.QGridLayout(); layout.addLayout(grid)
        specs = [('Normal',50,True,100,False), ('Limite inferior',0,True,100,False),
                 ('Limite superior',100,True,100,False), ('Desativada',50,False,100,False),
                 ('Sem intervalo',0,True,0,False), ('RTL',50,True,100,True)]
        bars = {}; horizontal = {}
        for col, (label, value, enabled, maximum, rtl) in enumerate(specs):
            grid.addWidget(W.QLabel(label), 0, col)
            bar = Bar(C.Qt.Orientation.Vertical)
            bar.setRange(0,maximum); bar.setPageStep(25); bar.setSingleStep(1); bar.setValue(value)
            bar.setEnabled(enabled); bar.setFocusPolicy(C.Qt.FocusPolicy.StrongFocus)
            bar.setMinimumHeight(210); bar.setFixedWidth(style.pixelMetric(W.QStyle.PixelMetric.PM_ScrollBarExtent))
            if rtl: bar.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft)
            grid.addWidget(bar,1,col,C.Qt.AlignmentFlag.AlignHCenter); bars[label]=bar
            row = W.QHBoxLayout(); row.addWidget(W.QLabel(label))
            h = Bar(C.Qt.Orientation.Horizontal)
            h.setRange(0,maximum); h.setPageStep(25); h.setSingleStep(1); h.setValue(value); h.setEnabled(enabled)
            if rtl: h.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft)
            row.addWidget(h); layout.addLayout(row); horizontal[label]=h
        value_label = W.QLabel('Valor: 50'); layout.addWidget(value_label)
        bars['Normal'].valueChanged.connect(lambda value: value_label.setText('Valor: '+str(value)))
        layout.addWidget(W.QLabel('Teste pressionar/segurar setas, arrastar puxador, clicar no trilho e usar o teclado.\n'
                                  'Sem intervalo segue o comportamento nativo Qt; não simula controles Motif exclusivos.'))
        window.resize(740,570); window.show(); app.processEvents(); T.QTest.qWait(60)
        sc = W.QStyle.SubControl
        subnames = {'menos':sc.SC_ScrollBarSubLine, 'mais':sc.SC_ScrollBarAddLine,
                    'puxador':sc.SC_ScrollBarSlider, 'trilho':sc.SC_ScrollBarGroove}
        data = {'qt':C.qVersion(), 'binding':binding, 'plugin':style.metaObject().className(),
                'theme':args.tema, 'device_pixel_ratio':window.devicePixelRatioF(),
                'extent':style.pixelMetric(W.QStyle.PixelMetric.PM_ScrollBarExtent), 'native_tests':[]}
        data['subcontrols'] = {name:{key:[r.x(),r.y(),r.width(),r.height()]
                                       for key,sub in subnames.items() for r in [bar.subrect(sub)]}
                               for name,bar in bars.items()}
        if args.capturas:
            args.capturas = args.capturas.expanduser().absolute()
            args.capturas.mkdir(parents=True, exist_ok=True)
        def capture(name):
            app.processEvents(); T.QTest.qWait(40)
            if args.capturas and not window.grab().save(str(args.capturas/(name+'.png')), 'PNG'):
                raise RuntimeError('Falha ao gravar PNG: '+name)
        capture('01-repouso')
        if args.capturas or args.testar:
            bar=bars['Normal']; bar.setValue(50)
            T.QTest.mouseMove(bar,bar.subrect(sc.SC_ScrollBarSlider).center())
            capture('02-ponteiro-no-puxador')
            T.QTest.mousePress(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,
                              bar.subrect(sc.SC_ScrollBarSubLine).center())
            capture('03-seta-pressionada')
            T.QTest.mouseRelease(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,
                                bar.subrect(sc.SC_ScrollBarSubLine).center())
            if not bar.value()<50: raise RuntimeError('Seta superior não reduziu o valor.')
            data['native_tests'].append('sub-line decrements')
            bar.setValue(50); T.QTest.mouseClick(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,
                                              bar.subrect(sc.SC_ScrollBarAddLine).center())
            if not bar.value()>50: raise RuntimeError('Seta inferior não aumentou o valor.')
            data['native_tests'].append('add-line increments')
            bar.setValue(50); center=bar.subrect(sc.SC_ScrollBarSlider).center()
            T.QTest.mousePress(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,center)
            capture('04-puxador-pressionado')
            T.QTest.mouseMove(bar,center+C.QPoint(0,25)); app.processEvents()
            T.QTest.mouseRelease(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,center+C.QPoint(0,25))
            if not bar.value()>50: raise RuntimeError('Arraste vertical não aumentou o valor.')
            data['native_tests'].append('vertical drag updates value')
            for label in ('Desativada','Sem intervalo'):
                target=bars[label]; old=target.value()
                T.QTest.mouseClick(target,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,
                                  target.subrect(sc.SC_ScrollBarAddLine).center())
                if target.value()!=old: raise RuntimeError('Controle indisponível mudou de valor.')
                data['native_tests'].append(label+' does not change value')
            for label in ('Normal','RTL'):
                target=horizontal[label];target.setValue(50)
                T.QTest.mouseClick(target,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,
                                  target.subrect(sc.SC_ScrollBarAddLine).center())
                if target.value()<=50: raise RuntimeError('Adição horizontal falhou: '+label)
                data['native_tests'].append('horizontal add-line '+label)
            bar.setValue(50); bar.setFocus(); T.QTest.keyClick(bar,C.Qt.Key.Key_Down)
            if bar.value()<=50: raise RuntimeError('Navegação por teclado falhou.')
            data['native_tests'].append('keyboard Down')
            capture('05-apos-testes')
            if args.capturas:
                (args.capturas/'METRICAS.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
            print(json.dumps(data,indent=2,ensure_ascii=False));return 0
        print(json.dumps(data,indent=2,ensure_ascii=False))
        return app.exec()


if __name__ == '__main__':
    try: sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print('ERRO:',exc,file=sys.stderr);sys.exit(1)
