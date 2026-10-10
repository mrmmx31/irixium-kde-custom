# Decorações de janelas

As três opções associadas ao Irixium moderno ficam disponíveis no repositório
como pacotes independentes. O instalador da suíte instala todas; o perfil
`moderno` continua selecionando `irixium_modern`.

| Opção no KDE | Pacote | ID e diretório em `~/.local/share/kwin/decorations/` |
| --- | --- | --- |
| Irixium Moderno | `modern/package` | `irixium_modern` |
| Irixium 1.3 (Aurorae) | `modern-13/package` | `irixium_modern_13` |
| Irixium 4.1 (Aurorae) | `modern-41/package` | `irixium_modern_41` |

Selecione a opção desejada em **Configurações do Sistema → Cores e temas →
Decorações da janela**. Todas apresentam menu de ações, minimizar e
maximizar/restaurar. As opções 1.3 e 4.1 não criam um botão fechar, mesmo que o
layout global do KWin contenha essa ação. O menu usa o ícone da aplicação e
abre o menu nativo do KWin ao soltar o botão esquerdo ou direito, sem timer.
O fechamento permanece disponível nas ações do menu e nos atalhos do KWin.
O pacote moderno existente mantém seus gestos próprios de menu.

As cópias 1.3 e 4.1 preservam todos os SVGs, PNGs, metadados, configurações e
licenças originais. Os arquivos `close.svg` continuam arquivados entre os
assets, sem uso no layout. `ORIGEM.json` registra os hashes de cada arquivo
importado; `MANIFEST.json` cobre o pacote instalável. Os metadados originais
ficam em `package/upstream/`, sem criar opções adicionais no catálogo do KDE.

A geometria segue os valores de cada arquivo `*rc` e o cálculo do
[Aurorae do KDE](https://develop.kde.org/docs/plasma/aurorae/), incluindo os
[limites nativos de largura de borda](https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/plugins/kdecorations/aurorae/src/lib/auroraetheme.cpp).
Por exemplo, `BorderLeft=80` da versão 4.1 é limitado a 6 no tamanho de borda
normal pelo Aurorae. Padding, espaçamento, larguras distintas de botões,
cores e estados ativos, inativos e maximizados pertencem a cada versão.
O preenchimento de cliente da prévia é limitado ao contrato da prévia do KDE,
como no pacote Moderno existente.

Para verificar integridade e renderização sem instalar ou alterar a sessão:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s decorations/tests -p 'test_*.py' -v
python3 decorations/tools/preview_modern_options.py --saida /tmp/irixium-opcoes-render
python3 decorations/tools/preview_native_kwin.py --saida /tmp/irixium-opcoes-kwin
```

As pastas de saída precisam ser novas. As prévias usam PyQt6, QtQuick, KSvg,
Kirigami e, na segunda ferramenta, o módulo de prévia KDecoration3. Elas
carregam os arquivos reais e salvam imagens e relatórios JSON; seus caches,
configurações e cópias temporárias ficam sob `/tmp`. A segunda prévia carrega
os três `main.qml` pelo plugin `org.kde.kwin.aurorae`, sem trocar a decoração
da sessão ou instalar arquivos no perfil real.

## DomainOS SR10.4

`domainos/package` fornece a opção **DomainOS SR10.4**, com ID
`domainos_sr104`, em paralelo ao IRIX Classic. A referência visual é a imagem
do [VUE no Domain/OS SR10.4, do Virtual OS Museum](https://virtualosmuseum.org/images/more_screenshots/Domain_OS%20SR10.4%20-%2001%20VUE%20desktop.png).
O desenho considera somente SR10.4. Nenhuma captura de SR10.4.1 ou de outras
versões participa desta adaptação.

O catálogo `components.json` inclui o pacote para instalação pela suíte.
Os perfis globais Classic e Moderno conservam suas decorações atuais; instalar
esta opção não seleciona o DomainOS e não altera o layout dos botões do KWin.
`domainos/MANIFEST.json` verifica a integridade do pacote antes da instalação.

Para instalar somente esta decoração, execute como usuário normal:

```sh
python3 tools/install_domainos_decoration.py --verificar
python3 tools/install_domainos_decoration.py
```

O destino é `$XDG_DATA_HOME/kwin/decorations/domainos_sr104`, normalmente
`~/.local/share/kwin/decorations/domainos_sr104`. Depois, selecione
**DomainOS SR10.4** em **Configurações do Sistema → Cores e temas → Decorações
da janela**. O instalador não aplica o tema, reinicia o KWin ou atualiza as
configurações de outros usuários.

A instalação mantém um backup independente em
`$XDG_STATE_HOME/irixium-domainos-decoration`, normalmente
`~/.local/state/irixium-domainos-decoration`. Para conferir e restaurar o último
backup desta instalação:

```sh
python3 tools/install_domainos_decoration.py --restaurar --verificar
python3 tools/install_domainos_decoration.py --restaurar
```

A restauração verifica se houve edições posteriores no pacote instalado antes
de substituir arquivos. Ela restaura somente esse pacote; a opção selecionada
no KDE continua sendo uma preferência do usuário.
