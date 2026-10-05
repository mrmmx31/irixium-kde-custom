#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Qt 6/Kvantum gallery for block 2 and scrollbar pressure.

Uses a temporary config, never substitutes Fusion, never changes the session.
--testar/--capturas use the actual plugin offscreen, not a simulated renderer.
"""
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
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true')
    p.add_argument('--capturas',type=Path)
    p.add_argument('--fonte-px',type=int,default=14)
    args=p.parse_args(argv)
    if not 10<=args.fonte_px<=28:p.error('Use uma fonte entre 10 e 28 pixels.')
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:
        print('Qt 6 ausente. Nenhuma dependência foi instalada; teste nativo não executado.',file=sys.stderr);return 77
    theme=Path(__file__).resolve().parents[1]/'IrixClassic'
    for ext in ('svg','kvconfig'):
        if not (theme/('IrixClassic.'+ext)).is_file():
            print('Arquivos IrixClassic não encontrados.',file=sys.stderr);return 1
    with tempfile.TemporaryDirectory(prefix='irixclassic-buttons-') as tmp:
        conf=Path(tmp);dest=conf/'Kvantum/IrixClassic';dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(theme/('IrixClassic.'+ext),dest/('IrixClassic.'+ext))
        (conf/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
        os.environ['XDG_CONFIG_HOME']=str(conf);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        if args.testar or args.capturas:os.environ['QT_QPA_PLATFORM']='offscreen'
        if binding=='PyQt6':from PyQt6 import QtWidgets as W,QtCore as C,QtGui as G,QtTest as T
        else:from PySide6 import QtWidgets as W,QtCore as C,QtGui as G,QtTest as T
        app=W.QApplication([sys.argv[0]])
        style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('Kvantum Qt 6 ausente. Não foi usado outro estilo como substituto.',file=sys.stderr);return 77
        app.setStyle(style);f=G.QFont('Nimbus Sans');f.setPixelSize(args.fonte_px);app.setFont(f)
        win=W.QDialog();win.setWindowTitle('IrixClassic — pressão e botões — 0.2.0-rc1')
        layout=W.QVBoxLayout(win)
        layout.addWidget(W.QLabel('A configuração da sessão não muda. Segure o botão para observar o relevo.'))
        command=W.QPushButton('Comando');command.setAutoDefault(False)
        default=W.QPushButton('Padrão');default.setDefault(True)
        unavailable=W.QPushButton('Indisponível');unavailable.setEnabled(False)
        toggle=W.QPushButton('Alternância');toggle.setCheckable(True);toggle.setAutoDefault(False)
        buttons=[command,default,unavailable,toggle]
        row=W.QHBoxLayout()
        for b in buttons:row.addWidget(b)
        layout.addLayout(row)
        toolrow=W.QHBoxLayout();toolrow.addWidget(W.QLabel('Paleta:'))
        palette=W.QToolButton();palette.setText('Ferramenta');palette.setToolButtonStyle(C.Qt.ToolButtonStyle.ToolButtonTextOnly)
        pal_toggle=W.QToolButton();pal_toggle.setText('Selecionada');pal_toggle.setCheckable(True);pal_toggle.setChecked(True)
        menu_tool=W.QToolButton();menu_tool.setText('Ação / menu');menu_tool.setPopupMode(W.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        menu=W.QMenu(menu_tool);menu.addAction('Primeira ação');a=menu.addAction('Ação indisponível');a.setEnabled(False);menu_tool.setMenu(menu)
        for b in (palette,pal_toggle,menu_tool):toolrow.addWidget(b)
        layout.addLayout(toolrow)
        toolbar=W.QToolBar('Ferramentas');toolbar.addAction('Normal');toolbar.addAction('Desativada').setEnabled(False)
        ta=toolbar.addAction('Alternância');ta.setCheckable(True)
        layout.addWidget(toolbar)
        layout.addWidget(W.QLabel('As setas abaixo mantêm as medidas da rc2. O novo relevo aparece durante a pressão.'))
        class Bar(W.QScrollBar):
            def subrect(self,sub):
                opt=W.QStyleOptionSlider();self.initStyleOption(opt)
                return self.style().subControlRect(W.QStyle.ComplexControl.CC_ScrollBar,opt,sub,self)
        bars=[];scrollrow=W.QHBoxLayout()
        for enabled in (True,False):
            bar=Bar(C.Qt.Orientation.Vertical);bar.setRange(0,100);bar.setValue(50);bar.setPageStep(25)
            bar.setFixedSize(18,165);bar.setEnabled(enabled);scrollrow.addWidget(bar);bars.append(bar)
        hbar=Bar(C.Qt.Orientation.Horizontal);hbar.setRange(0,100);hbar.setValue(50);hbar.setPageStep(25)
        hbar.setMinimumWidth(220);scrollrow.addWidget(hbar);bars.append(hbar)
        scrollrow.addStretch();layout.addLayout(scrollrow)
        counts=[0,0,0,0];status=W.QLabel('Nenhuma ação disparada.');layout.addWidget(status)
        def action(i):
            counts[i]+=1;status.setText('Ações: '+str(counts))
        for i,b in enumerate(buttons):b.clicked.connect(lambda checked=False,i=i:action(i))
        layout.addWidget(W.QLabel('Teste Tab/Espaço/Enter, sair e voltar com o mouse pressionado, menus e controles desativados.\n'
                                  'Os efeitos do popup e autoRaise são os do aplicativo/Qt; nenhum temporizador prolonga o relevo.'))
        win.resize(720,390);win.show();app.processEvents();T.QTest.qWait(40)
        folder=args.capturas.expanduser().absolute() if args.capturas else None
        if folder:folder.mkdir(parents=True,exist_ok=True)
        report={'qt':C.qVersion(),'binding':binding,'style':style.metaObject().className(),
                'theme':'IrixClassic','dpr':win.devicePixelRatioF(),'native_checks':[]}
        def snap(name):
            app.processEvents();T.QTest.qWait(20)
            if folder and not win.grab().save(str(folder/(name+'.png'))):raise RuntimeError('Falha no PNG.')
        def require(condition,message):
            if not condition:raise RuntimeError(message)
            report['native_checks'].append(message)
        snap('01-repouso')
        if not(args.testar or args.capturas):return app.exec()
        left=C.Qt.MouseButton.LeftButton;nomod=C.Qt.KeyboardModifier.NoModifier
        for i,b in enumerate((command,default)):
            before=counts[i];T.QTest.mousePress(b,left,nomod,b.rect().center());snap('02-pressionado-'+str(i))
            require(b.isDown(),'Estado down do botão '+str(i))
            require(counts[i]==before,'Nenhum clique antes da soltura '+str(i))
            image=b.grab().toImage();dpr=b.devicePixelRatioF()
            if dpr==1:
                # Inner lower band must survive the default-button overlay.
                require(image.pixelColor(image.width()//2,image.height()-2).name()=='#e1e1e1',
                        'Relevo inferior visível, botão '+str(i))
            T.QTest.mouseRelease(b,left,nomod,b.rect().center());app.processEvents()
            require(counts[i]==before+1,'Uma ação na soltura '+str(i))
            require(not b.isDown(),'Retorno do relevo '+str(i))
        before=counts[2];T.QTest.mouseClick(unavailable,left,nomod,unavailable.rect().center())
        require(counts[2]==before,'Botão indisponível não dispara ação')
        T.QTest.mouseClick(toggle,left,nomod,toggle.rect().center());require(toggle.isChecked(),'Seleção persistente')
        snap('03-selecionado')
        command.setFocus();before=counts[0]
        T.QTest.keyPress(command,C.Qt.Key.Key_Space);snap('04-espaco-pressionado')
        require(command.isDown(),'Pressão com Espaço')
        T.QTest.keyRelease(command,C.Qt.Key.Key_Space);require(counts[0]==before+1,'Soltura do Espaço dispara uma ação')
        sc=W.QStyle.SubControl
        for index,bar in enumerate((bars[0],bars[2])):
            for sub,label in ((sc.SC_ScrollBarSubLine,'menos'),(sc.SC_ScrollBarAddLine,'mais')):
                bar.setValue(50);point=bar.subrect(sub).center()
                T.QTest.mousePress(bar,left,nomod,point);snap('05-seta-'+str(index)+'-'+label)
                image=bar.grab().toImage();r=bar.subrect(sub)
                if index==0 and label=='menos' and bar.devicePixelRatioF()==1 and r.size()==C.QSize(18,18):
                    require(image.pixelColor(r.x()+10,r.y()+13).name()=='#e1e1e1','Lábio inferior da seta em pressão')
                T.QTest.mouseRelease(bar,left,nomod,point)
                require(bar.value()<50 if label=='menos' else bar.value()>50,'Ação da seta '+str(index)+' '+label)
        snap('06-fim')
        if folder:(folder/'RESULTADO-QT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps(report,indent=2,ensure_ascii=False));return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,RuntimeError) as exc:
        print('ERRO:',exc,file=sys.stderr);sys.exit(1)
