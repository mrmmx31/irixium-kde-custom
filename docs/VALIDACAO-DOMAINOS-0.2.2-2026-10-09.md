# DomainOS 0.2.2 — correções e entrega de 2026-10-09

## Ocorrência posterior: travamento ao mostrar uma dica

O usuário relatou travamento depois da entrega e identificou o hover de uma dica
como última ação. A medição do processo lsi encontrou timeout do D-Bus e 6,01 s
de CPU em 6,01 s de observação. Duas pilhas capturadas mostraram processamento de
geometria de PopupPlasmaWindow e pintura de máscara FrameSvg. Esses dados estão
em `/tmp/irix-domainos-freeze-022-state.json` e nos arquivos
`/tmp/irix-domainos-freeze-022-*-stack*.txt`.

Foi aplicada uma recuperação temporária somente à cópia instalada em lsi:
`DomainOSWindowThumbnails.active=false`, preservando o arquivo original em
`/tmp/irix-domainos-freeze-022-WindowThumbnails-original.qml`. As preferências não
foram alteradas. Após recarregar somente seu Plasma, o D-Bus voltou a responder.
Isso desativa provisoriamente dicas/miniaturas dessa apresentação; não é a
correção final nem comprova que a versão original esteja estável.

A investigação continua com teste de dica em Wayland, escala 0,5 e títulos longos.
O primeiro fixture teve conteúdo não materializado e não é prova positiva; o
segundo confirmou uma dica de 488 × 154 com timers responsivos, sem reproduzir o
travamento do painel completo. A versão 0.2.2 não deve ser considerada aprovada
para uso definitivo por seus ensaios anteriores. O ZIP congelado não foi alterado.

A correção posterior está documentada em
[DomainOS 0.2.3 — dicas e destaque](VALIDACAO-DOMAINOS-DICAS-2026-10-09.md).
Ela foi aplicada em lsi e reativa as dicas; a confirmação do hover na sessão real
continua separada dos testes privados. O pacote 0.2.2 não foi atualizado.

O restante deste documento conserva os resultados anteriores à ocorrência.

A 0.2.2 está instalada somente no perfil lsi. O Plasma desse usuário foi
recarregado pelo seu próprio `plasma-plasmashell.service`; os aplicativos ficaram
abertos. As preferências existentes foram comparadas chave a chave, os atalhos
foram preservados e permaneceu uma única barra. Nenhuma configuração global ou
do usuário p001532 foi alterada.

## Correções

- A roda da Iconbox percorre páginas, como as setas, por padrão. Não solicita
  ativação, restauração ou minimização de janelas. A alternativa de ativar pela
  roda permanece nas preferências, desligada por padrão.
- Quando a página realmente muda, fecha-se o seletor associado ao grupo anterior
  antes de reutilizar seus botões. O clique seguinte abre o grupo atual. No limite
  da paginação, sem mudança de página, o seletor permanece aberto. Os checkboxes
  selecionados são preservados.
- O seletor mantém os delegados de membros por identidade/PID durante mudanças
  reais do modelo. Isso conserva o hover e evita destruir a dica a cada atualização.
  A dica automática concorrente do ItemDelegate foi desativada.
- A largura da lista acompanha a área útil do ScrollView. Não há rolagem
  horizontal; títulos longos são abreviados e exibidos na dica. A altura considera
  cabeçalho, rodapé e até 15 linhas, limitada à tela. Botões continuam fora da
  área rolável. O modelo retém a geometria fechada, evitando um resize nativo
  tardio para zero membros antes da abertura seguinte.
- A faixa por trás do desenho era o fundo nativo do containment, não outra barra.
  Uma Binding retira esse fundo somente quando DomainOS é seu único widget.
  Adicionar outro widget restaura o fundo anterior. Não grava UserBackgroundHints
  nem altera SVGs do estilo. A máscara nativa continua contendo o desenho; não se
  afirma que seus pixels externos sejam idênticos ao estado anterior.
- A gaveta apresenta preferências permanentes, pins da taskbar e favoritos KDE
  em seções separadas, nessa ordem. Favoritos usam diretamente o modelo do menu
  Applications da barra, inclusive sua interface KDE opcional. Não são copiados
  para a configuração dos pins. Os comandos dos pins medem 28 × 28 px e deixam
  mais espaço para os nomes.

O KDE compartilha a associação dos favoritos entre clientes, mas mantém ordens
por cliente. A ordem garantida aqui é a do mesmo provedor usado pelo menu desta
barra; não se promete sincronização universal de reordenação entre outros menus.

