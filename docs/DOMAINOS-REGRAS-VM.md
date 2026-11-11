# VM Domain/OS SR10.4 de referência deste projeto

Esta máquina pertence exclusivamente ao projeto `irixium-kde-custom`. É a cópia
assistente do Apollo DN3500 com Domain/OS SR10.4 e HP VUE 2.01. Não é a VM
original do usuário, não é uma VM compartilhada com outros projetos e não pode
ser substituída por outra cópia só porque também inicializa Domain/OS.

## Disco e recuperação

O runtime vivo e canônico agora está dentro da árvore local do repositório:

```text
vm/domainos-sr10.4-assistant/runtime/
```

O disco fica em `runtime/discos/`. O nome em `private/` continua sendo um hard
link para o mesmo inode, sem duplicar seus 398.458.880 bytes:

```text
vm/domainos-sr10.4-assistant/runtime/discos/dn3500_sr10.4.assistant-20261018.awd
vm/domainos-sr10.4-assistant/private/dn3500_sr10.4.assistant-20261018.awd
```

O caminho antigo em `~/tempia/ia-tema/vm/shared/domainos-assistant-vm-20261018/`
permanece como symlink de compatibilidade para `runtime/`. Os nomes do disco no
repositório apontam para o mesmo inode; qualquer escrita do convidado afeta
ambos. O hard link não é snapshot nem cópia de segurança. O conteúdo muda com o
uso, portanto não trate um hash de sessão como imutável. Não copie, mova,
renomeie, restaure ou sobrescreva o disco enquanto MAME estiver usando-o. Para
uma cópia consistente, primeiro encerre a VM de modo controlado, preserve o
disco atual e só então faça uma cópia offline verificada.

O backup-base aprovado, mantido intacto em Downloads, é
`DomainOS-SR10.4-backup-base-20261014.zip` (SHA-256 do arquivo
`fa79d20bf59c8dc28d7a9893186085411dca29c0650ea7dbea4739c0ea54206c`); seu
membro original `DomainOS-SR10.4/discos/dn3500_sr10.4.awd` tem SHA-256
`de5d44ad44b62a9ab7368902a8fb1c65aed7994877122794f5d9469706737645`.
Esse membro é a origem histórica, não o clone de trabalho atual: a VM assistente
tem estado próprio. Nunca restaure o membro-base por cima dela. O disco pesado
fica fora do histórico Git por tamanho e por conter o sistema convidado; este
documento e `vm/domainos-sr10.4-assistant/MANIFEST.json` são o registro
versionável. O runtime e o disco estão intencionalmente ignorados pelo Git por
conterem o sistema convidado e estado mutável. Um clone Git novo não contém a
VM; não apague o runtime local nem suponha que o repositório remoto o recuperará.
A localização oficial agora é `vm/domainos-sr10.4-assistant/runtime/`; o symlink
legado em Tempia existe só para compatibilidade.

## Inicialização e isolamento

Use apenas o lançador mantido junto da VM:

```text
vm/domainos-sr10.4-assistant/runtime/abrir-domainos-assistant-vm.sh
```

Ele inicia `/usr/games/mame` MAME 0.276 para `dn3500`, em janela, sem áudio,
plugins, autosave ou throttle, com `-frameskip 4`, OpenGL e entrada de mouse.
Usa ROMs locais existentes em `~/Downloads/DomainOS-SR10.4/roms`; ROMs e mídias
não são copiadas para este repositório. O VUE deve subir antes de aplicar o
perfil interativo. O script cria namespace de rede isolado, TAP e proxies FTP e
Telnet, e carrega o roteiro salvo na pasta da sessão.

O perfil validado pelo usuário é CPU principal em 100%, CPU da Ethernet em 10%,
frameskip 4 e throttle desligado. Os clocks das CPUs são aplicados depois de a
rede do convidado responder; não acelere a CPU principal durante a detecção da
placa, pois isso já impediu a interface `net0` de aparecer em um boot anterior.
O perfil correspondeu a aproximadamente 2,5× em amostras locais e o usuário
confirmou que a resposta do mouse ficou confortável. Não aumentar para os
valores exploratórios antigos (CPU 200%/400%, Ethernet 100%) sem nova
autorização e teste.

