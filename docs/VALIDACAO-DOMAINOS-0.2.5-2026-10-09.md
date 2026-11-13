# DomainOS 0.2.5 — cores e ciclo de vida de menus e miniaturas

Esta rodada trata os relatos posteriores à instalação da 0.2.4: cabeçalhos e
controles ainda azuis, Operações sem menu, menu do botão direito inicialmente
pequeno e títulos entrando em seleção sem intenção nos checkboxes. Também
implementa o orçamento de miniaturas aprovado na segunda prancheta. As respostas
e suas notas ficam em arquivos privados de `/tmp`, fora da distribuição.

## Alterações e provas

| Área | Prova atual | Resultado e alcance |
| --- | --- | --- |
| Seleção, grupos e Operações | `/tmp/irix-domainos-popup-wayland-regressao-r1/RESULTADO.json` | 87/87; dois grupos reais, cinco janelas próprias, seleção parcial, restauração pelo título, lotes sobre dois UUIDs/PIDs exatos e três exclusões. |
| Menu nativo com Kvantum | `/tmp/irix-domainos-popup-wayland-kvantum-r2/RESULTADO.json` | 88/88; QMenu real 353 × 247, doze ações dentro da primeira abertura, cinco reaberturas, erro injetado e fallback. Zero diagnóstico QML/protocolo nesses ensaios privados. |
| Miniaturas visíveis | `plasma/tests/test_domainos_preview_budget.py` | 4/4; doze cartões completos, somente dois provedores visíveis, rolagem/fechamento cancelam a criação antiga, ação clicável antes da imagem. |
| Ciclo de vida e dica interna | `plasma/tests/test_domainos_thumbnails.py`, `plasma/tests/test_domainos_member_hint.py` | 16/16 e 4/4; troca do proprietário e reutilização da célula por outra identidade/PID descarregam o conteúdo. |
| Imagem Wayland atual | `/tmp/irix-domainos-miniaturas-wayland-budget-20261009-r2/RESULTADO.json` | 24/24; duas fontes do próprio processo, pintura azul confirmada na fonte e na miniatura, descarga e perfis reais intactos. |
| SVGs funcionais | `/tmp/irix-domainos-style-verification-025/verification.json` | 198/198 gates, 5/5 testes; KSvg, PlasmoidHeading e controles reais em quatro paletas offscreen privadas, inclusive troca no mesmo motor QML. 1.883 IDs/bounds comparados por esquema. Style 0.1.1 invalida o cache da arte. |

O texto da lista distingue `memberSelectionKeys` da seleção comum do ícone.
Sem caixa marcada, o título restaura/ativa. A primeira caixa inicia uma seleção
expressa; os títulos passam a acrescentar/retirar membros. Seleção de duas ou
mais janelas habilita Operações. Marcar caixas não restaura nem executa lotes.

O seletor usa um pai persistente. Operações conserva um snapshot dos alvos,
fecha as superfícies anteriores e abre no próximo turno do event loop, depois
de verificar novamente UUID/PID. O menu nativo segue a mesma sequência e
descarta uma criação parcial quando o provedor falha. Isso não adiciona um
timer de espera, repaint periódico ou nova tentativa automática.

Os SVGs anteriores ainda tinham cores opacas da referência, mesmo sem o arquivo
`colors`. As superfícies agora usam os papéis Background/HeaderBackground,
ViewBackground, ButtonBackground, TooltipBackground e Highlight. Texto e
símbolos usam os papéis correspondentes. Sombras e luzes misturam a superfície
temática com extremos branco/preto parcialmente transparentes, sem substituí-la
por uma paleta fixa. As bandas, tramas, limites e IDs continuam preservados.
O Classic independente e o backup aprovado não são modificados.

Cartões e alvos de clique são síncronos; apenas os provedores de imagem são
Loaders assíncronos. Cada Loader pertence ao proprietário atual e à região
visível. Sair da região, trocar de proprietário ou fechar cancela o anterior.
Não existe fila externa acumulando trabalho de ícones que já foram abandonados.

## Falha real observada e limites

Em 9 de outubro às **19:33:43 UTC**, o Plasma do lsi com a 0.2.4 encerrou com
erro Wayland `xdg_surface is already mapped`, objeto `xdg_popup#205`, saída 255.
O supervisor existente do KDE reiniciou o serviço. O log está preservado em
`/tmp/irix-domainos-wayland-fatal-20261009.log`; o relatório da entrega 0.2.4
foi atualizado para `delivered-with-later-runtime-failure`. Seu ZIP permanece
congelado.

O objeto do protocolo não identifica qual componente QML o criou. A nova prova
exercita a transição de grupo para Operações e o menu nativo sem reproduzir
o erro. Isso verifica a sequência corrigida; não comprova a causa do objeto
205 nem a ausência de toda falha futura em aplicações pessoais.

O monitor externo tem sondas periódicas e não viu a saída entre duas consultas;
a mudança de PID e o journal complementaram seu resultado. Ele não mata
aplicações, não modifica a unidade do KDE e não reinicia o Plasma. O `finally`
libera guardas quando o controle retorna, sem desfazer uma ação já enviada.
Objetos gráficos permanecem na thread exigida pelo Qt; as consultas externas
usam os processos auxiliares assíncronos já existentes.

Os ensaios funcionais de reset continuam **42/43**, com o diagnóstico instalado
do PromptDialog Kirigami idêntico à baseline. Não se altera o SDK nem se renomeia
esse resultado como aprovação integral.

## Tentativas preservadas

O ensaio offscreen de menus parou após 34 checks numa interação do fixture.
Kvantum r1 falhou antes do applet, pois a preparação confundia QStyle QWidget
com um módulo Qt Quick Controls. O r2 separa essas configurações e usa o QStyle
Kvantum realmente instalado. Miniaturas r1 ficou em 22/23: `QWidget::raise()`
não garantia pintura da fonte Wayland. O r2 ativa somente a fonte própria e
confirma separadamente sua pintura antes de comparar o frame. Todos esses
resultados falhos permanecem preservados.

A segunda prancheta foi analisada sem alterar suas respostas. O quadro de
soluções em GTK apresenta mecanismos, código, resultados e limites; não integra
o pacote nem substitui a avaliação final das sessões lsi e p001532.
