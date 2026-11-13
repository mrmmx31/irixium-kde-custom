# Contagem opcional do Thunderbird para o painel DomainOS

A integração mostra o total real de mensagens não lidas do perfil aberto do
Thunderbird. Foi verificada com Thunderbird 140.17 ESR. O botão do painel continua
abrindo o cliente escolhido nas preferências; a contagem é uma opção separada,
desativada por padrão. A agenda do painel usa seus provedores de feriados do KDE;
esta extensão não integra calendários.

O total soma pastas físicas, inclusive arquivos e lixeira quando contêm mensagens
não lidas. Exclui raízes, pesquisas virtuais, pastas unificadas e pastas de tags
para evitar contar a mesma mensagem por essas visualizações. Cópias existentes em
duas pastas físicas contam duas vezes. Zero significa que a fonte respondeu e o
total é zero. Fonte ausente, falha ou desconexão produz estado indisponível,
exibido como `—` no botão; não produz um zero inventado.

## Instalar para o usuário atual

O painel requer Plasma 6.1 ou superior e Qt 6.8 ou superior. A ponte opcional
requer `/usr/bin/python3` com `PyQt6.QtCore` e `PyQt6.QtDBus` (no Debian, pacote
`python3-pyqt6`). Essa dependência pertence à ponte; não é necessária para usar o
painel com a contagem desativada.

Na raiz deste repositório ou do pacote fonte:

```sh
python3 integrations/thunderbird-domainos/install.py --install-user
```

O comando registra o host em `~/.mozilla/native-messaging-hosts`, copia seu script
e gera o XPI em `$XDG_DATA_HOME/irixclassic-domainos/thunderbird` (por padrão,
`~/.local/share/irixclassic-domainos/thunderbird`). Registra também uma identidade
de aplicativo oculta para transportar a contagem ao KDE. Não altera o cliente de
e-mail padrão, perfis, contas ou extensões já instaladas do Thunderbird.

No Thunderbird, abra o gerenciador de extensões e use **Instalar extensão de um
arquivo** para selecionar o caminho `xpi` indicado pelo comando. Ative a contagem
nas preferências do painel e selecione Thunderbird, ou siga o padrão do KDE se
esse já for o cliente padrão. O instalador não instala o XPI em um perfil por
conta própria. Para preparar os arquivos sem instalar no usuário atual, use
`--stage /caminho/para/uma/pasta/nova`.

Ao seguir o cliente padrão do KDE, um clique no botão de correio atualiza a
identidade da fonte de forma assíncrona. A atualização não atrasa o lançamento e
oculta o contador anterior até resolver a escolha atual; não consulta preferências
periodicamente.

## Dados e funcionamento

A extensão solicita somente `accountsRead` e `nativeMessaging`. Consulta
`folders.query`, `folders.getFolderInfo` e eventos de alteração das pastas; não
solicita `messagesRead`, não consulta conteúdo de mensagens, bancos de e-mail,
contatos ou calendário. Embora a API de pastas disponibilize nomes e IDs, esses
dados não atravessam a ponte. O único payload publicado é disponibilidade e total
inteiro de mensagens não lidas. As permissões e APIs estão documentadas nas
[APIs oficiais do Thunderbird](https://webextension-api.thunderbird.net/en/mv3/folders.html)
e na [API de native messaging](https://webextension-api.thunderbird.net/en/mv3/runtime.html).
O teste desta implementação também conferiu os schemas distribuídos com a versão
140.17 ESR instalada, pois a documentação online acompanha versões posteriores.

O host mantém uma conexão D-Bus enquanto a porta nativa estiver aberta e publica
o agregado pela interface Unity LauncherEntry, consumida pelo SmartLauncher do
KDE. Uma identidade exclusiva e um watcher do serviço próprio impedem que um
badge antigo ou de outra extensão seja tratado como resultado desta ponte. A
conexão também é marcada indisponível após EOF ou encerramento abrupto do host.
Uma segunda instância do Thunderbird não substitui a fonte já conectada: o total
pertence ao primeiro perfil conectado. Feche-o antes de usar a fonte de outro
perfil.

Não há consulta periódica, reinício automático nem timer de reconexão. Eventos
recebidos durante uma leitura são agrupados para a próxima leitura. Depois de
corrigir um host ausente ou uma dependência, recarregue a extensão ou reinicie o
Thunderbird para estabelecer uma nova porta.

## Validação isolada

```sh
python3 plasma/tools/testar-domainos-thunderbird.py --mode provider --output /tmp/domainos-mail-provider
python3 plasma/tools/testar-domainos-thunderbird.py --mode panel --output /tmp/domainos-mail-panel
python3 plasma/tools/testar-domainos-thunderbird.py --mode thunderbird --output /tmp/domainos-mail-thunderbird
python3 -m unittest discover -s tests -p test_domainos_mail_bridge.py
```

Use pastas de resultado novas. Os ensaios usam HOME, XDG e D-Bus privados. O modo
`provider` testa framing, publicação nativa, badge antigo, zero conhecido, EOF e
crash. O modo `panel` também verifica a ligação Runtime/Instruments e o texto real
do botão, com os loaders de tarefas, pager, bandeja e gráfico desativados nesse
ensaio. O modo `thunderbird` inicia o aplicativo instalado com um perfil descartável, instala
o XPI nesse perfil e cria mensagens sintéticas em uma conta somente local para
comprovar alterações de total e marcação como lidas. Não usa perfis ou mensagens
pessoais. Esses ensaios não equivalem à instalação da extensão no seu perfil real.
