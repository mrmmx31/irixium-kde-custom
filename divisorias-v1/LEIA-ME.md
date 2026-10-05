# Irixium — divisórias dos botões e cortes nos cantos (v1)

Pacote complementar para o Irixium já instalado. Referência do tema:
`mrmmx31/irixium-kde-custom`, branch `master`, commit
`6f12fdc3325c331fe00e54419e9068aac2f3c459`.

**Não é o tema completo. Não executa `update-irixium.sh`, não altera o GitHub e
não substitui os teus SVGs, `MenuButton.qml`, `applications.png`, fontes,
ordem dos botões, GTK, Kvantum ou configurações do painel.**

## Alterações

`AuroraeButtonGroup.qml` recebe uma camada puramente decorativa: divisórias
verticais em duas cores, após os botões da esquerda e antes dos botões da
direita; oito cortes curtos que delimitam os quatro cantos da moldura; cores
ativas e inativas distintas. Os cortes externos ficam ocultos ao maximizar.
A camada não acrescenta capturadores de mouse, atalhos ou ações dos botões.

A sobreposição é habilitada somente quando `auroraeTheme.decorationPath`
corresponde a `.../Irixium/decoration`, `.svg` ou `.svgz`. Não é habilitada para
uma pasta com outro nome, como `Irixium-Copy`.

O arquivo QML é baseado no componente do KDE Plasma 6.3. Sua lógica original
de construção dos botões e suas margens permanecem intactas. No repositório
informado, esse arquivo ainda não existia: ele é um **novo arquivo a versionar**
e uma versão modificada de um componente instalado no sistema.

`aurorae/Irixium/Irixiumrc` muda apenas `ActiveTextColor` e
`InactiveTextColor` para preto, como na captura de referência do IRIX.
A fonte escolhida pelo usuário não muda. A instalação pode manter as cores
anteriores com `--manter-cor-titulo`.

Por que não aumentar os SVGs dos botões? A camada separada permite manter os
símbolos, os estados de hover/pressionado e suas caixas de 22 × 22 sem esticá-los.
Os SVGs da moldura também permanecem intactos: os cortes são desenhados sobre
ela, sem depender do esticamento ou repetição de uma peça do FrameSvg.

## Instalação

Extraia o ZIP e abra um terminal dentro da pasta `irixium-divisorias`.
Execute **como teu usuário normal, sem sudo**:

```sh
bash instalar-divisorias.sh --verificar
```

A verificação apenas compara a base do QML e confere a configuração. Não cria
backups nem escreve arquivos e **não equivale a carregar o QML no KWin**.
Se terminar sem erro:

```sh
bash instalar-divisorias.sh
```

Será solicitada autorização administrativa para copiar o QML do sistema,
por `pkexec`, ou por `sudo` quando `pkexec` não estiver instalado.
**Salve o trabalho, encerre a sessão do KDE e entre novamente.** O instalador
não reinicia o KWin, não encerra programas e não força o logout.

Para aplicar somente as divisórias/cantos, mantendo a cor atual do título,
use este comando no lugar da instalação padrão:

```sh
bash instalar-divisorias.sh --manter-cor-titulo
```

O programa procura automaticamente o componente Qt 6. No ambiente x86_64
informado, o caminho esperado é:

```text
/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml
```

É possível especificar outra pasta Qt 6 com `--qml-dir DIRETORIO`.
O tema é localizado por `XDG_DATA_HOME`, ou em
`~/.local/share/aurorae/themes/Irixium/` quando a variável não está definida.

## Proteção das personalizações

O instalador só aceita o componente-base incluído em `upstream/`, tolerando
linhas vazias e diferenças de fim de linha/espaços finais, ou o próprio
componente já modificado deste pacote. Se encontrar outra lógica, interrompe
antes de escrever qualquer arquivo. Não force uma versão diferente do KDE.

O `Irixiumrc` instalado **não é substituído integralmente**: o instalador
atualiza apenas as duas entradas de cor em `[General]`. O restante do arquivo,
inclusive ajustes locais posteriores ao commit de referência, é preservado.
A cópia completa incluída no pacote serve para revisão e versionamento.

A geometria registrada no repositório permanece:

```ini
TitleHeight=34
ButtonWidth=22
ButtonHeight=22
ButtonMarginTop=6
ButtonMarginTopMaximized=6
ButtonSpacing=4
```

O programa não escreve em `kwinrc` ou `kdeglobals`. Portanto, não altera
`ButtonsOnLeft=M`, `ButtonsOnRight=HXA`, fontes ou antialiasing.
A personalização global de `MenuButton.qml` já existente no teu projeto não
é modificada; a restrição ao Irixium refere-se à nova camada deste pacote.

## Backup e restauração

