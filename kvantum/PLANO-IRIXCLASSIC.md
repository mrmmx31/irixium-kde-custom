# Plano mestre — Kvantum IrixClassic

Manutenção: `mrmmx31`. Referência de continuidade do componente Kvantum.

## Estado atual — 0.7.1 estável

**Promoção autorizada em 06/10/2026.** A candidata 0.7.1-rc1 foi aceita localmente
com `candidate_accepted_locally` e nenhuma pendência. Toolbar, spinbox e
conjunto/limites receberam aceite com a mesma data. A promoção não muda desenhos,
medidas, efeitos ou áreas clicáveis. Não há nova exigência de aceite antes de
publicar este mesmo conteúdo. Registro: `../distribuicao/promocoes/0.7.1.json`.

| Bloco | Conteúdo | Situação da entrega estável |
|---|---|---|
| 1 | Rolagem, quatro setas, trilho, puxador e ranhuras | Incluído; pressão KDE confirmada com reparo separado |
| 2 | Botões de comando, padrão e ferramentas | Incluído e aprovado no escopo testado |
| 3 | Campos, combos, spinboxes e molduras | Incluído; limite de aparência readonly documentado |
| 4 | Checkbox, radio, parcial, foco e indisponibilidade | Incluído; retestes Classic e moderno aprovados |
| 5 | Menus, submenus, separadores e navegação | Incluído; retestes Classic e moderno aprovados |
| 6 | Abas, quatro orientações, fechamento e transbordamento | Incluído, com adaptações históricas documentadas |
| 7 | Sliders, progresso, divisores, listas, árvores, tabelas e complementos | Incluído; controles nativos/limites documentados |

## Lançamento e trabalho após a entrega

1. Fazer merge/commit desta promoção e enviar o commit ao remoto.
2. Publicar `irixclassic-kvantum-v0.7.1` com o script explícito de publicação.
3. Receber feedback e corrigir problemas em **nova versão**, partindo da tag estável.

A tag e os ZIPs já publicados são imutáveis por política do projeto. Não há
reescrita do aceite anterior, nem troca silenciosa da versão. Correções do escopo
atual seguem para 0.7.2; mudanças maiores de aparência/funcionalidade, para 0.8.0.
Esses números são planejamento, não releases já produzidas.

## Backlog pós-lançamento (não bloqueia a 0.7.1)

Compatibilidade relatada por outros usuários; melhora incremental de fidelidade;
acessibilidade e escalas; distinção universal de campos somente leitura quando
houver suporte adequado; comportamento de widgets personalizados/Qt Quick.
As limitações aceitas não passam a estar implementadas só pela mudança de canal.
Manter o Irixium moderno, as decorações, GTK e fontes independentes. Não
reaplicar o reparo Qt Quick confirmado sem regressão ou alteração do sistema.
Identificação pública: `mrmmx31`; sem nome civil/e-mail pessoal.

## Histórico de desenvolvimento — não representa pendências atuais

Os textos abaixo registram etapas anteriores, antes do aceite e da promoção.
O estado corrente é o descrito acima e em LANCAMENTO.json.

## Estado da entrega

**Fechamento da candidata — 0.7.1-rc1 preservada.** O desenvolvimento dos sete
blocos, acabamento e empacotamento está reunido. `distribuicao/fechar-candidata.sh`
concentra as verificações finais, capturas dos dois temas e de toolbar/spinbox,
ensaio de instalação/restauração em HOME temporário e parecer vinculado ao aceite
manual. A confirmação das setas e dos controles já aprovados não é reaberta.
Não há novos desenhos, alteração de escala/fontes, reaplicação de reparo KDE,
publicação automática ou promoção para estável. O estado final dos três itens de
aceite depende da inspeção da sessão de destino, ainda não recebida para 0.7.1.
Os registros anteriores abaixo são histórico, não novos resultados desta rodada.


**Consolidação da distribuição r1 — mesma aparência 0.7.1-rc1.**

