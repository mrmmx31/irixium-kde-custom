# DomainOS — interação, aplicativos, dicas e preferências

Esta revisão complementa a integração anterior. Os resultados R9/R5 descritos
na matriz e no relatório de 8 de outubro são históricos; não validam automaticamente
os componentes acrescentados nesta revisão. O desenho aprovado em Downloads e os
pacotes públicos anteriores permanecem intactos.

## Comportamento entregue

- Num grupo do Iconbox, clicar no título restaura somente aquela janela quando
  nenhum membro está selecionado por checkbox. Os checkboxes iniciam a seleção
  em lote; enquanto ela existir, clicar no título seleciona ou desmarca. Limpar
  todos os checkboxes devolve o clique direto para restaurar. As identidades
  nativas e os PIDs são conferidos novamente antes da ação.
- O segundo clique no mesmo lançador fecha seu menu ou quadro. O terceiro reabre.
  O estado capturado durante o evento evita o ciclo de fechar no pressionamento
  e reabrir ao soltar; não foi acrescentado timer de ação ou de repaint.
- O menu DomainOS continua sendo o padrão. Sua busca usa o provedor de aplicativos
  do KDE e pesquisa globalmente, mesmo quando a categoria aberta está vazia.
  Uma preferência permite usar a interface instalada do Menu de aplicativos do
  KDE, carregada sem modificar os arquivos do KDE.
- A gaveta de aplicativos fixados contém sempre “Preferências do painel…”,
  inclusive quando não há pins. Esse item não pertence à lista editável de pins.
- As dicas dos botões da barra e dos itens da bandeja vêm desligadas. A opção
  própria controla somente os itens desta instância; as condições originais dos
  provedores nativos são restauradas ao habilitar as dicas ou desmontar o painel.
- No Iconbox, o padrão é mostrar título/lista ordenada. A lista de grupos é rolável
  e não omite membros depois da oitava linha. As alternativas são miniaturas
  nativas ou nenhuma dica. Títulos permanecem texto literal, inclusive `<` e `&`.
- Capturas de miniaturas só existem enquanto a dica está visível. Dicas textuais
  não carregam provedores de captura. Ativar uma miniatura confere novamente a
  identidade da janela.

## Provas separadas por escopo

| Ensaio | Resultado | Evidência local |
| --- | --- | --- |
| Grupos, clique direto, seleção e duplo clique em Qt | 63/63 | `/tmp/irix-domainos-iconbox-group-title-qt-r10/RESULTADO.json` |
| Grupos com janelas reais em Wayland | 75/75 | `/tmp/irix-domainos-group-title-wayland-r1/RESULTADO.json` |
| Busca global, favoritos, gaveta e lançamento real controlado | 33/33 | `/tmp/irix-domainos-aplicativos-busca-global-r2/RESULTADO.json` |
| Lançamento e atividade pelo menu DomainOS | 32/32 | `/tmp/irix-domainos-aplicativos-atividade-busca-global-r1/RESULTADO.json` |
| Interface original KDE opcional, busca e preferências permanentes | 23/23 | `/tmp/irix-domainos-application-interface-native-r1/RESULTADO.json` |
| Padrões, Apply/Discard, persistência e independência das preferências | 48/48 | `/tmp/irix-domainos-preferencias-dicas-menu-r1/RESULTADO.json` |
| Dicas, grupos com 12 títulos e ciclo de vida da captura | 11/11 | `plasma/tests/test_domainos_thumbnails.py` |
| Miniaturas reais X11 e atualização por repaint de duas janelas próprias, após corrigir a visibilidade dos Loaders | 23/23 | `/tmp/irix-domainos-miniaturas-x11-owned-dicas-r4/RESULTADO.json` |
| Onze lançadores com os padrões da versão R7 | 19/19 | `/tmp/irix-domainos-toggle-native-r8/RESULTADO.json` |
| Onze lançadores, segundo clique, reabertura, dicas reais ativas, Escape e clique exterior | 19/19 | `/tmp/irix-domainos-toggle-native-hints-r2/RESULTADO.json` |
| Dicas dos 13 provedores reais da bandeja, bindings originais e ciclo habilitar/desligar/reativar | 42/42 | `/tmp/irix-domainos-native-tray-hints-r11/RESULTADO.json` |
| Instalar, repetir e restaurar quatro recursos em perfil privado, incluindo a correção das dicas | 22/22 | `/tmp/irix-domainos-entrega-20261009-r11-dicas/RESULTADO.json` |
| Atualização dos recursos do lsi e preservação das oito preferências pessoais | 5/5 | `/tmp/irix-domainos-instalacao-lsi-20261009-r10-interacao/RESULTADO.json` |
| Integridade e dependências do novo pacote de prévia | 3/3 | `/tmp/irix-domainos-teste-pacote-r7-dicas/VERIFICACAO.json` |
| Inicialização da prévia R7 e manutenção do painel nos dois desktops privados | 11/11 e 9/9 | `/tmp/irix-domainos-teste-uid1000-20261009-dicas-r7/RESULTADO.json` e `PAGER-VERIFICACAO.json` |

