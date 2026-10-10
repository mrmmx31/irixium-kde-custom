# Temas GTK

Os perfis Classic, Modern e DomainOS usam, respectivamente, `IrixClassic-KDE`,
`Irixium-KDE` e `DomainOS-SR10-4-KDE`. Essas variantes acompanham os papéis de cores exportados pelo
KDE para GTK2, GTK3 e GTK4, preservando o desenho de cada família.

| Pasta | Uso |
|---|---|
| [IrixClassic-KDE](IrixClassic-KDE/) | Classic adaptável ao esquema KDE |
| [Irixium-KDE](Irixium-KDE/) | Irixium adaptável ao esquema KDE |
| [IrixClassic-KDE-Reload](IrixClassic-KDE-Reload/) | Segunda identidade do mesmo desenho Classic para recarga nativa |
| [Irixium-KDE-Reload](Irixium-KDE-Reload/) | Segunda identidade do mesmo desenho Irixium para recarga nativa |
| [IrixClassic](IrixClassic/) | Variante Classic original com paleta própria |
| [Irixium](Irixium/) | Tema moderno original, preservado byte a byte |
| [DomainOS-SR10-4](DomainOS-SR10-4/) | Desenho Motif SR10.4 com paleta CoralReef de referência |
| [DomainOS-SR10-4-KDE](DomainOS-SR10-4-KDE/) | Desenho Motif SR10.4 adaptável ao esquema KDE |
| [DomainOS-SR10-4-KDE-Reload](DomainOS-SR10-4-KDE-Reload/) | Segunda identidade Motif para recarga nativa |

A suíte instala as pastas completas no diretório XDG de temas do usuário e
em `~/.themes`, necessário para a descoberta GTK2. Não instala arquivos em
`/usr/share`, não seleciona temas de outros usuários e não altera o login SDDM.
Os arquivos originais também são a fonte local para gerar os recursos GTK2;
não há download de temas durante uma troca de cores.

As barras DomainOS seguem a
[especificação comum SR10.4](../docs/DOMAINOS-REGRAS-ROLAGEM.md).
O gerador GTK3 lê o contrato JSON antes de construir os controles. A
[fila de revisão](../docs/DOMAINOS-FILA-REVISAO-VISUAL.md) distingue famílias
validadas e pendências: a moldura principal da tabela GTK3 preenchida ainda
requer adaptação; GTK2 e GTK4 não recebem a conclusão da etapa GTK3.

## Troca de tema e cores

O Tema Global do Plasma não seleciona sozinho o nome do tema Kvantum nem
recarrega todos os recursos GTK. O instalador inclui o observador por usuário
[theme_companion_bridge.py](../tools/theme_companion_bridge.py), que conecta
essas partes às escolhas feitas nas Configurações do Sistema. Ele usa eventos
KConfig e a exportação `gtk-3.0/colors.css` do GTK Config. Não há sondagem
periódica nem temporizador de redesenho do painel.

Ao selecionar um dos três Temas Globais da suíte, o observador seleciona seu
Kvantum e GTK correspondentes. Ao selecionar outro Tema Global, deixa a
seleção a cargo do KDE. Uma troca apenas do esquema de cores preserva um
nome GTK independente escolhido pelo usuário.

O observador também confere a alteração dos arquivos KDE, mesmo quando a
exportação GTK ainda contém as cores do tema anterior. Solicita ao GTK Config
a leitura da paleta atual pela notificação nativa `General/ColorScheme`, uma
vez por alteração. O auxiliar de configuração aguarda, por até dois segundos,
as duas exportações GTK3/GTK4 completas antes de adaptar GTK2/GTK4; a interface
não espera nem é redesenhada por esse auxiliar. Se a escolha mudar durante a
operação ou a exportação não chegar, a atualização anterior é recusada.

GTK3 utiliza os papéis exportados e as imagens simbólicas do tema. GTK2 gera
recursos de paleta em um cache próprio; GTK4 gera CSS com nomes de papéis
próprios, pois a folha CSS do usuário pode permanecer em memória. A mudança
entre as duas identidades do mesmo desenho provoca a recarga nativa dos
aplicativos já abertos. A preferência escura continua sendo respeitada:
`gtk-dark.css` importa o desenho correspondente, evitando cair no Adwaita.

A integração precisa do GTK Config do KDE, Python da distribuição com PyQt6
(QtCore/QtDBus) e Pillow. O instalador verifica as dependências; não instala
pacotes do sistema. Aplicativos que impõem seu próprio desenho, incluindo
alguns baseados em libadwaita, podem ignorar o tema GTK selecionado.

