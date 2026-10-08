# Irixium / IRIX Classic

Temas mantidos por **mrmmx31** para KDE Plasma 6. Todos os instaladores de temas
usam somente o perfil do usuário atual. Execute **sem sudo**.

## Instalar e aplicar

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash aplicar-tema.sh classic     # ou: moderno
```

A instalação atualiza 26 componentes gráficos locais, com backup, sem trocar a
seleção. A aplicação escolhe tema global, decoração, Kvantum, GTK, ícones,
cursores, cores, Plasma Style e splash correspondentes, sem redefinir painéis.
Não há download de dependências temáticas pela KDE Store nem instalação de SDDM.
Plasma 6, Aurorae/KSvg Qt 6, Kvantum Qt 6 e KSystemStats devem estar instalados pela distribuição.

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

## GTK e decorações opcionais

O Classic seleciona `IrixClassic` para GTK 2, 3 e 4; o Moderno mantém `Irixium`.
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
| Cores | `colors/Irixium.colors` |
| Plasma Styles | `plasma/IrixClassic/`, `plasma/Irixium/` |
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
não troca a seleção. O reparo opcional do KDE Qt Quick em `tools/qtquick_scrollbar_fix.py`
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
