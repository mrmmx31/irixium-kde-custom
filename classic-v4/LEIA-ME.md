# Irixium — IRIX Classic v4

Decoração de janela independente para Aurorae / KDE Plasma 6, preparada para
aproximar a aparência das referências do IRIX fornecidas nesta conversa.
A base do projeto foi conferida no repositório `mrmmx31/irixium-kde-custom`,
commit `790fcbcb44c3ba05dbcc4114b473b9b875e30820`.

**Esta não é outra substituição de um componente de sistema.** É uma decoração
QML completa, em uma pasta de usuário própria. Ela pode coexistir com o Irixium
atual e com as modificações v1/v2/v3. Nenhum commit ou push é feito.

## O que foi reconstruído

O desenho da moldura, dos compartimentos, das divisórias e dos símbolos utiliza
uma grade comum de pixels e quatro cores. O estado ativo usa `#A59F80`,
`#000000`, `#DAD7CA` e `#5B5746`. O inativo usa `#808080`, `#000000`,
`#C6C6C6` e `#424242`, medidos na referência inativa fornecida.

Os mapas contêm somente o desenho da decoração. Não contêm pixels do conteúdo
dos aplicativos, do papel de parede, de textos dos títulos ou de fontes antigas.
Os pequenos SVGs de inspeção em `referencia-vetorial/` mostram os símbolos, mas o
tema em execução utiliza a mesma rotina Canvas para todos os elementos gráficos.

Na grade 1×:

| Elemento | Medida |
|---|---:|
| Símbolo de menu | 17 × 5 |
| Símbolo de minimizar | 5 × 5 |
| Símbolo de maximizar/restaurar | 15 × 17 |
| Bordas laterais e inferior | 8 |
| Altura total acima do aplicativo, janela normal | 32 |
| Faixa do título, sem a moldura superior externa | 24 |
| Início da caixa do texto, contado da esquerda da janela normal | 44 |

São dimensões do desenho, não tamanhos de todos os alvos clicáveis. As células
clicáveis são maiores que os símbolos. O minimizador pequeno realmente chama
Minimizar; ele não fecha a janela. Menu à esquerda e minimizar/maximizar à
direita são parte da disposição fixa desta decoração histórica. As entradas
globais `ButtonsOnLeft`/`ButtonsOnRight` não são reescritas.

O menu conserva as ações nativas do KWin, inclusive Fechar. A preferência
existente do KWin para fechamento por duplo clique no menu é consultada, não
alterada. O título continua submetido à política nativa de mover/redimensionar
e de duplo clique. Clique direito e central no maximizador são encaminhados ao
KWin, como no componente normal do Aurorae.

## Limite de fidelidade

O desenho estático foi reconstruído a partir dos pixels das imagens fornecidas.
O pontilhado é intencional. Foram incluídas duas fases para a extremidade direita
da barra, correspondentes às larguras pares e ímpares das referências.

**Não foi executada uma sessão real de Qt Quick/KWin durante a preparação.**
Testes do instalador, da geometria e do rasterizador não substituem o teste da
integração, dos eventos do mouse e do compositor. Começa pela miniatura na tela
de Decorações de janelas e aplica somente se ela carregar corretamente.

A tipografia usa Nimbus Sans em negrito itálico, 14 pixels, como aproximação.
Não há fonte proprietária do IRIX neste pacote e não há garantia de identidade
dos glifos. Não são alteradas fontes globais, configurações de antialiasing,
resolução ou escala do monitor.

As referências não mostram todos os estados pressionados ou a janela
maximizada. Nesses estados, o pacote faz uma adaptação coerente: mesma paleta,
relevo invertido e deslocamento de um pixel no clique; mesma faixa de título ao
maximizar, sem a moldura externa. O grande quadrado permanece como símbolo de
maximizar/restaurar. Não se alega que esses estados foram copiados de um IRIX em
execução.

## Instalar sem trocar imediatamente o tema

Extraia o ZIP. Abra um terminal dentro de `irixium-classic-v4` e execute:

```sh
bash instalar-v4.sh --verificar
bash instalar-v4.sh
```

**Use o usuário normal, sem sudo.** Nenhum arquivo de `/usr` é escrito e nenhuma
autorização administrativa é solicitada. A verificação confirma integridade do
pacote e presença das ferramentas e do módulo Aurorae/Qt 6 nos diretórios
usuais; ela não testa a renderização do QML.

A segunda chamada instala o tema, mas **não troca a seleção atual**. Nas
Configurações do Sistema, procure **Decorações de janelas**, reabra essa página
caso já estivesse aberta, e selecione:

> Irixium — IRIX Classic (v4)