GTK4 não oferece steppers de scrollbar: essa versão mantém o trilho e o
indicador nativos, sem acrescentar botões de seta artificiais. As bordas Classic
usam cantos fixos e faixas de relevo com tamanho transversal inteiro. No GTK4,
somente o eixo uniforme dessas faixas é esticado, evitando os fragmentos vistos
com a repetição de imagens simbólicas no renderer Cairo.

Os temas Kvantum canônicos IrixClassic, Irixium e DomainOS-SR10-4 conservam suas cores nos SVG e
em `GeneralColors`. Para criar variantes locais que acompanham o esquema KDE,
use [apply_kvantum_colors.py](../tools/apply_kvantum_colors.py) depois de aplicar
as cores nas Configurações do Sistema. Esse comando manual integra o runtime
instalado, mas não é disparado automaticamente pelo observador GTK.

Na abertura de aplicações, Kvantum não separa os valores ativo e desativado de
`Base`, `AlternateBase` e `Shadow`. O script usa os valores ativos nativos e
declara essa limitação no resultado. Consulte [Kvantum](../kvantum/README.md)
para comandos, restauração e limites. A adaptação GTK continua independente.

## Instalação e restauração

Na própria sessão KDE, execute o instalador normal:

```sh
bash instalar-irixium.sh
```

`--sem-integracao` omite o observador; `--sem-cache` prepara os arquivos sem
iniciá-lo, para instalação fora da sessão gráfica. O runtime instalado contém
seus auxiliares e o catálogo: a unidade de usuário não depende do caminho do
checkout. Para iniciar posteriormente:

```sh
python3 tools/theme_companion_bridge.py --instalar --iniciar
```

O serviço é `irix-theme-companions.service`, pertencente somente ao usuário
que executou a instalação. Os recibos ficam no diretório XDG de estado. Os
arquivos gerados têm verificações de identidade e conteúdo; uma edição
posterior provoca recusa, em vez de sobrescrita silenciosa.

Uma atualização da suíte primeiro restaura seus próprios recursos de paleta,
antes de substituir as pastas dos temas. A restauração da suíte segue a mesma
ordem. Restaurar os arquivos da integração não restaura, por si só, uma escolha
anterior de Tema Global ou preferências de aplicativos. Recibos interrompidos
exigem conferir a recuperação antes de continuar.

## Origem e validação

[MODERN-PRESERVED.json](MODERN-PRESERVED.json) registra os SHA-256 dos 35
arquivos originais e a mudança do prefixo para `gtk/Irixium/`. O README e as
licenças upstream permanecem nessa pasta. As variantes modernas mantêm a
atribuição e as licenças dos recursos de origem; sua adaptação não muda essa
licença.

O Classic usa os mapas locais GPL-3.0-or-later de `kvantum/tools/` e sua tradução
GTK. Veja [origem](IrixClassic/ORIGEM.json), [compatibilidade](IrixClassic/README.md)
e [licença](IrixClassic/LICENSE). Os construtores adaptáveis ficam em
[gtk/tools](tools/), com inventários dos arquivos produzidos em cada variante.

DomainOS é uma família própria: relevo Motif de dois pixels, barras de 16 pixels,
setas triangulares de 12 pixels e indicadores sem as estrias Classic. A arte foi
redesenhada com coordenadas inteiras a partir da captura SR10.4 e das medidas do
VUE 2.01/Motif 1.1 na VM. As cores vêm dos papéis da paleta CoralReef nativa.
[build_kde_domainos.py](tools/build_kde_domainos.py) constrói os aliases;
[origem](DomainOS-SR10-4/ORIGEM.json) registra referência e inventário. Não são
redistribuídos imagens, programas ou fontes HP. Nimbus Sans aproxima a fonte
bitmap Swiss 742; GTK4 conserva sua limitação nativa de ausência de steppers.
O reteste GTK3 das duas identidades e estados das setas passou 408 verificações.
O VUE selecionava oito conjuntos de cores por aplicativo. A adaptação usa os
papéis de uma paleta global KDE; ela não reproduz automaticamente essa seleção
individual de cores por programa.

Os ensaios usam widgets reais GTK2/3/4, exportação nativa de cores e processos
já abertos, em perfis privados. Conferem fundos, texto, estados e transparência
dos controles em azul, amarelo e escuro, além de retorno à paleta anterior.
Uma galeria isolada completa também permite verificar Plasma e Kvantum juntos;
os testes de biblioteca não substituem essa validação da sessão.

