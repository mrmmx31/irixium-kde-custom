# Plano mestre — Kvantum IrixClassic

Manutenção: `mrmmx31`. Este arquivo é a referência de continuidade do trabalho.
Atualizar esta matriz em toda entrega. Não confundir tema Qt Widgets com decoração
Aurorae, tema GTK, estilo Plasma ou configuração de fontes.

## Estado da entrega

**0.1.0-rc2: bloco 1 implementado como candidato; aceitação em Qt/KDE pendente.**
A rc1 existente é uma base funcional, não prova de fidelidade dos blocos 2–7.
Não marcar um bloco como aprovado por ter apenas mapas SVG ou testes estáticos.

| Bloco | Conteúdo obrigatório | Estado | Próxima evidência |
|---|---|---|---|
| 1. Barras de rolagem | Setas ↑↓←→; trilho; puxador; ranhuras; extremidades; orientações; normal/hover/pressionado/desativado; extremos do intervalo; sem intervalo; RTL | Candidato 0.1.0-rc2 implementado; mapa vertical comparado; Qt nativo pendente | Galeria `prever-rolagem.sh`, teste de arraste, prints 100%, comparação com IRIX |
| 2. Botões | Push button; botão padrão; ferramenta; menu de ferramenta; normal/hover/pressionado/toggled/desativado; foco de teclado | Revisão histórica pendente; base rc1 preservada | SGI ch. 9 Pushbuttons + CDE/Motif; revisar relevos e áreas clicáveis |
| 3. Campos e entradas | Line edit editável e somente leitura; combo editável e de opções; spin box; painéis/frames; caret; seleção; foco; desativado | Pendente; base rc1 preservada | SGI Text Fields e Option Buttons; verificar cores distintas por função |
| 4. Checkboxes e radios | Desmarcado/marcado/parcial; rádio; exclusividade; foco; hover/pressionado/desativado; variantes em menu | Pendente; desenhos rc1 são adaptações | SGI: marca vermelha no checkbox e triângulo azul no rádio, figuras 9-3/9-4 |
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
