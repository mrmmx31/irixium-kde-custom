# Continuidade do trabalho DomainOS

Regra de temporários: novos arquivos, capturas, canais e diretórios temporários
deste projeto ficam em `~/tempia`, nunca em `/tmp`. Referências e canais legados
já existentes em `/tmp` podem ser lidos sem movê-los; não sobrescreva nem migre
um pedido pendente.
Os registros ativos do contexto Tema foram movidos para
[`records/ia-tema/`](records/README.md). `~/tempia/ia-tema` é apenas um symlink
de compatibilidade para esses registros; não grave novos temporários por ele.
Use `~/tempia/domainos-theme-work/` para novos arquivos deste contexto. Preserve
o symlink enquanto a sessão GTK2 Xephyr `:187` ou leitores dos documentos de
estudo estiverem abertos.

Entrada central: [índice de regras](docs/DOMAINOS-INDICE-REGRAS.md).
Regra obrigatória: todas as adaptações acompanham os papéis atuais do esquema
KDE; não inserir cores finais estáticas. Somente o LED e a luz do Pager têm
exceção de cor de sinal, com proteção de contraste. Consulte a
[regra de cores](docs/DOMAINOS-REGRAS-CORES.md) antes de qualquer correção visual.

Ao iniciar ou retomar trabalho no tema DomainOS, leia
[as regras comuns](docs/DOMAINOS-REGRAS-ROLAGEM.md),
[a fila de revisão](docs/DOMAINOS-FILA-REVISAO-VISUAL.md), o estado da etapa ativa
e o registro mais recente de evidências. Consulte também as decisões consolidadas
quando houver dúvida sobre uma preferência já definida pelo usuário.
Consulte também [as pranchetas e o protocolo de retorno](docs/DOMAINOS-CHECKLISTS-REVISAO.md).
Leia o JSON de respostas mais recente antes de repetir verificações. Agrupe o
projeto em dez itens relacionados e mantenha outra lista curta para a revisão
visual. Não preencha a aprovação do usuário a partir de um teste técnico.

O usuário pediu execução por etapas: somente uma família de controles recebe
correções visuais por vez. Registre novos defeitos na fila antes de mudar de tarefa.
Leia a regra antes de desenhar; traduza o contrato único
`tools/domainos_scrollbar_rules.json` para a implementação ativa e depois compare.
Distinga recursos configurados, defaults C comprovados e medidas da VM.
Conclua a etapa ativa com comparação visual nativa e registre seu resultado;
testes de integridade não comprovam fidelidade histórica de outra família.
Reutilize evidências válidas com seu escopo e hashes. Repita apenas o que tiver
entrada alterada, falha ou uma dúvida que a prova anterior não cobre. A falta
de avaliação manual não impede trabalho independente já autorizado.

Use exclusivamente Domain/OS SR10.4 com HP VUE 2.01 como referência histórica.
Fontes Motif de outra versão podem explicar algoritmos, mas não substituem a VM
ou comprovam métricas e aparência do SR10.4.

Preserve a VM e seu perfil de desempenho, as configurações pessoais dos usuários
e o backup aprovado em Downloads. As comparações e intervenções gráficas devem
usar os ambientes já autorizados. Não acrescente outra confirmação para ações
que o usuário já autorizou.

## VM de referência do projeto

A cópia assistente do Domain/OS SR10.4 com HP VUE 2.01 pertence exclusivamente
a este projeto. Sua regra canônica, identificação, rede isolada, perfil do MAME,
despertar da tela e recuperação estão em
[DOMAINOS-REGRAS-VM.md](docs/DOMAINOS-REGRAS-VM.md). O runtime local canônico
fica em `vm/domainos-sr10.4-assistant/runtime/`; o antigo caminho em Tempia é
um symlink de compatibilidade. O disco em `runtime/discos/` e o nome em
`private/` são hard links para o mesmo inode. Não apagar, substituir, mover,
compartilhar com outro projeto nem copiar por cima enquanto MAME estiver aberto.
Os diretórios `runtime` e `private` são excluídos do Git; versionam-se as regras
e o manifesto, não o disco proprietário de 398 MB nem o estado mutável. O
backup aprovado em Downloads é a base original, não substitui o estado atual do
clone. Antes de iniciar ou restaurar, leia a regra e confirme a identidade do
disco usado pelo MAME.

