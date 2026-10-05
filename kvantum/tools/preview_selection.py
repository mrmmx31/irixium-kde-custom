#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 4 gallery. Uses the real Kvantum QStyle with temporary configuration."""
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
ROOT=Path(__file__).resolve().parents[1]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true');p.add_argument('--fonte-px',type=int,default=14)
    p.add_argument('--tema',choices=('IrixClassic','Irixium'),default='IrixClassic')
    a=p.parse_args(argv)
    if not 10<=a.fonte_px<=28:p.error('--fonte-px deve estar entre 10 e 28.')
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:
        print('SKIP: PyQt6/PySide6 ausente. Galeria Qt não executada.',file=sys.stderr);return 77
    try:
        C=importlib.import_module(binding+'.QtCore');G=importlib.import_module(binding+'.QtGui')
        W=importlib.import_module(binding+'.QtWidgets');T=importlib.import_module(binding+'.QtTest')
    except ImportError as e:
        print('SKIP: dependência Qt ausente:',e,file=sys.stderr);return 77
    with tempfile.TemporaryDirectory(prefix='irix-selection-') as tmp:
        base=Path(tmp);dst=base/'Kvantum'/a.tema;dst.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(ROOT/a.tema/(a.tema+'.'+ext),dst/(a.tema+'.'+ext))
        (base/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme='+a.tema+'\n')
        os.environ['XDG_CONFIG_HOME']=str(base);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        app=W.QApplication(['irix-selection-gallery']);style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('SKIP: plugin Kvantum para este Qt ausente. Disponíveis:',W.QStyleFactory.keys(),file=sys.stderr);return 77
        app.setStyle(style);font=G.QFont('Nimbus Sans');font.setPixelSize(a.fonte_px);app.setFont(font)
        win=W.QMainWindow();win.setWindowTitle('IrixClassic — seleção / '+a.tema)
        central=W.QWidget();win.setCentralWidget(central);lay=W.QVBoxLayout(central)
        notice=W.QLabel('Marcação vermelha: opções independentes. Triângulo azul: opções exclusivas.\n'
            'Tab e Espaço testam o teclado. Pressão não é um estado SVG independente no Kvantum 1.1.4.')
        notice.setWordWrap(True);lay.addWidget(notice)
        groups=W.QHBoxLayout();lay.addLayout(groups)
        gb=W.QGroupBox('Caixas de seleção');box=W.QVBoxLayout(gb);groups.addWidget(gb)
        controls={}
        for key,text,checked in (('off','Desmarcado',False),('on','Marcado',True),('disabled','Indisponível marcado',True)):
            w=W.QCheckBox(text);w.setChecked(checked);box.addWidget(w);controls[key]=w
            if key=='disabled':w.setEnabled(False)
        mixed=W.QCheckBox('Estado parcial / três estados');mixed.setTristate(True)
        mixed.setCheckState(C.Qt.CheckState.PartiallyChecked);box.addWidget(mixed);controls['mixed']=mixed
        rb=W.QGroupBox('Escolha exclusiva');radios=W.QVBoxLayout(rb);groups.addWidget(rb)
        exclusive=W.QButtonGroup(win);exclusive.setExclusive(True)
        for i,text in enumerate(('Arquivo','Tela','Impressora indisponível')):
            w=W.QRadioButton(text);radios.addWidget(w);exclusive.addButton(w,i);controls['radio'+str(i)]=w
            w.setEnabled(i!=2);w.setChecked(i==0)
        tree=W.QTreeWidget();tree.setHeaderLabels(['Itens com marcação','Estado'])
        for i,state in enumerate((C.Qt.CheckState.Unchecked,C.Qt.CheckState.Checked,C.Qt.CheckState.PartiallyChecked)):
            it=W.QTreeWidgetItem(['Item artificial '+str(i+1),str(state.name)]);it.setFlags(it.flags()|C.Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(0,state);tree.addTopLevelItem(it)
        tree.setMaximumHeight(150);lay.addWidget(tree)
        menu=win.menuBar().addMenu('Seleção')
        toggle=menu.addAction('Opção independente');toggle.setCheckable(True);toggle.setChecked(True)
        menu.addSeparator();actionGroup=G.QActionGroup(win);actionGroup.setExclusive(True)
        for i,t in enumerate(('Modo arquivo','Modo tela')):
            act=menu.addAction(t);act.setCheckable(True);act.setChecked(i==0);actionGroup.addAction(act)
        disabledAct=menu.addAction('Indisponível');disabledAct.setCheckable(True);disabledAct.setChecked(True);disabledAct.setEnabled(False)
        status=W.QLabel('Pronto para comparar mouse, teclado, marcação parcial e indisponibilidade.');status.setWordWrap(True);lay.addWidget(status)
        for name,w in controls.items():
            w.toggled.connect(lambda v,n=name:status.setText(n+': '+str(v)))
        rtl=W.QCheckBox('Espelhar a galeria (direita para esquerda)')
        rtl.toggled.connect(lambda v:central.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft if v else C.Qt.LayoutDirection.LeftToRight));lay.addWidget(rtl)
        win.resize(620,470);win.show();app.processEvents();T.QTest.qWait(150)
        if not a.testar:return app.exec()
        results=[]
        def check(name,value):
            results.append({'test':name,'passed':bool(value)})
        def click(w):T.QTest.mouseClick(w,C.Qt.MouseButton.LeftButton);app.processEvents()
        click(controls['off']);check('checkbox mouse toggles',controls['off'].isChecked())
        controls['off'].setFocus(C.Qt.FocusReason.TabFocusReason);app.processEvents()
        T.QTest.keyClick(controls['off'],C.Qt.Key.Key_Space);check('checkbox Space toggles',not controls['off'].isChecked())
        check('keyboard focus target',controls['off'].hasFocus())
        before=controls['disabled'].isChecked();click(controls['disabled']);check('disabled unchanged',controls['disabled'].isChecked()==before)
        values=[]
        for _ in range(3):click(mixed);values.append(mixed.checkState().value)
        check('three states cycle',len(set(values))==3)
        click(controls['radio1']);check('exclusive radio group',controls['radio1'].isChecked() and not controls['radio0'].isChecked())
        before=controls['radio2'].isChecked();click(controls['radio2']);check('disabled radio unchanged',controls['radio2'].isChecked()==before)
        # Real renderer probe; no proxy QStyle and no custom widget painting.
        for kind,widget,col,primitive in (
            ('check',controls['on'],(204,0,0),W.QStyle.PrimitiveElement.PE_IndicatorCheckBox),
            ('radio',controls['radio1'],(0,0,204),W.QStyle.PrimitiveElement.PE_IndicatorRadioButton)):
            option=W.QStyleOptionButton();option.initFrom(widget);option.rect=C.QRect(0,0,15,15)
            option.state=W.QStyle.StateFlag.State_Enabled|W.QStyle.StateFlag.State_On|W.QStyle.StateFlag.State_Active
            image=G.QImage(15,15,G.QImage.Format.Format_ARGB32);image.fill(C.Qt.GlobalColor.transparent)
            painter=G.QPainter(image);style.drawPrimitive(primitive,option,painter,widget);painter.end()
            check(kind+' mark reaches real renderer',any(image.pixelColor(x,y).getRgb()[:3]==col for y in range(15) for x in range(15)))
        actionGroup.actions()[1].trigger();check('menu radios exclusive',actionGroup.actions()[1].isChecked() and not actionGroup.actions()[0].isChecked())
        toggle.trigger();check('menu checkbox toggles',not toggle.isChecked())
        print(json.dumps({'qt':C.qVersion(),'style':style.metaObject().className(),'binding':binding,
                          'results':results,'note':'Native behavior only; not a historical pixel-equivalence claim.'},ensure_ascii=False,indent=2))
        win.close();app.processEvents();return 0 if all(t['passed'] for t in results) else 1
if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
