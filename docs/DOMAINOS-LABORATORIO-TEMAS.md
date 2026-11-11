# Laboratório de temas Motif

Pedido incorporado ao goal em 2026-10-10. O usuário regula o desenho; a IA
mantém o aplicativo e os adaptadores. A ferramenta é reutilizável para outros
temas, com projetos próprios. A referência inicial continua sendo Domain/OS
SR10.4 / HP VUE 2.01, sem usar SR10.4.1.

## Arquitetura

- `tools/theme-lab/src/model.c`: dados, validação, projetos JSON, medidas e
  propostas independentes. Não depende de widgets nem instala temas.
- `tools/theme-lab/src/view.c`: interface e controles reais Motif/Xt, referência
  Motif interativa, PNG separado em pixels nativos e campos de ajuste.
  Encaminha ações ao controlador.
- `tools/theme-lab/src/controller.c`: interação, pipeta X11, tarefas assíncronas,
  importação, salvamento, prévias e exportação privada.
- `tools/theme-lab/backend.py`: disponibilidade de runtimes, leitura de papéis
  KDE e tradutores. GTK3 é o primeiro; outros têm status explícito.
- `tools/theme-lab/preview_gtk.py`: montagem de widgets GTK3 reais, acoplada
  ou desacoplada; eventos de seleção/posição retornam por JSON privado.
- `tools/theme-lab/src/native_colors.cpp`: leitor separado dos estados do
  esquema selecionado por KColorScheme; não inicia uma interface Qt nem DBus.

Uma receita reúne dimensões, papéis de cores, fatores de iluminação e notas.
A geometria medida da referência fica separada da proposta de cada família.
Padding e tamanho de fonte iniciais são defaults da ferramenta, sem atribuição
histórica. O código Motif 2.3.8 do Debian apoia este aplicativo; ele não prova
que a VM SR10.4 usa essa versão.

## Regra de cores e pipeta

Os controles acompanham os papéis vivos do esquema KDE. Os campos selecionam
papéis como `Colors:Button/BackgroundNormal`, não RGB finais fixos. Luz, sombra
e trilho derivam da paleta. A pipeta registra RGB16 e RGB8, posição, visual X11
e origem. A medida é evidência ou entrada futura para um esquema selecionável;
não substitui automaticamente os papéis de um consumidor.

Dentro do Xephyr, a pipeta mede sua tela privada, incluindo a referência PNG
e os controles dos outros toolkits. Não captura a sessão Wayland externa.
Esc ou botão direito cancela, e o ponteiro é liberado após 30 segundos.
As exceções LED/Pager continuam limitadas às cores de sinal já autorizadas.

## Famílias e ordem

Motif, GTK1/2/3/4/5 quando disponível, Qt5/6, Kvantum e Plasma têm receitas
separadas. Biblioteca ausente aparece como indisponível. Qt Quick de estilo
KDE e os SVGs do Plasma são implementações diferentes; uma prévia não confirma
a outra. Salvar a receita também não comprova um tradutor implementado.

Primeira entrega: controles Motif reais, medidas, importação/salvamento,
pipeta e tradução privada GTK3. Depois, traduzir as demais famílias uma por
vez, usando o mesmo contrato e evidências. Aplicar no laboratório muda a
prévia; instalar um tema exige uma proposta exportada e verificável.

## Verificação

O modelo recebe testes de importação inválida, persistência e separação das
receitas. O tradutor recebe ensaios com geometrias diferentes e papéis dinâmicos.
A interface precisa de prova nativa: manter/soltar controles, pipeta, importação,
salvamento e prévia real GTK3. A avaliação visual continua pertencendo ao usuário.
As duas respostas salvas da prancheta não aprovam os outros 18 itens.

Compilação e execução: [README da ferramenta](../tools/theme-lab/README.md).


### Layout de trabalho solicitado em 2026-10-10