## Evidências finais

| Ensaio | Resultado | Relatório |
| --- | --- | --- |
| Cliques, seleção, roda e limites da paginação em Qt | 85/85 | `/tmp/irix-domainos-group-sizing-iconbox-qt-r8-final/RESULTADO.json` |
| Tamanho e dicas nativas, 3/15/16 membros e atualizações reais | 100/100 | `/tmp/irix-domainos-group-sizing-native-r13-final/RESULTADO.json` |
| Roda e clique em nove grupos, 18 janelas reais privadas | 19/19 | `/tmp/irix-domainos-group-wheel-native-r5-final/RESULTADO.json` |
| Fundo do painel, proporções, máscara, flutuação e restauração | 44/44 | `/tmp/irix-domainos-native-backdrop-production-r2/RESULTADO.json` |
| Gaveta, favoritos nativos, ordem, lançamento e comandos compactos | 39/39 | `/tmp/irix-domainos-gaveta-favoritos-native-r3/RESULTADO.json` |
| Atualização recuperável no perfil lsi | 9/9 | `/tmp/irix-domainos-lsi-022-upgrade.json` |
| Conferência posterior em lsi, recursos e ausência de erros QML | 7/7 | `/tmp/irix-domainos-lsi-022-final.json` |

Os testes automatizados dos seletores usaram perfis/processos próprios e foram
encerrados. A prova do fundo foi repetida depois do congelamento das fontes.
Tentativas anteriores que falharam continuam guardadas: o primeiro ensaio do
fundo detectou uma edição concorrente do Iconbox, e o Qt R7 detectou alteração
do arquivo pessoal de painéis durante o intervalo, sem atribuí-la ao teste.
Esses resultados não foram reclassificados como aprovação.

Passaram também os 16 testes de migração de preferências, defaults/schema e
ponte, e os 5 testes do pacote independente. A conferência posterior de lsi
encontrou as quatro árvores instaladas idênticas às fontes congeladas, o novo
processo Plasma ainda ativo e zero erros QML do applet no journal desse processo.
A flag `iconboxWheelActivates` está ausente na configuração de lsi e recebe o
default `false` do schema atualizado.

O relato de ativação da roda na sessão anterior não era explicado por uma
preferência `true` salva. A recarga fria garante que a nova entrega use outro
processo/engine QML; não se apresenta essa observação como prova isolada de que
todo o comportamento relatado foi causado pelo cache.

## Distribuição e avaliação pessoal

Arquivo: `/home/lsi/Downloads/irixclassic-domainos-0.2.2.zip`, 588.790 bytes,
210 arquivos. SHA256:
`6f1672ce27d38161bd78a22db07728dde71a32c1c85af2f52db068bacba21ea7`.
O manifesto, os hashes e a igualdade com as fontes correntes foram conferidos em
`/tmp/irix-domainos-package-022-final.json`. O ZIP e seu `.zip.sha256` foram criados
como arquivos novos; a 0.2.1 e o backup aprovado em Downloads/backups ficaram
intactos. Instruções: [DomainOS 0.2.2](DOMAINOS-0.2.2.md).

Recibo ativo:
`~/.local/state/irixium-domainos-panel/backups/b24754297a6446a4ba3e10db9e964aec/receipt.json`.

O formulário GTK temporário permanece aberto. Suas respostas serão salvas em
`/tmp/irix-domainos-checklist-20261009-uid1000.json`; não faz parte do repositório.
Para o teste final na sessão KDE de p001532, o comando temporário é
`/tmp/irix-domainos-teste-022` pelo Alt+F2. A integridade real do launcher foi
conferida sem abrir GUI nem instalar no perfil desse usuário:
`/tmp/irix-domainos-launcher-022-verificacao.json`.

O launcher usa recursos/configurações privados numa janela independente.
Suas ações manuais de tarefas/Pager/favoritos atuam nos serviços reais do próprio
usuário. Ele não substitui o painel, não executa essas ações automaticamente e
não é uma sessão de janelas fictícias. Ao trocar de área pelo Pager, sua janela
normal pode permanecer na área de origem.

Ainda faltam, para concluir o goal completo, as respostas pessoais do checklist,
a avaliação final desta versão em p001532 e a confirmação do bloqueio físico da
sessão. Não foi executado bloqueio, logout ou desligamento pessoal para simular
essa confirmação. O arraste de janelas entre cartões do Pager continua adiado
conforme a decisão registrada.
