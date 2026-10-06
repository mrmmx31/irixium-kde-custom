#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual Qt/Kvantum finishing gallery. No desktop configuration changes."""
from __future__ import annotations
import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from gallery_report import GalleryReport
from arrow_runtime import make_private_folder
ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar', action='store_true')
    p.add_argument('--fonte-px', type=int, default=14)
    p.add_argument('--resultado', type=Path)
    p.add_argument('--capturas', type=Path, help='Somente as janelas e controles artificiais desta galeria.')
    p.add_argument('--offscreen', action='store_true')
    a = p.parse_args(argv)
    if not 10 <= a.fonte_px <= 28: p.error('Fonte entre 10 e 28 pixels.')
    if a.resultado and not a.testar: p.error('--resultado exige --testar.')
    binding = next((n for n in ('PyQt6','PySide6') if importlib.util.find_spec(n)), None)
    if not binding:
        print('SKIP: PyQt6/PySide6 ausente; galeria não executada.', file=sys.stderr); return 77
    captures=make_private_folder(a.capturas) if a.capturas else None
    with tempfile.TemporaryDirectory(prefix='irix-finishing-') as tmp:
        cfg = Path(tmp); dst = cfg/'Kvantum/IrixClassic'; dst.mkdir(parents=True)
        for ext in ('svg','kvconfig'):
            shutil.copyfile(ROOT/'IrixClassic'/('IrixClassic.'+ext), dst/('IrixClassic.'+ext))
        (cfg/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
        os.environ['XDG_CONFIG_HOME']=str(cfg); os.environ['QT_STYLE_OVERRIDE']='kvantum'
        if a.offscreen: os.environ['QT_QPA_PLATFORM']='offscreen'
        C=importlib.import_module(binding+'.QtCore'); G=importlib.import_module(binding+'.QtGui')
        W=importlib.import_module(binding+'.QtWidgets'); T=importlib.import_module(binding+'.QtTest')
        app=W.QApplication(['irix-finish']); style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('SKIP: plugin Kvantum ausente.', file=sys.stderr); return 77
        app.setStyle(style); font=G.QFont('Nimbus Sans'); font.setPixelSize(a.fonte_px); app.setFont(font)
        win=W.QMainWindow(); win.setWindowTitle('IrixClassic — acabamento 0.7.1')
        win.menuBar().setNativeMenuBar(False)
        win.menuBar().addMenu('&Arquivo').addAction('Exemplo sem efeito externo')
        win.menuBar().addMenu('&Opções').addAction('Teste de leitura')
        horizontal=W.QToolBar('Horizontal'); horizontal.setMovable(False)
        horizontal.addAction('Novo'); horizontal.addSeparator(); horizontal.addAction('Abrir')
        win.addToolBar(horizontal)
        vertical=W.QToolBar('Vertical'); vertical.setMovable(False)
        vertical.addAction('A'); vertical.addSeparator(); vertical.addAction('B')
        win.addToolBar(C.Qt.ToolBarArea.LeftToolBarArea, vertical)
        central=W.QWidget(); layout=W.QVBoxLayout(central); win.setCentralWidget(central)
        label=W.QLabel('Confira a divisória fina nas duas barras.\n'
            'Setas do campo numérico: repouso, pressão e extremos; scrollbar não foi alterada.')
        label.setWordWrap(True); layout.addWidget(label)
        spin=W.QSpinBox(); spin.setRange(0,9); spin.setValue(5); layout.addWidget(spin)
        negative=W.QSpinBox(); negative.setRange(-9,9); negative.setValue(-3); layout.addWidget(negative)
        disabled=W.QSpinBox(); disabled.setValue(4); disabled.setEnabled(False); layout.addWidget(disabled)
        readonly=W.QLineEdit('Somente leitura: limitação de cor mantida, não confundida com disabled.')
        readonly.setReadOnly(True); layout.addWidget(readonly)
        info=W.QLabel('Menu mantém as margens anteriores; a altura real é medida, não forçada.'); info.setWordWrap(True);layout.addWidget(info)
        layout.addStretch(); win.resize(650,360); win.show(); app.processEvents(); T.QTest.qWait(200)
        def capture(name, widget):
            if captures:
                path=captures/(name+'.png')
                if not widget.grab().save(str(path),'PNG'):
                    raise RuntimeError('Falha ao capturar somente a galeria de acabamento.')
                path.chmod(0o600)
        capture('01-acabamento',win)
        capture('02-toolbar-horizontal',horizontal)
        capture('03-toolbar-vertical',vertical)
        capture('04-spinbox-indisponivel',disabled)
        if not a.testar:
            if captures:
                win.close(); return 0
            return app.exec()
        report=GalleryReport({'theme':'IrixClassic','revision':'0.7.1','qt':C.qVersion(),
            'binding':binding,'platform':app.platformName(),'style_class':style.metaObject().className(),
            'font_pixel_size':a.fonte_px, 'captures_scope':'own artificial gallery only'},
            a.resultado or (captures/'RESULTADO-ACABAMENTO.json' if captures else None))
        done=False
        try:
            flag=W.QStyle.StateFlag; report.enter('toolbar_separator_renderer')
            extent=style.pixelMetric(W.QStyle.PixelMetric.PM_ToolBarSeparatorExtent,None,horizontal)
            report.check('toolbar separator allocation remains 10', extent==10)
            for horiz,bar in ((True,horizontal),(False,vertical)):
                width,height=(extent,28) if horiz else (28,extent)
                opt=W.QStyleOption(); opt.initFrom(bar); opt.rect=C.QRect(0,0,width,height)
                opt.state=flag.State_Enabled|flag.State_Active
                if horiz: opt.state |= flag.State_Horizontal
                image=G.QImage(width,height,G.QImage.Format.Format_ARGB32); image.fill(C.Qt.GlobalColor.transparent)
                painter=G.QPainter(image)
                try: style.drawPrimitive(W.QStyle.PrimitiveElement.PE_IndicatorToolBarSeparator,opt,painter,bar)
                finally:painter.end()
                pixels=[(x,y) for y in range(height) for x in range(width) if image.pixelColor(x,y).alpha()>0]
                minor={x if horiz else y for x,y in pixels}
                report.check(('horizontal' if horiz else 'vertical')+' toolbar has two painted separator columns',len(minor)==2)
            report.enter('spin_native_clicks')
            opt=W.QStyleOptionSpinBox(); opt.initFrom(spin); opt.frame=True
            opt.buttonSymbols=spin.buttonSymbols()
            opt.stepEnabled=W.QAbstractSpinBox.StepEnabledFlag.StepUpEnabled|W.QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
            window=win.windowHandle()
            if window is None or not T.QTest.qWaitForWindowExposed(window,2000):
                raise RuntimeError('Janela de teste não ficou exposta.')
            for sub,delta in ((W.QStyle.SubControl.SC_SpinBoxUp,1),(W.QStyle.SubControl.SC_SpinBoxDown,-1)):
                rect=style.subControlRect(W.QStyle.ComplexControl.CC_SpinBox,opt,sub,spin)
                if not rect.isValid():raise ValueError('Subcontrole numérico inválido.')
                point=spin.mapTo(win,rect.center()); before=spin.value()
                T.QTest.mousePress(window,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,point,20)
                try:
                    app.processEvents();T.QTest.qWait(30)
                    capture('05-spinbox-'+('mais' if delta>0 else 'menos')+'-pressionado',spin)
                finally:
                    T.QTest.mouseRelease(window,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,point,20)
                app.processEvents();capture('06-spinbox-'+('mais' if delta>0 else 'menos')+'-solto',spin)
                report.check('spin '+sub.name+' changes exactly one step',spin.value()==before+delta)
            report.enter('spin_glyph_renderer')
            for primitive,label in ((W.QStyle.PrimitiveElement.PE_IndicatorSpinUp,'up'),(W.QStyle.PrimitiveElement.PE_IndicatorSpinDown,'down')):
                opt=W.QStyleOptionSpinBox();opt.initFrom(spin);opt.frame=True;opt.rect=C.QRect(0,0,16,26)
                opt.buttonSymbols=spin.buttonSymbols();opt.stepEnabled=W.QAbstractSpinBox.StepEnabledFlag.StepUpEnabled|W.QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
                opt.state=flag.State_Enabled|flag.State_Active
                image=G.QImage(16,26,G.QImage.Format.Format_ARGB32);image.fill(C.Qt.GlobalColor.transparent)
                painter=G.QPainter(image)
                try:style.drawPrimitive(primitive,opt,painter,spin)
                finally:painter.end()
                dark=[(x,y) for y in range(26) for x in range(16) if image.pixelColor(x,y).name()=='#4c4c4c' and image.pixelColor(x,y).alpha()>0]
                report.check('spin '+label+' dark silhouette reaches renderer',len(dark)>=24)
            report.doc['metrics']={'menubar_height':win.menuBar().height(),
                'spinbox_height':spin.height(),'separator_extent':extent,'device_pixel_ratio':win.devicePixelRatioF()}
            done=True
        except (ValueError,RuntimeError,OSError) as exc: report.abort(exc)
        finally:
            code=report.finish(done);print(json.dumps(report.doc,ensure_ascii=False,indent=2));win.close();app.processEvents()
        return code

if __name__=='__main__':
    try: sys.exit(main())
    except ImportError as exc: print('SKIP:',exc,file=sys.stderr);sys.exit(77)
    except (ValueError,RuntimeError,OSError) as exc: print('ERRO:',exc,file=sys.stderr);sys.exit(1)
