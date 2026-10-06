# Correções de instalação e redimensionamento — 2026-10-06

Branch de trabalho: `#irixfiles`. Não houve commit/push automático nem alteração
em `/usr`, `/etc` ou configuração de outros usuários.

## Defeitos identificados e mudanças

- Classic redesenhava um Canvas da área inteira da janela a cada resize, com
  milhares de operações JS. `Frame.qml` agora usa peças SVG fixas, geradas de
  `Pixels.js` por `tools/build_tiles.py`; somente os símbolos pequenos usam Canvas.
- Consultas `KSvg.hasElement()` não notificavam bindings QML quando os SVGs modernos
  terminavam de carregar. Os botões ficavam vazios até mudar o hover/estado.
  Os bindings agora acompanham `repaintNeeded` e o caminho da imagem.
- Um nome upstream com espaço (`user-bookmarks copy.png`) fazia o GTK rejeitar
  o cache Irixium inteiro. Foi renomeado sem alterar a imagem; a auditoria agora
  detecta nomes incompatíveis com o cache, e o cache GTK gerado foi validado.
- O instalador principal parava nos ícones existentes e omitia ícones Irixium,
  Kvantum, cursor, GTK, esquema de cores e wallpaper Irixium. O conjunto agora
  substitui 15 componentes com staging, backup, conferência e reversão.
- Defaults continham `name=irixium` enquanto a pasta é `Irixium`, cursor diferente
  do incluído e referências de splash inconsistentes. Ambos os pacotes agora
  contêm seu splash; não dependem de instalação de tema de login.
- Dependências KNS remotas foram retiradas dos metadados da distribuição local.
  O esquema de cores e wallpaper foram capturados do pacote já instalado, com
  hashes/procedência em `ORIGEM.json`; não se afirma que sejam a última versão upstream.
- `aplicar-tema.sh classic|moderno` aplica o pacote Plasma e a seleção interna do
  Kvantum correspondente. O KCM de Tema Global, sozinho, não seleciona o Kvantum.
- A aplicação nativa também escreve `gtkrc`, `gtkrc-2.0` e `Trolltech.conf`.
  Eles agora entram no backup e na restauração, inclusive quando não existiam antes.

## Verificação

- 36 imagens reais de Qt Quick comparadas pixel a pixel com o painter anterior:
  larguras pares/ímpares, janelas pequenas, ativa/inativa, maximizada, escalas 1/2/3.
  Todas idênticas, sem avisos QML.
- Eventos reais do Qt nas duas decorações: clique simples aguarda o intervalo
  nativo, duplo clique fecha uma vez sem menu posterior, botão direito imediato.
- Verificação adicional de foco: janela ativa, inativa, ativada entre os cliques
  e desativada entre os cliques. Classic cancelava o gesto ao perder foco; agora
  foco só altera a arte. Os quatro cenários passaram nos dois temas, sem pedido
  de ativação extra. O teste entrega a segunda pressão e o evento double-click
  explicitamente, evitando a sequência adicional gerada por `QTest.mouseDClick`.
- Prévia moderna com KSvg: assets/estados válidos ao carregar, hover, pressão,
  soltura e captura. O teste anterior reproduziu SVGs ausentes; o corrigido passou.
- KWin Wayland virtual separado, D-Bus privado, perfis temporários: ambas as
  decorações carregaram com o plugin Aurorae e uma janela Qt redimensionável,
  sem erros dos componentes do tema. Avisos de portais/PipeWire do ambiente
  virtual não são resultados de renderização.
- Instalação em perfil vazio e segunda execução idempotente, sem downloads.
  Testes de rollback após falha, proteção de edições posteriores, links internos,
  rejeição de links externos, preservação de outros esquemas e ícones obsoletos.
- Aplicação e restauração nativas dos dois perfis em D-Bus privado e diretório
  temporário: todos os arquivos voltaram exatamente ao conteúdo anterior;
  arquivos criados pelo Plasma foram removidos na restauração.
- Reaplicação consecutiva de Classic e Irixium: pacote global, seleção Kvantum,
  decoração e ícones continuaram correspondendo ao perfil em todas as execuções.
  Os avisos `xrdb`/XCB são esperados nesse teste sem servidor X; não houve falha
  na aplicação dos arquivos de configuração.

Capturas da verificação solicitada estão em
`/tmp/irix-verificacao-20261006-uM1qlZ`: ambas as decorações em KWin real isolado,
antes/depois de redimensionar, galerias de estados Qt Quick e ícones instalados.
A captura da sessão principal falhou; essas imagens são do compositor de teste,
carregando os pacotes instalados. `resultado.json` registra as 480 verificações
automatizadas anteriores; o teste adicional de restauração GTK/Qt elevou o total
para 481 testes Python.

Comandos de desenvolvimento para os testes Qt (requerem PyQt6 QtQuick/QtTest;
`QtTest` aqui é o módulo Python, não o plugin QML):

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software dbus-run-session -- \
  /usr/bin/python3 classic-rewrite-rc1/tests/test_native_render.py
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software dbus-run-session -- \
  /usr/bin/python3 classic-rewrite-rc1/tests/test_native_input.py
```

Benchmark local, backend software/offscreen, 60 amostras após aquecimento,
janela aproximadamente 1600×1000; cada amostra altera tamanho, processa eventos
por 1 ms e captura o frame. Mediana anterior: **232,27 ms**; nova: **4,43 ms**.
Essa medida inclui a captura e não equivale a FPS/latência no compositor da sessão.
A comparação visual garante a arte, não o desempenho em toda GPU/distribuição.

A instância QML já carregada no KWin da sessão precisa de novo login para carregar
os arquivos substituídos de forma garantida. Não há reinício forçado de compositor.
As dependências de execução (Plasma 6/Aurorae/KSvg/Kvantum Qt 6) são verificadas e
continuam sendo fornecidas pela distribuição; o repositório fornece os temas.

Referências técnicas: a [documentação do Canvas Qt](https://doc.qt.io/qt-6/qml-qtquick-canvas.html)
explica o custo de upload de textura nas atualizações; o protocolo de invalidação
usado após instalar ícones é o sinal da sessão definido pelo próprio
[KIconLoader](https://github.com/KDE/kiconthemes/blob/master/src/kiconloader.cpp).


## Ajuste de feedback dos botões

A pedido do usuário, ações comuns agora ocorrem na soltura: Classic mantém
`armed` durante a pressão, permitindo que seu glyph mostre o relevo. O segundo
clique do menu também conserva o relevo até a soltura que solicita fechar.
O Irixium conserva seus SVGs pressionados e o menu bitmap ganhou bordas de
relevo baixo. Clique direito abre o menu ao soltar, sem intervalo adicional.
Somente a ambiguidade de clique simples/duplo mantém o intervalo Qt já existente.
Não há novo timer, espera mínima ou Canvas da área inteira.

Referência consultada: [código oficial CDE/dtwm, WmCEvent.c](https://github.com/cdesktopenv/cde/blob/master/cde/programs/dtwm/WmCEvent.c),
`CheckButtonPressBuiltin` (`PushGadgetIn`) e `CheckButtonReleaseBuiltin`
(`SetClientState` para minimizar/maximizar).

Teste Qt real: nenhuma ação enquanto o botão está pressionado, imagens dos
estados normal/pressionado diferentes e exatamente uma ação na soltura.
Duplo clique ativa/inativa e durante mudanças de foco continua válido.
Capturas em `/tmp/irix-relevo-20261006`; a espera de 30 ms usada pelo teste para
capturar uma imagem não existe no código do tema.