Observe a miniatura e então clique em Aplicar. Não é preciso desinstalar v2/v3.
A instalação é feita em:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/kwin/decorations/irixium_irix_classic_v4/
```

Também existe a opção de instalar e selecionar pela linha de comando:

```sh
bash instalar-v4.sh --ativar
```

Feche a página de configurações antes dessa opção para ela não regravar uma
seleção antiga. Essa opção escreve apenas as chaves `library` e `theme` do grupo
`org.kde.kdecoration2` de `kwinrc` e solicita `reconfigure` por D-Bus quando
`qdbus6` está disponível. Não reinicia nem mata o KWin. Após uma edição posterior
de QML, pode ser necessário salvar o trabalho e entrar novamente na sessão por
causa do cache; não use `kwin --replace` para isso.

## Voltar ao estado anterior

Na mesma pasta extraída:

```sh
bash restaurar-v4.sh
```

O script restaura a última instalação feita por este pacote. Se o Classic ainda
estiver selecionado, restaura as chaves anteriores. Se outro tema já tiver sido
selecionado, não troca essa escolha. Outras chaves de `kwinrc` são preservadas.
Os arquivos das versões v1/v2/v3 e o Irixium original permanecem intocados.

Backups e recibos ficam em:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/irixium-classic-v4/backups/
```

Se a decoração tiver sido editada manualmente após a instalação, a remoção por
script é recusada para preservar as edições. Nesse caso, basta selecionar o
tema anterior pela interface. Mantenha o backup e o pacote até concluir os testes.
Uma segunda instalação cria outro backup; a restauração sempre corresponde à
última instalação, e não necessariamente ao estado anterior a todas elas.

## Escala e ajustes locais

O perfil padrão usa a grade 1×. Escala fracionária do monitor, DPI e o compositor
podem impedir que uma unidade lógica coincida com um pixel físico. O instalador
não modifica essas preferências do desktop. Para comparar pixel a pixel com as
capturas, use uma captura sem redimensionamento e considere a escala efetiva.

O arquivo que concentra ajustes intencionais é:

```text
contents/ui/Appearance.qml
```

`pixelScale: 1` reproduz o tamanho básico. `2` ou `3` amplia a grade por um fator
inteiro sem mudar a proporção entre o pequeno minimizador, os compartimentos e
a moldura. `titleFamily`, `titlePixels`, `titleItalic` e `titleBold` afetam somente
o texto nesta decoração. Edite a cópia instalada após guardar uma cópia dela;
a validação do instalador recusa arquivos do pacote alterados sem atualizar o
manifesto. O limite do título é 10–18 pixels antes da ampliação.

## O que não está neste escopo

O interior do Konsole, abas, barras de ferramentas, menus dos aplicativos,
Kvantum, GTK, painel, ícones do desktop e papel de parede não são alterados.
Esta revisão atua na decoração externa, incluindo a fonte do título local.

## Relação com o repositório atual

A pasta `kwin/decorations/irixium_irix_classic_v4/` pode ser versionada no teu
checkout em uma branch separada. O pacote contém o código-fonte completo.
O `update-irixium.sh` antigo continua instalando e selecionando o Irixium antigo:
ele pode mudar a seleção, mas não apaga esta decoração nova. Para usar novamente
o Classic, selecione-o na interface. Não é necessário alterar componentes QML
do sistema ou copiar novamente `MenuButton.qml`/`AuroraeButtonGroup.qml`.

## Testes e documentação

`VALIDACAO.md` descreve o que foi e o que não foi testado. As rotinas de teste
estão em `tests/`. O arquivo `PREVIA.png` é uma prévia técnica do desenho,
**não uma captura do KWin**. O texto dessa prévia foi rasterizado por Pillow e
não demonstra a renderização nativa da fonte no Qt.

A API foi conferida no código primário do KDE, ramo Plasma/6.3:

- `src/plugins/kdecorations/aurorae/src/aurorae.cpp`: descoberta de pacotes QML,
  `kwin/decorations/`, contexto `decoration`, seleção da decoração.
- `src/plugins/kdecorations/aurorae/src/qml/Decoration.qml`: bordas e dimensões.
- `src/plugins/kdecorations/aurorae/themes/plastik/package/contents/ui/main.qml`:
  configuração de bordas e `decoration.installTitleItem()`.
- `src/plugins/kdecorations/aurorae/src/qml/DecorationButton.qml`: ações dos botões.

Código de reconstrução e ferramentas: GPL-3.0-or-later; ver `LICENSE`.
IRIX/SGI são referências visuais e marcas de seus respectivos titulares.
Este pacote não é software oficial da SGI nem inclui binários ou fontes do IRIX.
