# Bloco 2 — botões e correção de pressão das setas

Revisão: **0.2.0-rc1**. Manutenção: `mrmmx31`.
Base: `#kvantum-classic-rc1`, commit `4e9e56617d07374723b9db6a9716b3b861b4b028`.

## Correção pontual do bloco 1

O desenho da barra da rc2 foi aprovado pelo usuário. O relato pendente foi a
falta de relevo inferior ao clicar nos botões. No gerador rc2, a pressão invertia
as duas faixas da célula, mas a máscara triangular continuava inteiramente plana.
Nesta revisão, uma faixa clara de um pixel aparece no lado inferior/direito da
impressão do triângulo durante pressão/toggle. A máscara escura continua nas
mesmas coordenadas. O desenho de repouso/hover/desativado permanece idêntico.

Não foi alterada a largura 18, o comprimento mínimo 34, o puxador, o trilho,
as ranhuras ou qualquer um dos estados desses três componentes. Não se alteram
os eventos nativos, a repetição automática ou os limites da rolagem. Os mapas
pressionados das setas são adaptações declaradas: não temos screenshot SGI de
cada um desses estados. A causa exata de qualquer falha de entrega de eventos
na sessão não foi comprovada; a galeria agora verifica a cor do relevo durante
uma pressão real, além de verificar que a ação foi executada.

## Botões de comando, padrão e ferramenta

Os recursos do bloco 2 têm prefixos novos e separados. Os recursos anteriores
`ic-button` e `ic-tool` continuam no SVG porque campos, menus e outros controles
os herdam ou referenciam. Eles não foram redesenhados nesta etapa.

| Grupo | Prefixo | Tratamento |
|---|---|---|
| PanelButtonCommand | `ic-command` | Perfil normal de 3 faixas como no Help Viewer; inversão só do bisel interno durante pressão. |
| PanelButtonTool | `ic-palettebutton` | Face de ferramenta elevada; pressão de 2 faixas, sem deslocamento. |
| ToolbarButton | `ic-toolbarbutton` | Repouso/hover transparente para controles autoRaise; pressão e seleção visíveis. |
| Marcador de padrão | `ic-command-default` | Um contorno externo; não cobre o relevo interno quando o botão está pressionado. |
| Foco de teclado | `ic-focus` existente | Preservado, distinto de hover e do indicador de botão padrão. |

`focused` no SVG significa estado de ponteiro em vários caminhos do Kvantum,
não necessariamente foco de teclado. O desenho de hover de cada família é igual
ao repouso. O foco continua sendo desenhado pela primitiva Focus do motor.
Não se adiciona brilho nem animação. Botões de paleta têm face elevada e botões
em toolbar seguem a separação opcional ToolbarButton suportada pelo motor.
O aplicativo ainda decide `autoRaise`, botão plano, tamanho do ícone, ação,
menu, e se o botão está disponível. Um tema não altera essas decisões.

Pressão e seleção persistente usam bisel rebaixado. A seleção persistente tem
face `#919191`, em vez de `#999999`, para ser distinguível do gesto momentâneo.
Os textos e ícones não mudam de coordenadas. As dimensões dos frames, margens,
fonte, área clicável e mínimo de altura 22 não foram reduzidos.

Os recursos `*-disabled` são fornecidos. O Kvantum 1.1.4, em alguns caminhos de
push/tool buttons, usa o mapa normal/toggled com opacidade 0,7, além da paleta
desativada do texto. Por isso não se deve apresentar o mapa disabled isolado
como uma captura exata desse estado do plugin. A galeria testa que um botão
indisponível não executa a ação; o tema não habilita controles bloqueados.

Separadores de botões de ferramenta com menu foram incluídos sem criar espaço
extra. A lógica de popup/seleção continua nativa do Qt. Retorno do relevo na
soltura é imediato; nenhum temporizador mantém o desenho pressionado.

## Preservação de heranças

Foram fixados os recursos anteriormente herdados em GenericFrame,
DropDownButton, CheckBox, ToolboxTab, HeaderSection e ItemView. A configuração
efetiva de todos os grupos fora de PanelButtonCommand/PanelButtonTool é
comparada à rc2, exceto o novo grupo ToolbarButton e o comentário da versão.
Nada é escrito em Aurorae, GTK, fontes, escala, Irixium moderno ou decoração
Classic. O instalador mantém o comportamento recuperável já integrado; apenas
passa a reconhecer também o manifesto `0.2.0-rc1`.

## Referência visual e alcance

O frame do botão Close no Help Viewer da captura IRIX fornecida foi conferido
no retângulo `(936,470)-(988,501)`, PNG 1024×768. Suas 462 posições de borda
coincidem com o perfil de comando normal gerado. Texto/ícone foram excluídos;
o resultado não certifica outros tamanhos nem a rasterização Qt.

SGI, Indigo Magic User Interface Guidelines, ch. 9, Pushbuttons:
https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch09.html

A documentação descreve botões retangulares com texto/ícone centralizado e
indisponibilidade sem remoção. A figura online 9-1 não pôde ser baixada nesta
revisão; a referência pixel a pixel utilizada foi o PNG fornecido. Não é feita
alegação de ter obtido ou validado todos os estados originais da SGI.

Kvantum 1.1.4 — grupo ToolbarButton, herança e Focus:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/doc/Theme-Config

Kvantum 1.1.4 — despacho dos estados e tratamento de opacidade:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp

## Aceitação local

1. Abra `bash kvantum/prever-botoes.sh`. Mantenha a pressão do mouse para
   inspecionar o relevo: um clique rápido o mostra por pouco tempo, como no Qt.
2. Setas: verifique o traço claro abaixo/à direita; solte e confirme o retorno.
   Confira ambas as orientações, os extremos e o controle indisponível.
3. Comando e padrão: confirme a faixa clara na base e direita, sem salto do
   texto. O contorno de padrão não deve esconder essa faixa.
4. Ferramentas: paleta, toolbar plana, toggle e parte de menu. A ação e o popup
   não devem ser acionados duas vezes. Teste sair/voltar e soltar fora.
5. Teste Tab, Espaço e Enter; indisponíveis não respondem. Confira com a fonte
   usada na sessão, além da fonte de 14 pixels da galeria.
6. Não reavalie o tamanho da barra pelo comprimento do puxador; depende do
   conteúdo. Puxador, ranhuras e trilho devem permanecer iguais à rc2 aprovada.

Automação opcional usando plugin Qt 6 real:

```sh
bash kvantum/prever-botoes.sh --testar
bash kvantum/prever-botoes.sh --capturas /tmp/irix-botoes-qt
```

As capturas são feitas durante eventos reais do Qt, em plataforma offscreen,
quando os bindings e o plugin Kvantum estão presentes. Falta de dependência
retorna 77; falha de verificação retorna erro. Não usar uma renderização Fusion
como substituta nem tratar esses códigos como aprovação visual.