## Validação das setas Classic — 10/10/2026

A correção está nas variantes `IrixClassic-KDE` e `IrixClassic-KDE-Reload`.
O Classic original permanece como fonte, sem alteração de seus arquivos.
Em GTK2, a regra genérica usava a seta pequena do spinbutton também na scrollbar;
em GTK3, o chevron nativo aparecia sobre a arte e a geometria herdada comprimia
essa arte. Agora cada versão usa o desenho Classic correspondente:

| Versão | Implementação e verificação |
|---|---|
| GTK2 | `STEPPER` pinta a imagem original de 18 × 18 na própria célula, com relevo normal, pressionado e desativado. Ensaio nativo **34/34**, mais comparação dos quatro recortes pressionados **4/4**, iguais em RGBA às imagens esperadas. |
| GTK3 | O chevron nativo é desativado; a arte de 18 × 18 fica centralizada, mantendo as métricas da scrollbar. O reteste dos dois aliases em cinza e azul passou **408/408 verificações** de arte, estados nativos e dimensões. |
| GTK4 | A API nativa não tem botões de seta; conserva trilho e indicador, sem simular steppers. |

O ensaio GTK2 usou widgets reais em um processo privado, inclusive células fora
da origem da janela, clique mantido, mudança cinza → azul e recarga por alias.
Conferiu também spinbutton e dimensões inalterados, restauração dos oito RCs e
ausência de diagnósticos GTK. Os negativos anteriores foram preservados: uma
receita com repetição de imagem funcionava na origem, mas fragmentava a arte
em outras posições. A receita final pinta localmente a célula de 18 pixels.

O reteste GTK3 cobre as quatro direções nos estados normal, pressionado,
desabilitado, sem foco e desabilitado sem foco, incluindo os dois limites do
percurso. A comparação anterior das quatro imagens não cobria toda essa cascata:
as regras do botão comum comprimiam a seta nos estados desabilitado e pressionado.
O reset agora acompanha cada combinação de estado, preservando as imagens e as
dimensões. Os recortes nativos são comparados pixel a pixel, com tolerância de
um nível por canal para arredondamento das misturas de cores.

Os recibos locais de desenvolvimento, fora do pacote instalado, são:

- GTK2: `.qa-irix-gtk2-scrollbar-history/production-final-r12/RESULTADO.json`, SHA-256 `7f2b8fa3d485dac199c6294b2dd845174787355cf344d7b5f888c5c2db0149d5`.
- Pressionados: `PRESSED-EXACT.json` na mesma pasta, SHA-256 `c8f73dd9b2215258fde5a3d0d08bd85ec840a0b2736f8cd3f3db481f7ee8b521`.
- GTK3 normal, prova anterior: `.gtk-kde-modern-validation/arrow-readonly/r2/ARROW-COMPARISON.json`, SHA-256 `a81ff0aca7f375f20d3afb1bf744204e19a394c9ffc16b476767f2bbee9135e3`.
- GTK3 com estados e limites: `.qa-irix-gtk3-arrows-r11-r4/RESULTADO.json`.

Essa correção trata o Classic. O desenho e as métricas Irixium permanecem
próprios, e seus 35 arquivos originais continuam preservados. A prova técnica
não substitui a avaliação manual dos aplicativos do usuário nem modifica a
seleção dos Temas Globais ou o layout do painel.

## GTK1

O arquivo `gtk-1.2/gtkrc` preservado do Irixium contém somente uma paleta.
A suíte não oferece seleção nem uma variante Classic completa para GTK1.
O GTK Config do KDE trata GTK2/3/4, sem seletor GTK1. A convenção histórica
GTK1 é `themes/<tema>/gtk/gtkrc`, com configuração via `GTK_RC_FILES` ou
`~/.gtkrc`; copiar a pasta `gtk-1.2` não ativa esse tema.

Cobertura GTK1 exige implementação e teste com runtime isolado. Nenhuma
biblioteca antiga é instalada nos perfis atuais. Referências:
[GTK 1.2.10 oficial](https://download.gnome.org/sources/gtk+/1.2/gtk+-1.2.10.tar.gz),
[GTK Config 6.3.4](https://deb.debian.org/debian/pool/main/k/kde-gtk-config/kde-gtk-config_6.3.4.orig.tar.xz)
e [inicialização de CSS do GTK4 4.18.6](https://raw.githubusercontent.com/GNOME/gtk/4.18.6/gtk/gtksettings.c).
