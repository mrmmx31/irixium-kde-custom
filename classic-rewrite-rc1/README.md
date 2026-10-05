# IRIX Classic

Reescrita consolidada da decoração de janela desenvolvida a partir das referências
IRIX fornecidas por `mrmmx31`. **Revisão candidata: 1.0.0-rc3.** O nome exibido no KDE
é apenas **IRIX Classic**. Não se trata de uma release homologada em KWin.

## O que esta revisão faz

Preserva os mapas de pixels aprovados na v4 e a paleta ativa/inativa; reestrutura
geometria, desenho, entrada de mouse, ligação ao KWin e instalação. Um Canvas
compartilhado desenha moldura e símbolos na mesma grade. Os elementos de entrada
não criam superfícies gráficas individuais.

O perfil visual permanece: menu 17×5, minimizar 5×5, maximizar/restaurar 15×17,
borda 8, topo normal 32 e maximizado 24 unidades. São dimensões do desenho; os
alvos clicáveis são maiores. A escala da tela não é alterada. A fidelidade de
pixel pressupõe escala física inteira, especialmente 100%, como no teste que
normalizou as capturas do usuário. Fontes globais não são modificadas; a fonte
local continua sendo uma aproximação, não o arquivo original da SGI.

A interação não acrescenta destaque ao passar o ponteiro. A pressão inverte o
relevo do compartimento sem mover o símbolo nem impor duração artificial.
Minimizar/maximizar agem na soltura dentro do alvo; sair, voltar e soltar é aceito;
soltar fora cancela. Cancelamento do mouse, ocultação, redimensionamento e perda
da capacidade anulam a intenção de clique. A segunda pressão de um duplo clique
não é engolida inadvertidamente nos controles comuns.

Controles indisponíveis conservam a célula e ganham um desenho claro/escuro em
baixo-relevo. O evento é consumido, mas não encaminhado como ação nem como clique
na área de título atrás dele. A capacidade é novamente conferida no adaptador
KWin. Este desenho é uma adaptação explícita, não um estado IRIX comprovado por
captura. Janela inativa e operação indisponível são estados diferentes.

## Atualizar a Classic existente

Extraia o ZIP em uma pasta de trabalho, **fora da pasta instalada do tema**.
Abra o terminal na pasta `irix-classic` e execute, sem sudo:

```sh
bash instalar.sh --verificar
bash instalar.sh
```

A verificação não escreve arquivos e não carrega Qt Quick. Confere o conteúdo do
tema, as ferramentas KDE 6, o módulo Aurorae e o destino. Confirme o destino
impresso antes de instalar.

O instalador reutiliza o identificador Classic selecionado em `kwinrc`:
`irixium_irix_classic_v4`, `irixium_irix_classic_v5` ou `irix_classic`. Assim, quem
está usando v4/v5 recebe o novo código **no mesmo diretório**, com o nome visível
IRIX Classic. O sufixo antigo pode permanecer no caminho interno para manter
compatibilidade; ele não cria outra entrada na lista.

Se outra decoração estiver selecionada, mas houver uma única Classic instalada,
essa instalação é atualizada sem trocar a escolha atual. Se houver duas ou mais,
o script pede que seja selecionada a desejada ou informado `--destino`; não
adivinha qual cópia substituir. Apenas na primeira instalação sem nenhuma Classic
é utilizado o identificador `irix_classic`.

A troca de seleção só acontece com a opção explícita `--ativar`. Ao atualizar a
Classic já selecionada, ela naturalmente continuará selecionada, mas com novos
arquivos. **Salve o trabalho, encerre a sessão e entre novamente** para descartar
os componentes QML em cache. Não use `kwin --replace`.

Outras decorações v4/v5 que já existirem não são apagadas. Os antigos patches de
sistema v1/v2/v3 não são removidos nem reutilizados pelo código novo. Nenhum arquivo
em `/usr` é escrito, não há commit/push e nenhum serviço é reiniciado à força.

### Ajustes locais

