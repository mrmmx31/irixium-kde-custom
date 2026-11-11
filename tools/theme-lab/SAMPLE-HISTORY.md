# Históricos das amostras nativas

## Contrato de armazenamento — T04

`preview_sample_journal.py` guarda somente o histórico de texto das amostras.
Não escreve receitas, projetos, `editor-journal.json`, `project-history.json`
ou respostas da prancheta. Não guarda cores finais. O arquivo é individual
por família e origem: `sample-gtk2-coupled.json`, por exemplo. O workspace
privado da aplicação será sua origem; o hash da receita não é identidade da
amostra, pois alterar geometria/paleta não deve apagar texto.

Cada controle (`entry`, `text`, `spin`) possui texto, cursor, âncora, valor
numérico confirmado quando houver, estados de Undo/Redo e posição atual.
Os índices da seleção são caracteres Unicode, conforme os controles GTK,
não offsets em bytes. O spin pode conter texto parcial diferente do valor
confirmado; carregar não significa confirmar com Enter.

O documento usa UTF-8, versão1, tipo `theme_lab_sample_text_history`. A leitura
valida integralmente antes de oferecer estados ao widget. Não aceitar JSON
corrompido, chave duplicada, família/origem errada, seleção impossível, números
não finitos, controles desconhecidos ou versão inesperada. O original permanece
no disco. Um segundo `load` não substitui o histórico de uma sessão viva.

O chamador fornece diretório existente, próprio e0700; arquivos/lock são0600.
Links simbólicos e arquivos não regulares são recusados. Lock não bloqueante
mais comparação do SHA-256 impedem sobrescrita por outro escritor. A gravação
usa arquivo temporário no mesmo diretório, fsync, substituição atômica e fsync
do diretório. Erro deve ser apresentado pelo chamador; não equivale a salvar.
Erro depois da substituição pode ter publicado os bytes; uma repetição verifica
seu hash e sincroniza novamente o diretório, sem ocultar o primeiro erro.

Limites: até128 estados/1MiB por controle; preservar ao menos os dois últimos
estados permite ultrapassar1MiB em uma colagem grande. Limite rígido16MiB por
estado e32MiB por journal serializado (incluindo escape JSON). Não há promessa
de retenção ilimitada ou perda zero sob queda de energia. Arquivo de lock é
auxiliar, separado do JSON. O chamador não deve resetar em caso de erro.

## Estado comprovado

Onze testes de armazenamento passaram, incluindo dois processos independentes,
UTF-8, seleção, Undo/Redo, ramo novo, texto parcial de spin, quatro identidades
família/origem, corrupção, conflito, falha antes de publicação, falha de fsync,
links/permissões, limites e lock ocupado. Três regressões do histórico passaram.

## Integração GTK2 comprovada

`gtk2_sample_state.py` liga IDs estáveis dos três controles ao journal.
`NativeSession` restaura antes de criar a cena, captura seleção e alterações
pendentes antes de reconstruir/fechar, conserva controles temporariamente ocultos
e recusa uma reconstrução cujo checkpoint falhou. A prévia usa o diretório
privado `preview-events`; o controlador processa apenas `event-*.json`.

O watcher faz checkpoint a cada250ms e ao receber fechamento nativo. Falha
mantém a janela aberta, mostra o erro no título e registra no stderr. Uma nova
tentativa bem-sucedida limpa o aviso. Nenhum temporizador impede a edição.
Encerramento externo/crash pode perder alterações feitas desde o checkpoint;
esse limite não equivale a um fechamento nativo protegido. Uma gravação sem
mudanças não substitui o arquivo nem força fsync repetido; fsync pendente após
falha continua obrigatório na tentativa seguinte.

No processo privado GTK2, `gtk-entry-select-on-focus` fica falso para o foco
inicial não substituir cursor/âncora recuperados. Não altera o desktop.
PRIMARY tem um dono por tela: selecionar outro campo pode desfazer a seleção
ativa anterior, comportamento GTK2 nativo. Histórico preserva estados anteriores;
a prova usa uma seleção ativa por vez, sem prometer múltiplos donos simultâneos.

