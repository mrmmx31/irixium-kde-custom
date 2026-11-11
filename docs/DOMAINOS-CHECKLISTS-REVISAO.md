# Pranchetas de avaliação DomainOS

Atualização: 2026-10-10. **Frontend ativo: [prancheta Motif consolidada](DOMAINOS-PRANCHETA-UNIFICADA.md).**
As duas listas GTK abaixo foram preservadas na seção Checklists anteriores.
As instruções antigas de abertura ficam como registro histórico. São duas listas de dez grupos. Na abertura, todos
começaram **Não avaliado**; evidência técnica existente não equivale à sua aprovação.
Cada grupo permite Confirmado, Falha, Dúvida ou Não testei, com o botão Explicar.
O [retorno parcial salvo](review/RETORNO-20261010-PARCIAL.md) confirma V01 e V02
no escopo observado. Os outros 18 grupos continuam sem resposta.

## Projeto — dez grupos

Fonte: [checklist do projeto](review/project-checklist.json), requisitos F01–F35
e decisões consolidadas. As ressalvas de cada evidência aparecem na prancheta.

| ID | Grupo | Estado técnico |
| --- | --- | --- |
| P01 | Applications e gaveta de fixados | Evidências existentes |
| P02 | Relógio, calendário e feriados | Revalidado tecnicamente 2026-10-14 (23+138 verificações); avaliação manual pendente |
| P03 | Rede, gr_osview e correio | Conferido tecnicamente 2026-10-14; avaliação manual pendente |
| P04 | Iconbox: cliques, grupos e rolagem | Q360 confirmou Operações na produção; roda/grupos (19/19), setas+roda (21/21) e cliques/minimizar/restaurar (44/44) passaram no Xephyr :513. Sem mudança no QML; avaliação manual completa continua pendente. Ver `review/P04-ICONBOX-XEPHYR-20261018-R37.json`. |
| P05 | Seleção, Operações e pin temporário | Revalidado tecnicamente 2026-10-14 (65 checks); avaliação manual pendente |
| P06 | Pager e áreas de trabalho | Revalidado parcialmente em 2026-10-14; P08 é dependência explícita para fechar a luz; revisão manual pendente |
| P07 | Bandeja, excedentes e notificações | Revalidado parcialmente em 2026-10-14; lista de ordem vazia porque ConfigView ID4 não recebe o catálogo do applet ID3 (Q373 decide ponte read-only ou limitação); Volume Q335 e menu/contexto Q336 aguardam resposta |
| P08 | Rodapé, ajuda e LED de espera | Ajuste Applications 36×36 e gate geométrico de quatro lados passam 49/49 em Xvfb software e 49/49 em OpenGL threaded, ainda sem instalação no perfil; ver `docs/VALIDACAO-P08-20261014.json`. Activity.qml foi instalado por transação reversível. Evidências anteriores de Xephyr comprovam startup LED/cursor e aberturas de menu sob geometrias anteriores. Captura Plasma completa precisa ser repetida após build válido; Q334 e revisão manual pendentes |
| P09 | Preferências, dicas e miniaturas | Preferências 48/48; miniaturas 16/16, integração Iconbox 1/1 e ciclo nativo 59/59; cartões sem frame clicáveis e modo títulos limpo. Xephyr privado abriu os provedores mas não recebeu frames (15/17); avaliação humana recusada continua preservada, Q338 pendente |
| P10 | Temas, cores, decorações e suíte | Em andamento; GTK3 parcial por Q334, GTK2/GTK4 retidos pela T04 da outra IA, GTK1 depende de Q339; V06 spacing segue Q357 e V07 Q345; V08: além do recorte 15×255, a página 15/165 e o trilho 15×228 foram pareados; o thumb nativo mede 11×21 e Plasma 11×20, iniciado 1 px abaixo. O Plasma oculta o trilho em repouso. Q372 aguarda escolha entre documentar o limite ou abrir demanda QML; revisão humana segue aberta. V09 aguarda Q355/Q356/Q358 e estado transitório Apollo; V10 continua parcial. I174 registrou painel atual 971×109 e VUE 947×93, faixa inferior de 30 px em ambos e +16 px atuais na região superior; I175 deixou duas propostas textuais sem escolha nem instalação. I176/I177 são linha 2.0 após P10 e não foram iniciadas. Q334/I295 seguem dependendo do guest; revisão final aberta. |