Apenas sete propriedades literais são migradas de `Appearance.qml` /
`InteractionSettings.qml` ou do `Settings.qml` da revisão consolidada:
`pixelScale`, `titleFamily`, `titlePixels`, `titleItalic`, `titleBold`,
`menuOpensOnPress` e `menuDoubleClickClosesWindow`. Expressões QML arbitrárias
nesses valores são recusadas em vez de executadas ou interpretadas parcialmente. Outros arquivos personalizados da
instalação antiga ficam no backup, mas são substituídos pela nova base.

A partir desta revisão, ajuste `contents/ui/Settings.qml` na cópia instalada.
O perfil admite ampliação inteira 1/2/3 e fonte entre 10 e 18 pixels antes da
ampliação. Alterar o payload extraído do pacote exige regenerar o manifesto de
desenvolvimento; o instalador detecta alterações acidentais. O manifesto não é
uma assinatura criptográfica de origem.

## Menu e fechamento por duplo clique — correção rc2

Esta revisão corrige a disputa entre abrir o menu e reconhecer o segundo clique.
Na rc1 o menu era publicado na primeira pressão, antes de o segundo clique poder
chegar à decoração. Além disso, o fechamento dependia de uma preferência global
que o KWin considera desabilitada quando não configurada.

**Agora `menuDoubleClickClosesWindow: true` é uma preferência local da IRIX
Classic.** O instalador não grava `CloseOnDoubleClickOnMenu` no KDE e não altera
outras decorações. A operação continua condicionada a `decoration.client.closeable`
e chama `requestClose()`, não encerramento forçado do processo.

| Gesto no botão do menu, com o fechamento habilitado | Ação |
|---|---|
| Duplo clique esquerdo | Solicita Fechar, sem abrir o popup intermediário. |
| Clique esquerdo simples | Aguarda o intervalo de duplo clique do Qt após a soltura e abre o menu uma vez. |
| Clique direito | Abre o menu na pressão, no perfil padrão. |
| Pressionar e manter o esquerdo | Solicita o menu ao receber `pressAndHold` do Qt; não reabre na soltura. |
| Hover sem pressão | Nenhum efeito adicional. |

O pequeno atraso do clique esquerdo simples é intencional: o popup não deve
capturar o ponteiro enquanto um segundo clique ainda é possível. O intervalo vem
de `Qt.styleHints.mouseDoubleClickInterval`; a duração do gesto de manter
pressionado vem do Qt. **O temporizador não prolonga o efeito gráfico:** o relevo
volta ao normal na soltura, mesmo enquanto a ação simples está pendente.

Cancelamento, saída do botão enquanto o clique está pendente, ocultação, mudança
de geometria, perda de foco ou mudança de política anulam a ação pendente.
Acessibilidade e clique direito não deixam uma abertura esquerda pendente para
executar mais tarde. A ação de fechar só ocorre com o evento nativo de duplo clique
precedido de um clique esquerdo válido no mesmo controle.

## Ação imediata dos controles de janela

Os botões **Minimizar** e **Maximizar/Restaurar** solicitam a operação no evento
de pressão, como os controles nativos do KWin, em vez de aguardar a soltura do
ponteiro. Isso elimina o atraso perceptível entre clicar e iniciar a transição.
O botão do menu permanece com o fluxo próprio de clique simples/duplo clique,
incluindo a espera necessária para distinguir os dois gestos.

Para desabilitar esse atalho somente nesta decoração, edite na cópia instalada:

```qml
property bool menuDoubleClickClosesWindow: false
```

Nesse modo, `menuOpensOnPress` volta a determinar a abertura esquerda na pressão
ou na soltura. Com o fechamento habilitado, a espera do clique esquerdo prevalece
sobre `menuOpensOnPress`. A preferência local é preservada nas próximas atualizações.

**Limite de compatibilidade:** abrir o menu imediatamente na primeira pressão
esquerda e ao mesmo tempo depender de um segundo clique entregue ao QML não é a
estratégia usada nesta revisão. Ela prioriza o duplo clique funcional. O menu
continua pertencendo ao KWin; a seleção arrastada após manter pressionado e a
captura pelo popup precisam de validação em uma sessão real. Não se anuncia uma
reprodução integral dos grabs do CDE/Motif nem um estado persistente de popup
sem sinal do compositor. Os efeitos e a aparência estática permanecem os da rc1.

