# Revisão integrada r2 — entrada dos ensaios

Manutenção: `mrmmx31`. A aparência continua 0.7.0-rc1, sem alterações no SVG,
kvconfig, manifesto do tema, instalação, decorações ou reparo compartilhado.

## Dados recebidos

A rodada de 05/10/2026 usou Qt 6.8.2, PyQt6, Kvantum::Style e Wayland nos
ensaios de sessão. Os blocos 1–3 explicitamente usam offscreen. A suíte estática
registrou 282 casos, dos quais 7 foram ignorados por ausência de CairoSVG/Pillow:
275 aprovados, não 282. A suíte de instalação registrou 42 aprovados. As galerias
nativas 1, 2, 3, 6, 7 e integrada passaram. Seleção e menus registraram três
falhas cada e permanecem em reteste.

Nas setas, todos os quatro alvos são válidos. Widgets: movimento e pixels mudam
em 4/4. Quick instalado e arquivo direto: movimento 4/4, sunken/pixels falham
4/4. Cópia corrigida: movimento, sunken pressionado, limpeza na soltura e pixels
corretos em 4/4. Isso valida os cliques sintéticos testados na cópia temporária;
não instala o reparo nem certifica arraste, repetição longa ou todos os aplicativos.

## Alterações no executor

- Checkbox/radio: obter indicador e área clicável do QStyle; não usar o centro
  de um widget esticado pelo layout. O teste Espaço compara com seu próprio
  estado anterior, sem depender de aprovação do clique anterior.
- Menu: movimentos, pressão e soltura pela sobrecarga QWindow do QTest. Uma
  aproximação dentro da ação produz eventos reais no processo de ensaio, em vez
  de depender de QCursor::setPos. O alvo é conferido por actionAt.
- Os observadores registram coordenadas, eventos e sinais, sempre retornando
  False: não aceitam/consomem a entrada e não impõem estado gráfico.
- O sumário distingue skip de aprovação e exibe os quatro caminhos das setas,
  evitando esconder o êxito temporário atrás da falha do módulo instalado.

Não se adiciona setChecked, QAction.trigger ou setActiveAction aos caminhos de
clique para forçar um teste a passar. As verificações de teclado/lógica já
existentes permanecem separadas. A confirmação local da r2 ainda é necessária.

## Executar

Na raiz do clone, depois do merge desta revisão:

```sh
bash kvantum/prever-selecao.sh --testar
bash kvantum/prever-menus.sh --testar
```

Para o reparo compartilhado já incluído anteriormente, em operação separada:

```sh
bash kvantum/corrigir-pressao-qtquick.sh --verificar --diff
bash kvantum/corrigir-pressao-qtquick.sh
```

Sem sudo na frente; o utilitário solicita autorização quando necessário.
Leia o diff. Afeta org.kde.desktop para os estilos que usam esse módulo.
Feche completamente e reabra as aplicações KDE para recarregar o código.
A atualização do pacote do sistema pode substituir os arquivos reparados;
não reaplicar cegamente a uma versão diferente. Reversão independente:

```sh
bash kvantum/corrigir-pressao-qtquick.sh --restaurar
```

Nova coleta completa, em pasta nova/vazia:

```sh
bash kvantum/revisar-integracao.sh --nativos --comparar-setas \
  --saida "$HOME/Downloads/revisao-irix-integrada-r2"
```

Não é necessário reinstalar o tema. Este executor não instala o reparo.

## Base técnica externa (distinta dos resultados recebidos)

Qt 6.8.2, `qtestmouse.h`, MouseMove(QWidget): usa QCursor::setPos sem botão
pressionado. Qt 6.8.2, `qcheckbox.cpp`, hitButton: consulta SE_CheckBoxClickRect.
Qt 6.8.2, `qmenu.cpp`, mousePressEvent/mouseReleaseEvent: hasMouseMoved participa
da aceitação da ação. Esses contratos explicam riscos no ensaio antigo; não
constituem prova isolada da causa de cada falha no desktop do usuário.

Fontes:
- https://github.com/qt/qtbase/blob/v6.8.2/src/testlib/qtestmouse.h
- https://github.com/qt/qtbase/blob/v6.8.2/src/widgets/widgets/qcheckbox.cpp
- https://github.com/qt/qtbase/blob/v6.8.2/src/widgets/widgets/qmenu.cpp