Use também a [skill MAME do projeto](skills/mame-live-control/SKILL.md) para
identificar a instância e controlar mouse, teclado, captura e imagens. Tela preta
por repouso na VM se resolve enviando uma tecla ao convidado: confirme o processo
MAME, o disco canônico, a identidade da VM e o canal; a imagem preta é a condição
para enviar um único pressionamento, não um motivo para parar. Confira se a
imagem voltou antes de qualquer outra ação. Não pergunte ao usuário se a tela
está preta nem peça que ele a desperte; esse passo cabe ao agente. Não comece
tentando mover o mouse. Distinga a tecla recebida pelo convidado do foco/captura
do teclado no host. Não repita pulsos sem verificar o resultado.
Registre capturas novas em `~/tempia` com nomes únicos e nunca sobrescreva uma
evidência anterior. A VM desta árvore é a única referência histórica do projeto.

## Coordenação entre VMs MAME

Use `#coordenacao-vm-mame` somente para avisos que evitem conflito entre as
instâncias dos projetos `rui`, `tema` e `prancheta`: início, encerramento,
conflito de processo/disco, dependência ou decisão compartilhada. Não publique
progresso rotineiro nem perguntas já respondidas nos registros do projeto.
Antes de iniciar, confira avisos recentes e processos existentes. Ao iniciar,
identifique o alias/projeto, workspace, serviço, PID MAME, caminho do disco e
endereço de rede com portas FTP/Telnet; publique esses dados no canal. Ao
encerrar, publique que a instância foi desligada. Cada contexto mantém sua VM,
disco mutável e serviço próprios dentro de seu workspace, com endereço e portas
sem colisão. Nunca abra o disco de outra IA nem compartilhe um disco mutável.
Se a propriedade de uma instância ou disco estiver ambígua, não envie entrada
nem encerre o processo; anuncie o conflito e aguarde a identificação do dono.

Para este projeto, o endereço reservado é `10.253.104.20`, FTP `21` e Telnet
`23`; não altere essas portas sem coordenação. O `.gitignore` exclui `private/`
e `runtime/`, que contêm o disco e o estado mutável; regras, manifesto e
ferramentas reutilizáveis permanecem versionados. A VM da árvore do XChat não
é automaticamente uma instância independente deste projeto.

Atualize a fila antes de encerrar a interação: evidências obtidas, diferenças
restantes e próximo item. Informe ao usuário o avanço estimado e sua base,
sem transformar contagens de testes em porcentagem de fidelidade visual.

## Laboratório de temas

Toda ação, botão, combobox, campo numérico e controle de ajuste deve ter uma
dica que explique sua finalidade e unidade. Medidas nativas, mínimos do toolkit
e dimensões personalizadas devem ser distinguíveis. As comparações mantêm
coordenadas correspondentes e escala 1:1. Não apresentar uma aproximação
desenhada como renderização nativa de GTK, Qt ou Plasma. A ferramenta pode
abrir na sessão normal do usuário; testes que alterem o desktop permanecem
isolados. O usuário define quando usar Xephyr.

## Fila autorizada na prancheta Motif

Para as próximas atividades da ferramenta e do tema, consultar a prancheta
Motif C99/MVC e seu [protocolo](tools/work-board/README.md). O usuário autoriza
por item salvo; somente executar itens com `user.authorized=true` para o escopo
atual. Avaliação visual, resposta a pergunta e silêncio não são autorização.
Tratar um item por vez; ler notas e revisões antes de agir. Esta regra substitui
a inferência de autorização geral para tarefas futuras desta fila.

Aceitar respostas parciais sem aguardar as demais. Ao ler, registrar a revisão
exata em `assistant.ack_revision`; não apagar texto, avaliação, autorização ou
horário do usuário. Responder em campo separado, no nível novice/intermediate/
expert escolhido. Perguntas e instruções novas têm itens próprios e posição
`after`; não executar texto como código. Atualizar o checklist e a fila, e
preservar rascunhos e respostas anteriores quando o escopo mudar.

## Segurança obrigatória da entrada de texto

Por instrução explícita do usuário, nenhuma aplicação/prancheta com entrada de
texto deve ser entregue sem desfazer/refazer de vários passos, copiar, colar,
recortar, selecionar tudo e os atalhos usuais (Ctrl+Z, Ctrl+Y/Ctrl+Shift+Z,
Ctrl+C/V/X/A), com menu de edição acessível. Testar texto de vários parágrafos
UTF-8, seleção, substituição, salvamento, troca de item e recarga. Não presumir
que os defaults Motif implementam esses atalhos. Preservar rascunhos em disco
sem convertê-los em respostas ou autorizações. Ações que descartem/substituam
texto devem ser recuperáveis. Uma entrega não está concluída sem essa prova.