Os ensaios de grupos precedem a inclusão das dicas textuais. Eles validam os
gestos e as ações nativas; os ensaios posteriores de dicas e preferências cobrem
a camada de hover adicionada. O ensaio físico final identificou e corrigiu uma
interferência: o Loader da lista de títulos podia aparecer sobre o tile antes da
dica nativa abrir. Ambos os Loaders agora ficam invisíveis fora do tooltip, mantendo
a medição antecipada. O grupo volta a receber o primeiro clique; o hover e as
miniaturas foram revalidados após essa correção. Não se somam os números como se fossem uma
única matriz executada sobre uma única versão.

Em X11, foram fornecidos ao provedor somente os IDs de duas janelas criadas pelo
ensaio. As imagens vermelha/verde e a mudança posterior para azul confirmam
captura real e atualização, não imagens simuladas. O compositor existente não
foi substituído e as configurações da sessão conservaram seus hashes.

Em Wayland, o código utiliza a integração nativa de KWin/PipeWire. O ambiente
virtual não forneceu um frame pronto; portanto, **captura de miniaturas Wayland
ainda não tem validação positiva**. A indisponibilidade aparece explicitamente.
Isso não invalida a prova separada de restauração/seleção das janelas em Wayland.
O menu KDE opcional conserva seu despacho nativo; a prova da lente de atividade
citada acima pertence ao menu DomainOS.

## Minimização e seleção

O esclarecimento posterior sobre minimização corrigiu o relevo persistente do
Iconbox: uma janela selecionada e minimizada conserva sua seleção, mas levanta
os relevos do botão e do rótulo. Restaurar recupera o relevo da seleção. Num grupo,
esse estado elevado corresponde a todos os membros minimizados; um grupo misto
mantém seu estado anterior. Segurar fisicamente o botão continua afundando seu
relevo imediatamente. Não há novo timer, comando de janela ou alteração dos
checkboxs para produzir esse estado visual.

O teste Qt passou 73/73, incluindo dez verificações novas de minimização,
restauração, grupos mistos e seleção preservada:
`/tmp/irix-domainos-iconbox-minimized-qt-r1/RESULTADO.json`.
O ensaio físico X11 passou 19/19 em
`/tmp/irix-domainos-minimized-native-r1/RESULTADO.json`: clique real minimizou
um cliente próprio; o TasksModel e o QWidget confirmaram o estado, mantendo
WinId/PID e seleção. Duplo clique real no tile restaurou e focou esse mesmo
cliente. As capturas `RESTORED-SELECTED.png`, `MINIMIZED-SELECTED.png` e
`RESTORED-AGAIN.png` mostram a troca de relevo; nenhuma configuração real mudou.
As provas R7 acima precedem essa correção do relevo; suas evidências continuam
válidas para as partes que não foram alteradas, sem afirmar que R7 já a contém.

## Restaurar padrões

As oito categorias têm **Restaurar esta categoria**. A nova página **Padrões do
painel** contém **Restaurar todos os padrões**. Os dois controles preparam o
rascunho; Aplicar salva e Descartar conserva os valores anteriores. O reset geral
abrange as 40 entradas do schema, incluindo fixados e comandos personalizados,
somente nesta instância. Não cria desktops nem altera outras instâncias.