Gerador local de dois artefatos candidatos: tema mínimo para Kvantum Manager e
código-fonte correspondente com instalação/restauração de usuário. Ambos deixam
fora o reparo compartilhado Qt Quick; não o reaplicar nem investigar sem regressão.
Nenhuma mudança de SVG, kvconfig, fontes, escala, decoração ou Irixium moderno.
`distribuicao/CANDIDATA.json` registra o aceite pendente sem convertê-lo em sucesso.
O pedido para avançar não foi interpretado como envio dos retestes de acabamento.
Próximo retorno: toolbar/spinbox e os retestes modernos solicitados; depois o teste
de instalação/restauração do ZIP extraído e a revisão explícita da publicação.
Ver `../distribuicao/README.md` e executar `bash distribuicao/gerar-kvantum.sh --verificar`.

### Registro do acabamento (continua válido)

**0.7.1-rc1 — acabamento localizado; sete blocos preservados.**

Setas de rolagem: funcionamento confirmado pelo usuário após o reparo instalado.
Não reabrir a investigação nem reinstalar o reparo sem regressão observada.
Capturas recebidas em 100%/14 px: diferença de densidade comprovada. Seleção e
menus Classic passaram, respectivamente, em 11/11 e 17/17 verificações nativas.
Isso não equivale a certificar todos os detalhes históricos de cada controle.

Esta candidata corrige a divisória da toolbar e a legibilidade da spinbox;
aprimora o ensaio moderno e o registro parcial dos menus. Altura de menus e
cor de campo somente leitura ficam preservadas, com limites explícitos.
Próximo aceite: separador horizontal/vertical e spinboxes; depois consolidar
publicação, instalação e cobertura. Nenhuma nova fonte global ou módulo KDE.

| Bloco | Conteúdo obrigatório | Estado | Próxima evidência |
|---|---|---|---|
| 1. Barras de rolagem | Setas ↑↓←→; trilho; puxador; ranhuras; estados; extremos; sem intervalo; horizontal/vertical/RTL | Desenho e funcionamento confirmados pelo usuário; reparo compartilhado preservado | Não alterar sem regressão; conservar testes existentes |
| 2. Botões | Push button; botão padrão; ferramenta; menu de ferramenta; normal/hover/pressionado/toggled/desativado; foco de teclado | Aprovado pelo usuário em 0.2.0-rc1; preservado nesta revisão | Galeria prever-botoes.sh; tecla Espaço, retorno do relevo, padrão com pressão, disabled e menus de ferramenta |
| 3. Campos e entradas | Line edit editável e somente leitura; combo editável e de opções; spin box; painéis/frames; caret; seleção; foco; desativado | Implementado para teste em 0.3.0-rc1; cor readonly universal exige suporte fora do SVG | Galeria prever-campos.sh; foco, seleção, limites, RTL; docs/CAMPOS.md |
| 4. Checkboxes e radios | Off/on/parcial; exclusividade; foco; locate highlight; disabled; variantes em menu/lista | Funcional: 11/11 no Classic; geometria da seleção preservada; aceite visual histórico separado | prever-selecao.sh; test_selection.py; docs/SELECAO.md |
| 5. Menus | Barra; popup; item normal/selecionado/pressionado/desativado; separadores; check/radio; submenu; navegação mouse/teclado; item indisponível | Funcional: 17/17 no Classic; moderno ainda em reteste com registro parcial; densidade preservada | prever-menus.sh; galeria --qtquick; docs/MENUS.md |
| 6. Abas | Ativa/inativa/hover/desativada; foco; encaixe; quatro orientações; nomes longos; fechar/transbordamento | Implementado para teste em 0.6.0-rc1; sobreposição e estado em primeiro plano referenciados no VkTabPanel; geometria adaptada | prever-abas.sh, --testar, --qtquick; docs/ABAS.md |
| 7. Sliders e demais controles | Slider/scale; progresso determinado/indeterminado; splitter; headers; listas/tabelas/árvores; seleção; branches; tooltips; dock/toolbox; labels; size grip; MDI; dial | Implementado para ensaio em 0.7.0-rc1; partes nativas e limites históricos explicitados | prever-controles.sh, --testar, --qtquick; docs/COBERTURA-IRIXCLASSIC.md |

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

## Registro de 0.5.0-rc1

Bloco 5 acrescentado sem alterar os mapas anteriores. Barra normal baseada no
perfil central da captura Confidence Tests; estados não mostrados são adaptações.
`State_Selected` de QMenu é item armado, não seleção persistente de checkbox.
A herança para Toolbar, Tooltip, Slider e demais blocos foi neutralizada onde
necessário sem trocar sua configuração efetiva. Menus de combos recebem o novo
popup como consequência intencional da política `combo_menu=true` já existente;
os campos e seus botões não foram redesenhados.

