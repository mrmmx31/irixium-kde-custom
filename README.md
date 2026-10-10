# Irixium / IRIX Classic

Temas mantidos por **mrmmx31** para KDE Plasma 6. Todos os instaladores de temas
usam somente o perfil do usuário atual. Execute **sem sudo**.

## Instalar e aplicar

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash aplicar-tema.sh classic     # ou: moderno
```

A instalação atualiza 35 componentes locais, com backup, sem trocar a
seleção. A aplicação escolhe tema global, decoração, Kvantum, GTK, ícones,
cursores, cores, Plasma Style e splash correspondentes, sem redefinir painéis.
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

O layout do tema global usa esses widgets em novas instalações. A seleção do tema
continua preservando o painel existente. O desenho de pressão acompanha o mouse
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

## Irix Classic DomainOS

O [Plasma Style Irix Classic DomainOS](plasma/IrixClassicDomainOS/) é uma opção
independente do Classic atual, inspirada na referência HP e na composição enviada
pelo usuário. O instalador disponibiliza esse estilo, o applet
`org.irixclassic.domainos.panel` e o esquema de cores **DomainOS SR10.4**, versão
confirmada pelo usuário. A instalação mantém o estilo escolhido, os layouts e os
defaults do perfil Classic. `aplicar-tema.sh classic` continua selecionando o
conjunto Classic existente.

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

Para usar a barra no lugar da atual e associar a troca às opções do Plasma Style:

```sh
plasma-apply-desktoptheme IrixClassicDomainOS
python3 tools/activate_domainos.py --verificar
python3 tools/activate_domainos.py
python3 tools/domainos_style_bridge.py --instalar --iniciar
```

A ativação substitui somente o painel escolhido e guarda seu layout anterior em
arquivos privados. Não mantém uma segunda barra oculta. Com a ponte habilitada,
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
real. O esquema do painel e as variantes GTK adaptáveis acompanham KDE.
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
Os ensaios funcionais usam sessões privadas. Instalação e ativação são comandos
separados; a associação entre Style e layout exige habilitar a ponte no próprio perfil.

## GTK e decorações opcionais

O Classic seleciona `IrixClassic-KDE` para GTK 2, 3 e 4; o Moderno usa `Irixium-KDE`.
O instalador mantém ambos em XDG e `~/.themes`, pois GTK 2 procura neste último
caminho. A auditoria confere também essas cópias, como faz com os cursores legados.
Os controles Classic têm relevos retos, interruptores retangulares e resposta
imediata à pressão. GTK 2 requer o engine pixmap da distribuição; aplicativos
libadwaita ou com CSS próprio podem controlar sua aparência. Veja [GTK](gtk/README.md).
Para atualizar somente a seleção GTK na sessão atual, preservando o restante:

```sh
python3 tools/select_gtk.py classic
# Restaurar a seleção anterior, se não houve alterações posteriores:
python3 tools/select_gtk.py --restaurar
```

Para atualizar o Kvantum após aplicar um esquema de cores, execute
`python3 tools/apply_kvantum_colors.py` na própria sessão KDE. O comando mantém
os temas originais e gera cópias locais recuperáveis. Veja [Kvantum](kvantum/README.md).

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

| Componente | Fonte |
|---|---|
| Decoração IRIX Classic | `decorations/classic/` |
| Decoração Irixium e seus assets | `decorations/modern/` |
| Estilos Qt Widgets | `kvantum/IrixClassic/`, `kvantum/Irixium/` |
| GTK 2/3/4 | `gtk/IrixClassic/` e `gtk/Irixium/` |
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
não são incluídos. Nimbus Sans é fornecida pela distribuição.
