# DomainOS 0.2.6 — posição e regras das dicas

Esta correção responde às miniaturas que cobriam os títulos do seletor e às
dicas redundantes. Preserva o desenho aprovado, o esquema de cores, a seleção
por checkbox e as preferências existentes. Não modifica outro usuário.

## Comportamento

- Títulos completos e visíveis não mostram dica textual. Um título abreviado
  aguarda `Kirigami.Units.toolTipDelay`, o mesmo intervalo do estilo KDE instalado.
- A prévia fica acima do seletor inteiro. Uma lateral é o primeiro fallback;
  outra região externa é usada quando necessário. Sem espaço exterior seguro,
  a prévia não cobre os itens da lista.
- Sair lateralmente fecha a prévia. Uma passagem para outra linha libera o
  proprietário anterior, sem alternar superfícies antigas. Rolar a lista e
  reentrar mede a posição nova do título.
- A miniatura não acrescenta o título inteiro como outra dica. Somente uma
  legenda abreviada pode mostrar o nome completo, depois do intervalo nativo,
  dentro da área da imagem. Texto extenso tem rolagem nessa área.
- O título textual é literal. O nome completo permanece enquanto o ponteiro
  pertence à região; sair fecha e cancela apresentações pendentes.

A recomendação de não repetir nomes visíveis e usar o intervalo da plataforma
segue a [orientação primária da Microsoft](https://learn.microsoft.com/en-us/windows/win32/uxguide/ctrl-tooltips-and-infotips).
A miniatura interativa é tratada separadamente da dica passiva. O intervalo não
retarda cliques, ações nem o relevo dos botões. Não existe repaint periódico.

## Provas desta fonte

| Ensaio | Resultado | Alcance |
| --- | --- | --- |
| Seletor e prévia nativos | 71/71 | 55 critérios do host e 16 de isolamento/runner; dois clientes próprios com UUID/PID reais. |
| Dicas dos títulos | 11/11 | Intervalo da plataforma, texto literal, nome inteiro sem dica, cancelamento, identidade e proprietário. |
| Ciclo de vida dos cartões | 16/16 | Criação/descarte, cartões sem imagem, legenda cortada e cancelamento. |
| Orçamento de criação | 4/4 | Somente cartões da região visível recebem provedores. |

O ensaio nativo usa a Iconbox e o modelo de tarefas de produção em compositor,
D-Bus e perfil Wayland privados, com o executável instalado `plasmawindowed`.
A entrada percorre as QWindows reais: pares QPA Leave/Enter drenados antes de
MouseMove/Press/Release. Foram observadas 15 transições, escala 1 e ausência do
mouse grab da plataforma. Não se invocam handlers de clique QML nem se inventam
IDs de janela. É uma prova dirigida de eventos Qt, sem alegar entrada física
pelo seat do compositor.

Passaram o intervalo anterior à apresentação, ausência de dica nos nomes completos,
texto literal, posição acima do seletor inteiro, cancelamento antes do intervalo,
troca de linha e descarte do proprietário anterior, saída direta para outro cliente,
entrada no cartão e sua ativação única pelo UUID/PID esperado. O modelo nativo
confirmou a janela alvo ativa. Título simples, checkbox, Operações e clique externo
continuaram funcionando; a janela auxiliar fecha antes do pai ou menu sucessor.

A geometria medida foi prévia 288 × 214 em `(196, 260)` e seletor 400 × 142 em
`(150, 474)`: a prévia termina onde começa o seletor, sem cobrir suas linhas.
Os PNGs são capturas de cada superfície nativa, não uma montagem nem captura
integral do compositor. Nesse compositor privado a imagem não estava disponível;
o cartão mostrou a indisponibilidade e continuou clicável. Esses 71 critérios
não são uma nova prova de pixels do PipeWire.

Relatórios privados, não incluídos no ZIP:

- `/tmp/irix-domainos-member-hint-wayland-r16/RESULTADO.json`
- `/tmp/irix-domainos-member-hint-unit-final-r16-RESULTADO.json`
- `/tmp/irix-domainos-hints-006-final-unit-20261009-r1/RESULTADO.json`

Os hashes dos componentes são iguais entre esses ensaios. O GroupMemberHint
final tem SHA256 `87ea1af27d7628687b9e119ab5321f75954dab552be9a8eae5d4a2af9de5b40c`;
PreviewContents tem `ac3188f8b6aa90e972bf8d771989b1a772918fd69c7474b3adb0703bc77b5632`.
Os testes offscreen não usam o compositor real nem oferecem prova de captura.

As tentativas anteriores permanecem preservadas. As primeiras usavam MouseMove
sem os Enter/Leave que a plataforma entrega ao trocar de superfície; sua atribuição
a uma falha de produção ficou inconclusiva. A r15 completou essa entrada e revelou
uma falha concreta ao sair da prévia para outro cliente: os dois hovers estavam
falsos, mas a apresentação continuava aberta. A correção lê os estados atuais
após o mesmo evento, em vez da posição antiga que HoverHandler mantém no Leave.
A r16 repetiu e completou o percurso, sem erros QML ou protocolo Wayland.

## Implementação e limites

O seletor mantém um único proprietário de apresentação. A janela auxiliar
`Qt.ToolTip` recebe pai e flags antes de seu primeiro mapeamento; a anterior
é ocultada e descartada antes da sucessora ou do fechamento do seletor.
Ela não usa o objeto de tooltip compartilhado do Plasma nem a janela interna
`QQuickPopupWindow` para essa apresentação aninhada. A legenda abre uma
`Popup.Item` dentro da própria prévia, sem outra superfície nativa.

A posição da linha é medida novamente depois da rolagem. O seletor observa
movimento efetivo dentro da sua superfície; a saída de uma superfície aguarda
apenas o término do evento para verificar os hovers atuais da linha e prévia.
Isso permite transferir o ponteiro sem destruir o cartão antes do clique e fecha
uma apresentação sem proprietário. A política de clique externo do seletor
permite a ação do cartão enquanto o ponteiro está na sua prévia e retoma o
fechamento externo ao sair. Não há plugin binário, polling ou timer de repaint.

A revisão primária está preservada em
`/tmp/irix-domainos-native-qpa-crossing-review-20261009.json`. As funções do Qt
usadas somente pelo injetor de QA não são dependências novas do painel distribuído.

A posição respeita os limites do monitor da janela. Esse objeto QML não expõe
a área útil depois dos struts de painéis de terceiros. Um seletor que ocupa
toda a tela pode não deixar espaço para a prévia. Títulos passivos arbitrariamente
extensos continuam limitados à região disponível; não se declara leitura
integral de qualquer comprimento nessa apresentação.

As provas anteriores de pixels atualizados Wayland, menus, cores e resets
conservam seu escopo e hashes próprios. A tentativa X11 sem captura continua
registrada como falha, e o diagnóstico Kirigami dos resets permanece idêntico
à baseline instalada. Não se altera o SDK nem se renomeiam falhas como sucesso.

Instalação/restauração e avaliação pessoal de lsi/p001532 têm registros
separados. Os ZIPs anteriores e o backup aprovado permanecem congelados.
