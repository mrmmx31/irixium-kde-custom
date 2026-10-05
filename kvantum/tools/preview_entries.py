#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Qt Widgets input gallery. Temporary theme selection; no session writes."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true');p.add_argument('--capturas',type=Path)
    p.add_argument('--fonte-px',type=int,default=14);a=p.parse_args(argv)
    if not 10<=a.fonte_px<=28:p.error('Fonte entre 10 e 28 pixels.')
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:print('Qt 6 ausente; galeria/testes nativos não executados.',file=sys.stderr);return 77
    source=Path(__file__).resolve().parents[1]/'IrixClassic'
    with tempfile.TemporaryDirectory(prefix='irixclassic-entries-') as tmp:
        config=Path(tmp);dest=config/'Kvantum/IrixClassic';dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(source/('IrixClassic.'+ext),dest/('IrixClassic.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
        os.environ['XDG_CONFIG_HOME']=str(config);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        if a.testar or a.capturas:os.environ['QT_QPA_PLATFORM']='offscreen'
        if binding=='PyQt6':from PyQt6 import QtWidgets as W,QtCore as C,QtGui as G,QtTest as T
        else:from PySide6 import QtWidgets as W,QtCore as C,QtGui as G,QtTest as T
        app=W.QApplication([sys.argv[0]]);style=W.QStyleFactory.create('kvantum')
        if style is None:print('Plugin Kvantum Qt 6 ausente; sem substituição por Fusion.',file=sys.stderr);return 77
        app.setStyle(style);font=G.QFont('Nimbus Sans');font.setPixelSize(a.fonte_px);app.setFont(font)
        win=W.QWidget();win.setWindowTitle('IrixClassic 0.3.0-rc1 — campos e entradas')
        layout=W.QVBoxLayout(win);layout.addWidget(W.QLabel('Configuração temporária. Compare Tab, seleção de texto, limites e relevo.'))
        form=W.QFormLayout();layout.addLayout(form)
        editable=W.QLineEdit('Texto editável');form.addRow('Editável:',editable)
        readonly=W.QLineEdit('Somente leitura: texto selecionável');readonly.setReadOnly(True);form.addRow('Somente leitura:',readonly)
        unavailable=W.QLineEdit('Indisponível');unavailable.setEnabled(False);form.addRow('Desativado:',unavailable)
        password=W.QLineEdit('example');password.setEchoMode(W.QLineEdit.EchoMode.Password);form.addRow('Senha:',password)
        option=W.QComboBox();option.addItems(['Original','Alternativa','Terceira opção']);form.addRow('Opção:',option)
        combo=W.QComboBox();combo.setEditable(True);combo.addItems(['Entrada livre','Outro valor']);form.addRow('Combo editável:',combo)
        disabled=W.QComboBox();disabled.addItem('Opção indisponível');disabled.setEnabled(False);form.addRow('Combo desativado:',disabled)
        spin=W.QSpinBox();spin.setRange(-5,5);spin.setValue(0);form.addRow('Inteiro (-5…5):',spin)
        real=W.QDoubleSpinBox();real.setRange(-2,2);real.setDecimals(2);real.setSingleStep(.25);form.addRow('Decimal:',real)
        date=W.QDateEdit();date.setDate(C.QDate(2026,10,5));form.addRow('Data:',date)
        no_buttons=W.QSpinBox();no_buttons.setButtonSymbols(W.QAbstractSpinBox.ButtonSymbols.NoButtons);form.addRow('Sem setas:',no_buttons)
        rtl=W.QComboBox();rtl.addItems(['Direção RTL','Outra opção']);rtl.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft);form.addRow('Espelhado:',rtl)
        panel=W.QFrame();panel.setFrameShape(W.QFrame.Shape.StyledPanel);panel.setFrameShadow(W.QFrame.Shadow.Sunken)
        W.QVBoxLayout(panel).addWidget(W.QLabel('Moldura interna rebaixada. O aplicativo continua dono do conteúdo.'));layout.addWidget(panel)
        layout.addWidget(W.QLabel('Somente leitura não é desativado: permanece selecionável.\nA cor própria desse estado depende do aplicativo; não há estado readonly no SVG do Kvantum.'))
        win.resize(640,590);win.show();app.processEvents();T.QTest.qWait(50)
        folder=a.capturas.expanduser().absolute() if a.capturas else None
        if folder:folder.mkdir(parents=True,exist_ok=True)
        report={'qt':C.qVersion(),'binding':binding,'style':style.metaObject().className(),'theme':'IrixClassic','checks':[]}
        def require(ok,label):
            if not ok:raise RuntimeError(label)
            report['checks'].append(label)
        def shot(name):
            app.processEvents();T.QTest.qWait(25)
            if folder and not win.grab().save(str(folder/(name+'.png'))):raise RuntimeError('Falha no PNG.')
        shot('01-campos')
        if not(a.testar or a.capturas):return app.exec()
        editable.setFocus();editable.selectAll();T.QTest.keyClicks(editable,'IRIX');require(editable.text()=='IRIX','Edição de texto funciona');shot('02-foco')
        readonly.setFocus();readonly.selectAll();before=readonly.text();T.QTest.keyClicks(readonly,'X')
        require(readonly.text()==before,'Somente leitura bloqueia edição');readonly.selectAll();require(readonly.selectedText()==before,'Somente leitura permite seleção')
        require(not unavailable.isEnabled(),'Campo indisponível permanece desativado')
        option.setFocus();T.QTest.keyClick(option,C.Qt.Key.Key_Down);require(option.currentIndex()==1,'Combo altera seleção pelo teclado')
        combo.lineEdit().selectAll();T.QTest.keyClicks(combo.lineEdit(),'Novo valor');require(combo.currentText()=='Novo valor','Combo editável aceita texto')
        spin.setValue(5);spin.stepUp();require(spin.value()==5,'Limite superior respeitado');spin.setValue(-5);spin.stepDown();require(spin.value()==-5,'Limite mínimo respeitado')
        spin.setReadOnly(True);require(spin.isReadOnly(),'Spinbox somente leitura');spin.setReadOnly(False)
        real.stepUp();require(abs(real.value()-.25)<.00001,'Passo decimal preservado')
        require(date.date()==C.QDate(2026,10,5),'Conteúdo de data preservado')
        require(rtl.layoutDirection()==C.Qt.LayoutDirection.RightToLeft,'Direção RTL preservada')
        shot('03-validacao');print(json.dumps(report,indent=2,ensure_ascii=False))
        if folder:(folder/'RESULTADO-CAMPOS-QT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        return 0
if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as exc:print('Dependência Qt ausente:',exc,file=sys.stderr);sys.exit(77)
    except (OSError,ValueError,RuntimeError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