O teste temporário da pressão usa o hit-test do StyleItem em vez de uma consulta
de retângulo de seta não suportada. Nenhum arquivo de sistema é alterado pelo
pacote de tema; reparo em org.kde.desktop permanece separado e opt-in. O próximo
ensaio local deve distinguir a ação de rolar do relevo pressionado.

## Continuidade após 0.6.0-rc1

O antigo “próximo bloco 6 — abas” da entrega 0.5.0-rc1 está implementado para
validação. **Próximo bloco 7:** sliders/scales, progresso determinado/indeterminado,
divisores, cabeçalhos, listas/árvores/tabelas, grades, indicação de ordenação,
seleção, foco e indisponibilidade. Depois: revisão integrada de todos os blocos.
O bug de eventos das setas continua como trilha independente; não aguardar uma
mudança de desenho para considerar corrigido um problema de Qt Quick.

## Continuidade após 0.7.0-rc1

Os sete blocos possuem implementação ou tratamento explicitamente nativo/fora do
tema. Isso não equivale à aceitação final. Próxima etapa: **revisão integrada**,
primeiro Qt Widgets, depois os controles equivalentes Qt Quick e as aplicações
usadas na sessão. Conferir seleção focada/não focada, teclado, RTL, indicadores
desativados, progresso em extremos, textos longos, DPI e fallback de arte.

A barra aprovada não foi redesenhada. O bug das setas KDE permanece uma trilha
separada e não deve bloquear nem ser escondido pela conclusão do desenho.
File Finder/LEDs/thumbwheels específicos, cancelamento do arraste por Escape,
menu de abas colapsadas e organização de aplicativos exigem suporte além do SVG.
Não introduzir novos widgets, bibliotecas ou patches globais silenciosamente.

## Registro da revisão integrada r1

A versão de aparência permanece 0.7.0-rc1. Nenhum SVG ou configuração desse
pacote foi redesenhado. O merge aceita a base 0.6.0-rc1 e o bloco 7 já aplicado.
`revisar-integracao.sh` agrega evidências sem instalar o tema ou corrigir o
sistema. `prever-integracao.sh` compara os mesmos controles em IrixClassic e
Irixium. Histórico de aprovação, teste estático, execução nativa e fidelidade
histórica permanecem categorias distintas. A trilha Qt Quick não está encerrada.

## Aceite e acabamento 0.7.1-rc1

- Seleção/menus Classic: retestes recebidos aprovados. Não exigir as cores do
  Classic no teste do moderno; medir a célula que o QStyle realmente reserva.
- Toolbar: recurso canônico agora vertical, duas colunas centrais; o motor
  rotaciona nas toolbars verticais. A alocação continua 10; o cabo não muda.
- Spinbox: silhueta passa de 5×4 para 7×6 em célula de 12×12. Pressão, limites,
  repetição e disponibilidade continuam sob o Qt; scrollbar intacta.
- Menus: execução interrompida grava JSON parcial, etapa e rastreio de eventos.
  Isso corrige observabilidade; não é aprovação automática do menu moderno.
- Densidade: manter altura atual da menubar nesta revisão; 24 px da fotografia
  não são uma altura mínima universal para outras fontes. Sem forçar 24 px.
- Readonly: mesma superfície da entrada editável; limitação não resolvida pelo
  SVG. Não tratar readOnly como disabled nem injetar QSS nas aplicações.

## Encerramento técnico e critérios finais

- Código dos sete blocos e ferramentas de distribuição: preparados.
- Aparência e manifesto: permanecem 0.7.1-rc1; preservar bytes da candidata.
- Retestes finais: um fluxo, sem instalação global; skip/ausência/interrupção separados.
- Aceite restante: separador nas duas orientações, spinbox, conjunto/limitações.
- Publicação: notas e pacotes disponíveis, decisão explícita; não criar tag/push.
- Escopo não implementável só pelo SVG: documentado, não ocultado nem falsamente concluído.

Procedimento completo: `distribuicao/FECHAMENTO.md`. O programa não altera este
plano para fingir aceite; o parecer local mantém o vínculo com os hashes testados.