Quatro processos nativos passaram escrita/leitura nas duas origens, com texto
UTF-8, seleção TextView, cursor Entry, texto parcial spin separado do valor42,
Ctrl+Z/Y/Shift+Z depois da recuperação e rebuild sem perda. Falha artificial
bloqueou fechamento e rebuild conservando os três widgets; recuperação permitiu
fechar novamente. A prova não simula digitação Unicode: prepara estados pelos
controles nativos e exercita os atalhos pelo teclado X11 real. O controlador
Motif também passou Save/Load, Undo/Redo e reinício da prévia GTK2.

O launcher transfere somente journals GTK2 conhecidos e validados, exatamente
como bytes, com hashes e rechecagem de concorrência. Não copia arquivos lock
nem eventos. Dezoito testes de retomada passaram. Worker valida usando o módulo
do próprio pacote congelado; entrega pessoal concluída na Xephyr61, PID2901877, com origem2871342 viva
e64 históricos anteriores do editor preservados. A origem não continha journals
de amostras; não houve texto não salvo importado nem promessa retroativa de recuperação. GTK3 é consumidor futuro; aceitar seu nome no
formato não comprova integração nessa família. Ranges/listas e outros estados
não textuais exigem contrato próprio. Esta etapa não conclui T04.

## Contrato dos estados não textuais GTK2

`gtk2_runtime_state.py` oferece captura/restauração tipada dos controles reais:
toggle/check booleanos, radio0–1, combo−1–2, escalas e barras com limites reais
do GtkAdjustment, progresso0–1 e lista com conteúdo, linha selecionada e offsets.
A restauração valida o conjunto inteiro e confere intervalos atuais antes de
alterar qualquer widget. Não altera limites nativos para acomodar dados antigos.
Captura de uma cena parcial preserva os controles ocultos pelo ID estável.
Texto de lista é UTF-8: até4096 linhas,4096 bytes por linha e1MiB total. Lista
plana mantém uma seleção, conforme o modo nativo atual; paths inválidos, NaN,
infinito, booleanos em campos numéricos e controles desconhecidos são recusados.
Progresso atualiza também a legenda percentual, evitando valor/legenda divergentes.

Seis testes puros e duas origens GTK2 reais passaram dez tipos de controle,
60 linhas, seleção32 e offsets70/260, preservação de ocultos e preflight
sem alterações parciais. Recibo T04-AMOSTRAS-ESTADOS-GTK2-FUNDACAO-20261011.json.
## Persistência dos estados não textuais

`private_json_store.py` concentra lock/CAS, limites e publicação atômica dos dois
formatos. A API/schema textual existente permanece compatível. O formato novo
`preview_runtime_journal.py` usa `runtime-gtk2-{origin}.json`, tipo
`theme_lab_sample_runtime_state`, versão1. A lista de estados não é histórico
Undo de texto nem receita. Cada documento tem gravação independente; não é uma
transação conjunta de todos os arquivos. Se qualquer checkpoint falhar, manter
memória/janela e bloquear fechamento/rebuild; o documento já salvo pode estar
mais recente que o outro. A tentativa seguinte verifica os hashes e completa
os checkpoints, sem resetar o documento antigo.

SampleState carrega ambos os documentos antes de construir controles e captura
valores antes de reconstruir/fechar. Restaura os estados na nova cena, inclusive
os que ficaram ocultos. O watcher utiliza o mesmo prazo250ms; erro aparece no
título/stderr. Sob kill externo/crash vale o limite entre checkpoints. Após
destruição só publica snapshots previamente capturados, sem ler widgets mortos.
Caches iniciais toggle/check/radio do controlador são fallback: uma escolha
presente no journal tem precedência, mesmo se seu evento ainda não chegou ao C.
Não alterar limites nativos para acomodar valores salvos incompatíveis.

Prova final em quatro processos GTK2 recuperou dez tipos nas duas origens,
60 linhas Unicode, seleções distintas e offsets distintos, legendas coerentes,
ocultação/reaparecimento e rebuild após reinício. Caches contrários não alteraram
estados recuperados. Falha artificial de runtime impediu close/rebuild e
preservou widgets/bytes. Regressão textual de quatro processos passou CtrlZ/Y/
ShiftZ, seleção e spin parcial; controlador Motif passou SaveLoad/UndoRedo e
reinícios. Launcher transfere os quatro journals conhecidos por bytes/hashes;
19 testes de retomada passaram, incluindo runtime inválido sem destino criado.
Armazenamento runtime6/texto11, contrato runtime6 também passaram.
Entrega pessoal desta extensão ainda pendente. GTK3 e fidelidade histórica
não são comprovados por estas provas.