Ao maximizar, usar três painéis: ferramentas/seletores à esquerda; montagem
interativa acoplada ao centro; trecho de script relacionado à seleção à direita.
A plataforma e o esquema de teste usam comboboxes. O esquema afeta somente os
controles em teste, sem alterar o desktop. Atualização manual por botão ou
checkbox automático, com atraso configurável para reunir várias alterações.

Categorias têm checkbox de visibilidade e controles disponíveis para o toolkit.
O usuário escolhe e posiciona componentes no preview: setas isoladas, barras,
botões ou combinações como barra com setas. O painel de ferramentas apresenta
parâmetros do componente/estado selecionado. Permitir comparar normal,
pressionado e demais estados suportados, declarando limites do toolkit.
A segunda prévia é desacoplada e nativa (GTK/Qt/etc), independente da montagem.
Mostrar código somente do controle/regra em edição, sem despejar o tema inteiro.
A primeira versão da ferramenta deve ficar aberta para análise enquanto o layout
é adaptado; avaliações anteriores e projetos salvos devem ser preservados.

## Separação entre edição e aplicação

O controller mantém o projeto em edição e uma cena aplicada separados. O botão
Atualizar ou o intervalo automático copia a proposta para a cena e recria a
montagem GTK3 com seu tema privado. Selecionar um controle muda o editor. Mover
diretamente um controle altera somente a posição da cena; não aplica valores
de geometria ou cores ainda pendentes. Exportar registra a proposta sem alterar
a cena aplicada. Eventos antigos são recusados pelo hash da cena.

O trecho do terceiro painel contém os seletores reais GTK3 do controle/estado
escolhido, usando papéis de cores. Máscaras compartilhadas aparecem como
dependências. Famílias sem tradutor mostram uma receita JSON explicitamente
pendente; não se apresenta código fictício como implementado.

## Alcance desta entrega

O catálogo inicial contém 16 tipos em cinco categorias: botões, entradas,
faixas/barras, dados e contêineres. Não é ainda um inventário de todos os
widgets de cada biblioteca. Motif não tem ProgressBar padrão; o indicador usa
Scale e informa essa diferença. O GTK3 usa ProgressBar real. Composições de
scrollbar/setas seguem o contrato único já validado, sem copiar o desenho de
um outro toolkit para preencher uma plataforma indisponível.

Estado técnico reconciliado em 2026-10-17: GTK1 tem runtime XMMS/GTK+ 1.2
privado disponível, mas ainda não tem adaptador DomainOS; GTK5 segue sem runtime
publicado viável. GTK2 e GTK4 têm adaptadores parciais. Qt5 e Qt6 cobrem os 16
controles do catálogo em widgets reais, mas a revisão histórica/humana permanece
separada. Kvantum e Plasma têm tradutores reais de barras de rolagem apenas.
Nenhum seletor ou galeria, por si só, prova equivalência de todas as famílias.

## Entrega V2 e avaliação

A montagem de três painéis foi aberta na sessão de teste, preservando a V1 e
seus projetos. O [recibo funcional](review/theme-lab-v2/RESULTADO.json) registra
os hashes e 14 verificações nativas resolvidas; as
[capturas](review/theme-lab-v2/V2-OPEN.png) mostram a interface entregue.
Não equivalem à aprovação do usuário ou à fidelidade histórica completa.

Em 1280 × 800, os campos de geometria/cores mais abaixo exigem rolagem no editor.
O canvas e a referência conservam pixels 1:1, usando rolagem quando excedem o
painel central. O código preserva linhas sem quebra e tem rolagem horizontal.
Maximizar aumenta os painéis; não interpola o desenho de referência.

Próxima revisão: ajustes manuais GTK3, ampliação do catálogo de controles e,
depois, tradução de outra família. Os outros adaptadores não recebem aprovação
pela presença de um seletor de plataforma ou de uma galeria nativa.

## Referência Motif interativa

