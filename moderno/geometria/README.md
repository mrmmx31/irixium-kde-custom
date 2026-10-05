# Irixium moderno — geometria organizada

**Revisão de teste: 1.0.0-rc1. Manutenção: `mrmmx31`.**

Atualização pontual da decoração Aurorae SVG **Irixium**. Preserva seus desenhos,
estados de hover/pressão, fontes, cores, tamanhos dos botões, funções e disposição
escolhida no KWin. Não converte o tema moderno em IRIX Classic e não instala outra
entrada na lista de decorações.

## O que muda

No perfil padrão, em unidades lógicas e com tamanho de botão normal:

| Medida | Antes | Depois |
|---|---:|---:|
| Área de cada botão | 22 × 22 | 22 × 22 |
| Espaçamento entre as áreas dos botões | 4 | 6 |
| Espessura de cada divisória | 2 na sobreposição v2 | 2 |
| Folga de cada lado de uma divisória entre botões | 1 | 2 |
| Altura das divisórias na janela normal | 26 na v2 | 26 |
| Altura das divisórias na janela maximizada | 33 na v2 | 26 |
| Distância entre divisória terminal e caixa do título | 2 na v2, sem TitleBorder personalizado | 8 |
| Margem externa esquerda/direita dos botões, janela normal | 11 / 11 | 9 / 9 |
| Margem externa esquerda/direita dos botões, maximizada | 6 / 6 | 6 / 6 |
| Altura total acima do aplicativo, normal / maximizada | 34 / 34 | 34 / 34 |
| Posição vertical dos botões, normal / maximizada | 9 / 6 | 9 / 6 |

A folga horizontal passa a ser `2 + divisória de 2 + 2 = 6`. A faixa útil tem 26
unidades e contém a face de 22 com duas unidades acima e abaixo. O desenho e a
área clicável não são redimensionados. O título ganha a mesma distância de
segurança em ambos os lados; a centralização vertical que já funcionava é mantida.

Os cortes da moldura são recalculados junto com as divisórias terminais, mantendo
o espelhamento dos cantos. Controles ocultos pelo Aurorae não deixam divisórias
órfãs. O maximizador é identificado pela entrada configurada, não por uma
propriedade ausente no seu invólucro. Espaçadores explícitos não ganham um símbolo
nem uma divisória própria. As duas cores de relevo da sobreposição v2 são mantidas.

### Por que TitleHeight muda sem a barra encolher?

O Aurorae soma a altura interna às margens superior e inferior. O novo perfil usa
`TitleHeight=26`, `TitleEdgeTop=7` e `TitleEdgeBottom=1`: `26 + 7 + 1 = 34`.
Maximizada, usa `4 + 26 + 4 = 34`. O centro do texto e o centro dos botões continuam
nas mesmas coordenadas do perfil anterior. A margem inferior negativa deixa de
ser necessária. Consulte `docs/GEOMETRIA.md` para os cálculos.

## O que não é modificado

Não há cópia ou alteração de `MenuButton.qml`, `applications.png`, `close.svg`,
`minimize.svg`, `maximize.svg`, `restore.svg` ou `decoration.svg`. Não se alteram
`ButtonsOnLeft`, `ButtonsOnRight`, as cores dos títulos, o fechamento por duplo
clique, a escala do monitor, o KWin selecionado, as fontes globais ou os temas GTK.
Os arquivos e o comportamento da **IRIX Classic** permanecem intactos.

Esta revisão não recupera desenhos antigos nem modifica efeitos de interação.
Mantém os SVGs instalados, inclusive uma eventual adaptação do minimizador já
aplicada anteriormente. Não afirma corrigir outros comportamentos dos controles.

## Instalação local

**É um complemento:** o Irixium moderno e o módulo Aurorae/Qt 6 devem estar
instalados. Extraia este pacote numa pasta de trabalho, fora do tema instalado.
Abra um terminal dentro da pasta `irixium-moderno-geometria`:

```sh
bash instalar.sh --verificar
bash instalar.sh
```

Use o usuário normal, **sem sudo na frente**. A verificação não escreve arquivos,
não cria backup e não ativa outro tema. A instalação altera exatamente:

1. O `Irixiumrc` na pasta de usuário `aurorae/themes/Irixium/` — somente as chaves
   geométricas listadas em `tools/layout.py`; as outras entradas são preservadas.
2. O `AuroraeButtonGroup.qml` do módulo Aurorae/Qt 6 instalado no sistema — a cópia
   solicita autorização por `pkexec` ou, na ausência dele, `sudo`.

No Debian amd64, o segundo arquivo costuma estar em:

```text
/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml
```

O arquivo é compartilhado pelo Aurorae, mas o novo posicionamento e o desenho das
divisórias só são habilitados para um caminho que termine exatamente em
`/Irixium/decoration.svg` ou `.svgz`. Os demais temas conservam as expressões de
espaçamento e posição originais. A IRIX Classic independente não utiliza esse
componente. Como qualquer substituição de arquivo de pacote do sistema, uma
atualização do KDE pode sobrescrevê-lo; uma versão desconhecida não será forçada.

São reconhecidas a base Plasma 6.3 e as sobreposições de divisórias v1/v2 desta
customização. Código desconhecido é recusado antes da escrita. Botões com tamanho
ou largura individual personalizados e outra altura de título são recusados para
não alterar proporções deliberadamente escolhidas sem revisão.

**Depois de instalar, salve o trabalho, encerre a sessão KDE e entre novamente.**
Não há reinício forçado do KWin. Se estiver usando IRIX Classic, ela continua
selecionada: troque manualmente para **Irixium** para testar o moderno. Não é
necessário reinstalar a Classic nem executar o instalador antigo do repositório.

`aurorae/Irixium/Irixiumrc` neste ZIP é o perfil completo sobre a base publicada,
para inspeção. O instalador mescla apenas a geometria na cópia local: não substitua
seu arquivo inteiro por esse exemplo caso tenha cores ou preferências diferentes.

## Restauração

Na mesma pasta do pacote:

```sh
bash restaurar.sh --verificar
bash restaurar.sh
```

Depois, encerre a sessão e entre novamente. O recibo restaura os dois arquivos ao
estado anterior à atualização. Não interfere na seleção da decoração.

Backups privados e recibos ficam em:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/irixium-moderno-geometria/backups/
```

A restauração recusa apagar edições posteriores ou substituir um QML atualizado
pelo KDE. Em caso de operação interrompida, execute `bash restaurar.sh --recuperar`.
A recuperação só aceita os conteúdos anteriores ou novos conhecidos pelo recibo;
conteúdo desconhecido exige revisão manual. Mantenha o ZIP e os backups até testar.

## Integração no repositório

Para preparar os arquivos num **checkout local**, sem commit/push e sem instalar:

```sh
python3 integrar-repositorio.py /caminho/irixium-kde-custom --verificar
python3 integrar-repositorio.py /caminho/irixium-kde-custom
```

O utilitário:

- Mescla somente a geometria em `aurorae/Irixium/Irixiumrc`.
- Adiciona o pacote em `moderno/geometria/` e uma chamada a ele no final do
  `update-irixium.sh`. Esse fluxo passa a recusar execução direta como root antes
  de iniciar, solicitando as autorizações pontuais como usuário normal.
- Guarda os originais alterados dentro do diretório privado `.git`, não na árvore
  publicável. Recusa substituir uma pasta `moderno/geometria` com conteúdo diferente.

Revise com `git diff` e `git status` antes de versionar. A configuração de autor de
commits não é modificada. A identificação pública deste pacote é `mrmmx31`.

**Atenção:** o instalador antigo continua tendo suas próprias ações de fontes,
seleção e disposição dos botões; este integrador não as remove nem as redefine.
Para testar apenas esta correção, use `instalar.sh` deste pacote, não o fluxo antigo.

## Testes e limites

```sh
bash testar.sh
bash testar.sh --qml
```

A primeira opção executa Python/Node com arquivos temporários e modelos da lógica.
A segunda exige `qmltestrunner` do Qt 6 e exercita a geometria Qt Quick com objetos
KDE simulados. Não executa ações reais de janela. Ferramenta ausente retorna 77,
não sucesso. Dependências não são instaladas automaticamente.

**Não houve carregamento real desta revisão no KWin neste ambiente.** A evidência
executada e o roteiro local constam de `docs/VALIDACAO.md`. As medidas são do perfil
normal em escala 100%; não representam uma promessa de identidade de pixels em
escala fracionária ou com outro tamanho de botão. Esta é uma candidata de teste.

## Origem e licenças

Base: `mrmmx31/irixium-kde-custom`, commit
`790fcbcb44c3ba05dbcc4114b473b9b875e30820`, e código do KDE Plasma 6.3.
Os desenhos Irixium de Phob1an não foram redesenhados ou incluídos neste complemento.
O componente derivado de KDE usa GPL-2.0-or-later; as novas ferramentas usam
GPL-3.0-or-later. Textos das licenças estão em `LICENSES/`. Créditos de terceiros
foram preservados. Não há arquivos de fonte no pacote.