## Endereços e acesso

O convidado usa `192.168.240.2` dentro do namespace isolado. O alias de host
exclusivo desta cópia é `10.253.104.20`, FTP `21` e Telnet `23`. Não conectar ao
backend `192.168.240.2` diretamente pelo host. Execute clientes dentro do
namespace pelo helper:

```bash
vm/domainos-sr10.4-assistant/runtime/run-in-assistant-vm-network.sh telnet 10.253.104.20 23
```

FTP trabalha em modo ativo. O cliente deve anunciar/vincular o endereço de
retorno `192.168.240.1`. Telnet foi validado no endpoint atual; FTP root/lista
ativa também foram validados. Endereços antigos (`10.253.104.10` e anteriores)
estão aposentados. Não use os endereços de outras cópias ou VMs.

## Tela, mouse e interação física

Se a imagem do convidado ficar preta por repouso, desperte-a enviando uma única
tecla ao convidado e confirme que a imagem voltou antes de qualquer outra
entrada. Confirme processo MAME, disco canônico, identidade da VM e canal; a
imagem preta é a condição para enviar o pressionamento, não um motivo para
parar. Faça esse passo sem perguntar ao usuário se a tela está preta nem pedir
que ele a desperte. Não comece com movimento do mouse. Diferencie a tecla
entregue ao convidado do foco do teclado no host.

Há também um resultado específico desta cópia assistente: R381 e R393
registraram que um pulso de um quadro em `:kbd:keyboard4/Shift`, enviado pela
ponte MAME e liberado até o terceiro quadro, restaurou a imagem VUE nas duas
ocasiões. Isso é entrada de teclado injetada no convidado, não tecla física do
host. Para esta cópia, use uma única tecla e confira a imagem, a liberação e o
resultado antes de prosseguir; não repita pulsos às cegas. Se a tecla não
despertar a tela, verifique se o evento foi entregue ao convidado e reporte o
resultado; não transfira automaticamente ao usuário o passo de despertar.

AltGr solta a captura do ponteiro do host. Há relato reproduzido pelo usuário de
que, ao reativar/focar a janela do MAME mesmo com o ponteiro fora dela, a captura
volta. Trate isso como captura do host ao reativar a janela, separada do estado
do mouse no Domain/OS. Não prometa que AltGr mantém a soltura após troca de foco;
não altere opções de captura nem o perfil da VM sem autorização e verificação
específica.

## Identidade antes de operar

Antes de iniciar, enviar entrada, atualizar configurações ou recuperar o clone:

1. confira `ps -C mame,mame64,MAME -o pid,etime,comm,args`;
2. confirme que `-disk1` aponta exatamente para o arquivo canônico acima;
3. confirme que o alias de rede pertence ao namespace deste clone;
4. preserve o perfil 100%/10%, frameskip 4, sem throttle;
5. preserve o disco aprovado em Downloads e todas as demais VMs;
6. não escolha uma cópia antiga por data/nome sem comparar finalidade e
   manifesto.

Ao iniciar esta VM para uma sessão de trabalho, execute-a em um serviço do
`systemd --user`, separado do processo do XChat/Codex. Imediatamente depois da
abertura, registre o PID MAME, o PID/ID do serviço que o iniciou e o caminho
completo de `-disk1`. Associe o PID ao lançamento atual; não use um PID lembrado
de outro turno. Confirme que exatamente uma instância usa esse disco. Se houver
mais de uma, não envie entrada nem escolha uma delas pela aparência: registre
todos os PIDs e resolva a propriedade/duplicidade antes de operar. Uma VM já
aberta dentro da árvore do XChat não pode ser considerada independente só porque
o processo MAME tem um PID próprio.

PID, inode, estado do convidado e namespace são efêmeros e não constituem
identificadores permanentes. Após reinicialização do host, confirme novamente o
processo e os caminhos; não conclua que a VM foi perdida apenas porque o PID
anterior não existe.

Para procedimentos reutilizáveis de identificação da instância, captura,
despertar da tela e entrada de mouse/teclado, siga também a
[skill MAME do projeto](../skills/mame-live-control/SKILL.md) e sua
[referência específica SR10.4](../skills/mame-live-control/references/domainos-sr104.md).
