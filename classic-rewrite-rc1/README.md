# IRIX Classic

Reescrita consolidada da decoração de janela desenvolvida a partir das referências
IRIX fornecidas por Máximo. **Revisão candidata: 1.0.0-rc1.** O nome exibido no KDE
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

Apenas seis propriedades literais são migradas de `Appearance.qml` /
`InteractionSettings.qml` ou do `Settings.qml` da revisão consolidada:
`pixelScale`, `titleFamily`, `titlePixels`, `titleItalic`, `titleBold` e
`menuOpensOnPress`. Expressões QML arbitrárias nesses valores são recusadas em vez
de executadas ou interpretadas parcialmente. Outros arquivos personalizados da
instalação antiga ficam no backup, mas são substituídos pela nova base.

A partir desta revisão, ajuste `contents/ui/Settings.qml` na cópia instalada.
O perfil admite ampliação inteira 1/2/3 e fonte entre 10 e 18 pixels antes da
ampliação. Alterar o payload extraído do pacote exige regenerar o manifesto de
desenvolvimento; o instalador detecta alterações acidentais. O manifesto não é
uma assinatura criptográfica de origem.

## Menu nativo: limite que permanece explícito

O menu é solicitado ao pressionar, com o retângulo do botão passado ao KWin.
A decoração não recria o conteúdo do menu e não modifica sua política global de
duplo clique. O evento de duplo clique, **quando entregue pelo KWin**, só pede
Fechar se a preferência global permitir e se a janela for fechável.

O popup é nativo: pode assumir a captura do ponteiro. Não há uma notificação
pública de abertura/fechamento do menu da janela usada por esta implementação,
por isso não inventamos um estado "menu aberto" nem um timer que finja mantê-lo
pressionado. O desenho acompanha a pressão/cancelamento efetivamente recebidos.
A seleção por pressionar–arrastar–soltar e o duplo clique com o popup precisam
ser confirmados na sessão real. **Não são anunciados como equivalentes integrais
ao dtwm.** `menuOpensOnPress: false` oferece uma alternativa local na soltura,
sem mudar as preferências do KDE.

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
