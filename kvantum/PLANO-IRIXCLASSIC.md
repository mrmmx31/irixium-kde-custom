# Plano mestre — Kvantum IrixClassic

Manutenção: `mrmmx31`. Este arquivo é a referência de continuidade do trabalho.
Atualizar esta matriz em toda entrega. Não confundir tema Qt Widgets com decoração
Aurorae, tema GTK, estilo Plasma ou configuração de fontes.

## Estado da entrega

**0.4.0-rc1: bloco 4 implementado para teste; falha das setas ainda em investigação.**
Desenho da barra e botões aprovados pelo usuário; bloco 3 implementado em
0.3.0-rc1 sem confirmação de aceitação final. O relato de falha das setas em
outros Application Styles exige separar ação de rolagem e pressão visual.
Não alteramos os desenhos aprovados nem aplicamos reparos globais automaticamente.
Use `diagnosticar-setas.sh` para comparar Widgets/Quick e Fusion/Breeze/Kvantum.
Próximo desenvolvimento: **bloco 5 — menus**.
Blocos 3 e 4: aceitação em Qt/KDE pendente.
Não marcar fidelidade histórica ou runtime como aprovado por teste estático.

| Bloco | Conteúdo obrigatório | Estado | Próxima evidência |
|---|---|---|---|
| 1. Barras de rolagem | Setas ↑↓←→; trilho; puxador; ranhuras; estados; extremos; sem intervalo; horizontal/vertical/RTL | Desenho aprovado; ação/pressão ainda em investigação por falha em vários estilos | diagnosticar-setas.sh; comparar movimento e sunken em Widgets e Quick |
| 2. Botões | Push button; botão padrão; ferramenta; menu de ferramenta; normal/hover/pressionado/toggled/desativado; foco de teclado | Aprovado pelo usuário em 0.2.0-rc1; preservado nesta revisão | Galeria prever-botoes.sh; tecla Espaço, retorno do relevo, padrão com pressão, disabled e menus de ferramenta |
| 3. Campos e entradas | Line edit editável e somente leitura; combo editável e de opções; spin box; painéis/frames; caret; seleção; foco; desativado | Implementado para teste em 0.3.0-rc1; cor readonly universal exige suporte fora do SVG | Galeria prever-campos.sh; foco, seleção, limites, RTL; docs/CAMPOS.md |
| 4. Checkboxes e radios | Off/on/parcial; exclusividade; foco; locate highlight; disabled; variantes em menu/lista | Implementado em 0.4.0-rc1 para teste; pressão separada limitada pelo motor Kvantum | prever-selecao.sh; test_selection.py; docs/SELECAO.md |
| 5. Menus | Barra; popup; item normal/selecionado/pressionado/desativado; separadores; check/radio; submenu; navegação mouse/teclado; item indisponível | Pendente; não apagar indicação de seleção | SGI ch. 8 e CDE/Motif |
| 6. Abas | Ativa/inativa/hover/desativada; foco; encaixe no painel; orientações; abas estreitas; botão de fechar | Pendente; abas retangulares rc1 são adaptação, não comprovadas por screenshot | Localizar referência histórica equivalente ou manter adaptação explícita |
| 7. Sliders e demais controles | Scale/slider; progresso determinado/indeterminado; splitter; headers; listas/tabelas/árvores; seleção simples/múltipla; branches; tooltips; dock/toolbox; labels; size grip; MDI | Pendente; isolado da alteração da scrollbar | SGI ch. 7/9/10/11, métricas e limites reais do Qt/Kvantum |

## Matriz transversal obrigatória

Em cada controle aplicável: repouso, ponteiro sem clique, pressão, soltura dentro,
soltura fora, arraste, foco por teclado, seleção persistente, checked/partial,
indisponível, janela inativa, RTL, orientação, tamanho mínimo e escala. Não
confundir `focused` do SVG Kvantum (frequentemente hover) com foco de teclado.
Cada item deve receber status `referência`, `adaptado`, `Qt nativo`, `fora do tema`
ou `validado localmente` — nunca preencher uma lacuna com uma alegação histórica.