O segundo quadro central contém controles reais do Motif instalado. Sua receita
é `recipes.motif`; posição, medidas e fatores não vêm da receita GTK3 em edição.
As categorias visíveis acompanham a cena aplicada para permitir comparar o
mesmo conjunto. O esquema escolhido colore os dois quadros, com os papéis de
cada receita. Pressionar/soltar e mover os controles da referência não altera
os projetos. Para regular a própria referência, selecione a família Motif.

O PNG histórico continua disponível em **Imagem histórica**, em outra janela
sem bloquear a montagem. Motif 2.3.8 é uma referência executável para o trabalho;
as medidas e efeitos da VM SR10.4 continuam sendo a fonte histórica.

## Revisão solicitada para uso diário

A versão corrente do tema é publicada como beta sem depender do término dos
tradutores. A ferramenta abre nativamente na sessão lsi, com estado e paleta
de teste separados das configurações do desktop. Usar Xephyr quando solicitado.

Cada botão, seletor, campo e controle de ajuste recebe hint com finalidade e
unidade. A comparação mostra largura/altura medidas, tamanho automático ou
personalizado e posições correspondentes; não tratar o tamanho da amostra
como default universal do Motif. A fonte não é a etapa visual ativa.

Busca no código: localizar texto para frente e para trás. A montagem acoplada
usa renderização nativa quando implementada; famílias sem adaptador não devem
ser apresentadas como equivalentes. GTK3/Motif precedem os demais tradutores.

## Fila orientada pelo usuário

O restante da ferramenta está organizado em dez grupos na
[prancheta de trabalho Motif](../tools/work-board/README.md): medidas/spins;
catálogo/montagem; propriedades/estados; adaptadores; esquemas/pipeta;
código/busca; dicas; projetos/exportação; execução/recuperação; validação/entrega.
Cada grupo declara o que existe, o que falta e seu critério de conclusão.
A existência desses controles na prancheta não conclui o laboratório.

O usuário passa a liberar atividades por checkbox salvo. A IA recebe respostas
parciais e preserva notas, horários e revisões; explica no nível escolhido.
Os rascunhos de métricas no laboratório permanecem em andamento, sem completar
essa implementação antes da autorização específica. A prancheta compila em alvo
independente e pode abrir nativamente sem modificar a ferramenta ou seu projeto.

## Entrada de texto — requisito impeditivo de entrega

Após incidente Ctrl+Z na prancheta, o usuário determinou que nenhum frontend
com texto seja entregue sem undo/redo, copiar/colar/recortar, seleção e atalhos
usuais, menu acessível e prova nativa com vários parágrafos UTF-8. O laboratório
deve adotar uma camada explícita de edição antes da próxima entrega que altere
seus campos; os defaults Motif não comprovam esse requisito. Rascunhos devem
ser recuperáveis em disco e ações de substituição precisam ser reversíveis.
O módulo `tools/work-board/src/editor.c` é a primeira implementação; sua prova
aplica-se à prancheta, não certifica automaticamente o editor de temas.

## T04 — dez frentes internas (resposta à revisão5)