## Testes locais

Antes de atualizar, o código visual e de entrada pode ser exercitado com QtTest:

```sh
bash testar.sh --qml
```

Isso usa Qt 6 `qmltestrunner`, quando presente. **Testa Surface e ButtonInput, não
o menu nativo nem a classe C++ do KWin.** Ferramenta ausente é informada com código
77, não como sucesso. O pacote não instala dependências.

Após selecionar a decoração, duas janelas reais podem ser abertas com:

```sh
bash testar.sh --janelas
```

Uma tem tamanho fixo e não solicita maximização; a outra permite maximizar e
minimizar. O executor QML do Qt 6 é necessário apenas para esse auxiliar. Janelas
de aplicativos que já usa também servem ao roteiro em `docs/ACEITACAO.md`.

Para os testes de desenvolvimento Python/Node:

```sh
bash testar.sh
```

## Restauração

```sh
bash restaurar.sh
```

Restaura a última atualização desta base e, quando pertinente, as duas chaves de
seleção anteriores. Não sobrescreve outra decoração escolhida depois. Se houver
edições posteriores na pasta instalada, a restauração recusa apagá-las. O backup
é validado por hash antes de ser copiado. As operações de troca de diretório são
preparadas por staging/rename, com recibo e cópia completa anterior.

Backups privados e recibos ficam em:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/irix-classic/backups/
```

Uma interrupção entre etapas bloqueia nova atualização. Nesse caso:

```sh
bash restaurar.sh --recuperar
```

A recuperação só aceita os conteúdos conhecidos do recibo. Nenhuma técnica torna
a escrita de vários diretórios e a configuração do KWin uma única transação do
compositor; por isso o recibo de recuperação não é dispensado.

## Estrutura e escopo

- `package/contents/ui/Pixels.js`: mapas de referência preservados.
- `Geometry.js`: dimensões usadas tanto pelo desenho quanto pelos alvos.
- `Artwork.js` e `Surface.qml`: composição gráfica compartilhada e texto.
- `InputState.js` e `ButtonInput.qml`: máquina de estados e eventos Qt.
- `main.qml`: adaptação à API do KWin, capacidades e ações nativas.
- `Settings.qml`: preferências locais.
- `tools/manage.py`: identidade, staging, backup, migração e restauração.

O interior dos aplicativos, GTK, Kvantum, painel, wallpaper e ícones não são
alterados. O instalador antigo `update-irixium.sh` do repositório é outro fluxo:
ele pode selecionar o Irixium antigo e não deve ser confundido com esta atualização.
A pasta deste pacote pode ser versionada no checkout local; nada foi publicado
no GitHub nesta conversa.

Leia `docs/VALIDACAO.md`, `docs/CONTRATO.md` e `docs/FONTES.md` antes de considerar
esta candidata aprovada. Licença: GPL-3.0-or-later. Não inclui binários, código
privado ou arquivos de fonte do IRIX/SGI.

## Miniatura em Decorações de janelas (rc3)

O fundo da área de conteúdo da miniatura usa agora a cor `windowColor` fornecida
pelo PreviewItem do KWin. É opaco, sem copiar a cor da barra de título, e cobre a
miniatura de trás na área correspondente. A identificação exige o contrato do
objeto de prévia e a identidade da decoração; não usa nome do aplicativo, título
ou tamanho da janela.

Em janelas reais o preenchimento **não é criado**. A área cliente permanece a
cargo do aplicativo. Isso preserva inclusive transparência configurada no
terminal, cliques, duplo clique, estados desativados e o Application Style Kvantum.
O patch não define `alpha: false` e não altera cores globais.

A cor obtida é a da prévia do KCM: não é uma renderização do conteúdo de um
aplicativo nem do Kvantum de cada aplicação. Ela pode coincidir com a cor atrás
da miniatura; o critério é a opacidade na sobreposição, não uma cor artificial.

Veja `docs/PREVIA.md` para causa, fontes, teste local e limites. Os testes QML
adicionais rodam junto com `bash testar.sh --qml` quando QtTest 6 está instalado.