## Controles específicos e lacunas

LEDs, thumbwheels, dials e File Finder da SGI não têm correspondência universal
1:1 no Kvantum. Registrar o equivalente quando existir e não prometer introduzir
um novo widget só por meio do SVG. Avaliar QDial/MDI/fallbacks no bloco 7.

A scrollbar SGI guarda uma impressão da posição inicial durante arraste, aceita
Escape para desfazer o gesto e esconde só o puxador sem intervalo. Esses
comportamentos exigem estado/interação que o par `.kvconfig`/`.svg` não implementa.
Nesta etapa permanecem diferenças documentadas: não adicionar scripts globais ou
alterar aplicações silenciosamente para fingir a equivalência.

## Método e critério de conclusão

Para cada bloco: (1) referência visual/manual; (2) mapa para seções/IDs Kvantum;
(3) implementação isolada; (4) teste de preservação dos demais blocos;
(5) ZIP/patch para merge; (6) capturas/galeria interativa; (7) aceitação local.
A entrega de um ZIP é `implementado para teste`, não `validado localmente`.

## Regras de preservação

- Não editar `kvantum/Irixium/`, Aurorae, IRIX Classic da janela, GTK ou fontes.
- Antes de alterar uma seção herdada, conferir dependentes. No bloco 1, Slider,
  SliderCursor e Progressbar foram desvinculados da scrollbar sem mudar sua
  configuração efetiva anterior.
- Manter o nome IrixClassic, sem criar uma entrada para cada RC.
- Identificação pública apenas `mrmmx31`; preservar créditos/licenças de terceiros.
- Confirmar branch/commit antes de cada merge e recusar divergências nos alvos.

## Fontes-mestre

SGI, *Indigo Magic User Interface Guidelines*, 007-2167-003:
https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/index.html

Controles (inclui figuras para botões, opções, check/radio, LEDs, listas,
scrollbars, scales, File Finder, thumbwheels e dials):
https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch09.html

Kvantum 1.1.4, configuração e renderização:
https://github.com/tsujan/Kvantum/tree/V1.1.4/Kvantum

CDE/Motif (referência de comportamento, não prova do desenho exato da SGI):
https://github.com/cdesktopenv/cde/tree/master/cde/programs/dtwm


## Atualização 0.3.0-rc1 — bloco 3 e entrada Qt Quick

- Bloco 1: desenho da barra aprovado pelo usuário; SVG preservado. A pressão
  das setas ainda falhava. Encontrado caminho Qt Quick sem Sunken; reparo
  opcional separado e ensaio nativo incluídos, aceitação local pendente.
- Bloco 2: botões aprovados pelo usuário; não redesenhados nesta revisão.
- Bloco 3: campos, combo/option, spin e painéis implementados para validação.
  Foco de teclado e indisponibilidade separados. Cor específica para readonly
  em todos os apps não é suportada apenas pelo SVG Kvantum; sem alegação falsa
  de conclusão desse detalhe. Sem alteração de fonte global.
- Próximo bloco 4: checkboxes (marca vermelha segundo o manual SGI), radios
  (triângulo azul segundo o manual), parcial, desativado, foco e seleção.
- Blocos 5, 6 e 7: continuam pendentes de revisão específica conforme a matriz
  acima. A implementação inicial existente não significa aprovação histórica.

Fontes e limites desta rodada: `docs/CAMPOS.md` e `docs/PRESSAO-QTQUICK.md`.
As galerias Qt não executadas aqui devem ser testadas na máquina de destino.

## Registro de 0.4.0-rc1

52 recursos acrescentados; 2517 anteriores intocados. Marca vermelha, triângulo
azul e locate highlight fundamentados no manual SGI; pixels e parcial adaptados.
O motor Kvantum 1.1.4 não escolhe `pressed` para CheckBox/RadioButton e compõe os
indisponíveis com 0.7 de opacidade. Não anunciar suporte de estado inexistente.
O teste nativo do bloco 4 e a causa das setas continuam pendentes de ensaio local.