Os testes de cobertura do schema e do helper passaram 8/8. O ensaio nativo
`/tmp/irix-domainos-padroes-native-r3/RESULTADO.json` confirmou 31 verificações
funcionais: abertura sem mudança pendente, cliques reais de reset/Aplicar/Descartar,
edição das 40 chaves, reset das categorias Iconbox/Bandeja/Aplicativos, preservação
da segunda instância e persistência das duas após reiniciar o host privado.
O cabeçalho `ConfigDefaults.qml` nas capturas R3 foi fornecido artificialmente
pelo driver; a categoria de produção se chama **Padrões do painel**. O runner
agora consulta esse nome no modelo nativo, sem substituir as capturas históricas.

O relatório nativo permanece com `status: failed`: a verificação adicional de
ausência de erros QML encontrou seis TypeErrors no `PromptDialog.qml` do Kirigami
instalado, relativos aos enums `None`/`Success`. O baseline
`/tmp/irix-domainos-padroes-baseline-r7-native-r1/RESULTADO.json` passou 17/17
verificações de reprodução e isolamento: as páginas antigas R7, sem os controles
ou helpers de reset, produziram exatamente os mesmos seis erros ao descartar três
edições comuns. Os logs foram preservados; não houve supressão dos diagnósticos
nem alteração do SDK global. Essa limitação do diálogo instalado é separada da
validação funcional do reset e foi observada no ambiente privado de ensaio; não
se afirma que os seis erros apareçam na sessão pessoal do usuário.

## Ordem da bandeja

**Bandeja e notificações** mostra os nomes dos itens e setas de subir/descer.
Os campos manuais de IDs ficam em **Configuração avançada**, recolhida por padrão.
Mover edita somente `cfg_trayOrder`: Aplicar confirma, Descartar conserva a ordem
salva. Um ID temporariamente indisponível mantém sua posição. A política de
visibilidade é independente da ordenação; os seis primeiros itens visíveis ficam
na bandeja e os excedentes seguem sua sequência na ▶.

O ensaio `/tmp/irix-domainos-tray-order-native-r3/RESULTADO.json` passou 42/42
verificações de comportamento e isolamento. Usou cliques reais nas setas e nos
comandos nativos de Cancelar/Descartar/Aplicar, preservou as outras preferências
e o applet ID 101 e conferiu a ordem efetiva dos seis slots e dos seis excedentes.
As capturas `ORDER-INITIAL.png`, `ORDER-DRAFT.png`, `ORDER-DISCARDED.png`,
`ORDER-APPLIED.png` e `ORDER-BACKEND.png` estão nessa saída.

O gate separado `qml_runtime_errors_zero` permanece falso: os dois diálogos de
descarte produziram quatro TypeErrors `PromptDialog.None`/`Success`, correspondentes
às linhas reproduzidas no baseline R7 acima. O status qualifica explicitamente
essa condição; logs e diagnósticos não foram ocultados. A prova de ordenação
precede a correção posterior da textura das posições ocupadas da bandeja.

Para reproduzir o ensaio:

```sh
python3 plasma/tools/testar-domainos-ordem-bandeja.py \
  --saida /tmp/irix-domainos-ordem-bandeja-ensaio \
  --recursos-encerrados /tmp/irix-domainos-native-tray-hints-r11
```

## Nitidez e prévia

A revisão posterior dos slots identificou uma diferença funcional concreta:
o protótipo desenha cada posição com `PanelButton`, que tem `metal-weave.svg` por
padrão; o `Bevel` da posição nativa não recebia essa textura. Agora o slot recebe
o mesmo tecido quando contém um item e fica liso quando vazio. Não houve alteração
da arte aprovada, das medidas ou do relevo; pressionar continua usando o estado
do provedor nativo.

O ensaio `/tmp/irix-domainos-tray-texture-native-r2/RESULTADO.json` passou 28/28,
sem diagnósticos QML. Comparou pixels do fundo ocupado com um `PanelButton` de
referência, confirmou cinco vazios lisos, removeu e reapresentou um SNI próprio,
clicou fisicamente nele e recebeu seu callback `Activate`. Também verificou
pressão/soltura e habilitar/desligar os hints nativos. As imagens `occupied.png`,
`vacant.png`, `pressed.png`, `released.png` e `native-tooltip.png` estão nessa saída.

