# IrixClassic 0.7.0-rc1 — controles complementares / bloco 7

Manutenção: `mrmmx31`. Tema Kvantum, separado de Aurorae, GTK e Plasma.

## Entrega atual

Sliders/scales, progresso, divisores, cabeçalhos, seleção em listas/tabelas/árvores,
expansores, molduras de agrupamento, tooltips, alças de redimensionamento, títulos
de docks, MDI e dial. A largura da barra de rolagem e os blocos 1–6 permanecem
preservados. O bloco 7 fecha a implementação temática do roteiro; **não significa
homologação final nem reprodução histórica universal**.

```sh
# Na raiz do clone, sem sudo:
bash kvantum/testar-controles.sh
bash kvantum/prever-controles.sh
# Ensaio nativo opcional / galeria Qt Quick:
bash kvantum/prever-controles.sh --testar
bash kvantum/prever-controles.sh --qtquick
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

A instalação preserva a seleção atual e não executa o reparo Qt Quick.
Reabra os aplicativos. Restauração: `bash kvantum/restaurar-classic.sh`.
As galerias mantêm a configuração em diretório temporário. Somente
`--capturas /pasta/nova` salva imagens dos próprios controles da galeria.

`PREVIA-CONTROLES.png` contém mapas do SVG; não é captura nativa nem prova de
interação. Veja `../docs/CONTROLES.md` e `../docs/COBERTURA-IRIXCLASSIC.md`.
O plano completo está em `../PLANO-IRIXCLASSIC.md`.

## Setas KDE — ainda pendente

O usuário relata funcionamento no Kvantum Preview e falha nas telas KDE. Não
há novo resultado de `COMPARACAO-SETAS.json` para confirmar os quatro caminhos.
Esta entrega NÃO anuncia correção, NÃO redesenha as setas e NÃO modifica o
reparo opt-in existente. Essa investigação continua independente da arte.

## Histórico até 0.6.0-rc1

As descrições abaixo referem-se às entregas anteriores.

# IrixClassic 0.6.0-rc1 — abas

Manutenção: `mrmmx31`. Tema Kvantum para Application Style, não decoração de janela.

## Revisão atual

Bloco 6: abas com laterais inclinadas, selecionada em primeiro plano, junções de
painel nas quatro orientações, família para documentos, fechar e transbordamento.
Mantidos todos os 3.293 recursos SVG anteriores. A largura reservada ao rótulo
continua equivalente; a única mudança global de comportamento geométrico é
`active_tab_overlap=4`. Nenhuma fonte, escala ou configuração KDE global é alterada.

Referência funcional: SGI VkTabPanel. Desenho e dimensões escolhidos são adaptações,
não equivalência pixel a pixel. O menu histórico de abas colapsadas exige suporte
do aplicativo e não é instalado pelo tema. Consulte `../docs/ABAS.md`.

```sh
# Na raiz do clone:
bash kvantum/testar-abas.sh
bash kvantum/prever-abas.sh
bash kvantum/prever-abas.sh --testar
bash kvantum/prever-abas.sh --qtquick
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

Sem sudo. Galerias usam configuração temporária. Reabra os aplicativos após
instalar. Ausência de dependências retorna 77, nunca sucesso nativo.
`PREVIA-ABAS.png` é composição técnica das fatias, não captura Qt.

A seta nas aplicações KDE **permanece pendente**. Não há novo reparo global nesta
revisão; o desenho aprovado e o utilitário opcional antigo ficam intactos.
O novo `../comparar-setas.sh --saida /pasta/nova` reúne Widgets, módulo instalado,
QML do disco e cópia temporária corrigida em `COMPARACAO-SETAS.json`, sem instalar.

Plano completo: `../PLANO-IRIXCLASSIC.md`. Próximo desenvolvimento: **bloco 7**.

## Histórico (versões abaixo não são a versão atual do manifesto)

# IrixClassic 0.5.0-rc1 — menus

