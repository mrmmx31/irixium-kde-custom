# Irixium / IRIX Classic / DomainOS SR10.4

Temas mantidos por **mrmmx31** para KDE Plasma 6. Todos os instaladores de temas
usam somente o perfil do usuário atual. Execute **sem sudo**.

A [pré-release 1.1.0-beta.1](https://github.com/mrmmx31/irixium-kde-custom/releases/tag/v1.1.0-beta.1)
contém o conjunto gráfico completo pré-compilado. [Notas e limites](docs/RELEASE-1.1.0-beta.1.md).

## Instalar e aplicar

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash aplicar-tema.sh classic     # ou: moderno, domainos
```

A instalação disponibiliza três temas globais e atualiza 40 componentes locais,
com backup, sem trocar a seleção. A aplicação escolhe tema global, decoração,
Kvantum, GTK, ícones,
cursores, cores, Plasma Style e splash correspondentes, sem `--resetLayout`.
A ponte do DomainOS substitui somente o painel autorizado quando esse tema
global é escolhido; instalar os arquivos não substitui o painel.
Não há download de dependências temáticas pela KDE Store nem instalação de SDDM.
O tema Wine é disponibilizado sem criar ou alterar prefixos automaticamente;
use o [assistente do Wine Classic](wine/README.md) para escolher um prefixo.
A suíte completa exige Plasma 6 com Qt 6.8 ou superior, Aurorae/KSvg Qt 6, Kvantum Qt 6 e KSystemStats instalados pela distribuição.
O painel DomainOS funcional também exige PyQt6 QtCore/QtDBus do `/usr/bin/python3`
para sua ponte transitória com o KWin; o script de cores usa também QtGui.
O instalador verifica essas dependências.
Ao instalar a partir do checkout fonte, também são necessários um compilador
C++, `pkg-config` e os SDKs Qt6Widgets/Qt6Qml da mesma versão do Qt em execução
para compilar o módulo local do painel. O ZIP DomainOS pré-compilado inclui
esse módulo e dispensa os SDKs de desenvolvimento. O instalador não instala
pacotes de sistema.

Os temas completos e os destinos estão em [components.json](components.json),
usado pelo instalador e pela auditoria. A aplicação seleciona o esquema de sons
SGI **quando ele já está instalado e validado**; não modifica volume, mudo,
Não perturbe nem habilita eventos. `--sem-sons` preserva a seleção de sons.

Para atualizar uma decoração já em uso e liberar o QML antigo mantido pelo KWin,
execute na sessão KDE do próprio usuário:

```sh
bash instalar-irixium.sh --recarregar-decoracao
# Se os arquivos já estiverem instalados:
python3 tools/reload_decoration.py
```

A recarga alterna brevemente para a decoração nativa e retorna à mesma seleção
IRIX, preservando o conteúdo e as permissões de `kwinrc`, com backup. Outros
usuários não são acessados. Reabra os aplicativos para carregar Kvantum e ícones.
Não há reinício forçado do KWin. Se não houver uma sessão KDE disponível, salve o
trabalho e encerre/entre novamente na sessão após atualizar o QML. Os botões mostram relevo durante a pressão e executam a ação na soltura;
duplo clique no menu fecha também a janela inativa. Somente o clique simples no
menu aguarda o intervalo de duplo clique do Qt; esse timer não participa do resize.

## Painel Classic

O Classic inclui widgets próprios para o menu, três atalhos, Iconbox, bandeja e
relógio, com relevo compacto inspirado no Indigo Magic/Motif. O pager usa as
molduras Classic e as tarefas ficam numa fileira de ícones com legenda curta.

Para trocar ou ordenar os atalhos, use o botão direito em um deles e abra
**Organize Launchers… → Launchers**. A lista oferece adicionar, substituir,
remover, subir e descer; **Aplicar/OK** salva e **Cancelar** descarta as alterações.
Substituir conserva a posição e escolhe outro aplicativo sem editar seu arquivo
`.desktop`. Veja a [configuração dos atalhos](plasma/applets/org.irixclassic.quicklaunch/README.md).

Depois de instalar a suíte, atualize o painel existente na sessão KDE do próprio
usuário; este comando preserva os demais widgets, a ordem e as configurações:

```sh
python3 tools/classic_panel.py --verificar
python3 tools/classic_panel.py
# Voltar aos widgets anteriores usando o backup da alteração:
python3 tools/classic_panel.py --restaurar
```

O layout do tema global usa esses widgets em novas instalações. A seleção Classic
preserva o painel existente, ou recupera o painel anterior quando a ponte o
substituiu por escolha do tema global DomainOS. O desenho de pressão acompanha o mouse
enquanto o botão está abaixado; não adiciona espera nem temporizador visual.
Veja os [testes e limites da validação do painel](plasma/docs/VALIDACAO-PAINEL-2026-10-07.md).

Para mostrar o pager e acrescentar o monitor gr_osview no desktop:

```sh
python3 tools/classic_desktop.py --pager --grosview --verificar
python3 tools/classic_desktop.py --pager --grosview
```

O pager nativo se oculta com uma única área de trabalho. O helper cria a segunda
somente nesse caso e conserva as áreas existentes. O gr_osview aparece inicialmente
no canto superior direito, em 280×220, com CPU, memória, swap, disco e rede reais.
Ele pode ser movido/redimensionado na edição normal do Plasma; executar novamente
o helper preserva a posição escolhida e não duplica o widget. O layout Classic
também inclui o monitor em novas instalações. Veja o [widget](plasma/applets/org.irixclassic.grosview/README.md).

## IrixClassicDomainOS — terceiro tema global

**IrixClassicDomainOS** é uma opção independente de **IRIX Classic** e
**Irixium Moderno**, baseada no Domain/OS **SR10.4 com HP VUE 2.01**.
A decoração, os controles Motif e a paleta têm fontes próprias; a
[procedência das cores](colors/DomainOS-SR10.4.ORIGEM.json) identifica essa versão.
O perfil reutiliza os ícones, cursores e wallpaper Classic e disponibiliza:

| Componente | Seleção |
|---|---|
| Tema global | `org.magpie.irixclassic.domainos.desktop` |
| Decoração | `domainos_sr104` |
| Plasma Style e painel | `IrixClassicDomainOS`, `org.irixclassic.domainos.panel` |
| Esquema de cores | `DomainOS-SR10-4` — DomainOS SR10.4 |
| Kvantum | `DomainOS-SR10-4` |
| GTK 2/3/4 adaptável | `DomainOS-SR10-4-KDE` |

A lente de atividade do painel pisca em meios ciclos de 500 ms durante pedidos
pendentes e registros reais de inicialização publicados pelo KDE. O cursor de
espera segue o tema de cursores selecionado; não bloqueia os controles. A
permanência adicional da luz está desligada por padrão e seu tempo é configurável.
O fim de uma notificação de inicialização não declara conclusão do aplicativo.
Lançamentos sem essa notificação confirmam somente o pedido; veja os
[comportamentos e limites](plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md).

Depois de instalar a suíte, selecione **IrixClassicDomainOS** em Configurações do
Sistema → Tema global, ou execute `bash aplicar-tema.sh domainos`. As opções
Classic e Moderno continuam disponíveis e conservam seus próprios controles e
defaults.

A suíte instala as pontes GTK/Kvantum e Global no perfil do próprio usuário.
Quando instalada dentro da sessão KDE, inicia os serviços locais; se não houver
a sessão nativa disponível, inicie-os depois no terminal dessa sessão:

```sh
python3 tools/theme_companion_bridge.py --instalar --iniciar
python3 tools/domainos_style_bridge.py --temas-globais --iniciar
```

A instalação registra a seleção atual como referência e aguarda uma escolha
futura. Escolher o Global DomainOS autoriza a migração de um único painel, com
backup do layout, da bandeja e das preferências. Escolher depois o Global Classic
ou Moderno recupera esse painel anterior. Voltar ao Global DomainOS recupera as
preferências salvas do seu painel. Áreas de trabalho e outros layouts são
preservados, sem reset geral nem barra anterior oculta.

Se houver mais de um painel, a ponte exige identificar o painel da primeira
migração: `python3 tools/domainos_style_bridge.py --temas-globais --painel ID --iniciar`.
Uma ativação manual anterior continua independente das escolhas globais.
Veja o [fluxo e os limites de recuperação](docs/INSTALACAO-RECUPERAVEL.md).

Para disponibilizar somente o painel DomainOS, seu Style/esquema de cores e o
gr_osview, use o instalador independente como o próprio usuário, sem `sudo`:

```sh
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
# Conferir e restaurar apenas essa instalação independente:
python3 tools/install_domainos.py --restaurar --verificar
python3 tools/install_domainos.py --restaurar
```

São quatro destinos em `XDG_DATA_HOME`, com recibos próprios em
`XDG_STATE_HOME/irixium-domainos`. Esse comando verifica as dependências KDE/Qt usadas
por esses componentes e preserva seleção de tema, configurações e painel ativo.
Não atualiza outros temas, GTK/cursores, caches ou hooks. Sua restauração não usa
os recibos da suite completa.

O pacote independente de quatro componentes também permite usar a barra e
habilitar explicitamente a associação opcional às escolhas do Plasma Style:

```sh
plasma-apply-desktoptheme IrixClassicDomainOS
python3 tools/activate_domainos.py --verificar
python3 tools/activate_domainos.py
python3 tools/domainos_style_bridge.py --instalar --iniciar
```

A ativação manual substitui somente o painel escolhido e guarda seu layout
anterior em arquivos privados. Com essa opção da mesma ponte habilitada,
selecionar **IrixClassic** no Plasma Style recupera a barra anterior; selecionar
**IrixClassicDomainOS** volta à DomainOS, conservando suas preferências. Outros
Styles não acionam essa troca. Em perfis com vários painéis, indique `--painel ID`
na primeira ativação. Veja o [pacote atual 0.2.11](docs/DOMAINOS-0.2.11.md) e a
[auditoria dos testes e limites](docs/DOMAINOS-AUDITORIA-2026-10-09.md).
A avaliação pessoal final nas duas sessões continua separada dos ensaios privados.

A composição funcional preserva o desenho aprovado e conecta hora, calendário,
rede/gr_osview, tarefas, áreas de trabalho e bandeja aos provedores KDE. A placa
GNU/LINUX abre aplicativos; a gaveta tem fixados próprios. Seleção de janelas,
organização em lote e preferências por ferramenta estão no
[manual do painel](plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md).
Fonte indisponível não recebe dados ilustrativos. O modo visual de referência
continua disponível para comparação; arraste entre miniaturas do Pager está adiado.

Para testar em Xephyr sem instalar ou alterar o perfil, execute na sessão gráfica
do próprio usuário o [assistente de teste](plasma/tools/testar-domainos-sessao.py),
passando o PNG aprovado:

```sh
/usr/bin/python3 plasma/tools/testar-domainos-sessao.py --referencia /caminho/PAINEL-APROVADO.png
```

O assistente usa HOME, KWin e barramentos privados e verifica a troca de áreas
antes de liberar a prévia. Painel e referência permanecem visíveis nas duas áreas;
as janelas de tarefas continuam vinculadas às suas áreas. Fechar o Xephyr encerra
somente a prévia. `--verificar` confere recursos/dependências sem abrir a janela.

Para testar também Qt/Kvantum, GTK3/4, decorações, ícones, cursores e papel de
parede em um Plasma completo, use o
[lançador de tema completo](plasma/tools/prever-tema-completo.py) neste checkout,
com um ZIP DomainOS já construído para a versão Qt instalada:

```sh
python3 -B plasma/tools/prever-tema-completo.py --pacote /caminho/irixclassic-domainos-0.2.11.zip
# Abrir diretamente o terceiro tema global:
python3 -B plasma/tools/prever-tema-completo.py --pacote /caminho/irixclassic-domainos-0.2.11.zip --tema org.magpie.irixclassic.domainos.desktop --decoracao domainos_sr104
```

Execute na sessão gráfica do usuário, sem sudo. O lançador exige Xephyr,
bubblewrap, namespaces de usuário e os componentes KDE/Qt/GTK instalados; não
instala dependências. As galerias usam os controles nativos. Qt6 e GTK3 aparecem
na primeira área; GTK4 na segunda. Applications oferece Configurações de Cores
e Kvantum. Para comparar a decoração paralela, acrescente
`--decoracao domainos_sr104`.

A sessão tem HOME/XDG, compositor e DBus próprios, recursos do tema somente para
leitura e acesso apenas ao novo display. Rede, áudio, dispositivos, contas e
autenticação pessoais ficam indisponíveis. Trocar cores nela não altera o perfil
real. Os PIDs compartilham o namespace do Xephyr para que o X11 autentique as
operações sobre as janelas de teste; o helper conserva a verificação de identidade.
O esquema do painel e as variantes GTK adaptáveis acompanham KDE.
O Kvantum pode ser adaptado pelo [script de cores](kvantum/README.md), com os
limites de estados desativados descritos ali. A prévia permanece aberta
até o usuário fechar a janela externa Xephyr, encerrando somente seus processos.

A revisão R2 reúne as decisões em [requisitos](docs/DOMAINOS-REQUISITOS.md),
[preferências](docs/DOMAINOS-PREFERENCIAS.md) e
[rastreabilidade](docs/DOMAINOS-DECISOES-CONSOLIDADAS.md).
Consulte a [matriz F01–F35](docs/DOMAINOS-MATRIZ-VALIDACAO-R2.md) e o
[relatório dos testes](docs/VALIDACAO-DOMAINOS-INTEGRACAO-2026-10-08.md)
para as evidências, comandos de reprodução e limites da validação.
As alterações posteriores de cliques, menus e dicas estão no
[relatório de interação de 9 de outubro](docs/VALIDACAO-DOMAINOS-INTERACAO-2026-10-09.md).
Os ensaios funcionais usam sessões privadas. Foram verificadas escolhas nativas
Breeze → DomainOS → Classic → DomainOS → Moderno, conservando áreas de trabalho,
preferências dos widgets e geometria do painel restaurado. A
[ponte](tests/test_domainos_style_bridge.py) e a
[ativação](tests/test_domainos_global_activation.py) também têm testes de recusa,
rollback e preservação de escolhas independentes. A associação opcional entre
Plasma Style e layout exige habilitação explícita no próprio perfil; a associação
Global faz parte da instalação normal da suíte. `--sem-integracao` dispensa as pontes.

## GTK e decorações opcionais

O Classic seleciona `IrixClassic-KDE` para GTK 2, 3 e 4; o Moderno usa `Irixium-KDE`;
o DomainOS usa sua família Motif própria, `DomainOS-SR10-4-KDE`.
O instalador mantém as três famílias em XDG e `~/.themes`, pois GTK 2 procura neste último
caminho. A auditoria confere também essas cópias, como faz com os cursores legados.
Os controles Classic têm relevos retos, interruptores retangulares e resposta
imediata à pressão. GTK 2 requer o engine pixmap da distribuição; aplicativos
libadwaita ou com CSS próprio podem controlar sua aparência. Veja [GTK](gtk/README.md).
Para atualizar somente a seleção GTK do perfil Global atual, preservando o restante:

```sh
python3 tools/select_gtk.py classic      # ou: moderno, domainos
# Restaurar a seleção anterior, se não houve alterações posteriores:
python3 tools/select_gtk.py --restaurar
```

Para atualizar o Kvantum após aplicar um esquema de cores, execute
`python3 tools/apply_kvantum_colors.py` na própria sessão KDE. O comando mantém
os temas originais e gera cópias locais recuperáveis, selecionando a família do
Global atual. Para DomainOS, usa `DomainOS-SR10-4-KDE` e
`DomainOS-SR10-4-KDE-Reload` no Kvantum. O script consulta a paleta real do KDE,
atualiza os recursos e notifica os aplicativos Qt; ele é o passo manual após
trocar somente o esquema em Cores. A ponte GTK acompanha a exportação nativa de
cores e recarrega suas variantes adaptáveis. As fontes standalone permanecem
disponíveis para seleção independente. Veja [GTK](gtk/README.md) e
[Kvantum](kvantum/README.md) para os limites de cada toolkit.

As três [decorações do Moderno](decorations/README.md) são instaladas como opções:
`irixium_modern`, `irixium_modern_13` e `irixium_modern_41`. Todas exibem menu,
minimizar e maximizar/restaurar; as variantes importadas não criam o botão fechar.
Escolha a variante nas configurações de decorações da janela do seu usuário.

## Cursores

O pacote inclui `SGI-Classic`, associado ao Classic; `SGI-Irixium`, associado ao
moderno; e `sgi` como alternativa. Espera e progresso têm estados distintos,
e as duas variantes novas usam relógio animado. Cada estado oferece 24, 32, 48,
64 e 96, preservando o tamanho escolhido pelo usuário. O instalador mantém
os cursores nos caminhos XDG e `~/.icons`, ambos somente para esse usuário,
para que KDE/libXcursor encontrem a versão atual. Veja [cursors/](cursors/README.md).

## Ícones Classic e integração de aplicativos

O Classic 0.4.1 inclui 2.380 nomes e variantes de estado para o Plasma. Veja a
[cobertura e os testes](docs/VALIDACAO-ICONES-CLASSIC-2026-10-07.md).
A revisão de [originalidade e menus](docs/ORIGINALIDADE-ICONES-CLASSIC-2026-10-07.md)
separa VS Code/IntelliJ, aplicativos repetidos e categorias fora do padrão SGI.
Atalhos conhecidos com caminhos absolutos, ícones ausentes ou nomes genéricos
compartilhados podem ser adaptados com
`python3 tools/adapt_classic_launchers.py`, com backup e restauração local.

O PIA usa bitmaps próprios. A [integração opcional](integrations/pia/README.md)
instala seus seis estados SGI apenas no atalho deste usuário:
`python3 tools/adapt_pia_tray.py`. Reabra a interface pelo menu para carregá-la.
Os comandos `--verificar` e `--restaurar` estão disponíveis nos helpers.
A [integração do Kate](integrations/kate/README.md) adapta também o SVG Git
embutido: `python3 tools/adapt_kate_icons.py`. Salve os documentos e reabra
o Kate pelo menu para carregar esse recurso.

## Sons SGI: instalação local separada

O esquema, catálogo, mapeamento e instaladores estão em [sons/](sons/README.md).
Os áudios são baixados e instalados para seu usuário com atribuição à
[página histórica da SGI](https://ftp.jurassic.nl/mirrors/ftp.sgi.com/sgi/desktop/sounds/sounds.html).
Em outro computador:

```sh
bash sons/instalar.sh --baixar
bash aplicar-tema.sh classic --exigir-sons
```

O download usa HTTPS e valida os oito originais antes de converter para WAV.
Os bytes não entram no Git nem nos ZIPs. Com fontes já preparadas no cache local,
`bash sons/instalar.sh` reinstala sem rede; `--origem DIRETORIO` permite importar
uma cópia local. O downloader público substitui a necessidade do script privado.

Para exigir uma instalação com sons completos, audite com `--exigir-sons`.
Sem os originais, o conjunto gráfico continua instalável e o comando de aplicação
preserva os sons existentes. O comando com `--exigir-sons` recusa a aplicação,
em vez de anunciar que um esquema ausente foi configurado.

## IrixClassic Files experimental

O [IrixClassic Files](aplicativos/irixclassic-files/README.md) é um aplicativo
separado baseado no Dolphin 25.04.3 do Debian 13, com Pathfinder, Shelf e
Content Viewer. A alpha 0.1.0-alpha1 foi compilada e executada localmente; veja a
[validação e os limites](aplicativos/irixclassic-files/docs/VALIDACAO-LOCAL-2026-10-07.md).
Sua construção e instalação são opcionais e independentes dos temas.
O instalador próprio usa somente o perfil do usuário, sem substituir o Dolphin
ou mudar associações de arquivos. O componente tem testes e workflow próprios.

## Estrutura mantida

Regras de desenvolvimento e continuidade: [índice DomainOS](docs/DOMAINOS-INDICE-REGRAS.md).
Protocolos reutilizáveis em outros contextos de IA: [índice de skills](skills/INDEX.md).
As adaptações devem seguir o esquema KDE conforme a [regra de cores](docs/DOMAINOS-REGRAS-CORES.md).

| Componente | Fonte |
|---|---|
| Decoração IRIX Classic | `decorations/classic/` |
| Decoração Irixium e seus assets | `decorations/modern/` |
| Decoração DomainOS SR10.4 | `decorations/domainos/` |
| Estilos Qt Widgets | `kvantum/IrixClassic/`, `kvantum/Irixium/`, `kvantum/DomainOS-SR10-4/` |
| GTK 2/3/4 e variantes adaptáveis | `gtk/IrixClassic/`, `gtk/Irixium/`, `gtk/DomainOS-SR10-4/` e famílias `-KDE` |
| Ícones | `icons/themes/IrixClassic-SGI/`, `icons/Irixium/` |
| Três temas de cursores | `cursors/` |
| Cores | `colors/Irixium.colors`, `colors/DomainOS-SR10.4.colors` |
| Plasma Styles | `plasma/IrixClassic/`, `plasma/Irixium/`, `plasma/IrixClassicDomainOS/` |
| Painel DomainOS | `plasma/applets/org.irixclassic.domainos.panel/` |
| Wallpapers | `wallpapers/IrixClassic/`, `wallpapers/Irixium/` |
| Tema global e splash | `look-and-feel/` |
| Sons, sem os áudios | `sons/` |
| Instaladores, auditoria, transações | `tools/` |
| Testes e validação | `tests/`, `docs/`, testes dos componentes |
| Empacotamento/release estável do Kvantum | `distribuicao/` |

As decorações não sobrescrevem o Aurorae compartilhado. Os antigos overlays,
instaladores de sistema e cópias redundantes foram retirados da árvore ativa;
continuam recuperáveis pelo histórico Git. Veja
[reorganização e inventário local](docs/REORGANIZACAO-2026-10-06.md).

O hook opcional da Classic só mantém seu pacote disponível no perfil do usuário;
não troca a seleção. Seu runtime fica em `XDG_DATA_HOME/irixium/hooks/classic`,
com os arquivos necessários, sem depender da pasta de extração ou do checkout.
O reparo opcional do KDE Qt Quick em `tools/qtquick_scrollbar_fix.py`
é uma ferramenta de manutenção separada, fora da instalação dos temas.

## Validar e restaurar

```sh
python3 tools/audit_suite.py                    # fontes e vínculos no repositório
python3 tools/audit_suite.py --local --exigir-sons
bash testar-integracao.sh                      # todos os componentes públicos
bash instalar-irixium.sh --restaurar --verificar
bash instalar-irixium.sh --restaurar
bash aplicar-tema.sh --restaurar
```

As restaurações recusam sobrescrever edições posteriores. Backups ficam em
`XDG_STATE_HOME/irixium-suite` e `XDG_STATE_HOME/irixium-selection`. Sons possuem
seus próprios backups e restauração em `sons/restaurar.sh`.
Restaurar os arquivos da suíte desliga sua observação Global, preserva um eventual
Style opt-in e mantém helpers/backups para recuperação. O layout do painel tem
recibo e restauração separados; veja [instalação recuperável](docs/INSTALACAO-RECUPERAVEL.md).

Para desenvolvimento de componentes individuais, os READMEs das decorações e
Kvantum descrevem suas prévias, testes e instaladores. `update-irixium.sh` e
`restaurar-irixium.sh` continuam como atalhos para a decoração moderna.

## Créditos e licenças

Irixium moderno/Aurorae e Kvantum: Mark Whittaker / Phob1an. GTK: TheJollyDuck /
Shauna Recto. Cursores: jujum4n e colaboradores. Metadados e procedência ficam
junto de cada componente e em [UPSTREAMS.md](UPSTREAMS.md).

Créditos/licenças dos assets upstream foram preservados. O snapshot de ícones
Irixium não declara licença; o tema global upstream tem declarações GPL
conflitantes. Essas pendências não foram substituídas por uma licença presumida.
GTK separa licença de código e imagens no seu README. Os sons SGI não recebem
uma licença local nem entram no pacote público. IRIX/SGI são referências/marcas
de seus titulares; fontes tipográficas proprietárias e código privado do IRIX
não são incluídos. A família DomainOS/Motif foi redesenhada para esta adaptação;
não distribui fontes tipográficas proprietárias nem código do VUE/Motif.
Nimbus Sans é fornecida pela distribuição.
