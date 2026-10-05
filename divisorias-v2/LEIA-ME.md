# Irixium — divisórias v2

Correção da versão v1 entregue nesta conversa. Pacote complementar para o tema
Irixium/Aurorae do Plasma 6.3 analisado, com atualização direta da v1.
Não é um tema completo nem substitui o repositório irixium-kde-custom.

## Por que faltavam linhas na v1

1. O `AuroraeMaximizeButton.qml` do KDE tem um `Item` externo sem a propriedade
   `buttonType`. Essa propriedade existe nos botões internos. A v1 exigia
   `sourceButton.buttonType` para desenhar uma divisória e, por isso, excluía
   o compartimento de maximizar/restaurar.
2. A v1 exigia três bordas de pelo menos 7 unidades lógicas para mostrar qualquer
   corte dos cantos. No código do Aurorae, `BorderSize=Normal` limita as bordas
   laterais e inferior ao intervalo de 4 a 6. Assim, `BorderLeft=7` no rc se torna
   6 em execução e a condição da v1 fica falsa.

A v2 usa a entrada da disposição de botões para identificar cada compartimento
(incluindo maximizar/restaurar, excluindo espaços e botões invisíveis). Os cortes
usam separadamente a largura efetiva de cada borda, limitados à faixa do desenho,
e não exigem que todas as bordas tenham 7. O grupo fica acima da borda interna
para evitar que esta cubra o relevo. Nada disso acrescenta áreas de mouse.

## O que muda na instalação

Por padrão, **somente `AuroraeButtonGroup.qml`**. São preservados os SVGs, a imagem
`applications.png`, o teu `MenuButton.qml`, a disposição dos botões, os tamanhos,
as margens, a cor atual do título, as fontes e o restante do tema.

O efeito novo só é habilitado quando o caminho do SVG termina em
`/Irixium/decoration.svg`, `/Irixium/decoration.svgz` ou `/Irixium/decoration`.
Os cortes da moldura continuam ocultos com a janela maximizada. Isso é intencional;
as divisórias da barra de título permanecem.

A substituição do QML é feita no diretório do sistema, embora o desenho seja
condicionado ao Irixium. Uma atualização de pacotes do KDE pode substituir o
arquivo. Não aplique o patch à força em uma versão diferente do componente.

## Instalar sobre a v1

Não desinstale a v1 antes. Extraia o ZIP em uma pasta nova e abra o terminal
na pasta `irixium-divisorias-v2`. Não misture os arquivos com o ZIP antigo.

Verificação sem alterar arquivos ou criar backup:

```sh
bash instalar-divisorias.sh --verificar
```

Deve aparecer `Base reconhecida: Irixium divisórias v1`, ou a base original,
ou a v2 caso ela já esteja instalada. Se a base não for reconhecida, pare:
o instalador se recusa a sobrescrever uma customização desconhecida.

Instalação:

```sh
bash instalar-divisorias.sh
```

Execute como o usuário normal, **sem sudo na frente**. O script solicita pkexec
(ou sudo se pkexec não existir) apenas para a cópia do arquivo do sistema.
Python 3.9 ou posterior é necessário; o instalador usa apenas a biblioteca padrão.
Não é necessário instalar Node.js para aplicar ou restaurar o tema.

**Salve o trabalho, encerre a sessão do KDE e entre novamente.** Não basta abrir
outra janela. O instalador não mata/reinicia o KWin, não fecha aplicativos,
não apaga caches e não executa o `update-irixium.sh` do repositório.

## Reverter

Na pasta da v2:

```sh
bash restaurar-divisorias.sh --verificar
bash restaurar-divisorias.sh
```

Depois, encerre e entre novamente na sessão. O estado imediatamente anterior é
restaurado. Portanto, ao instalar por cima da v1, a primeira restauração retorna
à **v1**, não ao estado anterior a todas as personalizações.

