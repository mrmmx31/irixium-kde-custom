# Procedimento da VM Domain/OS SR10.4 deste projeto

Este complemento adapta a skill geral `mame-live-control` à única máquina
histórica autorizada neste repositório. A instância é o clone assistente
Domain/OS SR10.4 + HP VUE 2.01 em Apollo DN3500. Use apenas a cópia em
`vm/domainos-sr10.4-assistant/runtime/`; o symlink antigo em Tempia serve só
para compatibilidade. O disco vivo e o nome em `private/` são hard links ao
mesmo inode, não backups. Consulte `docs/DOMAINOS-REGRAS-VM.md` para manifesto,
backup-base, rede isolada e recuperação.

## Antes de interagir

1. Execute `vm/domainos-sr10.4-assistant/verify.sh`. Ele aceita coexistência
   somente depois de validar discos abertos, namespaces e canais exclusivos de
   todos os MAMEs visíveis; não é lock atômico. Revalide PID, inode, estado do
   convidado e rede após reiniciar o host e anuncie cada instância no canal de
   coordenação antes de iniciar ou encerrar uma VM.
2. Preserve o perfil validado: CPU principal 100%, CPU Ethernet 10%, frameskip
   4 e throttle desligado. Não aumente clocks antes de a rede do convidado
   responder.
3. Leia o estado atual da ponte e da captura. Use um único controlador e não
   publique comando novo enquanto houver pedido pendente ou resultado incerto.
4. Faça primeiro uma consulta limitada e uma captura atual da tela certa. Só
   envie entrada gráfica se a imagem confirmar que o alvo pretendido está
   visível. Coordenadas observadas em uma captura não são coordenadas universais.

## Teclado, mouse e foco

- Tela DomainOS preta/em repouso: confirme processo MAME, disco canônico,
  identidade da VM e canal; a imagem preta é a condição para enviar uma única
  tecla ao convidado, não um motivo para parar. Confirme que a imagem voltou
  antes de qualquer outra entrada. Esse passo cabe ao agente: não
  pergunte ao usuário se a tela está preta nem peça que ele a acorde. Não comece
  movendo o mouse. Nesta cópia assistente,
  R381 e R393 demonstraram que um pulso de um quadro em
  `:kbd:keyboard4/Shift`, liberado automaticamente no terceiro quadro, acordou
  a tela. Isso é tecla injetada no convidado, não tecla física do host. Verifique
  a imagem e a liberação; não repita pulsos às cegas. Se não despertar, verifique
  a entrega do evento ao convidado e reporte o resultado sem transferir
  automaticamente esse passo ao usuário.
- AltGr solta a captura do ponteiro. O comportamento observado é que reativar
  ou focar a janela MAME pode capturá-lo de novo mesmo com o ponteiro fora. Isso
  é captura/foco do host, não estado do mouse no Domain/OS. Não prometa que a
  soltura persiste ao alternar janelas.
- Antes de clicar, valide a janela do host pelo PID MAME real; preserve e
  restaure o foco/revert mode. Não envie evento para a janela host que estava
  anteriormente ativa.
- Consulte as portas e máscaras pelo probe atual. Os valores observados no
  adaptador Apollo (`:kbd:mouse1`: esquerda 16, meio 64, direita 32;
  `:kbd:mouse2`/`:kbd:mouse3`: contadores relativos) são exemplos a confirmar,
  não constantes para outras versões ou convidados.
- Use hold de curta duração com liberação automática e confira o estado da
  operação (`done`, `reason`, `error`, `cleanup_error`) antes de continuar.
  Prazos em tempo emulado não avançam se a VM estiver pausada. Em pendência,
  solte a operação existente pelo canal; não dispare outra.

## Capturas e evidência

- Guarde novas capturas/rascunhos em `~/tempia`, nunca em `/tmp`. Use nomes
  inéditos e falhe se o destino existir. Uma captura sobrescrita não pode ser
  validada pelo hash antigo; mantenha uma errata se isso ocorrer.
- Identifique cada imagem como pixel nativo do convidado (`screen:snapshot`) ou
  captura da janela MAME no host; overlays do menu MAME podem não aparecer no
  snapshot do convidado. Anote versão, escala, estado normal/pressionado/liberado
  e operação que produziu a imagem.
- Separe observação do usuário, pixels medidos, configuração/recursos, defaults
  comprovados em C e interpretação. Um teste de entrada ou integridade não
  atesta fidelidade visual. Use somente SR10.4 + VUE 2.01 para métricas
  históricas; outra versão de Motif pode ajudar a entender algoritmo, não
  comprovar a aparência desta máquina.
- Antes de encerrar, confira que os botões/contadores injetados foram liberados,
  callback terminou, foco/captura estão restaurados, perfil e estado de pausa
  continuam corretos, e o canal não tem pedido pendente. Registre limites e
  próximo passo na fila de revisão.

## Trabalho de outros projetos

Não importe discos, endereços, credenciais, canais, estado do convidado ou
evidências pertencentes a outras VMs/projetos. Procedimentos genéricos de
engenharia reversa (proveniência, isolamento de artefatos, diferenciação entre
análise host e prova no convidado) podem inspirar os recibos deste projeto, mas
não substituem a VM, suas autorizações ou suas regras. Um contexto paralelo de
engenharia reversa não concede acesso cruzado nem autoriza ações MAME.