Antes de alterar arquivos, é criado um backup com os conteúdos anteriores e
um manifesto de caminhos e hashes em:

```text
~/.local/state/irixium-divisorias/backups/
```

`XDG_STATE_HOME` é respeitado quando definido. O arquivo `latest` aponta para
o último backup concluído. Uma instalação sem mudanças não substitui esse
registro nem cria outro backup.

Para conferir a restauração sem executá-la:

```sh
bash restaurar-divisorias.sh --verificar
```

Para restaurar o estado anterior:

```sh
bash restaurar-divisorias.sh
```

Depois, encerre a sessão e entre novamente. Um backup específico pode ser
selecionado com `--backup CAMINHO_DO_BACKUP`.

A restauração automática é recusada se um arquivo que seria restaurado tiver
mudado depois da instalação, evitando apagar uma edição posterior ou
reverter silenciosamente uma atualização do KDE. Os backups não são apagados.
Em caso de falha, o programa informa o caminho do backup e se foi necessária
recuperação manual.

Se a interface não permitir abrir um terminal, o script de restauração pode
ser iniciado por um terminal virtual, após login com o mesmo usuário.
Não remova a pasta extraída nem o backup antes de validar o resultado.

## Teste visual necessário

Esta é uma versão para teste local. O ambiente de preparação não tinha uma
sessão KWin/Plasma 6 nem Qt 6 para compilar/carregar o componente. Não há
certificação de execução no teu desktop. Veja `VALIDACAO.md` para distinguir
os testes automatizados efetuados do teste gráfico ainda necessário.

Confira a mesma janela normal e maximizada, ativa e inativa; passe o mouse
sobre os botões e clique neles; observe os quatro cantos e redimensione a
janela. Confirme também que a área central do aplicativo não recebeu desenhos.

A moldura foi tratada como uma faixa de sete unidades lógicas, correspondente
ao tema de referência com bordas normais. Os marcadores dos cantos ficam
ocultos em bordas mais finas ou janelas pequenas demais. Em escala fracionária,
a nitidez final de linhas de uma unidade lógica deve ser verificada na tela.

## Repositório e atualizações do KDE

O `update-irixium.sh` original não é alterado nem executado por este pacote.
Para persistir esta versão, os arquivos do pacote podem ser versionados numa
branch de trabalho do teu repositório. Revise o diff antes de integrar.

Após uma atualização do KDE que substitua o componente do sistema, execute
novamente a verificação e a instalação deste pacote. Se a base mudar, será
necessário adaptar o QML antes de reaplicar; não copiar uma versão antiga
sobre uma nova à força.

Se mantiveres o `Irixiumrc` branco no repositório e rodares o instalador antigo,
ele poderá restaurar essa cor. Copiar a versão preta para a branch do tema ou
reexecutar este instalador resolve essa divergência. Não se trata de uma
sincronização automática do teu GitHub.

## Arquivos do pacote

| Arquivo | Finalidade |
|---|---|
| `AuroraeButtonGroup.qml` | Componente com a sobreposição de divisórias e cantos. |
| `aurorae/Irixium/Irixiumrc` | Configuração do commit de referência, com títulos pretos. |
| `instalar-divisorias.sh` | Entrada para verificação e instalação. |
| `restaurar-divisorias.sh` | Entrada para restauração do backup. |
| `irixium_install.py` | Implementação do instalador, apenas biblioteca padrão Python 3. |
| `upstream/` | Referências anteriores para comparação, não destinos de instalação. |
| `DIFERENCAS.diff` | Diff de revisão dos dois arquivos principais. |
| `tests/test_package.py` | Testes isolados em diretórios temporários. |
| `VALIDACAO.md` | Resultados e limites da validação. |
| `ORIGEM.json`, `SHA256SUMS` | Proveniência e integridade dos arquivos. |

## Licenças e fontes

O componente-base do Aurorae mantém o crédito a Martin Gräßlin e a licença
GPL-2.0-or-later. A nova sobreposição e os scripts seguem GPL-2.0-or-later.
O Irixium de referência credita Phob1an; o repositório de personalizações é
de `mrmmx31`. Cópias das licenças GPL 2 e GPL 3 estão em `LICENSES/`.
Nenhuma fonte tipográfica é distribuída neste pacote.

Fontes consultadas:

- Tema: https://github.com/mrmmx31/irixium-kde-custom/tree/6f12fdc3325c331fe00e54419e9068aac2f3c459
- Grupo dos botões: https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/AuroraeButtonGroup.qml
- Composição da decoração: https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/aurorae.qml
- Qt Quick Item: https://doc.qt.io/qt-6/qml-qtquick-item.html
- Qt Quick Repeater: https://doc.qt.io/qt-6/qml-qtquick-repeater.html