Os backups ficam em `${XDG_STATE_HOME:-$HOME/.local/state}/irixium-divisorias/backups`.
O instalador guarda os bytes anteriores e um manifesto de integridade. A v2
preserva o encadeamento para o backup da v1 quando ele ainda está registrado.
Nesse caso, uma segunda restauração com a ferramenta da v2 pode retornar ao
estado anterior à v1. Para selecionar explicitamente um backup:

```sh
bash restaurar-divisorias.sh --backup /caminho/completo/do/backup --verificar
bash restaurar-divisorias.sh --backup /caminho/completo/do/backup
```

A restauração automática recusa sobrescrever um arquivo alterado posteriormente
ou atualizado pelo KDE. Guarde a pasta do pacote e seus backups. Não use um
instalador antigo sobre uma instalação v2.

## Opções adicionais

`--manter-cor-titulo`: preserva as cores; agora é o comportamento padrão.

`--titulo-preto`: opção explícita que muda somente `ActiveTextColor` e
`InactiveTextColor` na seção `[General]` do rc. Não é necessária para corrigir
as divisórias, nem para quem já aplicou a cor preta na v1.

`--qml-dir /caminho/do/diretorio`: informa a pasta Qt 6 quando a descoberta
não encontra um único componente. Use a pasta que contém
`AuroraeButtonGroup.qml`, não um diretório de Qt 5.

## Conteúdo

- `AuroraeButtonGroup.qml`: componente novo a instalar.
- `instalar-divisorias.sh`, `restaurar-divisorias.sh`, `irixium_install.py`: instalação,
  validação das bases, backup e restauração.
- `DIFERENCAS-v1-v2.diff`: mudanças em relação ao QML anterior.
- `DIFERENCAS-original-v2.diff`: mudanças em relação à base KDE analisada.
- `compatibilidade/v1/AuroraeButtonGroup.qml`: cópia exata usada para reconhecer a v1;
  **não é o arquivo a instalar**.
- `upstream/`: referências anteriores às personalizações.
- `referencia/Irixiumrc-v1`: referência das configurações da v1, não é substituído
  integralmente pelo instalador. Não o copie por cima de ajustes locais.
- `tests/`, `VALIDACAO.md`: testes e limitações da validação.
- `ORIGEM.json`, `SHA256SUMS`, `LICENSES/`: origem, conferência e licenças.

Nenhum SVG, fonte, screenshot pessoal ou dado da sessão está incluído no pacote.
Nenhum commit, branch ou Pull Request foi criado no repositório remoto.

## Conferência visual necessária

Na disposição atual com menu à esquerda e dois botões visíveis à direita,
verifique três separadores verticais: depois do menu, antes do primeiro botão
direito e entre os dois botões direitos. Na janela normal com bordas suficientes,
verifique oito cortes curtos (dois por canto). Bordas muito estreitas ou ausentes
não recebem cortes que invadam a área de conteúdo.

Confira janela normal/maximizada, ativa/inativa e o clique dos botões. As margens
verticais dos botões são as mesmas da v1. A espessura lógica das linhas continua
em 1 unidade para a parte clara e 1 para a escura; escala fracionária precisa de
verificação no compositor real.

## Validação e fontes

Leia `VALIDACAO.md`: os testes de expressões usam JavaScript real extraído do QML,
mas **não executam o Qt Quick nem uma sessão KWin**. O pacote não foi visualmente
validado no computador do usuário. A saída da v1 foi examinada nos prints recebidos.

Fontes técnicas primárias consultadas:

- KDE AuroraeMaximizeButton.qml (Plasma/6.3):
  https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/AuroraeMaximizeButton.qml
- KDE auroraetheme.cpp, método `AuroraeTheme::borders` (Plasma/6.3):
  https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/lib/auroraetheme.cpp
- KDE aurorae.qml, grupos de botões e borda interna (Plasma/6.3):
  https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/aurorae.qml
- Qt Row: https://doc.qt.io/qt-6/qml-qtquick-row.html

O cabeçalho de autoria e licença do KDE foi preservado. O QML e os scripts seguem
GPL-2.0-or-later; as referências do tema Irixium mantêm sua origem e licença,
conforme `LICENSES/` e o repositório de referência.