Subtarefas internas da T04 (estado verificado em 2026-10-17):
1. Inventário de runtimes: GTK1/GTK5 verificados; XMMS fornece um GTK1 privado usável, sem adaptador DomainOS. GTK5 continua indisponível. GTK1 permanece fora do tema até uma demanda específica.
2. GTK2: adaptador em andamento. Botão e seta têm entregas próprias; botão alternável, checkbox e rádio foram integrados por I193–I195. R54 validou na UI Motif os campos persistíveis de largura/comprimento da escala e sua disponibilidade somente na família GTK2. I167 permanece parcial: faltam estados/propriedades e avaliação histórica, além de controles ainda não concluídos.
3. GTK4: rotas nativas para `push`, `toggle`, `check` e `scroll_h`/`scroll_v`; controles restantes continuam recusados antes de abrir a cena. A checkbox usa GtkCheckButton e papéis KDE; o parser C aceita estado apenas para índices suportados. Prova real de worker separado e acoplado: três cliques, retenção de estado ao regenerar, cena anterior preservada para controle recusado e recuperação. Recibo `review/T04-GTK4-CHECK-20261017.json`. Comparação visual com Motif/VM e avaliação humana ainda não feitas.
4. Qt5: I169 cobre os 16 controles do catálogo em widgets Qt reais com papéis KDE, entrada e layout nativos. Comparação estática com o Trash Can foi registrada; não é captura da VM nem aprovação visual humana. Recibo `review/I169-QT5-SCROLLBARS-20261016.json`.
5. Qt6: I170 cobre tecnicamente os 16 controles; setas de scrollbar usam sobreposição local, enquanto range, thumb, roda e ponteiro continuam Qt nativos. Checkbox/radio/entry têm provas de interação, sem medidas históricas pareadas e aprovação humana. Recibos I170 de scrollbar, lista e moldura.
6. Kvantum: I171 gera SVG/config privados e mede barras reais Qt6. A folga de 4 px aparece na montagem QScrollArea testada, não é uma métrica independente do Kvantum; outra montagem pode diferir. Recibo `review/I171-KVANTUM-GAP-RECHECK-20261016.json`.
7. Plasma Style: I172 gera o tema/paleta em XDG privado e prova `Plasma Components.ScrollBar`/KSvg real para `scroll_h`/`scroll_v`. O componente não oferece setas/steppers nem folga independente de 4 px; estado hover/disabled e comparação histórica seguem pendentes.
8. GTK1/GTK5: GTK1 está tecnicamente disponível apenas pelo runtime isolado XMMS/GTK+ 1.2; a janela de preferências demonstra widgets GTK1, não um tema DomainOS. GTK5 não tem release/runtime viável. Ver I173 e I436.
9. Prévia acoplada/separada: GTK4 checkbox agora tem prova nativa em ambas as origens; GTK2/GTK4 e alguns fluxos Qt têm provas próprias. A equivalência de receitas, métricas, posições e interações ainda precisa ser fechada por família e controle.
10. Integração e entrega: os testes de edição segura passaram nesta revisão com Xvfb dedicado: UTF-8 multilingue, Undo/Redo, atalhos, clipboard, salvar/reabrir, troca de controle e recuperação. A substituição pessoal e a validação Plasma completa não foram feitas.

Cada etapa usa quatro marcos: fundação, cena/sessão, controlador/histórico e entrega. A build C99 atual foi recompilada em `~/tempia/theme-lab-t04-20261017/build` (hash idêntico à build do workspace). A janela Motif está aberta em Xephyr :74, com HOME/XDG/projeto privados e o esquema KDE DomainOS copiado apenas para esse perfil. A prévia Plasma completa falhou antes de iniciar KWin/Plasma: o usuário já tinha 403 instâncias inotify abertas para o limite 384; nenhuma sessão existente foi encerrada. Evidência e limites: `review/T04-BUILD-XEPHYR-RECHECK-20261017.json`. Testes técnicos não substituem avaliação visual/histórica.

## T02 — catálogo em árvore e montagem (auditoria 2026-10-12)

A versão compilada atual passou a matriz nativa das cinco categorias e 16
controles, com Space/Enter e receitas GTK3/Motif independentes. Save/Load pelos
diálogos reais restaurou máscaras de visibilidade, controle selecionado,
posições e montagem. Uma tentativa anterior do harness clicou categoria fora do
recorte; não foi classificada como falha de produto. A repetição revelou e
validou o alvo antes da entrada. Ver recibo e hashes em
[T02-CATALOGO-AUDITORIA-20261012.json](review/T02-CATALOGO-AUDITORIA-20261012.json).
A expansão permanece estado da visão atual; a avaliação do usuário e a
fidelidade histórica não foram inferidas desses testes.
