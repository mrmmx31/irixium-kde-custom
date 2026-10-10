# Irixium / IRIX Classic / DomainOS SR10.4 — distribuição gráfica

Esta distribuição disponibiliza três temas globais e os 40 componentes do
catálogo `components.json`. Extraia o arquivo e execute os comandos abaixo
dentro da pasta `irix-suite-1.1.0-beta.2`, como seu usuário normal, sem `sudo`.

## Requisitos

Requer GNU/Linux x86_64, KDE Plasma 6 com Qt 6.8 ou superior, Aurorae, KSvg,
KSystemStats, Kvantum Qt 6 e GTK Config do KDE. As pontes usam PyQt6
QtCore/QtDBus/QtGui e Pillow do Python da distribuição em `/usr/bin/python3`.
GTK 2 usa o engine pixmap instalado pela distribuição. Aplicativos libadwaita
ou com estilos próprios podem controlar sua aparência.

O módulo nativo do painel já está incluído; esta distribuição não exige
compilador nem SDK de desenvolvimento. A arquitetura e a ABI das bibliotecas
Qt/C++ precisam ser compatíveis com o módulo. O instalador verifica as
dependências e o manifesto nativo antes de instalar; não instala pacotes de
sistema. Incompatibilidade exige um pacote construído para a plataforma.

## Instalar e escolher um tema

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
```

Instalar acrescenta opções e guarda backups. Não escolhe um tema, substitui o
painel ativo nem cria áreas de trabalho. A instalação registra a seleção atual
como referência para as pontes; escolhas independentes são preservadas.

Depois, escolha um dos três temas em Configurações do Sistema → Tema global,
ou aplique explicitamente um perfil:

```sh
bash aplicar-tema.sh classic
# Alternativas: moderno ou domainos
```

A aplicação seleciona decoração, Plasma Style, Kvantum, GTK, ícones, cursores,
cores e splash do perfil. Escolher DomainOS autoriza a migração de um painel,
com backup; voltar ao Global Classic ou Moderno recupera o painel anterior.
Perfis com vários painéis exigem indicar qual painel deve ser migrado. Não há
reset geral do layout nem alteração de outros usuários. O tema Wine fica
disponível como opção, sem modificar prefixos automaticamente.

Dentro da sessão KDE, a instalação inicia suas pontes locais. Se instalou fora
dela, execute depois no terminal da própria sessão:

```sh
python3 tools/theme_companion_bridge.py --instalar --iniciar
python3 tools/domainos_style_bridge.py --temas-globais --iniciar
```

## Cores e atualização

Ao trocar somente o esquema em Configurações do Sistema → Cores, aplique a
paleta atual também ao Kvantum:

```sh
python3 tools/apply_kvantum_colors.py
```

O script conserva os temas originais e gera variantes locais recuperáveis.
A ponte GTK acompanha as cores exportadas pelo GTK Config do KDE. Para escolher
explicitamente apenas a família GTK, preservando o restante:

```sh
python3 tools/select_gtk.py classic
# Alternativas: moderno ou domainos
```

Reabra os aplicativos para carregar recursos atualizados. Para liberar o QML
antigo de uma decoração na sessão KDE do próprio usuário:

```sh
python3 tools/reload_decoration.py
```

O comando preserva a seleção e não reinicia o KWin à força.

## Restaurar

Se ativou o painel DomainOS pelo Tema global e quer retirá-lo, escolha primeiro
o Global Classic ou Moderno. Para uma ativação manual, use
`python3 tools/activate_domainos.py --restaurar`. Depois confira e restaure os
arquivos instalados e, se desejado, a seleção de tema anterior:

```sh
bash instalar-irixium.sh --restaurar --verificar
bash instalar-irixium.sh --restaurar
bash aplicar-tema.sh --restaurar
```

Os recibos ficam em `XDG_STATE_HOME/irixium-suite` e
`XDG_STATE_HOME/irixium-selection`. A recuperação do painel tem recibos próprios
em `XDG_STATE_HOME/irixium-domainos-panel`. Edições posteriores são recusadas
para preservar alterações do usuário. A restauração de arquivos não apaga as
preferências criadas durante o uso. Veja `docs/INSTALACAO-RECUPERAVEL.md`.

Os componentes usam `XDG_DATA_HOME` e `XDG_CONFIG_HOME`; os defaults são
`~/.local/share` e `~/.config`. GTK 2 e cursores também recebem cópias de
compatibilidade em `~/.themes` e `~/.icons`. Nenhum caminho pessoal do autor é
necessário.

## Componentes opcionais

Os áudios SGI e seus instaladores não fazem parte desta distribuição gráfica.
A aplicação preserva os sons existentes quando o módulo opcional não está
disponível; `--sem-sons` também solicita essa preservação explicitamente.
`--exigir-sons` recusa a aplicação se não puder validar o conjunto de sons.
O checkout completo do projeto documenta a instalação separada dos sons.

Prévia Xephyr, ferramentas de desenvolvimento, testes e integrações opcionais
de aplicativos pertencem ao checkout completo. Este pacote contém os recursos
gráficos e os auxiliares de instalação, aplicação e recuperação descritos aqui.
O manual funcional do painel está em
`plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md`.