Manutenção: `mrmmx31`. Application Style Kvantum; não é decoração de janela.

## Revisão atual

Bloco 5: painel e barra de menu, item armado/pressionado, setas de submenu,
separadores e tear-off quando o aplicativo o oferece. Os recursos anteriores de
check/radio e campos permanecem intactos, assim como os desenhos da barra e dos
botões já aprovados. As métricas e recursos dos outros controles foram isolados
da herança dos menus.

```sh
# Na raiz do clone:
bash kvantum/testar-menus.sh
bash kvantum/prever-menus.sh
bash kvantum/prever-menus.sh --qtquick
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

O instalador não ativa outro tema. Reabra os aplicativos. Sem sudo. Galerias usam
seleção temporária. `--testar` faz testes nativos de Qt Widgets, quando disponíveis;
Qt Quick é galeria manual para comparar a camada KDE. Ausência de dependência
retorna 77, nunca aprovação. Nenhuma captura do desktop é coletada.

`PREVIA-MENUS.png` mostra mapas do SVG, não execução Qt. Os perfis históricos
amostrados e as adaptações estão discriminados em `../docs/MENUS.md`.
O plano completo continua em `../PLANO-IRIXCLASSIC.md` (próximo bloco: abas).

## Setas nas telas Qt Quick do KDE

O relato de funcionamento no Kvantum Preview e falha nas telas KDE é compatível
com caminhos Widgets/Qt Quick diferentes. O inventário recebido ainda mostra
`native_pressed_only=true`, sem marcador de reparo, e `prefer` para o recurso
embutido. Instalar este tema NÃO aplica o reparo de compatibilidade do sistema.
Consulte `../docs/PRESSAO-QTQUICK.md`; a confirmação local continua necessária.

O teste temporário foi corrigido: busca a seta por `hitTest`, pois o StyleItem
6.13 não expõe `subControlRect("up")` para scrollbars. Agora compara as duas
orientações com Fusion, Breeze ou Kvantum sem alterar a seleção da sessão.

## Histórico das revisões anteriores

O conteúdo abaixo descreve entregas anteriores. Seus números de versão não são
a revisão atual; a versão de instalação é a do MANIFEST.json.

## Nesta revisão

Checkbox com marca vermelha, radio em losango com triângulo azul, estado parcial
como adaptação ao Qt, clareamento de localização e contextos de menu/lista.
As 2517 primitivas antigas, botões, campos e rolagem foram preservados.
A grade 15×15 é original; não é cópia certificada de todos os pixels do IRIX.
Consulte `../docs/SELECAO.md` para referências e limites reais do motor.

**Kvantum 1.1.4 não escolhe um SVG pressed separado para check/radio.**
O bloqueio e a mudança da seleção permanecem nativos; indisponibilidade usa
opacidade 0.7. Foco de teclado não é confundido com hover ou seleção.

```sh
bash kvantum/testar-selecao.sh
bash kvantum/prever-selecao.sh
bash kvantum/prever-selecao.sh --testar
```

## Setas em outros Application Styles

A falha reportada é mantida como **não resolvida na sessão**. Não alteramos
novamente o SVG da rolagem nem ampliamos o reparo global experimental.
Inventário e ensaio diferenciam execução da ação de pressão visual:

```sh
bash kvantum/diagnosticar-setas.sh
bash kvantum/diagnosticar-setas.sh --testar --saida "$HOME/Downloads/diagnostico-setas"
```

O ensaio compara Qt Widgets e Qt Quick, com Fusion, Breeze e Kvantum que estiverem
instalados. Não modifica o Application Style global nem arquivos de sistema.
Veja `../docs/DIAGNOSTICO-SETAS.md`. Ausência de dependência retorna 77.

## Base dos blocos 1 e 2 preservada

A barra de rolagem da 0.1.0-rc2 foi preservada: puxador, trilho, ranhuras,
largura 18 e comprimento mínimo 34. Corrigido o detalhe de pressão das setas:
o contorno escuro do triângulo não muda de lugar, mas ganha o realce inferior/
direito que faltava, além da inversão da célula já existente.

O bloco 2 fornece recursos separados para comando, ferramenta/paleta e toolbar.
A pressão rebaixa o bisel interno sem mover o texto/ícone. O marcador do botão
padrão não oculta mais a faixa clara do bisel pressionado. Hover, seleção
persistente, foco de teclado e indisponibilidade têm papéis separados.
Não há temporizador ou animação prolongando artificialmente a pressão.

O perfil normal do botão de comando preserva os três tons de borda do Help
Viewer IRIX fornecido. Estados sem referência visual direta e equivalências
Qt continuam sendo adaptações documentadas, não cópias históricas certificadas.
A paleta geral, os tamanhos de fontes e as métricas dos outros blocos não mudam.

## Testar antes de instalar

Na raiz do checkout:

```sh
bash kvantum/testar-botoes.sh
bash kvantum/prever-botoes.sh
```

A galeria usa configuração temporária e Qt 6/Kvantum real quando disponível;
não troca a seleção da sessão. Exige PyQt6 ou PySide6 e o plugin Kvantum Qt 6.
Dependência ausente retorna código 77 e não é instalada automaticamente.
A fonte de 14 pixels é local à galeria; `--fonte-px 16` permite comparar.

Para testes de eventos e PNGs offscreen:

```sh
bash kvantum/prever-botoes.sh --testar
bash kvantum/prever-botoes.sh --capturas /tmp/irix-botoes-qt
```

A imagem `PRESSAO-E-BOTOES.png` é uma prancha técnica dos mapas, não um screenshot
Qt. `PREVIA.png` é a prévia inicial rc1; `PREVIA-ROLAGEM.png` e
`ESTADOS-ROLAGEM.png` documentam a rc2. Para o novo estado pressionado, use a
prancha nova e a galeria nativa, não as prévias históricas.

## Instalar / restaurar

Como usuário normal, sem sudo, na raiz do checkout:

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

Instala no diretório de configuração do usuário sem mudar a seleção. Se o tema
já estava selecionado, reabra os aplicativos. Caso contrário, escolha
IrixClassic no Kvantum Manager com Application Style definido como kvantum.
`--ativar` é opcional e altera só a seleção interna do Kvantum.

```sh
bash kvantum/restaurar-classic.sh
```

Restaura o último recibo desse instalador; depois reabra os aplicativos.
Não execute o atualizador da decoração moderna para testar este tema.
Nenhum recurso de /usr, Aurorae, decoração Classic, GTK, fontes globais,
esquema KDE, escala de tela ou base `kvantum/Irixium/` é alterado.

## Continuidade e limites

O plano completo está em `../PLANO-IRIXCLASSIC.md` e deve acompanhar cada merge.
Bloco 1: desenho aprovado pelo usuário, pressão corrigida aguardando reteste.
Bloco 2: implementado para teste local. Próximo: bloco 3, campos e entradas.
Blocos 4–7 mantêm a base anterior e ainda exigem revisão histórica específica.

Kvantum tematiza Qt Widgets e integrações que usem o estilo; não reimplementa
widgets exclusivos da SGI nem reorganiza a interface dos aplicativos. AutoRaise,
popup, tamanhos forçados e política de ações continuam pertencendo ao Qt/app.
Estados desativados podem ser desenhados pelo motor com normal/toggled e
opacidade adicional. Ausência de intervalo, Escape no arraste e impressão da
posição inicial da scrollbar SGI continuam limites documentados em
`../docs/ROLAGEM.md`.

Detalhes e aceitação: `../docs/BOTOES.md`.
Validação realizada: `../docs/VALIDACAO-BOTOES.md`.
Configuração derivada de Irixium por Mark Whittaker/Phob1an; SVG e utilitários
novos sob GPL-3.0-or-later. Créditos/licenças preservados. Nenhuma fonte tipográfica,
código privado ou binário IRIX é incluído.