A comparação em 971 × 109 encontrou zero diferenças em 13.147 pixels das regiões
apontadas: chapa, botão de aplicativos e luz. Os ensaios em software e OpenGL,
incluindo deslocamento de meio pixel e duas escalas adicionais, não reproduziram
interpolação nessas regiões. A imagem aprovada não foi redesenhada para tentar
corrigir uma divergência ainda não reproduzida.

Evidências: `/tmp/irix-domainos-metal-analysis-r1/RESULTADO.json` e
`/tmp/irix-domainos-metal-analysis-gpu-r1/SCALE-RESULTADO.json`.

O pacote seguinte, `/tmp/irix-domainos-teste-pacote-r8-defaults`, contém também a
correção de minimização, os resets e a lista visual de organização da bandeja.
Sua integridade e os dois verificadores de dependências passaram 3/3:
`/tmp/irix-domainos-teste-pacote-r8-defaults/VERIFICACAO.json`.
A prévia `/tmp/irix-domainos-teste-uid1000-20261009-defaults-r8` passou 11/11
verificações de inicialização e 9/9 do Pager. O Xephyr mostra a referência acima
e o painel funcional abaixo; fechar sua janela externa encerra seus processos.
Ícones públicos são entradas de leitura ligadas ao pacote anterior; não foram
duplicados nem alterados. Os snapshots anteriores e o backup de Downloads
permanecem intactos. O script
`/tmp/irix-domainos-teste-real --verificar` apenas verifica o novo pacote; sua
execução normal instala recursos no próprio perfil e abre uma janela independente.
Nenhum desses comandos substitui automaticamente o painel ativo.

A instalação dos quatro recursos anteriores à correção da textura no perfil lsi passou 5/5 em
`/tmp/irix-domainos-instalacao-lsi-20261009-r12-defaults/RESULTADO.json`.
Os destinos correspondem às fontes, o recibo contém somente destinos autorizados
desse perfil e as oito configurações pessoais mantiveram seus hashes. Não houve
ativação, substituição de painel, chamada de sessão ou atualização de caches.

## Entrega da textura e prévia R9

O snapshot seguinte é `/tmp/irix-domainos-teste-pacote-r9-tray-texture`, com 3/3
verificações de integridade e dependências. O applet corresponde às fontes atuais;
os recursos que não mudaram são entradas de leitura para os snapshots anteriores.
Os dois comandos públicos em `/tmp` apontam para R9. A atualização do perfil lsi
passou 5/5 em
`/tmp/irix-domainos-instalacao-lsi-20261009-r13-tray-texture/RESULTADO.json`,
preservando os hashes das oito configurações pessoais e sem ativação de tema.

A prévia atual está em
`/tmp/irix-domainos-teste-uid1000-20261009-tray-texture-r9-r3`.
Passou 11/11 verificações de inicialização e 9/9 do Pager. Sua captura
`PREVIA-FUNCIONAL.png` mostra o volume sobre o tecido e as outras cinco posições
lisas, ao lado da referência aprovada. O cache deste ensaio fica num diretório
privado novo de `~/.cache`, pois `/tmp` atingiu seu limite de inodes. HOME,
configuração, barramento e runtime continuam próprios do ensaio. O driver
temporário acrescentou somente campos diagnósticos ao observador e redirecionou
somente o cache; `ONE-OFF-CACHE-QA.json` comprova que o bundle permaneceu intacto.

As duas tentativas anteriores R9 permanecem registradas: a primeira parou ao
observar a tarefa C depois de mudar para a área 2; sem os campos diagnósticos
novos, sua causa não foi determinada. Nessa tentativa também mudou o hash do
`plasma-org.kde.plasma.desktop-appletsrc` pessoal durante o intervalo; não foi
atribuída uma causa nem restaurado esse arquivo. A segunda encerrou por falta
de inodes e conservou os quatro hashes pessoais. A terceira passou sem mudanças
nas fontes do painel ou nos critérios do teste e conservou os quatro hashes.
Os processos das tentativas encerradas pararam; somente seus caches recomputáveis
foram removidos. A nova janela foi deixada aberta para avaliação manual.

O compartilhamento de recursos na prévia portátil passou 22/22 verificações em
`/tmp/irix-domainos-linked-resource-qa-RESULTADO.json`. Ele só ocorre depois da
validação completa do manifesto; a execução a partir do checkout continua copiando
seus recursos. Decoração com metadados ajustados, configurações gerais e runtime
permanecem privados.
