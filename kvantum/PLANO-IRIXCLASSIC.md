# Plano mestre — Kvantum IrixClassic

Manutenção: `mrmmx31`. Este arquivo é a referência de continuidade do trabalho.
Atualizar esta matriz em toda entrega. Não confundir tema Qt Widgets com decoração
Aurorae, tema GTK, estilo Plasma ou configuração de fontes.

## Estado da entrega

**Revisão integrada r1, mantendo a aparência 0.7.0-rc1 byte a byte.**
Os sete blocos têm implementação ou tratamento nativo documentado. A revisão
agora dispõe de galeria única e agregador de resultados estáticos/nativos;
ela não equivale à aprovação final dos blocos 3–7.

O COMPARACAO-SETAS fornecido confirmou quatro movimentos e mudanças de pixels
em Qt Widgets. Nos casos Quick válidos havia pressão na MouseArea sem Sunken.
Dois casos da cópia corrigida entregaram Sunken e soltura corretos; os casos
chamados down registraram upPage. A cena anterior sobrepunha o canto das duas
barras. A revisão r1 corrige o isolamento e valida o destinatário do evento;
não marca os alvos inválidos como falhas do KDE. Arquivo instalado sem marcador
no momento da coleta; reparo compartilhado continua opt-in e não é redesenhado.

A seta KDE continua sem solução confirmada na aplicação real; há evidência
parcial favorável na cópia temporária. Aceitação em Qt/KDE pendente para esta
revisão integrada. `diagnosticar-setas.sh` continua disponível para inventário,
mas não substitui o ensaio de interação.

Veja `docs/REVISAO-INTEGRADA.md`. Próxima evidência: galeria integrada local e
quatro alvos válidos na comparação corrigida, depois validação na aplicação real.

| Bloco | Conteúdo obrigatório | Estado | Próxima evidência |
|---|---|---|---|
| 1. Barras de rolagem | Setas ↑↓←→; trilho; puxador; ranhuras; estados; extremos; sem intervalo; horizontal/vertical/RTL | Desenho aprovado; Widgets 4/4 observados; pressão Quick ausente, reparo temporário demonstrado em 2 casos; outros alvos antigos inconclusivos | comparar-setas.sh (executor r1 comum, sem canto sobreposto e com alvo validado); instalação KDE separada |
| 2. Botões | Push button; botão padrão; ferramenta; menu de ferramenta; normal/hover/pressionado/toggled/desativado; foco de teclado | Aprovado pelo usuário em 0.2.0-rc1; preservado nesta revisão | Galeria prever-botoes.sh; tecla Espaço, retorno do relevo, padrão com pressão, disabled e menus de ferramenta |
| 3. Campos e entradas | Line edit editável e somente leitura; combo editável e de opções; spin box; painéis/frames; caret; seleção; foco; desativado | Implementado para teste em 0.3.0-rc1; cor readonly universal exige suporte fora do SVG | Galeria prever-campos.sh; foco, seleção, limites, RTL; docs/CAMPOS.md |
| 4. Checkboxes e radios | Off/on/parcial; exclusividade; foco; locate highlight; disabled; variantes em menu/lista | Implementado em 0.4.0-rc1 para teste; pressão separada limitada pelo motor Kvantum | prever-selecao.sh; test_selection.py; docs/SELECAO.md |
| 5. Menus | Barra; popup; item normal/selecionado/pressionado/desativado; separadores; check/radio; submenu; navegação mouse/teclado; item indisponível | Implementado em 0.5.0-rc1 para teste; seleção/pressão, submenu, separador, check/radio e tear-off quando nativo | prever-menus.sh; galeria --qtquick; docs/MENUS.md |
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