## Revisão visual — dez grupos

Fonte: [checklist visual](review/visual-checklist.json) e
[fila de execução](DOMAINOS-FILA-REVISAO-VISUAL.md). Esta lista delimita a revisão;
não solicita repetir ensaios aprovados de cada componente.

| ID | Grupo | Avaliação humana | Estado técnico |
| --- | --- | --- | --- |
| V01 | Cores e harmonia das setas | Confirmado nas barras GTK observadas; sinal + do spin diferente de − relatado | Parcial; novo defeito do spin pendente e estado inteiramente insensível sem regra histórica confirmada |
| V02 | GTK3: barras, relevo e encaixe | Confirmado; usar como exemplo para as demais versões GTK | Parcial; em Xephyr, CSS border transparente não desenha; border/sombra opacos repetem nas linhas/células. Exige decisão sobre integração em nível de aplicação |
| V03 | GTK2 | Sem resposta | I167 ativa e parcial. R692 compara as células verticais normais do engine GTK2 instalado com VUE em 1:1 (0/225 diferenças por seta) e exercita setup/refresh do runtime instalado em raiz privada, preservando o engine após mudança sintética de papel; R710 confirma a transição real KDE BreezeLight→BreezeDark pelo observador privado (KColorScheme #fcfcfc→#292c30; paleta GTK2 atualizada e engine preservado); não prova repaint visual de cliente real. R689 confirma engine `domainos-pixbuf` mapeado pelas duas janelas XChat GTK2 abertas e a VM SR10.4 desperta. R690 compara as células normais esquerda/direita horizontais do engine atual: 0/225 diferenças por célula em 1:1. R691 atualiza o renderer implantado da ponte para conservar o engine ao regenerar a paleta; serviço preservado no mesmo PID e pacote íntegro, sem ainda disparar uma troca real de esquema. R394/R486 e R496–R500 cobrem quatro células normais 15×15 (900/900 pixels) e glyphs 11×11; R501 exercita 32 ciclos pressionar/soltar em quatro paletas; R502 compara 144 pares de esquemas, sem por isso provar mapeamento semântico correto. Ensaios GTK2 privados não substituem inspeção visual humana. Hover, limite/desabilitado histórico, thumb-drag e setas pressionadas na VM continuam pendentes; I517 controla a entrada direta VUE. | R693 acrescenta prova privada do engine: 24 recortes de seta 15×15 (normal, hover, pressionado, solto, limites e widget insensível) coincidem com a paleta gerada; clique nos limites continua bloqueado. Não valida fidelidade histórica VUE, troca real de esquema nem aceite humano. | R694 compara os padrões de papel da seta inferior normal/pressionada com o registro VUE: 0 diferenças em 242 pixels, com papéis dinâmicos e cursor excluído. Ainda é uma direção, não controle inteiro nem aceite humano. | R695: pré-voo do instalador GTK2 passou (`unchanged`, um destino) e o watcher passou com worker falso em fixture privada; não prova regeneração real de paleta. | R696 executa o sincronizador real sobre raízes Tempia: 70 recursos GTK2 mudaram após variar um papel KDE e o engine foi preservado; GTK4 foi interceptado sem escrita, portanto o evento real segue pendente. | R698: mudança real de arquivo na fixture acionou QFileSystemWatcher→QProcess→sincronizador GTK2; 69 assets e RC atualizados com engine preservado. Export KDE/D-Bus simulada, GTK4 sem escrita; transição real ainda pendente. | R752 — após R751, a barra GTK2 do XChat voltou ao perfil transversal Motif; mudaram somente quatro pixels internos por linha do trilho anteriormente achatado, enquanto as quatro setas normais mantêm 225/225 pixels. R755 — a prévia GTK2 nativa confirmou as quatro setas pressionadas/soltas em DomainOS e Breeze Dark (53/225 mudanças, 0 ao soltar), com papéis KDE preservados; as amostras retas dos anexos coincidem pixel a pixel. O aceite visual continua pendente. Avaliação visual humana pendente; a VM não foi tocada. Consulte a fila visual e o recibo R752. R756 — a seção reta continua 15/15 igual, mas a seta superior do anexo estreito tem 61 pixels em tom mais claro; GTK2 coincide com o raster SR10.4. Estado visual pendente; nenhuma cor foi alterada. R757 — no anexo estreito, o thumb tem 144 linhas com preenchimento central distinto do trilho; no XChat GTK2 o corpo visível repete o perfil do trilho e não mostra separação transversal. A referência VM disponível tem thumb quase integral; não identifica essa regra. Sem alteração até resolver a evidência. | R759 cruza o anexo com uma medida nova da VM: o thumb SR10.4 curto é distinto do trilho. R757 foi limitado por não dispor dele. O grande anexo GTK2 oculta a metade inferior; sem comprimento pareado, o thumb não pode ser avaliado. Nenhum código ou cor mudou; julgamento visual segue pendente.
| V04 | GTK4 e limites da API | Sem resposta | Adaptador GTK4 concluído tecnicamente em I168: trilho/thumb 15/11 px e relevo 2 px, estados e paletas dinâmicas em prévia separada/acoplada; zero diferenças contra receita gerada. GTK4 não fornece setas. Comparação não equivale a pixels Motif nem aprovação histórica; conferir recibo I168. |
| V05 | GTK1 e suporte disponível | Sem resposta | Na fila; cobertura DomainOS não comprovada |
| V06 | Qt Widgets e Kvantum | Sem resposta | Parcial: seta normal/pressionada/solta comparada pixel a pixel (cursor da referência mascarado); QTest mudou 53 pixels ao pressionar e soltura restaurou a base. Fixture 165/15 mede barra 15 px e thumb 22 px, cerca de 1 px acima da referência sem métricas pareadas. O espaçamento real viewport/barra é 0 px contra 4 px; tentativa `scrollbar_in_view=true` não altera a métrica e Kvantum não oferece opção identificada. Q357 pergunta se documentar limitação ou propor demanda própria para adaptador Qt. O fill do canto 15×15 coincide com o recorte VUE em 225/225 px; a janela 40×45 ao redor difere em 846/1800 px e não prova a junção completa. Estado disabled continua sem comparação nativa. Qt6 Widgets I170 agora tem adaptador parcial para `scroll_h/scroll_v`: 15 px, cores derivadas do KDE, setas nos limites e ciclo pressionado/solto passaram em rota real isolada; falta avaliação manual e comparação nova com VM. |
| V07 | Qt Quick e System Settings | Sem resposta | Parcial: setas reais Qt Quick/Kirigami nos dois eixos coincidem com variantes SVG 15×15 em 0 diferenças; barras de 15 px e canto 15×15 usam View.BackgroundNormal; System Monitor instalado não expôs conteúdo rolável nem moldura (V07 receipt); Q345 continua pendente para os 4 px; thumb/paletas/revisão humana pendentes |
| V08 | Controles próprios do Plasma Style | Sem resposta | Parcial: Plasma Components real em Xephyr mede barra 15 px/thumb transversal 11 px. A página 15/165 e trilho 15×228 pareados dão thumb nativo 11×21 e Plasma 11×20, iniciado 1 px abaixo; o Plasma esconde o trilho em repouso. Uma matriz dinâmica em quatro paletas alterou 781/781 px do thumb 11×71; o canto de popup real é do host. O recorte normal 15×255 difere em 2.208/3.825 px, incluindo setas Xt ausentes. Variação privada de inset não corrige o comprimento e alarga o thumb horizontal. Q372 respondeu preferência condicional pela alternativa B, sem autorização para implementar; qualquer solução deve ser isolada ao tema DomainOS e ter demanda própria autorizada. Revisão humana segue pendente. |
| V09 | Chapa metálica e desenho do LED | Sem resposta | Parcial (~60% do escopo de evidências: captura integrada 1:1, matriz de quatro paletas e comparação estática concluídas). Painel atual em containment real de Plasma/KWin em Xephyr, 971×109 px; recorte VUE sem oclusão 947×93 px. Q355 pergunta a composição do Pager; Q356 pergunta sobre a faixa de títulos entre Mail e Pager; Q358 pergunta se manter proporções 971×109 do canvas atual ou aproximar a captura VUE 947×93. LED/transições Apollo e revisão manual seguem pendentes. Percentual estima marcos de trabalho, não fidelidade visual. |
| V10 | Conjunto, decorações e esquemas | Sem resposta | Parcial: decoração revalidada; matrizes de paleta no consumidor Plasma V08 e painel V09 têm escopo individual. GTK/Qt restantes, integração conjunta de consumidores/estados e revisão humana seguem abertos. |

O retorno avalia a prévia R13. A correção posterior r2 das cores nos limites
GTK3 ainda não foi apresentada nessa Xephyr; sua prova técnica não foi
convertida em aprovação humana. Os datasets 1.0 permanecem preservados.

## Abrir e responder

O comando do projeto é `python3 -B tools/review_domainos.py`. Ele abre as duas
pranchetas e grava em uma pasta privada em `/tmp`, identificada pelo UID do
usuário, sem alterar seu tema. `--output` permite escolher outra pasta existente.

O frontend está na skill portável
[retro-ui-review](../skills/retro-ui-review/SKILL.md). A execução genérica não
depende de nome de usuário, Downloads ou instalação do projeto:

```bash
review_dir=$(mktemp -d /tmp/domainos-review.XXXXXX)
python3 -B skills/retro-ui-review/scripts/review_board.py \
  --data docs/review/project-checklist.json \
  --data docs/review/visual-checklist.json \
  --output "$review_dir/respostas.json" \
  --title 'DomainOS — pranchetas de avaliação'
```

Execute a partir da raiz do repositório, em uma sessão com GTK3/PyGObject.
Salvar respostas mantém a janela aberta. Salvar e fechar grava e encerra.
Fechar com alterações grava um rascunho. Ao reabrir com o mesmo caminho, as
respostas são recuperadas; mudanças de critério preservam a resposta anterior
e reabrem somente o item alterado. Cada nova gravação mantém um histórico.

Ao retomar o projeto, ler as respostas salvas, registrar falhas/dúvidas na fila
e consultar a evidência que já cobre cada grupo. Repetir uma prova somente por
entrada alterada, falha ou dúvida ainda não coberta. A avaliação do usuário não
bloqueia trabalho independente e as notas não são comandos executáveis.

O protocolo de controle da VM também está preservado como skill portável:
[mame-live-control](../skills/mame-live-control/SKILL.md). Ele usa a sessão
existente e não requer reiniciar a VM para consultar seu canal atual.

## Conferência desta entrega

| Verificação | Resultado e limite |
| --- | --- |
| Organização dos requisitos | Duas listas de dez grupos; F01–F35 aparecem uma vez na lista do projeto. Nenhuma aprovação preenchida pela IA. |
| Prancheta GTK | Janela real observada no KWin/Wayland, aberta e não minimizada. Uma falha inicial de escopo da variável de título foi corrigida; o registro bruto foi preservado. |
| Respostas | Persistência conferida offline. Retorno manual parcial salvo: V01 e V02 confirmados no escopo observado; outros 18 grupos sem resposta. JSON e janela preservados. |
| Skills portáveis | Metadados válidos, cópias instaladas idênticas e ZIP com hashes conferidos. |
| Scripts MAME | 19 testes offline com Lua 5.4 e serviços simulados; nenhum comando na VM nesta entrega. Isso não comprova movimento/foco em outro emulador. |

O [recibo com hashes](review/PREPARACAO-SKILLS.json) permite reutilizar essas
provas enquanto os arquivos e critérios permanecerem iguais. Os testes do tema
já registrados não foram repetidos para preparar estas pranchetas.

A distribuição R2 acrescenta a regra explícita de cores dinâmicas e os índices;
seu [recibo próprio](review/DISTRIBUICAO-REGRAS-R2.json) identifica os hashes novos.
Os scripts, datasets e a prancheta aberta foram preservados. A entrada central
passa a ser o [índice de regras](DOMAINOS-INDICE-REGRAS.md).

## Prancheta de trabalho Motif — decisões por item

Pedido posterior de 2026-10-10: frontend C99/Motif/MVC, com dez grupos da
ferramenta e dez do tema/painel. [Checklist](review/work-board-checklist.json)
e [uso/protocolo](../tools/work-board/README.md). Os datasets e o retorno parcial
GTK anteriores permanecem preservados; este novo arquivo não atribui aprovação
de revisão nem repete suas provas.

Recarregar busca critérios e respostas da IA sem apagar rascunhos. Salvar item
aceita retornos parciais, com revisão e horário próprios. Autorizar execução é
separado da avaliação. Perguntas e instruções aparecem em grupos próprios;
checkboxes entre linhas indicam o intervalo para inseri-las. O nível de
explicação é novice/intermediate/expert.

Ao ler, a IA desmarca somente o aviso de resposta nova da revisão exata.
O texto permanece até o usuário apagá-lo. Resposta da IA, horário de leitura e
estado de execução ficam separados. O modelo evita sobrescrever respostas
concomitantes e conserva um histórico antes de cada gravação.

**Regra atual para a fila futura:** executar somente itens autorizados no JSON
da prancheta Motif, um por vez e dentro de seu escopo. Responder a uma pergunta
não libera alterações. Isso substitui a autorização inferida de trabalhos
independentes para os itens desta fila. Preparar esta prancheta já foi pedido
explicitamente; ela não preenche autorizações de outras atividades.

Estado persistente, derivado de XDG:
`${XDG_STATE_HOME:-$HOME/.local/state}/ai-work-board/respostas.json`.
Abrir pelo `open` do projeto independente AI Work Board; os caminhos antigos
foram substituídos na fila ativa. Consulte a documentação de consolidação. A IA consulta durante o trabalho ou na próxima
interação; salvar não inicia um agente autônomo. O usuário pode responder somente
um item e voltar aos demais depois. Uma aprovação técnica não marca avaliação humana.

## Requisito obrigatório — edição segura

Não entregar campo de texto sem undo/redo de vários passos, copiar, colar,
recortar, selecionar tudo, atalhos Ctrl+Z/Y/Shift+Z/C/V/X/A e menu de edição.
Testar UTF-8, seleção/substituição, troca de item, salvar, recarregar e recuperar
rascunhos. Uma prancheta que organiza decisões também precisa da segurança
básica de um editor. O incidente e sua correção estão na fila; a entrega
anterior não incluía a prova desses comandos. Texto recuperado não é uma
autorização salva e não deve ser incorporado à fila como execução automática.

Atualização 2026-10-13: a build de produção atual passou `check-draft-review`,
`check-draft-review-native` e `check-editing` (12 invariantes). A repetição
nativa em Xephyr :62 com dados artificiais confirmou colagem UTF-8 multilinha,
substituição reversível, Ctrl+Z/Ctrl+Y, troca T01→T02→T01 e recuperação após
WM_DELETE/reabertura; a resposta persistida permaneceu vazia e sem autorização.
Recibo e capturas identificados em
`/home/lsi/tempia/board/work-board-drafts-recheck-20261013/receipt-manual-verification.json`.
A prova não altera a avaliação humana nem autoriza enviar rascunhos.

### Estado de retorno — 2026-10-14 14:56 UTC

Q102 está na sequência 194, sem resposta humana nova. A produção AI Work Board
segue aberta no PID 2876125 em :1; o hash ativo confere com o build. Q338, Q353
e Q360 estão disponíveis na interface. I352 continua sem autorização e Q353
aguarda os passos do relato de rascunho; a correção síncrona I261 está no build
e passou provas sintéticas. Não li o journal pessoal nem criei demanda
duplicada. T04/I167–I173 continuam com a outra IA.

### Retomada — 2026-10-14 16:47 UTC

Q102 revisão 191 já estava reconhecida; não houve resposta nova desde a nota
salva em 2026-10-13. A produção segue aberta no PID 3238326 com o hash estável
registrado na fila. Xephyr :68 continua vivo, mas o processo MAME está ausente;
a bridge mantém um pedido antigo sem resposta correlacionada. Mantive o guest
sem comandos e sem reinício. V08 permanece a família ativa, parcial por falta
de thumb histórico pareado e avaliação manual; Q334/Q354 bloqueiam novas
observações da VM, e Q357 permanece sem resposta. Confirmei no canal que o
corner ROI de V06 já foi medido (seq.240); Q345 ainda precisa indicar uma
aplicação Qt Quick real com moldura, e Q355/Q356/Q358/Q359 aguardam escolhas.
Q366 já pergunta pelo relato do menu de cores da Prancheta; não dupliquei a
pergunta. Não encontrei item visual autorizado e independente que possa avançar
sem essas respostas ou sem tocar em T04. Retomar pela próxima resposta salva,
mantendo Xephyr e produção disponíveis. Progresso reportado como estado de
etapas, sem percentual de fidelidade visual.

A auditoria desta retomada foi enviada no canal compartilhado Q102 seq.254.


### Atualização V08 — 2026-10-14 17:05 UTC

A comparação de conteúdo/fração pareada já está disponível: Help Viewer nativo
“Lines 1 to 15 of 165”, trilho 15×228 e thumb 11×21; Plasma Components real
com a mesma fração e trilho mede 11×20 e começa 1 px abaixo. O trilho do
componente fica oculto em repouso. Um teste privado reduziu os insets
verticalmente, mas manteve o thumb com 20 px e ampliou o thumb horizontal para
13 px, portanto não alterei o SVG do produto. Q372 foi reconhecida na revisão 0
e aguarda a escolha entre documentar o limite atual ou propor integração QML
separada. Xephyr :68 continua preservada sem processo MAME; a bridge mantém o
pedido 4260854bc6024f04a92238d48a3cd4c7 sem resposta/ack, sem novo input ou
reinício. A produção AI Work Board está aberta no PID 3339378 para respostas.
Recibo atualizado: `docs/VALIDACAO-V08-PLASMA-20261014.json`.

### P07 — pergunta de arquitetura para a ordenação da bandeja — 2026-10-14 17:10 UTC

A configuração falha porque o ConfigView (ID 4) não recebe a ação `internalAction`
do applet dono (ID 3); a prova capturou `availableItems=[]` contra 18 provedores
no host, com 14/43 gates de edição de ordem falhando. O escopo atual também
proíbe criar outra instância de bandeja ao abrir preferências. Registrei Q373
após P07 para escolher entre uma ponte runtime read-only sem escrita pessoal ou
a limitação dos campos avançados por IDs, com a lista dinâmica removida/documentada.
Reconheci Q373 revisão 0. P07 permanece parcial; nenhum painel/configuração foi
alterado e Q335/Q336 não foram inferidas. Recibo: `docs/VALIDACAO-P07-20261014.json`.

### V03 — GTK2, estado para avaliação do usuário — R760

O trilho GTK2 foi restaurado ao perfil de revisão mais plano `DDFFFFFFFFFFFLL`;
thumb elevado separado e papéis de cor KDE foram preservados. O perfil medido
na VM continua `DDLLFFFFFFFDDLL`. O reload atingiu 111 janelas sem erros X
concorrentes, sem reiniciar aplicações. I167 segue sem aceite humano. Aguardar
os pontos que o usuário reportar e autorizar antes de qualquer nova alteração.
Registro: [R760](review/I167-GTK2-BASELINE-RESTORED-20261029-R760.json).
